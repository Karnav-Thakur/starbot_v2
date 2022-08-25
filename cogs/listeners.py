import json
import discord
from discord.ext import commands
from errors_views import errors
import aiohttp
from discord.ext import tasks
from stars import client
from datetime import datetime
from api_wrappers import reddit
import random

with open('./tokens/api_key.txt') as f:
    api_key = f.read()



class Listeners(commands.Cog):
    def __init__(self,client):
        self.client = client
        self.memes.start()
    
    @tasks.loop(hours=2)
    async def memes(self):
        random_sub = 'memes'
        red_obj = reddit.Reddit(f"https://www.reddit.com/r/{random_sub}/random/.json",random_sub)
        link = await red_obj.link()
        title = await red_obj.title()
        is_nsfw = await red_obj.is_nsfw()
        author = await red_obj.author()
        guilds = await client.db.fetch("SELECT * FROM meme")
         

        if is_nsfw == False:

            embed= discord.Embed(title = title,colour = discord.Color.random())
            embed.set_image(url=link)
            embed.set_author(name=f'Meme by "{author}"')

            for i in guilds:
                meme_channel= client.get_channel(i['channel_id'])
                try:
                    await meme_channel.send(embed=embed)
                except AttributeError:
                    continue

    @memes.before_loop
    async def before_memes(self):
        print('waiting...')
        await self.client.wait_until_ready()

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.client.user.name} is Ready")

    @commands.Cog.listener()
    async def on_application_command_error(self,ctx:discord.ApplicationContext,error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.respond("You don't have permissions to use this command")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.respond("Give me enough arguments")
        elif isinstance(error, commands.CommandNotFound):
            await ctx.respond("There is no command with that name")
        elif isinstance(error, commands.BadArgument):
            await ctx.respond("The Argument that you provided is incorrect")
        elif isinstance(error, commands.DisabledCommand):
            karnav = self.client.get_user(573907301245911040)
            await ctx.respond(f"{ctx.command} is disabled by {karnav}")
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.respond("I don't have permission to use this command")
        elif isinstance(error,commands.NotOwner):
            karnav = self.client.get_user(573907301245911040)
            await ctx.respond(f"Only {karnav} can use this command for now")
        elif isinstance(error, commands.CommandOnCooldown):
            if error.retry_after > 3600:
                hours = round(error.retry_after//3600)
                minutes = round((error.retry_after - (3600*hours))//60)
                seconds = round(error.retry_after - (60*minutes)- (3600*hours))
                await ctx.respond(f"Your command is on cooldown, please wait `{hours}`h `{minutes}`m and `{seconds}`s ")
            elif error.retry_after > 60:
                minutes = round(error.retry_after//60)
                seconds = round(error.retry_after - (60*minutes))
                await ctx.respond(f"Your command is on cooldown, please wait `{minutes}`m and `{seconds}`s ")
            
            elif error.retry_after < 60:
                await ctx.respond(f"Your command is on cooldown, please wait `{round(error.retry_after)}`s ")
        elif isinstance(error,errors.NoPetError):
            await ctx.respond(str(error))
        elif isinstance(error,discord.ExtensionNotFound):
            await ctx.respond("The Extention you are trying to load is not found")
        elif isinstance(error,discord.Forbidden):
            await ctx.respond("I am missing perms to do that")
        elif isinstance(error,TypeError):
            await ctx.respond("You forgot to pass necessary arguments")
        elif isinstance(error,commands.NotOwner):
            await ctx.respond('You do not own this bot. Only KarnaV can use this command')
        else:
            raise error

    @commands.Cog.listener()
    async def on_message_delete(self,message):
        self.client.sniped_messages[message.guild.id] = (message.content, message.author, message.channel.name, message.created_at)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self,payload:discord.RawReactionActionEvent):
        if payload.user_id != client.owner_id:
            return


        msg= await client.get_message(payload.message_id)
        channel_id = await client.db.fetch('SELECT * FROM meme WHERE guild_id = $1',916037482171236372)
        if msg.author.id == client.user.id and payload.channel_id == channel_id:
            try:
                await msg.pin(reason='Karnav found this meme good')
            except Exception as e:
                return
        else:
            return

def setup(client):
    client.add_cog(Listeners(client))
