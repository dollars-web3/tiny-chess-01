"""Shrink engine.py for the 4 KiB packed cap without changing behaviour:
strip comments/docstrings, squeeze PST table spacing, rename long identifiers,
re-encode PST tables as base-62 strings. Behaviour is verified afterwards by
the perft/tactics tests (the packed output must play identically).
"""
import ast, re, sys

path = sys.argv[1]
src = open(path).read()

# sanity: '#' must never sit inside a string literal, or the naive strip breaks
for ln in src.split('\n'):
    h = ln.find('#')
    if h >= 0:
        pre = ln[:h]
        assert pre.count("'") % 2 == 0 and pre.count('"') % 2 == 0, ln

# 1) drop docstrings (module/function level string expressions)
tree = ast.parse(src)
drop = []
for node in ast.walk(tree):
    if isinstance(node, (ast.Module, ast.FunctionDef)):
        body = node.body
        if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                and isinstance(body[0].value.value, str):
            drop.append((body[0].lineno, body[0].end_lineno))
lines = src.split('\n')
for a, b in sorted(drop, reverse=True):
    del lines[a - 1:b]

# 2) strip comments line-wise, tidy blanks
out = []
for ln in lines:
    h = ln.find('#')
    if h >= 0:
        ln = ln[:h]
    out.append(ln.rstrip())
src = '\n'.join(ln for ln in out if ln.strip())

# 3) squeeze spaces after commas inside the PST dict literals
def find_block(s, name):
    i = s.index(name + ' = ')
    j = s.index('{', i)
    depth = 0
    for k in range(j, len(s)):
        if s[k] == '{': depth += 1
        elif s[k] == '}':
            depth -= 1
            if depth == 0:
                return i, k + 1, s[j:k + 1]
    raise ValueError(name)

for name in ('PST', 'PSTE'):
    a, b, text = find_block(src, name)
    src = src[:a] + src[a:b].replace(', ', ',') + src[b:]

# 4) rename long identifiers (word-boundary, longest first)
ren = {
    'choose_moves': 'chm', 'order_moves': 'omv', 'gen_moves': 'gmv',
    'parse_fen': 'pfn', 'parse_uci': 'puc', 'to_uci': 'tuc', 'sq_name': 'sqn',
    'evaluate': 'evl', 'attacked': 'atk', 'unmake': 'umk', 'qsearch': 'qs',
    'search': 'sr', 'make': 'mak', 'post': 'pst',
    'killers': 'klr', 'history': 'hst', 'nodes': 'nds', 'abort': 'abt',
    'PSTE': 'PE', 'PST': 'PT', 'VALE': 'VE', 'VAL': 'V', 'MATE': 'MT',
    'CAP': 'CP', 'Pos': 'Ps', 'king_hit': 'kh',
}
for old, new in sorted(ren.items(), key=lambda kv: -len(kv[0])):
    src = re.sub(r'\b' + old + r'\b', new, src)

# 5) encode PST/PT tables as one char per value (all values are multiples of 5
#    in [-50, 55]; char index - 10, times 5). Runs after the renames, so the
#    tables are named PT / PE here.
A5 = 'abcdefghijklmnopqrstuv'
def enc5(vals):
    assert len(vals) == 64 and all(v % 5 == 0 and -50 <= v <= 55 for v in vals)
    return ''.join(A5[v // 5 + 10] for v in vals)

for name in ('PT', 'PE'):
    a, b, text = find_block(src, name)
    val = ast.literal_eval(text)
    rep = name + ' = {' + ','.join(str(k) + ':_t("' + enc5(list(v)) + '")' for k, v in sorted(val.items())) + '}'
    src = src[:a] + rep + src[b:]

helper = ('A5 = "' + A5 + '"\n'
          'def _t(s):\n  return [(A5.index(c) - 10) * 5 for c in s]\n')
first_nl = src.index('\n')
src = src[:first_nl + 1] + helper + src[first_nl + 1:]

# 6) halve indentation (4-space levels -> 2-space levels; no multi-line
#    strings remain after the docstring strip, so leading-space mapping is safe)
def halve(ln):
    n = len(ln) - len(ln.lstrip(' '))
    return ' ' * (n // 2) + ln[n:]
src = '\n'.join(halve(ln) for ln in src.split('\n'))

open(path, 'w').write(src)
print('minified bytes:', len(src.encode()))
