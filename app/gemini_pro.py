import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PRO_MODEL_NAME = os.getenv("GEMINI_PRO_MODEL", "gemini-3.5-flash")


def get_genai_client() -> genai.Client:
    """Initializes and returns the Google Gen AI client."""
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
        raise ValueError("GEMINI_API_KEY is missing or invalid in .env")
    return genai.Client(api_key=GEMINI_API_KEY)


def generate_story(outline: list) -> str:
    """
    Generates a detailed comic story with narration and character dialogue
    from a list of comic panel outlines using gemini-3.5-flash.

    Args:
        outline (list): A list of dictionaries representing each comic panel's idea.

    Returns:
        str: The generated comic story text or an error message.
    """
    # Format the panel outline as a numbered list for clarity
    formatted_outline = "\n".join([f"{i + 1}. {item}" for i, item in enumerate(outline)])

    # Construct the prompt
    prompt = f"""
You're a comic book writer.

Given the following panel breakdown, write a comic-style story with engaging narration and character dialogues for each panel.

Panel Outline:
{formatted_outline}

Guidelines:
- Start each panel section strictly with the header format: **Panel 1: [Panel Title]**, **Panel 2: [Panel Title]**, etc.
- Include **CAPTION:**, **NARRATION:**, character dialogue lines, and **IMAGE PROMPT:** reference for each panel.
- Use a fun and engaging tone, like an actual comic book.
- Include narration and clearly marked character lines.
- Keep each panel self-contained but part of a cohesive story.
"""

    try:
        client = get_genai_client()
        response = client.models.generate_content(
            model=PRO_MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(
                    thinking_level=types.ThinkingLevel.MEDIUM
                )
            ),
        )
        return response.text
    except Exception as e:
        return f"Error generating story: {str(e)}"