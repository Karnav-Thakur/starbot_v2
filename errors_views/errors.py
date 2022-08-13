import discord
from discord.ext import commands

class NegativeError(commands.CommandError):
    pass
class NoPetError(commands.CommandError):
    pass
class PremiumError(commands.CommandError):
    pass