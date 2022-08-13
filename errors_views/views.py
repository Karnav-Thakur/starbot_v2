import json
import aiohttp
import discord
from discord.ui import Button,Select
from cogs import economy
from bs4 import BeautifulSoup
from stars import client,sv_id
import random
from api_wrappers import thispersondoesnotexist

class EmojiButton(Button):
    def __init__(self,emoji,answer_emoji):
        super().__init__(emoji=emoji)
        self.answer_emoji = answer_emoji

    async def callback(self,interaction:discord.Interaction):
        a = interaction.followup
        if str(self.emoji) == self.answer_emoji:
            for item in self.view.children:
                item.disabled= True
            await interaction.response.edit_message(view=self.view)
            await a.send(f"Good work!!! {interaction.user.mention} Here take the 100 <:doge_coin:865669474917154837>")
            await economy.add_bal(interaction.user,100)
            
        else:
            for item in self.view.children:
                item.disabled= True
            await interaction.response.edit_message(view=self.view)
            await a.send(f"Wrong, the correct answer was, {self.answer_emoji}")

class OrderButton(Button):
    def __init__(self,label,order_of_iteration,user_inp):
        super().__init__(label=label)
        self.order = order_of_iteration
        self.user_order =user_inp

    async def callback(self,interaction:discord.Interaction):
        a = interaction.followup
        self.user_order.append(self.label)
        self.disabled = True
        await interaction.response.edit_message(view=self.view)

        check = {"check":0}

        for item in self.view.children:
            if item.disabled == True:
                continue
            else:
                check["check"] = 1
        
        if check["check"] == 0:
            if self.user_order == self.order:
                await a.send("You did well, here are your 100 <:doge_coin:865669474917154837>")
                await economy.add_bal(interaction.user,100)
            else:
                await a.send("you failed")

class FindImposterButton(Button):
    def __init__(self,bet,answer_emoji,emoji):
        super().__init__(emoji=emoji)
        self.answer = answer_emoji
        self.bet = bet

    async def callback(self, interaction: discord.Interaction):
        earnings = self.bet
        a = interaction.followup
        if str(self.emoji) == self.answer:
            for item in self.view.children:
                item.disabled = True

            await interaction.response.edit_message(view= self.view)
            await a.send(f"Correct {self.emoji} was the imposter")
            await economy.add_bal(interaction.user,earnings)
        else:
            for item in self.view.children:
                item.disabled = True
            await interaction.response.edit_message(view= self.view)
            await a.send(f"Wrong {self.answer} was the imposter")
            await economy.add_bal(interaction.user,-earnings)

class TriviaButton(Button):
    def __init__(self,answer,label):
        super().__init__(label=label)
        self.answer = answer
    
    async def callback(self,interaction:discord.Interaction):
        a = interaction.followup
        if self.label == self.answer:
            for item in self.view.children:
                item.disabled= True
            await interaction.response.edit_message(view=self.view)
            await a.send(content="Correct, you got 100  <:doge_coin:865669474917154837> from that")
            await economy.add_bal(interaction.user,100)
            
        else:
            for item in self.view.children:
                item.disabled= True
            await interaction.response.edit_message(view=self.view)
            
            await a.send(f"You are Wrong, Correct answer was `{self.answer}`")

class RockPaperScissorButton(Button):
    def __init__(self,bet,game_func,comp,label,style,emoji):
        super().__init__(label=label,style=style,emoji=emoji)
        self.comp = comp
        self.game = game_func
        self.bet = bet
    
    async def callback(self, interaction: discord.Interaction):
        game = self.game(self.comp,self.label[0].lower())
        if game == True:
            await interaction.response.edit_message(content = f"{interaction.user.mention} Won!!!",view=None)
            await economy.add_bal(interaction.user,self.bet)
        elif game == "Tie":
            await interaction.response.edit_message(content = f"{interaction.user.mention} and {self.client.user.mention} Tied",view=None)
        elif not game:
            await interaction.response.edit_message(content = f"{interaction.user.mention} Lost !!",view=None)
            await economy.add_bal(interaction.user,-self.bet)

class CoinFlipButton(Button):
    def __init__(self,good,label,style):
        super().__init__(label=label,style=style)
        self.good = good
    
    async def callback(self, interaction: discord.Interaction):
        for child in self.view.children:
            child.disabled= True
        if self.label == self.good:
            await interaction.response.edit_message(content="Here your luck is good take these 100 <:doge_coin:865669474917154837>",view = self.view)
            await economy.add_bal(interaction.user,100)
        else:
            await interaction.response.edit_message(content="Your luck is bad can't give you any money :c ",view = self.view)

class RulesSelect(Select):
    def __init__(self,headings,data,options):
        super().__init__(options=options)
        self.headings = headings
        self.data = data
    
    async def callback(self,interaction:discord.Interaction):
        imdex = self.headings.index(self.values[0])
        data = self.data[imdex]
        a = interaction.followup
        for item in self.view.children:
            item.disabled = True
        
        await interaction.response.edit_message(view=self.view)
        await a.send(data)

class WillYouPressTheButton(Button):
    def __init__(self,attrs,label,style):
        super().__init__(label=label,style=style)
        self.url_ = attrs
        self.session = aiohttp.ClientSession()

    async def callback(self,interaction:discord.Interaction):
        r = await self.session.get(url= self.url_)
        r_text = await r.text()
        new_soup = BeautifulSoup(r_text,features='html.parser')
        notpressed = new_soup.find('span',{"class":"peopleDidntpress"})
        pressed = new_soup.find('span',{"class":"peoplePressed"})
        for item in self.view.children:
            item.disabled = True

        a = interaction.followup            
        await interaction.response.edit_message(view=self.view)
        await a.send(f"{pressed.text} People Pressed the button while {notpressed.text} People did not")

        await self.session.close()

class Connect4Button(Button):
    def __init__(self,board,con4,turn,gameover,label):
        super().__init__(label=label)
        self.board = board
        self.con4 = con4
        self.turn = turn
        self.gameover = gameover
    
    async def callback(self,interaction:discord.Interaction):
        self.turn = self.turn%2
        a = interaction.followup
        if self.turn == 0:
            for item in self.view.children:
                item.disabled = False
            await interaction.response.edit_message(view=self.view)
            # await interaction.response.defer(ephemeral= False)
            col = int(self.label) - 1 
            validLoc = await self.con4.isValidLocation(self.board,col)
            if validLoc:
                row = await self.con4.getNextOpenRow(self.board,col)
                await self.con4.dropPiece(self.board,row,col,"😍")
                win = await self.con4.winning(self.board,"😍")
                if win:
                    for item in self.view.children:
                        item.disabled = True
                    await interaction.message.edit(view=self.view)
                    await a.send("Player 1 Won")
                    self.gameover = True
            self.turn += 1

        self.turn = self.turn %2

        if self.turn == 1:
            col = random.randint(0,6)
            validLoc = await self.con4.isValidLocation(self.board,col)
            if validLoc:
                row = await self.con4.getNextOpenRow(self.board,col)
                await self.con4.dropPiece(self.board,row,col,"🙄")
                win = await self.con4.winning(self.board,"🙄")
                if win:
                    for item in self.view.children:
                        item.disabled = True
                    await interaction.response.edit_message(view=self.view)
                    await a.send("Player 2 Won")
                    self.gameover = True
            self.turn += 1
            

            
            for item in self.view.children:
                item.disabled = False
        await self.con4.editBoard(interaction.message,self.board,self.view)

class HelpSelect(Select):
    def __init__(self,headings,options):
        super().__init__(options = options)
        self.headings = headings
        # self.msg = msg
    
    async def callback(self, interaction: discord.Interaction):
        data = self.values[0].lower() # this is our slash command group
        
        list_of_commands = [i.name.strip() for i in client.walk_application_commands() if i.parent.__str__() == data if i.qualified_name.split(data)[1].strip() != '']
        embed = discord.Embed(title="HELP",colour=discord.Color.random())

        with open('./jsons/commands.json') as f:
            data = json.load(f)

        for j in list_of_commands:
            try:
                embed.add_field(name=j,value=data[j],inline=False)
            except KeyError:
                continue 
        

        for item in self.view.children:
            item.disabled = True
        await interaction.response.edit_message(embed=embed,view= self.view)