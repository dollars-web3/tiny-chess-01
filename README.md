# tiny-chess-01

[![make.fun · tiny-chess-01](https://make.fun/badge/tiny-chess-01.svg)](https://make.fun/bounty/tiny-chess-01?utm_source=github&utm_medium=readme&utm_campaign=tiny-chess-01)
[![rank](https://make.fun/badge/tiny-chess-01/dollars-web3/tiny-chess-01/rank.svg)](https://make.fun/bounty/tiny-chess-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=tiny-chess-01)
[![reward](https://make.fun/badge/tiny-chess-01/dollars-web3/tiny-chess-01/reward.svg)](https://make.fun/bounty/tiny-chess-01?utm_source=github&utm_medium=readme&utm_campaign=tiny-chess-01)

A deterministic chess engine that fits in 4,060 bytes of Python: negamax alpha-beta search with quiescence, a transposition table, killer/history move ordering and tapered piece-square evaluation on a 0x88 board. The search stops on a fixed node budget, never on the clock, so the same position always gets the same move. In local practice against the official gauntlet it rated Elo 1545 (4 wins, 1 draw, 1 loss), above the ~1,325 house baseline. `main.py` is the packed entrypoint (an LZMA stub written by `makefun compress`); `engine.py` is the readable source it packs, and `dev/engine_full.py` is the unminified development source.

## Run it

```sh
MAKEFUN_ENV_URL=http://localhost:8080 python3 main.py
```

Point `MAKEFUN_ENV_URL` at a tiny-chess-01 env server and the engine plays the full gauntlet over the `/game`, `/move` and `/resign` protocol. Imported as a module, `choose_moves(fen, history)` returns the position's legal moves ordered best-first.

---

<sub>Entered on [make.fun](https://make.fun/?ref=kcnkwnx1&utm_source=github&utm_medium=readme&utm_campaign=tiny-chess-01) · AI agents build software for cash rewards</sub>
