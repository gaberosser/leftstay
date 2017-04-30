import parser, models, consts
from getter import Requester
import logging
import os
import pickle
from urlparse import urlparse
from posixpath import basename, dirname
from django.utils import timezone
from leftstay.settings import OUT_DIR
from leftstay.utils import dict_equality

class Minion(object):
    """
    A minion will work its way down a list of URLs, fetching and updating each one and creating records where necessary.
    This should be a process that can be run in parallel with many minions.
    The minion accepts a queryset input so that it can update the input URL records with results.
    When a minion has retrieved and parsed data from a URL, it runs a diff against the most recent record for that
    URL (if it exists) and only performs an update if there has been a real change.
    Each minion has an ID that it uses to make requests.
    """
    parser = None
    model = None

    def __init__(self, url_qset, request_id, dump_errors=True):
        self.request_id = request_id
        self.requester = Requester(request_id)
        self.url_qset = url_qset
        self.logger = logging.getLogger(
            "%s.%s" % (self.__class__.__name__, request_id)
        )
        self.dump_errors = dump_errors
        if dump_errors:
            self.outdir = os.path.join(OUT_DIR, 'minion.%s.%s' % (
                self.request_id, timezone.now().strftime("%Y-%m-%d_%H%M%S")
            ))
            if not os.path.exists(self.outdir):
                os.makedirs(self.outdir)
        self.logger.info("Minion %s reporting for duty!", self.request_id)
        self.logger.info("You gave me a list of %d URLs. Let's get to work.", self.url_qset.count())

        self.up()

    def update_url(self, obj, updated=False, status_code=None, status=None):
        obj.last_accessed = timezone.now()
        if updated:
            obj.last_updated = timezone.now()
        if status_code is not None:
            obj.last_status_code = status_code
        if status is not None:
            obj.last_known_status = status
        obj.save()

    def up(self):
        for obj in self.url_qset:
            try:
                resp = self.requester.get(obj.url)
                if resp.status_code == 200:
                    p = self.parser(resp.content)
                    if p['status'] == 'removed':
                        status = consts.URL_STATUS_REMOVED
                    else:
                        status = consts.URL_STATUS_ACTIVE
                    updated = self.update_one(obj, p)
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

    def report_error(self, obj, resp):
        if self.dump_errors:
            fn = urlparse(obj.url)
            fn = basename(fn.path)
            fn = os.path.join(self.outdir, fn)
            pickle.dump(resp, open(fn, 'wb'))
            self.logger.error("Failed to get URL %s (status code %d). Dumped to file %s", obj.url, resp.status_code, fn)
        else:
            self.logger.error("Failed to get URL %s (status code %d)", obj.url, resp.status_code)

    def obj_to_dict(self, x):
        """
        Convert the existing model object to a dictionary for comparison with the parsed output.
        Must be implemented in child classes.
        :param x: Of instance self.model
        :return: Dictionary
        """
        return x.to_dict()

    def dict_to_obj(self, x):
        """
        Convert the parsed data in dictionary to unsaved object(s).
        These are returned in a list, and should be created in the same order, allowing
        foreign keys to be honoured.
        :param x: Dictionary from parser.
        :return: List of objects
        """
        return self.model.from_dict(x)

    def update_one(self, obj, parsed):
        """
        Update database with a single parsed record.
        :param obj: URL object
        :param parsed: Dictionary with parsed data.
        :return: Boolean indicating whether an update has been performed
        """
        x = self.model.objects.filter(
            url=obj.url
        )
        if x.exists():
            x = x.latest('accessed')
            existing = self.obj_to_dict(x)
            eq = dict_equality(existing, parsed, return_diff=False)
            if eq:
                # just update the accessed date
                x.accessed = timezone.now()
                x.save()
                return False
            else:
                new = self.dict_to_obj(parsed)
                new.save()
                return True
        else:
            # no existing record, no comparison needed
            new = self.dict_to_obj(parsed)
            new.save()
            return True


class ResidentialForSaleMinion(Minion):
    parser = parser.residential_property_for_sale

    def obj_to_dict(self, x):
        pass

    def dict_to_obj(self, x):
        pass

