# This file is all about function calling with OpenAI
import paho.mqtt.client as mqtt

# MQTT Broker Details (Use HiveMQ for free)
MQTT_BROKER = "broker.hivemq.com"  # Public MQTT Broker
MQTT_PORT = 1883
MQTT_TOPIC = "wander/commands"

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

#If the user wants to start the set up processs
tools_user_start = {
    "type": "function",
    "function": {
        "name": "user_start",
        "description": "This function should be called if the user ask to start the set up process or confirms it ",
        "parameters": {
            "type": "object",
            "properties": {
                "caregiver_name": {
                    "type": "string",
                    "description": "The full name of the caregiver."
                },
                "max_wandering_radius_feet": {
                    "type": "number",
                    "description": "The maximum distance (in feet) the patient is allowed to wander before triggering an alert."
                },
                "voice_recording_mp3": {
                    "type": "string",
                    "format": "binary",
                    "description": "A 1-minute MP3 voice recording for the patient."
                }
            },
            "required": ["caregiver_name", "max_wandering_radius_feet", "voice_recording_mp3"]
        }
    }
}

# This function should update the 11labs voice and tell the arudion how far they can wonder
def user_start(caregiver_name: str, max_wandering_radius_feet: float, voice_recording_mp3: bytes):

    print(f"Setup started for caregiver: {caregiver_name}")
    print(f"Allowed wandering radius: {max_wandering_radius_feet} feet")
    print(f"Voice recording received (size: {len(voice_recording_mp3)} bytes)")

    print(f"📡 Publishing MQTT message: {command}")  # ✅ Debug log
    mqtt_client.publish(MQTT_TOPIC, command, retain=True)  # ✅ Publish with retain flag

    return "Tell the user the set up process is complete"

#If the wander sees their loved one has left the geo fence and they want the deivce to bring them back 

#If the wander sees their loved one has left the geo fence and they want a contact to help

#If the wantder see their loved one has left the geo  fence and they want to call the police

#If the wander sees their loved one has re-entered the geo fence
