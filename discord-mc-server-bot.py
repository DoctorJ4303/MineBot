scriptVersion = '1.2.7'
# Thanks to nickbrooking for the mc-server code
import asyncio
import datetime
import io
import os
import random
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
import zipfile

import discord
import html2text
import requests
from discord.ext import commands, tasks
from discord.utils import get
from mcstatus import MinecraftServer
from bs4 import BeautifulSoup

#############
# Variables #
#############

ramAlloc = '4092'
TOKEN = 'ODI5MDA2OTcyNTA1NDIzOTcy.YGx26A.Fn1gk13-TT91_83v15wyPL5A8b4'
worldName = str(open('versions.txt','rt').readlines()[0][0:-1])
version = str(open('versions.txt','rt').readlines()[1][0:-1])
serverDir = 'versions\\' + str(open('versions.txt','rt').readlines()[1][0:-1]) + '.jar'
versions = ['1.16','1.15','1.14','1.13','1.12','1.11','1.10','1.9','1.8']
fullVersions = ['1.16.5','1.15.2','1.14.4','1.13.2','1.12.2','1.11.2','1.10.2','1.9.4','1.8.9']
minPlayers = 1
votedPlayers = []
server = ''
serverStopped = True
shuttingDown = False
os.system('title ' + '[d-s-bot - ' + scriptVersion + ']')
print('hi')
client = commands.Bot(command_prefix='mc.')
client.run('ODI5MDA2OTcyNTA1NDIzOTcy.YGx26A.Fn1gk13-TT91_83v15wyPL5A8b4')
@client.command()
async def test(ctx):
    ctx.send('pls')
#client.remove_command('help')
#client.load_extension('cogs.help-commands')

##################
# Main Functions #
##################

#Message
def m(message):
    print('[' + datetime.datetime.now().strftime('%H:%M:%S') + '] [d-s-bot - ' + scriptVersion + ']: ' + message)
#Command
def c(command):
    global server
    server.stdin.write((command + '\n').encode())
    server.stdin.flush()
#Remove Fancy
def removeFancy(s):
    listOfFancy = ['`','*','_']
    for fancy in listOfFancy:
        i = 0
        while i < len(s):
            if s[i:i+1] == fancy:
                s = s[0:i] + '\\' + s[i:len(s)]
                i += 2
            else:
                i += 1
    return s
#Start Server
async def startServer():
    global server
    global serverStopped
    
    m('Starting server...')
    server = subprocess.Popen(f'java -Xmx{ramAlloc}m -Xms{ramAlloc}m -jar '+ serverDir + ' nogui', stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    serverStopped = False
    b = threading.Thread(name='backround', target=printLog)
    b.start()
#Stop Server
async def stopServer():
    global server
    global serverStopped

    m('Server stopping...')
    c('stop')
    serverStopped = True
    await asyncio.sleep(10)
    server.kill()
#Zipdir
def zipdir(path, ziph):
    for root, dirs, files in os.walk(worldName):
        for file in files:
            ziph.write(os.path.join(root, file))
def download_url(url, save_path, chunk_size=128):
    r = requests.get(url, stream=True)
    with open(save_path, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=chunk_size):
            fd.write(chunk)
#Download World
async def downloadWorld(ctx, arg):
    global worldName
    global serverDir
    global version
    try:
        r = requests.get(str(arg) + '/download')
        z = zipfile.ZipFile(io.BytesIO(r.content))
        worldName = getWorld(z)
        for name in z.namelist():
            if not name.endswith(r'.txt') and not name.endswith(r'.zip'):
                z.extract(name)  

        propFileLines = open('server.properties','rt').readlines()           
        for i in range(len(propFileLines)):
            if 'level-name=' in propFileLines[i]:
                propFileLines[i] = f'level-name={worldName}\n'
        open('server.properties', 'wt').writelines(propFileLines)
                
        vFileContent = open('versions.txt','rt').readlines()
        open('versions.txt','w').close()
        vFileContent[0] = worldName  + '\n'      
        open('versions.txt', 'wt').writelines(vFileContent)
                            
        await ctx.send('Done!')
    except:
        await ctx.send('There was an error in downloading the world, try again in a few minutes')
#Get World
def getWorld(z):
    for name in z.namelist():
        if 'level.dat_old' in name:
            return name[0:-14]
#Get Version
def getVersion(arg):
    global serverDir
    global worldName
    global version
    htmlText = html2text.html2text(str(requests.get(str(arg)).text)).lower()
    html2text.HTML2Text().ignore_links = True
    vIndex = htmlText.rfind('mc version:') + 11
    for i in range(len(versions)):
        if versions[i] in htmlText[vIndex:vIndex+10]:
            version = fullVersions[i]

    vFileContent = open('versions.txt','r').readlines()
    vFileContent[1] = version + '\n'
    open('versions.txt','w').writelines(vFileContent)
def getVotedPlayers():
    global votedPlayers
    players = []
    for player in votedPlayers:
        if player.nick == None:
            players.append(removeFancy(str(player))[0:-5] + '\n')
        else:
            players.append(removeFancy(player.nick) + '\n')
    return (''.join(players) + str(len(votedPlayers)) + '/' + str(minPlayers))
#Save World
def saveWorld(name: str):
    zipf = zipfile.ZipFile('saves/' + name + '_' + version + '_' + datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + '.zip', 'w')
    zipdir(name + '/', zipf)
    zipf.close()
    with open('versions.txt', 'at') as vFile:
        vFile.write(name + '=' + version + '\n')

##########
# Events #
##########

#On Ready
@client.event
async def on_ready():
    checkPlayers.start()
    m("Bot is up!")
#Command Error
@client.event
async def on_command_error(ctx, error): 
    print(error)
    if isinstance(error, commands.CommandNotFound):
        await ctx.send('Invalid command')

############
# Commands #
############

# Admin Commands

#Op
@client.command()
@commands.has_permissions(manage_guild=True)
async def op(ctx, arg):
    if not serverStopped:
        c('op ' + str(arg))
        await ctx.send(str(arg) + ' has been opped')
    else:
        await ctx.send('Server is not up')
@op.error
async def op_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Missing a player')
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send('You do not have a high enough rank!')
#Stop
@client.command(aliases=['stop'])
@commands.has_permissions(manage_guild=True)
async def forcestop(ctx):
        global votedPlayers
        if not serverStopped:
            await stopServer()
            votedPlayers.clear()
            await ctx.send('Server has stopped')
        else:
            await ctx.send('The server is not up')
#Set Minimum Players
@client.command(aliases=['setminplayers','setmin'])
@commands.has_permissions(manage_guild=True)
async def set_min(ctx, arg):
    global minPlayers
    try:
        minPlayers = int(arg)
        await ctx.send('Minimum players has been set to '+str(arg))
    except ValueError:
        await ctx.send('Has to be a number')
@set_min.error
async def set_min_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Needs to be a number!')
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send('You do not have a high enough rank!')
# Server Commands

#Start
@client.command(aliases=['votestart'])
async def start(ctx):
    global scriptVersion
    global serverStopped
    global votedPlayers
    if serverStopped:
        if ctx.author in votedPlayers:
            await ctx.send('You have already voted!')
        else:
            votedPlayers.append(ctx.author)
            embed = discord.Embed(title='Voted Players', description=getVotedPlayers(), color=ctx.author.color)
            if not len(votedPlayers) >= minPlayers:
                await ctx.send(embed=embed)
    elif not serverStopped:
        ctx.send('Server is already up.')

    if serverStopped and len(votedPlayers) >= minPlayers:
        embed = discord.Embed(title='Starting Server...', description='', color=ctx.author.color)
        embed.add_field(name = 'World', value = worldName)
        embed.add_field(name = 'Version', value = version)
        await ctx.send(embed=embed)
        await startServer()
        serverStopped = False
#Cancel
@client.command(aliases=['cancelvote'])
async def cancel(ctx):
    global votedPlayers
    players = []
    try:
        votedPlayers.remove(ctx.message.author)
        players = []
        for player in votedPlayers:
            if player.nick == None:
                players.append(removeFancy(str(player))[0:-5] + '\n')
            else:
                players.append(removeFancy(player.nick) + '\n')
        description = (''.join(players) + str(len(votedPlayers)) + '/' + str(minPlayers))
        embed = discord.Embed(title='Voted Players', description=description, color=ctx.author.color)
        if len(votedPlayers) >= 1:
            await ctx.send(embed=embed)
    except ValueError:
        await ctx.send('You have not voted yet.')
#Say
@client.command()
async def say(ctx, *, arg):
    if not serverStopped:
        c('tellraw @a {\"text\":\"<' + str(ctx.author.nick) + '> ' + str(arg) + '\"}' if not ctx.author.nick == None 
                else 'tellraw @a {\"text\":\"<' + str(ctx.author)[0:-5] + '> ' + str(arg) + '\"}')
    else:
        await ctx.send('Server is not up.')
#Voted
@client.command(aliases=['votedplayers'])
async def voted(ctx):
    players = []
    if not len(votedPlayers) == 0:
        for player in votedPlayers:
            if player.nick == None:
                players.append(str(player) + '\n')
            else:
                players.append(str(player.nick) + '\n')
            description = (''.join(players) + '\n' + str(len(votedPlayers)) + '/' + str(int((minPlayers))))
            embed = discord.Embed(title='Voted Players', description=description, color=ctx.author.color)
            await ctx.send(embed=embed)
    else:
        await ctx.send('Nobody has voted yet')

# World Commands 

#Map
@client.command()
async def map(ctx, arg):
    if 'https://www.minecraftmaps.com/' in str(arg):
        yesAnswers = ['yes','ye','yea','yeah','yah','ya','y']

        await ctx.send('Would you like to save ' + worldName + '?')
        msg = await client.wait_for('message', check=lambda message: message.author == ctx.author)
        getVersion(arg)
        if msg.content.lower() in yesAnswers:
            await ctx.send('Saving...')
            saveWorld(worldName)
        try:
            shutil.rmtree(fr'{worldName}/')
        except:
            m('World file not found')
        await downloadWorld(ctx, arg)
    else:
        await ctx.send('That is not from minecraftmaps!')
@map.error
async def map_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Missing a link from minecraftmaps.com!')
#Saved Worlds
@client.command(aliases=['savedworlds','worlds'])
async def saved_worlds(ctx):
    global serverDir
    global version
    savedWorlds = []
    savedVersions = []
    e = discord.Embed(title='Saved Worlds', description='', color=ctx.author.color)
    vFileContent = open('versions.txt', 'r').readlines()
    for i in range(len(vFileContent)):
        if vFileContent[i] == 'Worlds:\n':
            for j in range(i+1, len(vFileContent)):
                savedWorlds.append(vFileContent[j].split('=')[0] + '\n')
                savedVersions.append(vFileContent[j].split('=')[1])
    e.add_field(name='World Name', value=''.join(savedWorlds))
    e.add_field(name='Version', value=''.join(savedVersions))
    await ctx.send(embed=e)
#Bot Version
@client.command(aliases=['botVersion','scriptversion','scriptVersion'])
async def botversion(ctx):
    await ctx.send('Minecraft Server Bot is on version ' + scriptVersion)
#World        
@client.command()
async def world(ctx, *, args):
#Take content out of file
    global worldName
    global version
    fileName = open(r"versions.txt", "r")
    propFile = open('server.properties','rt').readlines()
    bool1 = False
    zipName = ""
    content = fileName.readlines()
    length = len(content)
    fileName.close()
    worldInput = str(''.join(args))
    for count1 in range(length):
        #finding barrier
        if content[count1] == "------\n":
            if content[count1 + 1] == "Versions:\n":
                pass
            #Finding world area
            if content[count1 + 1] == "Worlds:\n":
                worldIndex = content.index("Worlds:\n")
                #Getting world and version
                for inCount in range(worldIndex,length):
                    for inCount1 in range(len(content[inCount])):
                        newContent = content[inCount]
                        if newContent[inCount1] == "=":
                            lengthContent = len(newContent)
                            world = newContent[0:inCount1]
                            if worldInput.lower() in world.lower():
                                bool1 = True
                                version = newContent[inCount1+1:lengthContent-1]
                                worldName1 = content[0][:-1]
                                versionName1 = content[1][:-1]
                                break
                    if bool1:
                        break
                            
    #Changing info in file to new info
    if bool1 == True:
        content[0] = world + '\n'
        content[1] = version + '\n'
        yesAnswers = ['yes','ye','yea','yeah','yah','ya','y']
        await ctx.send('Would you like to save ' + worldName1 + '?')
        msg = await client.wait_for('message', check=lambda message: message.author == ctx.author)
        if msg.content.lower() in yesAnswers:
            await ctx.send('Saving...')
            content.append(worldName1 + '=' + versionName1 + '\n')
            saveWorld(worldName1)
        
        try:
            shutil.rmtree(fr'{worldName1}/')
        except:
            m('World file not found')
        content.remove(world + '=' + version + '\n')

        savesList = os.listdir(r"./saves")
        for i in range(len(savesList)):
            if world == savesList[i].split('_')[0]:
                zipName = savesList[i]
                break

        try:
            z = zipfile.ZipFile("saves/"+zipName)
            for name in z.namelist():
                z.extract(name)
            z.close()
            os.remove("./saves/"+zipName)
        except:
            m('Zip file not found')

        for i in range(len(propFile)):
            if 'level-name=' in propFile[i]:
                propFile[i] = 'level-name=' + world + '\n'
        
        worldName = world
        open('server.properties','wt').writelines(propFile)
        open('versions.txt','wt').writelines(content)
        await ctx.send('Success!')
    else:
        await ctx.send("There is no world with that name")
@world.error
async def world_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Missing world name')
#Generate
@client.command()
async def generate(ctx):
    global serverDir
    global version
    global worldName
    global server
    if serverStopped:
        yesAnswers = ['yes','ye','yea','yeah','yah','ya','y']
        worldTypes = ['largeBiomes', 'default', 'amplified', 'flat']
        foundVersion = False
        typeFound = False
        await ctx.send('Would you like to save ' + worldName + '?')
        answer = await client.wait_for('message', check=lambda message: message.author == ctx.author)
        if answer.content.lower() in yesAnswers:
            await ctx.send('Saving...')
            saveWorld(worldName)
        try:
            shutil.rmtree(fr'{worldName}/')
        except:
            m('World file not found')

        propFile = open('server.properties', 'rt').readlines()
        verFile = open('versions.txt', 'rt').readlines()

        await ctx.send('What is the name of the new world?')
        levelName = await client.wait_for('message', check=lambda message: message.author == ctx.author)
        for i in range(len(propFile)):
            if 'level-name=' in propFile[i]:
                propFile[i] = 'level-name=' + levelName.content + '\n'

        await ctx.send('What is the version of ' + levelName.content + ' (1.8.9-1.16.5)')
        worldVersion = await client.wait_for('message', check=lambda message: message.author == ctx.author)
        for v in versions:
            if v in worldVersion.content:
                for jar in os.listdir('./versions'):
                    if v in str(jar):
                        foundVersion = True
                        serverDir = 'versions/' + str(jar)
                        version = str(jar)[:-4]
                        break
        if not foundVersion:
            await ctx.send('Invalid version!')

        await ctx.send('What is the seed of your new world (optional)')
        try:
            levelSeed = await client.wait_for('message', check=lambda message: message.author == ctx.author, timeout=5)
            for i in range(len(propFile)):
                if 'level-seed=' in propFile[i]:
                    propFile[i] = 'level-seed=' + levelSeed.content + '\n'
        except asyncio.exceptions.TimeoutError:
            for i in range(len(propFile)):
                if 'level-seed=' in propFile[i]:
                    propFile[i] = 'level-seed=\n'

        await ctx.send('What type of world do you want? default, flat, amplified, large biomes')
        levelType = await client.wait_for('message', check=lambda message: message.author == ctx.author)
        for i in range(len(worldTypes)):
            if worldTypes[i].lower() in ''.join(levelType.content.split(' ')):
                for j in range(len(propFile)):
                    if 'level-type=' in propFile[j]:
                        propFile[j] = 'level-type=' + worldTypes[i] + '\n'
                        typeFound = True
                        break
        if not typeFound:
            await ctx.send('Invalid type!')

        if foundVersion and typeFound:
            await ctx.send('Loading...')
            worldName = levelName.content
            verFile[0] = worldName + '\n'
            verFile[1] = version + '\n'
            open('versions.txt', 'wt').writelines(verFile)
            open('server.properties', 'wt').writelines(propFile)
            server = subprocess.Popen(f'java -Xmx{ramAlloc}m -Xms{ramAlloc}m -jar '+ serverDir + ' nogui', stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
            while True:
                line = server.stdout.readline()
                if 'Done' in line.decode():
                    c('stop')
                    await asyncio.sleep(5)
                    server.kill()
                    break
            
            await ctx.send('Success in generating ' + worldName + '!')
    else:
        await ctx.send('You cannot change the world when the server is up!')

@client.command()
async def properties(ctx):
    embed = discord.Embed(title='server.properties file', description='`1`  gamemode\n`2`  difficulty\n`3`  pvp\n`4`  hardcore\n`5`  motd', color=ctx.author.color)
    await ctx.send(embed=embed)
    answer = await client.wait_for('message', check=lambda message: message.author == ctx.author)
    properties = open('server.properties','rt').readlines()
    try:
        if int(answer.content) == 1:
            gamemodes = ['adventure','survival','spectator','creative']
            embed = discord.Embed(title='Gamemode', description='Change default gamemode\nadventure/survival/spectator/creative', color=ctx.author.color)
            await ctx.send(embed=embed)
            gamemodeAnswer = await client.wait_for('message', check=lambda message: message.author == ctx.author)
            if gamemodeAnswer.content.lower() in gamemodes:
                for i in range(len(properties)):
                    if 'gamemode=' in properties[i] and not 'force-gamemode=' in properties[1]:
                        properties[i] = 'gamemode=' + gamemodeAnswer.content.lower() + '\n'
                await ctx.send('Default gamemode has been set to '+gamemodeAnswer.content.lower()+'!')
            else:
                await ctx.send('Invalid value!')
                
        elif int(answer.content) == 2:
            difficulties = ['hard','normal','easy','peaceful']
            embed = discord.Embed(title='Difficulty', description='Change the default difficulty\nhard/normal/easy/peaceful')
            await ctx.send(embed=embed)
            difficultyAnswer = await client.wait_for('message', check=lambda message: message.author == ctx.author)
            if difficultyAnswer.content.lower() in difficulties:
                for i in range(len(properties)):
                    if 'difficulty=' in properties[i]:
                        properties[i] = 'difficulty=' + difficultyAnswer.content.lower() + '\n'
                await ctx.send('Changed default difficulty to ' + difficultyAnswer.content.lower() + '!')
            else:
                await ctx.send('Invalid value!')
        
        elif int(answer.content) == 3:
            TF = ['true','false']
            embed = discord.Embed(title='Pvp', description='Change allowed pvp\ntrue/false')
            await ctx.send(embed=embed)
            pvpAnswer = await client.wait_for('message', check=lambda message: message.author == ctx.author)
            if pvpAnswer.content.lower() in TF:
                for i in range(len(properties)):
                    if 'pvp=' in properties[i]:
                        properties[i] = 'pvp=' + pvpAnswer.content.lower() + '\n'
                await ctx.send('Changed allowed pvp to ' + pvpAnswer.content.lower() + '!')
            else:
                await ctx.send('Invalid value!')

        elif int(answer.content) == 4:
            TF = ['true','false']
            embed = discord.Embed(title='Hardcore', description='Change hardcore\ntrue/false')
            await ctx.send(embed=embed)
            hardcoreAnswer = await client.wait_for('message', check=lambda message: message.author == ctx.author)
            if hardcoreAnswer.content.lower() in TF:
                for i in range(len(properties)):
                    if 'hardcore=' in properties[i]:
                        properties[i] = 'hardcore=' + hardcoreAnswer.content.lower() + '\n'
                await ctx.send('Changed hardcore to ' + hardcoreAnswer.content.lower() + '!')
            else:
                await ctx.send('Invalid value!')

        elif int(answer.content) == 5:
            embed = discord.Embed(title='MOTD', description='Change the motd (message of the day)')
            await ctx.send(embed=embed)
            motdAnswer = await client.wait_for('message', check=lambda message: message.author == ctx.author)
            for i in range(len(properties)):
                if 'motd=' in properties[i]:
                    properties[i] = 'motd=' + motdAnswer.content + '\n'
            await ctx.send('The motd has been changed to ' + motdAnswer.content + '!')
        else:
            await ctx.send('Invalid Answer')

        with open('server.properties','wt') as propFile:
            propFile.writelines(properties)
    except ValueError:
        await ctx.send('Must be a number!')
    if not serverStopped:
        c('say Reloading...')
        await asyncio.sleep(1)
        c('reload')
# Fun Commands

#Gussing game
@client.command(aliases=['guesser','random','hangman'])
async def guessing(ctx, arg):
    rand1 = random.randint(0,9)
    if str(arg) == str(rand1):
        await ctx.send("Congratulations! You got the right answer.")
    else:
        await ctx.send("I'm sorry. That is an incorrect answer. The correct answer is "+str(rand1)+".")
@guessing.error
async def guessing_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Missing a number')

###################
# Backround Tasks #
###################

#Check Players
@tasks.loop(seconds=10)
async def checkPlayers():
    global serverStopped
    global shuttingDown
    if not serverStopped:
        players = MinecraftServer.lookup('localhost').status().players.online
        if players < minPlayers and not shuttingDown:
            shuttingDown = True
            c('say Not enough players, server shutting down in 10 minutes')
            for i in range(600):
                players = MinecraftServer.lookup('localhost').status().players.online
                if players >= minPlayers:
                    c('say More players have joined, Shutdown cancelled')
                    shuttingDown = False
                    break
                else:
                    await asyncio.sleep(1)
                    if i == 300:
                        c('say Not enough players, server shutting down in 5 minutes')
                    if i == 540:
                        c('say Not enough players, server shutting down in 1 minute')
                    if i == 595:
                        c('say Not enough players, server shutting down in 5 seconds')
                    if i == 599:
                        m('Server stopping...')
                        c('stop')
                        serverStopped = True
                        await asyncio.sleep(10)
                        server.kill()
def printLog():
    while not serverStopped:
        line = server.stdout.readline()
        if not line.rstrip().decode() == '':
            print(line.rstrip().decode())
