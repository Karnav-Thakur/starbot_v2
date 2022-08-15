import asyncio
import requests


async def main(string,ctx):
    a = requests.post('http://talkobamato.me/',{"input_text":string}).url

    speech_key = a.split('speech_key=')[1]
    
    download_url = f'http://talkobamato.me/synth/output/{speech_key}/obama.mp4'
    await ctx.respond("Please Wait for a few seconds, getting your video ready")
    await asyncio.sleep(10)
    return (download_url,speech_key)



