import click
import requests
import pprint
import json
from time import sleep
from configure import auth_key

transcript_endpoint = "https://api.assemblyai.com/v2/transcript"
upload_endpoint = 'https://api.assemblyai.com/v2/upload'
headers_auth_only = {'authorization': auth_key}
headers = {
    "authorization": auth_key,
    "content-type": "application/json"
}
CHUNK_SIZE = 5242880

@click.group()
def apis():
   """A CLI for using AssemblyAI for speech recognition"""

@click.argument('filename')
@apis.command()
def upload(filename):
    def read_file(filename):
        with open(filename, 'rb') as _file:
            while True:
                data = _file.read(CHUNK_SIZE)
                if not data:
                    break
                yield data
    
    upload_response = requests.post(
        upload_endpoint,
        headers=headers_auth_only, data=read_file(filename)
    )
    print(upload_response.json())
    return upload_response.json()['upload_url']

@click.argument('audio_url')
@click.option('-c', '--categories', is_flag=True, help="Pass if you want to get the categories of this transcript back")
@apis.command()
def transcribe(audio_url, categories: bool):

    transcript_request = {
        'audio_url': audio_url,
        'iab_categories': 'True' if categories else 'False',
    }

    transcript_response = requests.post(transcript_endpoint, json=transcript_request, headers=headers)
    pprint.pprint(transcript_response.json())
    return transcript_response.json()['id']

@click.argument('transcript_id')
@apis.command()
def poll(transcript_id):
    polling_endpoint = transcript_endpoint + "/" + transcript_id
    polling_response = requests.get(polling_endpoint, headers=headers)
    filename = transcript_id + '.txt'
    if polling_response.json()['status'] != 'completed':
        pprint.pprint(polling_response.json())
    else:
        if polling_response.json()['iab_categories'] == True:
            categories_filename = transcript_id + '_categories.txt'
            with open(categories_filename, 'w') as f:
                f.write(json.dumps(polling_response.json()['iab_categories_result']))
        print('Categories saved to', categories_filename)
        with open(filename, 'w') as f:
            f.write(polling_response.json()['text'])
        print('Transcript saved to', filename)
        return filename

@click.argument('location')
@click.option('-c', '--categories', is_flag=True, help="Pass True if you want to get the categories of this transcript back")
@apis.command()
def transcribe_from_location(location, categories: bool):
    def read_file(location):
        with open(location, 'rb') as _file:
            while True:
                data = _file.read(CHUNK_SIZE)
                if not data:
                    break
                yield data
            
    upload_response = requests.post(
        upload_endpoint,
        headers=headers_auth_only, data=read_file(location)
    )
    audio_url = upload_response.json()['upload_url']
    print('Uploaded to', audio_url)
    transcript_request = {
        'audio_url': audio_url,
        'iab_categories': 'True' if categories else 'False',
    }

    transcript_response = requests.post(transcript_endpoint, json=transcript_request, headers=headers)
    transcript_id = transcript_response.json()['id']
    polling_endpoint = transcript_endpoint + "/" + transcript_id
    print("Transcribing at", polling_endpoint)
    polling_response = requests.get(polling_endpoint, headers=headers)
    while polling_response.json()['status'] != 'completed':
        sleep(30)
        try:
            polling_response = requests.get(polling_endpoint, headers=headers)
        except:
            print("Expected to wait 30 percent of the length of your video")
            print("After wait time is up, call poll with id", transcript_id)
            return transcript_id
    _filename = transcript_id + '.txt'
    if polling_response.json()['iab_categories'] == True:
        categories_filename = transcript_id + '_categories.txt'
        with open(categories_filename, 'w') as f:
            f.write(json.dumps(polling_response.json()['iab_categories_result']))
        print('Categories saved to', categories_filename)
    with open(_filename, 'w') as f:
        f.write(polling_response.json()['text'])
    print('Transcript saved to', _filename)

def main():
    apis(prog_name="apis")

if __name__ == '__main__':
    main()