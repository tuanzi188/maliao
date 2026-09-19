# 渲染当前 1-1 关卡布局全景图（仅用于分析展示，不改游戏本体）
# 数据来源：index.html 中的结构化关卡定义
from PIL import Image, ImageDraw, ImageFont

TILE = 12                       # 每格像素
W, H = 224, 17                  # 地图尺寸（列 x 行）
CELL = TILE
IMG_W, IMG_H = W * CELL, H * CELL + 64

# 代码里的关卡数据
GROUND_ROW = 15
PITS   = [[69,70],[86,88],[153,154]]
PIPES  = [(28,2),(38,3),(46,4),(57,4),(163,2),(179,2)]
BRICKS_LOW  = [20,22,24,93,119,130,131,158,160]          # 行 11
BRICKS_HIGH = list(range(80,88)) + [91,92,93,118,121,128,129,130]  # 行 7
QBLOCKS_LOW  = [16,21,23,64,78,94,106,109,113,159]       # 行 11
QBLOCKS_HIGH = [22,94,109,119,120,131]                   # 行 7
COINS  = [(68,11),(71,11),(85,11),(89,11),(152,11),(155,11),
          (106,7),(107,7),(108,7),(124,11),(125,11),(126,11)]
STAIRS = []
for i in range(4): STAIRS += [(134+i, i+1),(141+i,4-i),(148+i,i+1),(155+i,4-i)]
for i in range(8): STAIRS.append((181+i, i+1))
HIDDEN = [(21,7),(64,7)]
GOAL = 198
ENEMY_GOOMBA = [22,41,51,52,80,82,97,107,110,113,128,129,174,176]
ENEMY_KOOPA  = [60,124]
PLANT_PIPES  = [38,57]      # 代码中带食人花的管道

# 颜色
C_SKY      = (108, 192, 252)
C_GROUND   = (210, 118, 30)
C_BRICK    = (181, 72, 42)
C_QBLOCK   = (232, 150, 30)
C_COIN     = (255, 210, 63)
C_PIPE     = (34, 172, 56)
C_HIDDEN   = (255, 255, 255)
C_GOAL     = (170, 190, 200)
C_ENEMY    = (200, 40, 40)
C_ENEMY_K  = (60, 160, 60)
C_PLANT    = (120, 255, 120)

img = Image.new('RGB', (IMG_W, IMG_H), C_SKY)
d = ImageDraw.Draw(img)

# 地面
for x in range(W):
    for r in (GROUND_ROW, GROUND_ROW+1):
        d.rectangle([x*CELL, r*CELL, x*CELL+CELL-1, r*CELL+CELL-1], fill=C_GROUND)
# 坑
for a,b in PITS:
    for x in range(a, b+1):
        for r in (GROUND_ROW, GROUND_ROW+1):
            d.rectangle([x*CELL, r*CELL, x*CELL+CELL-1, r*CELL+CELL-1], fill=(40,40,70))
# 管道（含食人花标记）
for col,h in PIPES:
    for k in range(h):
        for dx in (0,1):
            d.rectangle([(col+dx)*CELL, (GROUND_ROW-1-k)*CELL, (col+dx)*CELL+CELL-1, (GROUND_ROW-1-k)*CELL+CELL-1], fill=C_PIPE)
    if col in PLANT_PIPES:
        d.ellipse([col*CELL+2, (GROUND_ROW-1-h)*CELL-6, (col+1)*CELL-2, (GROUND_ROW-1-h)*CELL+4], fill=C_PLANT)
# 砖块
for x in BRICKS_LOW:  d.rectangle([x*CELL, 11*CELL, x*CELL+CELL-1, 11*CELL+CELL-1], fill=C_BRICK)
for x in BRICKS_HIGH: d.rectangle([x*CELL, 7*CELL, x*CELL+CELL-1, 7*CELL+CELL-1], fill=C_BRICK)
# 问号块
for x in QBLOCKS_LOW:  d.rectangle([x*CELL, 11*CELL, x*CELL+CELL-1, 11*CELL+CELL-1], fill=C_QBLOCK)
for x in QBLOCKS_HIGH: d.rectangle([x*CELL, 7*CELL, x*CELL+CELL-1, 7*CELL+CELL-1], fill=C_QBLOCK)
# 金币
for x,y in COINS:
    d.ellipse([x*CELL+3, y*CELL+3, x*CELL+CELL-4, y*CELL+CELL-4], fill=C_COIN)
# 台阶（地面色，带边）
for x,h in STAIRS:
    for k in range(h):
        d.rectangle([x*CELL, (GROUND_ROW-1-k)*CELL, x*CELL+CELL-1, (GROUND_ROW-1-k)*CELL+CELL-1], fill=C_GROUND,
                    outline=(120,60,10))
# 隐藏块（白框）
for x,y in HIDDEN:
    d.rectangle([x*CELL+1, y*CELL+1, x*CELL+CELL-2, y*CELL+CELL-2], outline=C_HIDDEN, width=2)
# 旗杆
d.rectangle([GOAL*CELL-1, 0, GOAL*CELL+1, GROUND_ROW*CELL], fill=C_GOAL)
d.ellipse([GOAL*CELL-3, 0, GOAL*CELL+3, 6], fill=(255,60,60))
# 敌人
for x in ENEMY_GOOMBA:
    d.ellipse([x*CELL+3, (GROUND_ROW-1)*CELL+2, x*CELL+CELL-4, (GROUND_ROW-1)*CELL+CELL-2], fill=C_ENEMY)
for x in ENEMY_KOOPA:
    d.rectangle([x*CELL+3, (GROUND_ROW-1)*CELL+2, x*CELL+CELL-4, (GROUND_ROW-1)*CELL+CELL-2], fill=C_ENEMY_K)

# 区段标注
try:
    font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 15)
except:
    font = ImageFont.load_default()
segments = [
    (0,   "开局教学区", (230,230,255)),
    (28,  "四连管道区", (220,255,220)),
    (69,  "坑①", (255,225,225)),
    (78,  "砖阵区", (230,230,255)),
    (94,  "道具区(星/十金币砖)", (220,255,220)),
    (134, "双丘区", (230,230,255)),
    (163, "终点区", (220,255,220)),
]
for start, name, col in segments:
    x0 = start * CELL
    x1 = (segments[segments.index((start,name,col))] is not None and
          (segments[segments.index((start,name,col))+1][0] if segments.index((start,name,col))+1 < len(segments) else W) * CELL)
    d.rectangle([x0, H*CELL, x1-1, H*CELL+24], fill=col)
    d.text((x0+3, H*CELL+3), name, fill=(40,40,40), font=font)
# 旗杆/出口标注
d.text((GOAL*CELL-20, H*CELL+28), "旗杆(198)", fill=(120,40,40), font=font)
d.text((163*CELL, H*CELL+28), "出口管", fill=(20,100,20), font=font)

img.save(r"D:\a工作空间\像素马里奥\mario_layout.png")
print("saved", img.size)
