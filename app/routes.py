import traceback
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.gemini_flash import generate_outline
from app.gemini_pro import generate_story
from app.image_generator import generate_image
from app.layout_builder import build_comic_layout
from app.exporters import save_pdf

router = APIRouter()
templates = Jinja2Templates(directory="templates")


class PromptRequest(BaseModel):
    prompt: str
    character_name: str = "Hero"
    setting: str = "Forest"
    tone: str = "Dramatic"
    style: str = "Comic Book"


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """
    Loads the homepage (index.html) where users submit their story details.
    """
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )


@router.post("/generate", response_class=HTMLResponse)
async def generate_comic(
    request: Request,
    prompt: str = Form(...),
    character_name: str = Form(...),
    setting: str = Form(...),
    tone: str = Form(...),
    style: str = Form(...)
):
    """
    Handles form submission, processes the input using Gemini Flash, Gemini Pro,
    and Stable Diffusion, builds the layout, exports to PDF, and renders comic_preview.html.
    """
    try:
        # Combine user input into a single full prompt
        full_prompt = (
            f"{prompt} "
            f"The main character is {character_name}. "
            f"The setting is a {setting}. "
            f"The tone is {tone}. The art style is {style}."
        )

        # Step 1: Generate panel outline
        outline = generate_outline(full_prompt)
        if not isinstance(outline, list) or not all("image_prompt" in panel for panel in outline):
            error_detail = outline[0].get("error") if isinstance(outline, list) and outline else "Unknown error"
            raise ValueError(f"Invalid outline structure from Gemini response: {error_detail}")

        # Step 2: Generate story
        full_story = generate_story(outline)

        # Step 3: Generate images (append art style to each panel's image prompt)
        images = [
            generate_image(f"{panel['image_prompt']}, {style} style")
            for panel in outline
        ]

        # Step 4: Layout
        layout = build_comic_layout(images, full_story, outline)

        # Step 5: Export to PDF
        pdf_path = save_pdf(layout)
        web_pdf_path = "/" + pdf_path.replace("\\", "/")  # make path safe for web

        return templates.TemplateResponse(
            request=request,
            name="comic_preview.html",
            context={
                "layout": layout,
                "pdf_path": web_pdf_path
            }
        )

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-comic/json")
async def generate_comic_json(payload: PromptRequest):
    """
    JSON API route that accepts a PromptRequest payload, triggers the full
    AI comic generation workflow, and returns layout data and PDF path.
    """
    try:
        full_prompt = (
            f"{payload.prompt} "
            f"The main character is {payload.character_name}. "
            f"The setting is a {payload.setting}. "
            f"The tone is {payload.tone}. The art style is {payload.style}."
        )

        outline = generate_outline(full_prompt)
        if not isinstance(outline, list) or not all("image_prompt" in panel for panel in outline):
            error_detail = outline[0].get("error") if isinstance(outline, list) and outline else "Unknown error"
            raise ValueError(f"Invalid outline structure from Gemini response: {error_detail}")

        full_story = generate_story(outline)
        images = [
            generate_image(f"{panel['image_prompt']}, {payload.style} style")
            for panel in outline
        ]
        layout = build_comic_layout(images, full_story, outline)
        pdf_path = save_pdf(layout)
        web_pdf_path = "/" + pdf_path.replace("\\", "/")

        return {
            "status": "success",
            "layout": layout,
            "pdf_path": web_pdf_path
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export-success", response_class=HTMLResponse)
async def export_success(request: Request, pdf_path: str = ""):
    """
    Displays a confirmation message after the comic PDF is downloaded.
    """
    return templates.TemplateResponse(
        request=request,
        name="export_success.html",
        context={
            "pdf_path": pdf_path
        }
    )


@router.get("/test-image")
async def test_image(prompt: str = "A futuristic city at sunset, sci-fi, cinematic, artstation"):
    """
    Developer utility route to test Stable Diffusion image generation standalone.
    """
    try:
        image_path = generate_image(prompt)
        return {
            "message": "Image generated successfully",
            "path": "/" + image_path.replace("\\", "/")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))