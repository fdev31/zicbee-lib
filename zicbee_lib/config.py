import os
from time import time
import ConfigParser

__all__ = ['DB_DIR', 'defaults_dict', 'config', 'aliases', 'shortcuts']

DB_DIR = os.path.expanduser(os.getenv('ZICDB_PATH') or '~/.zicdb')
VALID_EXTENSIONS = ['mp3', 'ogg', 'mp4', 'aac', 'vqf', 'wmv', 'wma', 'm4a', 'asf', 'oga', 'flac', 'mpc', 'spx']

def get_list_from_str(s):
    return [c.strip() for c in s.split(',')]

class _Aliases(dict):
    def __init__(self, name):
        dict.__init__(self)
        self._db_dir = os.path.join(DB_DIR, '%s.txt'%name)
        try:
            self._read()
        except IOError:
            self._write()

    def __delitem__(self, name):
        dict.__delitem__(self, name)
        self._write()

    def __setitem__(self, name, address):
        dict.__setitem__(self, name, address)
        self._write()

    def _read(self):
        self.update(dict((s.strip() for s in l.split(None, 1)) for l in file(self._db_dir)))

    def _write(self):
        f = file(self._db_dir, 'w')
        for k, v in self.iteritems():
            f.write('%s %s\n'%(k,v))
        f.close()

try: # Ensure personal dir exists
    os.mkdir(DB_DIR)
except:
    pass

try:
    from win32com.shell import shell, shellcon
    TMP_DIR = shell.SHGetPathFromIDList (
            shell.SHGetSpecialFolderLocation(0, (shellcon.CSIDL_DESKTOP, shellcon.CSIDL_COMMON_DESKTOPDIRECTORY)[0])
            )
except ImportError: # sane environment ;)
    TMP_DIR=r"/tmp"

# Dictionary with default configuration
defaults_dict = {
        'streaming_file' : os.path.join(TMP_DIR, 'zsong'),
        'download_dir' : TMP_DIR,
        'db_host' : 'localhost:9090',
        'player_host' : 'localhost:9090',
        'debug' : '',
        'default_search' : '',
        'history_size' : 50,
        'default_port': '9090',
        'web_skin' : 'default',
        'fork': 'no',
        'allow_remote_admin': 'yes',
        'socket_timeout': '30',
        'enable_history': 'yes',
        'custom_extensions': 'mpg,mp2',
        'players' : 'vlc,gst,mplayer',
        'music_folder' : '',
        'notify' : 'yes',
        'loop': 'yes',
        'autoshuffle': 'yes',
        }

config_filename = os.path.join(DB_DIR, 'config.ini')

class _ConfigObj(object):

    _cfg = ConfigParser.ConfigParser(defaults_dict)

    def _refresh(self):
        t = int(time()+0.5)
        if self._lastcheck + 1 < t:
            self._lastcheck = t
            st = os.stat(config_filename)
            st = max(st.st_mtime, st.st_ctime)
            if self._mtime < st:
                self._mtime = st
                self._cfg.read(config_filename)

    def __init__(self):

        self._mtime = 0 # last mtime of the file
        self._lastcheck = 0 # os.stat flood protection

        try:
            self._refresh()
        except OSError:
            self._cfg.write(file(config_filename, 'w'))

    def __setattr__(self, name, val):
        if name in ('_lastcheck', '_mtime'):
            return object.__setattr__(self, name, val)

        self._refresh()
        if name.endswith('_host'):
            ref = self[name]

            if val[0] in '+-':
                if val[0] == '+':
                    mode = 'a'
                else:
                    mode = 'd'
                val = val[1:].strip()
            else:
                mode = 'w'

            if isinstance(val, basestring):
                val = (v.strip() for v in val.split(','))

            vals = (aliases[v] if v in aliases else v for v in val)
            vals = ('%s:%s'%( v, self.default_port ) if ':' not in v
                    else v for v in vals)

            if mode != 'w':
                if mode == 'a':
                    ref.extend(vals)
                elif mode == 'd':
                    for v in vals:
                        ref.remove(v)
                vals = ref

            val = ','.join(vals)

        elif val.lower() in ('off', 'no'):
            val = ''

        val = self._cfg.set('DEFAULT', name, val)
        config._cfg.write(file(config_filename, 'w'))
        return val

    def __getattr__(self, name):
        self._refresh()
        v = self._cfg.get('DEFAULT', name)
        if name in ('db_host', 'player_host', 'custom_extensions', 'players', 'allow_remote_admin'):
            return [s.strip() for s in v.split(',')]
        return v

    __setitem__ = __setattr__
    __getitem__ = __getattr__

    def __iter__(self):
        for k in defaults_dict:
            yield (k, self[k])

# Config object, supports dots. and brackets[]
config = _ConfigObj()

# Dictionary-like of alias: expanded_value
aliases = _Aliases('aliases')
shortcuts = _Aliases('shortcuts')

class _DefaultDict(dict):
    def __init__(self, default, a, valid_keys=None):
        dict.__init__(self, a)
        self._default = default
        if valid_keys:
            self.valid_keys = valid_keys
        else:
            self.valid_keys = None

    def keys(self):
        k = dict.keys(self)
        if self.valid_keys:
            k = set(k)
            k.update(self.valid_keys)
        return k

    def __getitem__(self, val):
        try:
            return dict.__getitem__(self, val)
        except KeyError:
            return self._default

# List of valid extensions
VALID_EXTENSIONS.extend(config.custom_extensions)

# media-specific configuration
media_config = _DefaultDict( {'player_cache': 128, 'init_chunk_size': 2**18, 'chunk_size': 2**14},
        {
            'flac' : {'player_cache': 4096, 'init_chunk_size': 2**22, 'chunk_size': 2**20},
            'm4a' : {'player_cache': 4096, 'init_chunk_size': 2**22, 'chunk_size': 2**20, 'cursed': True},
            },
        valid_keys = VALID_EXTENSIONS)

