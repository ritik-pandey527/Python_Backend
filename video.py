import os
import requests
import moviepy.editor as mp
import speech_recognition as sr
from flask import Flask, request, jsonify

app = Flask(__name__)

# Cloudinary details
CLOUD_NAME = "dphzerv30"
API_KEY = "729132374995264"
API_SECRET = "ZAhu0TbqppD4vBwx3hnWWRRyMAga"
UPLOAD_PRESET = "ml_default"

def download_file(file_url, save_path):
    """Download a file from a given URL and save it locally."""
    try:
        response = requests.get(file_url, stream=True)
        response.raise_for_status()
        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        print(f"File downloaded successfully: {save_path}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error downloading file: {e}")

def extract_audio_from_video(video_path, audio_path):
    """Extract audio from a video and save it as a WAV file."""
    try:
        video = mp.VideoFileClip(video_path)
        audio = video.audio
        audio.write_audiofile(audio_path)
        print(f"Audio extracted to: {audio_path}")
    except Exception as e:
        raise Exception(f"Error extracting audio: {e}")

def upload_audio_to_cloudinary(file_path):
    """Upload an audio file to Cloudinary and return its secure URL."""
    url = f"https://api.cloudinary.com/v1_1/{CLOUD_NAME}/upload"
    try:
        with open(file_path, "rb") as file:
            data = {
                "upload_preset": UPLOAD_PRESET,
            }
            files = {
                "file": file
            }
            response = requests.post(url, auth=(API_KEY, API_SECRET), data=data, files=files)
            response.raise_for_status()
            result = response.json()
            print("Uploaded file URL:", result["secure_url"])
            return result["secure_url"]
    except Exception as e:
        raise Exception(f"Error uploading file to Cloudinary: {e}")

def transcribe_audio(audio_path):
    """Transcribe audio from a WAV file using Google Speech Recognition."""
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(audio_path) as source:
            audio_data = recognizer.record(source)
            transcript = recognizer.recognize_google(audio_data)
            print("Transcription successful.")
            return transcript
    except Exception as e:
        raise Exception(f"Error transcribing audio: {e}")

@app.route("/process-video", methods=["POST"])
def process_video():
    """Process video: download, extract audio, upload audio, and return JSON response."""
    try:
        # Get video URL from request
        video_url = request.json.get("video_url")
        if not video_url:
            return jsonify({"error": "Missing video_url"}), 400

        # Temporary file paths
        video_path = "video.mp4"
        audio_path = "audio.wav"

        # Download video
        download_file(video_url, video_path)

        # Extract audio
        extract_audio_from_video(video_path, audio_path)

        # Upload audio to Cloudinary
        audio_url = upload_audio_to_cloudinary(audio_path)

        # Transcribe audio
        transcript = transcribe_audio(audio_path)

        # Cleanup temporary files
        os.remove(video_path)
        os.remove(audio_path)

        return jsonify({"audio_url": audio_url, "transcript": transcript})

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Default to port 5000 if not set
    app.run(host="0.0.0.0", port=port, debug=True)
