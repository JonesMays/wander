import datetime
import io
from firebase_admin import credentials, storage, firestore
import mimetypes
from openai import OpenAI
from io import BytesIO
import Config
import datetime

# Function to upload media to Firebase Storage
def upload_file(media_content, media_url):

    content_type, _ = mimetypes.guess_type(media_url)

    if content_type is None:
        content_type = 'application/octet-stream'

    blob = Config.bucket.blob(f'userFiles/{media_url.split("/")[-1]}')  # Ensure the file name is extracted correctly
    blob.upload_from_string(media_content, content_type=content_type)
    blob.make_public()
    print("Uploaded file to firebase")

def save_chat(chat_id, chat_data):
    try:
        for message in chat_data['messages']:
            if isinstance(message['timestamp'], datetime.datetime):
                message['timestamp'] = message['timestamp'].isoformat()

        if isinstance(chat_data['createdAt'], datetime.datetime): 
            chat_data['createdAt'] = chat_data['createdAt'].isoformat()

        Config.db.collection('Tree_Hacks').document(chat_id).set(chat_data)
        print('Chat successfully written!')

    except Exception as e:
        print(f'Error writing thread: {e}')

# This ensures that the database has all the fields
def ensure_chat_fields(chat_data):
    if 'hasSentShareMessage' not in chat_data:
        chat_data['hasSentShareMessage'] = False
    if 'hasSentReminder' not in chat_data:
        chat_data['hasSentReminder'] = False
    if 'hasSubscribed' not in chat_data:
        chat_data['hasSubscribed'] = True
    if 'fileIDs' not in chat_data:
        chat_data['fileIDs'] = []
    if 'messages' not in chat_data:
        chat_data['messages'] = []
    if 'voiceID' not in chat_data:
        chat_data['voiceID'] = ''
    if 'participant' not in chat_data:
        chat_data['participant'] = []
    if 'createdAt' not in chat_data or not chat_data['createdAt']:
        chat_data['createdAt'] = datetime.datetime.now().isoformat()
    return chat_data


def get_chat(chat_id):
    try:
        chat_ref = Config.db.collection('Tree_Hacks').document(chat_id)
        chat = chat_ref.get()
        if chat.exists:
            chat_data = chat.to_dict()
            Config.chat_history = ensure_chat_fields(chat_data)
            print("The data was loaded")
            return True
        else:
            print('No such chat!')
            return False
    except Exception as e:
        print(f'Error getting thread: {e}')
        return False
      
