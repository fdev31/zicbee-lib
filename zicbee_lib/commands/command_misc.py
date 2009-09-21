__all__ = [ 'modify_move', 'modify_show', 'set_variables', 'tidy_show', 'inject_playlist' , 'hook_next', 'hook_prev']

import ConfigParser
from zicbee_lib.config import config
from zicbee_lib.core import get_infos, memory
from urllib import quote

def hook_next():
    if 'pls_position' in memory:
        del memory['pls_position']
    return '/next'

def hook_prev():
    if 'pls_position' in memory:
        del memory['pls_position']
    return '/prev'


def inject_playlist(symbol):
    uri = memory.get('last_search')
    if uri is None:
        print "Do a search first !"
        return
    pattern = uri.split('pattern=', 1)[1]
    substr = ("%s%%20pls%%3A%%20%s%%23"%(pattern, quote(symbol))).replace('%', '%%')
    v = "/search?host=%(db_host)s&pattern="+substr
    return v

def set_variables(name=None, value=None):
    try:
        if name is None:
            for varname, varval in config:
                print "%s = %s"%(varname, varval)
        elif value:
            config[name] = value
            print "%s = %s"%(name, config[name])
        else:
            print config[name]
            print "%s = %s"%(name, config[name])
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
        pos = memory.get('pls_position')
        if pos is None:
            return ''

        position = int(pos)

        if position >= 0:
            memory['show_offset'] = position
            return '/playlist?res=%s&start=%s'%(answers, position)
        else:
            memory['show_offset'] = 0
            return '/playlist?res=%s'%(answers)

def tidy_show(it):
    offs = memory['show_offset']
    now = int(memory.get('pls_position'))

    for i, line in enumerate(it):
        idx = offs+i
        print ('%3d '%idx if idx != now else ' >> ') + ' | '.join(line.split(' | ')[:4])

