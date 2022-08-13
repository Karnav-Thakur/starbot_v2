import discord
import numpy as np

class Connect4:
    def __init__(self,ROW,COL,p1:discord.Member,p2:discord.Member):
        self.p1 = p1
        self.p2 = p2
        self.ROW = ROW
        self.COL = COL

    async def createBoard(self):
        return np.zeros((self.ROW,self.COL),dtype=object)

    async def dropPiece(self,board,row,col,piece):
        board[row][col] = piece
        return board

    async def isValidLocation(self,board,col):
        return board[5][col] == 0

    async def getNextOpenRow(self,board,col):
        # ROW = 6
        for r in range(self.ROW):
            if board[r][col] == 0:
                return r
    
    async def printBoard(self,ctx:discord.ApplicationContext,board,view):
        embed = discord.Embed(title = f"{self.p1.name} is playing Connect4 with Bot",description=np.flip(board,0),color=discord.Color.random())
        msg = await ctx.respond(embed=embed,view=view)
        return await msg.original_message()
    
    async def editBoard(self,msg,board,view):
        embed = discord.Embed(title = f"{self.p1.name} is playing Connect4 with Bot",description=np.flip(board,0),color=discord.Color.random())
        msg = await msg.edit(embed=embed,view=view)

    async def winning(self,board,piece):
        
        for c in range(self.COL-3):
            for r in range(self.ROW):
                if board[r][c] == piece and board[r][c+1] == piece and board[r][c+2] == piece and board[r][c+3] == piece:
                    return True
        
        for c in range(self.COL):
            for r in range(self.ROW-3):
                if board[r][c] == piece and board[r+1][c] == piece and board[r+2][c] == piece and board[r+3][c] == piece:
                    return True
            
        for c in range(self.COL-3):
            for r in range(self.ROW-3):
                if board[r][c] == piece and board[r+1][c+1] == piece and board[r+2][c+2] == piece and board[r+3][c+3] == piece:
                    return True
    
        # Check negatively sloped diaganols
        for c in range(self.COL-3):
            for r in range(3, self.ROW):
                if board[r][c] == piece and board[r-1][c+1] == piece and board[r-2][c+2] == piece and board[r-3][c+3] == piece:
                    return True


    