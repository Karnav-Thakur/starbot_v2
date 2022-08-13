import discord
from discord.ext import commands
import json
from stars import client, sv_id
from discord import SelectOption
from discord.ui.view import View
from errors_views import views
class DetailedHelp(commands.Cog):
    def __init__(self,client):
        self.client= client

    helps = discord.SlashCommandGroup('helps', "Get help on what you want to do with the bot",sv_id)

    @helps.command(guild_ids = sv_id)
    async def help(self,ctx:discord.ApplicationContext):
        headings = []
        for i in client.walk_application_commands():
            headings.append(i.parent.__str__())
        
        headings = list(set(headings))
        headings.remove('None')

        select = []
        for head in headings:
            slct = SelectOption(label=head.upper())
            select.append(slct)
        
        somt = views.HelpSelect(headings=headings,options=select)
        view = View()
        view.add_item(somt)

        embed = discord.Embed(title='Help Command',description='Choose What you need help with',colour=discord.Color.random())
        
        await ctx.respond(embed=embed,view = view)

        


def setup(client):
    client.add_cog(DetailedHelp(client))