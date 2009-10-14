__all__ = ['get_players', 'resource_filename']

import os, sys
from pkg_resources import iter_entry_points, resource_filename as pkg_resource_filename, ExtractionError

class _FakeEntryPoint(object):

    def __init__(self, name, objname):
        exec ('import %s as _mymod')
        self._obj = getattr(_mymod, objname)
        self.name = name

    def load(self):
        return self._obj

def get_players():
    """ returns an iterable with available Player classes """
    l =  list(iter_entry_points("zicbee.player"))
    for p in l:
        try:
            p.load()
        except:
            l.remove(p)

    if not l:
        # failsafe
        for mod in "zicbee_mplayer", "zicbee_vlc":
            try:
                l.append( _FakeEntryPoint(mod, 'Player') )
            except ImportError:
                pass
    return l

def resource_filename(package, resource):
    """ substitute to pkg_resources.resource_filename """
    try:
        return pkg_resource_filename(package, resource)
    except (ExtractionError, KeyError):
        fullpath = os.path.join(package.replace('.', os.sep), resource)
        for path in [os.curdir] + sys.path:
            p = os.path.join(path, fullpath)
            if os.path.exists(p):
                return os.path.abspath(p)
        else:
            raise


