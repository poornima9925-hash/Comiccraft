import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from app.routes import router

# Load environment variables from .env
load_dotenv()

# Ensure required directories exist at startup
os.makedirs("static/panels", exist_ok=True)
os.makedirs("exports", exist_ok=True)
os.makedirs("fonts", exist_ok=True)

app = FastAPI(
    title="ComicCraft - AI Comic Story Creator",
    description="Generate personalized comic book stories and illustrations using Google Gemini and Stable Diffusion.",
    version="1.0.0"
)

# Mount static directories for serving panel images and exported PDFs
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/exports", StaticFiles(directory="exports"), name="exports")

# Include application routes
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)