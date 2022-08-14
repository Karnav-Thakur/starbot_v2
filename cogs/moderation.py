import json
from stars import client,sv_id
import discord
from discord.ext import commands
from datetime import datetime
from discord.ext.commands import BucketType

class Moderation(commands.Cog):
    def __init__(self,client):
        self.client = client
    
    moderation = discord.SlashCommandGroup('moderation','Moderate the server',sv_id)
    
    @moderation.command()
    @commands.has_permissions(kick_members = True)
    async def disable(self,ctx:discord.ApplicationContext,cmd,channel:discord.TextChannel):
        banns = await client.db.fetch("SELECT * FROM predicate WHERE guild_id = $1",ctx.guild.id)

        channels = [chan['channel_id'] for chan in banns]
        commands = [chan['command_name'] for chan in banns]

        vip = client.get_application_command("disable")
        vip2 =client.get_application_command("enable")
        comd =client.get_application_command(cmd)
        if str(comd) == str(vip) or str(comd) == str(vip2):
            await ctx.respond("You can't disable these commands lol")
            return
        
        if channel.id in channels:
            index = channels.index(channel.id)
            command = commands[index]
            if str(comd) == str(command):
                await ctx.respond("This command is already disabled")
                return

        await client.db.execute("INSERT INTO predicate (guild_id,channel_id,command_name) VALUES ($1,$2,$3)",ctx.guild.id,channel.id,str(comd))
        await ctx.respond(f"Disabled {str(cmd)} for {channel.mention}")

    @moderation.command()
    @commands.has_permissions(kick_members = True)
    async def enable(self,ctx:discord.ApplicationContext,command_name,channel : discord.TextChannel):
        result = await client.db.fetch(f"SELECT * FROM predicate WHERE guild_id = $1",ctx.guild.id)
        cmd = self.client.get_command(command_name)
        #DELETE FROM table WHERE urmom = dead
        check = 0
        for x in result:
            if str(cmd) == x['command_name']:
                await client.db.execute("DELETE FROM predicate WHERE channel_id = $1",channel.id)
                await ctx.respond(f"I enabled {cmd} for {channel.mention}")
                check = 1
                break
        
        if check == 1:
            pass
        else:
            await ctx.respond(f"{cmd} is already enabled for {channel.mention}")

    @moderation.command()
    @commands.has_permissions(kick_members= True)
    @commands.cooldown(1,3600,BucketType.guild)
    async def auto_meme(self,ctx:discord.ApplicationContext,channel:discord.TextChannel = None):
        if channel is None:
            await ctx.respond("Please Put a channel_id to change to")
            return
        
        guild = await client.db.fetchrow(f"SELECT * FROM meme WHERE guild_id = $1",ctx.guild.id)
        if not guild:
            await client.db.execute("INSERT INTO meme (guild_id,channel_id) VALUES($1,$2)",ctx.guild.id,channel.id)
            await ctx.respond(f"Successfully Changed meme channel to {channel.mention} ")
        else:
            if guild['channel_id'] == channel:
                await ctx.respond("This Channel is already set as the meme channel")
                return
            else:
                await client.db.execute("UPDATE meme SET channel_id =$1 WHERE guild_id = $2",channel.id,ctx.guild.id)
                await ctx.respond(f"Successfully Changed meme channel to {channel.mention} ")
                return                

    @moderation.command()
    @commands.has_permissions(kick_members = True)
    async def chatban(self,ctx:discord.ApplicationContext,member : discord.Member = None, time: int = None):
        if member == None:
            await ctx.respond(f"Please mention a member to chat ban {ctx.author.mention}")
            return
        if time == None:
            time = 60
        
        ids = []

        result = await client.db.fetch(f"SELECT * FROM ban WHERE guild_id = $1 ",ctx.guild.id)
        if result == None:
            await client.db.execute("INSERT INTO ban(guild_id,member_id, time) VALUES($1,$2,$3)",ctx.guild.id,member.id,time)
            await ctx.respond(f"{member.mention} has been chat banned! for {time} messages by {ctx.author.mention}")
            return
        for ida in result:
            ids.append(ida['guild_id'])

        if ctx.guild.id in ids:
            id_index = ids.index(ctx.guild.id)

            if result[id_index]['member_id'] == member.id:
                await ctx.respond(f"You can chatban a member only once, you need to wait {result[id_index]['time']} messages")
        else:
            await client.db.execute("INSERT INTO ban(guild_id,member_id, time) VALUES($1,$2,$3)",ctx.guild.id,member.id,time)
            await ctx.respond(f"{member.mention} has been chat banned! for {time} messages by {ctx.author.mention}")
            return

    @moderation.command()
    @commands.has_permissions(kick_members = True)
    async def chatunban(self,ctx:discord.ApplicationContext,member:discord.Member = None):
        if member == None:
            await ctx.respond("Please mention a member you want to unban")
            return
        ban = await client.db.fetchrow('SELECT * FROM ban WHERE member_id = $1 AND guild_id = $2',member.id,ctx.guild.id)

        if ban is None:
            await ctx.respond(f"`{member.name}#{member.discriminator}` was never chatbanned")
            return
        else:
            await client.db.execute("DELETE FROM ban WHERE member_id =$1 AND guild_id = $2",member.id,ctx.guild.id)
            await ctx.respond(f"{member.mention} was chat unbanned")

    @moderation.command()
    @commands.has_permissions(ban_members = True)
    async def bans(self,ctx:discord.ApplicationContext):
        bans = await ctx.guild.bans()
        await ctx.respond(f"{len(bans)} members are banned in this server")

    @commands.Cog.listener()
    async def on_message(self,message):
        if message.author == self.client.user:
            return

        bans = await client.db.fetchrow("SELECT * FROM ban WHERE member_id = $1 AND guild_id = $2",message.author.id,message.guild.id)

        if bans is None:
            return

        elif message.author.id == bans['member_id']:
            await message.delete()
        
class Manager(commands.Cog):
    def __init__(self,client):
        self.client = client
    
    manager = discord.SlashCommandGroup('manager','Manage the server',sv_id)

    
    @manager.command()
    @commands.has_permissions(manage_messages = True)
    async def warn(self,ctx:discord.ApplicationContext,member: discord.Member,*, reason = None):
        if reason == None:
            reason = "No reason was provided"
        result = await client.db.fetch("SELECT * FROM warns WHERE (guild_id,member_id) = ($1,$2)",ctx.guild.id,member.id)
        channel_id = await client.db.fetchrow(f"SELECT * FROM warn_channel WHERE guild_id = $1",ctx.guild.id)
        counts = []
        time = datetime.now().strftime('%y-%m-%d %a %H:%M:%S')
        for warn in result:
            counts.append(warn['count'])
        
        counts = sorted(counts,reverse=True)

 
        if channel_id == None:
            await ctx.respond("You don't have a channel setup for logs, please use `evo help warnchannel` to setup a warn channel.")
            return

        if result == []:
            await client.db.execute("INSERT INTO warns(guild_id,member_id,reason,count) VALUES($1,$2,$3,$4)",ctx.guild.id,member.id, reason, 1)
            await ctx.respond(f"I warned {member}")
            channel = self.client.get_channel(channel_id['channel_id'])
            embed = discord.Embed(title = "Warns",description=f"Moderator - {ctx.author.mention}",colour= discord.Color.random())
            embed.add_field(name = "Warned", value=member.name,inline=False)
            embed.add_field(name = "Reason", value = reason,inline=False)
            embed.add_field(name = "Time", value = time,inline=False)
            await channel.send(embed = embed)
            return
        for r in result:
            if member.id == r['member_id']:
                await ctx.respond(f"I warned {member}")
                await client.db.execute("INSERT INTO warns(guild_id,member_id,reason,count) VALUES($1,$2,$3,$4)",ctx.guild.id,member.id,reason, counts[0]+1)
                channel = self.client.get_channel(channel_id['channel_id'])
                embed = discord.Embed(title = "Warns",description=f"Moderator - {ctx.author.mention}", colour = discord.Color.random())
                embed.add_field(name = "Warned", value=f"{member.mention}",inline=False)
                embed.add_field(name = "Reason", value = reason,inline=False)
                embed.add_field(name = "Time", value = time,inline=False)
                await channel.send(embed = embed)
                return
 
    @manager.command()
    @commands.has_permissions(manage_messages = True)
    async def showwarn(self,ctx:discord.ApplicationContext, member:discord.Member):
        result = await client.db.fetch(f"SELECT * FROM warns WHERE guild_id = $1",ctx.guild.id)
        embed = discord.Embed(title=f"Warns of {member.name}", colour = discord.Colour.random())

        for res in result:
            embed.add_field(name = f"Reason -{res['reason']}", value = f"Counts - {res['count']}", inline=False)
        await ctx.respond(embed = embed)

    @manager.command()
    @commands.has_permissions(kick_members = True)
    async def clearwarns(self,ctx:discord.ApplicationContext,user:discord.Member):
        warns = await client.db.fetch("SELECT * FROM warns WHERE (guild_id,member_id) = ($1,$2)",ctx.guild.id,user.id)

        if warns is None:
            await ctx.respond(f"{user.name} has no warns in this database")
            return
        
        await client.db.execute("DELETE FROM warns WHERE(guild_id,member_id) = ($1,$2)",ctx.guild.id,user.id)
        await ctx.respond(f"Deleted all the warns of {user.name}")


    @manager.command()
    @commands.has_permissions(manage_messages = True)
    async def clear(self,ctx:discord.ApplicationContext,amount = 2):
        result= await client.db.fetchrow(F"SELECT * FROM clear_channel WHERE guild_id = $1",ctx.guild.id)

        time = datetime.now().strftime('%y-%m-%d %a %H:%M:%S')

        if result == None:
            await ctx.respond(f"You don't have a channel setup for the clear logs, please use `evo help clearchannel` for more info.")
            return

        if result:
            deleted = await ctx.channel.purge(limit=amount)
            await ctx.respond(f"I deleted {len(deleted)} messages in {ctx.channel.mention}", delete_after=1)
            channel = self.client.get_channel(result['channel_id'])
            embed = discord.Embed(title = "Clears",description = f"Moderation - {ctx.author.mention}",colour= discord.Color.random())
            embed.add_field(name = "Cleared in", value=ctx.channel.mention,inline= False)
            embed.add_field(name = "Deleted", value=f"{len(deleted)} messages",inline=False)
            embed.add_field(name = "Time", value=time,inline=False)
            await channel.send(embed = embed)
            return

    @manager.command()
    @commands.has_permissions(manage_messages = True)
    async def warnchannel(self,ctx:discord.ApplicationContext,channel: discord.TextChannel):
        channel_name=await client.db.fetchrow("SELECT * FROM warn_channel WHERE guild_id = $1",ctx.guild.id)

        if channel_name == None:
            await client.db.execute("INSERT INTO warn_channel(guild_id,channel_id) VALUES($1,$2)",ctx.guild.id,channel.id)
            await ctx.respond(f"I will now send all warn logs in {channel.mention} ")
            return
        
        if channel_name:
            await client.db.execute("UPDATE warn_channel SET channel_id = $1 WHERE guild_id = $2",channel.id, ctx.guild.id)
            await ctx.respond(f"I will now send all warn logs in {channel.mention} ")
            return

    @manager.command()
    @commands.has_permissions(manage_messages = True)
    async def clearchannel(self,ctx:discord.ApplicationContext,channel: discord.TextChannel):
        channel_name = await client.db.fetchrow(f"SELECT * FROM clear_channel WHERE guild_id = $1",ctx.guild.id)

        if channel_name == None:
            await client.db.execute("INSERT INTO clear_channel(guild_id,channel_id) VALUES($1,$2)",ctx.guild.id,channel.id)
            await ctx.respond(f"I will now send all clear logs in {channel.mention} ")
            return
        
        if channel_name:
            await client.db.execute("UPDATE clear_channel SET channel_id = $1 WHERE guild_id = $2",channel.id, ctx.guild.id)
            await ctx.respond(f"I will now send all clear logs in {channel.mention} ")
            return        


class Karnav(commands.Cog):
    def __init__(self,client):
        self.client = client
    
    karnav = discord.SlashCommandGroup('karnav','Only for KarnaV commands',sv_id,checks = [commands.is_owner().predicate])

    @karnav.command()
    async def reload(self,ctx:discord.ApplicationContext,module):
        self.client.reload_extension(f"cogs.{module}")
        await ctx.respond(f"Reloaded {module}")
    
    @karnav.command()
    async def desync(self,ctx:discord.ApplicationContext):
        with open('./jsons/commands.json') as f:
            data = json.load(f)
        
        un_sync = []
        for item in client.walk_application_commands():
            
            if str(item.full_parent_name) != '':
                try:
                    data[item.name]
                except KeyError:
                    un_sync.append(item.name)
            else:
                continue
        
        karnav_ = await client.fetch_user(573907301245911040)

        await karnav_.send(un_sync)

def setup(client):
    client.add_cog(Moderation(client))
    client.add_cog(Manager(client))
    client.add_cog(Karnav(client))