import requests


async def main(string):
    a = requests.post('http://talkobamato.me/',{"input_text":string}).url

    speech_key = a.split('speech_key=')[1]
    
    download_url = f'http://talkobamato.me/synth/output/{speech_key}/obama.mp4'
    return (download_url,speech_key)



