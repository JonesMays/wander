import threading
from flask import Flask, request, render_template, jsonify
import requests
from twilio.twiml.messaging_response import MessagingResponse
import time
from openai import OpenAI
import time
import datetime
from twilio.rest import Client
import datetime
import json
import os
import re
import Chat
import Config
import Functions
import paho.mqtt.client as mqtt
from elevenlabs import ElevenLabs
from pydub import AudioSegment 
from requests.auth import HTTPBasicAuth
import Eleven

def get_wander_reply(incoming_message):
    
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

    # Submit the thread to the assistant (as a new run)
    run = Config.openAI_client.beta.threads.runs.create(
        thread_id=thread.id, 
        assistant_id=Config.Assistant_ID, 
        tools=[Functions.tools_user_wandered_out, Functions.tools_user_wandered_back,Functions.tools_user_data, {"type": "file_search"}]
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

        if run.status == "requires_action":
            print("Function Calling")
            required_actions = run.required_action.submit_tool_outputs.model_dump()
            print(required_actions)
            tool_outputs = []

            for action in required_actions["tool_calls"]:
                func_name = action['function']['name']
                arguments = json.loads(action['function']['arguments'])

                # This is where they give me their location, tell them something, call 911, or let me speak with them
                if func_name == "user_wandered_out":
                    output = Functions.user_wandered_out(
                    )
                    tool_outputs.append({
                        "tool_call_id": action['id'],
                        "output": output
                    })
                elif func_name == "user_wandered_back":
                    output = Functions.user_wandered_back(
                    )
                    tool_outputs.append({
                        "tool_call_id": action['id'],
                        "output": output
                })
                elif func_name == "user_data":
                    output = Functions.user_data(
                    )
                    tool_outputs.append({
                        "tool_call_id": action['id'],
                        "output": output
                })
                else:
                    raise ValueError(f"Unknown function: {func_name}")

            print("Submitting outputs back to Wander...")
            Config.openAI_client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread.id,
                run_id=run.id,
                tool_outputs=tool_outputs
            )

    print(f"🏁 Run Completed!")

    # Get the latest message from the thread
    message_response = Config.openAI_client.beta.threads.messages.list(thread_id=thread.id)
    messages = message_response.data

    # Get the content of the latest message
    latest_message = messages[0]
    print(f"💬 Response: {latest_message.content[0].text.value}")

    # This saves the messga to chat history
    Config.chat_history['messages'].append({'role': 'assistant', 'content': latest_message.content[0].text.value, 'timestamp': datetime.datetime.now().isoformat()})
    print(Config.chat_history)
    
    return latest_message.content[0].text.value

def get_sms_reply(incoming_message, from_number, to_number):

        # This tells me what is being printed out 
        print(incoming_message)
        print(from_number)
        print(to_number)

        if incoming_message and from_number and to_number:

            if Chat.get_chat(from_number):
                    
                if "Wander STOP" in incoming_message:
                    Config.chat_history['hasSubscribed'] = False
                    Chat.save_chat(from_number, Config.chat_history)
                    resp = MessagingResponse()
                    resp.message("Aww, we'll miss you! If you ever want to keep a loving eye on your dear one again, just send us a text. We're always here for you! 😊")
                    return str(resp)
                    
                else:

                        latest_message = get_wander_reply(incoming_message)

                        # Respond with the latest message from OpenAI and save data 
                        Chat.save_chat(from_number, Config.chat_history)
                        Config.twilio_client.messages.create(
                            body=re.sub(r'【.*?】', '', latest_message),
                            from_=to_number,
                            to=from_number
                        )
                        return latest_message

            else:

                #New wander user yayy!!!!!! 
                Config.chat_history['participants'] = []
                Config.chat_history['messages'] = []
                Config.chat_history['createdAt'] =  datetime.datetime.now().isoformat()
                welcome_message = (
                    "Welcome! 🎉 Your Wander AI bracelet is now connected. Here's how we help:\n"
                    "1. Geofencing: Set safe zones.\n"
                    "2. Alerts: Get notified if boundaries are crossed.\n"
                    "3. Voice Guidance: Use your familiar cloned voice to reassure your loved one.\n"
                    "4. Emergency Contact: Reach out to authorities if needed.\n\n"
                    "We've got you covered! 😊❤️"
                )
                
                resp = MessagingResponse()
                Config.twilio_client.messages.create(
                    body=welcome_message,
                    from_=to_number,
                    to=from_number
                )
                    
                # Introduce a short delay
                time.sleep(3) # 3-second delay
                    
                # Send the contact message
                Config.twilio_client.messages.create(
                    body="Please send me a 1 minute recording of your voice to start",
                    from_=to_number,
                    to=from_number,
                    media_url=[Config.vcard_url]
                )

                Config.chat_history['participants'].append(from_number)
                Config.chat_history['messages'].append({'role': 'assistant', 'content': welcome_message, 'timestamp': datetime.datetime.now().isoformat()})
                Chat.save_chat(from_number, Config.chat_history)
                print("Welcome message send and start up process started")
                return "Welcome message sent"
                
        else:

            resp = MessagingResponse()
            resp.message("Hey there! I'm having a bit of trouble figuring this one out. 😅 You can hit up our founders at 901-628-8162 for some help. Need anything else?")
            return str(resp)
            
app = Flask(__name__)

# Define a route for the root URL
@app.route("/")
def route():
    return "TreeHack!"

@app.route("/respond", methods=['GET', 'POST'])
def reply():
    author = request.values.get('From', None)
    body = request.values.get('Body', None)
    num_media = int(request.values.get('NumMedia', 0))

    incoming_message = body
    from_number = author
    to_number = "+15737875233"

    if num_media > 0:
        media_url = request.values.get('MediaUrl0')  # Get the first media file
        content_type = request.values.get('MediaContentType0')  # File type

        print(f"📩 Received Media: {media_url} ({content_type})")

        # File paths
        original_file_path = f"./audio_{from_number}"
        mp3_file_path = f"./audio_{from_number}.mp3"

        # Determine file extension based on content type
        if content_type == "audio/x-caf":
            original_file_path += ".caf"
            audio_format = "caf"
        elif content_type == "audio/mp4":
            original_file_path += ".mp4"
            audio_format = "mp4"
        elif content_type == "audio/amr":
            original_file_path += ".amr"
            audio_format = "amr"
        else:
            response_message = "Oops! I received an unsupported audio format. Please send MP4, CAF, or AMR. 😊🎵"
            resp = MessagingResponse()
            resp.message(response_message)
            return str(resp)

        # Download the audio file
        response = requests.get(
            media_url, 
            auth=HTTPBasicAuth(Config.account_sid, Config.auth_token)
        )
        if response.status_code == 200:
            with open(original_file_path, "wb") as file:
                file.write(response.content)
            print(f"✅ Audio file downloaded: {original_file_path}")

            # Convert to MP3
            try:
                audio = AudioSegment.from_file(original_file_path, format=audio_format)
                audio.export(mp3_file_path, format="mp3")
                print(f"🎵 Converted to MP3: {mp3_file_path}")

                # 🧼 Clean the audio before processing
                cleaned_mp3_path = Eleven.clean_audio_with_elevenlabs(mp3_file_path)
                if cleaned_mp3_path:
                    mp3_file_path = cleaned_mp3_path  

                # Call ElevenLabs to clone the voice using the received audio
                voice = Config.eleven_labs.clone(
                    name=str(from_number),
                    description="The voice of the care giver for a person with dementia",
                    files=[mp3_file_path],
                )

                Config.chat_history['voiceID'] = voice.voice_id

                response_message = f"Yay, I got your audio message! I'm busy cloning that voice now 🎵. Your Wander will light up to let you know when I'm all done! 😊✨"

                Config.chat_history['messages'].append(
                    {'role': 'user', 'content': f"Audio file received: {media_url}", 'timestamp': datetime.datetime.now().isoformat()}
                )
                Chat.save_chat(from_number, Config.chat_history)

            except Exception as e:
                print(f"❌ Error converting audio: {e}")
                response_message = "Uh-oh! I couldn't process your audio file. Try sending it again in a different format. 😊🎵"

        else:
            response_message = "Oops! I couldn't download your audio file. Try sending it again! 😊🎵"

        # Send response back
        resp = MessagingResponse()
        resp.message(response_message)
        return str(resp)

    else:
        response_message = get_sms_reply(incoming_message, from_number, to_number)
        return response_message

# Called by Wander if the user leaves the geo fence
@app.route('/wandering')
def wandering():
    incoming_message = "The person has left the geofence"
    latest_message = get_wander_reply(incoming_message) 
    return "Tell Wander Webhook worked"

# Called by Wander if the user get back into the fence
@app.route('/not_wandering')
def not_wandering():
    incoming_message = "The person has returned to the geofence"
    latest_message = get_wander_reply(incoming_message) 
    return "Tell Wander Webhook worked"
   
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, ssl_context=('cert.pem', 'key.pem'))

