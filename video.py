import os
import requests
import moviepy.editor as mp
import speech_recognition as sr
from flask import Flask, request, jsonify

app = Flask(__name__)

video_path = "react_fdeqwq.mp4"
audio_path = "extracted.wav"
# Cloudinary details
CLOUDINARY_URL = "https://api.cloudinary.com/v1_1/dphzerv30/upload"
UPLOAD_PRESET = "ml_default"

def download_video_from_cloudinary(video_url, save_path):
    """Download video from Cloudinary to a local path."""
    try:
        response = requests.get(video_url, stream=True)
        response.raise_for_status()
        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        print(f"Video downloaded successfully: {save_path}")
        return save_path
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error downloading video: {e}")

def upload_to_cloudinary(file_path):
    """Upload a file to Cloudinary."""
    try:
        with open(file_path, "rb") as file:
            response = requests.post(
                CLOUDINARY_URL,
                files={"file": file},
                data={"upload_preset": UPLOAD_PRESET},
            )
            response.raise_for_status()
            file_url = response.json().get("secure_url")
            print(f"Uploaded file URL: {file_url}")
            return file_url
    except Exception as e:
        raise Exception(f"Failed to upload to Cloudinary: {e}")

def extract_audio_from_video(video_path, audio_path):
    """Extract audio from video and save it as a WAV file."""
    try:
        video = mp.VideoFileClip(video_path)
        audio = video.audio
        audio.write_audiofile(audio_path)
        print(f"Audio extracted to: {audio_path}")
        return audio_path
    except Exception as e:
        raise Exception(f"Error extracting audio: {e}")

def transcribe_audio(audio_path):
    """Transcribe audio using Google Speech Recognition."""
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(audio_path) as source:
            audio_data = recognizer.record(source)
            transcript = recognizer.recognize_google(audio_data)
            print("Transcription successful.")
            return transcript
    except sr.UnknownValueError:
        raise Exception("Google Speech Recognition could not understand the audio")
    except sr.RequestError as e:
        raise Exception(f"Could not request results from Google Speech Recognition service; {e}")
    except Exception as e:
        raise Exception(f"Error transcribing audio: {e}")

@app.route("/process-video", methods=["POST", "GET"])
def process_video():
    """Process video from Cloudinary, upload audio, and return transcription."""
    if request.method == "POST":
        try:
            # Get video URL from request
            video_url = request.json.get("video_url")
            if not video_url:
                return jsonify({"error": "Missing video_url"}), 400

            # Download video from Cloudinary
            download_video_from_cloudinary(video_url, video_path)

            # Extract audio from video
            extract_audio_from_video(video_path, audio_path)

            # Upload audio file to Cloudinary
            audio_url = upload_to_cloudinary(audio_path)

            # Transcribe audio
            transcript = transcribe_audio(audio_path)

            # Cleanup temporary files
            os.remove(video_path)
            os.remove(audio_path)

            return jsonify({"audio_url": audio_url, "transcript": transcript})

        except Exception as e:
            print(f"Error: {str(e)}")  # Log the error for debugging
            return jsonify({"error": str(e)}), 500
    elif request.method == "GET":
        # You can provide a default response or documentation for GET requests if needed.
        return jsonify({"message": "Please use a POST request to send a video URL for processing."}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Use PORT environment variable or default to 5000
    app.run(host="0.0.0.0", port=port, debug=True)
