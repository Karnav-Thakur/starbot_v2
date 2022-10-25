import asyncio
from email import message
import random
import discord
from stars import client,sv_id
from discord.ext import commands
from discord.ext.commands import BucketType
from errors_views import errors,views
import json
import math
from discord.ui import View,Button
from discord.enums import ButtonStyle
from games import games,random_reaction_game,order,findimposter,connect4
import re
from datetime import datetime
import aiohttp
from api_wrappers import opentdb
from PIL import Image, ImageFont,ImageDraw
from inspect import getmembers, isfunction

async def open_account(user:discord.Member): #opens a account for the user if account doesn't exist
    result = await client.db.fetchrow("SELECT * FROM main WHERE member_id = $1",(user.id))
    if result is not None:
        return
    else:
        await client.db.execute("INSERT INTO main (member_id,wallet,bank) VALUES ($1,$2,$3)",user.id,500,0)


async def add_bal(user:discord.Member,amount:int,mode="wallet"):# adds money in the account, can be used to remove money as well
    result = await client.db.fetchrow("SELECT * FROM main WHERE member_id = $1",(user.id))
    wallet,bank = result['wallet'],result['bank']
    if mode.lower() == "wallet":
        total = amount+ wallet
        await client.db.execute(f"UPDATE main SET wallet = $1 WHERE member_id = $2",total,user.id)
    if mode.lower() == "bank":
        total = amount+ bank
        await client.db.execute(f"UPDATE main SET bank = $1 WHERE member_id = $2",total,user.id)

async def show_account(user:discord.Member): # shows a user's account    
    result = await client.db.fetchrow("SELECT * FROM main WHERE member_id = $1",user.id)
    return result

async def show_pet(user:discord.Member):
    peta =  await client.db.fetchrow("SELECT * FROM pet WHERE member_id = $1",user.id)
    
    if peta is None:
        raise errors.NoPetError("User doesn't have any pets")
    else:
        return peta

async def inv(user:discord.Member):
    result = await client.db.fetch("SELECT * FROM inventory WHERE member_id = $1",user.id)
    return result

async def update_stats(user:discord.Member,stat,amount:int):
    peta = await show_pet(user)

    if peta is None:
        raise errors.NoPetError(f"{user.name} doesn't have a pet")
    else:
        orignal = peta[stat.strip().lower()]
        amt = orignal+amount

        if amt >= 100:
            amt = 100
        
            await client.db.execute(f"UPDATE pet SET {stat} = $1 WHERE member_id = $2",amt,user.id)
            return
        else:
            await client.db.execute(f"UPDATE pet SET {stat} = $1 WHERE member_id = $2",amt,user.id)

async def insert_into_inventory(user:discord.Member,item,amount:int):
    inventory = await inv(user)
    if amount > 0:
        if inventory is None:
            await client.db.execute("INSERT INTO inventory (member_id,item_name,amount) VALUES($1,$2,$3)",user.id,item.title(),amount)
            return
        else:
            items = await client.db.fetchrow("SELECT * FROM inventory WHERE (member_id,item_name) = ($1,$2)",user.id,item.title())

            if items is None:
                await client.db.execute("INSERT INTO inventory (member_id,item_name,amount) VALUES($1,$2,$3)",user.id,item.title(),amount)
            else:
                await client.db.execute("UPDATE inventory SET amount = $1 WHERE (member_id,item_name) = ($2,$3)",items["amount"]+amount,user.id,item.title())

    else:
        if inventory is None:
            raise errors.NegativeError("User doesn't have inventory, can't remove items")
        else:
            items = await client.db.fetchrow("SELECT * FROM inventory WHERE (member_id,item_name) = ($1,$2)",user.id,item.title())

            if items is None:
                raise errors.NegativeError("User doesn't have that item")
            else:
                if amount > items[2]:
                    raise errors.NegativeError("User doesn't have that many items")
                else:
                    await client.db.execute("UPDATE inventory SET amount = $1 WHERE (member_id,item_name) = ($2,$3)",items["amount"]+amount,user.id,item.title())

async def insert_into_shop(item,price:int,description):
    shoify = await shop()
    for x in shoify:
        if x["name"] == item.title():
            return 
    await client.db.execute("INSERT INTO shop(name,price,description) VALUES($1,$2,$3)",item.title(),price,description.title())

async def remove_from_shop(item):
    shopify = await shop()
    for x in shopify:
        if x['name'] == item.title():
            await client.db.execute("DELETE FROM shop WHERE name = $1",item.title())

async def show_job(user:discord.Member):
    job = await client.db.fetchrow("SELECT * FROM mem_job WHERE member_id = $1",user.id)
    return job

async def pet_store():
    pets = await client.db.fetch("SELECT * FROM pets")
    return pets

async def adopt_pet(pet:str,user:discord.Member):
    try:
        await show_pet(user)
    except errors.NoPetError:
        await client.db.execute("INSERT INTO pet(member_id, name,hunger,exp,attack,defence) VALUES($1,$2,$3,$4,$5,$6)",user.id,pet['name'],100,0,0,0)
        await add_bal(user,-pet['price'])
        return  
    return False

async def clean_inventory(user:discord.Member):
    inv_ = await inv(user)
    for item in inv_:
        if item['amount'] == 0:
            name = item['item_name']
            await client.db.execute("DELETE FROM inventory WHERE member_id = $1 AND item_name = $2",user.id,name)

async def shop():
    shop_ = await client.db.fetch("SELECT * FROM shop")
    return shop_

def check():#checks if the command is disabled in a channel or not
    async def predicate(ctx):
        banned=await client.db.fetch("SELECT * FROM predicate WHERE guild_id = $1",ctx.guild.id)
        channel_id = [chan['channel_id'] for chan in banned]
        cmd_list = [chan['command_name'] for chan in banned]
        cmd_channel = zip(channel_id,cmd_list)

        if banned == []:
            return True
        
        for item in cmd_channel:
            if ctx.channel.id == item[0]:
                if str(ctx.command) == item[1]:
                    return False
                else:
                    continue
        return True

    return commands.check(predicate)

def has_pet():
    async def predicate(ctx):
        ids = []
        peta = await client.db.fetch("SELECT * FROM pet")
        for pet in peta:
            ids.append(pet['member_id'])
        
        if ctx.author.id in ids:
            return True

        raise errors.NoPetError("You don't have any pet")
    
    return commands.check(predicate)

def is_premium():
    async def predicate(ctx):
        ids = []
        result =await client.db.fetch("SELECT * FROM premium")

        for mem in result:
            imd = mem["member_id"]
            ids.append(imd)


        if ctx.author.id in ids:
            return True

        raise errors.PremiumError("This is a premium command, you need premium access")
    
    return commands.check(predicate)



class Economy(commands.Cog):
    def __init__(self,client):
        self.client = client

    economy = discord.SlashCommandGroup('economy','Basic Bank Transactions',sv_id)

    @economy.command()
    @check()
    async def balance(self,interaction:discord.Interaction,user:discord.Member = None):
        if user is None:
            user = interaction.user


        await open_account(user)
        result = await client.db.fetchrow("SELECT * FROM main WHERE member_id = $1",(user.id))

        embed = discord.Embed(title = f"{user.name}'s Balance",colour=discord.Color.random())
        embed.add_field(name="Wallet",value=f"{result['wallet']:,} <:doge_coin:865669474917154837> ")
        embed.add_field(name="Bank",value=f"{result['bank']:,} <:doge_coin:865669474917154837>")

        await interaction.response.send_message(embed=embed)

    @economy.command()
    @check()
    async def deposit(self,interaction:discord.Interaction,amount = None):
        if amount is None:
            embed = discord.Embed(title = "Transaction Incomplete 🛑",description="You can't deposit none",colour=discord.Color.random())
            await interaction.response.send_message(embed=embed)
            return
        
        result = await client.db.fetchrow("SELECT * FROM main WHERE member_id = $1",(interaction.user.id))
        wallet = result['wallet']

        try:
            amount = int(amount)
        except ValueError:
            if amount.lower() in ['max','all']:
                await add_bal(interaction.user,wallet,"bank")
                await add_bal(interaction.user,-wallet,"wallet")
                embed = discord.Embed(title = "Transaction Complete 🟢",description=f"Deposited {wallet:,} <:doge_coin:865669474917154837>",colour=discord.Color.random())
                await interaction.response.send_message(embed=embed)
                return
            else:
                embed = discord.Embed(title = "Transaction Incomplete 🛑",description="Invalid Argument",colour=discord.Color.random())
                await interaction.response.send_message(embed=embed)
                return
        if amount < wallet:
            await add_bal(interaction.user,amount,"bank")
            await add_bal(interaction.user,-amount,"wallet")
            embed = discord.Embed(title = "Transaction Complete 🟢",description=f"Deposited {amount:,} <:doge_coin:865669474917154837>",colour=discord.Color.random())
            await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(title = "Transaction Incomplete 🛑",description="You can't desposit more than your wallet",colour=discord.Color.random())
            await interaction.response.send_message.send(embed=embed)

    @economy.command()
    @check()
    async def withdraw(self,interaction:discord.Interaction,amount = None):
        if amount is None:
            embed = discord.Embed(title = "Transaction Incomplete 🛑",description="You can't withdraw none",colour=discord.Color.random())
            await interaction.response.send_message(embed=embed)
            return
        
        result = await client.db.fetchrow("SELECT * FROM main WHERE member_id = $1",(interaction.user.id))
        bank = result['bank']

        try:
            amount = int(amount)
        except ValueError:
            if amount.lower() in ['max','all']:
                await add_bal(interaction.user,bank,"wallet")
                await add_bal(interaction.user,-bank,"bank")
                embed = discord.Embed(title = "Transaction Complete 🟢",description=f"Withdrew {bank:,} <:doge_coin:865669474917154837>",colour=discord.Color.random())
                await interaction.response.send_message(embed=embed)
                return
            else:
                embed = discord.Embed(title = "Transaction Incomplete 🛑",description="Invalid Argument",colour=discord.Color.random())
                await interaction.response.send_message(embed=embed)
                return
        if amount < bank:
            await add_bal(interaction.user,amount,"wallet")
            await add_bal(interaction.user,-amount,"bank")
            embed = discord.Embed(title = "Transaction Complete 🟢",description=f"Withrew {amount:,} <:doge_coin:865669474917154837>",colour=discord.Color.random())
            await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(title = "Transaction Incomplete 🛑",description="You can't withdraw more than your wallet",colour=discord.Color.random())
            await interaction.response.send_message(embed=embed)

    @economy.command()
    @check()
    @commands.is_owner()
    async def addmoney(self,interaction:discord.Interaction,user:discord.Member = None,amount:int = None):
        if amount is None:
            await interaction.response.send_message("Need some amount to give")
            return
        
        if user is None:
            user = interaction.user
            return
        
        result = await show_account(user)
        await add_bal(user,result["wallet"]+amount)
        await interaction.response.send_message(f"Gave {user.mention} {amount} <:doge_coin:865669474917154837>")
  
class Games(commands.Cog):
    def __init__(self,client):
        self.client = client
    
    games = discord.SlashCommandGroup('games','Very Fun Games',sv_id)

    @games.command()
    @check()
    async def beg(self,interaction:discord.Interaction):
        await open_account(interaction.user)
        random_number = random.randint(1,2)
        earnings = random.randint(1,100)
        with open('./jsons/stuff.json',encoding='utf-8') as f:
            data = json.load(f)
        

        if random_number == 1:
            # good stuff
            embed = discord.Embed(title="Beg Results",description=f"{random.choice(data['beg_good'])} {earnings} <:doge_coin:865669474917154837> ",colour=discord.Color.random())
            await add_bal(interaction.user,earnings)
        elif random_number == 2:
            # bad stuff
            embed = discord.Embed(title="Beg Results",description=f"{random.choice(data['beg_bad'])} ",colour=discord.Color.random())
        
        
        await interaction.response.send_message(embed=embed)

    @games.command()
    @check()
    async def guess(self,interaction:discord.Interaction,lower:int = 1,upper:int= 10,bet:int = None):
        bank = await show_account(interaction.user)
        if bet is None:
            await interaction.response.send_message("Can't bet none")

            return
        elif bet > bank['wallet']:
            await interaction.response.send_message("You can't bet more than you have")

            return
        
        if bet >= lower*10 and bet <= upper*100:
            tries = round(math.log(upper-lower+1,2))
            number = random.randint(lower,upper)
            def check(message):
                return message.author == interaction.user
            await interaction.response.send_message(f"You have {tries} tries to guess the answer")

            while tries> 0:
                guess = await self.client.wait_for('message',check=check)
                tried = int(guess.content)

                if tried > number:
                    tries-= 1
                    await guess.reply(f"You went higher, you have {tries} tries left  ") 
                
                if tried < number:
                    tries-= 1
                    await guess.reply(f"You went lower, you have {tries} tries left  ")
                
                if tried == number:
                    await guess.reply(f"You got it {interaction.user.mention}, it was {number} ")
                    await add_bal(interaction.user,bet)

                    return
                
            if tries == 0:
                await interaction.response.send_message(f"The tries are over {number} ")
                await add_bal(interaction.user,-bet)
                return
        else:
            await interaction.response.send_message(f"You need to bet between {lower*10} and {upper*100}")

    @games.command()
    @check()
    async def reaction_emoji(self,interaction:discord.Interaction):
        await random_reaction_game.main(interaction,self.client)

    @games.command()
    @check()
    async def order_game(self,interaction:discord.Interaction):
        await order.main(interaction)

    @games.command()
    @check()
    async def findimposter(self,interaction:discord.Interaction,bet:int = None):
        if bet is None:
            await interaction.response.send_message("You can't bet none") 
            return
        user = interaction.user
        result = await show_account(user)

        if result is None:
            await open_account(user)
            result = await show_account(user)
            
        if result['wallet'] < 100:
            embed = discord.Embed(title = "You need atleast 100 <:doge_coin:865669474917154837> to play",color=discord.Color.random())
            await interaction.response.send_message(embed = embed)
            return
        await findimposter.main(interaction,bet)

    @games.command()
    @check()
    async def tictactoe(self,interaction:discord.Interaction,amount:int):
        if amount > 1000:
            await interaction.response.send_message("Easy game doesn't mean easy money :(")
            return
        a = await show_account(interaction.user)
        if a[1] < amount:
            await interaction.response.send_message("Please Choose a amount that is less than or equal to your wallet amount")
            return

        win = False
        # winning_conditions = [[0,1,2],[3,4,5],[6,7,8],[0,3,6],[1,4,7],[2,5,8],[0,4,8],[2,4,6]]
        board = [["⬜","⬜","⬜"],["⬜","⬜","⬜"],["⬜","⬜","⬜"]]
        choices = ["a1","a2","a3","b1","b2","b3","c1","c2","c3"]
        s = ""
        turn = random.randint(1,2)
        for row in board:
            s += "".join(row)+ "\n"

        embed = discord.Embed(title = f"TicTacToe with {self.client.user.name}",description = s,colour = discord.Color.random())
        msg = await interaction.response.send_message(embed = embed)
        msg = await msg.original_message()
        followup = interaction.followup
        player1 = interaction.user
        player2 = self.client.user
        def check(message):
            return message.author == interaction.user
        
        def wincheck():
            if board[0][0] == board[0][1] == board[0][2] == '❎' or  board[0][0] == board[0][1] == board[0][2] == '🟠' or board[1][0] == board[1][1] == board[1][2] == '❎' or  board[1][0] == board[1][1] == board[1][2] == '🟠' or board[2][0] == board[2][1] == board[2][2] == '❎' or  board[2][0] == board[2][1] == board[2][2] == '🟠' or board[0][0] == board[1][1] == board[2][2] == '❎' or board[0][0] == board[1][1] == board[2][2] == '🟠' or board[0][2] == board[1][1] == board[2][0] == '❎' or board[0][2] == board[1][1] == board[2][0] == '🟠' or board[0][0] == board[1][0] == board[2][0] == '❎' or  board[0][0] == board[1][0] == board[2][0] == '🟠'or board[0][1] == board[1][1] == board[2][1] == '❎' or  board[0][1] == board[1][1] == board[2][1] == '🟠' or board[0][2] == board[1][2] == board[2][2] == '❎' or  board[0][2] == board[1][2] == board[2][2] == '🟠' :
                return True
            else:
                return False

        while win is False:

            if turn ==1:
                # ctx.author turn
                await followup.send(f"{player1.mention} it's your turn, message with the postion (a1 is the top left a2 is the top middle)")
                response = await self.client.wait_for('message', check = check)
                res = re.findall(r"[^\W\d_]+|\d+", response.content.lower())
                await response.delete()
                try:
                    res[1]
                except IndexError:
                    await followup.send('This was a wrong input, I am stopping the game')

                for row in board:
                    s = ""
                    if response.content.lower() not in choices:
                        await followup.send("You already placed here")
                    
                    if choices == []:
                        await followup.send("It's a Tie")
                        return
                
                    if res[0] == 'a':
                        board[0][int(res[1])-1] = '❎'
                        turn =2
                        # await ctx.respond(board)
                        for bruh in board:
                            s += "".join(bruh)+"\n"
                        embed2 = discord.Embed(title = f"TicTacToe with {self.client.user.name}",description = s,colour = discord.Color.random())
                        await msg.edit(embed= embed2)
                        popping_element = ""
                        popping_element += "".join(res)
                        choices.remove(popping_element)
                        a = wincheck()
                        if a is True:
                            win = True
                            await add_bal(player1,amount)
                            await followup.send(f"{player1.mention} Won {amount} <:doge_coin:865669474917154837> !!")
                            return
                        else:
                            pass
                        break
                    elif res[0] == 'b':
                        board[1][int(res[1])-1] = '❎'
                        turn =2
                        for bruh in board:
                            s += "".join(bruh)+"\n"
                        # await ctx.respond(board)
                        embed2 = discord.Embed(title = f"TicTacToe with {self.client.user.name}",description = s,colour = discord.Color.random())
                        await msg.edit(embed= embed2)
                        popping_element = ""
                        popping_element += "".join(res)
                        choices.remove(popping_element)
                        a = wincheck()
                        if a is True:
                            win = True
                            await add_bal(player1,amount)
                            await followup.send(f"{player1.mention} Won {amount} <:doge_coin:865669474917154837> !!")
                            return
                        else:
                            pass
                        break
                    elif res[0] == 'c':
                        board[2][int(res[1])-1] = '❎'
                        turn =2
                        for bruh in board:
                            s += "".join(bruh)+"\n"
                        # await ctx.respond(board)
                        embed2 = discord.Embed(title = f"TicTacToe with {self.client.user.name}",description = s,colour = discord.Color.random())
                        await msg.edit(embed= embed2)
                        popping_element = ""
                        popping_element += "".join(res)
                        choices.remove(popping_element)
                        a = wincheck()
                        if a is True:
                            win = True
                            await add_bal(player1,amount)
                            await followup.send(f"{player1.mention} Won {amount} <:doge_coin:865669474917154837> !!")
                            return
                        else:
                            pass
                        break
                    
            elif turn ==2:
                # self.client.user turn
                await followup.send(f"{player2.mention} is playing...")
                for row in board:
                    s = ""
                    choice = random.choice(choices)
                    rem = re.findall(r"[^\W\d_]+|\d+", choice)
                    if choice not in choices:
                        continue
                    if choices == []:
                        await followup.send("It's a Tie")
                        return
                    if rem[0] == 'a':
                        popping_element = ""
                        board[0][int(rem[1])-1] = '🟠'
                        turn =1
                        popping_element += "".join(rem)
                        choices.remove(popping_element)
                        # await ctx.respond(board)
                        for bruh in board:
                            s += "".join(bruh)+"\n"
                        embed2 = discord.Embed(title = f"TicTacToe with {self.client.user.name}",description = s,colour = discord.Color.random())
                        await msg.edit(embed= embed2)
                        a = wincheck()
                        if a is True:
                            await followup.send(f"{player2.mention} Won!!")
                            await add_bal(player1,-amount)
                            win = True
                            return
                        else:
                            pass
                        break
                    elif rem[0] == 'b':
                        board[1][int(rem[1])-1] = '🟠'
                        turn =1
                        popping_element = ""
                        popping_element += "".join(rem)
                        choices.remove(popping_element)
                        for bruh in board:
                            s += "".join(bruh)+"\n"
                        # await ctx.respond(board)
                        embed2 = discord.Embed(title = f"TicTacToe with {self.client.user.name}",description = s,colour = discord.Color.random())
                        await msg.edit(embed= embed2)
                        a = wincheck()
                        if a is True:
                            await followup.send(f"{player2.mention} Won!!")
                            win = True
                            await add_bal(player1,-amount)
                            return
                        else:
                            pass
                        break
                    elif rem[0] == 'c':
                        board[2][int(rem[1])-1] = '🟠'
                        turn =1
                        popping_element = ""
                        popping_element += "".join(rem)
                        choices.remove(popping_element)
                        for bruh in board:
                            s += "".join(bruh)+"\n"
                        # await ctx.respond(board)
                        embed2 = discord.Embed(title = f"TicTacToe with {self.client.user.name}",description = s,colour = discord.Color.random())
                        await msg.edit(embed= embed2)
                        a = wincheck()
                        if a is True:
                            await followup.send(f"{player2.mention} Won!!")
                            win = True
                            await add_bal(player1,-amount)
                            return
                        else:
                            pass
                        break

    @games.command()
    @check()
    async def trivia(self,ctx:discord.ApplicationContext,cata :int= None):
        url = f"https://opentdb.com/api.php?amount=10&category={cata}&type=multiple"

        if cata is None:
            url = "https://opentdb.com/api.php?amount=10&type=multiple"

        a = opentdb.OpenTDB(url,0,9)

        def no_get():
            return random.random()

        question =await a.question()
        answers = await a.answers()
        answers_correctly = []
        for elem in answers:
            if type(elem) == list:
                for thing in elem:
                    answers_correctly.append(thing)
            else:
                answers_correctly.append(elem)
        correct_answer = answers[0]
        category = await a.category()
        difficulty = await a.difficulty()
        embed = discord.Embed(title="Trivia",color=discord.Color.random())
        embed.add_field(name="Question",value=question,inline=False)
        embed.add_field(name="Category",value=category,inline=False)
        embed.add_field(name="Difficulty",value=difficulty,inline=False)
        order.shuffle(answers_correctly,len(answers_correctly))
        view = View()
        for a in answers_correctly:
            button = views.TriviaButton(correct_answer,a)
            view.add_item(button)

        for index,answer in enumerate(answers_correctly):
            embed.add_field(name=index+1,value=answer,inline=False)
        await ctx.respond(embed = embed,view=view)
    
    @games.command()
    @check()
    async def rps(self,ctx:discord.ApplicationContext,bet:int = None):
        if bet is None:
            await ctx.respond("You need to bet something")
            return
        def rps(comp,you):
            if comp == you:
                return "Tie"
            
            elif comp == "r":
                if you == "p":
                    return True
                elif you == "s":
                    return False

            elif comp == "p":
                if you == "s":
                    return True
                elif you == "r":
                    return False
            
            elif comp == "s":
                if you == "r":
                    return True
                elif you == "p":
                    return False

        comp_num = random.randint(1,3)
        if comp_num == 1:
            comp = "r"
        if comp_num == 2:
            comp = "p"
        if comp_num == 3:
            comp = "s"
        rock = views.RockPaperScissorButton(bet,rps,comp,label="Rock",style=ButtonStyle.green,emoji="🪨")
        paper = views.RockPaperScissorButton(bet,rps,comp,label="Paper",style=ButtonStyle.green,emoji="🧻")
        scissors = views.RockPaperScissorButton(bet,rps,comp,label="Scissors",style=ButtonStyle.green,emoji="✂️")

        view = View()
        view.add_item(rock)
        view.add_item(paper)
        view.add_item(scissors)

        embed = discord.Embed(title="Play Rock Paper Scissor",color=discord.Color.random())
        await ctx.respond(embed=embed,view=view)

    @games.command()
    @check()
    async def snake_eyes(self,ctx:discord.ApplicationContext, bet: int = None):
        user = ctx.author
        await open_account(user)
        result =await show_account(user)
        if bet == None:
            await ctx.respond("You need to bet something")
            return
        if bet > result["wallet"]:
            await ctx.respond("You don't have that much amount in your wallet")
            return
        random_int = random.randint(0,5)
        random_int2 = random.randint(0,5)
        emoji__list1 = ["<:dice_1:859905254039355402>","<:dice_2:859905254439387156>","<:dice_3:859905254174752788>","<:dice_4:859905254149849168>","<:dice_5:859905253901205555>","<:dice_6:859905253728976897>"]
        random_emoji_1 = emoji__list1[random_int]
        random_emoji_2 = emoji__list1[random_int2]
        await ctx.respond("Rolling The Dice...")
        await asyncio.sleep(5)
        if random_int == 0:
            if random_int2 == 0:
                embed = discord.Embed(title = "Snake Eyes", description = f"{user.name} just won ", colour = discord.Colour.random())
                embed.add_field(name = random_int+ 1, value = random_emoji_1)
                embed.add_field(name = random_int2+ 1, value = random_emoji_2)
                await ctx.respond(embed = embed)
                await add_bal(user,bet)

            if random_int2 != 0:
                embed = discord.Embed(title = "Snake Eyes", description = f"{user.name} was quite close but he won only 50% of their bet amount", colour = discord.Colour.random())
                embed.add_field(name = random_int+ 1, value = random_emoji_1)
                embed.add_field(name = random_int2+ 1, value = random_emoji_2)
                await ctx.respond(embed = embed)
                await add_bal(user, (0.5*bet))
        if random_int2 == 0:
            if random_int != 0:
                embed = discord.Embed(title = "Snake Eyes", description = f"{user.name} was quite close but he won only 50% of their bet amount", colour = discord.Colour.random())
                embed.add_field(name = random_int+ 1, value = random_emoji_1)
                embed.add_field(name = random_int2+ 1, value = random_emoji_2)
                await ctx.respond(embed = embed)
                await add_bal(user, (0.5*bet))
        if random_int != 0:
            if random_int2 != 0:
                embed = discord.Embed(title = "Snake Eyes", description = f"{user.name} just lost", colour = discord.Colour.random())
                embed.add_field(name = random_int+ 1, value = random_emoji_1)
                embed.add_field(name = random_int2+ 1, value = random_emoji_2)
                await ctx.respond(embed = embed)
                await add_bal(user,-bet)
        
    @games.command()
    @check()
    async def bet(self,ctx:discord.ApplicationContext, amount: int = None):
        user = ctx.author
        await open_account(user)
        result =await show_account(user)
        if amount is None:
            await ctx.respond("You need to bet something")
            return
        if result['wallet'] < amount:
            await ctx.respond(f"You only have {result['wallet']} in your wallet")
            return
        random_int1 = random.randint(1,40)
        random_int2 = random.randint(1,40)
        user_int = random_int1
        client_int = random_int2
        if user_int > client_int:
            embed = discord.Embed(title = "Bet",description = f"{ctx.author.name} Won", colour = discord.Colour.random())
            embed.add_field(name = f"{ctx.author.name}'s score", value = user_int)
            embed.add_field(name = f"{self.client.user.name}'s score", value = client_int)
            await ctx.respond(embed = embed)
            await add_bal(user, amount)
        if user_int < client_int:
            embed = discord.Embed(title = "Bet",description = f"{self.client.user.name} won", colour = discord.Colour.random())
            embed.add_field(name = f"{ctx.author.name}'s score", value = user_int)
            embed.add_field(name = f"{self.client.user.name}'s score", value = client_int)
            await ctx.respond(embed = embed)
            await add_bal(user,-amount)

        if user_int == client_int:
            embed = discord.Embed(title = "Bet",description = f"{ctx.author.name} and {self.client.user.name} tied", colour = discord.Colour.random())
            embed.add_field(name = f"{ctx.author.name}'s score", value = user_int)
            embed.add_field(name = f"{self.client.user.name}'s score", value = client_int)
            await ctx.respond(embed = embed)
            await add_bal(user, (0.5*amount))

    @games.command()
    @check()
    async def blackjack(self,ctx:discord.ApplicationContext,bet:int = None):

        if bet is None:
            await ctx.respond("You need to bet something")
            return

        button1 = Button(label="Hit",emoji='⬆️',style=ButtonStyle.green)
        button2 = Button(label="Stay",emoji='🖐🏻',style=ButtonStyle.gray)
        button3 = Button(label="Stop",emoji='🛑',style=ButtonStyle.danger)

        random_number_user = [i for i in range(1,12)]
        random_number_bot = [i for i in range(1,12)]
        
        score = {"bot_score":0,"user_score":0}
        view = View()
        view.add_item(button1)
        view.add_item(button2)
        view.add_item(button3)

        embed = discord.Embed(title=f"Playing BlackJack with {ctx.author.name}",colour = discord.Color.random())
        embed.add_field(name = f"{self.client.user.name}'s Score", value=score["bot_score"],inline=False)
        embed.add_field(name = f"{ctx.author.name}'s Score", value=score["user_score"])
        msg = await ctx.respond(embed = embed,view=view)
        msg = await msg.original_message()  

        async def hit_callback(interaction:discord.Interaction):
            a = interaction.followup
            if interaction.user == ctx.author:
                score["bot_score"] += random.choice(random_number_bot)
                score["user_score"] += random.choice(random_number_user)
                embed = discord.Embed(title=f"Playing BlackJack with {ctx.author.name}",colour = discord.Color.random())
                embed.add_field(name = f"{self.client.user.name}'s Score", value=score["bot_score"],inline=False)
                embed.add_field(name = f"{ctx.author.name}'s Score", value=score["user_score"])
                await msg.edit(embed = embed,view=view)
                if score['bot_score'] < 21:
                    if score["user_score"] > 21:
                        for item in view.children:
                            item.disabled = True
                        await interaction.response.edit_message(view = view)
                        await a.send("You got busted haha!!")
                        await add_bal(ctx.author,-bet)
                
                elif score["bot_score"] >21 and score['user_score'] < 21:
                    for item in view.children:
                            item.disabled = True
                    await interaction.response.edit_message(view = view)
                    await a.send("You Won 🥳")
                    await add_bal(ctx.author,bet)

                elif score["bot_score"] >21 and score["user_score"] > 21:
                    for item in view.children:
                            item.disabled = True
                    await interaction.response.edit_message(view = view)
                    await a.send("You Tied bruh")
                
                elif score["bot_score"] == 21 and score["user_score"] !=21:
                    for item in view.children:
                            item.disabled = True
                    await interaction.response.edit_message(view = view)
                    await a.send("User reached 21 first! You busted!!")
                    await add_bal(ctx.author,-bet)
                
                elif score["user_score"] == 21 and score['bot_score'] !=21:
                    for item in view.children:
                            item.disabled = True
                    await interaction.response.edit_message(view = view)
                    await a.send("You reached 21 first, user busted!!")
                    await add_bal(ctx.author,bet)
                
                elif score["bot_score"] ==21 and score["user_score"] == 21:
                    for item in view.children:
                            item.disabled = True
                    await interaction.response.edit_message(view = view)
                    await a.send("You Tied bruh")
                        
            else:
                await interaction.response.send_message("You can't do that",ephemeral=True)
        
        async def stay_callback(interaction:discord.Interaction):
            a = interaction.followup
            if interaction.user == ctx.author:
                score["bot_score"] += random.choice(random_number_bot)
                # score["user_score"] += random.choice(random_number_user)
                embed = discord.Embed(title=f"Playing BlackJack with {ctx.author.name}",colour = discord.Color.random())
                embed.add_field(name = f"{self.client.user.name}'s Score", value=score["bot_score"],inline=False)
                embed.add_field(name = f"{ctx.author.name}'s Score", value=score["user_score"])
                await msg.edit(embed = embed,view=view)
                if score['bot_score'] < 21:
                    if score["user_score"] > 21:
                        for item in view.children:
                            item.disabled = True
                        await interaction.response.edit_message(view = view)
                        await a.send("You got busted haha!!")
                        await add_bal(ctx.author,-bet)
                                    
                    elif score["bot_score"] > score["user_score"]:
                        for item in view.children:
                                item.disabled = True
                        await interaction.response.edit_message(view = view)
                        await a.send("You got busted haha!!")
                        await add_bal(ctx.author,-bet)
                    
                    elif score["user_score"] > score["bot_score"]:
                        for item in view.children:
                                item.disabled = True
                        await interaction.response.edit_message(view = view)
                        await a.send("You Won 🥳")
                        await add_bal(ctx.author,bet)
                    elif score["user_score"] == score["bot_score"]:
                        for item in view.children:
                            item.disabled = True
                        
                        await interaction.response.edit_message(view = view)
                        await a.send("You Tied bruh")
 
                
                elif score["bot_score"] >21 and score['user_score'] < 21:
                    for item in view.children:
                            item.disabled = True
                    await interaction.response.edit_message(view = view)
                    await a.send("You Won 🥳")
                    await add_bal(ctx.author,bet)

                elif score["bot_score"] >21 and score["user_score"] > 21:
                    for item in view.children:
                            item.disabled = True
                    await interaction.response.edit_message(view = view)
                    await a.send("You Tied bruh")
                
                elif score["bot_score"] == 21 and score["user_score"] !=21:
                    for item in view.children:
                            item.disabled = True
                    await interaction.response.edit_message(view = view)
                    await a.send("User reached 21 first! You busted!!")
                    await add_bal(ctx.author,-bet)
                
                elif score["user_score"] == 21 and score['bot_score'] !=21:
                    for item in view.children:
                            item.disabled = True
                    await interaction.response.edit_message(view = view)
                    await a.send("You reached 21 first, user busted!!")
                    await add_bal(ctx.author,bet)
                
                elif score["bot_score"] ==21 and score["user_score"] == 21:
                    for item in view.children:
                            item.disabled = True
                    await interaction.response.edit_message(view = view)
                    await a.send("You Tied bruh")           
            else:
                await interaction.response.send_message('This is not for you',ephemeral=True)

        async def stop_callback(interaction:discord.Interaction):
            a = interaction.followup
            if interaction.user == ctx.author:
                for item in view.children:
                    item.disabled = True
                await interaction.response.edit_message(view = view)

                await a.send("You stopped so you automatically lost :(")
            else:
                await interaction.response.send_message('This is not for you',ephemeral=True)

        button1.callback = hit_callback
        button2.callback = stay_callback
        button3.callback = stop_callback

    @games.command()
    @check()
    async def connect4(self,ctx:discord.ApplicationContext,bet=None):
        if bet is None:
            await ctx.respond("You have to bet something")
            return
        elif bet > 1000:
            await ctx.respond("Easy game doesn't mean easy money :)")
        p1 = ctx.author
        p2 = self.client.user
        con4 = connect4.Connect4(6,7,p1,p2)
        board = await con4.createBoard()
        turn = 0
        view = View()
        gameOver = False
        for i in range(1,8):
            button = views.Connect4Button(board,con4,turn,gameOver,str(i))
            view.add_item(button)
        await con4.printBoard(ctx,board,view)

    @games.command()
    @check()
    async def impossiblequiz(self,ctx:discord.ApplicationContext):
        with open('./jsons/theimpossiblequiz.json',encoding='utf-8') as f:
            data = json.load(f)

        for index,i in enumerate(data):
            embed = discord.Embed(title='Impossible Quiz',colour=discord.Color.random())
            embed.add_field(name=f'Question No. {index+1}',value=i['question'])
            view = View()
            for index,opt in enumerate(i['options']):
                if index < 2:
                    button = views.TheImpossibleQuiz(opt,ButtonStyle.blurple,i['options'],i['answer_index'],row=1)
                    view.add_item(button)
                if index >= 2:
                    button = views.TheImpossibleQuiz(opt,ButtonStyle.blurple,i['options'],i['answer_index'],row=2)
                    view.add_item(button)
            await ctx.respond(embed=embed,view=view)

            try:
                som = await client.wait_for('interaction',check=lambda interaction:interaction.data['component_type'] == 2,timeout=10.0)
            except asyncio.TimeoutError:
                await ctx.respond("Ded")
                return

            if 'return' in i['options']:
                return   

            await asyncio.sleep(1)         

class Shop(commands.Cog):
    def __init__(self,client):
        self.client = client
    
    shops = discord.SlashCommandGroup('shop','Buy and sell your stuff',sv_id)

    @shops.command()
    @check()
    async def shop(self,ctx:discord.ApplicationContext,*,item:str = None):
        shopify = await shop()
        # print(shopify)
        embed = discord.Embed(title="Shop",colour=discord.Color.random())
        index = 0
        if item is None:
            for stuff in shopify:
                embed.add_field(name=f"{index+1}. {stuff['name']} ",value=f"Price - {stuff['price']}<:doge_coin:865669474917154837>\nDescription - {stuff['description']}",inline=False)
                index += 1
        
            await ctx.respond(embed = embed)
            return
        else:
            for stuff in shopify:
                if item.lower() == stuff['name'].lower():
                    embed.add_field(name=f"{stuff['name']} Price - {stuff['price']}<:doge_coin:865669474917154837>",value=stuff['description'])
                    await ctx.respond(embed = embed)
                    return
            
            await ctx.respond("The item you were looking for is not in the shop, please make sure you have the right spelling")

    @shops.command()
    @commands.is_owner()
    @check()
    async def add_items(self,ctx:discord.ApplicationContext):
        
        def check(message):
            return ctx.message.author == message.author    
        
        await ctx.respond("Enter name")
        name= await self.client.wait_for('message',check = check)
        await ctx.respond("Name Stored")
        await ctx.respond("Enter price")
        price= await self.client.wait_for('message',check=check)
        await ctx.respond("Price Stored")
        await ctx.respond("Enter description")
        description= await self.client.wait_for('message',check =check)
        await ctx.respond("Description Stored")
        try:
            int(price.content)
        except ValueError:
            await ctx.respond("Pls type a integer amount")
        
        await insert_into_shop(name.content,int(price.content),description.content)
        await ctx.respond("All things are done!")

    @shops.command()
    @check()
    async def sell(self,ctx,item=None,amount:int = 1):
        if item is None:
            await ctx.respond("Can't sell none")
            return
        
        inv_ = await inv(ctx.author)
        shop_ = await shop()

        for x in inv_:
            if x['item_name'] == item.title():
                if x['amount'] < amount:
                    await ctx.respond("You can't see more than what you have")
                    return
                else:
                    await ctx.respond(f"Successfully sold {amount} {x['item_name']}(s)")
                    await insert_into_inventory(ctx.author,x['item_name'],-amount)
                    price = [c['price'] for c in shop_ if c['name'] == x['item_name']]
                    await add_bal(ctx.author,amount*price[0])
                    return
        
        await ctx.respond(f"You don't have `{item.title()}` in your inventory")

    @shops.command()
    @check()
    async def buy(self,ctx,item=None,amount:int = 1):
        if item is None:
            await ctx.respond("Can't buy None")
            return
        
        shop_ = await shop()
        bank = await show_account(ctx.author)

        for x in shop_:
            if x['name'] == item.title():
                total_price = x['price']* amount

                if total_price > bank['wallet']:
                    await ctx.respond(f"You can't afford {amount} {item.title()}(s)")
                    return
                
                await ctx.respond(f"Bought {amount} {item.title()}(s) ")
                await insert_into_inventory(ctx.author,item.title(),amount)

    @shops.command()
    @check()
    async def inventory(self,ctx,user:discord.Member = None):
        if user is None:
            user = ctx.author
        await clean_inventory(user)
        inv_ = await inv(user)
        embed= discord.Embed(title = f"{user.name}'s Inventory",color = discord.Color.random())
        index = 0
        for item in inv_:
            embed.add_field(name = f"{index+1}. {item['item_name']}",value = item['amount'])
            index += 1
        await ctx.respond(embed=embed)

    @shops.command()
    @commands.is_owner()
    @check()
    async def removeitems(self,ctx:discord.ApplicationContext):
        def check1(message):
            return ctx.message.author == message.author

        items = []
        result =await shop()

        for item in result:
            items.append(item['name'])

        await ctx.respond("Enter The Name")
        name = await self.client.wait_for('message', check = check1)
        act_name = name.content

        if act_name.title() in items:
            embed = discord.Embed(title = "Item Removing",description = "React Within 30 seconds", colour= discord.Color.random())
            embed.add_field(name = act_name.capitalize(), value = "Do you really want to delete this?" )
            await ctx.respond(embed = embed)

        
        
        await remove_from_shop(act_name)
        await ctx.respond(f"Removed {act_name.title()} from shop")

    @shops.command()    
    @check()
    async def postmemes(self,ctx:discord.ApplicationContext):
        inv_ = await inv(ctx.author)

        laptop_or_not = [x for x in inv_ if x['item_name'] == "Laptop"]

        with open('./jsons/stuff.json', encoding='utf-8') as f:
            data = json.load(f)

        random_number = random.randint(1,3)
        earnings = random.randint(1,100)

        if laptop_or_not == [] or laptop_or_not[0]['amount'] == 0:
            await ctx.respond("You don't have a laptop in your inventory")
            return
        if laptop_or_not:
            if random_number == 1:
                # good
                embed = discord.Embed(title=f'{ctx.author.name} posted some memes',description=f"{random.choice(data['laptop_responses_good'])} {earnings} <:doge_coin:865669474917154837> ",color=discord.Color.random())
                await ctx.respond(embed=embed)
                await add_bal(ctx.author,earnings)
            elif random_number == 2:
                embed = discord.Embed(title=f'{ctx.author.name} posted some memes',description=random.choice(data['laptop_responses_bad']),color=discord.Color.random())
                await ctx.respond(embed= embed)
            elif random_number ==3:
                embed = discord.Embed(title=f'{ctx.author.name} posted some memes',description=f"{random.choice(data['laptop_responses_bad'])} and your laptop also broke",color=discord.Color.random())
                await insert_into_inventory(ctx.author,"Laptop",-1)
                await ctx.respond(embed=embed)

    @shops.command()
    @check()
    async def hunt(self,ctx:discord.ApplicationContext):
        inventory = await inv(ctx.author)
        with open('./jsons/stuff.json',encoding='utf-8') as f:
            data = json.load(f)
        
        rifle = [x for x in inventory if x['item_name'] == "Rifle"]
        chances = random.randint(1,3)
        earnings = random.randint(1,400)

        if rifle:
            if rifle[0]['amount'] == 0:
                await ctx.respond("You don't have a rifle")
                return
            
            else:
                if chances == 1:
                    # good
                    embed= discord.Embed(title=f'{ctx.author.name} Hunted',description=f"{random.choice(data['rifle_good'])}{earnings}<:doge_coin:865669474917154837>",color=discord.Color.random())
                    await add_bal(ctx.author,earnings)
                    await ctx.respond(embed= embed)
                    
                if chances == 2:
                    # bad
                    embed= discord.Embed(title=f'{ctx.author.name} Hunted',description=f"{random.choice(data['rifle_bad'])}",color=discord.Color.random())
                    await ctx.respond(embed=embed)
                if chances == 3:
                    #worse
                    embed= discord.Embed(title=f'{ctx.author.name} Hunted',description=f"{random.choice(data['rifle_bad'])} and your rifle broke",color=discord.Color.random())
                    await ctx.respond(embed=embed)
                    await insert_into_inventory(ctx.author,"Rifle",-1)
        else:
            await ctx.respond("You don't have a rifle")
    
    @shops.command()
    @check()
    async def fish(self,ctx:discord.ApplicationContext):
        inventory = await inv(ctx.author)
        fish = random.randint(1,5)


        pole = [x for x in inventory if x['item_name'] == "Fishing Pole"]
        # fishes = [x for x in inventory if x['item_name'] == "Fish"]
        
        if pole == []:
            await ctx.respond("You don't have a Fishing Pole")
            return
        
        elif pole[0]['amount'] == 0:
            await ctx.respond("You don't have a Fishing Pole")
            return
        else:
            embed= discord.Embed(title="Fishing",description=f"You pulled out {fish} :fish:",color = discord.Color.random())
            await ctx.respond(embed = embed)
            
            await insert_into_inventory(ctx.author,"Fish",fish)

    @shops.command()
    @commands.cooldown(1,60,BucketType.user)
    @check()
    async def eat(self,ctx:discord.ApplicationContext):
        inventory = await inv(ctx.author)
        chance = random.randint(1,10)
        earnings = random.randint(1,500)
        
        fish = [x for x in inventory if x['item_name'] == "Fish"]
        with open("./jsons/stuff.json",encoding='utf-8') as f:
            data = json.load(f)
        if fish == []:
            await ctx.respond("You don't have any fish ")
            return
        elif fish[0]['amount'] == 0:
            await ctx.respond("You don't have any fish")
            return
        
        else:
            if chance >= 5:
                # good
                embed = discord.Embed(title = f"{ctx.author} ate Fish",description=f"{random.choice(data['fish_good'])}".format(f"{earnings}<:doge_coin:865669474917154837>"),color=discord.Color.random())
                await ctx.respond(embed = embed)
                await insert_into_inventory(ctx.author,"Fish",-1)
                await add_bal(ctx.author,earnings)
            elif chance < 5:
                embed = discord.Embed(title = f"{ctx.author} ate Fish",description=f"{random.choice(data['fish_bad'])}".format(f"{earnings}<:doge_coin:865669474917154837>"),color=discord.Color.random())
                await ctx.respond(embed = embed)
                await insert_into_inventory(ctx.author,"Fish",-1)
                await add_bal(ctx.author,-earnings)

    @shops.command()
    @check()
    async def time(self,ctx:discord.ApplicationContext):
        random_chance = random.randint(1,10)

        time = datetime.now()
        time_str = time.ctime()
        time_str_list = time_str.split(" ")

        inventory = await inv(ctx.author)

        if inventory is None:
            await ctx.respond("You don't have a watch")
            return
        
        watch = [i for i in inventory if i['item_name'] == "Watch"]
        if watch == []:
            await ctx.respond("You don't have a watch")
            return
        elif watch[0]['amount'] == 0:
            await ctx.respond("You don't have a watch")
            return


        if random_chance == 10:
            embed = discord.Embed(title=f'{ctx.author.name} saw time',description=f'The time was {time_str_list[3]}, but your watch broke',colour= discord.Color.random())
            await ctx.respond(embed=embed)
            await insert_into_inventory(ctx.author,"Watch",-1)
        else:
            # good
            embed = discord.Embed(title=f'{ctx.author.name} saw time',description=f'The time was {time_str_list[3]}',colour= discord.Color.random())
            await ctx.respond(embed = embed)

class Fun(commands.Cog):
    def __init__(self,client):
        self.client = client
    
    fun = discord.SlashCommandGroup('fun','less intensive gaming',sv_id)

    @fun.command()
    @check()
    @commands.cooldown(1,60*60*24, BucketType.user)
    async def daily(self,ctx:discord.ApplicationContext):
        result = await show_account(ctx.author)
        if result is None:
            await open_account(ctx.author)
            result = await show_account(ctx.author)
        
        await add_bal(ctx.author,500)
        embed = discord.Embed(title = 'Daily Rewards',description = "Here are your 500<:doge_coin:865669474917154837>", colour= discord.Color.random())
        await ctx.respond(embed = embed)

    @fun.command()
    @check()
    async def hack(self,ctx:discord.ApplicationContext,user: discord.Member):
        if user.id == ctx.author.id or user.id == self.client.user.id:
            await ctx.respond("You are trying to rob the wrong people")
            return

        author =await show_account(ctx.author)
        userm =await show_account(user)

        if author is None or userm is None :
            await ctx.respond("Either you don't have a bank or they don't.")
            return
        
        if author['wallet'] <= 200 or userm['wallet'] <= 200:
            await ctx.respond("You need atleast 200 <:doge_coin:865669474917154837> dork!!!")
            return
    
        msg = await ctx.respond("<a:loading:872874857925320754> Hacking Initiated.")
        msg = await msg.original_message()
        await asyncio.sleep(1)
        await msg.edit(content = "<a:loading:872874857925320754> Gathering Credentials")
        await asyncio.sleep(1)
        await msg.edit(content = "<a:loading:872874857925320754> Accessing Wallet")
        await msg.delete()
        def p_bar(a): 
            total = 25
            rn = round(a/4)
            body = "░" * total 
            li = list(body)

            for i , elem in enumerate(li[:rn]):
                li[i] = "▓"

            ku = "".join(li)
            return f"{ku}"

        mesg = await ctx.respond(p_bar(10))
        await asyncio.sleep(1)
        await mesg.edit(content = p_bar(30))
        await asyncio.sleep(1)
        await mesg.edit(content = p_bar(50))
        await asyncio.sleep(1)
        await mesg.edit(content = p_bar(70))
        await asyncio.sleep(5.2)
        random_no = random.randint(1,2)
        if random_no == 1:
            random_amt = random.randint(1,round(userm[1]/2))
            embed = discord.Embed(title = "Hacking Successful", colour = discord.Color.random())
            embed.add_field(name = f"You robbed {user.name}", value = f"You got {random_amt} <:doge_coin:865669474917154837>")
            await ctx.respond(embed = embed)
            await add_bal(ctx.author,random_amt)
            await add_bal(user,-random_amt)
        else:
            random_amt = random.randint(1,round(author[1]/2))
            embed = discord.Embed(title = "Hacking Failed", colour = discord.Color.random())
            embed.add_field(name = f"You tried robbing {user.name}", value = f"You were caught and had to pay {random_amt} <:doge_coin:865669474917154837>")
            await ctx.respond(embed = embed)
            await add_bal(user,random_amt)
            await add_bal(ctx.author,-random_amt)

    @fun.command()
    @check()
    async def charity(self,ctx:discord.ApplicationContext,amount : int = None):
        result =await  show_account(ctx.author)
        if result is None:
            await ctx.respond("You yourself need charity!")
            return
        if amount is None:
            await ctx.respond("You can't donate 0 amounts")
            return
        if amount > result['wallet']:
            await ctx.respond("You can't donate more than you have")
            return
        
        random_pts = random.randint(-10, 30)
        remsut =await  client.db.fetchrow("SELECT * FROM luck WHERE member_id = $1",ctx.author.id)

        if remsut is None:
            await client.db.execute("INSERT INTO luck (member_id,pts,amount) VALUES($1,$2,$3)",ctx.author.id,0,amount)
            await add_bal(ctx.author,-amount)
            await ctx.respond("As this is your first donation, you recieve 0 luck points. ")
            return
        
        await client.db.execute("UPDATE luck SET pts =$1,amount = $2 WHERE member_id = $3",remsut['pts']+random_pts,remsut['amount']+amount,ctx.author.id)
        await add_bal(ctx.author,-amount)
        await ctx.respond(f"{ctx.author.mention} has donated {amount} <:doge_coin:865669474917154837>, they recieved {random_pts} luck points.")
        return

    @fun.command()
    @check()
    async def luck(self,ctx:discord.ApplicationContext):
        result = await client.db.fetchrow("SELECT * FROM luck WHERE member_id = $1",ctx.author.id)

        if result is None:
            embed = discord.Embed(title = f"{ctx.author.name}'s Luck Points", colour = discord.Color.random())
            await ctx.respond(embed = embed)
            return
        
        embed = discord.Embed(title = f"{ctx.author.name}'s Luck Points", colour = discord.Color.random())
        embed.add_field(name = "Luck Points", value = result['pts'],inline=False)
        embed.add_field(name = "Amount Donated", value = f"{result['amount']}<:doge_coin:865669474917154837>",inline=False)
        await ctx.respond(embed = embed)

    @fun.command()
    @check()
    async def give(self,ctx:discord.ApplicationContext,user:discord.Member,amount:int):

        await open_account(ctx.author)
        author = await show_account(ctx.author)
        if amount > author['wallet']:
            await ctx.respond("You can't give more than what you have")
            return

        await add_bal(user,amount)
        await add_bal(ctx.author,-amount)
        embed = discord.Embed(title = "Sent Successfully", description = f"You just sent {user.name} {amount} <:doge_coin:865669474917154837> ", colour = discord.Colour.random())
        await ctx.respond(embed =embed)

    @fun.command()
    @check()
    async def search(self,ctx:discord.ApplicationContext):
        
        with open('./jsons/search.json',encoding='utf-8') as f:
            search_data = json.load(f)

        places = list(search_data.keys())
        act_p = []
        act = [0,1,2,3]
        for x in range(0,3):
            random_choice = random.choice(act)
            act_p.append(places[random_choice])
            act.remove(random_choice)


        random_amt = random.randint(1,100)
        button1 = Button(label=act_p[0],style=ButtonStyle.green)
        button2 = Button(label=act_p[1],style=ButtonStyle.green)
        button3 = Button(label=act_p[2],style=ButtonStyle.green)
        
        view = View()
        view.add_item(button1)
        view.add_item(button2)
        view.add_item(button3)

        embed = discord.Embed(title = "Search",description = "Seach the area", colour=discord.Color.random())
        msg = await ctx.respond(embed= embed, view =view)
        msg = await msg.original_message()

        async def button_callback_1(interaction):
            await interaction.response.send_message(f"{random.choice(search_data[act_p[0]])}{random_amt} <:doge_coin:865669474917154837>")
            await add_bal(ctx.author,random_amt)
            await msg.delete()
            return
        async def button_callback_2(interaction):
            await interaction.response.send_message(f"{random.choice(search_data[act_p[1]])}{random_amt} <:doge_coin:865669474917154837>")
            await add_bal(ctx.author,random_amt)
            await msg.delete()
            return
        async def button_callback_3(interaction):
            await interaction.response.send_message(f"{random.choice(search_data[act_p[2]])}{random_amt} <:doge_coin:865669474917154837>")
            await add_bal(ctx.author,random_amt)
            await msg.delete()
            return

        button1.callback = button_callback_1
        button2.callback = button_callback_2
        button3.callback = button_callback_3
 
    @fun.command()
    @check()
    async def coinflip(self,ctx:discord.ApplicationContext):
        choice = random.choice(['Head','Tails'])
        button1 = views.CoinFlipButton(choice,label="Head",style=ButtonStyle.primary)
        button2 = views.CoinFlipButton(choice,label="Tails",style=ButtonStyle.primary)
        view = View()
        view.add_item(button1)
        view.add_item(button2)


        await ctx.respond("Test your luck out",view = view)

    @fun.command()
    @commands.is_owner()
    async def users(self,ctx):
        bank = await client.db.fetch("SELECT * FROM main")

        await ctx.author.send(f"{len(bank)} users use the economy feature")

class Premium(commands.Cog):
    def __init__(self,client):
        self.client = client
    
    prem = discord.SlashCommandGroup('prem','For the special friends of KarnaV',sv_id)
    
    @prem.command()
    @commands.is_owner()
    async def premium(self,ctx:discord.ApplicationContext,user:discord.Member):
        result =await client.db.fetch("SELECT * FROM premium WHERE member_id = $1",user.id)

        if not result:
            await client.db.execute("INSERT INTO premium(member_id) VALUES($1)",user.id)

            await ctx.respond(f"I have added {user.mention} as a premium user")
            return
        if result:
            await ctx.respond("This user is already a premuim user :)")

    @prem.command()
    @commands.is_owner()
    async def unprimium(self,ctx:discord.ApplicationContext,user:discord.Member):
        result = await client.db.fetch("SELECT * FROM premium WHERE member_id = $1",user.id)

        if not result:
            await ctx.respond("This user is not a premuim user")

        if result:
            await client.db.execute("DELETE FROM premium WHERE member_id = $1",user.id)
            await ctx.respond(f"I have removed {user.mention} from a premium user")
            return

    @prem.command()
    @is_premium()
    @check()
    async def crime(self,ctx:discord.ApplicationContext):
        user_acc = await show_account(ctx.author)
        random_money = random.randint(300,2000)        

        if user_acc['wallet'] < 2000:
            await ctx.respond("You need 2000 <:doge_coin:865669474917154837> to commit a crime")
            return

        with open('./jsons/stuff.json',encoding='utf-8') as f:
            data = json.load(f)
        
        random_gen = random.randint(1,10)
        if random_gen <= 5:
            # good
            embed = discord.Embed(title = f"{ctx.author.name} commmited a crime 😳 ",description = f"{random.choice(data['crime_good'])} {random_money} <:doge_coin:865669474917154837>" ,colour = discord.Color.random())
            await add_bal(ctx.author,random_money)
            await ctx.respond(embed = embed)

        if random_gen > 5:
            # bad
            req = random.choice(data['crime_bad'])
            embed = discord.Embed(title = f"{ctx.author.name} commmited a crime 😳 ",description  = req.format(random_money), colour= discord.Color.random())
            await add_bal(ctx.author,-random_money)
            await ctx.respond(embed=embed)
 
    @prem.command()
    @is_premium()
    @check()
    @commands.cooldown(1,60, BucketType.user)
    async def reversal(self,ctx:discord.ApplicationContext):

        async with aiohttp.ClientSession() as session:
            r = await session.get('https://random-word-api.herokuapp.com/word?number=10')
            words =await r.json()
        
        random_word = random.choice(words)

        reversal_word = random_word[::-1]
        await ctx.respond(reversal_word)

        await ctx.respond("Please give answer in 10 seconds")

        def check(message):
            return ctx.message.author == message.author

        try:
            answer = await self.client.wait_for('message', check=check, timeout = 10) 
        except asyncio.TimeoutError:
            await ctx.respond("Opps your time ran out :(")
            return
        
        if answer.content.lower() == random_word:
            await ctx.respond('correct, take 100 <:doge_coin:865669474917154837>')
            await add_bal(ctx.author,100)
        
        else:
            await ctx.respond("Your word doesn't match with the one given to you")
            return

    @prem.command()
    @is_premium()
    @check()
    async def finish(self,ctx:discord.ApplicationContext):
        with open('./jsons/stuff.json',encoding='utf-8') as f:
            dam = json.load(f)
        
        sentences = dam['sentences']

        sentence = random.choice(sentences)
        old_data = sentence.split(" ")
        data = sentence.split(" ")
        random_word = random.choice(data)
        data.remove(random_word)
        a_str = " "

        for x in old_data:
            if x == random_word:
                a_str += "_ "*len(random_word)
            else:
                a_str += f"{x} "


        embed = discord.Embed(title = "Finish The Line",description = f"`{a_str}`" ,colour = discord.Color.random())
        embed.set_footer(text = "Let's see if you are smart enough to figure it out :)")
        await ctx.respond(embed=embed)


        def check(message):
            return ctx.message.author == message.author
        
        x = 3
        while x >=0:
            x -=1
            answer = await self.client.wait_for('message', check = check)
            if answer.content.lower() == random_word.lower():
                await ctx.respond(f"You guessed it right it was `{random_word}`. The full sentence is `{sentence}`, take 100 <:doge_coin:865669474917154837>")
                await add_bal(ctx.author,100)
                return
            
            elif x == 0:
                await ctx.respond(f"Your tries are over :(, it was `{random_word}`. The full sentence was `{sentence}`")
                return

            else:
                await ctx.respond("Umm this is not the correct answer, try again")

class Pet(commands.Cog):
    def __init__(self,client):
        self.client = client
    
    pet = discord.SlashCommandGroup('pet','Have your own companion')

    @pet.command()
    @check()
    async def pet_list(self,ctx:discord.ApplicationContext,* ,animal= None):
        result =await  client.db.fetch("SELECT * FROM pets")
        embed = discord.Embed(title = 'Pets', colour = discord.Color.random())
        if animal is None:
            for pet in result:
                embed.add_field(name = f"{pet['name']} - {pet['price']} <:doge_coin:865669474917154837> ", value = pet['description'], inline=False)
            await ctx.respond(embed = embed)
        else:
            for pt in result:
                if pt['name'].lower() == animal.lower():
                    embed.add_field(name = f'{pt["name"]} - {pt["price"]} <:doge_coin:865669474917154837> ', value = pt['description'])
                    await ctx.respond(embed = embed)

    @pet.command()
    @commands.is_owner()
    @check()
    async def add_pet(self,ctx:discord.ApplicationContext):

        def check(message):
            return message.author == ctx.message.author
        
        await ctx.respond("Enter the Name")
        name = await self.client.wait_for('message', check = check)
        await ctx.respond("Enter the Description")
        desc = await self.client.wait_for('message', check = check)
        await ctx.respond("Enter the Price")
        price = await self.client.wait_for('message', check = check)

        await client.db.execute("INSERT INTO pets(name,description,price) VALUES($1,$2,$3)",name.content,desc.content,int(price.content))
        await ctx.respond("Done !")

    @pet.command()
    @check()
    async def adopt(self,ctx:discord.ApplicationContext,*,animal = None):
        pet_store =await client.db.fetch("SELECT * FROM pets")
        peta = await show_pet(ctx.author)
        bank = await show_account(ctx.author)


        if animal is None:
            await ctx.respond("You can't adopt No animal")
            return
        
        if peta is None:
            for pet in pet_store:
                if pet['name'].lower() == animal.lower():
                    if pet['price'] > bank['wallet']:
                        await ctx.respond("You don't have money to adopt this animal")
                        return
                    await ctx.respond(f"You are adopting {pet['name']}")
                    await adopt_pet(pet['name'],ctx.author)
                    await ctx.respond(f"You successfully adopted {pet[0]}, take good care of it ")
                    return
        

        elif (peta[1]):
            await ctx.respond("You already have a pet, can't get another one ;-;")
            return
        else:
            await ctx.respond("The animal you are trying to adopt is not in the database")
            return

    @pet.command()
    @check()
    @has_pet()
    async def feed(self,ctx:discord.ApplicationContext):
        peta =await show_pet(ctx.author)
        inv_ = await inv(ctx.author)
        random_number = random.randint(1,30)

        if peta is None:
            await ctx.respond(f"{ctx.author.mention} You don't have any pets")
            return
        
        else:
            for treat in inv_:
                if treat['item_name'] == "Treats" and treat['amount'] > 0:
                    await ctx.respond(f"{ctx.author.mention} Fed their pet")
                    await insert_into_inventory(ctx.author,"Treats",-1)

                    if random_number + peta['hunger'] > 100:
                        new = random_number+ peta['hunger']
                        old = new - 100
                        random_number = random_number-old
                        await update_stats(ctx.author,"hunger",random_number)

                    else:
                        await update_stats(ctx.author,"hunger",random_number)
                    
                    return
            
            await ctx.respond("You don't have any treats in your inventory")

    @pet.command()
    @check()
    @has_pet()
    async def disown(self,ctx:discord.ApplicationContext):
        peta = await show_pet(ctx.author)
        
        if peta is None:
            await ctx.respond("You don't have any pets to disown")
            return
        else:
            pet = peta['name']
            await client.db.execute("DELETE FROM pet WHERE member_id = $1",ctx.author.id)
            await ctx.respond(f"You disowned {pet} 😔")

    @pet.command()
    @has_pet()
    @check()
    async def pet_stats(self,ctx:discord.ApplicationContext,user:discord.Member = None):
        if user  is  None:
            user = ctx.author
        peta = await show_pet(user)
        if peta is None:
            await ctx.respond("You don't have a pet")
            return

        embed = discord.Embed(title = f"{peta['name']} Stats", colour = discord.Color.random())
        embed.add_field(name = 'Hunger', value = f"{peta['hunger']}/100")
        embed.add_field(name = 'Experience', value = f"{peta['exp']}/100")
        embed.add_field(name = "Attack", value = f"{peta['attack']}/100 ")
        embed.add_field(name = "Defence", value = f"{peta['defence']}/100 ")
        embed.add_field(name = "Type", value = f"{peta['name']}")
        embed.add_field(name = "Level", value = f"{peta['level']}")
        embed.add_field(name = "Nickname", value = f"{peta['nick']}")
        await ctx.respond(embed = embed)

    @pet.command()
    @has_pet()    
    @check()
    async def petfight(self,ctx:discord.ApplicationContext):
        peta =await show_pet(ctx.author)
        random_number = random.randint(1,10)
        random_earnings = random.randint(1,200)
        random_attack = random.randint(1,15)
        random_exp = random.randint(1,15)
        random_def = random.randint(1,15)
        with open('./jsons/stuff.json',encoding='utf-8') as f:
            data = json.load(f)
        
        if random_number < 5:
            good = random.choice(data[f"{peta['name'].lower()}_good"])
            embed = discord.Embed(title = f"{peta['name']} attacked",description = good.format(f"{random_earnings} <:doge_coin:865669474917154837>"),colour = discord.Color.random())
            await ctx.respond(embed = embed)
            await add_bal(ctx.author,random_earnings)
            soom =peta[4] + random_attack  
            if soom> 100:
                soom = soom - 100
                random_attack -= soom
                await update_stats(ctx.author,"attack",random_attack)
                await update_stats(ctx.author,"exp",random_exp)
                await update_stats(ctx.author,"defence",random_def)
                
            else:
                await update_stats(ctx.author,"attack", random_attack)
                await update_stats(ctx.author,"exp",random_exp)
                await update_stats(ctx.author,"defence",random_def)



        else:
            bad = random.choice(data[f"{peta[1].lower()}_bad"])
            embed = discord.Embed(title = f"{peta[1]} attacked", description = bad, colour= discord.Color.random())
            await ctx.respond(embed = embed)
        
        random_number = random.randint(1,20)
        hunger = peta[2]
        if (hunger- random_number)> 0:
            await update_stats(ctx.author,"hunger",-random_number)
        else:
            await ctx.respond(f"{ctx.author.mention}, Your pet is really hungry")

    @pet.command()
    @has_pet()
    @check()
    async def play(self,ctx:discord.ApplicationContext): 
        functions = [f for _, f in getmembers(games,isfunction) if f.__module__ == games.__name__]
        random_number = random.randint(1,len(functions))
        bank = await show_account(ctx.author)

        if bank['wallet'] < 200:
            return await ctx.respond("You need atleast 200 <:doge_coin:865669474917154837> to play")

        if random_number == 1:
            a = await games.a_hangman(ctx)
        
        elif random_number== 2:
            a = await games.a_rock_paper_scissor(ctx)

        elif random_number == 3:
            a = await games.a_finish(ctx)

        elif random_number == 4:
            a = await games.a_dragon(ctx)
        
        random_no = random.randint(1,20)
        peta = await show_pet(ctx.author)

        if peta['hunger']- random_no> 0:
            await update_stats(ctx.author,"hunger",-random_no)

    @pet.command()
    @has_pet()
    @check()
    async def fetch(self,ctx:discord.ApplicationContext):
        inventory = await inv(ctx.author)
        if inventory is None:
            await ctx.respond("You don't have any bones in your inventory")
            return
        peta = await show_pet(ctx.author)
        chance = random.randint(1,20)
        chance_even = [f for f in range(1,20) if f%2 ==0]
        chance_odd = [i for i in range(1,20) if i%2 != 0]
        bone = [k for k in inventory if k['item_name'] == "Bone"]
        if bone == []:
            await ctx.respond("You don't have any bones in your inventory")
            return
        if bone[0]['amount'] == 0:
            await ctx.respond("You don't have any bones in your inventory")
            return
        
        if chance in chance_even:
            # good
            embed = discord.Embed(title=f"{ctx.author.name} Played Fetch with {peta[1]}",description=f"Your {peta[1]} fetched you the bone",color=discord.Color.random())
            await update_stats(ctx.author,"exp",4)
            await ctx.respond(embed=embed)
        elif chance in chance_odd:
            #bad
            embed = discord.Embed(title=f"{ctx.author.name} Played Fetch with {peta[1]}",description=f"Your {peta[1]} did fetched you the bone, you lost it",color=discord.Color.random())
            await update_stats(ctx.author,"exp",4)
            await insert_into_inventory(ctx.author, "Bone",-1)
            await ctx.respond(embed=embed)

    @pet.command()
    @has_pet()
    @check()
    async def level_up(self,ctx:discord.ApplicationContext):
        peta = await show_pet(ctx.author)

        pet_exp = peta['exp']
        pet_attack = peta['attack']
        pet_defence = peta['defence']
        pet_level = peta['level']


        if pet_exp == 100 and pet_attack == 100 and pet_defence == 100:
            await ctx.respond("Your pet can level up!")
            random_number = random.randint(1000,5000)
            await add_bal(ctx.author,random_number)
            await client.db.execute("UPDATE pet SET level = $1, attack = $2, exp = $3, defence = $4 WHERE member_id = $5",pet_level+1, 0,0,0,ctx.author.id)
            await ctx.respond(f"WOW you also got {random_number} <:doge_coin:865669474917154837> as a reward ")


        else:
            await ctx.respond("Your pet still needs some time to upgrade, it can upgrade when it reaches 100 in every stats") 
            return

    @pet.command()
    @has_pet()
    @check()
    @commands.cooldown(1,10800,BucketType.user)
    async def nickname(self,ctx:discord.ApplicationContext,*,name):
        a = await show_pet(ctx.author)
        await client.db.execute('UPDATE pet SET nick = $! WHERE member_id = $2',name,ctx.author.id)
        await ctx.respond(f"Named your {a[1]} {name} ")

class Work(commands.Cog):
    def __init__(self,client):
        self.client = client

    works = discord.SlashCommandGroup('works', "Don't be a jobless bum",sv_id)

    @works.command()
    @check()
    async def worklist(self,ctx:discord.ApplicationContext, work = None):
        result =await client.db.fetch("SELECT * FROM job")

        embed = discord.Embed(title = "Jobs", colour=discord.Color.random())
        if work == None:
            for job in result:
                embed.add_field(name = job['name'], value=f"Pay - {job['pay']} <:doge_coin:865669474917154837>\nDescription - {job['description']}", inline=False)
            
            await ctx.respond(embed = embed)
            return
        
        for job in result:
            if work.lower() == job['name'].lower():
                embed.add_field(name = job['name'], value=f"Pay - {job['pay']} <:doge_coin:865669474917154837>\nDescription - {job['desciption']}", inline=False)
                await ctx.respond(embed= embed)
                return
        else:
            await ctx.respond("The job you tried seaching for doesn't exist rn, please check your spellings")
            return

    @works.command()
    @check()
    @commands.cooldown(1,60*60, BucketType.user)
    async def work(self,ctx:discord.ApplicationContext):
        mem_job = await client.db.fetchrow("SELECT * FROM mem_job WHERE member_id = $1",ctx.author.id)
        random_gen = random.randint(1,10)
        random_good = random.randint(1,20)

        
        if mem_job == None:
            await ctx.respond("You don't have any job, please use `evo jw` to get new employment")
            return
        
        elif mem_job['cond'] == str(1):
            with open('./jsons/stuff.json',encoding='utf-8') as f:
                response = json.load(f)
            if random_gen < 5:
                #good
                response = random.choice(response[f'{mem_job["name"].lower()}_good'])
                embed = discord.Embed(title = f"{ctx.author.name} worked!!", description = f"{response} {mem_job['pay']} <:doge_coin:865669474917154837>", colour= discord.Color.random())
                await add_bal(ctx.author,mem_job['pay'])
                
                await ctx.respond(embed = embed)
            elif random_gen > 5:
                #bad
                respo = random.choice(response[f'{mem_job["name"].lower()}_bad'])
                embed = discord.Embed(title = f"{ctx.author.name} worked!!", description = f"{respo}", colour= discord.Color.random())
                await ctx.respond(embed = embed)
            elif random_gen == 5:
                #worst
                resp = random.choice(response[f'{mem_job["name"].lower()}_fire'])
                embed = discord.Embed(title = f"{ctx.author.name} worked!!", description = f"{resp}", colour= discord.Color.random())
                await ctx.respond(embed =embed)
                await client.db.execute("UPDATE mem_job SET cond= ? WHERE member_id = ?",False, ctx.author.id)

            if random_good == 10:
                await ctx.respond("You got a promotion :), use `evo sw` for more information")
                sql = "UPDATE mem_job SET pay = ? WHERE member_id = ?"
                val = (mem_job[3]+ 1000, ctx.author.id)
                await client.db.execute("UPDATE mem_job SET pay = ? WHERE member_id = ?",mem_job[3]+ 1000, ctx.author.id)
        
        elif mem_job['cond'] == str(0):
            await ctx.respond(f"You were fired from your job as {mem_job[1]}, please wait 1 hour to be able to apply for other job")
            await asyncio.sleep(3600)
            await client.db.execute("UPDATE mem_job SET cond = ? WHERE member_id = ?",None,ctx.author.id)

            await ctx.respond(f"Your Fire Period is over, you can apply for jobs now :) {ctx.author.mention} ")
        
    @works.command()
    @check()
    async def joinwork(self,ctx:discord.ApplicationContext,work):
        jobs =await client.db.fetch("SELECT * FROM job")
        jok = []
        mem_job =await show_job(ctx.author)
        for job in jobs:
            jok.append(job['name'].lower())
        if work.lower() not in jok:
            await ctx.respond(f"You can't join this work check `evo wl` to check the works available")
            return
        

        if mem_job is None:
            for joo in jobs:
                if joo['name'].lower() == work.lower():
                    await client.db.execute("INSERT INTO mem_job(member_id,name,cond,pay) VALUES($1,$2,$3,$4)",ctx.author.id,joo['name'],str(1),joo['pay'])
                    await ctx.respond(f"Congratulations !! You are now working as {joo['name']}")
                    return
        if mem_job['cond'] == str(1):
            for jap in jobs:
                if mem_job['name'].lower() == work.lower():
                    await ctx.respond(f"You already work as {mem_job['name']}")
                    return
                elif jap['name'].lower() == work.lower():
                    await ctx.respond(f"Congratulations !! You are now working as {jap['name']}")
                    await client.db.execute("UPDATE mem_job SET name=$1, cond= $2, pay = $3 WHERE member_id = $4",jap[0],str(1),jap[1],ctx.author.id)
                    return
        if mem_job['cond'] == str(-1):
            for jjap in jobs:
                if mem_job['name'].lower() == work.lower():
                    await ctx.respond(f"You already work as {mem_job['name']}")
                    return
                elif jjap['name'].lower() == work.lower():
                    await ctx.respond(f"You resigned from your work as a {mem_job['name']}, now you work as {jjap['name']}")
                    await client.db.execute("UPDATE mem_job SET name=$1, cond= $2, pay = $3 WHERE member_id = $4",jjap[0],str(-1),jjap[1],ctx.author.id)
                    return
                
        if mem_job[2] == str(0):
            await ctx.respond("You have been recently fired from your job! Please wait to apply after sometime")
            return
        
    @works.command()
    @check()
    async def showwork(self,ctx:discord.ApplicationContext):
        result =await show_job(ctx.author)

        if result is None:
            await ctx.respond("You don't have a record with employement")
            return

        embed = discord.Embed(title = f"Works as {result['name']}", colour= discord.Color.random())
        if result['cond'] == str(0):
            embed.add_field(name = f"Current Condition - Fired\n", value = "Earliar Pay - {:,} <:doge_coin:865669474917154837>".format(result['pay']))
        
        if result['cond'] == None:
            embed.add_field(name = "Doesn't Work, or resigned\n", value = "Earliar Pay - {:,} <:doge_coin:865669474917154837>".format(result['pay']))
        
        if result["cond"] == str(1):
            embed.add_field(name = "Currently Employed", value = "Current Pay - {:,} <:doge_coin:865669474917154837>".format(result['pay']))
        
        await ctx.respond(embed = embed)

    @works.command()
    @check()
    @commands.is_owner()
    @commands.cooldown(1,19,BucketType.user)
    async def addwork(self,ctx:discord.ApplicationContext):

        def check1(message):
            return ctx.message.author == message.author

        await ctx.respond("I will start the job adding process")

        await ctx.respond("Enter The Name")
        name = await self.client.wait_for('message', check = check1)
        act_name = name.content

        await ctx.respond("Name has been stored")
        await ctx.respond("Enter the pay")
        try:
            pay = await self.client.wait_for('message', check = check1)
            act_pay = pay.content
        except ValueError:
            await ctx.respond("Please Put a Integer Value")
            return
        await ctx.respond("Pay has been stored")
        await ctx.respond("Enter the description")

        desc = await self.client.wait_for('message', check = check1)
        act_desc = desc.content
        await ctx.respond("Description has been stored")

        embed = discord.Embed(title = "Job Adding",description = "React Within 30 seconds", colour= discord.Color.random())
        embed.add_field(name = name.content, value = f"Pay - {pay.content}\n Description - {desc.content}")        
        await ctx.respond(embed = embed)

        

        await client.db.execute("INSERT INTO job(name,pay,description) VALUES($1,$2,$3)",act_name.title(),int(act_pay),act_desc.title())
        await ctx.respond("New Job Created successfully")
        return
        
    @works.command()
    @check()
    @commands.is_owner()
    async def removework(self,ctx:discord.ApplicationContext):
        result =await  client.db.fetch("SELECT * FROM job")
        job = await show_job(ctx.author)
        work = []
        pay = []
        desc = []
        for works in result:
            work.append(works["name"].lower())
            pay.append(works["pay"])
            desc.append(works["description"])
        def check(message):
            return ctx.message.author == message.author
        
        await ctx.respond("Add the name of the job to remove")
        answer = await self.client.wait_for('message', check=check)
        if answer.content.lower() in work:
            ind = work.index(answer.content.lower())
            embed = discord.Embed(title = "Remove Work", colour = discord.Color.random())
            embed.add_field(name = f"Job Name - {work[ind].capitalize()}", value=f"{pay[ind]}\n{desc[ind]}")
            await ctx.respond(embed=embed)


            await client.db.execute("DELETE FROM job WHERE name = $1",work[ind].capitalize())
            await ctx.respond(f"Alright, removed {work[ind]}")


            
        if job["name"] == answer.content.capitalize():
            await client.db.execute("DELETE FROM mem_job WHERE name = $1",work[ind].capitalize())
            await ctx.respond(f"{ctx.author.mention} Since you had {work[ind].capitalize()} Job, the job is deleted, get a new job")


        elif answer.content.lower() not in work:
            await ctx.respond(f"No job of name {answer.content.capitalize} ")



def setup(client):
    client.add_cog(Economy(client))
    client.add_cog(Games(client))
    client.add_cog(Shop(client))
    client.add_cog(Fun(client))
    client.add_cog(Premium(client))
    client.add_cog(Pet(client))
    client.add_cog(Work(client))