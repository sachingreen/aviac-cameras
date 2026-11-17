"""Minimal KiCad s-expression reader/writer."""
import re
_tok = re.compile(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+')

class Sym(str):
    pass

def loads(text):
    stack, cur = [], []
    for m in _tok.finditer(text):
        t = m.group(0)
        if t == '(':
            stack.append(cur); cur = []
        elif t == ')':
            done = cur; cur = stack.pop(); cur.append(done)
        elif t[0] == '"':
            cur.append(t[1:-1].replace('\\"', '"').replace('\\\\', '\\').replace('\\n', '\n'))
        else:
            cur.append(Sym(t))
    return cur[0]

def q(s):
    return '"' + str(s).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'

def dumps(x, ind=0):
    if isinstance(x, list):
        simple = all(not isinstance(i, list) for i in x)
        if simple:
            return '(' + ' '.join(dumps(i) for i in x) + ')'
        pad = '\n' + '\t' * (ind + 1)
        out = '(' + dumps(x[0])
        for i in x[1:]:
            out += (pad if isinstance(i, list) else ' ') + dumps(i, ind + 1)
        return out + '\n' + '\t' * ind + ')'
    if isinstance(x, Sym):
        return str(x)
    if isinstance(x, str):
        return q(x)
    if isinstance(x, float):
        s = f'{x:.4f}'.rstrip('0').rstrip('.')
        return s if s not in ('-0', '') else '0'
    return str(x)

def find(x, key):
    return [i for i in x if isinstance(i, list) and i and i[0] == key]

def first(x, key):
    r = find(x, key)
    return r[0] if r else None
