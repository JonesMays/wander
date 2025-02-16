# This file is all about function calling with OpenAI
import paho.mqtt.client as mqtt
import asyncio
import Eleven  # Assuming this contains your ElevenLabs AI functions
from elevenlabs import Voice, VoiceSettings, text_to_speech, stream
import sounddevice as sd
import numpy as np
import Config
import sounddevice as sd
import numpy as np
import tempfile
import os
import uuid
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
import time
import datetime
from openai import OpenAI

# MQTT Broker Details (Use HiveMQ for free)
MQTT_BROKER = "broker.hivemq.com"  # Public MQTT Broker
MQTT_PORT = 1883
MQTT_TOPIC = "wander/commands"

# This will detect paitent speech
def detect_patient_speech():
    """Detects if the patient is speaking. Returns True if speech is detected."""
    print("🎤 Detecting patient speech...")
    audio_data = sd.rec(int(5 * 24000), samplerate=24000, channels=1, dtype=np.int16)  # Record for 5 sec
    sd.wait()

    # Check if there is significant sound
    if np.max(np.abs(audio_data)) > 500:  # Adjust threshold as needed
        return True
    return False

# This will listen and transcipt the patinet 
def listen_to_patient():
    """Records the patient's response and transcribes it to text."""
    print("🎧 Listening for patient response...")
    audio_data = sd.rec(int(5 * 24000), samplerate=24000, channels=1, dtype=np.int16)
    sd.wait()
    
    # Convert recorded audio to text (mock function, replace with actual speech-to-text)
    transcribed_text = "Patient's spoken words"  # Replace with actual transcription logic
    print(f"📝 Patient said: {transcribed_text}")
    return transcribed_text

# get text 
def get_voice_reply(incoming_message):
    """Processes an incoming message and generates a response."""

    Config.chat_history['messages'].append(
        {'role': 'user', 'content': incoming_message, 'timestamp': datetime.datetime.now().isoformat()}
    )

    formatted_messages = [
        {"role": message['role'], "content": message['content']}
        for message in Config.chat_history['messages'][-10:]
    ]

    # Create a thread with the incoming message
    thread = Config.openAI_client.beta.threads.create(
        messages=formatted_messages
    )

    print(f"👉 Incoming Message: {incoming_message}")

    # Submit the thread to the assistant (as a new run) without function calls
    run = Config.openAI_client.beta.threads.runs.create(
        thread_id=thread.id, 
        assistant_id=Config.Assistant_ID
    )

    print(f"👉 Run Created: {run.id}")

    # Wait for run to complete
    while run.status != "completed":
        run = Config.openAI_client.beta.threads.runs.retrieve(
            thread_id=thread.id, 
            run_id=run.id
        )
        print(f"🏃 Run Status: {run.status}")
        time.sleep(1)

    print(f"🏁 Run Completed!")

    # Get the latest message from the thread
    message_response = Config.openAI_client.beta.threads.messages.list(thread_id=thread.id)
    messages = message_response.data

    # Get the content of the latest message
    latest_message = messages[0]
    print(f"💬 Response: {latest_message.content[0].text.value}")

    # Save the message to chat history
    Config.chat_history['messages'].append(
        {'role': 'assistant', 'content': latest_message.content[0].text.value, 'timestamp': datetime.datetime.now().isoformat()}
    )
    print(Config.chat_history)
    
    return latest_message.content[0].text.value


# Connect to MQTT broker
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to MQTT Broker!")
    else:
        print(f"❌ Failed to connect, return code {rc}")

mqtt_client = mqtt.Client()
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)

mqtt_client.on_connect = on_connect
mqtt_client.loop_start()

#If the user wanders out of the bounds
tools_user_wandered_out = {
    "type": "function",
    "function": {
        "name": "user_wandered_out",
        "description": "This function should be called if the user wandered out or just types WWW",
        "parameters": {}
    }
}

import threading

def user_wandered_out():

    global reminder_active, reminder_thread
    reminder_active = True  # Start reminders

    """Handles the case when the patient wanders out, sending periodic reminders and listening for responses."""

    command = "alert"
    print(f"📡 Publishing MQTT message: {command}")  # ✅ Debug log
    mqtt_client.publish(MQTT_TOPIC, command, retain=True)  # ✅ Publish alert status

    def reminder_loop():
        """Continuously sends reminders every minute unless interrupted by user speech."""
        while reminder_active:

            # Generate AI response
            response_text = get_voice_reply("Give me a message to encourage my patient to come back to their home.")

            # Generate speech and play it
            Eleven.text_to_speech_and_play(response_text)

            # Check if the patient is speaking
            if detect_patient_speech():
                print("🎤 Patient started speaking... Listening mode activated.")
                patient_response = False
                
                if patient_response:
                    # Respond to the patient's speech
                    response_text = get_voice_reply(patient_response)
                    filename = Eleven.text_to_speech_and_play(response_text)

                    if filename and os.path.exists(filename):
                        audio = AudioSegment.from_mp3(filename)
                        play(audio)
                        os.remove(filename)  # Clean up after playing
                    else:
                        print("❌ Error: Could not play the generated response audio file.")
                
                print("✅ Resuming reminders after conversation.")

            print("⏳ Waiting for 1 minute before next reminder...")
            time.sleep(60)  # Wait 1 minute before sending another reminder

    # Start the reminder loop in a background thread
    reminder_thread = threading.Thread(target=reminder_loop, daemon=True)
    reminder_thread.start()

    return "Tell the user that you turned on the wander"

#If the user wanders back into the bounds
tools_user_wandered_back = {
    "type": "function",
    "function": {
        "name": "user_wandered_back",
        "description": "This function should be called if the user wandered back or if the user just types BBB",
        "parameters": {}
    }
}

def user_wandered_back():
    
    global reminder_active
    reminder_active = False 

    command = "safe"
    print(f"📡 Publishing MQTT message: {command}")  # ✅ Debug log
    mqtt_client.publish(MQTT_TOPIC, command, retain=True)  # ✅ Publish "safe" status

     # Generate AI response
    response_text = get_voice_reply("I made it back to my house/location")

    # Generate speech and play it
    filename = Eleven.text_to_speech_and_play(response_text)

    return "Tell the user that you turned off the wander"

#If the user wanders back into the bounds
tools_user_data= {
    "type": "function",
    "function": {
        "name": "user_data",
        "description": "This function should be called if the user ask for data on how their loved ones dementia doing",
        "parameters": {}
    }
}

# This function should update the 11labs voice and tell the arudion how far they can wonder
def user_data():
    #send the png
    
    return "Tell the user that the data is graphed in the png and is based on your limited but current movemement data"