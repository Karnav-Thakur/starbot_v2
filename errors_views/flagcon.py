import discord
from discord.ext import commands

class PollFlag(commands.FlagConverter):
    opt1: str
    opt2: str

class EmbedFlags(commands.FlagConverter):
    title: str
    description:str

class SimilarFlags(commands.FlagConverter):
    str1: str
    str2: str