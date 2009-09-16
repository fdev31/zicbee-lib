from functools import partial
from .utils import memory
from .command_get import get_last_search
from .command_misc import *

# commands dict: <cmd name>:<request string OR handler_function>, <doc>, [extra dict]
# in request string, you can use two forms: positional or named
# in positional form, you should have as many %s as required parameters, they will be passed in given order
# in named form, you have dict expension for: args (a string containing all arguments separated by a space), db_host, player_host
# if given an handler_function, this is executed to get the request string
#
# In both forms, you should return an uri, if it's a relative prefix, db_host or player_host is chose according to "/db/" pattern presence
# the request result is print on the console
# TODO:
# in extra parameters, allow definition of a display_function

commands = {
        'play': ('/search?host=%(db_host)s&pattern=%(args)s', 'Play a song'),
        'search': ('/db/search?fmt=txt&pattern=%(args)s', 'Query the database', dict(uri_hook=partial(memory.__setitem__, 'last_search'))),
        'as': (partial(inject_playlist, '+'), 'Appends last search to current playlist'),
        'is': (partial(inject_playlist, '>'), 'Inserts last search to current playlist (after the current song)'),
        'm3u': ('/db/search?fmt=m3u&pattern=%(args)s', 'Query the database, request m3u format'),
        'version': ('/db/version', 'Show DB version'),
        'db_tag': ('/db/tag/%s/%s', 'Associates a tag to a song (params: Id, Tag)'),
        'artists': ('/db/artists', 'Show list of artists'),
        'albums': ('/db/albums', 'Show list of albums'),
        'genres': ('/db/genres', 'Show list of genres'),
        'kill': ('/db/kill', 'Power down'),
        'get': (get_last_search, 'Download results of last search or play command'),
        'set': (set_variables, 'List or set application variables'),
        # complete_set': (lambda: [v[0] for v in config_list()], lambda: set(v[1] for v in config_list()))
        'stfu': ('/close', 'Closes player'),
        'pause': ('/pause', 'Toggles pause'),
        'next': (hook_next, 'Zap current track'),
        'prev': (hook_prev, 'Go back to last song'),
        'infos': ('/infos', 'Display player status'),
        'meta': ('/db/infos?id=%s', 'Display metadatas of a song giving his id'),
        'delete': ('/delete?idx=%s', "Remove player's song at given position"),
        'move': (modify_move, "Move a song from a position to another\n\t(if none given, adds just next current song)"),
        'swap': ('/swap?i1=%s&i2=%s', "Swap two songs"),
        'append': ('/append?name=%s', "Append a named playlist to the current playlist"),
        'save': ('/copy?name=%s', "Save the current playlist as given name"),
        'volume': ('/volume?val=%s', "Changes the volume"),
        'playlist': ('/playlist', "Shows the entire playlist (Might be SLOW!)"),
        'show': (modify_show, "Shows N elements after the current song,\n\tyou can optionally gives an alternative offset.", dict(display_modifier=tidy_show)),
        'guess': ('/guess/%(args)s', "Tells if you are right (blind mode)"),
        'shuffle': ('/shuffle', "Shuffles the playlist"),
        'tag': ('/tag/%s', "Set a tag on current song"),
        'rate': ('/rate/%s', "Rate current song"),
        'clear': ('/clear', "Flushes the playlist"),
#       ' seek': ('/seek/%s', "Seeks on current song"),
        }
