import discord 
from discord.ext import commands
from stars import sv_id, client
import youtube_dl
import requests


class Music(commands.Cog):
    def __init__(self,client):
        discord.client = client
    
    music = discord.SlashCommandGroup('music','Get some funny music',sv_id)

    @music.command()
    async def join(self,ctx:discord.ApplicationContext):
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            if channel in client.voice_clients:
                await ctx.respond(f"I am already connected to {channel.name}")
                return
            await channel.connect()
            await ctx.respond(f'Joined {channel.name} ')
        else:
            await ctx.respond("You have to be in a voice channel to use this command")
            
    @music.command()
    async def dc(self,ctx:discord.ApplicationContext):
        if ctx.author.voice:
            client_channel = client.voice_clients[0]
            if ctx.author.voice.channel !=client_channel.channel :
                await ctx.respond("Please Be in the same voice channel as me to disconnect me")
                return
            
            await client.voice_clients[0].disconnect()
            await ctx.respond(f"Disconnected from {client_channel.channel}")
        else:
            await ctx.respond("You are not in any voice channel")
    
    @music.command()
    async def move(self,ctx:discord.ApplicationContext,to:discord.VoiceChannel):
        if ctx.author.voice and ctx.author.voice.channel == to :
            await client.voice_clients[0].disconnect()
            await ctx.respond(f"Moved from {client.voice_clients[0]} to {to}")
            await to.connect()

    @music.command()
    async def play(self,ctx:discord.ApplicationContext,*,song):
        await ctx.defer()
        a = ctx.followup
        if ctx.author.voice is None:
            await ctx.respond("You are not in a voice channel.")
            return
        
        voice_channel = ctx.author.voice.channel
        if ctx.voice_client is None:
            await voice_channel.connect()
        else:
            await ctx.voice_client.move_to(voice_channel)
        await a.send(f"Finding videos with name **{song}**")
        ctx.voice_client.stop()
        FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
        YDL_OPTIONS = {'format': 'bestaudio'}

        vc = ctx.voice_client

        with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
            try:
                requests.get(song)
            except requests.exceptions.MissingSchema:
                info= ydl.extract_info(f"ytsearch:{song}", download=False)['entries'][0]['webpage_url']
                info2 = ydl.extract_info(info,download=False)
                url2 = info2['formats'][0]['url']
                source = await discord.FFmpegOpusAudio.from_probe(url2, **FFMPEG_OPTIONS,method=False)
                await a.send(f"Now Playing: {info2['title']} ")
            else:
                info_link = ydl.extract_info(song, download=False)
                print(info_link)
                url2 = info_link['formats'][0]['url']
                source = await discord.FFmpegOpusAudio.from_probe(url2, **FFMPEG_OPTIONS,method=False)
                await a.send(f"Now Playing: {info_link['title']} ")
        vc.play(source)


def setup(client):
    client.add_cog(Music(client))
