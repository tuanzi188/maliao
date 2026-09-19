import io, sys
sys.stdout.reconfigure(encoding='utf-8')

W, H = 16, 32

# 每行的实心列区间（含头、茎、叶）；None 表示该行两段（V 形缺口未闭合）
SIL = {
    0:  [(1, 6), (10, 15)],
    1:  [(1, 6), (10, 15)],
    2:  [(1, 7), (9, 15)],
    3:  [(1, 7), (9, 15)],
    4:  [(0, 16)],
    5:  [(0, 16)],
    6:  [(0, 16)],
    7:  [(0, 16)],
    8:  [(0, 16)],
    9:  [(0, 16)],
    10: [(0, 16)],
    11: [(0, 16)],
    12: [(0, 16)],
    13: [(0, 16)],
    14: [(1, 15)],
    15: [(2, 14)],
    16: [(3, 13)],
    17: [(4, 12)],
    18: [(6, 10)],
    19: [(6, 10), (3, 6), (10, 13)],
    20: [(6, 10), (2, 6), (10, 14)],
    21: [(6, 10), (1, 6), (10, 15)],
    22: [(6, 10), (0, 6), (10, 16)],
    23: [(6, 10), (0, 6), (10, 16)],
    24: [(6, 10), (1, 6), (10, 15)],
    25: [(6, 10), (2, 6), (10, 14)],
    26: [(6, 10), (3, 6), (10, 13)],
    27: [(6, 10)],
    28: [(6, 10)],
    29: [(6, 10)],
    30: [(6, 10)],
    31: [(6, 10)],
}
HEAD_BOTTOM = 18          # 行 >= 此值为茎/叶（绿色）

inside = [[False] * W for _ in range(H)]
for r, spans in SIL.items():
    for a, b in spans:
        for c in range(a, b):
            inside[r][c] = True

def out(r, c):
    """该坐标是否在轮廓外（越界/空格都算外）"""
    return r < 0 or r >= H or c < 0 or c >= W or not inside[r][c]

g = [['.'] * W for _ in range(H)]
for r in range(H):
    for c in range(W):
        if not inside[r][c]:
            continue
        body = 'R' if r < HEAD_BOTTOM else 'C'
        g[r][c] = body
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if (dr or dc) and out(r + dr, c + dc):
                    g[r][c] = 'K'
                    break
            if g[r][c] == 'K':
                break

# 白色内唇：V 形开口两侧内壁直接刷白（覆盖描边，让白贴着开口，参考图即如此）
for r, walls in ((0, (5, 10)), (1, (5, 10)), (2, (6, 9)), (3, (6, 9))):
    for c in walls:
        if inside[r][c]:
            g[r][c] = 'W'
# 两瓣顶端整体白尖
for r in range(4):
    for c in range(W):
        if g[r][c] == 'R':
            g[r][c] = 'W'

# 红斑（参考图为成块的白斑，落在两瓣中下部）
for r, c in ((6, 3), (6, 4), (7, 11), (7, 12), (9, 4), (9, 5),
             (9, 10), (11, 2), (11, 3), (12, 7), (12, 8), (13, 12), (13, 13)):
    if g[r][c] == 'R':
        g[r][c] = 'W'

# 茎暗侧 + 叶片下缘阴影
for r in range(HEAD_BOTTOM, H):
    for c in range(W):
        if g[r][c] != 'C':
            continue
        if c == 9:
            g[r][c] = 'D'                                   # 茎的背光侧
        elif (c < 5 or c > 10) and out(r + 1, c) is False and r >= 24:
            g[r][c] = 'D'                                   # 叶下缘

for r in g:
    print("  '" + ''.join(r) + "',")
assert all(len(x) == W for x in (''.join(r) for r in g)), 'row width drift'
print('rows =', H)
