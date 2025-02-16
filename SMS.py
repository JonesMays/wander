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
        tools=[Functions.tools_user_get_current_location, {"type": "file_search"}]
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
                if func_name == "get_social_search":
                    output = Functions.user_get_current_location(
                        isGroupChat=False,
                        conversation_sid=0,
                        name=arguments['name']['name'],
                        address=arguments['location']['address'],
                        area=arguments['location']['area']
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
                    body="Ready to start the setup process?",
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

# Handles when user sends in voice recording of themselves
@app.route("/respond", methods=['GET', 'POST'])
def reply():
    
    author = request.values.get('From', None)
    body = request.values.get('Body', None)

    incoming_message=body
    from_number=author
    to_number="+15737875233"

    return get_sms_reply(incoming_message, from_number, to_number)

#This updates the esp32 that data is posted
@app.route('/wander ', methods=['GET', 'POST'])  # ✅ Allow both GET & POST
def send_command():

    if request.method == 'GET':
        command = request.args.get("command", "")  # ✅ Get data from URL
        if command:
            print(f"📡 Publishing MQTT message: {command}")  # ✅ Debug log
            mqtt_client.publish(MQTT_TOPIC, command)  # ✅ Publish to ESP32
            return jsonify({"message": f"Command '{command}' sent!"})
        return jsonify({"error": "No command provided"}), 400

    elif request.method == 'POST':
        data = request.json
        command = data.get("command", "")

        if command:
            print(f"📡 Publishing MQTT message: {command}")  # ✅ Debug log
            mqtt_client.publish(MQTT_TOPIC, command)  # ✅ Publish message
            return jsonify({"message": f"Command '{command}' sent!"})
    
        return jsonify({"error": "No command provided"}), 400
    
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

