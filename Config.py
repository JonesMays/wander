import os
from openai import OpenAI
from twilio.rest import Client
import datetime
import firebase_admin
from firebase_admin import credentials, storage, firestore
# This files contains all the import key stuff

# Twilio credentials (make sure these are set as environment variables for security)
account_sid = os.environ.get('TWILIO_ACCOUNT_SID', 'AC8258d093c21bcf253394dc71fec9fe67')
auth_token = os.environ.get('TWILIO_AUTH_TOKEN', '1b0071d3282e96811f5759b0b09fda07')
twilio_client = Client(account_sid, auth_token)

# OpenAI API and assistant key 
openAI_client = OpenAI(api_key="sk-proj-5vFAPbxha4bnga12s0rlT3BlbkFJON5D9IeQkZh7e5SxwqGi")
Assistant_ID = "asst_dILO5bb8bq3NL66oUCUwObE5"

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
    'textStop': False
}

# url to contact card for the number
vcard_url = 'https://firebasestorage.googleapis.com/v0/b/jadeai-77973/o/Jade%20AI.vcf?alt=media'