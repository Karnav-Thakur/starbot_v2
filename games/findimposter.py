import random
from discord.ui import View
import json
from errors_views import views
import discord

async def main(interaction:discord.Interaction,bet):
    emojis = ["<:red:909887581733388388>","<:yellow:909887799451348992>","<:black:909888021812367380>","<:blue:909888257758728303>"]
    ans = random.choice(emojis)
    view = View()

    for emo in emojis:
        button = views.FindImposterButton(bet,ans,emo)
        view.add_item(button)
        

    embed1 = discord.Embed(title="Who's the imposter?", description="Find the imposter before the reactor breaks down", color=discord.Color.red())
    embed1.add_field(name="Red", value='<:red:909887581733388388>')
    embed1.add_field(name="Yellow", value='<:yellow:909887799451348992>')
    embed1.add_field(name="Black", value='<:black:909888021812367380>')
    embed1.add_field(name="Blue", value='<:blue:909888257758728303>')
    await interaction.response.send_message(embed=embed1,view=view)
    print(ans)