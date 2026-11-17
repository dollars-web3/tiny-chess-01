# tiny-chess-01 entry: a compact chess engine (negamax + alpha-beta, quiescence,
# transposition table, tapered PST eval) with a driver for the make.fun env.
# Deterministic: the search stops on a fixed node budget, never on a clock.
import os, sys, json, random
from urllib.request import Request, urlopen
from urllib.error import HTTPError

# ---------- board: 0x88, pieces +1..+6 = P N B R Q K (white), negative = black
KN = (33, 31, 18, 14, -14, -18, -31, -33)
KG = (16, -16, 1, -1, 17, 15, -15, -17)
BD = (17, 15, -15, -17)
RD = (16, -16, 1, -1)
VAL = (0, 100, 320, 330, 500, 900, 0)
VALE = (0, 120, 320, 330, 500, 900, 0)
PST = {
1: (0,0,0,0,0,0,0,0, 50,50,50,50,50,50,50,50, 10,10,20,30,30,20,10,10, 5,5,10,25,25,10,5,5, 0,0,0,20,20,0,0,0, 5,-5,-10,0,0,-10,-5,5, 5,10,10,-20,-20,10,10,5, 0,0,0,0,0,0,0,0),
2: (-50,-40,-30,-30,-30,-30,-40,-50, -40,-20,0,0,0,0,-20,-40, -30,0,10,15,15,10,0,-30, -30,5,15,20,20,15,5,-30, -30,0,15,20,20,15,0,-30, -30,5,10,15,15,10,5,-30, -40,-20,0,5,5,0,-20,-40, -50,-40,-30,-30,-30,-30,-40,-50),
3: (-20,-10,-10,-10,-10,-10,-10,-20, -10,0,0,0,0,0,0,-10, -10,0,5,10,10,5,0,-10, -10,5,5,10,10,5,5,-10, -10,0,10,10,10,10,0,-10, -10,10,10,10,10,10,10,-10, -10,5,0,0,0,0,5,-10, -20,-10,-10,-10,-10,-10,-10,-20),
4: (0,0,0,0,0,0,0,0, 5,10,10,10,10,10,10,5, -5,0,0,0,0,0,0,-5, -5,0,0,0,0,0,0,-5, -5,0,0,0,0,0,0,-5, -5,0,0,0,0,0,0,-5, -5,0,0,0,0,0,0,-5, 0,0,0,5,5,0,0,0),
5: (-20,-10,-10,-5,-5,-10,-10,-20, -10,0,0,0,0,0,0,-10, -10,0,5,5,5,5,0,-10, -5,0,5,5,5,5,0,-5, 0,0,5,5,5,5,0,-5, -10,5,5,5,5,5,0,-10, -10,0,5,0,0,0,0,-10, -20,-10,-10,-5,-5,-10,-10,-20),
6: (-30,-40,-40,-50,-50,-40,-40,-30, -30,-40,-40,-50,-50,-40,-40,-30, -30,-40,-40,-50,-50,-40,-40,-30, -30,-40,-40,-50,-50,-40,-40,-30, -20,-30,-30,-40,-40,-30,-30,-20, -10,-20,-20,-20,-20,-20,-20,-10, 20,20,0,0,0,0,20,20, 20,30,10,0,0,10,30,20),
}
PSTE = {
1: (0,0,0,0,0,0,0,0, 35,35,35,35,35,35,35,35, 25,25,25,25,25,25,25,25, 15,15,15,15,15,15,15,15, 8,8,8,8,8,8,8,8, 0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0),
6: (-50,-40,-30,-20,-20,-30,-40,-50, -30,-20,-10,0,0,-10,-20,-30, -30,-10,20,30,30,20,-10,-30, -30,-10,30,40,40,30,-10,-30, -30,-10,30,40,40,30,-10,-30, -30,-10,20,30,30,20,-10,-30, -30,-30,0,0,0,0,-30,-30, -50,-30,-30,-30,-30,-30,-30,-50),
}
_r = random.Random(20261117)
ZK = [[_r.getrandbits(64) for _ in range(128)] for _ in range(13)]
ZC = [_r.getrandbits(64) for _ in range(16)]
ZE = [_r.getrandbits(64) for _ in range(8)]
ZS = _r.getrandbits(64)
MATE = 100000
CAP = 30000

class Pos:
    __slots__ = ('b', 'side', 'cast', 'ep', 'half', 'h', 'k', 'pl')
    def __init__(self):
        self.b = [0] * 128
        self.side = 1; self.cast = 0; self.ep = -1; self.half = 0; self.h = 0
        self.k = [-1, -1]; self.pl = []

def parse_fen(fen):
    p = Pos()
    parts = fen.split()
    rows = parts[0].split('/')
    mp = {'p': 1, 'n': 2, 'b': 3, 'r': 4, 'q': 5, 'k': 6}
    for i, row in enumerate(rows):
        rank = 7 - i; f = 0
        for ch in row:
            if ch.isdigit(): f += int(ch)
            else:
                v = mp[ch.lower()]
                p.b[rank * 16 + f] = v if ch.isupper() else -v
                p.pl.append(rank * 16 + f)
                if v == 6: p.k[0 if ch.isupper() else 1] = rank * 16 + f
                f += 1
    p.side = 1 if len(parts) < 2 or parts[1] == 'w' else -1
    cast = parts[2] if len(parts) > 2 else '-'
    p.cast = (('K' in cast) * 1) | (('Q' in cast) * 2) | (('k' in cast) * 4) | (('q' in cast) * 8)
    if len(parts) > 3 and parts[3] != '-':
        p.ep = (int(parts[3][1]) - 1) * 16 + (ord(parts[3][0]) - 97)
    if len(parts) > 4: p.half = int(parts[4])
    h = 0
    for s in range(128):
        v = p.b[s]
        if v: h ^= ZK[v + 6][s]
    h ^= ZC[p.cast]
    if p.ep >= 0: h ^= ZE[p.ep & 7]
    if p.side < 0: h ^= ZS
    p.h = h
    return p

def attacked(p, sq, by):
    b = p.b
    if by > 0:
        for d in (-15, -17):
            t = sq + d
            if not (t & 0x88) and b[t] == 1: return True
    else:
        for d in (15, 17):
            t = sq + d
            if not (t & 0x88) and b[t] == -1: return True
    for d in KN:
        t = sq + d
        if not (t & 0x88) and b[t] == 2 * by: return True
    for d in KG:
        t = sq + d
        if not (t & 0x88) and b[t] == 6 * by: return True
    for dirs, kinds in ((BD, (3, 5)), (RD, (4, 5))):
        for d in dirs:
            t = sq + d
            while not (t & 0x88):
                v = b[t]
                if v:
                    if v == kinds[0] * by or v == kinds[1] * by: return True
                    break
                t += d
    return False

def gen_moves(p, caps_only=False):
    b = p.b; side = p.side; moves = []
    for s in p.pl:
        v = b[s]
        if (v > 0) != (side > 0): continue
        a = abs(v); r = s >> 4
        if a == 1:
            fwd = 16 * side
            promo_rank = 6 if side > 0 else 1
            for d in (fwd - 1, fwd + 1):
                t = s + d
                if t & 0x88: continue
                if b[t] and (b[t] > 0) != (side > 0) or t == p.ep:
                    if r == promo_rank:
                        for pr in (5, 2): moves.append((s, t, pr * side))
                    else: moves.append((s, t, 0))
            t = s + fwd
            if not (t & 0x88) and not b[t]:
                if not caps_only:
                    if r == promo_rank:
                        for pr in (5, 2, 4, 3): moves.append((s, t, pr * side))
                    else: moves.append((s, t, 0))
                    start = 1 if side > 0 else 6
                    t2 = s + 2 * fwd
                    if r == start and not b[t2]: moves.append((s, t2, 0))
                elif r == promo_rank:
                    for pr in (5, 2): moves.append((s, t, pr * side))
        elif a == 2:
            for d in KN:
                t = s + d
                if t & 0x88: continue
                if not b[t] or (b[t] > 0) != (side > 0):
                    if not caps_only or b[t]: moves.append((s, t, 0))
        elif a == 6:
            for d in KG:
                t = s + d
                if t & 0x88: continue
                if not b[t] or (b[t] > 0) != (side > 0):
                    if not caps_only or b[t]: moves.append((s, t, 0))
            if not caps_only:
                if side > 0 and s == 4:
                    if p.cast & 1 and not b[5] and not b[6] and b[7] == 4 and not attacked(p, 4, -1) and not attacked(p, 5, -1) and not attacked(p, 6, -1): moves.append((4, 6, 0))
                    if p.cast & 2 and not b[3] and not b[2] and not b[1] and b[0] == 4 and not attacked(p, 4, -1) and not attacked(p, 3, -1) and not attacked(p, 2, -1): moves.append((4, 2, 0))
                if side < 0 and s == 116:
                    if p.cast & 4 and not b[117] and not b[118] and b[119] == -4 and not attacked(p, 116, 1) and not attacked(p, 117, 1) and not attacked(p, 118, 1): moves.append((116, 118, 0))
                    if p.cast & 8 and not b[115] and not b[114] and not b[113] and b[112] == -4 and not attacked(p, 116, 1) and not attacked(p, 115, 1) and not attacked(p, 114, 1): moves.append((116, 114, 0))
        else:
            dirs = BD if a == 3 else RD if a == 4 else KG
            for d in dirs:
                t = s + d
                while not (t & 0x88):
                    if not b[t]:
                        if not caps_only: moves.append((s, t, 0))
                    else:
                        if (b[t] > 0) != (side > 0): moves.append((s, t, 0))
                        break
                    t += d
    return moves

def make(p, m):
    s, t, pr = m
    b = p.b
    v = b[s]; cap = b[t]; undo = [cap, p.cast, p.ep, p.half, None, p.h, p.k[0], p.k[1]]
    if abs(v) == 6: p.k[0 if p.side > 0 else 1] = t
    h = p.h ^ ZC[p.cast]
    if p.ep >= 0: h ^= ZE[p.ep & 7]
    p.ep = -1
    if cap: h ^= ZK[cap + 6][t]; p.pl.remove(t)
    b[t] = v; b[s] = 0
    p.pl[p.pl.index(s)] = t
    h ^= ZK[v + 6][s] ^ ZK[v + 6][t]
    if abs(v) == 1:
        p.half = 0
        if t == undo[2] and cap == 0 and (t & 7) != (s & 7):
            cs = t - 16 * p.side
            undo[4] = b[cs]; h ^= ZK[b[cs] + 6][cs]; b[cs] = 0; p.pl.remove(cs)
        elif abs(t - s) == 32:
            p.ep = (s + t) // 2; h ^= ZE[p.ep & 7]
        if pr:
            b[t] = pr; h ^= ZK[v + 6][t] ^ ZK[pr + 6][t]
    elif cap: p.half = 0
    else: p.half += 1
    if abs(v) == 6:
        if p.side > 0: p.cast &= ~3
        else: p.cast &= ~12
        if abs(t - s) == 2:
            if t == 6: b[5] = b[7]; b[7] = 0; h ^= ZK[4 + 6][7] ^ ZK[4 + 6][5]; p.pl[p.pl.index(7)] = 5
            elif t == 2: b[3] = b[0]; b[0] = 0; h ^= ZK[4 + 6][0] ^ ZK[4 + 6][3]; p.pl[p.pl.index(0)] = 3
            elif t == 118: b[117] = b[119]; b[119] = 0; h ^= ZK[-4 + 6][119] ^ ZK[-4 + 6][117]; p.pl[p.pl.index(119)] = 117
            elif t == 114: b[115] = b[112]; b[112] = 0; h ^= ZK[-4 + 6][112] ^ ZK[-4 + 6][115]; p.pl[p.pl.index(112)] = 115
    if t == 7 or s == 7: p.cast &= ~1
    if t == 0 or s == 0: p.cast &= ~2
    if t == 119 or s == 119: p.cast &= ~4
    if t == 112 or s == 112: p.cast &= ~8
    p.cast &= 15
    h ^= ZC[p.cast] ^ ZS
    p.h = h
    p.side = -p.side
    return undo

def unmake(p, m, undo):
    s, t, pr = m
    p.side = -p.side
    b = p.b
    v = b[t]
    if pr: v = 1 * p.side
    b[s] = v; b[t] = undo[0]
    p.pl[p.pl.index(t)] = s
    if undo[0]: p.pl.append(t)
    if undo[4] is not None:
        cs = t - 16 * p.side
        b[cs] = undo[4]; p.pl.append(cs)
    if abs(v) == 6 and abs(t - s) == 2:
        if t == 6: b[7] = b[5]; b[5] = 0; p.pl[p.pl.index(5)] = 7
        elif t == 2: b[0] = b[3]; b[3] = 0; p.pl[p.pl.index(3)] = 0
        elif t == 118: b[119] = b[117]; b[117] = 0; p.pl[p.pl.index(117)] = 119
        elif t == 114: b[112] = b[115]; b[115] = 0; p.pl[p.pl.index(115)] = 112
    p.cast, p.ep, p.half = undo[1], undo[2], undo[3]
    p.h = undo[5]
    p.k[0], p.k[1] = undo[6], undo[7]

def evaluate(p):
    b = p.b; mg = 0; eg = 0; phase = 0; bishops = [0, 0]
    for s in p.pl:
        v = b[s]
        a = abs(v); f = s & 7; r = s >> 4
        if v > 0: ti = (7 - r) * 8 + f
        else: ti = r * 8 + f
        m = VAL[a] + PST[a][ti]
        e = VALE[a] + PSTE.get(a, PST[a])[ti]
        if v > 0: mg += m; eg += e
        else: mg -= m; eg -= e
        if a in (2, 3): phase += 1; bishops[0 if v > 0 else 1] += (a == 3)
        elif a == 4: phase += 2
        elif a == 5: phase += 4
    if bishops[0] >= 2: mg += 25; eg += 25
    if bishops[1] >= 2: mg -= 25; eg -= 25
    if phase > 24: phase = 24
    return (mg * phase + eg * (24 - phase)) // 24

nodes = 0; abort = False; TT = {}; killers = {}; history = {}; HIST = set()

def order_moves(p, moves, tt_move, ply):
    b = p.b; scored = []
    k = killers.get(ply, ())
    for m in moves:
        sc = 0
        if m == tt_move: sc = 1 << 24
        else:
            cap = b[m[1]]
            if cap or m[1] == p.ep: sc = (1 << 20) + abs(cap if cap else 1) * 16 - abs(b[m[0]]) // 32
            elif m in k: sc = 1 << 18
            else: sc = history.get((p.side, m[0], m[1]), 0)
            if m[2]: sc += 1 << 19
        scored.append((sc, m))
    scored.sort(key=lambda x: -x[0])
    return [m for _, m in scored]

def qsearch(p, alpha, beta, ply):
    global nodes, abort
    nodes += 1
    if nodes >= CAP: abort = True
    if abort: return alpha
    if p.half >= 100: return 0
    if ply > 28: return p.side * evaluate(p)
    ksq = p.k[0] if p.side > 0 else p.k[1]
    chk = attacked(p, ksq, -p.side)
    if chk:
        moves = gen_moves(p)
    else:
        stand = p.side * evaluate(p)
        if stand >= beta: return beta
        if stand > alpha: alpha = stand
        moves = gen_moves(p, caps_only=True)
    tt = TT.get(p.h)
    moves = order_moves(p, moves, tt[3] if tt else None, ply)
    legal = 0
    for m in moves:
        if not chk and not m[2]:
            capv = p.b[m[1]]
            if (capv or m[1] == p.ep) and stand + VAL[abs(capv) if capv else 1] + 150 <= alpha: continue
        undo = make(p, m); undo.append(p.h)
        if attacked(p, p.k[1] if p.side > 0 else p.k[0], p.side):
            unmake(p, m, undo); continue
        legal += 1
        sc = -qsearch(p, -beta, -alpha, ply + 1)
        unmake(p, m, undo)
        if abort: return alpha
        if sc >= beta: return beta
        if sc > alpha: alpha = sc
    if chk and not legal: return -MATE + ply
    return alpha

def search(p, depth, alpha, beta, ply):
    global nodes, abort
    if depth <= 0: return qsearch(p, alpha, beta, ply)
    nodes += 1
    if nodes >= CAP: abort = True
    if abort: return alpha
    if ply > 0:
        if p.h in HIST or p.half >= 100: return 0
        tt = TT.get(p.h)
        if tt and tt[0] >= depth:
            if tt[2] == 0: return tt[1]
            if tt[2] == 1 and tt[1] < beta: beta = tt[1]
            elif tt[2] == 2 and tt[1] > alpha: alpha = tt[1]
            if alpha >= beta: return tt[1]
    else:
        tt = TT.get(p.h)
    ksq = p.k[0] if p.side > 0 else p.k[1]
    chk = attacked(p, ksq, -p.side)
    if chk: depth += 1
    moves = order_moves(p, gen_moves(p), tt[3] if tt else None, ply)
    best = -2 * MATE; bestm = None; a0 = alpha
    for m in moves:
        undo = make(p, m); undo.append(p.h)
        if attacked(p, p.k[1] if p.side > 0 else p.k[0], p.side):
            unmake(p, m, undo); continue
        sc = -search(p, depth - 1, -beta, -alpha, ply + 1)
        unmake(p, m, undo)
        if abort: return alpha
        if sc > best: best = sc; bestm = m
        if sc > alpha: alpha = sc
        if alpha >= beta:
            if not p.b[m[1]] and m[1] != p.ep:
                kl = killers.setdefault(ply, [])
                if m not in kl: kl.insert(0, m); del kl[2:]
                history[(p.side, m[0], m[1])] = history.get((p.side, m[0], m[1]), 0) + depth * depth
            break
    if bestm is None:
        return -MATE + ply if chk else 0
    flag = 0 if a0 < best < beta else (1 if best <= a0 else 2)
    TT[p.h] = (depth, best, flag, bestm)
    return best

def uci(m):
    s, t, pr = m
    out = 'abcdefgh'[s & 7] + str((s >> 4) + 1) + 'abcdefgh'[t & 7] + str((t >> 4) + 1)
    if pr: out += 'nbrq'[abs(pr) - 2]
    return out

def parse_uci(p, u):
    s = (int(u[1]) - 1) * 16 + (ord(u[0]) - 97)
    t = (int(u[3]) - 1) * 16 + (ord(u[2]) - 97)
    pr = 0
    if len(u) > 4: pr = (2 + 'nbrq'.index(u[4])) * p.side
    return (s, t, pr)

def choose_moves(fen, hist_fens_moves):
    """Return root moves ordered best-first for the position in fen."""
    global nodes, abort, TT, killers, history, HIST
    p = parse_fen(fen)
    # rebuild game-history hashes for repetition awareness
    HIST = set()
    if hist_fens_moves:
        start_fen, moves_uci = hist_fens_moves
        q = parse_fen(start_fen); HIST.add(q.h)
        for u in moves_uci:
            make(q, parse_uci(q, u)); HIST.add(q.h)
    TT = {}; killers = {}; history = {}
    root = gen_moves(p)
    scored = [(0, m) for m in root]
    nodes = 0; abort = False
    depth = 1
    while depth <= 32:
        cur = []
        alpha = -2 * MATE
        for _, m in scored:
            undo = make(p, m); undo.append(p.h)
            if attacked(p, p.k[1] if p.side > 0 else p.k[0], p.side):
                unmake(p, m, undo); continue
            sc = -search(p, depth - 1, -2 * MATE, -alpha if cur else 2 * MATE, 1)
            unmake(p, m, undo)
            if abort: break
            cur.append((sc, m))
            if sc > alpha: alpha = sc
        if abort or not cur: break
        cur.sort(key=lambda x: -x[0])
        scored = cur; depth += 1
    return [uci(m) for _, m in scored]

# ---------- env driver
ENV = os.environ.get('MAKEFUN_ENV_URL', '')

def post(path, body):
    req = Request(ENV + path, data=json.dumps(body).encode(), headers={'content-type': 'application/json'})
    with urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())

def main():
    st = post('/game', {})
    while st.get('status') != 'done':
        if st.get('status') == 'over':
            st = post('/game', {}); continue
        fen = st['fen']; legal = st.get('legal_moves') or []
        cands = choose_moves(fen, (st.get('start_fen', fen), st.get('moves') or []))
        tried = []
        nxt = None
        for mv in cands + [x for x in legal if x not in cands]:
            if mv in tried: continue
            tried.append(mv)
            try:
                nxt = post('/move', {'game': st['game'], 'move': mv}); break
            except HTTPError:
                continue
        if nxt is None:
            post('/resign', {'game': st['game']})
            st = post('/game', {})
        else:
            st = nxt
    sys.stdout.write(json.dumps({k: st.get(k) for k in ('wins', 'draws', 'losses')}) + '\n')

if __name__ == '__main__':
    main()
