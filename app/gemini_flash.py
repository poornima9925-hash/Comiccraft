import os
import re
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
FLASH_MODEL_NAME = os.getenv("GEMINI_FLASH_MODEL", "gemini-3.5-flash")


def get_genai_client() -> genai.Client:
    """Initializes and returns the Google Gen AI client."""
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
        raise ValueError("GEMINI_API_KEY is missing or invalid in .env")
    return genai.Client(api_key=GEMINI_API_KEY)


def generate_outline(user_prompt: str) -> list:
    """
    Generates a 5-panel comic layout based on the user's story idea using gemini-3.5-flash.

    Args:
        user_prompt (str): The user's comic idea prompt.

    Returns:
        list: A list of dictionaries, one for each panel.
    """
    prompt = f"""
You are a professional AI comic planner.

Your task is to generate a *strictly formatted* JSON array containing 5 panel descriptions for a comic based on the story idea below:

STORY: "{user_prompt}"

Each JSON object must include:
- "panel" (integer)
- "title" (string)
- "scene_description" (string)
- "image_prompt" (string)

Respond ONLY in this valid JSON format, without any explanations or markdown:
[
  {{
    "panel": 1,
    "title": "Title here",
    "scene_description": "Scene description here",
    "image_prompt": "Image prompt for Stable Diffusion"
  }},
  ...
]
"""

    output_text = ""
    try:
        client = get_genai_client()
        response = client.models.generate_content(
            model=FLASH_MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                thinking_config=types.ThinkingConfig(
                    thinking_level=types.ThinkingLevel.LOW
                ),
            ),
        )
        output_text = (response.text or "").strip()

        print(f"\n=== RAW GEMINI ({FLASH_MODEL_NAME}) RESPONSE ===\n", output_text)

        # Remove any markdown formatting if present
        if output_text.startswith("```json"):
            output_text = output_text.replace("```json", "").replace("```", "").strip()
        elif output_text.startswith("```"):
            output_text = output_text.replace("```", "").strip()

        # Extract JSON array if extra text was included around brackets
        json_match = re.search(r"\[.*\]", output_text, re.DOTALL)
        if json_match:
            output_text = json_match.group(0)

        panel_data = json.loads(output_text)

        # Additional structure validation
        if not isinstance(panel_data, list):
            raise ValueError("Gemini response is not a list.")

        for panel in panel_data:
            if not isinstance(panel, dict) or not all(
                key in panel for key in ("panel", "title", "scene_description", "image_prompt")
            ):
                raise ValueError(f"Invalid panel format or missing keys: {panel}")

        return panel_data

    except json.JSONDecodeError as e:
        print("JSON Decode Error:", e)
        print("Full Text Received:\n", output_text)
        return [{"error": f"JSON parsing failed: {str(e)}"}]

    except Exception as e:
        print("Unexpected Error:", e)
        return [{"error": f"Generation failed: {str(e)}"}]