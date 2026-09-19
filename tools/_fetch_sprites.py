# 抓取 nesmaps.com SMB 精灵页面，解析图片 URL 并下载到 sprites_raw/
import re, os, urllib.request

BASE = "https://nesmaps.com/maps/SuperMarioBrothers/sprites/SuperMarioBrothersSprites.html"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sprites_raw")
os.makedirs(OUT, exist_ok=True)

req = urllib.request.Request(BASE, headers={"User-Agent": "Mozilla/5.0"})
html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore")

# 找出所有 <img src> 及其前的行名称
imgs = re.findall(r'<img[^>]+src="([^"]+)"', html)
print("img count:", len(imgs))
for src in imgs:
    url = src if src.startswith("http") else "https://nesmaps.com/maps/SuperMarioBrothers/sprites/" + src.lstrip("./")
    name = url.split("/")[-1]
    dest = os.path.join(OUT, name)
    try:
        urllib.request.urlretrieve(url, dest)
        print("OK", name, os.path.getsize(dest))
    except Exception as e:
        print("FAIL", url, e)
