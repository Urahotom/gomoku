import random

EMPTY, BLACK, WHITE = 0, 1, 2
DIRS = ((0, 1), (1, 0), (1, 1), (1, -1))


class Board:
    def __init__(self, n=15):
        self.n = n
        self.grid = [[EMPTY] * n for _ in range(n)]
        self.history = []

    def inside(self, r, c):
        return 0 <= r < self.n and 0 <= c < self.n

    def get(self, r, c):
        return self.grid[r][c]

    def place(self, r, c, color):
        if not self.inside(r, c) or self.grid[r][c] != EMPTY:
            return False
        self.grid[r][c] = color
        self.history.append((r, c, color))
        return True

    def is_full(self):
        return len(self.history) >= self.n * self.n

    def check_win(self, r, c, color):
        """Return list of winning lines (each a list of (r,c)) through (r,c)."""
        lines = []
        for dr, dc in DIRS:
            line = [(r, c)]
            for s in (1, -1):
                rr, cc = r + dr * s, c + dc * s
                while self.inside(rr, cc) and self.grid[rr][cc] == color:
                    line.append((rr, cc))
                    rr += dr * s
                    cc += dc * s
            if len(line) >= 5:
                line.sort()
                lines.append(line)
        return lines or None

    def candidates(self, radius=2):
        if not self.history:
            return [(self.n // 2, self.n // 2)]
        seen = set()
        n = self.n
        for r0, c0, _ in self.history:
            for r in range(max(0, r0 - radius), min(n, r0 + radius + 1)):
                for c in range(max(0, c0 - radius), min(n, c0 + radius + 1)):
                    if self.grid[r][c] == EMPTY:
                        seen.add((r, c))
        return list(seen)
