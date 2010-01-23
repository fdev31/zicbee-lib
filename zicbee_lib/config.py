import os
import atexit
import ConfigParser

__all__ = ['DB_DIR', 'defaults_dict', 'config', 'aliases', 'shortcuts']

DB_DIR = os.path.expanduser(os.getenv('ZICDB_PATH') or '~/.zicdb')
VALID_EXTENSIONS = ['mp3', 'ogg', 'mp4', 'aac', 'vqf', 'wmv', 'wma', 'm4a', 'asf', 'oga', 'flac']

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
        'fork': 'yes',
        'socket_timeout': '30',
        'enable_history': 'yes',
        'custom_extensions': 'mpg,mp2',
        'players' : '',
        'notify' : 'yes',
        'loop': 'yes',
        'autoshuffle': 'yes',
        }

config_filename = os.path.join(DB_DIR, 'config.ini')

class _ConfigObj(object):

    _cfg = ConfigParser.ConfigParser(defaults_dict)

    def __init__(self):
        if os.path.exists(config_filename):
            self._cfg.read(config_filename)
        else:
            self._cfg.write(file(config_filename, 'w'))

    def __setattr__(self, name, val):

        if name.endswith('_host'):

            if val in aliases:
                val = aliases[val]

            if ':' not in val:
                val = '%s:%s'%( val, self.default_port )
        elif val.lower() in ('off', 'no'):
            val = ''

        val = self._cfg.set('DEFAULT', name, val)
        config._cfg.write(file(config_filename, 'w'))
        return val

    def __getattr__(self, name):
        return self._cfg.get('DEFAULT', name)

    __setitem__ = __setattr__
    __getitem__ = __getattr__

    def __iter__(self):
        for k in defaults_dict:
            yield (k, self[k])

# Ensure the file is written on drive
#atexit.register(lambda: config._cfg.write(file(config_filename, 'w')))

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
VALID_EXTENSIONS.extend(c.strip() for c in config.custom_extensions.split(','))

# media-specific configuration
media_config = _DefaultDict( {'player_cache': 128, 'init_chunk_size': 2**18, 'chunk_size': 2**14},
        {
            'flac' : {'player_cache': 4096, 'init_chunk_size': 2**22, 'chunk_size': 2**20},
            'm4a' : {'player_cache': 4096, 'init_chunk_size': 2**22, 'chunk_size': 2**20, 'cursed': True},
            },
        valid_keys = VALID_EXTENSIONS)

