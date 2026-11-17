"""Read symbols from the installed KiCad libraries (resolving 'extends')."""
import os, copy, functools
from sexp import loads, find, first, Sym
SYMDIR = '/usr/share/kicad/symbols'

@functools.lru_cache(None)
def _lib(lib):
    t = loads(open(os.path.join(SYMDIR, lib + '.kicad_sym')).read())
    return {s[1]: s for s in find(t, 'symbol')}

def get(libid):
    """Return a flattened symbol s-expr named 'Lib:Name' ready for embedding in lib_symbols."""
    lib, name = libid.split(':')
    d = _lib(lib); s = copy.deepcopy(d[name])
    ext = first(s, 'extends')
    if ext:
        base = copy.deepcopy(d[ext[1]])
        props = {p[1]: p for p in find(s, 'property')}
        out = [Sym('symbol'), name]
        for item in base[2:]:
            if isinstance(item, list) and item[0] == 'property':
                out.append(props.pop(item[1], item))
            elif isinstance(item, list) and item[0] == 'symbol':
                item[1] = name + item[1][len(ext[1]):]
                out.append(item)
            else:
                out.append(item)
        for p in props.values():
            out.insert(3, p)
        s = out
    s[1] = lib + ':' + name
    return s

def pins(sym):
    """list of dict(unit, number, name, etype, x, y, angle, length)"""
    res = []
    for sub in find(sym, 'symbol'):
        parts = sub[1].rsplit('_', 2)
        unit, style = int(parts[-2]), int(parts[-1])
        if style > 1:
            continue
        for p in find(sub, 'pin'):
            at = first(p, 'at')
            res.append(dict(unit=unit, number=first(p, 'number')[1], name=first(p, 'name')[1], etype=str(p[1]),
                            x=float(at[1]), y=float(at[2]), angle=float(at[3]) if len(at) > 3 else 0.0,
                            length=float(first(p, 'length')[1]), hide=any(i == 'hide' for i in p)))
    return res

def prop(sym, key):
    for p in find(sym, 'property'):
        if p[1] == key:
            return p[2]
    return ''

if __name__ == '__main__':
    import sys
    for libid in sys.argv[1:]:
        s = get(libid)
        print('##', libid, '| fp:', prop(s, 'Footprint'))
        print('  ' + ' '.join(f"{p['number']}:{p['name']}[{p['etype'][:3]}{'/u%d' % p['unit'] if p['unit'] > 1 else ''}]" for p in sorted(pins(s), key=lambda p: (len(p['number']), p['number']))))
