import os
from datetime import datetime
import requests
from fpdf import FPDF

EXPORT_FOLDER = "exports"
FONT_FOLDER = "fonts"
FONT_PATH = os.path.join(FONT_FOLDER, "DejaVuSans.ttf")
DEJAVU_TTF_URL = (
    "https://raw.githubusercontent.com/reingart/pyfpdf/master/fpdf/font/DejaVuSans.ttf"
)

os.makedirs(EXPORT_FOLDER, exist_ok=True)
os.makedirs(FONT_FOLDER, exist_ok=True)


class PDF(FPDF):
    pass


def ensure_unicode_font() -> bool:
    """
    Ensures DejaVuSans.ttf exists in fonts/ for Unicode PDF rendering.
    Downloads it automatically if not present.
    """
    if os.path.exists(FONT_PATH) and os.path.getsize(FONT_PATH) > 10000:
        return True
    try:
        print("Downloading DejaVuSans.ttf for Unicode PDF generation...")
        resp = requests.get(DEJAVU_TTF_URL, timeout=15)
        if resp.status_code == 200:
            with open(FONT_PATH, "wb") as f:
                f.write(resp.content)
            return True
    except Exception as e:
        print(f"Could not download DejaVuSans.ttf ({e}). Falling back to Helvetica.")
    return False


def save_pdf(layout: list) -> str:
    """
    Compiles the full comic into a multi-page PDF file using the FPDF library.

    Args:
        layout (list): Structured comic layout list from build_comic_layout().

    Returns:
        str: Path to the saved PDF file.
    """
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    has_unicode_font = ensure_unicode_font()
    if has_unicode_font:
        pdf.add_font("DejaVu", "", FONT_PATH, uni=True)
        font_family = "DejaVu"
    else:
        font_family = "Helvetica"

    pdf.set_font(font_family, "", 12)

    for panel in layout:
        image_path = panel["image_path"]
        story_text = panel["text"]
        panel_title = panel.get("title", f"Panel {panel['panel']}")
        scene_desc = panel.get("scene_description", "")

        pdf.add_page()

        # Panel title (no bold required for single TTF weight)
        pdf.set_font(font_family, "", 14)
        header_line = f"Panel {panel['panel']}: {panel_title}"
        if not has_unicode_font:
            header_line = header_line.encode("latin-1", "replace").decode("latin-1")
        pdf.cell(0, 10, header_line, ln=True, align="C")
        pdf.set_font(font_family, "", 12)

        # Image placement
        y_image = 30
        image_height = 100
        spacing_after_image = 15

        if os.path.exists(image_path):
            pdf.image(image_path, x=10, y=y_image, w=pdf.w - 20, h=image_height)
        else:
            pdf.set_y(y_image)
            pdf.multi_cell(0, 10, f"[Image missing: {image_path}]")

        # Text placement below image
        pdf.set_y(y_image + image_height + spacing_after_image)
        story_lines = story_text.strip().splitlines()

        # Remove title line like "**Panel 1: Title**" if present
        if story_lines and story_lines[0].strip().lower().startswith("**panel"):
            story_lines = story_lines[1:]

        cleaned_text = "\n".join(story_lines).strip()
        if scene_desc:
            cleaned_text = f"Scene: {scene_desc}\n\n{cleaned_text}"

        if not has_unicode_font:
            cleaned_text = cleaned_text.encode("latin-1", "replace").decode("latin-1")

        pdf.multi_cell(0, 8, cleaned_text)

    # Save with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"comic_{timestamp}.pdf"
    pdf_path = os.path.join(EXPORT_FOLDER, filename)
    pdf.output(pdf_path)
    return pdf_path