import random
import requests
from bs4 import BeautifulSoup
from api_wrappers import giphy

with open('./tokens/giphy_api_key.txt') as f:
    api_key = f.read()

gifs = giphy.Giphy(api_key,'hamburger')
l = gifs.links()

rand = random.choice(l)
# print(rand)

r = requests.get(rand)

soup = BeautifulSoup(r.text,features='html.parser')
# print(soup)

s = soup.find_all('meta')
print(s[10].attrs['content'])