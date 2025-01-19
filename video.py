import requests
import moviepy.editor as mp
import speech_recognition as sr
from flask import Flask, request, jsonify

app = Flask(__name__)

# Cloudinary details
CLOUDINARY_URL = "https://api.cloudinary.com/v1_1/dphzerv30/upload"
UPLOAD_PRESET = "ml_default"


def download_video(video_url, save_path):
    """Download video from Cloudinary"""
    response = requests.get(video_url, stream=True)
    if response.status_code == 200:
        with open(save_path, "wb") as video_file:
            for chunk in response.iter_content(chunk_size=1024):
                video_file.write(chunk)
        return save_path
    else:
        raise Exception(f"Failed to download video: {response.status_code}")


def extract_audio(video_path, audio_path):
    """Extract audio from video and save as WAV"""
    video = mp.VideoFileClip(video_path)
    audio = video.audio
    audio.write_audiofile(audio_path)
    return audio_path


def upload_to_cloudinary(file_path):
    """Upload file to Cloudinary"""
    with open(file_path, "rb") as file:
        response = requests.post(
            CLOUDINARY_URL,
            files={"file": file},
            data={"upload_preset": UPLOAD_PRESET},
        )
        if response.status_code == 200:
            return response.json()["secure_url"]
        else:
            raise Exception(f"Failed to upload to Cloudinary: {response.json()}")


def transcribe_audio(audio_path):
    """Transcribe audio using SpeechRecognition"""
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio_data = recognizer.record(source)
        transcript = recognizer.recognize_google(audio_data)
    return transcript


@app.route("/process-video", methods=["POST"])
def process_video():
    """Process video from Cloudinary and return transcript"""
    try:
        # Get video URL from request
        video_url = request.json.get("video_url")
        if not video_url:
            return jsonify({"error": "Missing video_url"}), 400

        # Paths
        video_path = "downloaded_video.mp4"
        audio_path = "extracted_audio.wav"

        # Process video and audio
        download_video(video_url, video_path)
        extract_audio(video_path, audio_path)

        # Upload audio to Cloudinary
        audio_url = upload_to_cloudinary(audio_path)

        # Transcribe audio
        transcript = transcribe_audio(audio_path)

        # Return result
        return jsonify({"audio_url": audio_url, "transcript": transcript})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Use PORT environment variable or default to 5000
    app.run(host="0.0.0.0", port=port, debug=True)
