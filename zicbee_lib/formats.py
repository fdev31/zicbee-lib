""" It's all about formats, (de)serialisation, filename cleaning, duration display, help-retrieval, etc... """
__all__ = ['jdump', 'jload', 'clean_path', 'safe_path', 'duration_tidy', 'get_help_from_func', 'dump_data_as_text', 'get_index_or_slice',
'compact_int', 'uncompact_int']

import inspect
import itertools
from types import GeneratorType
import os
from os.path import abspath, expanduser, expandvars
from zicbee_lib.debug import log

# Filename path cleaner
def clean_path(path):
    """ Expands a path with variables & user alias


    :param str path: a path containing shell-like shortcuts
    :returns: A normalized path.
    :rtype: str
    """
    return expanduser(abspath(expandvars(path)))

def safe_path(path):
    """ Avoids path separators in the path


    :param str path: the possible unsafe path
    :returns: A string without separator
    :rtype: str
    """
    return path.replace(os.path.sep, ' ')

# int (de)compacter [int <> small str convertors]
# convert to base62...
#: conversion base
base = 62
#: available characters
chars = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']

def compact_int(ival):
    """ Makes an int compact


    :param int ival: the integer value you want to shorten
    :returns: A string equivalent to the integer but with a more compact representation
    :rtype: str
    """
    result = []
    rest = ival
    b = base
    while True:
        int_part, rest = divmod(rest, b)
        result.append(chars[rest])
        if not int_part:
            break
        rest = int_part
    result = "".join(reversed(result))
    log.info('compact(%s) = %s', ival, result)
    return result

def uncompact_int(str_val):
    """ Makes an int from a compact string


    :param str str_val: The string representing a compact integer value
    :returns: The integer value
    :rtype: int
    """
    # int(x, base) not used because it's limited to base 36
    unit = 1
    result = 0
    for char in reversed(str_val):
        result += chars.index(char) * unit
        unit *= base
    log.info('uncompact(%s) = %s', str_val, result)
    return result

def get_index_or_slice(val):
    """ Converts a string representing an index into an int or a slice


    :param str val: string like ``4`` or ``1:10``
    :raises:  :exc:`ValueError`
    :returns: :keyword:`int` or :keyword:`slice` corresponding to the given string
    """
    try:
        i = int(val)
    except ValueError:
        if ':' in val:
            vals = [int(x) if x else 0 for x in val.split(':')]
            if vals[1] > 0:
                vals[1] += 1
            i = slice(*vals)
        else:
            raise
    return i

################################################################################

#
# Try to get the most performant json backend
#
# cjson:
# 10 loops, best of 3: 226 msec per loop
# simplejson:
# 1 loops, best of 3: 10.3 sec per loop
# demjson:
# 1 loops, best of 3: 65.2 sec per loop
#

json_engine = None
try:
    from json import dumps as jdump, loads as jload
    json_engine = "python's built-in"
except ImportError:
    try:
        from cjson import encode as jdump, decode as jload
        json_engine = 'cjson'
    except ImportError:
        try:
            from simplejson import dumps as jdump, loads as jload
            json_engine = 'simplejson'
        except ImportError:
            from demjson import encode as jdump, decode as jload
            json_engine = 'demjson'

log.info("using %s engine."%json_engine)
################################################################################

def dump_data_as_text(d, format):
    """ Dumps simple types (dict, iterable, float, int, unicode)
    as: json or plain text (compromise between human readable and parsable form)

    :param str format: value in "html", "json" or "txt"
    :returns: an iterator returning text
    """
    if format == "json":
        if isinstance(d, GeneratorType):
            d = list(d)
        yield jdump(d)
    elif format == "html":
        yield "<html><body>"
        if isinstance(d, dict):
            for k, v in d.iteritems():
                yield '<b>%s</b>: %s<br/>\n'%(k, v)
        else:
            # assume iterable
            yield "<ul>"
            for elt in d:
                yield "<li>%r</li>\n"%elt
            yield "</ul>"
        yield "</body></html>"
    else: # assume "txt"
        if isinstance(d, dict):
            for k, v in d.iteritems():
                yield '%s: %s\n'%(k, v)
        else:
            # assume iterable
            for elt in d:
                if isinstance(elt, (list, tuple)):
                    yield " | ".join(str(e) for e in elt) + "\n"
                else:
                    yield "%s\n"%elt

################################################################################

_plur = lambda val: 's' if val > 1 else ''

def duration_tidy(orig):
    """ Pretty formats an integer duration


    :param orig: the value you want to pretty-print
    :type orig: int or float
    :returns: A string representing the given duration
    :rtype: :keyword:`str`
    """
    minutes, seconds = divmod(orig, 60)
    if minutes > 60:
        hours, minutes = divmod(minutes, 60)
        if hours > 24:
            days, hours = divmod(hours, 24)
            return '%d day%s, %d hour%s %d min %02.1fs.'%(days, _plur(days), hours, _plur(hours), minutes, seconds)
        else:
            return '%d hour%s %d min %02.1fs.'%(hours, 's' if hours>1 else '', minutes, seconds)
    else:
        return '%d min %02.1fs.'%(minutes, seconds)
    if minutes > 60:
        hours = int(minutes/60)
        minutes -= hours*60
        if hours > 24:
            days = int(hours/24)
            hours -= days*24
            return '%d days, %d:%d.%ds.'%(days, hours, minutes, seconds)
        return '%d:%d.%ds.'%(hours, minutes, seconds)
    return '%d.%02ds.'%(minutes, seconds)

################################################################################
# documents a function automatically

def get_help_from_func(cmd):
    """
    Returns a pretty-string from a function.

    :arg callable cmd: the fonction/method you want to get documentation from
    :Returns: (:keyword:`str` tidy doc, :keyword:`bool` is_remote) from a function
    :rtype: :keyword:`tuple`
    """
    arg_names, not_used, neither, dflt_values = inspect.getargspec(cmd)
    is_remote = any(h for h in arg_names if h.startswith('host') or h.endswith('host'))

    if cmd.__doc__:
        if dflt_values is None:
            dflt_values = []
        else:
            dflt_values = list(dflt_values)

        # Ensure they have the same length
        if len(dflt_values) < len(arg_names):
            dflt_values = [None] * (len(dflt_values) - len(arg_names))

        doc = '::'.join('%s%s'%(arg_name, '%s'%('='+str(arg_val) if arg_val is not None else '')) for arg_name, arg_val in itertools.imap(None, arg_names, dflt_values))

        return ("%s\n%s\n"%(
            ("%s[::%s]"%(cmd.func_name[3:], doc) if len(doc) > 1 else cmd.func_name[3:]), # title
            '\n'.join('   %s'%l for l in cmd.__doc__.split('\n') if l.strip()), # body
        ), is_remote)
    else:
        return (cmd.func_name[3:], is_remote)

