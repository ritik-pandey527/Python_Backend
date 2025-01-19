from flask import Flask, request, jsonify
import moviepy.editor as mp
import speech_recognition as sr
import requests

app = Flask(__name__)

# Hardcoded Cloudinary credentials (Not recommended for production)
CLOUD_NAME = "dphzerv30"
API_KEY = "729132374995264"
API_SECRET = "ZAhu0TbqppD4vBwx3hnWWRRyMAga"

# Variable to store the transcribed text globally
transcribed_text = ""

def download_file(url, save_path):
    """
    Downloads a file from a given URL to the specified local path.
    """
    response = requests.get(url)
    with open(save_path, "wb") as file:
        file.write(response.content)
    print(f"File downloaded and saved as {save_path}")

def upload_audio_to_cloudinary(file_path):
    """
    Uploads an audio file to Cloudinary using the REST API.
    
    :param file_path: Path to the .wav file
    :return: URL of the uploaded file
    """
    url = f"https://api.cloudinary.com/v1_1/{CLOUD_NAME}/upload"
    with open(file_path, "rb") as file:
        data = {
            "upload_preset": "ml_default",  # Replace with your unsigned upload preset
        }
        files = {
            "file": file
        }
        try:
            response = requests.post(url, auth=(API_KEY, API_SECRET), data=data, files=files)
            response.raise_for_status()
            result = response.json()
            print("Uploaded file URL:", result["secure_url"])
            return result["secure_url"]
        except Exception as e:
            print("Error uploading file:", e)
            return None

def process_video_and_audio(video_path, audio_output_path):
    global transcribed_text  # Use the global variable to store transcribed text
    
    # Load the video
    video = mp.VideoFileClip(video_path)
    
    # Extract the audio from the video
    audio_file = video.audio
    audio_file.write_audiofile(audio_output_path)
    
    # Initialize recognizer
    r = sr.Recognizer()
    
    # Load the audio file
    with sr.AudioFile(audio_output_path) as source:
        data = r.record(source)
    
    # Convert speech to text
    try:
        transcribed_text = r.recognize_google(data)
        print("\nThe resultant text from video is: \n")
        print(transcribed_text)
    except sr.UnknownValueError:
        print("Google Speech Recognition could not understand the audio.")
        transcribed_text = "Error: Could not understand audio."
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service; {e}")
        transcribed_text = "Error: Speech recognition service unavailable."

    # Upload the audio to Cloudinary
    upload_audio_to_cloudinary(audio_output_path)

@app.route('/process_video', methods=['POST'])
def process_video():
    data = request.get_json()
    
    # Extract URL from the request
    file_url = data.get('file_url')

    if not file_url or not CLOUD_NAME or not API_KEY or not API_SECRET:
        return jsonify({"error": "Missing parameters"}), 400

    # Specify the local paths for video and audio files
    save_path = "downloaded_video.mp4"
    audio_output_path = "extracted_audio.wav"

    try:
        # Step 1: Download the video
        download_file(file_url, save_path)

        # Step 2: Process the video (extract audio and upload to Cloudinary)
        process_video_and_audio(save_path, audio_output_path)

        return jsonify({"message": "Video processed successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/out_video', methods=['GET'])
def out_video():
    global transcribed_text
    
    if transcribed_text:
        return jsonify({"transcribed_text": transcribed_text}), 200
    else:
        return jsonify({"error": "No transcription available. Please process a video first."}), 400

if __name__ == '__main__':
    app.run(debug=True)
