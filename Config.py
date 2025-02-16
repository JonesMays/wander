import os
from openai import OpenAI
from twilio.rest import Client
import datetime
import firebase_admin
from firebase_admin import credentials, storage, firestore
from elevenlabs import ElevenLabs
# This files contains all the import key stuff

# Twilio credentials (make sure these are set as environment variables for security)
account_sid = os.environ.get('TWILIO_ACCOUNT_SID', 'xxxxxxxxxxxx')
auth_token = os.environ.get('TWILIO_AUTH_TOKEN', 'xxxxxxxxxx')
twilio_client = Client(account_sid, auth_token)

# OpenAI API and assistant key 
openAI_client = OpenAI(api_key="xxxx")
Assistant_ID = "xxxx"

#Eleven labs api key
eleven_labs = ElevenLabs(
    api_key="xxxxxxxxx",
)

# Firebase credentials for using the platform
#cred = credentials.Certificate('/home/ec2-user/jade_AI/jadeai-77973-firebase-adminsdk-jlw5m-59e0f5a501.json')
cred = credentials.Certificate('/Users/jonesmaysii/Desktop/XcodeP/Opal_AI/jadeai-77973-firebase-adminsdk-jlw5m-59e0f5a501.json')
firebase_admin.initialize_app(cred, {
    'storageBucket': 'jadeai-77973'  # Ensure this is your correct project ID
})
db = firestore.client() 

# Firebase database structure
chat_history = {
    'participants': ['user1'],
    'messages': [
        {'role': 'user', 'content': 'Hello!', 'timestamp': datetime.datetime.now().isoformat()},
    ],
    'fileIDs': [],
    'hasSentShareMessage': False,
    'hasSentReminder': False,
    'hasSubscribed': True,
    'createdAt': datetime.datetime.now().isoformat(),
    'textStop': False,
    'voiceID': ''
}

# url to contact card for the number
vcard_url = 'https://firebasestorage.googleapis.com/v0/b/jadeai-77973/o/Jade%20AI.vcf?alt=media'