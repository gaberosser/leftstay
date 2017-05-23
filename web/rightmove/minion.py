import parser, models, consts
from getter import Requester, PropertyXmlGetter, update_property_urls
import logging
import os
import pickle
from urlparse import urlparse
from posixpath import basename, dirname
from django.utils import timezone
from leftstay.settings import OUT_DIR, DEFAULT_USER_AGENT
from leftstay.utils import dict_equality
# Celery implementation
from leftstay import celery_app


class Minion(object):
    """
    A minion will work its way down a list of URLs, fetching and updating each one and creating records where necessary.
    This should be a process that can be run in parallel with many minions.
    The minion accepts a queryset input so that it can update the input URL records with results.
    When a minion has retrieved and parsed data from a URL, it runs a diff against the most recent record for that
    URL (if it exists) and only performs an update if there has been a real change.
    Each minion has an ID that it uses to make requests.
    """

    model = None

    @staticmethod
    def parser(*args, **kwargs):
        """
        This has to be implemented as a staticmethod, otherwise it will be called with implicit passing of `self`.
        Since the function does not expect an instance of Minion as its first argument, it will fail (!)
        """
        return NotImplementedError

    def __init__(self, url_qset, user_agent, dump_errors=True):
        self.user_agent = user_agent
        self.requester = Requester(user_agent)
        self.url_qset = url_qset
        self.logger = logging.getLogger(
            "rightmove.%s.%s" % (self.__class__.__name__, user_agent)
        )
        self.dump_errors = dump_errors
        if dump_errors:
            self.outdir = os.path.join(OUT_DIR, '%s.%s.%s' % (
                self.__class__.__name__.lower(),
                self.user_agent,
                timezone.now().strftime("%Y-%m-%d_%H%M%S")
            ))
            if not os.path.exists(self.outdir):
                os.makedirs(self.outdir)
        self.logger.info("Minion %s reporting for duty!", self.user_agent)
        self.up()

    def update_url(self, obj, updated=False, status_code=None, status=None):
        obj.last_accessed = timezone.now()
        if updated:
            obj.last_updated = timezone.now()
        if status_code is not None:
            obj.last_status_code = status_code
        if status is not None:
            obj.last_known_status = status
        if status_code == 200:
            obj.consecutive_failed_attempts = 0
        else:
            obj.consecutive_failed_attempts += 1

        obj.save()

    def up(self):
        n = self.url_qset.count()
        self.logger.info("You gave me a list of %d URLs. Let's get to work.", n)
        for i, obj in enumerate(self.url_qset):
            self.logger.info("%d / %d", i + 1, n)
            resp = None
            try:
                resp = self.requester.get(obj.url)
                if resp.status_code == 200:
                    dat = self.parser(resp.content, url_obj=obj)
                    if dat['status'] == 'removed':
                        status = consts.URL_STATUS_REMOVED
                    else:
                        status = consts.URL_STATUS_ACTIVE

                    if len(dat['errors']):
                        self.logger.error(
                            "Encountered some errors with url %s",
                            obj.url,
                            extra={'errors': dat['errors']}
                        )

                    updated = self.update_one(obj, dat['deferred'])
                    self.update_url(
                        obj,
                        updated=updated,
                        status_code=resp.status_code,
                        status=status
                    )
                else:
                    self.report_error(obj, resp)
                    self.update_url(
                        obj,
                        updated=False,
                        status_code=resp.status_code,
                        status=consts.URL_STATUS_INACCESSIBLE
                    )
            except Exception:
                self.logger.exception("I failed on URL %s", obj.url)
                if resp is not None:
                    self.report_error(obj, resp)

    def report_error(self, obj, resp):
        if self.dump_errors:
            fn = urlparse(obj.url)
            fn = basename(fn.path)
            fn = os.path.join(self.outdir, fn)
            pickle.dump(resp, open(fn, 'wb'))
            self.logger.error("Failed to get URL %s (status code %d). Dumped to file %s", obj.url, resp.status_code, fn)
        else:
            self.logger.error("Failed to get URL %s (status code %d)", obj.url, resp.status_code)

    def get_deferred(self, x):
        """
        Convert the existing model object to one or more DeferredModel instances for comparison with the parsed output.
        Must be implemented in child classes.
        :param x: Of instance self.model
        :return: List of DeferredModel instances in the same order as they would be created by the parser.
        """
        # base implementation returns only one instance
        return [x.to_deferred()]

    def update_one(self, obj, parsed):
        """
        Update database with a single parsed record.
        :param obj: URL object
        :param parsed: Dictionary with parsed data.
        :return: Boolean indicating whether an update has been performed
        """
        x = self.model.objects.filter(
            url=obj
        )
        if x.exists():
            x = x.latest('accessed')
            existing = self.get_deferred(x)
            if len(existing) != len(parsed):
                self.logger.error(
                    "Number of existing deferred instances (%d) does not match the number of parsed instances (%d).",
                    len(existing),
                    len(parsed)
                )
                self.logger.error("This is probably due to the implementation of the get_deferred() method")
                raise AttributeError("Lengths of deferred lists do not match.")

            eq = all([
                dict_equality(e.attrs, p.attrs, return_diff=False) for e, p in zip(existing, parsed)
            ])

            if eq:
                # just update the accessed date
                x.accessed = timezone.now()
                x.save()
                return False
            else:
                for p in parsed:
                    p.save()
                return True
        else:
            # no existing record, no comparison needed
            for p in parsed:
                p.save()
            return True


class ResidentialForSaleMinion(Minion):
    model = models.PropertyForSale

    @staticmethod
    def parser(*args, **kwargs):
        return parser.residential_property_for_sale(*args, **kwargs)

    def get_deferred(self, x):
        """
        Generates a list of deferred objects.
        The first object corresponds to the PropertyForSale itself, then subsequent objects are deferred NearestStation
        ordered by station name.
        """
        de = super(ResidentialForSaleMinion, self).get_deferred(x)
        if x.neareststation_set.exists():
            for ns in x.neareststation_set.order_by('station'):
                de.append(ns.to_deferred())
        return de
