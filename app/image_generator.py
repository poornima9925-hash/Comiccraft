import os
import re
import time
from io import BytesIO
from urllib.parse import quote
import requests
from PIL import Image, ImageDraw
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

load_dotenv()

HF_API_KEY = os.getenv("HF_API_KEY")

# Cloud models supported on Hugging Face Serverless Inference API
HF_CLOUD_MODELS = [
    "black-forest-labs/FLUX.1-schnell",
    "stabilityai/stable-diffusion-xl-base-1.0",
    "runwayml/stable-diffusion-v1-5",
]


def sanitize_filename(prompt: str) -> str:
    """
    Sanitizes an image prompt string into a safe, unique PNG filename.
    """
    cleaned = re.sub(r"[^a-zA-Z0-9_-]", "_", prompt.strip())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")[:45]
    timestamp = int(time.time() * 1000)
    return f"{cleaned or 'panel'}_{timestamp}.png"


def _generate_via_hf_cloud(prompt: str) -> Image.Image | None:
    """
    Generates an image in the cloud using Hugging Face InferenceClient (0 GB local storage).
    """
    if not HF_API_KEY or HF_API_KEY == "your_huggingface_api_key_here":
        return None

    client = InferenceClient(api_key=HF_API_KEY, timeout=45)
    for model_id in HF_CLOUD_MODELS:
        try:
            print(f"[Cloud Image] Generating via Hugging Face API ({model_id})...")
            image = client.text_to_image(prompt=prompt, model=model_id)
            if image:
                return image
        except Exception as e:
            print(f"[Warning] HF Cloud model {model_id} unavailable: {e}")
            continue
    return None


def _generate_via_pollinations_cloud(prompt: str) -> Image.Image | None:
    """
    Secondary cloud fallback if the HF free-tier token is rate-limited.
    """
    try:
        print("[Cloud Image] Using fast cloud fallback generator...")
        encoded_prompt = quote(prompt)
        seed = int(time.time() * 1000) % 100000
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=512&height=512&seed={seed}&nologo=true"
        response = requests.get(url, timeout=30)
        if response.status_code == 200 and response.content:
            return Image.open(BytesIO(response.content)).convert("RGB")
    except Exception as e:
        print(f"[Warning] Secondary cloud fallback failed: {e}")
    return None


def _create_fallback_image(prompt: str, path: str):
    """
    Creates a local placeholder image if the machine is completely offline.
    """
    img = Image.new("RGB", (512, 512), color=(38, 50, 56))
    draw = ImageDraw.Draw(img)
    draw.rectangle([16, 16, 496, 496], outline=(255, 202, 40), width=4)
    wrapped_text = f"Comic Panel Illustration\n\n{prompt[:180]}"
    draw.text((36, 60), wrapped_text, fill=(255, 255, 255))
    img.save(path)


def generate_image(prompt: str, filename: str = None) -> str:
    """
    Generates a comic-style illustration from the prompt in the cloud
    and saves it under static/panels/.
    """
    if not filename:
        filename = sanitize_filename(prompt)
    if not filename.lower().endswith(".png"):
        filename += ".png"

    path = f"static/panels/{filename}"
    os.makedirs(os.path.dirname(path), exist_ok=True)

    # 1. Try Hugging Face Cloud API first
    image = _generate_via_hf_cloud(prompt)

    # 2. Fallback to secondary cloud image API if HF is busy/rate-limited
    if image is None:
        image = _generate_via_pollinations_cloud(prompt)

    # 3. Save image or create offline placeholder
    if image is not None:
        image.save(path)
        print(f"[Cloud Image] Saved panel to {path}")
    else:
        _create_fallback_image(prompt, path)

    return path