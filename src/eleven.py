# First, we import the 'requests' library, which allows us to send HTTP requests in Python.
import requests

CHUNK_SIZE = 1024

XI_API_KEY = "215264bda5909baa2209a775039586f4"
VOICE_ID = "3HvsYcfM7edGBSii5w9U"
TEXT_TO_SPEAK = "how is your day?"
# OUTPUT_PATH = "output2.mp3"

tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/stream"

headers = {
  "Accept": "application/json",
  "xi-api-key": XI_API_KEY,
  "Content-Type": "application/json"
}

# 
def generateElevenRecording(textInput):
    # generate a random number from 0 to 1000000
    import random
    randomNum = random.randint(0, 1000000)

    # turn the random number into a string
    randomNumStr = str(randomNum)

    OUTPUT_PATH = "response" + "_" + textInput[:10] + "_" + randomNumStr + ".mp3"
    # This is the data that we're going to send with our request. It's a Python dictionary which will be converted into a JSON object.
    TEXT_TO_SPEAK = textInput
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
    return OUTPUT_PATH

generateElevenRecording("are you feeling happy today? i am jeffrey and I cannot wait to make an announcement!")