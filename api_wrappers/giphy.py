import asyncio
import requests
import random

class Giphy:

    def get_request(url_):
        r = requests.get(url_)
        r_ = r.json()
        return r_
        
    def __init__(self,api_key,query,limit=5,offset=0):
        self.key = api_key
        self.query = query
        self.limit = limit
        self.offset = offset
        url = f'https://api.giphy.com/v1/gifs/search?api_key={self.key}&q={self.query}&limit={self.limit}&offset={self.offset}&rating=g&lang=en'
        self.json = Giphy.get_request(url)
        
    
    def links(self):
        links = []
        for item in self.json["data"]:
            links.append(item['url'])
        return links
    
    
    
        