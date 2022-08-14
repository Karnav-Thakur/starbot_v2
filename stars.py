import json
import os
import discord
from discord.ext import commands
import asyncio
import asyncpg
from datetime import datetime

intents = discord.Intents.all()

sv_id = [985606394466148493 , 813495143512408134,916037482171236372]
client = commands.Bot(command_prefix='star ',intents = intents,owner_id=573907301245911040)

client.launch_time = datetime.utcnow()

client.sniped_messages = {}

async def create_db_pool():
    with open('./jsons/stuff.json',encoding='utf-8') as f:
        data = json.load(f)
    
    client.db = await asyncpg.create_pool(dsn = data['database'])
    print("Connection Successful")

with open('./jsons/commands.json') as f:
    comad = json.load(f)


with open('./tokens/token.txt') as f:
    token = f.read()



for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        ext = f'cogs.{filename[:-3]}'    
        client.load_extension(ext)

client.remove_command('help')
loop = asyncio.get_event_loop()
loop.run_until_complete(create_db_pool())
client.run(token)
    