import aiohttp
import asyncio
import random
import json

 # https://opentdb.com/api.php?amount=10 url
session = aiohttp.ClientSession()



class OpenTDB:
    """lower and upper should be in the range of the amount of questions"""
    def __init__(self,url,lower,upper,json = None):
        self.url = url
        self.lower = lower
        self.upper = upper
        if self.upper < self.lower:
            raise ValueError("Upper limit is lower than lower limit")
        self.random_number = random.randint(self.lower-1,self.upper-1)
        self.json = json
        

    async def question(self):
        """Get a random question """
        r = await session.get(self.url, )
        self.json = await r.json()

        question = self.json['results'][self.random_number]['question']
        
        question_as_a_list = question.split("&quot;")
        new_ques = []
        new_new_ques = []
        
        for item in question_as_a_list:
            new_ques.append(item.split("&#039;"))
        
        for x in question_as_a_list:
            new_new_ques.append(x.split("&rsquo;"))

        
        
        if len(new_ques) == 1:
            question_as_a_list = "".join(question_as_a_list)
        
        elif len(new_new_ques) == 1:
            question_as_a_list = "".join(question_as_a_list)

        elif len(new_new_ques) != 1:
            question_as_a_list = ""
            for item in new_ques:
                question_as_a_list += "".join(item)

        else:
            question_as_a_list = ""
            for item in new_ques:
                question_as_a_list += "".join(item)
            

        


        return question_as_a_list
    
    async def answers(self):
        """Get the answers for the random question above, 
        the answers are in a list the first element is the 
        correct answer and the second element is the list of wrong options """
        correct_answers = self.json['results'][self.random_number]['correct_answer']
        incorrect_answers = self.json['results'][self.random_number]['incorrect_answers']

        return [correct_answers,incorrect_answers]
        
    async def category(self):
        """Gives Category to the question """
        category = self.json['results'][self.random_number]['category']
        return category

    async def difficulty(self):
        """Give difficulty of the question"""
        diff = self.json['results'][self.random_number]['difficulty']
        return diff
