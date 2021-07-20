import sys
from configure import auth_key
import requests
import pprint
from time import sleep

headers = {
    "authorization": auth_key,
    "content-type": "application/json"
}
transcript_endpoint = "https://api.assemblyai.com/v2/transcript"
upload_endpoint = 'https://api.assemblyai.com/v2/upload'

def read_file(filename):
    with open(filename, 'rb') as _file:
        while True:
            data = _file.read(5242880)
            if not data:
                break
            yield data

upload_response = requests.post(
    upload_endpoint,
    headers=headers, data=read_file(sys.argv[1])
)
print('Audio file uploaded')
transcript_request = {'audio_url': upload_response.json()['upload_url']}
transcript_response = requests.post(transcript_endpoint, json=transcript_request, headers=headers)
print('Transcription Requested')
pprint.pprint(transcript_response.json())
polling_response = requests.get(transcript_endpoint+"/"+transcript_response.json()['id'], headers=headers)
filename = transcript_response.json()['id'] + '.txt'
while polling_response.json()['status'] != 'completed':
    sleep(30)
    polling_response = requests.get(transcript_endpoint+"/"+transcript_response.json()['id'], headers=headers)
    print("File is", polling_response.json()['status'])
with open(filename, 'w') as f:
    f.write(polling_response.json()['text'])
print('Transcript saved to', filename)