__all__ = [ 'modify_move', 'modify_show', 'set_variables', 'tidy_show', 'inject_playlist',
'hook_next', 'hook_prev', 'complete_set', 'complete_alias', 'set_alias', 'set_grep_pattern',
'apply_grep_pattern', 'set_shortcut']

import ConfigParser
from zicbee_lib.config import config, aliases, shortcuts
from zicbee_lib.core import get_infos, memory, iter_webget
from zicbee_lib.formats import get_index_or_slice
from urllib import quote

def complete_set(cur_var, params):
    """ "set" command completion """
    if len(params) <= 2 and cur_var:
        # complete variables
        ret = (k for k, a in config if k.startswith(cur_var))
    elif len(params) >= 2:
        data = dict(config)
        # complete values
        if '_host' in params[1]:
            data.update(('___'+v, v) for v in aliases)
        ret = [v for v in data.itervalues()]
        for r in list(ret):
            if isinstance(r, (list, tuple)):
                ret.remove(r)
                ret.extend(r)
        ret.append('localhost')
        ret = set(r for r in ret if r.startswith(cur_var))
    return ret

def hook_next(output):
    """ "next" command hook """
    if 'pls_position' in memory:
        del memory['pls_position']
    return '/next'

def hook_prev(output):
    """ "prev" command hook """
    if 'pls_position' in memory:
        del memory['pls_position']
    return '/prev'

def set_grep_pattern(output, *pat):
    """ remembers the "grep" pattern """
    memory['grep'] = ' '.join(pat)
    return '/playlist'

def apply_grep_pattern(it):
    """ apply the "grep" pattern to the given iterator """
    # TODO: optimize
    pat = memory['grep'].lower()
    grep_idx = []
    for i, line in enumerate(it):
        if pat in line.lower():
            grep_idx.append(i)
            yield "%3d %s"%(i, ' | '.join(line.split(' | ')[:4]))

    memory['grepped'] = grep_idx

def inject_playlist(output, symbol):
    """ Play (inject in current playlist) the last "search" result """
    uri = memory.get('last_search')
    if not uri:
        print "Do a search first !"
        return
    pattern = uri[0].split('pattern=', 1)[1] # the pattern should be the same for anybody
    # crazy escaping
    substr = ("%s%%20pls%%3A%%20%s%%23"%(pattern, quote(symbol))).replace('%', '%%')
    v = "/search?host=%(db_host)s&pattern="+substr
    return v

def set_shortcut(output, name=None, *args):
    """ Sets some shortcut """
    if args:
        value = ' '.join(args)
    else:
        value = None

    try:
        if name is None:
            for varname, varval in shortcuts.iteritems():
                output(["%s = %s"%(varname, varval)])
        elif value:
            if value.lower() in ('no', 'off', 'false'):
                del shortcuts[name]
            else:
                shortcuts[name] = value
                output(["%s = %s"%(name, shortcuts[name])])
        else:
            output(["%s = %s"%(name, shortcuts[name])])
    except KeyError:
        print "invalid option."

def set_alias(output, name=None, value=None):
    """ Sets some alias """
    try:
        if name is None:
            for varname, varval in aliases.iteritems():
                output(["%s = %s"%(varname, varval)])
        elif value:
            if value.lower() in ('no', 'off', 'false'):
                del aliases[name]
            else:
                aliases[name] = value
                output(["%s = %s"%(name, aliases[name])])
        else:
            output(["%s = %s"%(name, aliases[name])])
    except KeyError:
        print "invalid option."

def complete_alias(cur_var, params):
    """ Completes the "alias" command """
    if len(params) <= 2 and cur_var:
        # complete variables
        ret = (k for k in aliases.iterkeys() if k.startswith(cur_var))
    elif len(params) >= 2:
        ret = (v for v in aliases.itervalues() if v.startswith(cur_var))
    return ret

def set_variables(output, name=None, value=None, *args):
    """ Set some variable """
    CST = ' ,='
    if name:
        if '=' in name:
            nargs = (n.strip() for n in name.split('=') if n.strip())
            name = nargs.next()
            args = tuple(nargs) + args
        name = name.strip(CST)

    if args:
        value = ("%s,%s"%(value.strip(CST), ','.join(a.strip(CST) for a in args))).strip(CST)


    try:
        def _out(k, v):
            return output(["%s = %s"%(k, ', '.join(v) if isinstance(v, list) else v )])
        if name is None:
            for varname, v in config:
                _out(varname, v or 'off')
        else:
            if value is not None:
                config[name] = value

            v = config[name]
            _out(name, v)
    except ConfigParser.NoOptionError:
        output(["invalid option."])

def modify_delete(output, songid):
    """ hook for the "delete" command """
    if songid == 'grep':
        return ('/delete?idx=%s'%(i-idx) for idx, i in enumerate(memory['grepped']))
    else:
        return '/delete?idx=%s'%songid

def modify_move(output, songid, where=None):
    """ Hook for the "move" command """
    if where is None:
        infos = get_infos()
        where = int(infos['pls_position'])+1
    if songid == 'grep':
        return ('/move?s=%s&d=%s'%(i, where+idx) for idx, i in enumerate(memory['grepped']))
    else:
        return '/move?s=%s&d=%s'%(songid, where)

def random_command(output, what='artist'):
    """ executes the "random" command
    Fills the playlist with a random artist (or album)
    """
    dbh = config.db_host[0]
    arg = iter_webget('http://%s/db/random?what=%s'%(dbh, what)).next()
    return '/search?%s&host=%s'%(arg, dbh)

def show_random_result(it):
    """ displays the "random" command result """
    uri = modify_show(None)
    return ('-'.join(r.split('|')[1:4]) for r in iter_webget(uri))

def modify_show(output, answers=10):
    """ Hook for the "show" command """
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
    """ Improve the "show" output """
    offs = memory['show_offset']
    now = int(memory.get('pls_position', -1))

    for i, line in enumerate(it):
        idx = offs+i
        yield '%3s %s'%(idx if idx != now else ' >> ', ' | '.join(line.split(' | ')[:4]))

