# This file is all about the conversation with my macs speakers 
import asyncio
import json
import sounddevice as sd
import numpy as np
import websockets
import wave
import os
from elevenlabs import ElevenLabs
from elevenlabs.conversational_ai.conversation import Conversation
import Config
import requests
from requests.auth import HTTPBasicAuth

import uuid
from pydub import AudioSegment
from pydub.playback import play
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs

# Initialize ElevenLabs client
ELEVEN_LABS_API_KEY = "sk_b93da5f80170383c63661ffdbe7c1923d4dc9a4ba53b8d4b"
ELEVEN_LABS_AGENT_ID = "lBIULzeSraGV3KoxMsuT"

# Audio parameters
SAMPLE_RATE = 24000  # ElevenLabs default
CHANNELS = 1
DURATION = 5  # seconds for each audio clip
FORMAT = np.int16  # 16-bit PCM format

async def record_audio():
    """Captures microphone input and returns audio as numpy array"""
    print("🎤 Recording... Speak now!")
    audio_data = sd.rec(
        int(DURATION * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype=FORMAT
    )
    sd.wait()
    print("✅ Recording finished!")
    return audio_data

async def play_audio(audio_data):
    """Plays received AI-generated audio using computer speakers."""
    print("🔊 Playing response...")
    sd.play(audio_data, samplerate=SAMPLE_RATE)
    sd.wait()
    print("✅ Playback finished!")

async def elevenlabs_conversation():
    """Handles real-time conversation using ElevenLabs."""
    uri = f"wss://api.elevenlabs.io/v1/conversations/{ELEVEN_LABS_AGENT_ID}/stream"

    headers = [("Authorization", f"Bearer {ELEVEN_LABS_API_KEY}")]
    async with websockets.connect(uri, extra_headers=headers) as ws:
        print("🎙️ Connected to ElevenLabs AI Agent!")

        # Start conversation with a specific voice ID
        await ws.send(json.dumps({
            "action": "start",
            "voice_id": Config.chat_history['voiceID']  # 👈 Pass your new voice ID here
        }))

        while True:
            # Record user input from the microphone
            user_audio = await record_audio()

            # Send user audio to ElevenLabs
            await ws.send(json.dumps({
                "audio": user_audio.tobytes()
            }))

            # Receive and play AI response
            response = await ws.recv()
            response_data = json.loads(response)

            if "audio" in response_data:
                ai_audio = np.frombuffer(response_data["audio"], dtype=FORMAT)
                await play_audio(ai_audio)

            elif "status" in response_data and response_data["status"] == "disconnected":
                print("🔴 Disconnected from ElevenLabs AI")
                break

#This function cleans audio
def clean_audio_with_elevenlabs(mp3_file_path):
    """Removes background noise from the audio file using ElevenLabs' Audio Isolation API."""
    url = "https://api.elevenlabs.io/v1/audio-isolation"

    with open(mp3_file_path, "rb") as audio_file:
        files = {"audio": audio_file}
        headers = {"xi-api-key": ELEVEN_LABS_API_KEY}

        response = requests.post(url, files=files, headers=headers)

        if response.status_code == 200:
            print("✅ Audio cleaned successfully!")
            cleaned_file_path = f"{mp3_file_path}_cleaned.mp3"

            # Save the cleaned audio
            with open(cleaned_file_path, "wb") as f:
                f.write(response.content)
            return cleaned_file_path  # Return new cleaned file path
        else:
            print(f"❌ Error cleaning audio: {response.status_code} - {response.text}")
            return None  # Return None if cleaning fails
        
def text_to_speech_and_play(text: str):
    # Call ElevenLabs text-to-speech API
    response = Config.eleven_labs.text_to_speech.convert(
        voice_id=Config.chat_history['voiceID'],  # Example voice ID
        output_format="mp3_22050_32",
        text=text,
        model_id="eleven_turbo_v2_5",  # Low latency model
        voice_settings=VoiceSettings(
            stability=0.7,  # More consistent voice
            similarity_boost=1.0,
            style=0.2,  # Slight variation but not too much
            use_speaker_boost=False,
        ),
    )

    # Save to a temporary file
    filename = f"{uuid.uuid4()}.mp3"
    with open(filename, "wb") as f:
        for chunk in response:
            if chunk:
                f.write(chunk)
    
    print(f"✅ Audio saved as {filename}")

    # Load and play the audio
    audio = AudioSegment.from_mp3(filename)
    play(audio)

    # Optional: Delete the file after playing
    os.remove(filename)
