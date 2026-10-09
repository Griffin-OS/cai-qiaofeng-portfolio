"""Custom high-resolution PPTX-to-PDF renderer for this one-page resume.

It intentionally avoids PowerPoint's PDF exporter.  It composites source PNGs and
PPTX drawing instructions at a configurable raster resolution, then embeds the
lossless result in a PDF and adds URI annotations from the source deck.
"""
from __future__ import annotations

import argparse
import io
import json
import math
import os
import re
import sys
import zipfile
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_MANIFEST = SCRIPT_DIR / "templates" / "cai_qiaofeng_resume_manifest.json"
PAGE_W_PT = 540.0
PAGE_H_PT = 780.0

THEME = {
    "bg1": "FFFFFF",
    "tx1": "000000",
    "bg2": "E8E8E8",
    "tx2": "0E2841",
    "accent1": "156082",
    "accent2": "E97132",
    "accent3": "196B24",
    "accent4": "0F9ED5",
    "accent5": "A02B93",
    "accent6": "4EA72E",
}
FONT_REGULAR = Path(r"C:\Windows\Fonts\msyh.ttc")
FONT_BOLD = Path(r"C:\Windows\Fonts\msyhbd.ttc")
FONT_LIGHT = Path(r"C:\Windows\Fonts\msyhl.ttc")
FONT_SANS = Path(r"C:\Windows\Fonts\bahnschrift.ttf")


def clamp(value: float, lower: int = 0, upper: int = 255) -> int:
    return max(lower, min(upper, int(round(value))))


def rgb(value: str | None, alpha: int = 255) -> tuple[int, int, int, int]:
    value = (value or "000000").lstrip("#")
    if len(value) != 6:
        return (0, 0, 0, alpha)
    return (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16), alpha)


def color_of(spec: dict | None, default: str = "000000") -> tuple[int, int, int, int]:
    if not spec:
        return rgb(default)
    kind = spec.get("kind")
    value = spec.get("val")
    if kind == "schemeClr":
        value = THEME.get(value, default)
    return rgb(value or default)


@lru_cache(maxsize=256)
def font_for(path: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(path, max(1, size), index=0)
    except OSError:
        return ImageFont.truetype(str(FONT_REGULAR), max(1, size), index=0)


def choose_font(run: dict, px_size: int) -> ImageFont.FreeTypeFont:
    props = (run or {}).get("run_properties") or {}
    attrs = props.get("attrs") or {}
    typeface = " ".join(
        str((props.get(key) or {}).get("typeface") or "")
        for key in ("east_asian", "latin", "complex_script")
    ).lower()
    if attrs.get("b") in {"1", 1, True} or "medium" in typeface or "bold" in typeface or "ding" in typeface:
        path = FONT_BOLD
    elif "light" in typeface:
        path = FONT_LIGHT
    elif any(x in typeface for x in ("bahnschrift", "aptos")):
        path = FONT_SANS
    else:
        path = FONT_REGULAR
    return font_for(str(path), px_size)


def has_bold(run: dict) -> bool:
    props = (run or {}).get("run_properties") or {}
    attrs = props.get("attrs") or {}
    face = " ".join(str((props.get(k) or {}).get("typeface") or "") for k in ("east_asian", "latin")).lower()
    return attrs.get("b") in {"1", 1, True} or "medium" in face or "bold" in face or "ding" in face


def run_color(run: dict, default: tuple[int, int, int, int] = (0, 0, 0, 255)) -> tuple[int, int, int, int]:
    props = (run or {}).get("run_properties") or {}
    fill = props.get("fill")
    if fill and fill.get("type") == "solidFill":
        return color_of(fill.get("color"), "000000")
    return default


def flatten(nodes: list[dict]):
    for node in nodes:
        if node.get("type") == "grpSp":
            yield from flatten(node.get("children", []))
        else:
            yield node


def rect_px(node: dict, scale: float) -> tuple[int, int, int, int]:
    r = node.get("render_bounds_slide_pt") or node.get("transform") or {}
    x = (r.get("x") if "x" in r else r.get("x_pt", 0)) * scale
    y = (r.get("y") if "y" in r else r.get("y_pt", 0)) * scale
    w = (r.get("w") if "w" in r else r.get("w_pt", 0)) * scale
    h = (r.get("h") if "h" in r else r.get("h_pt", 0)) * scale
    return (round(x), round(y), round(x + w), round(y + h))


def alpha_modifiers(node: dict, im: Image.Image) -> Image.Image:
    amount = None
    for adj in node.get("image_adjustments") or []:
        if adj.get("type") == "alphaModFix":
            amount = float((adj.get("attrs") or {}).get("amt", 100000)) / 100000.0
    if amount is None:
        return im
    im = im.convert("RGBA")
    a = im.getchannel("A").point(lambda value: int(value * amount))
    im.putalpha(a)
    return im


def crop_image(im: Image.Image, crop: dict | None) -> Image.Image:
    crop = crop or {}
    if not crop:
        return im
    w, h = im.size
    l = float(crop.get("l", 0)) / 100000.0
    r = float(crop.get("r", 0)) / 100000.0
    t = float(crop.get("t", 0)) / 100000.0
    b = float(crop.get("b", 0)) / 100000.0
    box = (round(w * l), round(h * t), max(round(w * l) + 1, round(w * (1 - r))), max(round(h * t) + 1, round(h * (1 - b))))
    return im.crop(box)


def image_from_pptx(archive: zipfile.ZipFile, manifest: dict, rid: str) -> Image.Image:
    target = (manifest.get("relationships", {}).get(rid) or {}).get("target")
    if not target:
        raise KeyError(f"Image relationship {rid} is missing")
    member = "ppt/" + target.replace("../", "")
    return Image.open(io.BytesIO(archive.read(member))).convert("RGBA")


def paste_picture(base: Image.Image, node: dict, archive: zipfile.ZipFile, manifest: dict, scale: float):
    box = rect_px(node, scale)
    x0, y0, x1, y1 = box
    if x1 <= x0 or y1 <= y0:
        return
    im = image_from_pptx(archive, manifest, node["image_rid"])
    im = alpha_modifiers(node, crop_image(im, node.get("crop")))
    im = im.resize((x1 - x0, y1 - y0), Image.Resampling.LANCZOS)
    name = node.get("name", "")
    # The portrait is a circular crop with a gold halo in the original design.
    if node.get("id") == 13 or "Picture 12" == name:
        diameter = min(x1 - x0, y1 - y0)
        cx, cy = x0 + (x1 - x0) // 2, y0 + (y1 - y0) // 2
        mask = Image.new("L", (diameter, diameter), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, diameter - 1, diameter - 1), fill=255)
        # Preserve the warm outer shadow independently of PDF transparency.
        glow_mask = mask.filter(ImageFilter.GaussianBlur(max(12, int(scale * 3.2))))
        glow = Image.new("RGBA", (diameter, diameter), (201, 169, 79, 0))
        glow.putalpha(glow_mask.point(lambda p: int(p * 0.34)))
        base.alpha_composite(glow, (cx - diameter // 2, cy - diameter // 2))
        clip = Image.new("RGBA", (diameter, diameter), (0, 0, 0, 0))
        src = im.resize((diameter, diameter), Image.Resampling.LANCZOS)
        clip.paste(src, (0, 0), mask)
        base.alpha_composite(clip, (cx - diameter // 2, cy - diameter // 2))
        ring = ImageDraw.Draw(base)
        ring.ellipse((cx - diameter // 2, cy - diameter // 2, cx + diameter // 2 - 1, cy + diameter // 2 - 1), outline=(222, 199, 137, 255), width=max(3, int(scale * 1.1)))
    else:
        base.alpha_composite(im, (x0, y0))


def fill_and_line(base: Image.Image, node: dict, scale: float):
    kind = ((node.get("geometry_detail") or {}).get("preset") or (node.get("geometry") or {}).get("type") or "rect")
    fill_spec = node.get("fill") or {}
    fill = None
    if fill_spec.get("type") == "solidFill":
        fill = color_of(fill_spec.get("color"))
    line_spec = node.get("line") or {}
    line_fill = line_spec.get("fill") or {}
    line_color = color_of(line_fill.get("color"), "000000") if line_fill.get("type") == "solidFill" else None
    if fill is None and line_color is None:
        return
    width_pt = line_spec.get("width_pt") or 0
    width = max(1, round(width_pt * scale)) if line_color and width_pt else 0
    x0, y0, x1, y1 = rect_px(node, scale)
    if x1 <= x0 or y1 <= y0:
        return
    draw = ImageDraw.Draw(base)
    if kind == "ellipse":
        draw.ellipse((x0, y0, x1 - 1, y1 - 1), fill=fill, outline=line_color, width=width or 1 if line_color else 1)
    elif kind == "rtTriangle":
        # In the resume this is a subtle upper-right white folded-corner decoration.
        draw.polygon([(x0, y0), (x1 - 1, y0), (x1 - 1, y1 - 1)], fill=fill)
    elif kind == "line":
        if line_color:
            draw.line((x0, y0, x1, y1), fill=line_color, width=max(1, width))
    elif kind == "rect":
        draw.rectangle((x0, y0, x1 - 1, y1 - 1), fill=fill, outline=line_color, width=width or 1 if line_color else 1)
    elif fill:
        # Tiny freeforms are purely ornamental contact icons / link arrow. A compact
        # filled marker retains their visual weight without flattening the layout.
        draw.rounded_rectangle((x0, y0, x1 - 1, y1 - 1), radius=max(1, min(x1 - x0, y1 - y0) // 4), fill=fill, outline=line_color, width=width or 1 if line_color else 1)


def connector(base: Image.Image, node: dict, scale: float):
    line = node.get("line") or {}
    fill = line.get("fill") or {}
    if fill.get("type") != "solidFill":
        return
    c = color_of(fill.get("color"))
    width = max(1, round((line.get("width_pt") or 0.6) * scale))
    x0, y0, x1, y1 = rect_px(node, scale)
    draw = ImageDraw.Draw(base)
    dash = ((line.get("dash") or {}).get("val") or "").lower()
    if dash in {"sysdot", "dot"} and (x0 != x1 or y0 != y1):
        distance = math.hypot(x1 - x0, y1 - y0)
        step = max(width * 4, round(scale * 3.2))
        for pos in range(0, max(1, int(distance)), step):
            frac = pos / distance
            px = round(x0 + (x1 - x0) * frac)
            py = round(y0 + (y1 - y0) * frac)
            draw.ellipse((px - max(1, width // 2), py - max(1, width // 2), px + max(1, width // 2), py + max(1, width // 2)), fill=c)
    elif dash in {"dash", "sysdash"} and (x0 != x1 or y0 != y1):
        distance = math.hypot(x1 - x0, y1 - y0)
        stride = max(width * 8, round(scale * 6))
        chunk = stride * 0.55
        pos = 0.0
        while pos < distance:
            a, b = pos / distance, min(distance, pos + chunk) / distance
            draw.line((round(x0 + (x1-x0)*a), round(y0 + (y1-y0)*a), round(x0 + (x1-x0)*b), round(y0 + (y1-y0)*b)), fill=c, width=width)
            pos += stride
    else:
        draw.line((x0, y0, x1, y1), fill=c, width=width)


def tokenize(text: str) -> list[str]:
    # Keep natural Latin words together but permit Chinese line breaking.
    parts = re.findall(r"[A-Za-z0-9.+/@××_\-]+|\s+|[^A-Za-z0-9.+/@××_\-\s]", text or "")
    return parts or [""]


def styled_tokens(text_node: dict, scale: float):
    paragraphs = (text_node.get("text") or {}).get("paragraphs") or []
    result = []
    for paragraph in paragraphs:
        runs = paragraph.get("runs") or []
        pprops = (paragraph.get("paragraph_properties") or {}).get("attrs") or {}
        styles = []
        for run in runs:
            raw = run.get("text", "")
            props = run.get("run_properties") or {}
            attrs = props.get("attrs") or {}
            size_pt = float(attrs.get("sz", 1050)) / 100.0
            font = choose_font(run, max(1, round(size_pt * scale)))
            styles.append((raw, font, run_color(run), has_bold(run), size_pt * scale, attrs.get("i") in {"1", 1, True}))
        if not styles and paragraph.get("text"):
            pseudo = {"run_properties": {"attrs": {"sz": "1050"}}}
            styles.append((paragraph["text"], choose_font(pseudo, round(10.5 * scale)), (0, 0, 0, 255), False, 10.5 * scale, False))
        result.append((styles, pprops))
    return result


def measure(font: ImageFont.FreeTypeFont, value: str) -> float:
    if not value:
        return 0.0
    return float(font.getlength(value))


def line_height(font: ImageFont.FreeTypeFont, fallback: float) -> float:
    bbox = font.getbbox("Ag中文")
    return max(fallback * 1.13, (bbox[3] - bbox[1]) * 1.15)


def text_draw_ops(node: dict, scale: float):
    x0, y0, x1, y1 = rect_px(node, scale)
    body = (node.get("text") or {}).get("body_properties") or {}
    l_ins = float(body.get("lIns", 0)) / 12700.0 * scale
    r_ins = float(body.get("rIns", 0)) / 12700.0 * scale
    t_ins = float(body.get("tIns", 0)) / 12700.0 * scale
    b_ins = float(body.get("bIns", 0)) / 12700.0 * scale
    content_x0 = x0 + l_ins
    content_x1 = x1 - r_ins
    content_y0 = y0 + t_ins
    content_y1 = y1 - b_ins
    width = max(1, content_x1 - content_x0)
    lines: list[tuple[list[tuple[str, ImageFont.FreeTypeFont, tuple[int, int, int, int], bool, bool]], str, float]] = []
    for styles, pprops in styled_tokens(node, scale):
        all_tokens = []
        for raw, font, color, bold, px_size, italic in styles:
            for token in tokenize(raw):
                all_tokens.append((token, font, color, bold, italic, px_size))
        current = []
        used = 0.0
        max_px = 0.0
        for token in all_tokens:
            token_width = measure(token[1], token[0])
            is_break = token == "\n"
            if is_break or (current and used + token_width > width and token[0].strip()):
                lines.append((current, pprops.get("algn", "l"), max_px))
                current = []
                used = 0.0
                max_px = 0.0
                if is_break:
                    continue
                if token[0].isspace():
                    continue
            current.append(token)
            used += token_width
            max_px = max(max_px, token[5])
        if current:
            lines.append((current, pprops.get("algn", "l"), max_px))
        elif not all_tokens:
            lines.append(([], pprops.get("algn", "l"), 10.5 * scale))
    if not lines:
        return []
    total_height = 0.0
    heights = []
    for line, _align, max_px in lines:
        ref_font = line[0][1] if line else font_for(str(FONT_REGULAR), max(1, int(max_px)))
        h = line_height(ref_font, max_px)
        heights.append(h)
        total_height += h
    anchor = body.get("anchor", "t")
    if anchor == "ctr":
        y = content_y0 + max(0, (content_y1 - content_y0 - total_height) / 2)
    elif anchor == "b":
        y = content_y1 - total_height
    else:
        y = content_y0
    ops = []
    for (line, align, _max_px), h in zip(lines, heights):
        width_line = sum(measure(font, text) for text, font, *_ in line)
        if align == "ctr":
            x = content_x0 + max(0, (width - width_line) / 2)
        elif align == "r":
            x = content_x1 - width_line
        else:
            x = content_x0
        for text, font, color, bold, italic, _sz in line:
            if text:
                ops.append((round(x), round(y), text, font, color, bold, italic))
            x += measure(font, text)
        y += h
    return ops


def draw_text(base: Image.Image, node: dict, scale: float):
    ops = text_draw_ops(node, scale)
    if not ops:
        return
    # Render a restrained glow under the yellow technical descriptor. It is kept
    # as pixels so dark backgrounds do not flatten it during PDF serialization.
    if node.get("id") == 16:
        layer = Image.new("L", base.size, 0)
        ld = ImageDraw.Draw(layer)
        for x, y, text, font, _color, _bold, _italic in ops:
            ld.text((x, y), text, font=font, fill=200, stroke_width=0)
        layer = layer.filter(ImageFilter.GaussianBlur(max(2, int(scale * 0.65))))
        glow = Image.new("RGBA", base.size, (241, 227, 198, 0))
        glow.putalpha(layer.point(lambda p: int(p * 0.45)))
        base.alpha_composite(glow)
    draw = ImageDraw.Draw(base)
    for x, y, text, font, c, bold, italic in ops:
        # Pillow's FreeType renderer stays sharp at the chosen output resolution.
        draw.text((x, y), text, font=font, fill=c, stroke_width=0)


def add_custom_arrow(base: Image.Image, node: dict, scale: float):
    # Link-arrow freeform in the upper-right callout.
    if node.get("id") != 121:
        return False
    x0, y0, x1, y1 = rect_px(node, scale)
    color = (181, 142, 59, 255)
    draw = ImageDraw.Draw(base)
    thickness = max(2, int(scale * 0.45))
    draw.line((x0, y1 - thickness, x1 - thickness, y0 + thickness), fill=color, width=thickness)
    draw.line((x1 - thickness * 3, y0 + thickness, x1 - thickness, y0 + thickness), fill=color, width=thickness)
    draw.line((x1 - thickness, y0 + thickness, x1 - thickness, y0 + thickness * 3), fill=color, width=thickness)
    return True


def render(dpi: int, output_png: Path, source: Path, manifest_path: Path):
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    scale = dpi / 72.0
    width, height = round(PAGE_W_PT * scale), round(PAGE_H_PT * scale)
    base = Image.new("RGBA", (width, height), (255, 255, 255, 255))
    with zipfile.ZipFile(source) as archive:
        for node in flatten(manifest["top_level_nodes"]):
            t = node.get("type")
            if t == "pic":
                paste_picture(base, node, archive, manifest, scale)
            elif t == "cxnSp":
                connector(base, node, scale)
            elif t == "sp":
                if not add_custom_arrow(base, node, scale):
                    fill_and_line(base, node, scale)
                draw_text(base, node, scale)
    output_png.parent.mkdir(parents=True, exist_ok=True)
    base.convert("RGB").save(output_png, format="PNG", compress_level=6, optimize=False, dpi=(dpi, dpi))
    return manifest


def make_pdf(png_path: Path, output_pdf: Path, manifest: dict):
    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(output_pdf), pagesize=(PAGE_W_PT, PAGE_H_PT), pageCompression=1)
    c.setTitle("蔡峤峰｜简历")
    c.setAuthor("蔡峤峰")
    c.setSubject("High-resolution resume generated with a custom source-aware renderer")
    c.drawImage(ImageReader(str(png_path)), 0, 0, width=PAGE_W_PT, height=PAGE_H_PT, mask="auto")
    for link in manifest.get("custom_pdf_annotation_plan", []):
        rect = link.get("bounds_pt_top_left") or link.get("rect_pt_top_left") or link.get("rect")
        if not rect:
            continue
        x, y, w, h = rect["x"], rect["y"], rect["w"], rect["h"]
        c.linkURL(link.get("target") or link["url"], (x, PAGE_H_PT - y - h, x + w, PAGE_H_PT - y), relative=0, thickness=0)
    c.showPage()
    c.save()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dpi", type=int, default=600)
    parser.add_argument("--source", required=True, help="The PPTX to render (same design schema as this template).")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST), help="Source-aware drawing manifest for the PPTX template.")
    parser.add_argument("--png", help="Optional lossless intermediate PNG path. Defaults beside the PDF.")
    parser.add_argument("--pdf", required=True)
    args = parser.parse_args()
    pdf = Path(args.pdf).resolve()
    png = Path(args.png).resolve() if args.png else pdf.with_suffix(".png")
    source = Path(args.source).resolve()
    manifest_path = Path(args.manifest).resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    if not manifest_path.is_file():
        raise FileNotFoundError(manifest_path)
    manifest = render(args.dpi, png, source, manifest_path)
    make_pdf(png, pdf, manifest)
    print(f"PNG={png}")
    print(f"PDF={pdf}")
    print(f"DPI={args.dpi}")


if __name__ == "__main__":
    main()
