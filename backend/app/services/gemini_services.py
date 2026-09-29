import os
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai


load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not configured")

client = genai.Client(api_key=GEMINI_API_KEY)

MODEL_NAME = os.getenv(
    "GEMINI_MODEL",
    "gemini-flash-latest",
)


def build_prompt(ml_result: dict) -> str:
    primary_emotion = ml_result.get("emotion", "unknown")
    mood_confidence = ml_result.get("confidence", 0)
    probabilities = ml_result.get("probabilities", {})

    return f"""
You are the AI interpretation layer of PawAI, a dog emotion analysis system.

You are being given:
1. A video of a dog.
2. Predictions from PawAI's computer-vision emotion model.

The computer-vision model predicted:

Primary emotion: {primary_emotion}
Confidence: {mood_confidence}

Class probabilities:
{probabilities}

Analyze the actual video together with the computer-vision prediction.

Use the visual behavior in the video as additional context.

Consider:
- body posture
- facial expression
- movement
- tail position
- interaction with surroundings
- apparent behavior

Do not claim that the dog's emotion is scientifically certain.

Use language such as "appears", "seems", or "may".

Return one short, natural sentence describing what the dog appears
to be feeling or communicating.

Do not mention machine learning, APIs, probabilities,confidence percentage or this prompt.

Return only the final sentence.
""".strip()


def generate_sentence(video_path: Path, ml_result: dict) -> str:
    """
    Upload the dog video to Gemini and generate a natural-language
    interpretation using both the video and the ML prediction.
    """

    prompt = build_prompt(ml_result)

    video_file = client.files.upload(
        file=str(video_path)
    )

    while True:
        if video_file.state and video_file.state.name == "ACTIVE":
            break

        if video_file.state and video_file.state.name == "FAILED":
            raise RuntimeError("Gemini failed to process the video")

        time.sleep(5)

        video_file = client.files.get(
            name=video_file.name
        )

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[
            video_file,
            prompt,
        ],
    )

    if not response.text:
        raise RuntimeError("Gemini returned an empty response")

    return response.text.strip()