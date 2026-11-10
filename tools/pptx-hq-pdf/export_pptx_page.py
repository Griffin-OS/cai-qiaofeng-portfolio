#!/usr/bin/env python3
"""Export one PPTX slide as a searchable PDF; restore clickable web links."""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import fitz
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE


def convert_to_pdf(source: Path, destination: Path) -> str:
    if os.name == "nt":
        try:
            import win32com.client
            app = win32com.client.DispatchEx("PowerPoint.Application")
            app.Visible = 1
            presentation = None
            try:
                presentation = app.Presentations.Open(str(source), True, False, False)
                presentation.ExportAsFixedFormat(str(destination), 2, Intent=2)
                return "PowerPoint (print quality)"
            finally:
                if presentation is not None:
                    presentation.Close()
                app.Quit()
        except ImportError:
            pass
    executable = shutil.which("libreoffice") or shutil.which("soffice")
    if not executable:
        raise RuntimeError("Install PowerPoint + pywin32 (Windows) or LibreOffice.")
    with tempfile.TemporaryDirectory(prefix="pptx-to-pdf-profile-") as profile:
        subprocess.run(
            [executable, f"-env:UserInstallation={Path(profile).as_uri()}",
             "--headless", "--convert-to", "pdf", "--outdir",
             str(destination.parent), str(source)],
            check=True, capture_output=True, text=True,
        )
    generated = destination.parent / (source.stem + ".pdf")
    if generated != destination:
        generated.replace(destination)
    if not destination.is_file():
        raise RuntimeError("PDF conversion produced no output file.")
    return "LibreOffice (font/layout check required)"


def link_boxes(presentation: Presentation, slide_number: int):
    """Yield hyperlink rectangles; recursively handle PPT group transforms."""
    def walk(shapes, sx=1., sy=1., dx=0., dy=0.):
        for shape in shapes:
            if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
                xf = shape._element.grpSpPr.xfrm
                if not xf.chExt.cx or not xf.chExt.cy:
                    continue
                scale_x = shape.width / xf.chExt.cx
                scale_y = shape.height / xf.chExt.cy
                yield from walk(
                    shape.shapes, sx * scale_x, sy * scale_y,
                    dx + sx * (shape.left - xf.chOff.x * scale_x),
                    dy + sy * (shape.top - xf.chOff.y * scale_y),
                )
                continue
            urls = set()
            try:
                if shape.click_action.hyperlink.address:
                    urls.add(shape.click_action.hyperlink.address)
            except (AttributeError, TypeError):
                pass
            if shape.has_text_frame:
                for paragraph in shape.text_frame.paragraphs:
                    for run in paragraph.runs:
                        if run.hyperlink.address:
                            urls.add(run.hyperlink.address)
            if urls:
                bounds = (dx + sx * shape.left, dy + sy * shape.top,
                          dx + sx * (shape.left + shape.width),
                          dy + sy * (shape.top + shape.height))
                for url in urls:
                    yield bounds, url
    yield from walk(presentation.slides[slide_number - 1].shapes)


def export_slide(source: Path, destination: Path, number: int) -> None:
    source = source.expanduser().resolve()
    destination = destination.expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    presentation = Presentation(source)
    if not 1 <= number <= len(presentation.slides):
        raise ValueError(f"Slide {number} not found; deck has {len(presentation.slides)} slides.")
    with tempfile.TemporaryDirectory(prefix="pptx-hq-export-") as td:
        full_pdf = Path(td) / "all_slides.pdf"
        engine = convert_to_pdf(source, full_pdf)
        original = fitz.open(full_pdf)
        result = fitz.open()
        result.insert_pdf(original, from_page=number - 1, to_page=number - 1,
                          links=True, annots=True)
        page = result[0]
        scale_x = page.rect.width / presentation.slide_width
        scale_y = page.rect.height / presentation.slide_height
        for bounds, url in link_boxes(presentation, number):
            rect = fitz.Rect(bounds[0] * scale_x, bounds[1] * scale_y,
                             bounds[2] * scale_x, bounds[3] * scale_y) & page.rect
            if rect.is_empty or not url.startswith(("https://", "http://")):
                continue
            existing = page.get_links()
            if any(
                item.get("uri") == url
                and fitz.Rect(item["from"]).intersects(rect)
                and (fitz.Rect(item["from"]) & rect).get_area() >= rect.get_area() * .6
                for item in existing
            ):
                continue
            page.insert_link({"kind": fitz.LINK_URI, "from": rect, "uri": url})
        result.set_metadata({"title": source.stem + f" — Slide {number}",
                             "subject": "Vector-first PDF with PPTX hyperlinks restored"})
        result.save(destination, garbage=4, deflate=True)
        result.close()
        original.close()
        print(f"Exported slide {number} using {engine}: {destination}")
    check = fitz.open(destination)
    assert len(check) == 1
    print(f"Check: {len(check[0].get_text())} searchable characters, "
          f"{len(check[0].get_links())} links.")
    check.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pptx", type=Path)
    parser.add_argument("--slide", type=int, default=2)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    export_slide(args.pptx, args.out, args.slide)
