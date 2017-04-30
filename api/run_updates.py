import parser, models
from getter import Requester
import logging
import os
import pickle
from urlparse import urlparse
from posixpath import basename, dirname
from django.utils import timezone
from leftstay.settings import OUT_DIR


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

    def __init__(self, url_qset, request_id, dump_errors=True):
        self.request_id = request_id
        self.requester = Requester(request_id)
        self.url_qset = url_qset
        self.logger = logging.getLogger("minion.%s" % request_id)
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

    def up(self):
        for obj in self.url_qset:
            try:
                resp = self.requester.get(obj.url)
                if resp.status_code == 200:
                    p = self.parser(resp.content)
                    self.update_one(obj, p)
                else:
                    self.report_error(obj, resp)

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


    def update_one(self, obj, parsed):
        # TODO
        pass