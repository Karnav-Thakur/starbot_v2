import random
from discord.ext import commands
from discord.ui import View
from errors_views import views
import discord



async def main(interaction:discord.Interaction,client:commands.Bot):
    emoji_list = ['😄', '😂', '🤣', '😞', '😭', '🙂', '🤨', '😅', '🥺', '🤓']
    random_emoji = random.choice(emoji_list)
    view = View()
    for emoji in emoji_list:
        button = views.EmojiButton(emoji,random_emoji)
        view.add_item(button)
    
    await interaction.response.send_message("Select the correct emoji",view= view)
