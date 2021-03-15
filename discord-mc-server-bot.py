scriptVersion = '1.2.5'
# Thanks to nickbrooking for the mc-server code
import discord
import threading
import random
import zipfile
import requests
import io
import datetime
import os
import shutil
import subprocess
import sys
import urllib.request
import asyncio
import time
import html2text
from discord.ext import commands, tasks
from discord.utils import get
from mcstatus import MinecraftServer

#############
# Variables #
#############

ramAlloc = '4092'
TOKEN = "ODA2NTYyOTcxNjU5OTI3NTc5.YBrQTQ.r0OwAwJojSoR0xzTdFlb8pzj-Oo"
worldName = str(open('versions.txt','rt').readlines()[0][0:-1])   
serverDir = 'versions\\' + str(open('versions.txt','rt').readlines()[1][0:-1]) + '.jar'
version = str(open('versions.txt','rt').readlines()[1][0:-1])
minPlayers = 1
votedPlayers = []
server = ''
serverStopped = True
shuttingDown = False
client = commands.Bot(command_prefix='.')
client.remove_command('help')

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
#Initialisation
def init():
    os.system('title ' + '[d-s-bot - ' + scriptVersion + ']')
    client.run(TOKEN)
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
#Remove space
def removeSpaces(s):
    i = 0
    while i < len(s):
        if s[i] == ' ':
            s = s[0:i] + s[i+1:len(s)]
            m(s)
        else:
            i+=1
    return s
#Start Server
async def startServer(ctx):
    global server
    global serverStopped
    
    m('Starting server...')
    server = subprocess.Popen(f'java -Xmx{ramAlloc}m -Xms{ramAlloc}m -jar '+ serverDir + ' nogui', stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    b = threading.Thread(name='backround', target=printLog)
    serverStopped = False
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
    for root, files in os.walk(worldName):
        for file in files:
            ziph.write(os.path.join(root, file))
#Download World
async def download_world(ctx, arg):
    global worldName
    global serverDir
    global version
    lines = []
    try:
                
        await ctx.send('Downloading...')
        z = zipfile.ZipFile(io.BytesIO(requests.get(str(str(arg) + '/download')).content))
        worldName = getWorld(z)
        for name in z.namelist():
            if not name.endswith(r'.txt') and not name.endswith(r'.zip'):
                z.extract(name)
                            
        lines = open('server.properties','rt').readlines()           
        for i in range(len(lines)):
            if 'level-name=' in lines[i]:
                lines[i] = f'level-name={worldName}\n'
        open('server.properties', 'wt').write(''.join(lines))
                
        lines = open('versions.txt','rt').readlines()
        lines[0] = worldName  + '\n'      
        open('versions.txt', 'wt').write(''.join(lines))
                            
        await ctx.send('Done!')
                
    except:
        await ctx.send('There was an error in downloading the world, try again in a few minutes')
#Get World
def getWorld(z):
    for name in z.namelist():
        if 'level.dat_old' in name:
            return name[0:-14]
#Get Version
def getVersion(ctx, arg):
    global serverDir
    global worldName
    global version
    lines = []
    versions = ['1.16','1.15','1.14','1.13','1.12','1.11','1.10','1.9','1.8']
    htmlText = html2text.html2text(str(requests.get(str(arg)).text))
    html2text.HTML2Text().ignore_links = True
    for i in range(len(htmlText)):
        if htmlText.lower()[i:i+11] == 'mc version:':
            for v in versions:
                if v in htmlText[i+10:i+20]:
                    for files in os.listdir('./versions'):
                        for fileName in files:
                            if fileName.endswith(r'.jar'):
                                if v in fileName:
                                    version = fileName[0:-4]
                                    with open('versions.txt', 'rt') as f:
                                        for line in f:
                                            lines.append(line)
    open('versions.txt','wt').close()
    lines[1] = version + '\n'
    with open('versions.txt','at') as f:
        for line in lines:
            f.write(line)
#Save World
def saveWorld():
    zipf = zipfile.ZipFile('saves/' + worldName + '_' + version + '_' + datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + '.zip', 'w')
    zipdir(worldName + '/', zipf)
    zipf.close()
    with open('versions.txt', 'at') as f:
        f.write('\n' + worldName + '=' + version)

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
    if not isinstance(error, commands.CheckFailure):
        print(error)
        await ctx.message.add_reaction('❗')
        await ctx.send("Invalid command")
        
#################
# Help Commands #
#################

@client.group(invoke_without_command=True, aliases=['?'])
async def help(ctx):
    embed = discord.Embed(title='Help', description='Use .help <command> for more info on a command', color=ctx.author.color)
    embed.add_field(name='General', value='start, cancel, say, voted')
    embed.add_field(name='World', value='world, worlds, map,\n regen, properties')
    await ctx.send(embed=embed)

# General

#Start
@help.command(aliases=['votestart'])
async def start(ctx):
    embed = discord.Embed(title='Start', description=('Vote to start the server, you need ' + str(minPlayers) + ' vote(s) to start the server'), color=ctx.author.color)
    embed.add_field(name='Aliases', value='votestart')
    await ctx.send(embed=embed)
#Cancel
@help.command(aliases=['cancelvote'])
async def cancel(ctx):
    embed = discord.Embed(title='Cancel', description=('Removes your vote to start the server, you need ' + str(minPlayers) + ' vote(s) to start the server'), color=ctx.author.color)
    embed.add_field(name='Aliases', value='cancelvote')
    await ctx.send(embed=embed)
#Say
@help.command()
async def say(ctx):
    embed = discord.Embed(title='Say', description=('Says a message in minecraft chat'), color=ctx.author.color)
    await ctx.send(embed=embed)
#Voted
@help.command(aliases=['votedplayers'])
async def voted(ctx):
    embed = discord.Embed(title='Voted', description=('Gets a list of all voted players'), color=ctx.author.color)
    embed.add_field(name='Aliases', value='votedplayers')
    await ctx.send(embed=embed)

# World

#Map
@help.command()
async def map(ctx):
    embed = discord.Embed(title='Map', description=('Downloads a map from https://www.minecraftmaps.com/'), color=ctx.author.color)
    await ctx.send(embed=embed)
#List Worlds
@help.command(aliases=['savedworlds','worlds'])
async def saved_worlds(ctx):
    embed = discord.Embed(title='Worlds', description=('Gets a list of all saved worlds'), color=ctx.author.color)
    await ctx.send(embed=embed)
#World
@help.command()
async def world(ctx):
    embed = discord.Embed(title='World', description=('Able to change world from saves'), color=ctx.author.color)
    await ctx.send(embed=embed)
#Generate
@help.command()
async def generate(ctx):
    embed = discord.Embed(title='Regenerate', description=('Regenerate a default minecraft world'), color=ctx.author.color)
    embed.add_field(name='Customizability', value='Custom seed, wait 5 seconds if not wanted\nCustom world name\nMinecraft version, 1.8.9-1.16.5')
    await ctx.send(embed=embed)
#Properties
@help.command()
async def properties(ctx):
    embed = discord.Embed(title='Properties', description=('Change default properties of a Minecraft server'), color=ctx.author.color)
    embed.add_field(name='Customizable Properties', value='Default gamemode\nDefault difficulty\nAllowed pvp\nHardcore\nmotd (message of the day)')
    await ctx.send(embed=embed)

############
# Commands #
############

# Admin Commands

#Op
@client.command()
@commands.has_permissions(administrator=True)
async def op(ctx, arg):
    if not serverStopped:
        c('op ' + str(arg))
        await ctx.send(str(arg) + ' has been opped')
    else:
        await ctx.send('Server is not up')
#Stop
@client.command(aliases=['stop'])
@commands.has_permissions(administrator=True)
async def forcestop(ctx):
        global votedPlayers
        if not serverStopped:
            await stopServer()
            votedPlayers.clear()
            await ctx.send('Server has stopped')
        else:
            await ctx.send('The server is not up')
#Set Minimum Players
@client.command(aliases=['setmin','setplayers'])
@commands.has_permissions(administrator=True)
async def setminplayers(ctx, arg):
    global minPlayers
    try:
        minPlayers = int(arg)
        await ctx.send('Minimum players has been set to '+str(arg))
    except ValueError:
        await ctx.send('Has to be a number')
        
# Server Commands

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
        await ctx.message.add_reaction('✅')
    except ValueError:
        await ctx.send('You have not voted yet.')
#Start
@client.command(aliases=['votestart'])
async def start(ctx):
    global scriptVersion
    global serverStopped
    global votedPlayers
    playerVoted = False
    players = []
    if serverStopped:
        for player in votedPlayers:
            if serverStopped and player == ctx.message.author:
                playerVoted = True
                await ctx.send('You have already voted.')
                break
        if not playerVoted and serverStopped:
            votedPlayers.append(ctx.message.author)
            players = []
            for player in votedPlayers:
                if player.nick == None:
                    players.append(removeFancy(str(player))[0:-5] + '\n')
                else:
                    players.append(removeFancy(player.nick) + '\n')
            description = (''.join(players) + str(len(votedPlayers)) + '/' + str(minPlayers))
            embed = discord.Embed(title='Voted Players', description=description, color=ctx.author.color)
            if not len(votedPlayers) >= minPlayers:
                await ctx.send(embed=embed)
            await ctx.message.add_reaction('✅')
    elif not serverStopped:
        ctx.send('Server is already up.')
    
    if serverStopped and len(votedPlayers) >= minPlayers:
        embed = discord.Embed(title='Starting Server...', description='', color=ctx.author.color)
        embed.add_field(name = 'World', value = worldName)
        embed.add_field(name = 'Version', value = version)
        await ctx.send(embed=embed)
        await startServer(ctx)
        serverStopped = False
#Say
@client.command()
async def say(ctx, *, arg):
    if not serverStopped:
        if not ctx.author.nick == None:
            c('tellraw @a {\"text\":\"<' + str(ctx.author.nick) + '> ' + str(arg) + '\"}')
        else:
            c('tellraw @a {\"text\":\"<' + str(ctx.author)[0:-5] + '> ' + str(arg) + '\"}')
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
        noAnswers = ['no','naw','nah','nope','n']

        await ctx.send('Would you like to save ' + worldName + '?')
        msg = await client.wait_for('message', check=lambda message: message.author == ctx.author)
        if msg.content.lower() in yesAnswers:
            await ctx.send('Saving...')
            saveWorld()
            try:
                shutil.rmtree(fr'{worldName}/')
            except:
                m('World file not found')
            getVersion(ctx, arg)
            await download_world(ctx, arg)
        elif msg.content.lower() in noAnswers:
            try:
                shutil.rmtree(fr'{worldName}/')
            except:
                m('World file not found')
            getVersion(ctx, arg)
            await download_world(ctx, arg)
        else:
            await ctx.send('Invalid answer!')
    else:
        await ctx.send('That is not from minecraftmaps!')
#Saved Worlds
@client.command(aliases=['savedworlds','worlds'])
async def saved_worlds(ctx):
    savedWorlds = []
    savedVersions = []
    embed = discord.Embed(title='Saved Worlds', description='', color=ctx.author.color)
    for files in os.listdir('./saves'):
        for fileName in files:
            for i in range(len(fileName)):
                if fileName[i] == '_':
                    savedWorlds.append(fileName[0:i] + '\n')
                    for j in range(9):
                        if fileName[j+i+1] == '_':
                            savedVersions.append(fileName[i+1:j+i+1] + '\n')
                            break
                    break
    embed.add_field(name='Worlds', value=''.join(savedWorlds))
    embed.add_field(name='Versions', value=''.join(savedVersions))
    await ctx.send(embed=embed)
#Bot Version
@client.command(aliases=['botVersion','scriptversion','scriptVersion'])
async def botversion(ctx):
    await ctx.send('Minecraft Server Bot is on version ' + scriptVersion)
#World        
@client.command()
async def world(ctx, arg):
#Take content out of file
    fileName = open(r"versions.txt", "r")
    propFile = open('server.properties','rt').readlines()
    bool1 = False
    zipName = ""
    content = fileName.readlines()
    #print(content)
    length = len(content)
    #print(length)
    fileName.close()
    worldInput = str(arg)
    for count1 in range(length):
        #finding barrier
        if content[count1] == "------\n":
            if content[count1 + 1] == "Versions:\n":
                pass
            #Finding world area
            if content[count1 + 1] == "Worlds:\n":
                worldIndex = content.index("Worlds:\n")
                #print(worldIndex)
                #Getting worlds
                for inCount in range(worldIndex,length):
                    for inCount1 in range(len(content[inCount])):
                        newContent = content[inCount]
                        if newContent[inCount1] == "=":
                            lengthContent = len(newContent)
                            worldName = newContent[0:inCount1]
                            versionName = newContent[inCount1+1:lengthContent]
                            #print(worldName)
                            if worldInput.lower() in worldName.lower():
                                #print(worldInput,worldName)
                                await ctx.send("Loading...")
                                #print(versionName)
                                bool1 = True
                                versionName1 = versionName
                                worldName1 = worldName
                                worldName = content[0][:-1]
                                break
                    if bool1:
                        break
                            
    #Changing info in file to new info
    if bool1 == True:
        changedContent = content
        for count2 in range(2):
            changedContent.pop(0)
        #print(versionName1)
        changedContent.insert(0,worldName1+"\n")
        changedContent.insert(1,versionName1)
        outContent = changedContent
        #print(worldName1)
        #print(outContent)
        yesAnswers = ['yes','ye','yea','yeah','yah','ya','y']
        await ctx.send('Would you like to save ' + worldName + '?')
        msg = await client.wait_for('message', check=lambda message: message.author == ctx.author)
        if msg.content.lower() in yesAnswers:
            await ctx.send('Saving...')
            saveWorld()
        try:
            shutil.rmtree(fr'{worldName}/')
        except:
            m('World file not found')
        savesList = os.listdir(r"./saves")
        for count4 in range(len(savesList)):
            if worldInput.lower() in savesList[count4].lower():
                zipName = savesList[count4]
            else:
                pass
        try:
            z = zipfile.ZipFile("saves/"+zipName)
            worldName = getWorld(z)
            for name in z.namelist():
                z.extract(name)
            os.remove("./saves/"+zipName)
        except PermissionError:
            m('Zip file not found')
        for i in range(len(propFile)):
            if 'level-name=' in propFile[i]:
                propFile[i] = 'level-name=' + worldName + '\n'
        outContent2 = [worldName+"\n" , "*.zip\n", ".gitignore\n", "server.properties\n", "versions.txt\n"]
        fileHandle1 = open(r".gitignore","w")
        fileHandle1.writelines(outContent2)
        fileHandle1.close()
        open('server.properties','wt').write(''.join(propFile))
        open('versions.txt','wt').write(''.join(outContent))
        await ctx.send('Success!')
    else:
        await ctx.send("There is no world with that name")
#Generate
@client.command()
async def generate(ctx):
    global serverDir
    global version
    global worldName
    yesAnswers = ['yes','ye','yea','yeah','yah','ya','y']
    versions = ['1.16','1.15','1.14','1.13','1.12','1.11','1.10','1.9','1.8']
    worldTypes = ['largeBiomes', 'default', 'amplified', 'superflat']
    propFile = open('server.properties', 'rt').readlines()
    verFile = open('versions.txt', 'rt').readlines()
    foundVersion = False
    typeFound = False

    await ctx.send('Would you like to save ' + worldName + '?')
    answer = await client.wait_for('message', check=lambda message: message.author == ctx.author)
    if answer.content.lower() in yesAnswers:
        await ctx.send('Saving...')
        saveWorld()
    try:
        shutil.rmtree(fr'{worldName}/')
    except:
        m('World file not found')

    await ctx.send('What is the seed of your new world seed (optional)')
    try:
        levelSeed = await client.wait_for('message', check=lambda message: message.author == ctx.author, timeout=5)
        for i in range(len(propFile)):
            if 'level-seed=' in propFile[i]:
                propFile[i] = 'level-seed=' + levelSeed.content + '\n'
    except asyncio.exceptions.TimeoutError:
        for i in range(len(propFile)):
            if 'level-seed=' in propFile[i]:
                propFile[i] = 'level-seed=\n'

    await ctx.send('What type of world do you want? default, superflat, amplified, large biomes')
    levelType = await client.wait_for('message', check=lambda message: message.author == ctx.author)
    for t in worldTypes:
        if t.lower() in removeSpaces(levelType.content.lower()):
            for i in range(len(propFile)):
                if 'level-type=' in propFile[i]:
                    propFile[i] = 'level-type=' + t + '\n'
                    typeFound = True
                    break
    if not typeFound:
        await ctx.send('Invalid type!')
        return

    await ctx.send('What is the name of the new world?')
    levelName = await client.wait_for('message', check=lambda message: message.author == ctx.author)
    for i in range(len(propFile)):
        if 'level-name=' in propFile[i]:
            propFile[i] = 'level-name=' + levelName.content + '\n'

    await ctx.send('What is the version of ' + levelName.content)
    worldVersion = await client.wait_for('message', check=lambda message: message.author == ctx.author)
    for v in versions:
        if v in worldVersion.content:
            for jar in os.listdir('./versions'):
                if v in str(jar):
                    foundVersion = True
                    serverDir = str(jar)
                    version = serverDir[:-4]
                    break
    if not foundVersion:
        await ctx.send('Invalid version!')

    if foundVersion and typeFound:
        worldName = levelName.content
        verFile[0] = worldName + '\n'
        verFile[1] = version + '\n'
        open('versions.txt', 'wt').write(''.join(verFile))
        open('server.properties', 'wt').write(''.join(propFile))
        await ctx.send('Success in generating ' + worldName + '!')

@client.command()
async def properties(ctx):
    description = '`1`  gamemode\n`2`  difficulty\n`3`  pvp\n`4`  hardcore\n`5`  motd'
    embed = discord.Embed(title='server.properties file', description=description, color=ctx.author.color)
    await ctx.send(embed=embed)
    answer = await client.wait_for('message', check=lambda message: message.author == ctx.author)
    try:
        if int(answer.content) == 1:
            gamemodes = ['adventure','survival','spectator','creative']
            embed = discord.Embed(title='Gamemode', description='Change default gamemode\nadventure/survival/spectator/creative', color=ctx.author.color)
            await ctx.send(embed=embed)
            gamemodeAnswer = await client.wait_for('message', check=lambda message: message.author == ctx.author)
            if gamemodeAnswer.content.lower() in gamemodes:
                properties = open('server.properties','rt').readlines()
                for i in range(len(properties)):
                    if 'gamemode=' in properties[i] and not 'force-gamemode=' in properties[1]:
                        properties[i] = 'gamemode=' + gamemodeAnswer.content.lower() + '\n'
                with open('server.properties','wt') as propFile:
                    propFile.write(''.join(properties))
                await ctx.send('Default gamemode has been set to '+gamemodeAnswer.content.lower()+'!')
            else:
                await ctx.send('Invalid value!')
                
        elif int(answer.content) == 2:
            difficulties = ['hard','normal','easy','peaceful']
            embed = discord.Embed(title='Difficulty', description='Change the default difficulty\nhard/normal/easy/peaceful')
            await ctx.send(embed=embed)
            difficultyAnswer = await client.wait_for('message', check=lambda message: message.author == ctx.author)
            if difficultyAnswer.content.lower() in difficulties:
                properties = open('server.properties','rt').readlines()
                for i in range(len(properties)):
                    if 'difficulty=' in properties[i]:
                        properties[i] = 'difficulty=' + difficultyAnswer.content.lower() + '\n'
                with open('server.properties','wt') as propFile:
                    propFile.write(''.join(properties))
                await ctx.send('Changed default difficulty to ' + difficultyAnswer.content.lower() + '!')
            else:
                await ctx.send('Invalid value!')
        
        elif int(answer.content) == 3:
            TF = ['true','false']
            embed = discord.Embed(title='Pvp', description='Change allowed pvp\ntrue/false')
            await ctx.send(embed=embed)
            pvpAnswer = await client.wait_for('message', check=lambda message: message.author == ctx.author)
            if pvpAnswer.content.lower() in TF:
                properties = open('server.properties','rt').readlines()
                for i in range(len(properties)):
                    if 'pvp=' in properties[i]:
                        properties[i] = 'pvp=' + pvpAnswer.content.lower() + '\n'
                with open('server.properties','wt') as propFile:
                    propFile.write(''.join(properties))
                await ctx.send('Changed allowed pvp to ' + pvpAnswer.content.lower() + '!')
            else:
                await ctx.send('Invalid value!')

        elif int(answer.content) == 4:
            TF = ['true','false']
            embed = discord.Embed(title='Hardcore', description='Change hardcore\ntrue/false')
            await ctx.send(embed=embed)
            hardcoreAnswer = await client.wait_for('message', check=lambda message: message.author == ctx.author)
            if hardcoreAnswer.content.lower() in TF:
                properties = open('server.properties','rt').readlines()
                for i in range(len(properties)):
                    if 'hardcore=' in properties[i]:
                        properties[i] = 'hardcore=' + hardcoreAnswer.content.lower() + '\n'
                with open('server.properties','wt') as propFile:
                    propFile.write(''.join(properties))
                await ctx.send('Changed hardcore to ' + hardcoreAnswer.content.lower() + '!')
            else:
                await ctx.send('Invalid value!')

        elif int(answer.content) == 5:
            embed = discord.Embed(title='MOTD', description='Change the motd (message of the day)')
            await ctx.send(embed=embed)
            motdAnswer = await client.wait_for('message', check=lambda message: message.author == ctx.author)
            properties = open('server.properties','rt').readlines()
            for i in range(len(properties)):
                if 'motd=' in properties[i]:
                    properties[i] = 'motd=' + motdAnswer.content + '\n'
                with open('server.properties','wt') as propFile:
                    propFile.write(''.join(properties))
            await ctx.send('The motd has been changed to ' + motdAnswer.content + '!')
            
        else:
            await ctx.send('That is out of range!')
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

###################
# Backround Tasks #
###################

#Check Players
@tasks.loop(seconds=10)
async def checkPlayers():
    global serverStopped
    global shuttingDown
    global votedPlayers
    
    if not serverStopped:
        try:
            
            players = MinecraftServer.lookup('localhost').status().players.online
            
            if players < minPlayers and not shuttingDown:
                shuttingDown = True
                c('say Server shutting down in 10 minutes')
                await asyncio.sleep(300)
                players = MinecraftServer.lookup('localhost').status().players.online
                
                if players < minPlayers:
                    c('say Server shutting down in 5 minute')
                    await asyncio.sleep(240)
                    players = MinecraftServer.lookup('localhost').status().players.online
                    
                    if players < minPlayers:
                        c('say Server shutting down in 1 minute')
                        await asyncio.sleep(55)
                        players = MinecraftServer.lookup('localhost').status().players.online
                        
                        if players < minPlayers:
                            c('say Server shutting down in 5 seconds')
                            await asyncio.sleep(1)
                            c('say Server shutting down in 4 seconds')
                            await asyncio.sleep(1)
                            c('say Server shutting down in 3 seconds')
                            await asyncio.sleep(1)
                            c('say Server shutting down in 2 seconds')
                            await asyncio.sleep(1)
                            c('say Server shutting down in 1 second')
                            await asyncio.sleep(1)
                            players = MinecraftServer.lookup('localhost').status().players.online
                            
                            if players < minPlayers:
                                stopServer()
                                votedPlayers.clear()
                                shuttingDown = False
                            elif players >= minPlayers and shuttingDown:
                                c('say More players have joined, cancelling the shutdown')
                                shuttingDown = False
                                
                        elif players >= minPlayers and shuttingDown:
                            c('say More players have joined, cancelling the shutdown')
                            shuttingDown = False
                            
                elif players >= minPlayers and shuttingDown:
                    c('say More players have joined, cancelling the shutdown')
                    shuttingDown = False
                    
            elif players >= minPlayers and shuttingDown:
                c('say More players have joined, cancelling the shutdown')
                shuttingDown = False

        except ConnectionRefusedError:
            shuttingDown = False
            m('The server is not responding, try again later.')
def printLog():
    while not serverStopped:
        line = server.stdout.readline()
        print(line.rstrip().decode())
init()
