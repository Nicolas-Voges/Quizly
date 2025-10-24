import yt_dlp
import re
import os
import whisper
from google import genai
import json
from pathlib import Path


def download_audio(url, tmp_filename):
    """Download audio from YouTube to a temporary file.

    This helper writes audio to ``tmp_filename``. It raises on
    failure so the calling view can convert the exception into an
    HTTP response.
    """

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": tmp_filename,
        "quiet": True,
        "noplaylist": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    

def transcribe_audio(tmp_filename):
    """Transcribe the audio file and return the transcript text."""
    model = whisper.load_model("tiny", device="cuda" if os.getenv("WHISPER_USE_CUDA") == "1" else "cpu")
    result = model.transcribe(tmp_filename)
    return result["text"]
    

def generate_quiz_json(transcript_text):
            """Use a language model to produce a quiz JSON from transcript_text.

            Returns a Python dict parsed from the model output.
            """
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

            prompt = f"""
                    Based on the following transcript, generate a quiz in valid JSON format.

                    The quiz must follow this exact structure:

                    {{
                        "title": "Create a concise quiz title based on the topic of the transcript.",
                        "description": "Summarize the transcript in no more than 150 characters. Do not include any quiz questions or answers.",
                        "questions": [
                            {{
                                "question_title": "The question goes here.",
                                "question_options": ["Option A", "Option B", "Option C", "Option D"],
                                "answer": "The correct answer from the above options"
                            }},
                            ...
                            (exactly 10 questions)
                        ]
                    }}

                    Requirements:
                    - Each question must have exactly 4 distinct answer options.
                    - Only one correct answer is allowed per question, and it must be present in 'question_options'.
                    - The output must be valid JSON and parsable as-is (e.g., using Python's json.loads).
                    - Do not include explanations, comments, or any text outside the JSON
                    ---
                    {transcript_text}
                    ---
                    """

            response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
            )

            raw_text = response.text
            cleaned_text = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text.strip(), flags=re.MULTILINE)
            return json.loads(cleaned_text)


def generate_quiz_json_from_url(url):
    """Generate a quiz dict from a YouTube URL.

    This convenience helper downloads the audio for the given YouTube URL
    into the repository `media/audio.m4a` file, transcribes it with Whisper,
    removes the temporary audio file and returns the parsed quiz JSON
    produced by the language model.

    Parameters
    ----------
    url : str
        The YouTube video URL to process.

    Returns
    -------
    dict
        A Python dictionary parsed from the model output matching the
        quiz schema used by this project (title, description, questions).

    Raises
    ------
    Any exception raised by the underlying helpers (`download_audio`,
    `transcribe_audio`, `generate_quiz_json`) is propagated to the caller.

    Side effects
    ------------
    Writes a temporary `media/audio.m4a` file in the project and deletes
    it after transcription.
    """

    audio_path = Path(__file__).resolve().parent.parent.parent / 'media' / 'audio.m4a'

    if audio_path.exists():
        audio_path.unlink()

    tmp_filename = str(audio_path)

    download_audio(url, tmp_filename)

    transcript_text = transcribe_audio(tmp_filename)
    os.remove(tmp_filename)

    return generate_quiz_json(transcript_text)