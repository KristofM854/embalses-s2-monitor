import json, sys
from PIL import Image
out, dest = sys.argv[1], sys.argv[2]
frames = json.load(open(f"{out}/frames.json"))
W = 900
imgs, durs = [], []
for f, ms in frames:
    im = Image.open(f).convert("RGB")
    im = im.resize((W, round(im.height * W / im.width)), Image.LANCZOS)
    imgs.append(im); durs.append(ms)
# one shared palette keeps the file small and avoids colour flicker between frames
pal = imgs[0].copy()
strip = Image.new("RGB", (W, sum(i.height for i in imgs[::2])))
y = 0
for i in imgs[::2]:
    strip.paste(i, (0, y)); y += i.height
pal = strip.quantize(colors=128, method=Image.Quantize.MEDIANCUT)
q = [i.quantize(palette=pal, dither=Image.Dither.NONE) for i in imgs]
q[0].save(dest, save_all=True, append_images=q[1:], duration=durs, loop=0, optimize=True)
import os; print(dest, round(os.path.getsize(dest) / 1e6, 2), "MB")
