# Extraction : fonctions, tables lues (1D/2D/constantes), positions sur les axes, variables RAM lues/écrites
# (appelé par preparer.py ; usage direct : python3 -I base_tables.py dis.pkl db.pkl)
import pickle, re, sys, collections, json
D = pickle.load(open(sys.argv[1], 'rb')); A = sorted(D)
A5 = 0xE5770
CAL = (0x55000, 0x5D000)

def norm(o):
    def f(m):
        v = int(m.group(1), 16)
        if A5 <= v < 0xF0000: return f'${v - A5:x}(a5)'
        return m.group(0)
    return re.sub(r'\$([0-9a-f]{5,6})\.l', f, o)

I = []
for a in A:
    s, m, o = D[a]
    I.append((a, m, norm(o)))
idx = {a: i for i, (a, _, _) in enumerate(I)}

def ops(o):
    return [x.strip() for x in re.split(r',(?![^(]*\))', o)] if o else []

# limites de fonctions : cibles jsr/bsr dans le code
targets = set()
for a, m, o in I:
    if m == 'jsr' or m.startswith('bsr'):
        mm = re.fullmatch(r'\$([0-9a-f]+)(\.l)?', o)
        if mm: targets.add(int(mm.group(1), 16))
# + adresses suivant un rts/bra qui commencent par movem/link (fonctions appelées par pointeur)
for i, (a, m, o) in enumerate(I[:-1]):
    if m in ('rts',) and I[i + 1][1] in ('movem.l', 'link.w', 'move.l') :
        targets.add(I[i + 1][0])
T = sorted(t for t in targets if t in idx)
import bisect
def func_of(a):
    k = bisect.bisect_right(T, a) - 1
    return T[k] if k >= 0 else 0

def is_cal(v): return CAL[0] <= v < CAL[1]
def calref(x):
    mm = re.fullmatch(r'#?\$([0-9a-f]+)(\.l)?', x)
    if mm:
        v = int(mm.group(1), 16)
        if is_cal(v): return v
    return None

ramre = re.compile(r'\$([0-9a-f]+)\(a5\)')

# positions sur les axes
pos = {}
for i, (a, m, o) in enumerate(I):
    if m in ('pea.l', 'move.l') :
        op = ops(o)
        ax = calref(op[0]) if op else None
        if ax is None or (m == 'move.l' and op[-1] != '-(a7)'): continue
        cnt = inp = None
        for j in range(i - 1, max(i - 4, 0), -1):
            mm, oo = I[j][1], I[j][2]
            if mm == 'move.w' and oo.endswith('-(a7)'):
                src = oo.rsplit(',', 1)[0]
                if src.startswith('#'): cnt = int(src.strip('#$'), 16)
                elif inp is None: inp = src
        if cnt is None: continue
        for j in range(i + 1, min(i + 25, len(I))):
            mm, oo = I[j][1], I[j][2]
            if mm == 'move.w' and oo.startswith('d0, $') and oo.endswith('(a5)'):
                pos.setdefault(oo[4:], (ax, cnt + 1, inp, a)); break
            if mm in ('jsr', 'rts'): break
# copies de positions
for a, m, o in I:
    if m == 'move.w':
        op = ops(o)
        if len(op) == 2 and op[0] in pos and op[1].endswith('(a5)') and op[1] not in pos:
            pos[op[1]] = pos[op[0]]

def nextstore(i, lim=12):
    reg = 'd0'
    for j in range(i + 1, min(i + lim, len(I))):
        mm, oo = I[j][1], I[j][2]
        op = ops(oo)
        if mm.startswith('move') and len(op) == 2 and op[0] == reg:
            if op[1].endswith('(a5)'): return op[1]
            if re.fullmatch(r'd[0-7]', op[1]): reg = op[1]; continue
        if mm in ('jsr', 'rts') or mm.startswith('b'): break
    return reg

lookups = []   # (addr, func, kind, table, posinfo..., out)
for i, (a, m, o) in enumerate(I):
    if m == 'fsmove' and I[i - 1][2].startswith('$4(a7), d0') and I[i - 2][2] == '(a7), a0':
        # 1D inline : push pos ; push table
        tb = ps = None
        for j in range(i - 3, max(i - 6, 0), -1):
            mm, oo = I[j][1], I[j][2]
            op = ops(oo)
            if tb is None and (mm == 'pea.l' or (mm == 'move.l' and op[-1] == '-(a7)')):
                tb = calref(op[0]) if mm == 'move.l' else calref(op[0])
            elif tb is not None and mm == 'move.w' and op[-1] == '-(a7)':
                ps = op[0]; break
        if tb: lookups.append((a, func_of(a), '1D', tb, ps, None, nextstore(i)))
    if m == 'jsr' and o in ('$49a6c.l', '$49aba.l'):
        st = []
        for j in range(i - 1, max(i - 10, 0), -1):
            mm, oo = I[j][1], I[j][2]
            if mm == 'pea.l': st.append(oo)
            elif oo.endswith('-(a7)') and mm.startswith('move'): st.append(oo.rsplit(',', 1)[0])
            if len(st) == 4: break
        if len(st) == 4:
            tb, x, y, stride = st
            lookups.append((a, func_of(a), '2D' + ('s' if o == '$49aba.l' else 'u'), calref(tb) or tb, y, x, nextstore(i)))

scal = collections.defaultdict(set)   # const -> funcs
fn_reads = collections.defaultdict(set); fn_writes = collections.defaultdict(set)
fn_scal = collections.defaultdict(set)
for a, m, o in I:
    f = func_of(a)
    op = ops(o)
    if m in ('pea.l',): continue
    for k, x in enumerate(op):
        v = None
        mm = re.fullmatch(r'\$([0-9a-f]+)\.l', x)
        if mm and is_cal(int(mm.group(1), 16)): v = int(mm.group(1), 16)
        if v: scal[v].add(f); fn_scal[f].add(v)
        for r in ramre.findall(x):
            if k == len(op) - 1 and len(op) == 2 and not m.startswith(('cmp', 'tst', 'btst')):
                fn_writes[f].add(r)
            else:
                fn_reads[f].add(r)
    if len(op) == 1 and m.startswith(('clr', 'st', 'sf', 'neg', 'not', 'addq', 'subq')):
        for r in ramre.findall(op[0]): fn_writes[f].add(r)

out = dict(funcs=T, pos={k: list(v) for k, v in pos.items()}, lookups=lookups,
           scal={hex(k): sorted(v) for k, v in scal.items()},
           reads={f: sorted(v) for f, v in fn_reads.items()}, writes={f: sorted(v) for f, v in fn_writes.items()},
           fscal={f: sorted(v) for f, v in fn_scal.items()})
pickle.dump(out, open(sys.argv[2], 'wb'))
print(len(T), 'fonctions', len(lookups), 'lookups', len(scal), 'constantes', len(pos), 'positions')
