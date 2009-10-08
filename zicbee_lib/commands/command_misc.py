__all__ = [ 'modify_move', 'modify_show', 'set_variables', 'tidy_show', 'inject_playlist',
'hook_next', 'hook_prev', 'complete_set', 'complete_alias', 'set_alias', 'set_grep_pattern', 'apply_grep_pattern']

import ConfigParser
from zicbee_lib.config import config, aliases
from zicbee_lib.core import get_infos, memory
from zicbee_lib.formats import get_index_or_slice
from urllib import quote

def complete_set(cur_var, params):
    if len(params) <= 2 and cur_var:
        # complete variables
        ret = (k for k, a in config if k.startswith(cur_var))
    elif len(params) >= 2:
        data = dict(config)
        # complete values
        if '_host' in params[1]:
            data.update(('___'+v, v) for v in aliases)
        ret = set([v for v in data.itervalues()] + ['localhost'])
    return ret

def hook_next(output):
    if 'pls_position' in memory:
        del memory['pls_position']
    return '/next'

def hook_prev(output):
    if 'pls_position' in memory:
        del memory['pls_position']
    return '/prev'

def set_grep_pattern(output, *pat):
    memory['grep'] = ' '.join(pat)
    return '/playlist'

def apply_grep_pattern(it):
    # TODO: optimize
    pat = memory['grep'].lower()
    grep_idx = []
    for i, line in enumerate(it):
        if pat in line.lower():
            grep_idx.append(i-len(grep_idx))
            yield "%3d %s"%(i, ' | '.join(line.split(' | ')[:4]))

    memory['grepped'] = grep_idx

def inject_playlist(output, symbol):
    uri = memory.get('last_search')
    if uri is None:
        print "Do a search first !"
        return
    pattern = uri.split('pattern=', 1)[1]
    # crazy escaping
    substr = ("%s%%20pls%%3A%%20%s%%23"%(pattern, quote(symbol))).replace('%', '%%')
    v = "/search?host=%(db_host)s&pattern="+substr
    return v

def set_alias(output, name=None, value=None):
    try:
        if name is None:
            for varname, varval in aliases.iteritems():
                output(["%s = %s"%(varname, varval)])
        elif value:
            aliases.add(name, value)
            output(["%s = %s"%(name, aliases[name])])
        else:
            output(["%s = %s"%(name, aliases[name])])
    except KeyError:
        print "invalid option."

def complete_alias(cur_var, params):
    if len(params) <= 2 and cur_var:
        # complete variables
        ret = (k for k in aliases.iterkeys() if k.startswith(cur_var))
    elif len(params) >= 2:
        ret = (v for v in aliases.itervalues() if v.startswith(cur_var))
    return ret

def set_variables(output, name=None, value=None):
    try:
        if name is None:
            for varname, varval in config:
                output(["%s = %s"%(varname, varval)])
        elif value:
            config[name] = value
            output(["%s = %s"%(name, config[name])])
        else:
            output(["%s = %s"%(name, config[name])])
    except ConfigParser.NoOptionError:
        output(["invalid option."])

def modify_delete(output, songid):
    if songid == 'grep':
        return ('/delete?idx=%s'%i for i in memory['grepped'])
    else:
        return '/delete?idx=%s'%songid

def modify_move(output, songid, where=None):

    if where is None:
        infos = get_infos()
        where = int(infos['pls_position'])+1
    if songid == 'grep':
        return ('/move?s=%s&d=%s'%(i, where) for i in memory['grepped'])
    else:
        return '/move?s=%s&d=%s'%(songid, where)

def modify_show(output, answers=10):
    answers = get_index_or_slice(answers)
    if isinstance(answers, slice):
        memory['show_offset'] = answers.start
        results = 0 if answers.stop <= 0 else answers.stop - answers.start
        return '/playlist?res=%s&start=%s'%(results, answers.start)
    else:
        pos = memory.get('pls_position')
        if pos is None:
            return ''

        try:
            position = int(pos)
        except TypeError:
            position = -1

        if position >= 0:
            memory['show_offset'] = position
            return '/playlist?res=%s&start=%s'%(answers, position)
        else:
            memory['show_offset'] = 0
            return '/playlist?res=%s'%(answers)

def tidy_show(it):
    offs = memory['show_offset']
    now = int(memory.get('pls_position', -1))

    for i, line in enumerate(it):
        idx = offs+i
        yield '%3s %s'%(idx if idx != now else ' >> ', ' | '.join(line.split(' | ')[:4]))

