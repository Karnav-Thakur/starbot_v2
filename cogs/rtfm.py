import io
import os
import re
import zlib
import logging

import aiohttp
import discord
from stars import  sv_id
from discord.ext import commands



class SphinxObjectFileReader:
   
    BUFSIZE = 16 * 1024

    def __init__(self, buffer):
        self.stream = io.BytesIO(buffer)

    def readline(self):
        return self.stream.readline().decode("utf-8")

    def skipline(self):
        self.stream.readline()

    def read_compressed_chunks(self):
        decompressor = zlib.decompressobj()
        while True:
            chunk = self.stream.read(self.BUFSIZE)
            if len(chunk) == 0:
                break
            yield decompressor.decompress(chunk)
        yield decompressor.flush()

    def read_compressed_lines(self):
        buf = b""
        for chunk in self.read_compressed_chunks():
            buf += chunk
            pos = buf.find(b"\n")
            while pos != -1:
                yield buf[:pos].decode("utf-8")
                buf = buf[pos + 1 :]
                pos = buf.find(b"\n")


class Docs(commands.Cog, name="Documentation"):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

        self.page_types = {
            "discord.py": "https://discordpy.readthedocs.io/en/latest",
            "levelling": "https://discord-ext-levelling.readthedocs.io/en/latest/",
            "pycord": "https://docs.pycord.dev/en/master/"
        }

    def finder(self, text, collection, *, key=None, lazy=True):
        suggestions = []
        text = str(text)
        pat = ".*?".join(map(re.escape, text))
        regex = re.compile(pat, flags=re.IGNORECASE)
        for item in collection:
            to_search = key(item) if key else item
            r = regex.search(to_search)
            if r:
                suggestions.append((len(r.group()), r.start(), item))

        def sort_key(tup):
            if key:
                return tup[0], tup[1], key(tup[2])
            return tup

        if lazy:
            return (z for _, _, z in sorted(suggestions, key=sort_key))
        else:
            return [z for _, _, z in sorted(suggestions, key=sort_key)]

    def parse_object_inv(self, stream, url):
    
        result = {}

     
        inv_version = stream.readline().rstrip()

        if inv_version != "# Sphinx inventory version 2":
            raise RuntimeError("Invalid objects.inv file version.")

        stream.readline().rstrip()[11:]
        stream.readline().rstrip()[11:]


        line = stream.readline()
        if "zlib" not in line:
            raise RuntimeError("Invalid objects.inv file, not z-lib compatible.")

        # This code mostly comes from the Sphinx repository.
        entry_regex = re.compile(r"(?x)(.+?)\s+(\S*:\S*)\s+(-?\d+)\s+(\S+)\s+(.*)")
        for line in stream.read_compressed_lines():
            match = entry_regex.match(line.rstrip())
            if not match:
                continue

            name, directive, prio, location, dispname = match.groups()
            domain, _, subdirective = directive.partition(":")
            if directive == "py:module" and name in result:

                continue

            if directive == "std:doc":
                subdirective = "label"

            if location.endswith("$"):
                location = location[:-1] + name

            key = name if dispname == "-" else dispname
            prefix = f"{subdirective}:" if domain == "std" else ""

            result[f"{prefix}{key}"] = os.path.join(url, location)

        return result

    async def build_rtfm_lookup_table(self, page_types):
        cache = {}
        for key, page in page_types.items():
            async with aiohttp.ClientSession() as session:
                async with session.get(page + "/objects.inv") as resp:
                    if resp.status != 200:
                        raise RuntimeError(
                            "Cannot build rtfm lookup table, try again later."
                        )

                    stream = SphinxObjectFileReader(await resp.read())
                    cache[key] = self.parse_object_inv(stream, page)

        self._rtfm_cache = cache

    async def do_rtfm(self, interaction:discord.Interaction, key, obj):
        page_types = self.page_types
        await interaction.response.defer()

        if obj is None:
            await interaction.response.send_message(page_types[key])
            return

        if not hasattr(self, "_rtfm_cache"):
            
            # await ctx.trigger_typing()
            await self.build_rtfm_lookup_table(page_types)

        cache = list(self._rtfm_cache[key].items())

        self.matches = self.finder(obj, cache, key=lambda t: t[0], lazy=False)[:8]

        e = discord.Embed(colour=0x05FFF0)
        
        e.set_footer(text=f'Requested By {interaction.user}', icon_url=f'{interaction.user.avatar.url}')
        # e.set_thumbnail(url="https://i.imgur.com/hTC4xoX.gif")
        a = interaction.followup
        if len(self.matches) == 0:
        
            return await a.send("Could not find anything. Sorry.")

        e.description = "\n".join(f"[`{key}`]({url})" for key, url in self.matches)
        await a.send(embed=e)

    @discord.slash_command(
        name="rtfm",
        description="Gives you a documentation link for a d.py entity.",
        guild_ids = sv_id,
    )
    @commands.is_owner()
    async def rtfm(self, interaction:discord.Interaction, key: str = None, *, query: str = None):
        if not key or key.lower() not in self.page_types.keys():
            query = query or ""
            key = key or ""

            query = key + query
            key = "discord.py"

        if query is not None:
            if query.lower() == "rtfm":
                await interaction.response.send_message(
                    embed=discord.Embed.from_dict(
                        {
                            "title": "Read The Fucking Manual",
                            "color": "0x00FC7E",
                            "description": "You expect me to know?",
                            "footer": {"text": "Imagine including easter eggs"},
                        }
                    )
                )

        await self.do_rtfm(interaction, key, query)

def setup(client):
    client.add_cog(Docs(client))