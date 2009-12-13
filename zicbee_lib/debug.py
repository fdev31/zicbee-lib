__all__ = ['DEBUG', 'debug_enabled', 'log', 'nop', 'set_trace']
import os
import logging
import traceback
from logging import getLogger
from zicbee_lib.config import config

log = getLogger('zicbee')
def nop(*args):
    """ Don't do anything """
    return

try:
    # tells if debug is enabled or not
    debug_enabled = (str(config.debug).lower()[:1] not in 'fn') if config.debug else False
    # disable if "false" or "no"
except:
    debug_enabled = False

#try:
#    from pudb import set_trace as _strace
#except ImportError:
from pdb import set_trace as _strace

def set_trace():
    """ Breaks into a debugger prompt, should run pdb. """
    try:
        _strace()
    except :
        print "Exception in stread, can't step into!"

# environment overrides
if not debug_enabled and os.environ.get('DEBUG'):
    debug_enabled = os.environ['DEBUG'] != '0'

def traced(fn):
    """ Decorator that calls :ref:DEBUG in case of exception """
    def _get_decorator(decorated):
        def _decorator(*args, **kw):
            try:
                return decorated(*args, **kw)
            except:
                DEBUG()
        return _decorator
    return _get_decorator(fn)

def DEBUG(trace=True):
    """ Prints a traceback + exception,
    optionally breaks into a debugger.


    Args:
        trace (bool): if True, breaks into a debugger after showing infos.

    Returns:
        None.
    """
    traceback.print_stack()
    traceback.print_exc()
    if trace:
        set_trace()


if debug_enabled:
    default_formatter = logging.Formatter('[%(threadName)s %(relativeCreated)d] %(module)s %(funcName)s:%(lineno)s %(message)s')
    try:
        LOGFILENAME='zicbee.log'
        file(LOGFILENAME, 'a').close()
    except Exception:
        LOGFILENAME=None

    handlers = [ logging.StreamHandler() ] # first is stderr
    if LOGFILENAME:
        handlers.append( logging.FileHandler(LOGFILENAME) )

    # add handlers
    for h in handlers:
        log.addHandler(h)
        h.setFormatter( default_formatter )

    try:
        val = int(os.environ.get('DEBUG', 1))*10
    except ValueError:
        val = logging.DEBUG

    log.setLevel(val)
else:
    globals()['DEBUG'] = nop
    log.setLevel(logging.FATAL)

