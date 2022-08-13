import random
from discord.ui import View
import json
import discord
from errors_views import views

def shuffle(iteration,length:int):
    for index,elem in enumerate(iteration):
        randomPos = random.randint(0,length-1)
        iteration[index],iteration[randomPos] =iteration[randomPos],iteration[index]
    return iteration 



async def main(interaction:discord.Interaction):

    with open('./jsons/stuff.json',encoding='utf-8') as f:
        data = json.load(f)
    
    lists = data['order']
    some = random.choice(lists).title()
    some_list = some.split(" ")

    correct_order = some_list[:]
    new_order = shuffle(some_list,len(some_list))
    user_inp = []
    view = View()
    for item in new_order:
        button = views.OrderButton(item,correct_order,user_inp)
        view.add_item(button)
    
    await interaction.response.send_message("Rearrange the sentence (yeah welcome back to class 10)",view=view)
