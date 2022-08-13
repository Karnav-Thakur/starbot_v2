import random
from cogs import economy
from stars import client
import discord

async def a_hangman(ctx):
    peta = await economy.show_pet(ctx.author)
    lvl = peta[6]

    words = ["afforest","aftermath","becalm","blithesome","broadsheet","buffoonish","caprice","capricious","causerie","chivalrous","congratulatory","dapper","debonaire","emblazon","eudaemonia","extremum","exultant","featherbrained","felicity","gabble","gallant","gilt","gleeful","halcyon"]
    ran_word = random.choice(words)
    ran_word_list = list(ran_word)
    ran_letter = random.choice(ran_word)
    earnings = random.randint(1,200)


    temp = ""

    for letter in ran_word_list:
        if letter == ran_letter:
            temp += "_"
        
        else:
            temp += letter
        
    # return f"{temp} {ran_letter} {ran_word}"
    embed = discord.Embed(title = "You are playing Hangman with your pet",description = f"Complete the word {temp}",colour = discord.Color.random())
    await ctx.send(embed = embed)

    def check(message):
        return message.author == ctx.message.author
    
    guess = await client.wait_for("message",check = check)
    guess = guess.content.lower()

    if guess == ran_letter or guess == ran_word:
        await ctx.send(f"Correct the missing letter was `{ran_word}` and the word is `{ran_letter}`")
        await economy.add_bal(ctx.author,earnings*lvl)
        await economy.update_stats(ctx.author,"attack",random.randint(1,20))
        await economy.update_stats(ctx.author,"defence",random.randint(1,20))
        await economy.update_stats(ctx.author,"exp",random.randint(1,20))
        await ctx.send(f"Your Pet's stats has been increased")
    else:
        await ctx.send(f"You are wrong, the correct letter was {ran_word}, the word was {ran_letter}")

async def a_rock_paper_scissor(ctx):
    peta = await economy.show_pet(ctx.author)
    lvl = peta[6]
    earnings = random.randint(1,200)
    embed = discord.Embed(title = "You are playing Rock Paper Scissors with your pet",description = f"{ctx.author.name} is choosing (r/p/s)",colour = discord.Color.random())
    await ctx.send(embed = embed)
    def check(message):
        return message.author == ctx.message.author
    you = await client.wait_for('message',check = check)
    you = you.content.lower()
    comp_number = random.randint(1,3)
    if comp_number == 1:
        comp = 'r'
    elif comp_number == 2:
        comp = 'p'
    elif comp_number == 3:
        comp = 's'

    if comp == you:
        await ctx.send("You Tied")
              
    elif comp == "r":
        if you == "p":
            await ctx.send("You won")
            await economy.add_bal(ctx.author,earnings*lvl)
            await economy.update_stats(ctx.author,"attack",random.randint(1,20))
            await economy.update_stats(ctx.author,"defence",random.randint(1,20))
            await economy.update_stats(ctx.author,"exp",random.randint(1,20))
            await ctx.send(f"Your Pet's stats has been increased")
        elif you == "s":
            await ctx.send("You lost")

    elif comp == "p":
        if you == "s":
            await ctx.send("You won")
            await economy.add_bal(ctx.author,earnings*lvl)
            await economy.update_stats(ctx.author,"attack",random.randint(1,20))
            await economy.update_stats(ctx.author,"defence",random.randint(1,20))
            await economy.update_stats(ctx.author,"exp",random.randint(1,20))
            await ctx.send(f"Your Pet's stats has been increased")
        elif you == "r":
            await ctx.send("You lost")
    
    elif comp == "s":
        if you == "r":
            await ctx.send("You won")
            await economy.add_bal(ctx.author,earnings*lvl)
            await economy.update_stats(ctx.author,"attack",random.randint(1,20))
            await economy.update_stats(ctx.author,"defence",random.randint(1,20))
            await economy.update_stats(ctx.author,"exp",random.randint(1,20))
            await ctx.send(f"Your Pet's stats has been increased")
        elif you == "p":
            await ctx.send("You lost")

async def a_finish(ctx):
    peta = await economy.show_pet(ctx.author)
    sentence_list = ["The elevator to success is out of order You’ll have to use the stairs, one step at a time","People often say that motivation doesn’t last Well, neither does bathing – that’s why we recommend it daily" ,"I always wanted to be somebody, but now I realise I should have been more specific" ,"I am so clever that sometimes I don’t understand a single word of what I am saying." ,"People say nothing is impossible, but I do nothing every day" ,"Life is like a sewer… what you get out of it depends on what you put into it.","You can’t have everything Where would you put it","Work until your bank account looks like a phone number" ,"Change is not a four letter word… but often your reaction to it is","If you think you are too small to make a difference  try sleeping with a mosquito"]
    earnings = random.randint(1,200)
    random_sentence = random.choice(sentence_list)
    lvl = peta[6]

    old_data = random_sentence.split(" ")
    data = random_sentence.split(" ")
    word = random.choice(data)

    data.remove(word)

    a_str = " "

    for x in old_data:
        if x == word:
            a_str += "\_ "*len(word)
        else:
            a_str += f"{x} "
    
    # await ctx.send(a_str)
    # return [word ,a_str,random_sentence]

    embed = discord.Embed(title = "You are playing Finish the Sentence with your pet",description = a_str,colour = discord.Color.random())
    await ctx.send(embed = embed)
    def check(message):
        return message.author == ctx.message.author
    
    you = await client.wait_for('message', check = check)
    
    if word.lower() == you.content.lower() or a_str.lower()== you.content.lower() or random_sentence.lower() == you.content.lower():
        await ctx.send(f"Correct the missing word was {word}, and the quote was `{random_sentence}`")
        await economy.add_bal(ctx.author,earnings*lvl)
        await economy.update_stats(ctx.author,"attack",random.randint(1,20))
        await economy.update_stats(ctx.author,"defence",random.randint(1,20))
        await economy.update_stats(ctx.author,"exp",random.randint(1,20))
        await ctx.send(f"Your Pet's stats has been increased")
    else:
        await ctx.send(f"That wasn't correct, the correct word was {word}")

async def a_dragon(ctx):
    embed = discord.Embed(title = "You are fighting A dragon with your pet",description = f"{ctx.author.name} good luck",colour = discord.Color.random())
    await ctx.send(embed = embed)

    random_game_chance = random.randint(1,3)

    if random_game_chance == 1:
        await a_hangman(ctx)
    elif random_game_chance == 2:
        await a_rock_paper_scissor(ctx)
    elif random_game_chance == 3:
        await a_finish(ctx)