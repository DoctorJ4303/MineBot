import discord
from discord.ext import commands

class HelpCommands(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.group(invoke_without_command=True, aliases=['?'])
    async def help(self, ctx):
        embed = discord.Embed(title='Help', description='Use .help <command> for more info on a command', color=ctx.author.color)
        embed.add_field(name='General', value='start, cancel, say, voted')
        embed.add_field(name='World', value='world, savedworlds,\nmap, regen,\nproperties')
        await ctx.send(embed=embed)

    # General

    #Start
    @help.command(aliases=['votestart'])
    async def start(self, ctx):
        embed = discord.Embed(title='Start', description=('Vote to start the server'), color=ctx.author.color)
        embed.add_field(name='Aliases', value='votestart')
        await ctx.send(embed=embed)
    #Cancel
    @help.command(aliases=['cancelvote'])
    async def cancel(self, ctx):
        embed = discord.Embed(title='Cancel', description=('Removes your vote to start the server'), color=ctx.author.color)
        embed.add_field(name='Aliases', value='cancelvote')
        await ctx.send(embed=embed)
    #Say
    @help.command()
    async def say(self, ctx):
        embed = discord.Embed(title='Say', description=('Says a message in minecraft chat'), color=ctx.author.color)
        await ctx.send(embed=embed)
    #Voted
    @help.command(aliases=['votedplayers'])
    async def voted(self, ctx):
        embed = discord.Embed(title='Voted', description=('Gets a list of all voted players'), color=ctx.author.color)
        embed.add_field(name='Aliases', value='votedplayers')
        await ctx.send(embed=embed)

    # World

    #Map
    @help.command()
    async def map(self, ctx):
        embed = discord.Embed(title='Map', description=('Downloads a map from https://www.minecraftmaps.com/'), color=ctx.author.color)
        await ctx.send(embed=embed)
    #List Worlds
    @help.command(aliases=['savedworlds','worlds'])
    async def saved_worlds(self, ctx):
        embed = discord.Embed(title='Worlds', description=('Gets a list of all saved worlds'), color=ctx.author.color)
        embed.add_field(name='Aliases', value='savedworlds, worlds')
        await ctx.send(embed=embed)
    #World
    @help.command()
    async def world(self, ctx):
        embed = discord.Embed(title='World', description=('Able to change world from saves'), color=ctx.author.color)
        await ctx.send(embed=embed)
    #Generate
    @help.command()
    async def generate(self, ctx):
        embed = discord.Embed(title='Regenerate', description=('Regenerate a default minecraft world'), color=ctx.author.color)
        embed.add_field(name='Customizability', value='Custom seed, wait 5 seconds if not wanted\nCustom world name\nMinecraft version, 1.8.9-1.16.5')
        await ctx.send(embed=embed)
    #Properties
    @help.command()
    async def properties(self, ctx):
        embed = discord.Embed(title='Properties', description=('Change default properties of a Minecraft server'), color=ctx.author.color)
        embed.add_field(name='Customizable Properties', value='Default gamemode\nDefault difficulty\nAllowed pvp\nHardcore\nmotd (message of the day)')
        await ctx.send(embed=embed)

def setup(client):
    client.add_cog(HelpCommands(client))