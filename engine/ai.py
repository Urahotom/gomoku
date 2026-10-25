"""Gomoku AI.

level 1: quick heuristic (1-ply pattern scoring)
level 2: negamax + alpha-beta search (default), candidate pruning & move ordering
"""

import random

from .board import DIRS, EMPTY, BLACK, WHITE

SCORE_FIVE = 100000
WIN = 10 ** 7
INF = 10 ** 9
ATTRACT = 0.92

_RUN_SCORE = {
    1: (0, 10, 10),
    2: (0, 50, 300),
    3: (0, 500, 3000),
    4: (0, 1000, 10000),
    5: (0, SCORE_FIVE, SCORE_FIVE),
}

BRANCH = (12, 8, 6)


def _pattern_score(count, ends):
    if count >= 5:
        return SCORE_FIVE
    if ends == 0:
        return 0
    if count == 4:
        return 10000 if ends == 2 else 1000
    if count == 3:
        return 3000 if ends == 2 else 500
    if count == 2:
        return 300 if ends == 2 else 50
    return 10


def _line_info(board, r, c, dr, dc, color):
    count = 1
    ends = 0
    for s in (1, -1):
        rr, cc = r + dr * s, c + dc * s
        while board.inside(rr, cc) and board.get(rr, cc) == color:
            count += 1
            rr += dr * s
            cc += dc * s
        if board.inside(rr, cc) and board.get(rr, cc) == EMPTY:
            ends += 1
    return count, ends


def eval_move(board, r, c, color):
    """Heuristic value of playing (r, c) as `color` (must be empty)."""
    board.grid[r][c] = color
    try:
        parts = sorted(
            (_pattern_score(*_line_info(board, r, c, dr, dc, color)) for dr, dc in DIRS),
            reverse=True,
        )
    finally:
        board.grid[r][c] = EMPTY
    return parts[0] + 0.3 * parts[1]


def _near_candidates(board, radius):
    grid = board.grid
    n = board.n
    seen = set()
    for r in range(n):
        row = grid[r]
        for c in range(n):
            if row[c]:
                for rr in range(max(0, r - radius), min(n, r + radius + 1)):
                    grow = grid[rr]
                    for cc in range(max(0, c - radius), min(n, c + radius + 1)):
                        if grow[cc] == EMPTY:
                            seen.add((rr, cc))
    return seen


def immediate_win(board, color):
    for r, c in _near_candidates(board, 1):
        board.grid[r][c] = color
        w = board.check_win(r, c, color)
        board.grid[r][c] = EMPTY
        if w:
            return (r, c)
    return None


def find_win(board, color):
    for r, c in board.candidates():
        board.grid[r][c] = color
        win = board.check_win(r, c, color)
        board.grid[r][c] = EMPTY
        if win:
            return (r, c)
    return None


# ---------- static evaluation ----------

_LINE_CACHE = {}


def _get_lines(n):
    lines = _LINE_CACHE.get(n)
    if lines is not None:
        return lines
    lines = []
    for r in range(n):
        lines.append([(r, c) for c in range(n)])
    for c in range(n):
        lines.append([(r, c) for r in range(n)])
    for k in range(-(n - 5), n - 4):
        cells = [(r, r - k) for r in range(n) if 0 <= r - k < n]
        lines.append(cells)
    for k in range(4, 2 * n - 5):
        cells = [(r, k - r) for r in range(n) if 0 <= k - r < n]
        lines.append(cells)
    _LINE_CACHE[n] = lines
    return lines


def _both_scores(board):
    grid = board.grid
    sb = 0
    sw = 0
    for line in _get_lines(board.n):
        cols = [grid[r][c] for r, c in line]
        ln = len(cols)
        i = 0
        while i < ln:
            col = cols[i]
            if col == EMPTY:
                i += 1
                continue
            j = i + 1
            while j < ln and cols[j] == col:
                j += 1
            cnt = j - i
            ends = (1 if i > 0 and cols[i - 1] == EMPTY else 0) + (
                1 if j < ln and cols[j] == EMPTY else 0
            )
            s = _RUN_SCORE[cnt if cnt < 5 else 5][ends]
            if col == BLACK:
                sb += s
            else:
                sw += s
            i = j
    return sb, sw


def evaluate(board, color):
    """Static score from the perspective of `color` (side to move)."""
    sb, sw = _both_scores(board)
    if color == BLACK:
        return sb - ATTRACT * sw
    return sw - ATTRACT * sb


# ---------- search ----------


def _ordered_moves(board, color, limit):
    opp = 3 - color
    cands = _near_candidates(board, 2)
    if not cands:
        return []
    scored = []
    for r, c in cands:
        s = eval_move(board, r, c, color) + 0.85 * eval_move(board, r, c, opp)
        scored.append((s, (r, c)))
    scored.sort(key=lambda x: -x[0])
    return [mv for _, mv in scored[:limit]]


def _negamax(board, color, depth, alpha, beta, ply):
    if immediate_win(board, color):
        return WIN - ply * 1000
    if depth <= 0:
        return evaluate(board, color)
    moves = _ordered_moves(board, color, BRANCH[min(ply, len(BRANCH) - 1)])
    if not moves:
        return 0
    best = -INF
    for r, c in moves:
        board.grid[r][c] = color
        val = -_negamax(board, 3 - color, depth - 1, -beta, -alpha, ply + 1)
        board.grid[r][c] = EMPTY
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best


def _choose_heuristic(board, ai_color, noise, block_cell):
    cands = board.candidates()
    if not cands:
        return (board.n // 2, board.n // 2), "best"
    opp = 3 - ai_color
    scored = []
    for r, c in cands:
        s = eval_move(board, r, c, ai_color) + 0.9 * eval_move(board, r, c, opp)
        if noise > 0:
            s *= 1.0 + noise * (random.random() * 2 - 1)
        scored.append((s, (r, c)))
    scored.sort(key=lambda x: -x[0])
    best = scored[0][0]
    top = [mv for s, mv in scored if s >= best * 0.999]
    mv = random.choice(top)
    return mv, ("block" if mv == block_cell else "best")


def choose_move(board, ai_color, noise=0.1, level=2, depth=3):
    """Return ((r, c), reason) where reason is 'win' | 'block' | 'best'."""
    opp = 3 - ai_color
    win = immediate_win(board, ai_color)
    if win:
        return win, "win"
    block_cell = immediate_win(board, opp)
    if level <= 1 or not board.history:
        mv, reason = _choose_heuristic(board, ai_color, noise, block_cell)
        return mv, ("block" if mv == block_cell else reason)

    cands = _near_candidates(board, 2)
    if not cands:
        return (board.n // 2, board.n // 2), "best"
    moves = _ordered_moves(board, ai_color, BRANCH[0] + 2)
    alpha = -INF
    best_val = -INF
    best_moves = []
    for r, c in moves:
        board.grid[r][c] = ai_color
        val = -_negamax(board, opp, depth - 1, -INF, -alpha, 1)
        board.grid[r][c] = EMPTY
        if val > best_val + 1e-6:
            best_val = val
            best_moves = [(r, c)]
        elif val >= best_val - 1e-6:
            best_moves.append((r, c))
        if best_val > alpha:
            alpha = best_val
    mv = random.choice(best_moves)
    return mv, ("block" if mv == block_cell else "best")
