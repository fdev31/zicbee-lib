__all__ = ['memory', 'iter_webget', 'webget', 'get_infos']

from time import time
try:
    import urllib as urllib2
except ImportError: # Compatibility with python3
    import urllib2 # WARNING: urllib2 makes IncompleteRead sometimes... observed with python2.x

from .config import config, DB_DIR

def get_infos():
    d = {}
    for line in iter_webget('/infos'):
        line = line.strip()
        if line:
            k, v = line.split(':', 1)
            v = v.lstrip()
            d[k] = v
            memory[k] = v
    return d

def _safe_webget_iter(uri):
    site = urllib2.urlopen(uri)
    while True:
        try:
            l = site.readline()
        except Exception, e:
            print "ERR:", e
            break
        else:
            if l:
                yield l.strip()
            else:
                break

def iter_webget(uri):
    if not '://' in uri:
        if 'db' in uri.split('/', 4)[:-1]:
            host = config['db_host']
        else:
            host = config['player_host']

        uri = 'http://%s/%s'%(host, uri.lstrip('/'))
    try:
        return _safe_webget_iter(uri)
    except IOError, e:
        print "webget(%s): %s"%(uri, e)


class _LostMemory(dict):
    amnesiacs = (
        'album',
        'song_position',
        'title',
        'artist',
        'uri',
        'pls_position',
        'paused',
        'length',
        'score',
        'id',
        'pls_size',
        'tags')

    def __init__(self):
        self._tss = dict()
        dict.__init__(self)

    def __getitem__(self, idx):
        if self._is_recent(idx):
            return dict.__getitem__(self, idx)

    def _is_recent(self, idx):
        if idx not in self.amnesiacs:
            return True
        DURATION=1
        t = time()

        return self._tss.get(idx, t-(2*DURATION))+DURATION > t

    def __setitem__(self, itm, val):
        self._tss[itm] = time()
        dict.__setitem__(self, itm, val)

    def __delitem__(self, slc):
        del self._tss[slc]
        dict.__delitem__(self, slc)

    def get(self, idx, default=None):
        """ Gets the data, if not recent enough refresh infos """
        if not self._is_recent(idx):
            get_infos()
        return dict.get(self, idx, default)

    def clear(self):
        dict.clear(self)
        self._tss.clear()

memory = _LostMemory()
