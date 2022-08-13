import random
import asyncio
import discord
from discord.ui import Button,View
from discord.enums import ButtonStyle
import json
from errors_views import views  

class Fight:
    def __init__(self,player1: discord.Member,player2: discord.Member):
        self.player1 = player1
        self.player2 = player2
        self.health = {self.player1:100,self.player2: 100}
    
    async def take_damage(self,damage:int,player):
        if damage < self.health[player]:
            self.health[player] -= damage
        else:
            self.health[player] = 0
        
    async def win_or_not(self,player):
        if self.health[player] == 0:
            return True
        else: 
            return False

    @staticmethod
    async def random_damage():
        return random.randint(1,30)

    async def fight(self,ctx): 
        # damage = random.randint(1,30)
        turn = {"turn":0}
        with open('./jsons/stuff.json',encoding="utf-8") as f:
            data = json.load(f)
        win = {"winning": False}
            
        punch = views.FightButton(self.player1,self.player2,self.health,turn['turn'],win["winning"],style=ButtonStyle.blurple,label="Punch")
        view = View()
        view.add_item(punch)
        await ctx.send(f"It's {self.player1.mention}'s turn",view = view)