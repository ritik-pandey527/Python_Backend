import os
import requests
import moviepy.editor as mp
import speech_recognition as sr
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

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
        if os.path.exists(audio_path):
            os.remove(audio_path)

        video = mp.VideoFileClip(video_path)
        audio = video.audio
        audio.write_audiofile(audio_path)
        print(f"Audio extracted to: {audio_path}")

        if not os.path.exists(audio_path):
            raise Exception("Audio extraction failed, file does not exist.")
    except Exception as e:
        raise Exception(f"Error extracting audio: {e}")

def upload_audio_to_cloudinary(file_path):
    """Upload an audio file to Cloudinary and return its URL with the same name."""
    url = f"https://api.cloudinary.com/v1_1/{CLOUD_NAME}/upload"
    try:
        file_name = os.path.basename(file_path)
        data = {
            "upload_preset": UPLOAD_PRESET,
            "public_id": file_name.split('.')[0],
        }
        with open(file_path, "rb") as file:
            files = {
                "file": file
            }
            response = requests.post(url, auth=(API_KEY, API_SECRET), data=data, files=files)
            response.raise_for_status()
            result = response.json()
            print("Uploaded file URL:", result["url"])
            return result["url"]
    except Exception as e:
        raise Exception(f"Error uploading file to Cloudinary: {e}")

def transcribe_audio(audio_path):
    """Transcribe audio from a WAV file using Google Speech Recognition."""
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(audio_path) as source:
            print("Loading audio file...")
            audio_data = recognizer.record(source)
            print("Transcribing audio...")
            transcript = recognizer.recognize_google(audio_data, language="en-US")
            print("Transcription successful.")
            return transcript
    except sr.UnknownValueError:
        raise Exception("Google Speech Recognition could not understand the audio. Check audio quality.")
    except sr.RequestError as e:
        raise Exception(f"Google Speech Recognition service error: {e}")
    except Exception as e:
        raise Exception(f"Error transcribing audio: {e}")

@app.route("/process-video", methods=["POST"])
def process_video():
    """Process video: download, extract audio, and transcribe audio."""
    try:
        video_url = request.json.get("video_url")
        if not video_url:
            return jsonify({"error": "Missing video_url"}), 400

        video_path = "video.mp4"
        audio_path = "geeksforgeeks.wav"

        # Download video
        download_file(video_url, video_path)

        # Extract audio
        extract_audio_from_video(video_path, audio_path)

        # Transcribe audio
        transcript = transcribe_audio(audio_path)

        # Cleanup temporary video file
        os.remove(video_path)

        # Return local audio path and transcription
        return jsonify({
            "audio_path": os.path.abspath(audio_path),
            "transcript": transcript
        })

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Default to port 5000 if not set
    app.run(host="0.0.0.0", port=port, debug=True)
