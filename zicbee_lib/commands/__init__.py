# commands dict: <cmd name>:<request string OR handler_function>, <doc>, [extra dict]
# in request string, you can use two forms: positional or named
# in positional form, you should have as many %s as required parameters, they will be passed in given order
# in named form, you have dict expension for: args (a string containing all arguments separated by a space), db_host, player_host
# if given an handler_function, this is executed to get the request string
#
# In both forms, you should return an uri, if it's a relative prefix, db_host or player_host is chose according to "/db/" pattern presence
# the request result is print on the console

import sys
import thread
from urllib import quote
from functools import partial
from types import GeneratorType
from zicbee_lib.core import memory, config, iter_webget
from .command_get import get_last_search
from .command_misc import complete_alias, complete_set, hook_next, hook_prev
from .command_misc import inject_playlist, modify_move, modify_show, set_alias, modify_delete
from .command_misc import set_variables, tidy_show, apply_grep_pattern, set_grep_pattern

commands = {
#        'freeze': (dump_home, 'Dumps a minimalistic python environment'),
        'play': ('/search?host=%(db_host)s&pattern=%(args)s', 'Play a song', dict(threaded=True)),
        'search': ('/db/search?fmt=txt&pattern=%(args)s', 'Query the database', dict(uri_hook=partial(memory.__setitem__, 'last_search'))),
        'as': (partial(inject_playlist, symbol='>'), 'Appends last search to current playlist'),
        'is': (partial(inject_playlist, symbol='+'), 'Inserts last search to current playlist (after the current song)'),
        'm3u': ('/db/search?fmt=m3u&pattern=%(args)s', 'Query the database, request m3u format'),
        'version': ('/db/version', 'Show DB version'),
        'db_tag': ('/db/tag/%s/%s', 'Associates a tag to a song (params: Id, Tag)'),
        'artists': ('/db/artists', 'Show list of artists'),
        'albums': ('/db/albums', 'Show list of albums'),
        'genres': ('/db/genres', 'Show list of genres'),
        'kill': ('/db/kill', 'Power down'),
        'get': (get_last_search, 'Download results of last search or play command'),
        'set': (set_variables, 'List or set application variables, use "off" or "no" to disable an option.', dict(complete=complete_set)),
        'alias': (set_alias, 'List or set hosts aliases', dict(complete=complete_alias)),
        # complete_set': (lambda: [v[0] for v in config], lambda: set(v[1] for v in config))
        'stfu': ('/close', 'Closes player'),
        'pause': ('/pause', 'Toggles pause'),
        'next': (hook_next, 'Zap current track'),
        'prev': (hook_prev, 'Go back to last song'),
        'infos': ('/infos', 'Display player status'),
        'meta': ('/db/infos?id=%s', 'Display metadatas of a song giving his id'),
        'delete': (modify_delete, "Remove player's song at given position, if not given a position, removes a named playlist"),
        'move': (modify_move, "Move a song from a position to another\n\t(if none given, adds just next current song)"),
        'swap': ('/swap?i1=%s&i2=%s', "Swap two songs"),
        'append': ('/append?name=%s', "Append a named playlist to the current playlist"),
        'load': ('/copy?name=%s', "Loads the specified playlist"),
        'inject': ('/inject?name=%s', "Inserts the specified playlist to current one"),
        'save': ('/save?name=%s', "Saves the current playlist to given name"),
        'volume': ('/volume?val=%s', "Changes the volume"),
        'playlist': ('/playlist', "Shows the entire playlist (Might be SLOW!)"),
        'grep': (set_grep_pattern, "Grep (search for a pattern) in the playlist", dict(display_modifier=apply_grep_pattern)),
        'playlists': ('/playlists', "Shows all your saved playlists"),
        'show': (modify_show, "Shows N elements after the current song,\n\tif you set a slice (ex.: show 3:10) then it shows the selected range.", dict(display_modifier=tidy_show)),
        'guess': ('/guess/%(args)s', "Tells if you are right (blind mode)"),
        'shuffle': ('/shuffle', "Shuffles the playlist"),
        'tag': ('/tag/%s', "Set a tag on current song"),
        'rate': ('/rate/%s', "Rate current song"),
        'clear': ('/clear', "Flushes the playlist"),
#       ' seek': ('/seek/%s', "Seeks on current song"),
        }

# execution code

possible_commands = commands.keys()
possible_commands.append('help')
def write_lines(lines):
    sys.stdout.writelines(l+'\n' for l in lines)

def execute(name=None, line=None, output=write_lines):
    if line is None:
        args = name.split()
        name = args.pop(0)
    else:
        args = line.split()

    if name not in possible_commands:
        # abbreviations support
        possible_keys = [k for k in possible_commands if k.startswith(name)]
        if len(possible_keys) == 1:
            name = possible_keys[0]
        elif not possible_keys:
            if name in ('EOF', 'exit', 'bye'):
                raise SystemExit
            print 'Unknwown command: "%s"'%name
            return
        elif name not in possible_keys:
            print "Ambiguous: %s"%(', '.join(possible_keys))
            return

    if name == 'help':
        if args:
            try:
                print commands[args[0]][1]
            except KeyError:
                if args[0] not in commands:
                    print '"%s" is not recognised.'%args[0]
                else:
                    print "No help for that command."
            finally:
                return

        for cmd, infos in commands.iteritems():
            print "%s : %s"%(cmd, infos[1])
        print """
                 Syntax quick sheet
    Tags:
      * id (compact style) * genre * artist * album * title * track
      * filename * score * tags * length

    Playlists (only with play command):
        use "pls: <name>" to store the request as "<name>"
        add ">" prefix to name to append instead of replacing
        "+" prefix inserts just next
        "#" = special name to point "current" playlist

    Numerics (length, track, score) have rich operators, default is "==" for equality
        length: >= 60*5
        length: < 60*3+30
        length: >100
        score: 5
        """

        return

    try:
        pat, doc = commands[name]
        extras = None
    except ValueError:
        pat, doc, extras = commands[name]

    if callable(pat):
        pat = pat(output, *args)
        if not pat:
            return

    args = [quote(a) for a in args]

    if not isinstance(pat, (list, tuple, GeneratorType)):
        pat = [pat]

    for pattern in pat:
        if '%s' in pattern:
            expansion = tuple(args)
        else:
            expansion = dict(args = '%20'.join(args), db_host=config['db_host'], player_host=config['player_host'])
        try:
            uri = pattern%expansion
        except Exception, e:
            print "Invalid arguments: %s"%e
        else:
            if extras and extras.get('uri_hook'):
                extras['uri_hook'](uri)
            r = iter_webget(uri)
            if r:
                def _finish(r, out=None):
                    if extras and extras.get('display_modifier'):
                        r = extras['display_modifier'](r)
                    if out:
                        out(r)
                    else:
                        for l in r:
                            pass
                if extras and extras.get('threaded', False):
                    thread.start_new(_finish, (r,))
                else:
                    _finish(r, output)

def _safe_execute(what, output, *args, **kw):
    i = what(*args, **kw)
    if hasattr(i, 'next'):
        output(i)

