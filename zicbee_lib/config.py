import os
import atexit
import ConfigParser

__all__ = ['DB_DIR', 'defaults_dict', 'config', 'aliases']

DB_DIR = os.path.expanduser(os.getenv('ZICDB_PATH') or '~/.zicdb')

class _Aliases(dict):
    def __init__(self):
        dict.__init__(self)
        self._db_dir = os.path.join(DB_DIR, 'aliases.txt')
        try:
            self._read()
        except IOError:
            self._write()

    def add(self, name, address):
        self[name] = address
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

defaults_dict = {
        'streaming_file' : '/tmp/zsong',
        'download_dir' : '/tmp',
        'db_host' : 'localhost:9090',
        'player_host' : 'localhost:9090',
        'debug' : '',
        'default_search' : '',
        'history_size' : 50,
        'default_port': '9090',
        'web_skin' : 'default',
        'fork': 'blank_me_to_stop_forking_on_serve_mode',
        'socket_timeout': '30',
        'enable_history': 'blank_to_disable',
        'players' : '',
        'loop': 'yes',
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

config = _ConfigObj()
aliases = _Aliases()

class DefaultDict(dict):
    def __init__(self, default, *a):
        dict.__init__(self, *a)
        self._default = default

    def __getitem__(self, val):
        try:
            return dict.__getitem__(self, val)
        except KeyError:
            return self._default

media_config = DefaultDict( {'player_cache': 128, 'init_chunk_size': 2**18, 'chunk_size': 2**14},
        {
            'flac' : {'player_cache': 4096, 'init_chunk_size': 2**22, 'chunk_size': 2**20},
            }
        )
