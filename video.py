import os
import requests
import moviepy.editor as mp
import speech_recognition as sr
from flask import Flask, request, jsonify

app = Flask(__name__)

# Set the maximum file size for uploads (e.g., 50 MB)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB

# Ensure directories for video and audio files exist
VIDEO_DIR = 'videos'
AUDIO_DIR = 'audio'

os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)

video_path = os.path.join(VIDEO_DIR, "react_fdeqwq.mp4")
audio_path = os.path.join(AUDIO_DIR, "geeksforgeeks.wav")
audio_download_path = os.path.join(AUDIO_DIR, "local_audio.wav")  # Local path to save the extracted audio

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
    """Process video from Cloudinary, download audio locally, and return transcription."""
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

            # Save the extracted audio locally (skip upload to Cloudinary)
            os.rename(audio_path, audio_download_path)  # Rename the audio file for download
            print(f"Audio saved locally at: {audio_download_path}")

            # Transcribe audio
            transcript = transcribe_audio(audio_download_path)

            # Cleanup temporary files
            os.remove(video_path)
            os.remove(audio_download_path)

            return jsonify({"audio_download_url": audio_download_path, "transcript": transcript})

        except Exception as e:
            print(f"Error: {str(e)}")  # Log the error for debugging
            return jsonify({"error": str(e)}), 500
    elif request.method == "GET":
        # You can provide a default response or documentation for GET requests if needed.
        return jsonify({"message": "Please use a POST request to send a video URL for processing."}), 200

if __name__ == "__main__":
    # For production, we will use Gunicorn (especially when deployed on Heroku or any server)
    app.run(debug=True, host="0.0.0.0", port=5000)
