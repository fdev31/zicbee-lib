# -*- coding: utf-8 -*-
from __future__ import absolute_import, with_statement
__all__ = ['tokens2python', 'parse_string', 'string2python', 'tokens2string']

import re
from zicbee_lib.formats import compact_int, uncompact_int # decodes packed "id" keyword + generates varnames
from zicbee_lib.remote_apis import ASArtist


class VarCounter(object):

    @property
    def varname(self):
        v = self.count
        self.count = v+1
        return "v"+compact_int(v)

    def __enter__(self, *a):
        self.count = 0
        return self

    def __exit__(self, *a):
        pass


class Node(object):

    def __init__(self, name):
        self.name = name

    def __repr__(self, *unused):
        return "%s"%self.name

    python = __repr__

    def isa(self, other):
        return self.__class__ == other.__class__ and self.name == getattr(other, 'name', None)

    def __eq__(self, other):
        return self.name == getattr(other, 'name', None) if other else False


class Not(Node):

    def python(self, cnt):
        return "not"


class Tag(Node):

    def __init__(self, name):
        Node.__init__(self, name)
        self.substr = []

    def __eq__(self, other):
        if not other:
            return False
        return self.name == getattr(other, 'name', None) and self.substr == getattr(other, 'substr', [])

    def __add__(self, other):
        assert isinstance(other, basestring)
        if not self.is_sensitive():
            other = other.lower()
        self.substr.append(other)
        return self

    def from_name(self, name=None):
        return self.__class__(name or self.name)

    def is_sensitive(self):
        return self.name[0].isupper()

    def python(self, cnt):
        name = self.name.strip(':').lower()
        if not self.is_sensitive():
            name += ".lower()"
        prefix, val = self.split_value()
        if prefix == "in":
            return ("%r in %s"%(val, name), {})
        else:
            varname = cnt.varname
            var = {varname: val}
            return ("%s == %s"%(name, varname), var)

    def split_value(self):
        v = self.value
        if v[0] in '<>=':
            if v[1] == '=':
                prefix = v[:2]
                v = v[2:]
            else:
                prefix = v[:1]
                v = v[1:]
                if prefix == '=':
                    prefix = '=='
        else:
            prefix = 'in'
        return (prefix, v)

    @property
    def value(self):
        return (' '.join(self.substr)).strip()

    def __repr__(self):
        if self.value:
            return "%s %s"%(self.name, self.value)
        else:
            return self.name


class NumTag(Tag):

    def is_sensitive(self):
        return True

    def python(self, cnt):
        val = self.value
        name = self.name.strip(':')
        if val[0] in '<>=':
            varname = cnt.varname
            if val[0] == '=':
                expr = ("%s == %s"%(name, varname), {varname: int(val[1:].strip())})
            else:
                if val[1] == '=':
                    expr = ("%s %s %s"%(name, val[:2], varname), {varname: int(val[2:].strip())})
                else:
                    expr = ("%s %s %s"%(name, val[:1], varname), {varname: int(val[1:].strip())})
        else: # default
            a_varname = cnt.varname
            b_varname = cnt.varname
            var = {a_varname: int(val)-1, b_varname: int(val)+1}
            expr = ("%s <= %s <= %s"%(a_varname, name, b_varname), var)
        return expr


class Index(Tag):

    def is_sensitive(self):
        return True

    def python(self, cnt):
        val = self.value
        varname = cnt.varname
        return ("__id__ == %s"%(varname), {varname: uncompact_int(val)})

    @property
    def value(self):
        if len(self.substr) != 1:
            return 'N/A'
        return (' '.join(self.substr)).strip()


class Special(Tag):

    def __eq__(self, other):
        return self.name == getattr(other, 'name', None) if other else False

    def __repr__(self):
        if self.value:
            return "%s %s"%(self.name, self.value)
        else:
            return self.name[:-1]

    def python(self, cnt):
        return '' # Not applicable

# Recognised infos is here:

TAG_RE = re.compile(r'([A-Za-z][a-z_-]*:)')
OP_RE = re.compile(r'(\W|^|(?<!\\))(and|or|!)(\W|$)')
GRP_RE = re.compile(r'(?<!\\)([()])')

OPEN = Node('(')
CLOSE = Node(')')

OR = Node('or')
AND = Node('and')
NOT = Not('!')

ID = Index('id:')
ARTIST = Tag('artist:')
ALBUM = Tag('album:')
TITLE = Tag('title:')
TAG = Tag('tags:')

CS_ARTIST = Tag('Artist:')
CS_ALBUM = Tag('Album:')
CS_TITLE = Tag('Title:')

LENGTH = NumTag('length:')
SCORE = NumTag('score:')

PLAYLIST = Special('pls:')
AUTO = Special('auto:')

OPERATORS = (AND, OR, NOT)
TAGS = (ARTIST, ALBUM, TITLE, LENGTH, SCORE, PLAYLIST, AUTO, ID,
        CS_ARTIST, CS_ALBUM, CS_TITLE)


def parse_string(st):
    # minor sanity check, allowing people to use !artist: syntax (instead of ! artist:)
    st = re.sub('!(\S)', r'! \1', st)
    # handle ()
    st = GRP_RE.split(st)
    for i, sub in enumerate(st):
        for tag in OPEN, CLOSE:
            if tag.name == sub:
                st[i] = tag
                break
    # handle or, and
    #print "* groups:", st
    for i, sub in reversed(list(enumerate(st))):
        if isinstance(sub, basestring):
            subs = OP_RE.split(sub)
            if len(subs) > 1:
                st[i:i+1] = subs
    for i, sub in enumerate(st):
        for tag in OPERATORS:
            if tag.name == sub:
                st[i] = tag
                break
    #print "* operators:", st

    # handle tags
    for i, sub in reversed(list(enumerate(st))):
        if isinstance(sub, basestring):
            subs = TAG_RE.split(sub)
            if len(subs) > 1:
                st[i:i+1] = subs
    for i, sub in enumerate(st):
        for tag in TAGS:
            if tag.name == sub:
                st[i] = tag.from_name(tag.name) # tags are UNIQUE
                break
    #print "* tags:", st
    # cleaning up
    res = []
    infos = {'tag': None}
    for token in st:
        if isinstance(token, basestring) and not token.strip():
            continue
        if isinstance(token, basestring):
            if not infos['tag']:
                res.append(token)
            else:
                infos['tag'] += token
        else:
            if isinstance(token, Tag):
                infos['tag'] = token
            else:
                infos['tag'] = None
            res.append(token)
    # strips eventual pure text objects
    for i, r in enumerate(res):
        if isinstance(r, basestring):
            res[i] = Node(r.strip())
    # Inserts missing operators
    i = enumerate(res)
    prev = None
    prev_prev = None
    while True:
        try:
            idx, tok = i.next()
        except StopIteration:
            break
        if isinstance(prev, Tag) and isinstance(tok, Tag) and not isinstance(tok, Special) and not\
        (isinstance(prev, Special) and (prev_prev is None or isinstance(prev_prev, Special))):
            res[idx:idx] = [AND]
            i.next() # skip the newly added token
        elif prev == CLOSE and tok == OPEN: # ... ) ( ... => ...) or (...
            res[idx:idx] = [OR]
            i.next()
        prev_prev = prev
        prev = tok
    # converts tag:, ( ,str1 , op1, str2, op2, str3, )
    # to: ( ,tag-str1, op1, tag-str2, op2, tag-str3, )
    i = enumerate(res)
    prev = None
    while True:
        try:
            idx, tok = i.next()
        except StopIteration:
            break
        if isinstance(prev, Tag) and tok == OPEN:
            # looks-up the associated ")" while sorting operators and values
            concerned_tag = prev
            start_idx = idx
            count = 1
            operators = []
            values = []
            loc_prev = None
            while True:
                idx, tok = i.next()
                if tok == OPEN:
                    count += 1
                elif tok == CLOSE:
                    count -= 1
                else:
                    prev_is_txt = isinstance(loc_prev, basestring)
                    cur_is_txt = isinstance(tok, basestring)

                    if tok in OPERATORS:
                        operators.append(tok)
                    elif cur_is_txt:
                        if prev_is_txt:
                            loc_prev = "%s %s"%(loc_prev, tok)
                    else:
                        values.append(tok)
                if count == 0:
                    break
                loc_prev = tok
            ops = iter(operators)
            replaces = [OPEN]
            for n in values:
                t = Tag(concerned_tag.name) # naked tag
                t += n.name
                replaces.append(t)
                try:
                    replaces.append(ops.next())
                except StopIteration:
                    continue
            replaces.append(CLOSE)
            res[start_idx-1:idx+1] = replaces
        prev = tok
    if len(res) == 1 and type(res[0]) == Node:
        val = res[0].name
        res = [ARTIST.from_name() + val, OR, ALBUM.from_name() + val, OR, TITLE.from_name() + val]
    return res


def tokens2python(tokens):
    with VarCounter() as vc:
        ret = []
        d = {}
        for tok in tokens:
            r = tok.python(vc)
            if isinstance(r, tuple):
                d.update(r[1])
                ret.append(r[0])
            else:
                ret.append(r)

    return (' '.join(ret), d)


def tokens2string(tokens):
    return ' '.join(str(t) for t in tokens)


def string2python(st):
    toks = parse_string(st)
    if AUTO in toks:
        max_vals = int(toks[toks.index(AUTO)].value or 10)
        it = enumerate(list(toks))
        offset = 0
        while True:
            try:
                i, tok = it.next()
            except StopIteration:
                break
            if tok.name == ARTIST.name:
                ext_list = [OPEN, tok]
                v = tok.value
                if v[0] in '=<>':
                    prefix = v[0]
                    v = v[1:]
                else:
                    prefix = ''
                similar_artists = ASArtist(v).getSimilar()[:max_vals]
                for artist in similar_artists:
                    ext_list.extend((OR, ARTIST.from_name(tok.name)+(prefix+artist[1])))
                ext_list.append(CLOSE)
                toks[i+offset:i+offset+1] = ext_list
                offset += len(ext_list)-1
    return tokens2python(toks)


def _string2python(st):
    return tokens2python(parse_string(st))

if __name__ == '__main__':
    def to(st):
        print "-"*80
        print st
        print string2python(st)[0]
    to("artist: björk or artist:  foobar auto:")
    to("artist: (björk or foobar) auto:")
    to("auto: artist: (björk or foobar)")
    to("auto: 20 artist: (toto or björk or foobar)")
    
    raise SystemExit()
    
    tst_str = [
        'artist: Björk or artist: toto',
        'artist: metallica album: black',
        'artist:(noir or toto)',
        'artist:  ( noir or toto   ) ',
        'something else',
        'artist: the blues bro and (title: sal or title: good)',
        'artist: the blues bro and title:  (sal or good)',
        'artist:toto and(album: rorot or title: za andva ti)',
        'artist:toto and(album: =rorot or title: za andva ti)',
    ]

    print string2python("artist: joe title: sub marine")

    for st in tst_str:
        print "-"*80
        print st
        ps = parse_string(st)
        print ps
        print tokens2python(ps)

    while True:
        line = raw_input('pattern: ')
        ps = parse_string(line)
        print ps
        print tokens2python(ps)
