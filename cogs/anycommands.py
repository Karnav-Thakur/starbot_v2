import discord
from discord.ext import commands
from PIL import Image,ImageDraw,ImageFont
from io import BytesIO
import random
import json
from stars import client,sv_id
from discord.ui import Button, View
from discord import ApplicationContext, SelectOption
from discord.enums import ButtonStyle
from helpers import afks
import requests
from bs4 import BeautifulSoup
from datetime import datetime,timedelta
from math import log10,log,sinh,cosh,tanh,tan,sin,cos,sqrt
import aiohttp
from api_wrappers import reddit,giphy,thispersondoesnotexist
# from akinator.async_aki import Akinator
import matplotlib.pyplot as plt
from errors_views import views,flagcon

def remove(afk):
    if "[AFK]" in afk.split(" "):
        return " ".join(afk.split("")[1:])


class Modules(commands.Cog):
    def __init__(self,client):
        self.client = client

    modules = discord.SlashCommandGroup('modules','Various Fun Commands',sv_id)

    @modules.command()
    async def aichat(self,ctx:discord.ApplicationContext,channel:discord.TextChannel):
        ai_channel = await client.db.fetchrow("SELECT * FROM ai_chat WHERE guild_id = $1",ctx.guild.id)

        if ai_channel is None:
            await client.db.execute("INSERT INTO ai_chat (guild_id,channel_id) VALUES($1,$2)",ctx.guild.id,channel.id)
            await ctx.respond(f"{channel.mention} has been set as the ai chat channel")
        
        else:
            if ai_channel['channel_id'] == channel.id:
                await ctx.respond(f"{channel.mention} is already set as the ai channel")
            else:
                await client.db.execute("UPDATE ai_chat SET channel_id = $1 WHERE guild_id = $2",channel.id,ctx.guild.id)
                await ctx.respond(f"{channel.mention} has been set as the ai chat channel")

    @modules.command()
    async def remove_aichat(self,ctx:discord.ApplicationContext):
        ai_channel = await client.db.fetchrow('SELECT * FROM ai_chat WHERE guild_id=$1',ctx.guild.id)

        if ai_channel is None:
            await ctx.respond("There is no AI channel registered in this server")
        else:
            await client.db.execute("DELETE FROM ai_chat WHERE guild_id = $1",ctx.guild.id)
            await ctx.respond(f"<#{ai_channel['channel_id']}> has been removed from the AI Bot channel list.")

    @modules.command()
    async def snipe(self,ctx:discord.ApplicationContext):
        try:
            contents,author,channel_name,time = client.sniped_messages[ctx.guild.id]
        except:
            await ctx.respond("There is nothing to snipe")
            return
        
        embed = discord.Embed(title = "I sniped something",description = contents, colour = discord.Colour.random())
        embed.set_author(name = f"{author.name}#{author.discriminator}", icon_url = author.display_avatar.url)
        embed.set_footer(text = f"Deleted in : <#{channel_name}>")
        await ctx.channel.send(embed = embed)

    @modules.command()
    async def whois(self, ctx:discord.ApplicationContext, member: discord.Member = None):
        if member == None:
            member = ctx.author
        roles = [role for role in member.roles]
        embed = discord.Embed(colour=member.color,
                                timestamp=ctx.message.created_at)
        embed.set_author(name=f"User Info - {member}")
        embed.set_thumbnail(url=member.display_avatar.url)

        embed.add_field(name="ID.", value=member.id)
        embed.add_field(name="Name - ", value=member.display_name)

        embed.add_field(name="Created At: ", value=member.created_at.strftime(
            "%a, %#d %B %Y, %I:%M %p UTC"))
        embed.add_field(name="Joined At", value=member.joined_at.strftime(
            "%a, %#d %B %Y, %I:%M %p UTC"))

        embed.add_field(name=f"Roles ({len(roles)})", value=" ".join(
            [role.mention for role in roles]))
        embed.add_field(name="Heighest Role", value=member.top_role.mention)

        embed.add_field(name="Bot?", value=member.bot)

        await ctx.respond(embed=embed)

    @modules.command()
    @commands.is_owner()
    async def ghost(self, ctx:discord.ApplicationContext):
        x = ctx.guild.members
        random_x = random.choice(x)
        await ctx.respond(random_x.mention, delete_after = 2)
            
    @modules.command()
    async def serverinfo(self, ctx:discord.ApplicationContext):
        guild = str(ctx.guild.name)
        description = str(ctx.guild.description)
        owner = str(ctx.guild.owner)
        created_at = str(ctx.guild.created_at.strftime(
            "%a, %#d %B %Y, %I:%M %p UTC"))
        id_ = str(ctx.guild.id)
        region = str(ctx.guild.region)
        membercount = str(ctx.guild.member_count)
        afk = str(ctx.guild.afk_channel)
        emojis = len(ctx.guild.emojis)
        icon = str(ctx.guild.icon)
        roles = len(ctx.guild.roles)
        default_role = ctx.guild.default_role
        cate = len(ctx.guild.categories)
        text = len(ctx.guild.text_channels)
        voice = len(ctx.guild.voice_channels)

        embed = discord.Embed(title="Server Information",
                            colour=ctx.author.color)

        embed.add_field(name="Server Name: ", value=guild, inline=False)
        embed.add_field(name="Server Description: ",
                        value=description, inline=False)

        embed.add_field(name="Owner: ", value=owner, inline=False)
        embed.add_field(name="Created At: ", value=created_at, inline=False)

        embed.add_field(name="Server ID: ", value=id_, inline=False)
        embed.add_field(name="Region:", value=region, inline=False)

        embed.add_field(name="Total Members: ",
                        value=membercount, inline=False)
        embed.add_field(name="AFK Channels", value=afk, inline=False)

        embed.add_field(name="Emojis", value=emojis, inline=False)
        embed.add_field(name="Roles", value=roles, inline=False)

        embed.add_field(name="Default Role", value=default_role, inline=False)
        embed.add_field(name="Categories", value=cate, inline=False)

        embed.add_field(name="Text Channels", value=text, inline=False)
        embed.add_field(name="Voice Channels", value=voice, inline=False)
        if ctx.guild.icon == None:
            await ctx.respond(embed=embed)
            return
        else:
            embed.set_thumbnail(url=ctx.guild.icon)
            await ctx.respond(embed=embed)

    @modules.command()
    async def servers(self,ctx:discord.ApplicationContext):
        guild_num = self.client.guilds
        embed = discord.Embed(title = f"{self.client.user.name} is in" , description = f"{len(guild_num)} servers" ,colour = discord.Colour.random())
        await ctx.respond(embed = embed)

    @modules.command()
    async def wouldyourather(self,ctx:discord.ApplicationContext):
        with open('./text_files/links.txt', 'r') as f:
            links = f.readlines()

        random_links = random.choice(links)
        data = requests.get(random_links)
        soup = BeautifulSoup(data.text, 'html.parser')
        clmas = soup.find('div' , {"class": "result result-1"})
        div = clmas.find('span', {"class": "option-text"})
        total1 = clmas.find('div' , {'class': 'total-votes'})
        span1 = total1.find('span' , {'class': 'count'})
        clmas2 = soup.find('div' , {"class": "result result-2"})
        div2 = clmas2.find('span', {"class": "option-text"})
        total2 = clmas2.find('div' , {'class': 'total-votes'})
        span2 = total2.find('span' , {'class': 'count'})

        embed = discord.Embed(title = "Would you Rather", colour = discord.Colour.random())
        embed.add_field(name = "Choice 1" , value =  div.text, inline=False)
        embed.add_field(name = "Choice 2" , value =  div2.text, inline=False)
        embed.set_footer(text = f"Play the same question at {random_links}")

        choice1 = Button(style=ButtonStyle.green,label="Choice 1")
        choice2 = Button(style=ButtonStyle.danger,label="Choice 2")

        view = View()
        view.add_item(choice1)
        view.add_item(choice2)

        msg = await ctx.respond(embed = embed, view = view)
        
        async def button_callback_choice1(interaction):
            await interaction.response.send_message(f"{span1.text} users agree with you while {span2.text} disagree")
            await msg.delete()
        async def button_callback_choice2(interaction):
            await interaction.response.send_message(f"{span2.text} users agree with you while {span1.text} disagree")
            await msg.delete()


        choice1.callback = button_callback_choice1
        choice2.callback = button_callback_choice2

    @modules.command()
    async def ping(self,ctx:discord.ApplicationContext):
        ping = round(self.client.latency*1000)
        embed = discord.Embed(title="Pong🏓", description=f"{ping}", colour=ctx.author.color)
        await ctx.respond(embed = embed)

    @modules.command()
    async def bot(self,ctx:discord.ApplicationContext):
        python = '3.9.5'
        discord_ver = discord.__version__
        latency = round(self.client.latency *1000)
        karnav = await self.client.fetch_user(573907301245911040)

        embed = discord.Embed(title = "Bot Information", colour = discord.Color.random())
        embed.add_field(name = "Python Version",  value = python, inline=False)
        embed.add_field(name = "Latency", value=f'{latency}ms', inline=False)
        embed.add_field(name = "Owner Name",value = karnav)
        embed.add_field(name = "Pycord Version", value = discord_ver, inline=False)
        embed.add_field(name = "Support Server", value = "[Karnav's Hornbill](https://discord.gg/cFBT2gmjj2)",inline=False)
        embed.add_field(name = "Total Commands", value = f"{len(client.application_commands)}",inline=False)
        await ctx.respond(embed = embed)

    @modules.command()
    async def rate(self,ctx:discord.ApplicationContext,member: discord.Member = None,arg = None):
        if member == None:
            member = ctx.author
        rate = ['gay', 'horny']
        random_percent = random.randint(0,100)
        if arg == None:
            arg = random.choice(rate)

        if arg == "gay":
            arg = f"{arg}🏳️‍🌈"
            
        elif arg == "horny":
            arg = f"{arg}<:horny:959398917433356298>"
        
        embed = discord.Embed(title=f"{member.name} is {random_percent}% {arg}", colour = discord.Color.random())
        await ctx.respond(embed = embed)

    @modules.command()
    async def truthordare(self,ctx:discord.ApplicationContext):
        truth = Button(style=ButtonStyle.green,label="Truth")
        dare = Button(style=ButtonStyle.danger,label="Dare")

        with open('./jsons/stuff.json',encoding='utf-8') as f:
            truth_q = json.load(f)
        embed = discord.Embed(title = "Choose Truth or Dare", colour = discord.Color.random())
        view = View()
        view.add_item(truth)
        view.add_item(dare)

        msg = await ctx.respond(embed =embed, view = view)

        async def button_callback_truth(interaction):
            questions = truth_q['truth']
            question = random.choice(questions)
            embed = discord.Embed(title = "Truth", colour = discord.Color.random())
            embed.add_field(name = "Question ", value = question)
            await interaction.response.send_message(embed=embed)
            await msg.delete()
        async def button_callback_dare(interaction):
            questions = truth_q['dare']
            question = random.choice(questions)
            embed = discord.Embed(title = "Dare", colour = discord.Color.random())
            embed.add_field(name = "Question ", value = question)
            await interaction.response.send_message(embed = embed)
            await msg.delete()
        
        truth.callback = button_callback_truth
        dare.callback = button_callback_dare
   
    @modules.command()
    async def neverhaveiever(self,ctx:discord.ApplicationContext):
        with open('./jsons/stuff.json', encoding='utf8') as f:
            nhie = json.load(f)
        
        await ctx.respond(random.choice(nhie['never_have_i_ever']))

    @modules.command()
    async def afk(self,ctx:ApplicationContext,*,reason = ""):
        member = ctx.author
        afk = afks.afk
        if member.id in afk.keys():
            afk.pop()
        else:
            try:
                await member.edit(nick = f"[AFK]{member.display_name}")
            except discord.HTTPException:
                pass
        afk[str(ctx.guild.id)] = {}
        afk[str(ctx.guild.id)][str(member.id)] = reason
        embed = discord.Embed(title = "Member AFK",description = f"{member.mention} has gone AFK" , colour = discord.Color.random())
        # embed.set_author(name = self.client.user.name,icon_url=self.client.user.avatar)
        if reason != "":
            embed.add_field(name = "AFK Note", value = reason)
        else:
            pass        

        await ctx.respond(embed = embed)

    @modules.command()
    async def up(self,ctx:discord.ApplicationContext):
        delta_uptime = datetime.utcnow() - client.launch_time
        hours, remainder = divmod(int(delta_uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)
        embed= discord.Embed(title = f"Uptime of {self.client.user.name}",description =f"{days}d, {hours}h, {minutes}m, {seconds}s", colour = discord.Color.random())
        await ctx.respond(embed = embed)

    @modules.command()
    async def calc(self,ctx:discord.ApplicationContext,arg):
        arg_as_list = arg.split("**")
        
        if len(arg_as_list) == 1:
            try:
                await ctx.respond(eval(arg,{'square_root':sqrt,"pow":pow,'log10':log10,'sine':sin,'sineh':sinh,'cos':cos,'cosh':cosh,"tan":tan,'tanh':tanh,"log":log}))
            except NameError:
                await ctx.respond("That operation is banned")
            except SyntaxError:
                await ctx.respond("Syntax provided is wrong")

        elif int(arg_as_list[1]) > 50:
            await ctx.respond("Your argument is too big, I don't have the power to perform this calculation ")
            return
        else:
            try:
                await ctx.respond(eval(arg,{'square_root':sqrt,"pow":pow,'log10':log10,'sine':sin,'sineh':sinh,'cos':cos,'cosh':cosh,"tan":tan,'tanh':tanh,"log":log}))
            except NameError:
                await ctx.respond("That operation is banned")
            except SyntaxError:
                await ctx.respond("Syntax provided is wrong")

    @modules.command()
    async def gentext(self,ctx:discord.ApplicationContext):
        history = []
        today = datetime.utcnow()

        async for message in ctx.channel.history(before = today,after=today-timedelta(days=1)):
            history.append(message.content)
        
        history_str = " ".join(history)            

        history_str_list = history_str.split(" ")

        random_sayer_list = []

        for x in range(20):
            random_sayer_list.append(random.choice(history_str_list))

        random_sayer_str = " ".join(random_sayer_list)

        await ctx.respond(random_sayer_str)

    @modules.command()
    async def insult(self,ctx:discord.ApplicationContext):
        async with aiohttp.ClientSession() as session:
            r = await session.get('https://insult.mattbas.org/api/insult')

        r_text = await r.text()
        await ctx.respond(r_text)

    @modules.command()
    async def funfact(self,ctx:discord.ApplicationContext):
        async with aiohttp.ClientSession() as session:
            r = await session.get('https://uselessfacts.jsph.pl/random.json?language=en')
            text = await r.text()
            text_dict = eval(text)
            await ctx.respond(text_dict['text'])

    @modules.command()
    async def meme(self,ctx:discord.ApplicationContext,*,sub = None):
        if sub == None:
            sub = "memes"
        meme_thing = reddit.Reddit(f"https://www.reddit.com/r/{sub}/random/.json",sub)
        link = await meme_thing.link()
        title = await meme_thing.title()
        subreddit = await meme_thing.subreddit()
        nsfw = await meme_thing.is_nsfw()
        next_meme = Button(style=ButtonStyle.green,label = "Next Meme")
        end_interaction = Button(style=ButtonStyle.danger,label="End Interaction")

        view = View()
        view.add_item(next_meme)
        view.add_item(end_interaction)

        embed = discord.Embed(title=f"{title}-{subreddit}",color=discord.Color.random())
        embed.set_image(url=link)

        if nsfw == False:
            msg = await ctx.respond(embed=embed,view = view)
        else:
            await ctx.respond("You can't send NSFW pics from this!")
            return
        
        async def next_callback(interaction:discord.Interaction):
            meme_thing = reddit.Reddit(f"https://www.reddit.com/r/{sub}/random/.json",sub)
            link = await meme_thing.link()
            title = await meme_thing.title()
            subreddit = await meme_thing.subreddit()
            nsfw = await meme_thing.is_nsfw()


            embed = discord.Embed(title=f"{title}-{subreddit}",color=discord.Color.random())
            embed.set_image(url=link)

            if nsfw == False:
                await msg.edit(embed=embed,view = view)

        async def end_callback(interaction:discord.Interaction):
            for item in view.children:
                item.disabled = True
            
            await interaction.response.edit_message(view = view)
        
        next_meme.callback = next_callback
        end_interaction.callback = end_callback

    @modules.command()        
    async def numfact(self,ctx:discord.ApplicationContext,num):
        url = f"http://numbersapi.com/{num}?json"
        async with aiohttp.ClientSession() as session:
            r = await session.get(url)
        text = await r.text()
        true = "True"
        false = "False"
        text_evaled = eval(text)
        embed = discord.Embed(title=f"Number {num}",colour = discord.Color.random())
        embed.add_field(name='Fact',value=text_evaled['text'])
        await ctx.respond(embed=embed)

    @modules.command()
    async def enlarge(self,ctx:discord.ApplicationContext,emoji:discord.PartialEmoji):
        embed = discord.Embed(title=emoji.id,colour = discord.Color.random())
        embed.set_image(url = emoji.url)
        await ctx.respond(embed=embed)
        
    # @modules.command()
    # async def akinator(self,ctx:discord.ApplicationContext):
    #     aki = Akinator()
    #     q = await aki.start_game()
    #     ques = {'q':q}

    #     responses = ["Yes","No","I Don't Know","Probably","Probably Not"]

    #     view = View()
    #     for res in responses:
    #         button = views.AkinatorButton(aki,ctx.author,ques,style=ButtonStyle.blurple,label = res)
    #         view.add_item(button)

    #     embed = discord.Embed(title="Akinator",description=ques["q"],colour=discord.Color.random())
    #     await ctx.respond(embed=embed,view = view)

    @modules.command()    
    async def trivia_category(self,ctx:discord.ApplicationContext):
        url = "https://opentdb.com/api_config.php"
        session = aiohttp.ClientSession()
        r = await session.get(url,headers = {'Connection': 'keep-alive'})
        r_text = await r.text()
        soup = BeautifulSoup(r_text,features= "html.parser")
        
        select = soup.find("select",{"name": "trivia_category"})
        options = select.find_all("option")
        options = options[1:]

        embed = discord.Embed(title="All the categories available",colour=discord.Color.random())
        for item  in options:
            embed.add_field(name = item.text,value=item.attrs['value'])
        embed.set_footer(text="Use the numbers to get trivia questions of a particular category")
        await session.close()
        await ctx.respond(embed=embed)

    modules2 = discord.SlashCommandGroup('modules2','Part 2 of Fun',sv_id)

    @modules2.command()
    async def showerthoughts(self,ctx:discord.ApplicationContext):
        url = 'https://www.reddit.com/r/showerthoughts/random/.json'
        async with aiohttp.ClientSession() as session:
            r = await session.get(url=url)
            r_json = await r.json()
            title = r_json[0]['data']['children'][0]['data']['title']

        await ctx.respond(title)

    @modules2.command()
    async def rules(self,ctx:discord.ApplicationContext):
        headings = ["User-bots, Spamming, Alts, and Macros","Sharing Exploits","Etiquette"]
        select = []
        with open('./text_files/rules.txt') as f:
            data = f.read().splitlines()
        
        for heading in headings:
            slct = SelectOption(label=heading)
            select.append(slct)
        
        somt = views.RulesSelect(headings,data,select)
        view = View()
        view.add_item(somt)

        await ctx.respond("Rules",view=view)

    @modules2.command()
    @commands.has_permissions(manage_messages = True)
    async def graph(self,ctx:discord.ApplicationContext):
        today = datetime.utcnow()
        await ctx.respond("Creating the Graph")
        day_limit = today - timedelta(days = 7)
        limits = [day_limit,day_limit + timedelta(days = 1),day_limit + timedelta(days = 2),day_limit + timedelta(days = 3),day_limit + timedelta(days = 4),day_limit + timedelta(days = 5),day_limit + timedelta(days = 6)]
        messages = {}

        for limit in limits:
            temp = []
            async for message in ctx.channel.history(before = limit+ timedelta(days = 1),after = limit):
                temp.append(message.content)
            messages[limit] = len(temp)
        
        dates = []
        moi = []
        for date, mes in messages.items():
            dates.append(f"{date.day}-{date.month}")
            moi.append(mes)


        plt.plot(dates,moi,c='b')
        plt.xlabel("Dates")
        plt.ylabel("Messages")
        plt.title(f"Messages Sent in {ctx.channel.name} in 1 week")

        

        buffer = BytesIO()
        plt.savefig(buffer,format='png')
        plt.clf()
        buffer.seek(0)
        await ctx.respond(file = discord.File(buffer,'graph.png'))

    @modules2.command()
    async def similar(self,ctx:discord.ApplicationContext,*,flags:flagcon.SimilarFlags):
        str1 = flags.str1
        str2 = flags.str2

        def longer_string(str1,str2):
            if len(str1) > len(str2):
                return str1
            else:
                return str2

        words_similar = 0

        string = longer_string(str1,str2)



        for i in range(len(string)):
            try:
                if str2[i] == str1[i]:
                    words_similar += 1
            except IndexError:
                break
        
        percent_similarity = (words_similar/len(string))* 100
        await ctx.respond(f"`{str1}` and `{str2}` are {round(percent_similarity)}% similar ")

    @modules2.command()
    async def wyptb(self,ctx:discord.ApplicationContext):
        url = 'https://willyoupressthebutton.com'
        session = aiohttp.ClientSession()
        r = await session.get(url=url)
        r_text = await r.text()
        soup = BeautifulSoup(r_text,features='html.parser')
        choice = soup.find("div",{'id':'cond'})
        but = soup.find("div",{'id':'res'})
        correct_ig = soup.find('a',{"id":'yesbtn'})
        await session.close()
        
        new_url = url+f'{correct_ig.attrs["href"]}'
        attrs_dict = new_url
        press = views.WillYouPressTheButton(attrs_dict,"I Will",ButtonStyle.success)
        notpress = views.WillYouPressTheButton(attrs_dict,"I Will Not",ButtonStyle.danger)

        view = View()
        view.add_item(press)
        view.add_item(notpress)
        a = choice.text.strip()
        b = but.text.strip()
        embed = discord.Embed(title = "Will You Press The Button",description = a,color=discord.Color.random())
        embed.add_field(name="But",value = b)
        await ctx.respond(embed = embed,view =view)

    @modules2.command()
    async def eightball(self,ctx:discord.ApplicationContext,*,question):
        with open('./jsons/stuff.json',encoding='utf-8') as f:
            data = json.load(f)
        
        answers = data['8ball']

        embed = discord.Embed(title = random.choice(answers),description=question,color=discord.Color.random())
        await ctx.respond(embed=embed)

    @modules2.command()
    async def test(self,ctx:discord.ApplicationContext):
        red = reddit.Reddit(f"https://www.reddit.com/r/memes/random/.json","memes")
        print(await red.author())

    @modules2.command()
    async def notexist(self,ctx:discord.ApplicationContext):
        obj = thispersondoesnotexist.ThisPersonDoesNotExist("https://this-person-does-not-exist.com/en")
        link = await obj.link()
        await ctx.respond(link)


    @commands.Cog.listener()
    async def on_message(self,message):        
        for ids, reason in afks.afk.items():
            if int(ids) == message.guild.id:
                for imd,reas in reason.items():
                    try:
                        member = self.client.get_user(int(imd))
                        print(member.id)
                    except AttributeError:
                        member = await self.client.fetch_user(int(imd))
                    
                    if member == message.author:
                        afks.afk.pop(str(message.guild.id))
                        try:
                            await message.author.edit(nick = remove(message.author.display_name))
                        except discord.HTTPException:
                            pass

                        await message.channel.send(f"Welcome back {message.author.mention} I have removed your AFK ")
                        return

                    if (message.reference and member == (await message.channel.fetch_message(message.reference.message_id)).author) or member.id in message.raw_mentions:
                        await message.reply(f"{member.name} is AFK: {reas}")

class ImageCommands(commands.Cog):
    def __init__(self,client):
        self.client = client

    imagecommands = discord.SlashCommandGroup('imagecommands','Images',sv_id)


    @imagecommands.command()
    async def wanted(self,ctx:discord.ApplicationContext,user: discord.Member = None):
        if user == None:
            user = ctx.author
        
        wanted = Image.open('./templates/wanted.jpg')
        asset = user.display_avatar
        data = BytesIO(await asset.read())
        pfp = Image.open(data)

        pfp = pfp.resize((204,204))
        wanted.paste(pfp,(93,195))
        buffer = BytesIO()
        wanted.save(buffer,format='png')
        buffer.seek(0)
        await ctx.respond(file = discord.File(buffer,'profile.png'))

    @imagecommands.command()
    async def simp(self,ctx:discord.ApplicationContext,user:discord.Member = None):
        if user == None:
            user =  ctx.author

        simp_card = Image.open('./templates/simp_card.jpg')
        asset = user.display_avatar
        data = BytesIO(await asset.read())
        pfp = Image.open(data)

        pfp = pfp.resize((130,130))
        simp_card.paste(pfp,(27,59))
        buffer = BytesIO()
        simp_card.save(buffer,format='png')
        buffer.seek(0)
        await ctx.respond(file = discord.File(buffer,'simp.png'))
        
    @imagecommands.command()
    async def ship(self,ctx:discord.ApplicationContext,user:discord.Member = None, user2:discord.Member=None):
        if user == None and user2 == None:
            members = ctx.guild.members
            user = random.choice(members)
            user2 = random.choice(members)

        if user2 == None:
            user2 = ctx.author
        

        ship_card = Image.open('./templates/ship.png')
        
        asset_user1 = user.display_avatar
        asset_user2 = user2.display_avatar
        
        data_user1 = BytesIO(await asset_user1.read())
        data_user2 = BytesIO(await asset_user2.read())
        
        pfp_user1 = Image.open(data_user1)
        pfp_user2 = Image.open(data_user2)

        random_number = random.randint(1,100)

        font = ImageFont.truetype('./fonts/Fruktur-Regular.ttf', size=60)
        draw = ImageDraw.Draw(ship_card)
        # color = (255,18,3)
        

        pfp_user1 = pfp_user1.resize((567,567))
        pfp_user2 = pfp_user2.resize((567,567))
        
        ship_card.paste(pfp_user1,(0,0))
        ship_card.paste(pfp_user2,(885,0))

        arg = f"{random_number}%"
        draw.text((665,217),arg,(255,18,3),font=font,align="center")

        buffer = BytesIO()
        ship_card.save(buffer,format='png')
        buffer.seek(0)
        await ctx.respond(f'🔴`{user.name}`\n🟢`{user2.name}`',file = discord.File(buffer,'ship.png'))

class TextCommands(commands.Cog):
    def __init__(self,client):
        self.client = client
    
    textcommands = discord.SlashCommandGroup('textcommands','Spice up your text',sv_id)

    @textcommands.command()
    async def text_to_emoji(self,ctx:discord.ApplicationContext,*,text= None):
        alphabets = {32:' ',33:'!',34:'"',35:"#",36:"$",37:"%",38:'&',39:"'",40:'(',41:')',42:'*',43:'+',44:',',45:'-',46:'.',47:'/',48:'0',49:'1',50:'2',51:'3',52:'4',53:'5',54:'6',55:'7',56:'8',57:'9',58:':',59:';',60:'<',61:'=',62:'>',63:'?',64:'@',65:'🇦',66:'🇧',67:'🇨',68:'🇩',69:'🇪',70:'🇫',71:'🇬',72:'🇭',73:'🇮',74:'🇯',75:'🇰' ,76:'🇱',77:'🇲',78:'🇳',79:'🇴',80:'🇵',81:'🇶',82:'🇷',83:'🇸',84:'🇹',85:'🇺',86:'🇻',87:'🇼',88:'🇽',89:'🇾',90:'🇿'}
        stri = ""
        if text is None:
            await ctx.respond("You need to have a message to emojify")
            return
        for words in text:
            stri += f" {(alphabets[ord(words.upper())])}"

        try:
            await ctx.channel.purge(limit=1)
        except:
            pass
        await ctx.respond(stri)

    @textcommands.command()
    async def text_clap(self,ctx:discord.ApplicationContext,*,text=None):
        if text is None:
            await ctx.respond("use some message for the clapping effect")
            return
        stri = ""
        text = text.split(' ')
        for word in text:
            if word == text[-1]:
                stri+= f" {word}"
                break
            stri += f" {word} :clap:"
        try:
            await ctx.channel.purge(limit = 1)
        except:
            pass
        await ctx.respond(stri)

    @textcommands.command()
    async def text_doot(self,ctx:discord.ApplicationContext,*,text=None):
        if text is None:
            await ctx.respond("use some message for the clapping effect")
            return
        stri = ""
        text = text.split(' ')
        for word in text:
            if word == text[-1]:
                stri+= f" {word}"
                break
            stri += f" {word} 💀🎺"
        try:
            await ctx.channel.purge(limit = 1)
        except:
            pass
        await ctx.respond(stri)

    @textcommands.command()
    async def alternate_caps(self,ctx:discord.ApplicationContext,*,text= None):
        if text is None:
            await ctx.respond("Please put a text to alternate caps")
            return

        stri = "".join([word.upper() if index%2 == 0 else word for index,word in enumerate(text)])
        try:
            await ctx.channel.purge(limit = 1)
        except:
            pass
        await ctx.respond(stri)

    @textcommands.command()
    async def text_chinese(self,ctx:discord.ApplicationContext,*,text = None):
        if text is None:
            await ctx.respond("Put a text to convert into chinese")
            return
         
        #卂乃匚ᗪ乇千Ꮆ卄丨ﾌҜㄥ爪几ㄖ卩Ɋ尺丂ㄒㄩᐯ山乂ㄚ乙

        alphabets = {32:' ',33:'!',34:'"',35:"#",36:"$",37:"%",38:'&',39:"'",40:'(',41:')',42:'*',43:'+',44:',',45:'-',46:'.',47:'/',48:'0',49:'1',50:'2',51:'3',52:'4',53:'5',54:'6',55:'7',56:'8',57:'9',58:':',59:';',60:'<',61:'=',62:'>',63:'?',64:'@',65:'卂',66:'乃',67:'匚',68:'ᗪ',69:'乇',70:'千',71:'Ꮆ',72:'卄',73:'丨',74:'ﾌ',75:'Ҝ',76:'ㄥ',77:'爪',78:'几',79:'ㄖ',80:'卩',81:'Ɋ',82:'尺',83:'丂',84:'ㄒ',85:'ㄩ',86:'ᐯ',87:'山',88:'乂',89:'ㄚ',90:'乙'}

        await ctx.respond(" ".join([alphabets[ord(word.upper())] for word in text]))

    @textcommands.command()
    async def embedify(self,ctx:discord.ApplicationContext,*,flags: flagcon.EmbedFlags):
        embed = discord.Embed(title = flags.title,description=flags.description,color=discord.Color.random())
        await ctx.respond(embed=embed)

class Miscellaneous(commands.Cog):
    def __init__(self,client):
        self.client = client
    
    miscellaneous = discord.SlashCommandGroup('miscellaneous', 'Being silly',sv_id)

    @miscellaneous.command()
    async def slap(self,ctx:discord.ApplicationContext,user:discord.Member = None):
        if user is None:
            await ctx.respond("Please tag someone")
            return
        with open('./jsons/stuff.json',encoding='utf-8') as f:
            data = json.load(f)
        
        slap_gifs = data["slap"]
        gifs = random.choice(slap_gifs)
        embed = discord.Embed(colour=discord.Color.random())
        embed.set_image(url=gifs)
        embed.set_author(name=f"{ctx.author.name} slapped {user.name} oof",icon_url=ctx.author.display_avatar.url)
        await ctx.respond(embed=embed)

    @miscellaneous.command()
    async def kick(self,ctx:discord.ApplicationContext,user:discord.Member=None):
        if user is None:
            await ctx.respond("Please tag someone")
            return
        with open('./tokens/giphy_api_key.txt') as f:
            api_key = f.read()  

        gifs = giphy.Giphy(api_key=api_key,query='anime kick')
        links = gifs.links()

        kick =  random.choice(links)
        await ctx.respond(f"{kick}.gif")
        embed = discord.Embed(colour=discord.Color.random())
        embed.set_image(url=kick)
        embed.set_author(name=f"{ctx.author.name} kicked {user.name} oof",icon_url=ctx.author.display_avatar.url)
        await ctx.respond(embed=embed)
        
#hello world


def setup(client):
    client.add_cog(Modules(client))
    client.add_cog(ImageCommands(client))
    client.add_cog(TextCommands(client))
    client.add_cog(Miscellaneous(client))
