__all__ = [ 'last_uri', 'modify_move', 'modify_show', 'set_variables', 'tidy_show' ]

import ConfigParser
from .config import config_list, config_read, config_write
from .utils import get_infos, memory

def last_uri(u):
    memory['last_search'] = u

def set_variables(name=None, value=None):
    try:
        if name is None:
            for varname, varval in config_list():
                print "%s = %s"%(varname, varval)
        elif value:
            config_write(name, value)
            print "%s = %s"%(name, config_read(name))
        else:
            print config_read(name)
            print "%s = %s"%(name, config_read(name))
    except ConfigParser.NoOptionError:
        print "invalid option."

def modify_move(songid, where=None):
    if where is None:
        infos = get_infos()
        where = int(infos['pls_position'])+1
    return '/move?s=%s&d=%s'%(songid, where)

def modify_show(answers=10, start=None):
    if start:
        memory['show_offset'] = int(start)
        return '/playlist?res=%s&start=%s'%(answers, start)
    else:
        position = int(get_infos()['pls_position'])
        if position >= 0:
            memory['now_playing'] = memory['show_offset'] = position
            return '/playlist?res=%s&start=%s'%(answers, position)
        else:
            memory['now_playing'] = memory['show_offset'] = 0
            return '/playlist?res=%s'%(answers)

def tidy_show(it):
    offs = memory['show_offset']
    now = memory.get('now_playing', None)

    for i, line in enumerate(it):
        idx = offs+i
        print ('%3d '%idx if idx != now else ' >> ') + ' | '.join(line.split(' | ')[:4])

