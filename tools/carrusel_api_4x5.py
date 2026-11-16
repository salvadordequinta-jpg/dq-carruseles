#!/usr/bin/env python3
"""Carruseles Luis de Quinta Inmobiliaria para publicacion automatica (API Instagram).
Formato 1080x1350 (4:5). La cuadricula del perfil recorta a 3:4 (34 px por lado),
por eso el margen lateral es de 96 px y nada importante toca los bordes.

Uso: python3 carrusel_api_4x5.py spec.json carpeta_salida
spec.json: {"id":"2026-11-12","slides":[{"kicker":"...","title":"...","body":"...","cta":false}, ...]}
Salida: slide_1.jpg ... slide_N.jpg (JPEG, <8 MB) + grid_preview.jpg
Necesita ./fonts/Poppins-*.ttf y ./assets/logo_rgba.png (o rutas en env FONTS_DIR / LOGO).
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1350
M = 96
NAVY = (19, 43, 77)
NAVY_DARK = (9, 19, 38)
TEAL = (10, 129, 159)
WHITE = (255, 255, 255)
SOFT = (214, 226, 238)
HANDLE = "@inmobiliarialuisdequinta"

FD = os.environ.get("FONTS_DIR", "fonts")
LOGO = os.environ.get("LOGO", "assets/logo_rgba.png")


def font(w, s):
    return ImageFont.truetype(os.path.join(FD, f"Poppins-{w}.ttf"), s)


def wrap(draw, text, f, maxw):
    lines = []
    for para in text.split("\n"):
        words, cur = para.split(), ""
        for w in words:
            t = (cur + " " + w).strip()
            if draw.textlength(t, font=f) <= maxw:
                cur = t
            else:
                if cur:
                    lines.append(cur)
                cur = w
        lines.append(cur)
    return lines


def draw_block(draw, y, text, weight, size, color, maxw, lh, min_size, max_h):
    s = size
    while True:
        f = font(weight, s)
        lines = wrap(draw, text, f, maxw)
        h = len(lines) * int(s * lh)
        if h <= max_h or s <= min_size:
            break
        s -= 4
    for ln in lines:
        draw.text((M, y), ln, font=f, fill=color)
        y += int(s * lh)
    return y


def render(slide, idx, total, logo):
    cta = slide.get("cta", False)
    bg = TEAL if cta else NAVY
    im = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(im)
    maxw = W - 2 * M
    accent = WHITE if cta else TEAL
    # linea de acento + kicker
    y = 150
    d.rectangle([M, y, M + 80, y + 8], fill=accent)
    y += 40
    if slide.get("kicker"):
        d.text((M, y), slide["kicker"].upper(), font=font("SemiBold", 34), fill=accent)
        y += 80
    hook = idx == 1
    y = draw_block(d, y, slide["title"], "Bold", 112 if hook else 96, WHITE, maxw,
                   1.12, 72, 560 if hook else 470)
    y += 50
    if slide.get("body"):
        draw_block(d, y, slide["body"], "Regular", 42, WHITE if cta else SOFT, maxw,
                   1.45, 34, H - y - 260)
    # pie: logo + handle + contador
    lg = logo.copy()
    lg.thumbnail((110, 132))
    ly = H - 96 - lg.size[1]
    im.paste(lg, (M, ly), lg)
    d.text((M + lg.size[0] + 28, ly + lg.size[1] // 2 - 18), HANDLE,
           font=font("Medium", 28), fill=WHITE if cta else SOFT)
    cnt = f"{idx}/{total}"
    cf = font("Medium", 28)
    d.text((W - M - d.textlength(cnt, font=cf), ly + lg.size[1] // 2 - 18), cnt,
           font=cf, fill=WHITE if cta else SOFT)
    return im


def grid_preview(covers, labels, out):
    """Simula la cuadricula del perfil: miniaturas recortadas a 3:4 desde el centro."""
    tw, th = 360, 480
    cols = 3
    rows = (len(covers) + cols - 1) // cols
    pad, top = 6, 70
    g = Image.new("RGB", (cols * tw + (cols + 1) * pad, top + rows * (th + pad) + pad + 40), (255, 255, 255))
    d = ImageDraw.Draw(g)
    d.text((pad + 4, 18), "Vista previa de la cuadrícula del perfil (recorte 3:4)",
           font=font("SemiBold", 26), fill=(30, 30, 30))
    for i, c in enumerate(covers):
        cw = int(H * 3 / 4)  # 1012
        x0 = (W - cw) // 2
        crop = c.crop((x0, 0, x0 + cw, H)).resize((tw, th), Image.LANCZOS)
        x = pad + (i % cols) * (tw + pad)
        y = top + (i // cols) * (th + pad)
        g.paste(crop, (x, y))
        lf = font("SemiBold", 20)
        lw = d.textlength(labels[i], font=lf)
        d.rectangle([x + tw - lw - 22, y + 8, x + tw - 8, y + 38], fill=(255, 255, 255))
        d.text((x + tw - lw - 15, y + 10), labels[i], font=lf, fill=(19, 43, 77))
    d.text((pad + 4, g.size[1] - 34), "La más reciente aparece arriba a la izquierda.",
           font=font("Regular", 20), fill=(90, 90, 90))
    g.save(out, quality=92)


def main(spec_path, outdir):
    spec = json.load(open(spec_path, encoding="utf-8"))
    os.makedirs(outdir, exist_ok=True)
    logo = Image.open(LOGO).convert("RGBA")
    slides = spec["slides"]
    for i, s in enumerate(slides, 1):
        im = render(s, i, len(slides), logo)
        im.save(os.path.join(outdir, f"slide_{i}.jpg"), "JPEG", quality=92, optimize=True)
    print("ok", outdir, len(slides))


if __name__ == "__main__":
    if sys.argv[1] == "--grid":
        # --grid out.jpg label1=dir1 label2=dir2 ... (orden: mas reciente primero)
        out = sys.argv[2]
        pairs = [a.split("=", 1) for a in sys.argv[3:]]
        covers = [Image.open(os.path.join(p, "slide_1.jpg")) for _, p in pairs]
        grid_preview(covers, [l for l, _ in pairs], out)
    else:
        main(sys.argv[1], sys.argv[2])
