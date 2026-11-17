import os, sys, json, random
A5 = "abcdefghijklmnopqrstuv"
def _t(s):
 return [(A5.index(c) - 10) * 5 for c in s]
from urllib.request import Request, urlopen
from urllib.error import HTTPError
KN = (33, 31, 18, 14, -14, -18, -31, -33)
KG = (16, -16, 1, -1, 17, 15, -15, -17)
BD = (17, 15, -15, -17)
RD = (16, -16, 1, -1)
CASTL = ((1, 4, 7, 4, (5, 6), (4, 5, 6), 6), (2, 4, 0, 4, (1, 2, 3), (4, 3, 2), 2), (4, 116, 119, -4, (117, 118), (116, 117, 118), 118), (8, 116, 112, -4, (113, 114, 115), (116, 115, 114), 114))
CRM = {7: 1, 0: 2, 119: 4, 112: 8}
CRM2 = {6: (7, 5), 2: (0, 3), 118: (119, 117), 114: (112, 115)}
V = (0, 100, 320, 330, 500, 900, 0)
VE = (0, 120, 320, 330, 500, 900, 0)
PH = (0, 0, 1, 1, 2, 4, 0)
PT = {1:_t("kkkkkkkkuuuuuuuummoqqommllmppmllkkkookkkljikkijllmmggmmlkkkkkkkk"),2:_t("aceeeecacgkkkkgcekmnnmkeelnoonleeknoonkeelmnnmlecgkllkgcaceeeeca"),3:_t("giiiiiigikkkkkkiiklmmlkiillmmlliikmmmmkiimmmmmmiilkkkkligiiiiiig"),4:_t("kkkkkkkklmmmmmmljkkkkkkjjkkkkkkjjkkkkkkjjkkkkkkjjkkkkkkjkkkllkkk"),5:_t("giijjiigikkkkkkiikllllkijkllllkjkkllllkjilllllkiiklkkkkigiijjiig"),6:_t("eccaacceeccaacceeccaacceeccaaccegeecceegiggggggiookkkkoooqmkkmqo")}
PE = {1:_t("kkkkkkkkrrrrrrrrppppppppnnnnnnnnmmmmmmmmkkkkkkkkkkkkkkkkkkkkkkkk"),6:_t("aceggecaegikkigeeioqqoieeiqssqieeiqssqieeioqqoieeekkkkeeaeeeeeea")}
_r = random.Random(20261117)
ZK = [[_r.getrandbits(64) for _ in range(128)] for _ in range(13)]
ZC = [_r.getrandbits(64) for _ in range(16)]
ZE = [_r.getrandbits(64) for _ in range(8)]
ZS = _r.getrandbits(64)
MT = 100000
CP = 30000
class Ps:
  __slots__ = ('b', 'side', 'cast', 'ep', 'half', 'h', 'k', 'pl')
  def __init__(self):
    self.b = [0] * 128
    self.side = 1; self.cast = 0; self.ep = -1; self.half = 0; self.h = 0
    self.k = [-1, -1]; self.pl = []
def pfn(fen):
  p = Ps()
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
def kh(p):
  return atk(p, p.k[1] if p.side > 0 else p.k[0], p.side)
def atk(p, sq, by):
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
def gmv(p, caps_only=False):
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
    elif a in (2, 6):
      for d in KN if a == 2 else KG:
        t = s + d
        if t & 0x88: continue
        if not b[t] or (b[t] > 0) != (side > 0):
          if not caps_only or b[t]: moves.append((s, t, 0))
      if a == 6 and not caps_only:
        for bit, home, rook, rv, emp, safe, dest in CASTL:
          if s == home and p.cast & bit and b[rook] == rv and all(not b[x] for x in emp) and all(not atk(p, x, -side) for x in safe): moves.append((s, dest, 0))
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
def mak(p, m):
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
      rf, rt = CRM2[t]; rv = b[rf]; b[rt] = rv; b[rf] = 0; h ^= ZK[rv + 6][rf] ^ ZK[rv + 6][rt]; p.pl[p.pl.index(rf)] = rt
  for sq in (s, t): p.cast &= ~CRM.get(sq, 0)
  h ^= ZC[p.cast] ^ ZS
  p.h = h
  p.side = -p.side
  return undo
def umk(p, m, undo):
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
    rf, rt = CRM2[t]; b[rf] = b[rt]; b[rt] = 0; p.pl[p.pl.index(rt)] = rf
  p.cast, p.ep, p.half = undo[1], undo[2], undo[3]
  p.h = undo[5]
  p.k[0], p.k[1] = undo[6], undo[7]
def evl(p):
  b = p.b; mg = 0; eg = 0; phase = 0; bishops = [0, 0]
  for s in p.pl:
    v = b[s]
    a = abs(v); f = s & 7; r = s >> 4
    if v > 0: ti = (7 - r) * 8 + f
    else: ti = r * 8 + f
    m = V[a] + PT[a][ti]
    e = VE[a] + PE.get(a, PT[a])[ti]
    if v > 0: mg += m; eg += e
    else: mg -= m; eg -= e
    phase += PH[a]
    if a == 3: bishops[0 if v > 0 else 1] += 1
  if bishops[0] >= 2: mg += 25; eg += 25
  if bishops[1] >= 2: mg -= 25; eg -= 25
  if phase > 24: phase = 24
  return (mg * phase + eg * (24 - phase)) // 24
nds = 0; abt = False; TT = {}; klr = {}; hst = {}; HIST = set()
def omv(p, moves, tt_move, ply):
  b = p.b; scored = []
  k = klr.get(ply, ())
  for m in moves:
    sc = 0
    if m == tt_move: sc = 1 << 24
    else:
      cap = b[m[1]]
      if cap or m[1] == p.ep: sc = (1 << 20) + abs(cap if cap else 1) * 16 - abs(b[m[0]]) // 32
      elif m in k: sc = 1 << 18
      else: sc = hst.get((p.side, m[0], m[1]), 0)
      if m[2]: sc += 1 << 19
    scored.append((sc, m))
  scored.sort(key=lambda x: -x[0])
  return [m for _, m in scored]
def qs(p, alpha, beta, ply):
  global nds, abt
  nds += 1
  if nds >= CP: abt = True
  if abt: return alpha
  if p.half >= 100: return 0
  if ply > 28: return p.side * evl(p)
  ksq = p.k[0] if p.side > 0 else p.k[1]
  chk = atk(p, ksq, -p.side)
  if chk:
    moves = gmv(p)
  else:
    stand = p.side * evl(p)
    if stand >= beta: return beta
    if stand > alpha: alpha = stand
    moves = gmv(p, caps_only=True)
  tt = TT.get(p.h)
  moves = omv(p, moves, tt[3] if tt else None, ply)
  legal = 0
  for m in moves:
    undo = mak(p, m)
    if kh(p):
      umk(p, m, undo); continue
    legal += 1
    sc = -qs(p, -beta, -alpha, ply + 1)
    umk(p, m, undo)
    if abt: return alpha
    if sc >= beta: return beta
    if sc > alpha: alpha = sc
  if chk and not legal: return -MT + ply
  return alpha
def sr(p, depth, alpha, beta, ply):
  global nds, abt
  if depth <= 0: return qs(p, alpha, beta, ply)
  nds += 1
  if nds >= CP: abt = True
  if abt: return alpha
  tt = TT.get(p.h)
  if ply > 0:
    if p.h in HIST or p.half >= 100: return 0
    if tt and tt[0] >= depth:
      if tt[2] == 0: return tt[1]
      if tt[2] == 1 and tt[1] < beta: beta = tt[1]
      elif tt[2] == 2 and tt[1] > alpha: alpha = tt[1]
      if alpha >= beta: return tt[1]
  ksq = p.k[0] if p.side > 0 else p.k[1]
  chk = atk(p, ksq, -p.side)
  if chk: depth += 1
  moves = omv(p, gmv(p), tt[3] if tt else None, ply)
  best = -2 * MT; bestm = None; a0 = alpha
  for m in moves:
    undo = mak(p, m)
    if kh(p):
      umk(p, m, undo); continue
    sc = -sr(p, depth - 1, -beta, -alpha, ply + 1)
    umk(p, m, undo)
    if abt: return alpha
    if sc > best: best = sc; bestm = m
    if sc > alpha: alpha = sc
    if alpha >= beta:
      if not p.b[m[1]] and m[1] != p.ep:
        kl = klr.setdefault(ply, [])
        if m not in kl: kl.insert(0, m); del kl[2:]
        hst[(p.side, m[0], m[1])] = hst.get((p.side, m[0], m[1]), 0) + depth * depth
      break
  if bestm is None:
    return -MT + ply if chk else 0
  flag = 0 if a0 < best < beta else (1 if best <= a0 else 2)
  TT[p.h] = (depth, best, flag, bestm)
  return best
def uci(m):
  s, t, pr = m
  out = 'abcdefgh'[s & 7] + str((s >> 4) + 1) + 'abcdefgh'[t & 7] + str((t >> 4) + 1)
  if pr: out += 'nbrq'[abs(pr) - 2]
  return out
def puc(p, u):
  s = (int(u[1]) - 1) * 16 + (ord(u[0]) - 97)
  t = (int(u[3]) - 1) * 16 + (ord(u[2]) - 97)
  pr = 0
  if len(u) > 4: pr = (2 + 'nbrq'.index(u[4])) * p.side
  return (s, t, pr)
def chm(fen, hist_fens_moves):
  global nds, abt, TT, klr, hst, HIST
  p = pfn(fen)
  HIST = set()
  if hist_fens_moves:
    start_fen, moves_uci = hist_fens_moves
    q = pfn(start_fen); HIST.add(q.h)
    for u in moves_uci:
      mak(q, puc(q, u)); HIST.add(q.h)
  TT = {}; klr = {}; hst = {}
  root = gmv(p)
  scored = [(0, m) for m in root]
  nds = 0; abt = False
  depth = 1
  while depth <= 32:
    cur = []
    alpha = -2 * MT
    for _, m in scored:
      undo = mak(p, m)
      if kh(p):
        umk(p, m, undo); continue
      sc = -sr(p, depth - 1, -2 * MT, -alpha if cur else 2 * MT, 1)
      umk(p, m, undo)
      if abt: break
      cur.append((sc, m))
      if sc > alpha: alpha = sc
    if abt or not cur: break
    cur.sort(key=lambda x: -x[0])
    scored = cur; depth += 1
  return [uci(m) for _, m in scored]
ENV = os.environ.get('MAKEFUN_ENV_URL', '')
def pst(path, body):
  req = Request(ENV + path, data=json.dumps(body).encode())
  with urlopen(req, timeout=60) as r:
    return json.loads(r.read().decode())
def main():
  st = pst('/game', {})
  while st.get('status') != 'done':
    if st.get('status') == 'over':
      st = pst('/game', {}); continue
    fen = st['fen']; legal = st.get('legal_moves') or []
    cands = chm(fen, (st.get('start_fen', fen), st.get('moves') or []))
    nxt = None
    for mv in dict.fromkeys(cands + legal):
      try:
        nxt = pst('/move', {'game': st['game'], 'move': mv}); break
      except HTTPError:
        continue
    if nxt is None:
      pst('/resign', {'game': st['game']})
      st = pst('/game', {})
    else:
      st = nxt
  print('done')
if __name__ == '__main__':
  main()