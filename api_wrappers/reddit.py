import aiohttp
import asyncio


class Reddit:
    
    def __init__(self,url,subreddit,json = None):
        self.url = url 
        self.subreedit = subreddit
        self.json = json
    
    async def link(self):
        if self.subreddit == None:
            self.subreedit = "memes"

        async with aiohttp.ClientSession() as session:
            async with session.get(self.url,headers = {'Connection': 'keep-alive'}) as r:
                self.json = await r.json(content_type=None)
                if r.status == 200:
                    try:
                        link = self.json[0]['data']['children'][0]['data']['preview']['images'][0]['source']['url']
                    except KeyError:
                        return
                    link = link.replace("amp;", "")
                    return link
                else:
                    await self.link()
    
    async def title(self):
        title = self.json[0]["data"]['children'][0]["data"]["title"]
        return title

    async def subreddit(self):
        sub = self.json[0]['data']['children'][0]['data']['subreddit']
        return sub
    
    async def is_nsfw(self):
        nsfw = self.json[0]['data']['children'][0]['data']['over_18']
        return nsfw

    async def author(self):
        try:
            author = self.json[0]['data']['children'][0]['data']['author']
        except KeyError:
            await self.author()
        return author

