import os
from ConfigParser import ConfigParser
from functools import partial

DB_DIR = os.path.expanduser(os.getenv('ZICDB_PATH') or '~/.zicdb')
try: # Ensure personal dir exists
    os.mkdir(DB_DIR)
except:
    pass

defaults = dict(
        db_host = 'localhost:9090',
        player_host = 'localhost:9090',
        default_port = '9090',
        download_dir = '/tmp',
        history_size = '50',
        )
config_filename = os.path.join(DB_DIR, 'config.ini')

config = ConfigParser(defaults)
config.read(config_filename)
config_read = partial(config.get, 'DEFAULT')
config_list = partial(config.items, 'DEFAULT')

def config_write(varname, value):
    if varname.endswith('_host') and not ':' in value:
        value+=':%s'%config_read('default_port')
    try:
        config.set('DEFAULT', varname, value)
    except Exception, e:
        print str(e)
    else:
        config.write(file(config_filename, 'w'))


