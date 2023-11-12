# First, we import the 'requests' library, which allows us to send HTTP requests in Python.
import requests

CHUNK_SIZE = 1024

XI_API_KEY = "3cd06380b66b2b0b1238146614b2eeb5"
VOICE_ID = "EXAVITQu4vr4xnSDxMaL"
TEXT_TO_SPEAK = "Hi how are you?"
OUTPUT_PATH = "output.mp3"

tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/stream"

headers = {
  "Accept": "application/json",
  "xi-api-key": XI_API_KEY,
  "Content-Type": "application/json"
}

# This is the data that we're going to send with our request. It's a Python dictionary which will be converted into a JSON object.
data = {
  "text": TEXT_TO_SPEAK,
  "model_id": "eleven_multilingual_v1",
  "voice_settings": {
    "stability": 0.5,
    "similarity_boost": 0.8
  }
}

#API call
response = requests.post(tts_url, json=data, headers=headers, stream=True)

# This block of code is saving the streamed audio file to the output path we specified earlier.
with open(OUTPUT_PATH, 'wb') as f:
    for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
        if chunk:
            f.write(chunk)

print(f"Finished writing audio file to {OUTPUT_PATH}")