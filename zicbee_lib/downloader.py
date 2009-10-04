import os
import sys
import time
from zicbee_lib.core import urllib2
from itertools import chain
from weakref import WeakKeyDictionary
try:
    from zicbee.core.zutils import duration_tidy
except ImportError:
    def duration_tidy(secs):
        return "%.1f s."%(secs)

def DownloadGenerator(uri):
    uri, filename = uri

    if os.path.exists(filename):
        return

    site = urllib2.urlopen(uri)
    out_file = file(filename, 'w')
    BUF_SZ = 2**16
    try:
        total_size = int(site.info().getheader('Content-Length'))
    except TypeError:
        total_size = None
    actual_size = 0
    progress_p = 0

    while True:
        data = site.read(BUF_SZ)
        if not data:
            out_file.close()
            break
        out_file.write(data)
        actual_size += len(data)

        if total_size:
            percent = total_size/actual_size
        else:
            percent = actual_size

        if percent != progress_p:
            yield percent

            progress_p = percent
        else:
            yield '.'


class Downloader(object):
    def __init__(self, nb_dl=2):
        self._nb_dl = nb_dl
        self._last_display = time.time()

    def run(self, uri_list):
        downloaders = [] # Generators to handle
        in_queue = [] # List of "TODO" uris

        _download_infos = dict(count=0, start_ts = time.time())
        percent_memory = WeakKeyDictionary()
        write_out = sys.stdout.write

        def _download():
            for dl in downloaders:
                try:
                    ret = dl.next()
                except StopIteration:
                    downloaders.remove(dl)
                    _download_infos['count'] += 1
                else:
                    if isinstance(ret, int):
                        percent_memory[dl] = ret

            # Display things
            t = time.time()

            if self._last_display + 0.1 < t:
                self._last_display = t
                sumup = ', '.join('%3d%%'%(val if int(val)<=100 else 0)
                        for val in percent_memory.itervalues())
                write_out(' [ %s ] %d               \r'%(sumup, _download_infos['count']))

                sys.stdout.flush()

        for uri in chain( uri_list, in_queue ):
            if len(downloaders) < self._nb_dl:
                try:
                    dg = DownloadGenerator(uri)
                    dg.next() # start the pump
                    downloaders.append( dg )
                except StopIteration:
                    pass
            else:
                in_queue.append(uri) # Later please !
                # iterate
                _download()

        # Terminate the job
        while downloaders:
            _download()

        t = time.time() - _download_infos['start_ts']
        write_out("                         \nGot %d files in %s. Enjoy ;)\n"%(
                _download_infos['count'], duration_tidy(t)))
