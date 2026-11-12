#!/usr/bin/env python3
"""Export one PPTX slide as a PowerPoint-native, searchable PDF.

Windows PowerPoint is the default engine. LibreOffice is an explicit fallback
because it can substitute fonts and reflow text in complex PowerPoint files.
"""
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


PP_FIXED_FORMAT_PDF = 2
PP_FIXED_FORMAT_INTENT_PRINT = 2
PP_PRINT_OUTPUT_SLIDES = 1
PP_PRINT_SLIDE_RANGE = 4
MSO_FALSE = 0


def export_with_powerpoint(source: Path, destination: Path, slide_number: int) -> None:
    """Ask Windows PowerPoint to create the requested slide directly as PDF."""
    try:
        import pythoncom
        import win32com.client
    except ImportError as exc:
        raise RuntimeError("PowerPoint export requires pywin32.") from exc

    app = None
    presentation = None
    initialized = False
    try:
        pythoncom.CoInitialize()
        initialized = True
        app = win32com.client.DispatchEx("PowerPoint.Application")
        app.Visible = 1
        presentation = app.Presentations.Open(str(source), True, False, False)
        if not 1 <= slide_number <= presentation.Slides.Count:
            raise ValueError(
                f"Slide {slide_number} not found; deck has {presentation.Slides.Count} slides."
            )

        # ExportAsFixedFormat supports a native slide range. This deliberately
        # avoids exporting the whole deck and then rebuilding it with a PDF tool.
        print_options = presentation.PrintOptions
        print_options.Ranges.ClearAll()
        print_range = print_options.Ranges.Add(slide_number, slide_number)
        presentation.ExportAsFixedFormat(
            str(destination),
            PP_FIXED_FORMAT_PDF,
            PP_FIXED_FORMAT_INTENT_PRINT,
            MSO_FALSE,
            1,
            PP_PRINT_OUTPUT_SLIDES,
            MSO_FALSE,
            print_range,
            PP_PRINT_SLIDE_RANGE,
            "",
            True,
            True,
            True,
            False,
            False,
        )
    finally:
        if presentation is not None:
            presentation.Close()
        if app is not None:
            app.Quit()
        if initialized:
            pythoncom.CoUninitialize()

    if not destination.is_file():
        raise RuntimeError("PowerPoint reported success but did not create a PDF.")


def export_with_libreoffice(source: Path, destination: Path, slide_number: int) -> None:
    """Use LibreOffice only when the caller explicitly allows the fallback."""
    executable = shutil.which("libreoffice") or shutil.which("soffice")
    if not executable:
        raise RuntimeError("Install Microsoft PowerPoint + pywin32, or LibreOffice for fallback.")

    with tempfile.TemporaryDirectory(prefix="pptx-to-pdf-profile-") as profile:
        subprocess.run(
            [
                executable,
                f"-env:UserInstallation={Path(profile).as_uri()}",
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                str(destination.parent),
                str(source),
            ],
            check=True,
            capture_output=True,
            text=True,
        )

    full_pdf = destination.parent / f"{source.stem}.pdf"
    if not full_pdf.is_file():
        raise RuntimeError("LibreOffice did not create a PDF.")
    try:
        with fitz.open(full_pdf) as document:
            if not 1 <= slide_number <= len(document):
                raise ValueError(f"Slide {slide_number} not found; PDF has {len(document)} pages.")
            selected = fitz.open()
            selected.insert_pdf(document, from_page=slide_number - 1, to_page=slide_number - 1)
            selected.save(destination, garbage=4, deflate=True)
            selected.close()
    finally:
        if full_pdf != destination and full_pdf.exists():
            full_pdf.unlink()


def link_boxes(presentation: Presentation, slide_number: int):
    """Yield web-link rectangles while preserving nested group transforms."""

    def walk(shapes, sx=1.0, sy=1.0, dx=0.0, dy=0.0):
        for shape in shapes:
            if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
                transform = shape._element.grpSpPr.xfrm
                if not transform.chExt.cx or not transform.chExt.cy:
                    continue
                scale_x = shape.width / transform.chExt.cx
                scale_y = shape.height / transform.chExt.cy
                yield from walk(
                    shape.shapes,
                    sx * scale_x,
                    sy * scale_y,
                    dx + sx * (shape.left - transform.chOff.x * scale_x),
                    dy + sy * (shape.top - transform.chOff.y * scale_y),
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
                bounds = (
                    dx + sx * shape.left,
                    dy + sy * shape.top,
                    dx + sx * (shape.left + shape.width),
                    dy + sy * (shape.top + shape.height),
                )
                for url in urls:
                    if url.startswith(("https://", "http://")):
                        yield bounds, url

    yield from walk(presentation.slides[slide_number - 1].shapes)


def add_missing_links(pdf_path: Path, presentation: Presentation, slide_number: int) -> int:
    """Supplement missing links without redrawing, reflowing, or rasterizing the PDF."""
    document = fitz.open(pdf_path)
    temporary_path = pdf_path.with_name(f"{pdf_path.stem}.links-tmp.pdf")
    try:
        if len(document) != 1:
            raise RuntimeError(f"Expected one PDF page, found {len(document)}.")
        page = document[0]
        scale_x = page.rect.width / presentation.slide_width
        scale_y = page.rect.height / presentation.slide_height
        existing = page.get_links()
        added = 0

        for bounds, url in link_boxes(presentation, slide_number):
            rect = fitz.Rect(
                bounds[0] * scale_x,
                bounds[1] * scale_y,
                bounds[2] * scale_x,
                bounds[3] * scale_y,
            ) & page.rect
            if rect.is_empty:
                continue
            if any(
                item.get("uri") == url
                and fitz.Rect(item["from"]).intersects(rect)
                and (fitz.Rect(item["from"]) & rect).get_area() >= rect.get_area() * 0.6
                for item in existing
            ):
                continue
            page.insert_link({"kind": fitz.LINK_URI, "from": rect, "uri": url})
            existing.append({"uri": url, "from": rect})
            added += 1

        if added:
            document.save(temporary_path, garbage=0, deflate=False)
    finally:
        document.close()

    if added:
        temporary_path.replace(pdf_path)
    return added


def validate_pdf(pdf_path: Path) -> tuple[int, int]:
    """Return searchable character and link counts after reopening the final PDF."""
    with fitz.open(pdf_path) as document:
        if len(document) != 1:
            raise RuntimeError(f"Expected one PDF page, found {len(document)}.")
        page = document[0]
        text_chars = len(page.get_text().strip())
        if not text_chars:
            raise RuntimeError("PDF has no selectable text; refusing to deliver a page image.")
        return text_chars, len(page.get_links())


def export_slide(
    source: Path,
    destination: Path,
    slide_number: int,
    allow_libreoffice_fallback: bool,
    repair_links: bool,
) -> str:
    source = source.expanduser().resolve()
    destination = destination.expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not source.is_file():
        raise FileNotFoundError(source)

    presentation = Presentation(source)
    if not 1 <= slide_number <= len(presentation.slides):
        raise ValueError(f"Slide {slide_number} not found; deck has {len(presentation.slides)} slides.")

    engine = "PowerPoint native PDF"
    try:
        if os.name != "nt":
            raise RuntimeError("Native PowerPoint automation is available only on Windows.")
        export_with_powerpoint(source, destination, slide_number)
    except Exception as exc:
        if not allow_libreoffice_fallback:
            raise RuntimeError(
                "Native PowerPoint export failed. Fix PowerPoint/pywin32, or rerun with "
                "--allow-libreoffice-fallback and perform the required visual comparison."
            ) from exc
        export_with_libreoffice(source, destination, slide_number)
        engine = "LibreOffice fallback (visual comparison required)"

    links_added = add_missing_links(destination, presentation, slide_number) if repair_links else 0
    text_chars, link_count = validate_pdf(destination)
    print(f"Exported slide {slide_number} using {engine}: {destination}")
    print(f"Check: {text_chars} searchable characters, {link_count} links, {links_added} links added.")
    return engine


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pptx", type=Path)
    parser.add_argument("--slide", type=int, default=2)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--allow-libreoffice-fallback",
        action="store_true",
        help="Use LibreOffice only if native PowerPoint export is unavailable; inspect the output manually.",
    )
    parser.add_argument("--skip-link-repair", action="store_true")
    args = parser.parse_args()
    export_slide(
        args.pptx,
        args.out,
        args.slide,
        args.allow_libreoffice_fallback,
        not args.skip_link_repair,
    )

