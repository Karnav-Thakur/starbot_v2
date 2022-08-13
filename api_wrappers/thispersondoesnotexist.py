from io import BytesIO
import aiohttp
import asyncio
from bs4 import BeautifulSoup


class ThisPersonDoesNotExist:
    def __init__(self,url):
        self.url = url
    
    async def link(self):
        session = aiohttp.ClientSession()
        r = await session.get(self.url)
        r_t = await r.text()
        soup = BeautifulSoup(r_t,features='html.parser')
        link = soup.find('img', {'id':'avatar'})
        await session.close()
        return link


