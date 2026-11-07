"""Собирает готовую папку dist/ для заливки на хостинг: python3 build.py

Если рядом лежит src/cards.json (скачан из редактора в приложении), карточки берутся из него,
а фото из карточек сохраняются отдельными файлами в dist/img/.
"""
import base64
import json
import re
import shutil
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).parent
SRC, DIST = ROOT / "src", ROOT / "dist"

HEAD = """<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#1F4D45">
<meta name="robots" content="noindex, nofollow">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="IT-помощь">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" href="icons/icon-192.png">
<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">
<style>:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}body{margin:0}[hidden]{display:none!important}img{max-width:100%}</style>
"""

DATA_URL = re.compile(r"^data:image/(jpeg|jpg|png|webp);base64,(.+)$", re.S)


def icon(size, maskable=False):
    S = 1024
    teal, ivory, brass = (31, 77, 69), (246, 241, 232), (210, 165, 100)
    img = Image.new("RGB", (S, S), teal)
    d = ImageDraw.Draw(img)
    k = 0.62 if maskable else 0.8          # у maskable рисунок меньше — края обрезает система
    c, u = S / 2, S * k / 24
    ox, oy = c - 12 * u, c - 12 * u + u * 0.5
    P = lambda x, y: (ox + x * u, oy + y * u)
    w = int(u * 1.7)
    d.arc([*P(6, 12), *P(18, 24)], 180, 360, fill=ivory, width=w)
    d.line([P(3.6, 18), P(20.4, 18)], fill=ivory, width=w)
    d.line([P(12, 12), P(12, 9.6)], fill=ivory, width=w)
    d.line([P(10, 9.2), P(14, 9.2)], fill=brass, width=w)
    return img.resize((size, size), Image.LANCZOS)


def cards_from_json(path):
    """Читает cards.json, выносит фото-data-URL в dist/img и возвращает JS-строку с карточками."""
    cards = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(cards, list) or not cards:
        raise SystemExit("cards.json пустой или не список карточек")
    (DIST / "img").mkdir(exist_ok=True)
    saved = 0
    for c in cards:
        for i, step in enumerate(c.get("steps", []), 1):
            m = DATA_URL.match(step.get("photo", "") or "")
            if not m:
                continue
            ext = "jpg" if m.group(1) in ("jpeg", "jpg") else m.group(1)
            name = f"img/{c['id']}-{i}.{ext}"
            (DIST / name).write_bytes(base64.b64decode(m.group(2)))
            step["photo"] = name
            saved += 1
    print(f"Карточки из cards.json: {len(cards)}, фото вынесено: {saved}")
    return "const DEFAULT_CARDS = " + json.dumps(cards, ensure_ascii=False, indent=2) + ";"


def main():
    if DIST.exists():
        shutil.rmtree(DIST)
    (DIST / "icons").mkdir(parents=True)
    body = (SRC / "app.html").read_text(encoding="utf-8")
    body = body.replace('<meta name="claude:viewport-fit-sides" content="cover">\n', "")
    cards_json = SRC / "cards.json"
    if cards_json.exists():
        a, b = body.index("/*CARDS_START*/"), body.index("/*CARDS_END*/")
        body = body[:a] + "/*CARDS_START*/\n" + cards_from_json(cards_json) + "\n" + body[b:]
    body = body.replace('\n<div id="app"', '\n</head>\n<body>\n<div id="app"', 1)
    (DIST / "index.html").write_text(HEAD + body + "\n</body>\n</html>\n", encoding="utf-8")
    for f in ("sw.js", "manifest.webmanifest"):
        shutil.copy(SRC / f, DIST / f)
    if (SRC / "img").exists():
        shutil.copytree(SRC / "img", DIST / "img", dirs_exist_ok=True)
    icon(192).save(DIST / "icons/icon-192.png")
    icon(512).save(DIST / "icons/icon-512.png")
    icon(512, maskable=True).save(DIST / "icons/icon-maskable-512.png")
    icon(180).save(DIST / "icons/apple-touch-icon.png")
    print("Готово:", DIST)


if __name__ == "__main__":
    main()
