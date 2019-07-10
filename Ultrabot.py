import discord
import traceback
from discord.ext import commands
import praw
import datetime as dt
import os
import requests
from datetime import datetime, timedelta
import re
import json
import threading
import youtube_dl
import urllib.parse
import urllib.request
import sys
import asyncio
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import random
import smtplib
import ssl
from operator import itemgetter
from pokarray import pokarray
from aiohttp import web
import aiohttp
from dateutil import parser
import time
from secret import jsonfo


reddit = praw.Reddit(client_id=jsonfo["red_id"], \
                     client_secret=jsonfo["red_secret"], \
                     user_agent=jsonfo["red_usr_agent"], \
                    )

memes = reddit.subreddit('memes')
dankmemes = reddit.subreddit('dankmemes')
showerthoughts = reddit.subreddit('showerthoughts')
smartish = reddit.subreddit('iamverysmart')
advice = reddit.subreddit('quotes')

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

context = ssl.create_default_context()
password = jsonfo["bot_email_pass"]
port = 465

prefix = '!'

antispam_time = {}
antispam_count = {}
banter = {}
blacklist = []
bypasses = []
daily = []
hackathons = []
rawleaders = []
leaders = []
playlists = []

curr = []

player = 0

forced = False
songs = []
source = 1

punishments = [lambda message: msg_timeout(message, 300),
                             lambda message: msg_timeout(message, 600), 
                             lambda message: msg_timeout(message, 1200),
                             lambda message: msg_timeout(message, 2400),
                             lambda message: msg_timeout(message, 4800),
                             lambda message: msg_timeout(message, 9600),
                             lambda message: msg_timeout(message, 19200),
                             lambda message: memkick(message),
                             lambda message: memban(message)]

roulette_count = 1

# Firebase Initialization
cred = credentials.Certificate("key.json")
firebase = firebase_admin.initialize_app(cred)
db = firestore.client()

black_ref = db.collection(u'blacklist')
blacollection = black_ref.stream()
for i in blacollection:
    blacklist = i.to_dict()["blacklist"]

leadercoll = db.collection(u'leaderboard')
leaderboard = leadercoll.stream()
for i in leaderboard:
    raw = i.to_dict()
    rawleaders.append(raw)

leadmembers = list(rawleaders[0].keys())
rawleaders = rawleaders[0]

for i in leadmembers:
    scoring =[i, rawleaders[i]]
    leaders.append(scoring)

leaders = sorted(leaders, key=itemgetter(1), reverse=True)


playcoll = db.collection(u'playlists')
rawplay = playcoll.stream()
for i in rawplay:
    raw = i.to_dict()
    playlists.append(raw)

playlists = playlists[0]

daycoll = db.collection(u'daily')
rawday = daycoll.stream()
for i in rawday:
    raw = i.to_dict()
    daily.append(raw)
daily = daily[0]

timecoll = db.collection(u'timeouts')
rawtimes = timecoll.stream()
for i in rawtimes:
    timeouts =  i.to_dict()


TOKEN = jsonfo["TOKEN"]

auth_id = lambda msg: str(msg.author.id)

def cliname():
    global guild
    return guild.me.nick

async def memkick(message):
    author = message.author
    await message.guild.kick(author, reason='Antispam offenses')
    embed=discord.Embed(title='Antispam', description=f"Kicked {muter.mention} due to excessive violations.", color=0x800080)
    embed.set_author(name="SpamBot", icon_url=client.user.avatar_url)
    await channel.send(embed=embed)


async def memban(message):
    author = message.author
    await message.guild.ban(author, reason='Antispam offenses')
    embed=discord.Embed(title='Antispam', description=f"Banned {muter.mention} due to excessive violations.", color=0x800080)
    embed.set_author(name="SpamBot", icon_url=client.user.avatar_url)
    await channel.send(embed=embed)


async def msg_timeout(message, timeout):
    mute = discord.utils.get(message.guild.roles, name='Mute')
    verif = discord.utils.get(message.guild.roles, name='Verified Hackers') 
    muter = message.author
    channel = message.channel
    await muter.add_roles(mute, reason='Antispam')
    await muter.remove_roles(verif, reason='Antispam!')
    embed=discord.Embed(title='Antispam', description=f"Muted {muter.mention} for {timeout/60} minutes due to spam.", color=0x800080)
    embed.set_author(name="SpamBot", icon_url=client.user.avatar_url)
    embed.set_footer(text = "Ultrabot by Pradyun Narkadamilli")
    await channel.send(embed=embed)
    await asyncio.sleep(timeout)
    if mute in muter.roles:
        await muter.remove_roles(mute, reason="Timeout over!")
        await muter.add_roles(verif, reason="Timout over!")
        embed=discord.Embed(title='Antispam', description=f"Unmuted {muter.mention}, timeout is over.", color=0x800080)
        embed.set_author(name="SpamBot", icon_url=client.user.avatar_url)
        embed.set_footer(text = "Ultrabot by Pradyun Narkadamilli")
        await channel.send(embed=embed)


async def roulsend(msg, channel):
    embed=discord.Embed(title='Roulette', description=msg, color=0x008080)
    embed.set_author(name=f"Ref {cliname()}", icon_url=client.user.avatar_url)
    embed.set_footer(text = "Ultrabot by Pradyun Narkadamilli")
    await channel.send(embed=embed)


async def pyrun(file):
    proc = await asyncio.create_subprocess_shell(
        f'python {file}',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()

    if stdout:
        return f'{stdout.decode()}'
    if stderr:
        return f'{stderr.decode()}'


async def runsend(msg, channel):
    embed=discord.Embed(title='Runtime', description=msg, color=0xffff00)
    embed.set_author(name="Server", icon_url=client.user.avatar_url)
    embed.set_footer(text = "Ultrabot by Pradyun Narkadamilli")
    await channel.send(embed=embed)

async def compilec(file):
    proc = await asyncio.create_subprocess_shell(
        f'gcc -o {file}.out {file}.c',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()

    if stdout:
        return f'{stdout.decode()}'
    if stderr:
        return f'{stderr.decode()}'


async def runc(file):
    proc = await asyncio.create_subprocess_shell(
        f'./{file}.out',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()

    if stdout:
        return f'{stdout.decode()}'
    if stderr:
        return f'{stderr.decode()}'



async def compilecpp(file):
    proc = await asyncio.create_subprocess_shell(
        f'g++ -o {file}.out {file}.cpp',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()

    if stdout:
        return f'{stdout.decode()}'
    if stderr:
        return f'{stderr.decode()}'


async def runcpp(file):
    proc = await asyncio.create_subprocess_shell(
        f'./{file}.out',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()

    if stdout:
        return f'{stdout.decode()}'
    if stderr:
        return f'{stderr.decode()}'


async def vercheck():
    proc = await asyncio.create_subprocess_shell(
        f'gcc -version',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()

    if stdout:
        return 'GCC is good.'
    if stderr:
        return 'GCC is good.'


async def javac(file):
    proc = await asyncio.create_subprocess_shell(
        f'javac {file}',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()

    if stdout:
        return ['success', f'{stdout.decode()}']
    if stderr:
        return ['error', f'{stderr.decode()}']        


async def runjava(file):
    proc = await asyncio.create_subprocess_shell(
        f'java {file}',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()

    if stdout:
        return f'{stdout.decode()}'
    if stderr:
        return f'{stderr.decode()}'


def get_pre(bot):
    try:
        return bot.command_prefix
    except AttributeError:
        return '!'

def usage(command):
    compalias = command.qualified_name
    if len(command.aliases) > 0:
        for alias in command.aliases:
            compalias = f'{compalias}|{alias}'
        compalias = f'[{compalias}]'
    return f'{get_pre(client)}{compalias} {command.signature}'

def cogster(cog):
    embed=discord.Embed(title=f'{cog.qualified_name}', color=0x800080)
    embed.set_author(name="IIT IT", icon_url=client.user.avatar_url)
    embed.set_footer(text = "Ultrabot by Pradyun Narkadamilli")
    for cmd in cog.get_commands():
        embed.add_field(name=cmd.name, value=cmd.brief, inline=False)
    return embed



client = 1
client = commands.Bot(command_prefix=get_pre(client))
client.remove_command('help')
guild = 1

@client.check
async def globally_block_dms(ctx):
    if ctx.guild is not None:
        return True
    else:
        raise commands.NoPrivateMessage


def checkint(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


async def role_check(member, role_id):
    returner = False
    for i in member.roles:
        if i.id == role_id:
            returner = True
    return returner


async def number_response(ctx, author):
    global client

    def check(msg):
        if msg.author.id == author.id and msg.channel == ctx:
            if checkint(msg.content):
                if int(msg.content)>0:
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False
    try:
        number = await client.wait_for('message', check=check)
        number = number.content
        number = int(number)
        return number

    except asyncio.TimeoutError:
        return False


async def check_response(ctx, content, author):
    global client

    def check(msg):
        return msg.author.id == author.id and msg.content.lower() in content and msg.channel == ctx
    try:
        return await client.wait_for('message', check=check)
    except asyncio.TimeoutError:
        return None


class Games(commands.Cog, name='Games'):

    def __init__(self, bot):
        self.bot = bot

    '''@commands.command(brief="I'd like some Black Jack Cheese please.", description='One of the most popular card games in the world, now on discord for no apparent reason.')
    async def blackjack(self, ctx):
        global rawleaders
        global db
        global leaders'''

    @commands.command(brief="Settle the conflict with a flip!", description="Literally a coinflip.")
    async def flip(self, ctx):
        flip = random.randint(1,2)
        flip = "heads"
        if flip == 2:
            flip == "tails"
        msg = f"The coin landed on {flip}."
        embed=discord.Embed(title="Coinflip", description=msg, color=0x008000)
        embed.set_author(name=f"Treasurer {cliname()}", icon_url=client.user.avatar_url)
        embed.set_footer(text = "Ultrabot by Pradyun Narkadamilli")
        await ctx.send(embed=embed)


    @commands.command(brief="Think of a social security check, but on a daily basis.", description="Basically every daily reward ever, but in this server, with this bot. Sound good?")
    async def daily(self, ctx):
        global leaders
        global rawleaders
        global db
        global daily

        now = datetime.now()
        if str(ctx.author.id) not in list(daily.keys()):
            pass
        else:
            timer = daily[str(ctx.author.id)]
            timer = parser.parse(timer)
            if not timer + timedelta(hours=24) <= now:
                diff = timer + timedelta(hours = 24) - now
                msg = f"Too early for that man... I'm gonna need you to wait {diff}."
                embed=discord.Embed(title="Daily", description=msg, color=0x008000)
                embed.set_author(name=f"Banker {cliname()}", icon_url=client.user.avatar_url)
                embed.set_footer(text = "Ultrabot by Pradyun Narkadamilli")
                await ctx.send(embed=embed)
                return

        daily[str(ctx.author.id)] = str(now)


        msg = 'Winner winner, chicken dinner... you get 30 coins!'
        embed=discord.Embed(title='Daily', description=msg, color=0x008000)
        embed.set_author(name=f"Banker {cliname()}", icon_url=client.user.avatar_url)
        embed.set_footer(text = "Ultrabot by Pradyun Narkadamilli")
        await ctx.send(embed=embed)
        rawleaders[str(ctx.author.id)] += 30
        leaders[:] = (value for value in leaders if value[0] != str(ctx.author.id))
        leaders.append([str(ctx.author.id), rawleaders[str(ctx.author.id)]])
        leaders = sorted(leaders, key=itemgetter(1), reverse=True)
        db.collection(u'leaderboard').document(u'leaderboard').set(rawleaders)
        db.collection(u'daily').document(u'daily').set(daily)


    @commands.command(brief='Do you have what it takes to name them all?', description='In honor of the age long pop culture icon, this game has you guess Pokémon!')
    async def pokeguess(self, ctx):
        global rawleaders
        global leaders
        global db
        pokenum = random.randint(1, 802)
        imgurl = f"https://gearoid.me/pokemon/images/artwork/{pokenum}.png"
        pokename = pokarray[pokenum-1]['names']['en']
        msg = "**Who's that Pokémon!?**\nQuick, you've got 20 seconds!"
        embed=discord.Embed(title='PokéGuess', description=msg, color=0xffff00)
        embed.set_author(name=f"Trainer {cliname()}", icon_url=client.user.avatar_url)
        embed.set_footer(text = "Ultrabot by Pradyun Narkadamilli")
        embed.set_image(url=imgurl)
        await ctx.send(embed=embed)
        def check(text):
            return text.channel == ctx.channel and text.author == ctx.author
        try:
            guessname = await client.wait_for('message', check=check, timeout=20)
        except asyncio.TimeoutError:
            embed=discord.Embed(title='PokéGuess', description=f"Too late! The Pokémon's name was {pokename.capitalize()}!", color=0xffff00)
            embed.set_author(name=f"Trainer {cliname()}", icon_url=client.user.avatar_url)
            embed.set_footer(text = "Ultrabot by Pradyun Narkadamilli")
            await ctx.send(embed=embed)
            return
        if not guessname.content.lower() == pokename:
            embed=discord.Embed(title='PokéGuess', description=f"I'm sorry, but that's wrong! That Pokémon's name was {pokename.capitalize()}!", color=0xffff00)
            embed.set_author(name=f"Trainer {cliname()}", icon_url=client.user.avatar_url)
            embed.set_footer(text = "Ultrabot by Pradyun Narkadamilli")
            await ctx.send(embed=embed)
            return
        embed=discord.Embed(title='PokéGuess', description=f"Well done! The name of that Pokémon is indeed {pokename.capitalize()}!", color=0xffff00)
        embed.set_author(name=f"Trainer {cliname()}]", icon_url=client.user.avatar_url)
        embed.set_footer(text = "Ultrabot by Pradyun Narkadamilli")
        await ctx.send(embed=embed)
        try:
            curbal = rawleaders[str(ctx.author.id)]
        except KeyError:
            rawleaders[str(ctx.author.id)] = 0
        rawleaders[str(ctx.author.id)] += 5
        leaders[:] = (value for value in leaders if value[0] != str(ctx.author.id))
        leaders.append([str(ctx.author.id), rawleaders[str(ctx.author.id)]])
        leaders = sorted(leaders, key=itemgetter(1), reverse=True)
        db.collection(u'leaderboard').document(u'leaderboard').set(rawleaders)


    @commands.command(brief='How much ya got?', description='Your score in the server, an aggregate of all the games.')
    async def score(self, ctx, *, user: discord.Member=None):
        global rawleaders
        if user is None:
            try:
                msg = f'Your score is {rawleaders[str(ctx.author.id)]}.'
            except:
                msg='You haven\'t won any games yet... I can\'t give you a score!'
            embed=discord.Embed(title='Score', description=msg, color=0x008000)
            embed.set_author(name=f"Ref {cliname()}", icon_url=client.user.avatar_url)
            embed.set_footer(text = "Ultrabot by Pradyun Narkadamilli")
            await ctx.send(embed=embed)
        elif user is not None:
            try:
                msg = f'The score of {user.mention} is {rawleaders[str(user.id)]}.'
            except:
                msg = f'Looks like {user.mention} hasn\'t played any games yet... he doesn\'t have a score!'
            embed=discord.Embed(title='Score', description=msg, color=0x008000)
            embed.set_author(name=f"Ref {cliname()}", icon_url=client.user.avatar_url)
            embed.set_footer(text = "Ultrabot by Pradyun Narkadamilli")
            await ctx.send(embed=embed)


    @commands.command(brief='Time to mess with the money...', description='Bet some points, and see how your luck stacks up. Time to push your way up the leaderboard!', aliases=['bet', 'wager'])
    async def gamble(self, ctx, *, bet):
        global leaders
        global db
        global rawleaders


        try:
            bal = rawleaders[str(ctx.author.id)]
            if bal == 0:
                raise discord.UserInputError
        except:
            embed=discord.Embed(description="You have no money! Play some Roulette or PokéGuess and get some!", color=0x00ff00)
            embed.set_author(name="Gambling", icon_url=(client.user.avatar_url))
            embed.set_footer(text = "Ultrabot by Pradyun Narkadamilli")
            await ctx.send(embed=embed)
            return
        if bet.lower() == "all":
            bet = bal
        if not checkint(bet):
            return
        bet = int(bet)
        if bet <= bal:
            better = random.randint(1, 100)
            houser = random.randint(1, 100)
            mult = (random.randint(1, 100))/100
            pfp = ctx.author.avatar_url
            if better >= houser:
                await asyncio.sleep(3)
                embed=discord.Embed(description=f"{ctx.author.display_name} was able to increase his investments!", color=0x00ff00)
                embed.set_author(name=f"{ctx.author.display_name}'s Gambling Game", icon_url=(pfp))
                embed.add_field(name=f'{ctx.author.display_name}\'s Roll', value=better, inline=True)
                embed.add_field(name="House\'s Roll", value=houser, inline=True)
                embed.add_field(name="Bet Amount", value=bet, inline=False)
                embed.add_field(name="Multiplier", value=mult+1, inline=True)
                embed.set_footer(text=f"Your new balance is {int(bal+int((mult*bet)//1))} points")
                await ctx.send(embed=embed)
                rawleaders[str(ctx.author.id)] += int(mult*bet//1)
                rawleaders[str(ctx.author.id)] = rawleaders[str(ctx.author.id)]//1
            elif better < houser:
                await asyncio.sleep(3)
                embed=discord.Embed(description=f"{ctx.author.display_name} lost his money! Sucker...", color=0xff0000)
                embed.set_author(name=f"{ctx.author.display_name}'s Gambling Game", icon_url=(pfp))
                embed.add_field(name=f'{ctx.author.display_name}\'s Roll', value=better, inline=True)
                embed.add_field(name="House\'s Roll", value=houser, inline=True)
                embed.add_field(name="Bet Amount", value=bet, inline=False)
                embed.set_footer(text=f"Your new balance is {bal-bet} points")
                await ctx.send(embed=embed)
                rawleaders[str(ctx.author.id)] -= bet
            leaders[:] = (value for value in leaders if value[0] != str(ctx.author.id))
            leaders.append([str(ctx.author.id), rawleaders[str(ctx.author.id)]])
            leaders = sorted(leaders, key=itemgetter(1), reverse=True)
            db.collection(u'leaderboard').document(u'leaderboard').set(rawleaders)
        elif bet > bal:
            embed=discord.Embed(description="Rule one of gambling.... don\'t spend money you don\'t have!", color=0x00ff00)
            embed.set_author(name="Gambling", icon_url=(client.user.avatar_url))
            embed.set_footer(text = "Ultrabot by Pradyun Narkadamilli")
            await ctx.send(embed=embed)


    @commands.command(brief='How do you stack up against the others?', description='Check out who the top performers of the server are...')
    async def leaderboard(self, ctx):
        global leaders
        if len(leaders) < 3:
            msg = 'Looks like the leaderboard isn\'t quite populated enough yet...'
            embed=discord.Embed(title='Leaderboard', description=msg, color=0x008000)
            embed.set_author(name=f"Commissioner {cliname()}", icon_url=client.user.avatar_url)
            embed.set_footer(text = "Ultrabot by Pradyun Narkadamilli")
            await ctx.send(embed=embed)
        else:
            rank1 = client.get_user(int(leaders[0][0]))
            rank2 = client.get_user(int(leaders[1][0]))
            rank3 = client.get_user(int(leaders[2][0]))
            score1 = leaders[0][1]
            score2 = leaders[1][1]
            score3 = leaders[2][1]
            msg = f''':first_place: {rank1.mention}:{score1}\n:second_place: {rank2.mention}:{score2}\n:third_place: {rank3.mention}:{score3}'''
            embed=discord.Embed(title='Leaderboard', description=msg, color=0x008000)
            embed.set_author(name=f"Commissioner {cliname()}", icon_url=client.user.avatar_url)
            embed.set_footer(text = "Ultrabot by Pradyun Narkadamilli")
            await ctx.send(embed=embed)




    @commands.command(brief='In Soviet Russia, we shoot gun to have fun.', description='Enjoy a good ol\' fashioned game of russian roulette. Break out the vodka!')
    async def roulette(self, ctx, *, challenger: discord.Member):
        global rawleaders
        global leadmembers
        global leaders
        global roulette_count
        global db
        global prefix
        guild = ctx.guild
        if challenger != ctx.author:
            msg = f'{challenger.mention}, do you accept the challenge?' \
                f'If so, type in yes{prefix} in the next 20 seconds.' \
                f'If not, type anything else ending with {prefix}.'
            embed=discord.Embed(title='Roulette', description=msg, color=0x008080)
            embed.set_author(name=f"Ref {cliname()}", icon_url=client.user.avatar_url)
            embed.set_footer(text = "Ultrabot by Pradyun Narkadamilli")
            await ctx.send(embed=embed)
            try:
                def check(text):
                    return text.author == challenger and text.content.endswith(prefix)

                msg = await client.wait_for('message', check=check, timeout=20)
            except asyncio.TimeoutError:
                msg = 'Too Late! There shall be no roulette!'
                embed=discord.Embed(title='Roulette', description=msg, color=0x008080)
                embed.set_author(name=f"Ref {cliname()}", icon_url=client.user.avatar_url)
                embed.set_footer(text = "Ultrabot by Pradyun Narkadamilli")
                await ctx.send(embed=embed)
                return
            if msg.content.lower() == 'yes' + prefix:
                msg = 'Looks like we have shootout coming up boys...'
                embed=discord.Embed(title='Roulette', description=msg, color=0x008080)
                embed.set_author(name=f"Ref {cliname()}", icon_url=client.user.avatar_url)
                embed.set_footer(text = "Ultrabot by Pradyun Narkadamilli")
                await ctx.send(embed=embed)
                category = client.get_channel(jsonfo["roulette_id"])
                name = 'roulette' + str(roulette_count)
                role = await guild.create_role(name=name, colour=discord.Colour(16711935))
                roulette_count += 1
                await ctx.author.add_roles(role, reason='Russian Roulette')
                await challenger.add_roles(role, reason='Russian Roulette')
                overwrites = {
                    role: discord.PermissionOverwrite(send_messages=True),
                    discord.utils.get(guild.roles, name='Verified Hackers'): discord.PermissionOverwrite(
                        send_messages=False, read_messages=True),
                    guild.default_role: discord.PermissionOverwrite(read_messages=False),
                }
                channel = await guild.create_text_channel(name, overwrites=overwrites, category=category)
                flipped = False
                shot = False
                msg = f'There must be a coin flip to determine the first to shoot... and perhaps get shot...\nHe (or She) who has declared the challenge shall have the choice of the flip... {ctx.author.mention}, enter h for Heads, and t for Tails. Capitalization won\'t matter! You have 30 seconds. Invalid input will not be registered.'
                embed=discord.Embed(title='Roulette', description=msg, color=0x008080)
                embed.set_author(name=f"Ref {cliname()}", icon_url=client.user.avatar_url)
                embed.set_footer(text = "Ultrabot by Pradyun Narkadamilli")
                await channel.send(embed=embed)
                flip = await check_response(channel, ['h', 't'], ctx.author)
                if flip is not None:
                    flipped = True

                if not flipped:
                    msg = 'Sorry...but time ran out!'
                    embed=discord.Embed(title='Roulette', description=msg, color=0x008080)
                    embed.set_author(name=f"Ref {cliname()}", icon_url=client.user.avatar_url)
                    embed.set_footer(text = "Ultrabot by Pradyun Narkadamilli")
                    await channel.send(embed=embed)
                    await asyncio.sleep(10)
                    await role.delete()
                    await channel.delete()
                    roulette_count -= 1
                    return

                coinflip = random.randint(1, 2)
                if flip.content.lower() == 'h':
                    flip = 1

                elif flip.content.lower() == 't':
                    flip = 2

                if coinflip == flip:
                    p1 = ctx.author
                    p2 = challenger
                else:
                    p1 = challenger
                    p2 = ctx.author

                if coinflip == 1:
                    msg = 'The coin landed on heads.'
                    await roulsend(msg, channel)
                elif coinflip == 2:
                    msg = 'The coin landed on tails.'
                    await roulsend(msg, channel)
                await asyncio.sleep(2)
                await roulsend(f'Looks like {p1.mention} will shoot the gun first...', channel)
                await asyncio.sleep(2)
                await roulsend('Let the games begin!', channel)
                await roulsend(f'{p1.mention}, You now have the privilege of choosing the number of chambers in your gun... only one bullet will be present... Enter your choice. Your number must be 6 or higher', channel)
                ammo = await number_response(channel, p1)
                while ammo is False or ammo < 6:
                    await roulsend('That input was invalid... care to try again?', channel)
                    ammo = await number_response(channel, p1)
                clip = []
                for i in range(ammo):
                    clip.append(0)
                clip[random.randint(0, (ammo-1))] = 1
                numshot = 1
                while not shot:
                    await roulsend(f'{p1.mention}, it\'s your turn to fire...\nEnter a number at or below {str(ammo)}... This is the number of times you will shoot your gun. Non-number input will not be registered.', channel)
                    shot1 = await number_response(channel, p1)
                    while shot1 is False or shot1 > ammo:
                        await roulsend('That input was invalid... care to try again?', channel)
                        shot1 = await number_response(channel, p1)
                    for i in range(shot1):
                        fire = random.randint(0, ammo-1)
                        ammo -= 1
                        if clip[fire] == 1:
                            await roulsend(f"I'm sorry {p1.mention}... But you were shot.", channel)
                            await asyncio.sleep(10)
                            if p1.id  != client.user.id:
                                if str(p2.id) in leadmembers:
                                    rawleaders[str(p2.id)] += 50
                                    leaders[:] = (value for value in leaders if value[0] != str(p2.id))
                                    leaders.append([str(p2.id), rawleaders[str(p2.id)]])
                                    leaders = sorted(leaders, key=itemgetter(1), reverse=True)
                                    db.collection(u'leaderboard').document(u'leaderboard').set(rawleaders)
                                elif str(p2.id) not in leadmembers:
                                    rawleaders[str(p2.id)] = 50
                                    leadmembers.append(str(p2.id))
                                    leaders.append([str(p2.id), rawleaders[str(p2.id)]])
                                    leaders = sorted(leaders, key=itemgetter(1), reverse=True)
                                    db.collection(u'leaderboard').document(u'leaderboard').set(rawleaders)
                            shot = True
                            break
                        elif clip[fire] == 0:
                            await roulsend(f'Chamber {str(numshot)} did not kill you {p1.mention}...', channel)
                            await asyncio.sleep(3)
                            clip.pop(fire)
                            numshot += 1
                    if shot:
                        break
                    await roulsend(f'{p2.mention}, it\'s your turn to fire...\nEnter a number at or below {str(ammo)}... This is the number of times you will shoot your gun. Non-number input will not be registered.', channel)
                    shot2 = await number_response(channel, p2)
                    while shot2 is None or shot2 > ammo:
                        await roulsend('That input was invalid... care to try again?', channel)
                        shot2 = await number_response(channel, p2)
                    for i in range(shot2):
                        fire = random.randint(0, ammo - 1)
                        ammo -= 1
                        if clip[fire] == 1:
                            await roulsend(
                                f"I'm sorry {p2.mention}... But you were shot.", channel)
                            await asyncio.sleep(10)
                            if p2.id  != client.user.id:
                                if str(p1.id) in leadmembers:
                                    rawleaders[str(p1.id)] += 50
                                    leaders[:] = (value for value in leaders if value[0] != str(p1.id))
                                    leaders.append([str(p1.id), rawleaders[str(p1.id)]])
                                    leaders = sorted(leaders, key=itemgetter(1), reverse=True)
                                    db.collection(u'leaderboard').document(u'leaderboard').set(rawleaders)
                                elif str(p1.id) not in leadmembers:
                                    rawleaders[str(p1.id)] = 50
                                    leadmembers.append(str(p1.id))
                                    leaders.append([str(p1.id), rawleaders[str(p1.id)]])
                                    leaders = sorted(leaders, key=itemgetter(1), reverse=True)
                                    db.collection(u'leaderboard').document(u'leaderboard').set(rawleaders)
                            shot = True
                            break
                        elif clip[fire] == 0:
                            await roulsend(f'Chamber {str(numshot)} did not kill you {p2.mention}...', channel)
                            await asyncio.sleep(3)
                            clip.pop(fire)
                            numshot += 1

                await role.delete()
                await channel.delete()
                roulette_count -= 1
            else:
                await roulsend('Chicken!', ctx)
                return
        else:
            await roulsend('Did you just try to challenge yourself?', ctx)
            return


class Utils(commands.Cog, name='Utils'):
    def __init__(self, bot):
        self.bot = bot


    @commands.command(brief='Ping Pong Right Wrong', description='Check response time of bot.')
    async def ping(self, ctx):
        """ Pong! """
        ping = client.latency
        embed=discord.Embed(title='Pong', description=f"{int(ping)}ms response time.", color=0x800080)
        embed.set_author(name="SportBot", icon_url=client.user.avatar_url)
        embed.set_footer(text = "Ultrabot by Pradyun Narkadamilli")
        await ctx.send(embed=embed)
        print(f'Ping {int(ping)}ms')
    
    @commands.command(brief='[BLEEP]', description='Censor certain words or phrases.')
    async def blacklist(self, ctx, *, phrase=None):
        global blacklist
        global db

        if not ctx.author.guild_permissions.administrator and phrase:
            embed=discord.Embed(title='Blacklist', description="Your permissions are insufficient.", color=0x800080)
            embed.set_author(name="SwearBot", icon_url=client.user.avatar_url)
            embed.set_footer(text = "Ultrabot by Pradyun Narkadamilli")
            await ctx.send(embed=embed)
            return
        elif phrase is None:
            if blacklist != []:
                words = ''
                for i in blacklist:
                    words += f'{i}\n'
                words = words.strip()
                embed=discord.Embed(title='Blacklist', description=f"You can't say these phrases\n{words}", color=0x800080)
                embed.set_author(name="SwearBot", icon_url=client.user.avatar_url)
                embed.set_footer(text = "Ultrabot by Pradyun Narkadamilli")
                await ctx.send(embed=embed)
            else:
                embed=discord.Embed(title='Blacklist', description=f"There are no words in the blacklist.", color=0x800080)
                embed.set_author(name="SwearBot", icon_url=client.user.avatar_url)
                embed.set_footer(text = "Ultrabot by Pradyun Narkadamilli")
                await ctx.send(embed=embed)
            return
        elif not checkint(phrase) and ctx.author.guild_permissions.administrator:
            blacklist.append(phrase)
            embed=discord.Embed(title='Blacklist', description=f"Your phrase was added to the blacklist", color=0x800080)
            embed.set_author(name="SwearBot", icon_url=client.user.avatar_url)
            embed.set_footer(text = "Ultrabot by Pradyun Narkadamilli")
            await ctx.send(embed=embed)
            db.collection('blacklist').document('blacklist').set({u'blacklist':blacklist})

        elif checkint(phrase) and ctx.author.guild_permissions.administrator:
            try:
                blacklist.pop(int(phrase) - 1)
                embed=discord.Embed(title='Blacklist', description=f"Phrase {int(phrase)} was deleted from the blacklist", color=0x800080)
                embed.set_author(name="SwearBot", icon_url=client.user.avatar_url)
                embed.set_footer(text = "Ultrabot by Pradyun Narkadamilli")
                await ctx.send(embed=embed)
                db.collection('blacklist').document('blacklist').set({u'blacklist':blacklist})
            except:
                embed=discord.Embed(title='Blacklist', description=f"The number supplied was too high.", color=0x800080)
                embed.set_author(name="SwearBot", icon_url=client.user.avatar_url)
                embed.set_footer(text = "Ultrabot by Pradyun Narkadamilli")
                await ctx.send(embed=embed)


    @commands.command(brief="Muzzle that pesky bloke.", description="Admins only! There's that one guy we all hate... just shut him up with this thing.")
    async def mute(self, ctx, *, muter: discord.Member=None):
        mute = discord.utils.get(ctx.guild.roles, name='Mute')
        verif = discord.utils.get(ctx.guild.roles, name='Verified Hackers') 
        if muter==None:
            mutes = ""
            for mem in mute.members:
                mutes += mem.mention + "\n"
            mutes = mutes.strip()
            embed=discord.Embed(title='Mute List', description=mutes, color=0x800080)
            embed.set_author(name="GagBot", icon_url=client.user.avatar_url)
            embed.set_footer(text = "Ultrabot by Pradyun Narkadamilli")
            await ctx.send(embed=embed)
            return
        if not ctx.author.guild_permissions.manage_roles:
            embed=discord.Embed(title='Error', description="You can't change roles... Insufficient perms!", color=0x800080)
            embed.set_author(name="GagBot", icon_url=client.user.avatar_url)
            embed.set_footer(text = "Ultrabot by Pradyun Narkadamilli")
            await ctx.send(embed=embed)
            return

        if verif not in muter.roles and mute not in muter.roles:
            embed=discord.Embed(title='Error', description=f"{muter.mention} isn't verified!", color=0x800080)
            embed.set_author(name="GagBot", icon_url=client.user.avatar_url)
            embed.set_footer(text = "Ultrabot by Pradyun Narkadamilli")
            await ctx.send(embed=embed)
            return

        if mute not in muter.roles:
            await muter.add_roles(mute, reason='Shut up!')
            await muter.remove_roles(verif, reason='Shut up!')
            embed=discord.Embed(title='Mute', description=f"Muted {muter.mention}", color=0x800080)
            embed.set_author(name="GagBot", icon_url=client.user.avatar_url)
            embed.set_footer(text = "Ultrabot by Pradyun Narkadamilli")
            await ctx.send(embed=embed)
            return

        elif mute in muter.roles:
            await muter.remove_roles(mute, reason="No more shut up!")
            await muter.add_roles(verif, reason="No more shut up!")
            embed=discord.Embed(title='Unmute', description=f"Unmuted {muter.mention}", color=0x800080)
            embed.set_author(name="GagBot", icon_url=client.user.avatar_url)
            embed.set_footer(text = "Ultrabot by Pradyun Narkadamilli")
            await ctx.send(embed=embed)
            return




        


    @commands.command(brief='Displays this command.', description='The help command\'s usage portion can be a little difficult to understand.\nThe [] means that you can use any of the command aliases, or the argument is optional.\n<> indicates that an argument must be supplied.')
    async def help(self, ctx, *, cmdcog=None):
    #Let's see if the user supplied an argument! If not, let's send the default help text.
        if cmdcog is None:
            embed=discord.Embed(title='Help', description=f"I see that you've come seeking help... look no further!\nTo get help with a command, do {client.command_prefix}help <command>.\nIf you want help with a category, do {client.command_prefix}help <category> with any of the below categories:\n**Code, Games, Misc, Music, Utils**\n\n There is a separate help page for the antispam system, which you can access with {client.command_prefix}help Antispam.", color=0x800080)
            embed.set_author(name="IIT IT", icon_url=client.user.avatar_url)
            embed.set_footer(text = "Ultrabot by Pradyun Narkadamilli")
            await ctx.send(embed=embed)
            return

        if cmdcog.capitalize() == 'Antispam':
            desc = """Ultrabot has built in Antispam! As far as Ultrabot cares, if you send a message within 5 seconds of the last one, you get a 'strike'.
After 20 strikes, you will get a cooldown,  and then you will have your strikes reset.
Another way to reset your strikes is by waiting one minute, without sending any messages, in which case Ultrabot will reset.
Every offense doubles your timeout. The initial timeout is 5 minutes. The second offense goes to 10 minutes, third goes to 20 minutes, etc.
After 7 offenses, you will get kicked. Rejoin the server and get an 8th offense, and it results in a ban.
Additionally, there is a blacklist system as well.
The blacklist system has no repercussions, but if someone (not an admin) sends a message with a blacklisted word, it will be deleted."""
            embed=discord.Embed(title="Antispam", description=desc, color=0x800080)
            embed.set_author(name="IIT IT", icon_url=client.user.avatar_url)
            embed.set_footer(text = "Ultrabot by Pradyun Narkadamilli")
            await ctx.send(embed=embed)


        posscog = client.get_cog(cmdcog.capitalize())
        if posscog is not None:
            if len(posscog.get_commands())>0:
                embed = cogster(posscog)
                await ctx.send(embed=embed)
                return
        posscmd = client.get_command(cmdcog.capitalize())
        if posscmd is not None:
            desc = f'{posscmd.description}'
            desc = f'{desc}\n{usage(posscmd)}'
            embed=discord.Embed(title=posscmd.name, description=desc, color=0x800080)
            embed.set_author(name="IIT IT", icon_url=client.user.avatar_url)
            embed.set_footer(text = "Ultrabot by Pradyun Narkadamilli")
            await ctx.send(embed=embed)
            return
        embed=discord.Embed(title='Help', description='That\'s weird... I can\'t find a Category or Command with that name! Try again!', color=0x800080)
        embed.set_author(name="IIT IT", icon_url=client.user.avatar_url)
        embed.set_footer(text = "Ultrabot by Pradyun Narkadamilli")
        await ctx.send(embed=embed)



    @commands.command(brief='Need assistance? Look no further.', description='Just some basic steps on garnering assistance, if you need it.')
    async def assist(self, ctx):
        mentoring = client.get_channel(jsonfo["code_help_id"])
        msg = "Don't worry {0.author.mention}. We're here for you!\n".format(ctx) + "\nIf you're having code-related issues, head on over to {1.mention}, where you can get some help with your problems.\nIf you have questions about a hackathon, please direct DM one of the organizers, and they will put you in touch with the appropriate authority.\nFor other miscellaneous queries, please DM Pradyun.".format(prefix, mentoring)
        embed=discord.Embed(title='Help', description=msg, color=0x800080)
        embed.set_author(name="IIT IT", icon_url=client.user.avatar_url)
        embed.set_footer(text = "Ultrabot by Pradyun Narkadamilli")
        await ctx.send(embed=embed)

    @commands.command(hidden=True)
    async def update(self, ctx):
        global rawleaders
        global playlists
        global leaders


        await ctx.message.delete()
        rawleaders = []
        leaders = []
        playlists = []

        leadercoll = db.collection(u'leaderboard')
        leaderboard = leadercoll.get()
        for i in leaderboard:
            raw = i.to_dict()
            rawleaders.append(raw)

        leadmembers = list(rawleaders[0].keys())
        rawleaders = rawleaders[0]

        for i in leadmembers:
            scoring =[i, rawleaders[i]]
            leaders.append(scoring)

        leaders = sorted(leaders, key=itemgetter(1), reverse=True)


        playcoll = db.collection(u'playlists')
        rawplay = playcoll.get()
        for i in rawplay:
            raw = i.to_dict()
            playlists.append(raw)

        playlists = playlists[0]


    @commands.command(hidden=True)
    async def prefix(self, ctx):
        await ctx.message.delete()
        # Is the User of appropriate rank?
        if ctx.author.guild_permissions.administrator:
            # Function referenced in wait for message. Checks if user sent message in private channel.
            author = ctx.author
            def check(text):
                return type(text.channel) is discord.DMChannel and text.author == author

            msg = 'You have selected the prefix option. This allows you to change your prefix of a command.\nPlease enter your new prefix.\nEnter anything above 1 character in order to cancel this.'
            await ctx.author.send(msg)
            bypasses.append(ctx.author)
            try:
                msg = await client.wait_for('message', check=check, timeout=30)
            except:
                await ctx.author.send('Too Late')
                return
            bypasses[:] = (value for value in bypasses if value != ctx.author)
            if msg is None:
                await ctx.author.send('Too late!')
            elif len(msg.content) == 1:
                prefix = msg.content
                client.command_prefix = msg.content
                await ctx.author.send('Prefix has been changed to ' + prefix)
                await ctx.send(
                    '{0.author.mention}'.format(ctx) + ' has changed my prefix to "' + prefix + '"!')
                await client.change_presence(activity=discord.Game(name=prefix + 'help'))
            elif len(msg.content) > 1:
                await ctx.author.send('That prefix was too long!')
            else:
                await ctx.author.send('Try again later?')
        else:
            msg = "You don't have the permissions for that!"
            await ctx.author.send(msg)



class Code(commands.Cog, name='Code'):
    def __init__(self, bot):
        self.bot = bot


    @commands.command(aliases=['runthon', 'pyrun'], brief='A python runtime, in Discord.', description='Execute this command, DM the bot your code, and you can see it execute! Great for debugging errors and such.')
    async def python(self, ctx):
        msg = 'Hey there! Do you mind typing in your python code for me? All you need to do is *```python*,a newline, your code, another newline, then *```*'
        await runsend(msg, ctx.author)
        try:
            def check(text):
                return type(text.channel) is discord.DMChannel and text.author == ctx.author and bool(re.search("```python\n([\s\S]*?)\n```", text.content))
            msg = await client.wait_for('message', check=check, timeout=100)
        except asyncio.TimeoutError:
            await runsend('Too Late! If you sent a message, it may not have been formatted correctly.', ctx.author)
            return
        code = re.findall('```python\n([\s\S]*?)\n```', msg.content)
        code = code[0]
        inputs = re.findall('input\(\'([\s\S]*?)\'\)', code)
        if re.findall('input\(\"([\s\S]*?)\"\)', code) is not None:
            r = re.findall('input\(\"([\s\S]*?)\"\)', code)
            for i in r:
                inputs.append(i)
        file = f'{ctx.author.id}.txt'
        for i in inputs:
            f = open(f'{ctx.author.id}.txt', 'w')
            f.write(code)
            f.close()
            try:
                out = await asyncio.wait_for(pyrun(file), timeout=15.0)
                if out.startswith(i):
                    msg = f'Your program demanded an input! Please respond to the following within 30 seconds:\n{out}'
                    await runsend(msg, ctx.author)
                    try:
                        def check(text):
                            return type(text.channel) is discord.DMChannel and text.author == ctx.author

                        msg = await client.wait_for('message', check=check, timeout=30)
                    except asyncio.TimeoutError:
                        await runsend('Too Late!', ctx.author)
                        return
                    code = code.replace(f'input(\'{i}\')', f'\'{msg.content}\'', 1)

            except asyncio.TimeoutError:
                await runsend('Your program took too long to resolve.', ctx.author)
                os.remove(file)
                return

        f = open(f'{ctx.author.id}.txt', 'w')
        f.write(code)
        f.close()
        file = f'{ctx.author.id}.txt'
        try:
            out = await asyncio.wait_for(pyrun(file), timeout=15.0)
            msg = f'Your program \'s output was the following:\n{out}'
            await runsend(msg, ctx.author)

        except asyncio.TimeoutError:
            await runsend('Your program took too long to resolve.', ctx.author)

        os.remove(file)

    @commands.command(aliases=['pyerror', 'pyhelp'], brief='A way to share errors in python.', description='Execute this command, DM the bot your code, and the bot will DM you the program output. After that, the bot will share the program txt as well as the program output to the code-help channel.')
    async def pyror(self, ctx):
        msg = 'Hey there! Do you mind typing in your python code for me? All you need to do is *```python*,a newline, your code, another newline, then *```*'
        await runsend(msg, ctx.author)
        try:
            def check(text):
                return type(text.channel) is discord.DMChannel and text.author == ctx.author and bool(
                    re.search("```python\n([\s\S]*?)\n```", text.content))

            msg = await client.wait_for('message', check=check, timeout=100)
        except asyncio.TimeoutError:
            await runsend('Too Late! If you sent a message, it may not have been formatted correctly.', ctx.author)
            return
        code = re.findall('```python\n([\s\S]*?)\n```', msg.content)
        code = code[0]
        inputs = re.findall('input\(\'([\s\S]*?)\'\)', code)
        if re.findall('input\(\"([\s\S]*?)\"\)', code) is not None:
            r = re.findall('input\(\"([\s\S]*?)\"\)', code)
            for i in r:
                inputs.append(i)
        file = f'{ctx.author.id}.txt'
        for i in inputs:
            f = open(f'{ctx.author.id}.txt', 'w')
            f.write(code)
            f.close()
            try:
                out = await asyncio.wait_for(pyrun(file), timeout=15.0)
                if out.startswith(i):
                    msg = f'Your program demanded an input! Please respond to the following within 30 seconds:\n{out}'
                    await runsend(msg, ctx.author)
                    try:
                        def check(text):
                            return type(text.channel) is discord.DMChannel and text.author == ctx.author

                        msg = await client.wait_for('message', check=check, timeout=30)
                    except asyncio.TimeoutError:
                        await ctx.author.send('Too Late!')
                        return
                    code = code.replace(f'input(\'{i}\')', f'\'{msg.content}\'', 1)

            except asyncio.TimeoutError:
                await runsend('Your program took too long to resolve.', ctx.author)
                os.remove(file)
                return

        f = open(f'{ctx.author.id}.txt', 'w')
        f.write(code)
        f.close()
        file = f'{ctx.author.id}.txt'
        try:
            out = await asyncio.wait_for(pyrun(file), timeout=15.0)
            msg = f'Your program \'s output was the following:\n{out}'
            await runsend(msg, ctx.author)
            filer = discord.File(f'{ctx.author.id}.txt', filename=f'code.py')
            msg = f'{ctx.author.mention} needs help with his python code! Can you someone help him? His code is in the txt file below, and his program output as well.\nProgram output:\n{out}'
            mentoring = client.get_channel(jsonfo["code_help_id"])
            embed=discord.Embed(title='Runtime', description=msg, color=0xffff00)
            embed.set_author(name="Server", icon_url=client.user.avatar_url)
            await mentoring.send(embed=embed, file=filer)

        except asyncio.TimeoutError:
            await runsend('Your program took too long to resolve.', ctx.author)

        os.remove(file)


    @commands.command(aliases=['jahelp', 'jahrule','coffassist'], brief='A way to share your java problems.', description='Execute this command, DM the bot your code, and you can see it execute! Great for debugging errors and such.')
    async def javerror(self, ctx):
        msg = 'Hey there! Do you mind typing in your java code for me? All you need to do is *```java*,a newline, your code, another newline, then *```*. Please note that as of now, we do not support graphical elements or user input. User input is coming soon though!\nP.S: Make sure that your programs\'s public class is named something odd! This way, we can ensure that your program doesn\'t get mixed up with somebody else\'s.'
        await runsend(msg, ctx.author)
        try:
            def check(text):
                return type(text.channel) is discord.DMChannel and text.author == ctx.author and bool(re.search("```java\n([\s\S]*?)\n```", text.content))
            msg = await client.wait_for('message', check=check, timeout=100)
        except asyncio.TimeoutError:

            await runsend('Too Late! If you sent a message, it may not have been formatted correctly.', ctx.author)
            return
        code = re.findall("```java\n([\s\S]*?)\n```", msg.content)
        code = code[0]
        try:
            filename = re.findall('(?:public\s)(?:class|interface|enum)\s([^\n\s]*)', code)[0]
        except:
            await ctx.author.send('You sure you structured your code properly?')
            return
        f = open(f'{filename}.java', 'w')
        f.write(code)
        f.close()
        file = f'{filename}.java'
        try:
            out = await asyncio.wait_for(javac(file), timeout=15.0)
            if out is not None:
                if out[0] == 'error' and out[1] != 'Picked up JAVA_TOOL_OPTIONS: -Xmx300m -Xss512k -XX:CICompilerCount=2 -Dfile.encoding=UTF-8 \n':
                    out[1] = out[1].replace('Picked up JAVA_TOOL_OPTIONS: -Xmx300m -Xss512k -XX:CICompilerCount=2 -Dfile.encoding=UTF-8 \n', '')
                    msg = f'Compilation of your program returned the following:\n{out[1]}'
                    await runsend(msg, ctx.author)
                    finout = f'{ctx.author.mention} needs help with his Java program! Attached below are his compiler output, as well as his code itself.\n{out[1]}'
                    filer = discord.File(f'{filename}.java', filename=f'code.java')
                    mentoring = client.get_channel(jsonfo["code_help_id"])
                    embed=discord.Embed(title='Runtime', description=finout, color=0xffff00)
                    embed.set_author(name="Server", icon_url=client.user.avatar_url)
                    await mentoring.send(embed=embed, file=filer)
                    os.remove(file)
                    return
                else:
                    msg = 'Compilation was successful'
                    await runsend(msg, ctx.author)
            else:
                msg = 'Compilation was successful'
            if True:    
                try:
                    out = await asyncio.wait_for(runjava(filename), timeout=15.0)
                    if out is not None:
                        msg = f'Your program returned:\n {out}'
                    else:
                        msg = 'Your program evaluated successfully, but did not return anything.'

                    finout = f'{ctx.author.mention} needs help with his Java program! Attached below are his program output, as well as his code itself (compiled classfile and src code).\n{out}'
                    filer = discord.File(f'{filename}.java', filename=f'{filename}.java')
                    javile = discord.File(f'{filename}.class', filename=f'{filename}.class')
                    await runsend(msg, ctx.author)
                    mentoring = client.get_channel(jsonfo["code_help_id"])
                    embed=discord.Embed(title='Runtime', description=finout, color=0xffff00)
                    embed.set_author(name="Server", icon_url=client.user.avatar_url)
                    await mentoring.send(embed=embed, files=[filer, javile])
                except asyncio.TimeoutError:
                    await runsend('Your program took loo long to run!', ctx.author)
        except asyncio.TimeoutError:
            await runsend('Your program took too long to compile!', ctx.author)
            os.remove(file)
            return

        os.remove(file)
        os.remove(f'{filename}.class')


    @commands.command(aliases=['javac', 'jarun','coffee'], brief='A java compiler/runtime, in Discord.', description='Execute this command, DM the bot your code, and you can see it execute! Great for debugging errors and such.')
    async def java(self, ctx):
        msg = 'Hey there! Do you mind typing in your java code for me? All you need to do is *```java*,a newline, your code, another newline, then *```*. Please note that as of now, we do not support graphical elements or user input. User input is coming soon though!\nP.S: Make sure that your programs\'s public class is named something odd! This way, we can ensure that your program doesn\'t get mixed up with somebody else\'s.'
        await runsend(msg, ctx.author)
        try:
            def check(text):
                return type(text.channel) is discord.DMChannel and text.author == ctx.author and bool(re.search("```java\n([\s\S]*?)\n```", text.content))
            msg = await client.wait_for('message', check=check, timeout=100)
        except asyncio.TimeoutError:

            await runsend('Too Late! If you sent a message, it may not have been formatted correctly.', ctx.author)
            return
        code = re.findall("```java\n([\s\S]*?)\n```", msg.content)
        code = code[0]
        try:
            filename = re.findall('(?:public\s)(?:class|interface|enum)\s([^\n\s]*)', code)[0]
        except:
            await ctx.author.send('You sure you structured your code properly?')
            return
        f = open(f'{filename}.java', 'w')
        f.write(code)
        f.close()
        file = f'{filename}.java'
        try:
            out = await asyncio.wait_for(javac(file), timeout=15.0)
            if out is not None:
                if out[0] == 'error' and out[1] != 'Picked up JAVA_TOOL_OPTIONS: -Xmx300m -Xss512k -XX:CICompilerCount=2 -Dfile.encoding=UTF-8 \n':
                    out[1] = out[1].replace('Picked up JAVA_TOOL_OPTIONS: -Xmx300m -Xss512k -XX:CICompilerCount=2 -Dfile.encoding=UTF-8 \n', '')
                    msg = f'Compilation of your program returned the following:\n{out[1]}'
                    await ctx.author.send(msg)
                    os.remove(file)
                    return
                else:
                    msg = 'Compilation was successful'
                    await runsend(msg, ctx.author)
            else:
                msg = 'Compilation was successful'
                await runsend(msg, ctx.author)
            if True:    
                try:
                    out = await asyncio.wait_for(runjava(filename), timeout=15.0)
                    if out is not None:
                        msg = f'Your program returned:\n {out}'

                    else:
                        msg = 'Your program evaluated successfully, but did not return anything.'
                    
                    await runsend(msg, ctx.author)

                except asyncio.TimeoutError:
                    await ctx.author.send('Your program took loo long to run!')
        except asyncio.TimeoutError:
            await runsend('Your program took too long to compile!', ctx.author)
            os.remove(file)
            return
        

        os.remove(file)
        os.remove(f'{filename}.class')

    '''@commands.command(aliases=['runc', 'ifailedfrench', 'gcc'], brief='A C compiler, in Discord.', description='Execute this command, DM the bot your code, and you can see it execute! Great for debugging errors and such.')
    async def crun(self, ctx):
        msg = 'Hey there! Do you mind typing in your C code for me? All you need to do is *```c*,a newline, your code, another newline, then *```*'
        await ctx.author.send(msg)
        try:
            def check(text):
                print(text.content)
                return type(text.channel) is discord.DMChannel and text.author == ctx.author and bool(re.search("```c\n([\s\S]*?)\n```", text.content))
            msg = await client.wait_for('message', check=check, timeout=100)
        except asyncio.TimeoutError:
            await ctx.author.send('Too Late! If you sent a message, it may not have been formatted correctly.')
            return
        code = re.findall('```c\n([\s\S]*?)\n```', msg.content)
        code = code[0]
        f = open(f'{ctx.author.id}.c', 'w')
        f.write(code)
        f.close()
        file = f'{ctx.author.id}'
        try:
            out = await asyncio.wait_for(compilec(file), timeout=15.0)
            if out is not None:
                msg = f'Your program\'s compilation returned the following:\n{out}'
                await ctx.author.send(msg)
                if not os.path.isfile(f'{file}.out'):
                    os.remove(f'{file}.c')
                    return
            else:
                msg = f'Your program compiled fine!'
            await ctx.author.send(msg)
            try:
                out = await asyncio.wait_for(runc(file), timeout=15.0)
                msg = f'Your program outputted the following:\n{out}'
                await ctx.author.send(msg)
            except asyncio.TimeoutError:
                await ctx.author.send('Your program took too long to resolve.')
                os.remove(f'{file}.c')
                os.remove(f'{file}.out')
                return

        except asyncio.TimeoutError:
            await ctx.author.send('Your compilation took too long to resolve.')
            os.remove(f'{file}.c')
            return

        os.remove(f'{file}.c')
        os.remove(f'{file}.out')

    @commands.command(aliases=['runcpp', 'cpp', 'c++', 'g++'], brief='A C compiler, in Discord.', description='Execute this command, DM the bot your code, and you can see it execute! Great for debugging errors and such.')
    async def cpprun(self, ctx):
        msg = 'Hey there! Do you mind typing in your C++ code for me? All you need to do is *```cpp*,a newline, your code, another newline, then *```*'
        await ctx.author.send(msg)
        try:
            def check(text):
                print(text.content)
                return type(text.channel) is discord.DMChannel and text.author == ctx.author and bool(re.search("```cpp\n([\s\S]*?)\n```", text.content))
            msg = await client.wait_for('message', check=check, timeout=100)
        except asyncio.TimeoutError:
            await ctx.author.send('Too Late! If you sent a message, it may not have been formatted correctly.')
            return
        code = re.findall('```cpp\n([\s\S]*?)\n```', msg.content)
        code = code[0]
        f = open(f'{ctx.author.id}.cpp', 'w')
        f.write(code)
        f.close()
        file = f'{ctx.author.id}'
        try:
            out = await asyncio.wait_for(compilecpp(file), timeout=15.0)
            if out is not None:
                msg = f'Your program\'s compilation returned the following:\n{out}'
                await ctx.author.send(msg)
                if not os.path.isfile(f'{file}.out'):
                    os.remove(f'{file}.cpp')
                    return
            else:
                msg = f'Your program compiled fine!'
            await ctx.author.send(msg)
            try:
                out = await asyncio.wait_for(runcpp(file), timeout=15.0)
                msg = f'Your program outputted the following:\n{out}'
                await ctx.author.send(msg)
            except asyncio.TimeoutError:
                await ctx.author.send('Your program took too long to resolve.')
                os.remove(f'{file}.cpp')
                os.remove(f'{file}.out')
                return

        except asyncio.TimeoutError:
            await ctx.author.send('Your compilation took too long to resolve.')
            os.remove(f'{file}.cpp')
            return

        os.remove(f'{file}.cpp')
        os.remove(f'{file}.out')'''


class CommandErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """The event triggered when an error is raised while invoking a command.
        ctx   : Context
        error : Exception"""

        if hasattr(ctx.command, 'on_error'):
            return

        ignored = (commands.CommandNotFound)
        error = getattr(error, 'original', error)
        if isinstance(error, ignored) and isinstance(error, commands.MissingRequiredArgument) is not True:
            return

        elif isinstance(error, commands.UserInputError):
            embed=discord.Embed(title='Error', description=f"The argument supplied was invalid.", color=0x800080)
            embed.set_author(name="IIT IT", icon_url=client.user.avatar_url)
            embed.set_footer(text = "Ultrabot by Pradyun Narkadamilli")
            return await ctx.send(embed=embed)


        elif isinstance(error, commands.DisabledCommand):
            embed=discord.Embed(title='Error', description=f"That command has been disabled.", color=0x800080)
            embed.set_author(name="IIT IT", icon_url=client.user.avatar_url)
            embed.set_footer(text = "Ultrabot by Pradyun Narkadamilli")
            return await ctx.send(embed=embed)

        elif isinstance(error, commands.NoPrivateMessage):
            try:
                embed=discord.Embed(title='Error', description=f"That command can't be used in Direct Messages!", color=0x800080)
                embed.set_author(name="IIT IT", icon_url=client.user.avatar_url)
                embed.set_footer(text = "Ultrabot by Pradyun Narkadamilli")
                return await ctx.author.send(embed=embed)
            except:
                pass

        elif isinstance(error, commands.BadArgument):
            try:
                embed=discord.Embed(title='Error', description=f"That argument was invalid", color=0x800080)
                embed.set_author(name="IIT IT", icon_url=client.user.avatar_url)
                embed.set_footer(text = "Ultrabot by Pradyun Narkadamilli")
                return await ctx.send(embed=embed)
            except:
                pass

        elif isinstance(error, commands.MissingRequiredArgument):
            try:
                msg = f'{ctx.command} required an argument that you did not specify upon invocation. Try using `{client.command_prefix}help {ctx.command}` to see the proper usage.'
                embed=discord.Embed(title='Error', description=msg, color=0x800080)
                embed.set_author(name="IIT IT", icon_url=client.user.avatar_url)
                embed.set_footer(text = "Ultrabot by Pradyun Narkadamilli")
                return await ctx.send(embed=embed)
            except:
                pass

        print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)


class Misc(commands.Cog, name='Misc'):
    def __init__(self, bot):
        self.bot = bot


    @commands.command(brief="Quotes to live by. Or maybe not.", description="A reddit scraper that fetches quotes.")
    async def quotes(self, ctx):
        global advice
        i = advice.random()
        title = i.title
        author = i.author.name
        score = i.score
        ratio = i.upvote_ratio
        pfp = i.author.icon_img
        desc = f'Score: {score}\nUpvote Ratio: {int(ratio*100)}%'
        embed=discord.Embed(title=title, description=desc, color=0x1100ff)
        embed.set_author(name=author, icon_url=(pfp))
        embed.set_footer(text = 'Quotes from r/quotes')
        await ctx.send(embed=embed)


    @commands.command(brief="Are you very smart?", description="A bunch of idiots who think that they're smart")
    async def smart(self, ctx):
        global smartish
        i = smartish.random()
        title = i.title
        url = i.url
        author = i.author.name
        score = i.score
        ratio = i.upvote_ratio
        pfp = i.author.icon_img
        desc = f'Score: {score}\nUpvote Ratio: {int(ratio*100)}%'
        embed=discord.Embed(title=title, description=desc, color=0x1100ff)
        embed.set_author(name=author, icon_url=(pfp))
        embed.set_footer(text = 'Stupidity from r/iamverysmart')
        embed.set_image(url=url)
        await ctx.send(embed=embed)

    @commands.command(brief="It's time to c-c-c-c-cringe", description="We don't know if it's dank, but it's definitely a meme")
    async def meme(self, ctx):
        global memes
        i = memes.random()
        title = i.title
        url = i.url
        author = i.author.name
        score = i.score
        ratio = i.upvote_ratio
        pfp = i.author.icon_img
        desc = f'Score: {score}\nUpvote Ratio: {int(ratio*100)}%'
        embed=discord.Embed(title=title, description=desc, color=0x1100ff)
        embed.set_author(name=author, icon_url=(pfp))
        embed.set_footer(text = 'Memes from r/memes')
        embed.set_image(url=url)
        await ctx.send(embed=embed)


    @commands.command(brief="Time for the dankest memes out there...", description="This time, we're sure it's a dank meme.")
    async def dank(self, ctx):
        global dankmemes
        i = dankmemes.random()
        title = i.title
        url = i.url
        author = i.author.name
        score = i.score
        ratio = i.upvote_ratio
        pfp = i.author.icon_img
        desc = f'Score: {score}\nUpvote Ratio: {int(ratio*100)}%'
        embed=discord.Embed(title=title, description=desc, color=0x1100ff)
        embed.set_author(name=author, icon_url=(pfp))
        embed.set_footer(text = 'Memes from r/dankmemes')
        embed.set_image(url=url)
        await ctx.send(embed=embed)

    @commands.command(brief="Think thank thunk, I'm smellier than a skunk.", description="Think if you got something in the tank, but you think thoughts in the shower so they're showerthoughts.")
    async def think(self, ctx):
        global showerthoughts
        i = showerthoughts.random()
        title = i.title
        author = i.author.name
        score = i.score
        ratio = i.upvote_ratio
        pfp = i.author.icon_img
        desc = f'Score: {score}\nUpvote Ratio: {int(ratio*100)}%'
        embed=discord.Embed(title=title, description=desc, color=0x1100ff)
        embed.set_author(name=author, icon_url=(pfp))
        embed.set_footer(text = 'Revelations from r/showerthoughts')
        await ctx.send(embed=embed)    


    @commands.command(brief='Free hugs!', description='When you\'re down in the dumps, I\'m here for you. Or just use this for the memes.')
    async def hug(self,ctx):

        msg = "There there. I'm here for you. \n *hugs {0.author.mention}*".format(ctx)
        embed=discord.Embed(title='Therapy', description=msg, color=0x1100ff)
        embed.set_author(name=f"Therapist {cliname()}", icon_url=client.user.avatar_url)
        embed.set_footer(text = "Ultrabot by Pradyun Narkadamilli")
        await ctx.send(embed=embed)

    @commands.command(brief='Kuroshita!', description='Ever wanted to kill your worst enemy? Well now, you can...')
    async def kill(self, ctx, *, member: discord.Member):
        if ctx.author.id == member.id:
            msg = 'Suicide is not the way... call 119 for some Indian Tech support.'
            embed=discord.Embed(title='Therapy', description=msg, color=0x1100ff)
            embed.set_author(name=f"Therapist {cliname()}", icon_url=client.user.avatar_url)
            embed.set_footer(text = "Ultrabot by Pradyun Narkadamilli")
            await ctx.send(embed=embed)
            return

        elif ctx.author.id ==  210262966317219841:
            msg = f'Power be with {ctx.author.mention}... Under Pradyun\'s divine judgement, as his primary retainer, I say unto you, perish!\n*By the power of the Master Bolt, {member.mention} is struck down by tens of millions of volts.*'
            
        elif member.id == 210262966317219841:
            msg = f'Never try to kill my master... For your crimes, you shall be punished by death!\n***WHOOSH***\n*The severed head of {ctx.author.mention} falls to the ground*'

        elif member.id == client.user.id:
            msg = f'{ctx.author.mention}, your treachery will not go unnoticed... \n*Gun in hand, {member.mention} shoots {ctx.author.mention}*'

        else:
            msg = f'{ctx.author.mention}, you have been bestowed the trident of Poseidon. Use it wisely...\n*Armed with the Earth Shaker\'s power, {member.mention} is consumed by a jagged crevice.*'
        
        embed=discord.Embed(title='Undertaker', description=msg, color=0x000000)
        embed.set_author(name=f"{cliname()}", icon_url=client.user.avatar_url)
        embed.set_footer(text = "Ultrabot by Pradyun Narkadamilli")
        await ctx.send(embed=embed)

    @commands.command(name='repeat', aliases=['mimic', 'copy'], brief='I\'ll copy you all I want!', description='You say something, I\'ll say it too. Fun!')
    async def do_repeat(self, ctx, *, inp: str):
        await ctx.send(inp)

    @commands.command(brief='A little about me!')
    async def about(self, ctx):
        msg = "Hi there!\nI'm Ultrabot! I was designed by Pradyun Narkadamilli, using the discord.py library.\nMy code will be on github shortly! Just make sure you have a server to run me on!"
        embed=discord.Embed(title='Autobiography', description=msg, color=0x800080)
        embed.set_author(name=f"Tour Guide {cliname()}", icon_url=client.user.avatar_url)
        embed.set_footer(text = "Ultrabot by Pradyun Narkadamilli")
        await ctx.send(embed=embed)

    @commands.command(aliases=['hi','greetings','hey','sup'], brief='Catch a quick greeting from ya boi.')
    async def hello(self, ctx):
        msg = 'Hey there {0.author.mention}!'.format(ctx)
        embed=discord.Embed(title='Greetings', description=msg, color=0xffff00)
        embed.set_author(name=f"Jester {cliname()}", icon_url=client.user.avatar_url)
        embed.set_footer(text = "Ultrabot by Pradyun Narkadamilli")
        await ctx.send(embed=embed)


'''class Music(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    @commands.command(brief='Join channel')
    async def join(self, ctx):
        try:
            channel = ctx.author.voice.channel
        except:
            await ctx.send("You're not in a voice channel!")
            return
        try:
            await channel.connect()
        except discord.errors.ClientException:
            await ctx.guild.voice_client.disconnect()
            await channel.connect()

    @commands.command(brief='Leave Channel')
    async def leave(self, ctx):
        server  = ctx.guild
        try:
            await server.voice_client.disconnect()
        except:
            await ctx.send("I don't think I'm in a voice channel...")



    @commands.command(brief='Testing phase for now. Only sends first youtube search reult.')
    async def search(self, ctx, *, query: str):
        global player
        vc = ctx.guild.voice_client
        if vc is None:
            await ctx.send("I'm not in a voice channel... can you put me in one?")
            return
        query = urllib.parse.urlencode({'search_query':query})
        rawcon = urllib.request.urlopen(f'https://www.youtube.com/results?{query}')
        res  = re.findall('href=\"\\/watch\\?v=(.{11})', rawcon.read().decode())
        res = res[0]
        url = f'https://www.youtube.com/watch?v={res}'
        source = await YTDLSource.create_source(ctx, url, download=False)
        vc.play(source)'''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'before_options' : '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

async def mushelper(e, ctx):
    global songs
    global forced
    global source
    if e:
        embed=discord.Embed(title='Turntables', description='Player error: %s' % e, color=0xff8c00)
        embed.set_author(name=f"DJ {cliname()}", icon_url=client.user.avatar_url)
        await ctx.send(embed=embed)
        return
    if len(songs)>0 and ctx.voice_client is not None:
        async with ctx.typing():
            player = songs[0]['src']
            ctx.voice_client.play(player, after=lambda e: synchelper(e, ctx))
            source = random.randint(1111111111,9999999999)
            embed=discord.Embed(title='**Now Playing**', description='{}\n[{}]({})\n{}'.format(songs[0]['channtitle'] ,songs[0]['title'], songs[0]['url'], songs[0]['duration']), color=0xff8c00)
            embed.set_author(name=f"DJ {cliname()}", icon_url=client.user.avatar_url)
            embed.set_thumbnail(url=f"http://img.youtube.com/vi/{songs[0]['res']}/0.jpg")
            await ctx.send(embed=embed)
            songs.pop(0)
    elif ctx.voice_client is not None and not forced:
        embed=discord.Embed(title='Turntables', description="That's all folks... play some more jams!", color=0xff8c00)
        embed.set_author(name=f"DJ {cliname()}", icon_url=client.user.avatar_url)
        await ctx.send(embed=embed)
        await ctx.voice_client.disconnect()

    elif forced:
        forced = False

def synchelper(error, ctx):
    coro = mushelper(error, ctx)
    fut = asyncio.run_coroutine_threadsafe(coro, client.loop)


class Music(commands.Cog, name='Music'):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(brief='Make a playlist, or play yours!', description='This command has five modes: default (show your own playlist. For this you need no contextual argument.), show, play, add, and del. Those modes are invoked as a contextual argument, meaning that you must enter one of them where the mode argument is listed.')
    async def playlist(self, ctx, *, mode=None):
        global playlists
        global songs
        global forced

        if mode=='show':
            member = None
            embed=discord.Embed(title='Playlist', description="Type in the name of the user whose playlist you want to see, or just mention them.", color=0xff8c00)
            embed.set_author(name=f"DJ {cliname()}", icon_url=client.user.avatar_url)
            await ctx.send(embed=embed)
            author = ctx.author
            def check(text):
                return text.channel == ctx.channel and text.author == author
            try:
                rmember = await client.wait_for('message', check=check, timeout=20)
            except asyncio.TimeoutError:
                embed=discord.Embed(title='Playlist', description="Too late!", color=0xff8c00)
                embed.set_author(name=f"DJ {cliname()}", icon_url=client.user.avatar_url)
                await ctx.send(embed=embed)
                return
            try:
                member = await commands.MemberConverter().convert(ctx, rmember.content)
            except commands.UserInputError:
                pass
            if member:
                if str(member.id) not in list(playlists.keys()):
                    embed=discord.Embed(title='Playlist', description=f"It looks like {member.mention} doesn't have a playlist set up yet!", color=0xff8c00)
                    embed.set_author(name=f"DJ {cliname()}", icon_url=client.user.avatar_url)
                    await ctx.send(embed=embed)
                elif len(playlists[str(member.id)]) == 0:
                    embed=discord.Embed(title='Playlist', description=f"There's nothing in {member.mention}'s' playlist!", color=0xff8c00)
                    embed.set_author(name=f"DJ {cliname()}", icon_url=client.user.avatar_url)
                    await ctx.send(embed=embed)
                else:
                    playlist = playlists[str(member.id)]
                    msg = f"There\'s {len(playlist)} song(s) in {member.mention}'s playlist:"
                    for i in list(range(len(playlist))):
                        url = playlist[i]
                        res  = url.split('?v=')[1]
                        api_key=jsonfo["youtube_api_key"]
                        searchUrl=f"https://www.googleapis.com/youtube/v3/videos?id={res}&key="+api_key+"&part=snippet"
                        response = urllib.request.urlopen(searchUrl).read()
                        data = json.loads(response)
                        title = data['items'][0]['snippet']['title']
                        msg = msg+f"\n{i+1}:[{title}]({url})"

                    embed=discord.Embed(title='Playlist', description=msg, color=0xff8c00)
                    embed.set_author(name=f"DJ {cliname()}", icon_url=client.user.avatar_url)
                    await ctx.send(embed=embed)
            else:
                embed=discord.Embed(title='Playlist', description="I can't find a user with that name!", color=0xff8c00)
                embed.set_author(name=f"DJ {cliname()}", icon_url=client.user.avatar_url)
                await ctx.send(embed=embed)



        elif mode=='play':
            if str(ctx.author.id) in list(playlists.keys()):
                playlist = playlists[str(ctx.author.id)]
                songs = []
                if len(playlist) > 0:
                    if ctx.voice_client is not None:
                        if ctx.voice_client.is_paused() or ctx.voice_client.is_playing():
                            forced = True
                            ctx.voice_client.stop()
                    elif ctx.voice_client is None:
                        if ctx.author.voice:
                            await ctx.author.voice.channel.connect()
                        else:
                            await ctx.send(":no_entry_sign:  You are not connected to a voice channel.")
                            return


                    url = playlist[0]
                    res  = url.split('?v=')[1]
                    api_key=jsonfo["youtube_api_key"]
                    searchUrl=f"https://www.googleapis.com/youtube/v3/videos?id={res}&key="+api_key+"&part=snippet%2CcontentDetails"
                    response = urllib.request.urlopen(searchUrl).read()
                    data = json.loads(response)
                    duration=data['items'][0]['contentDetails']['duration']
                    duration = duration.replace('PT', '')
                    duration = duration.replace('M', ' Minutes, ')
                    duration = duration.replace('S', ' Seconds')
                    duration = duration.replace('D', ' Days, ')
                    duration = duration.replace('H', ' Hours, ')
                    title = data['items'][0]['snippet']['title']
                    channelTitle = data['items'][0]['snippet']['channelTitle']

                    async with ctx.typing():
                        player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
                        ctx.voice_client.play(player, after=lambda e: synchelper(e, ctx))
                        source = random.randint(1111111111,9999999999)
                        embed=discord.Embed(title='**Now Playing**', description='{}\n[{}]({})\n{}'.format(channelTitle, title, url, duration), color=0xff8c00)
                        embed.set_author(name=f"DJ {cliname()}", icon_url=client.user.avatar_url)
                        embed.set_thumbnail(url=f"http://img.youtube.com/vi/{res}/0.jpg")
                        await ctx.send(embed=embed)
                    if len(playlist) > 1:
                        for i in list(range(1, len(playlist))):
                            url = playlist[i]
                            res  = url.split('?v=')[1]
                            api_key=jsonfo["youtube_api_key"]
                            searchUrl=f"https://www.googleapis.com/youtube/v3/videos?id={res}&key="+api_key+"&part=snippet%2CcontentDetails"
                            response = urllib.request.urlopen(searchUrl).read()
                            data = json.loads(response)
                            duration=data['items'][0]['contentDetails']['duration']
                            duration = duration.replace('PT', '')
                            duration = duration.replace('M', ' Minutes, ')
                            duration = duration.replace('S', ' Seconds')
                            duration = duration.replace('D', ' Days, ')
                            duration = duration.replace('H', ' Hours, ')
                            title = data['items'][0]['snippet']['title']
                            channelTitle = data['items'][0]['snippet']['channelTitle']
                            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
                            playdic = {'src': player, 'url': url, 'duration': duration, 'res': res, 'channtitle':channelTitle, 'title': title}
                            songs.append(playdic)

                        embed=discord.Embed(title='Turntables', description=f"Just queued up the rest of {ctx.author.mention}'s playlist!", color=0xff8c00)
                        embed.set_author(name=f"DJ {cliname()}", icon_url=ctx.author.avatar_url)
                        await ctx.send(embed=embed)
                else:
                    embed=discord.Embed(title='Turntables', description=f"There aren't any songs in your playlist!", color=0xff8c00)
                    embed.set_author(name=f"DJ {cliname()}", icon_url=ctx.author.avatar_url)
                    await ctx.send(embed=embed)

            else:
                embed=discord.Embed(title='Turntables', description=f"It seems that you don't have a playlist! Maybe get on that!", color=0xff8c00)
                embed.set_author(name=f"DJ {cliname()}", icon_url=ctx.author.avatar_url)
                await ctx.send(embed=embed)


        elif mode==None:
            if str(ctx.author.id) not in list(playlists.keys()):
                embed=discord.Embed(title='Turntables', description=f"It looks like you don't have a playlist set up yet!", color=0xff8c00)
                embed.set_author(name=f"DJ {cliname()}", icon_url=client.user.avatar_url)
                await ctx.author.send(embed=embed)
            elif len(playlists[str(ctx.author.id)]) == 0:
                embed=discord.Embed(title='Turntables', description=f"There's nothing in your playlist!", color=0xff8c00)
                embed.set_author(name=f"DJ {cliname()}", icon_url=client.user.avatar_url)
                await ctx.author.send(embed=embed)
            else:
                playlist = playlists[str(ctx.author.id)]
                msg = f'There\'s {len(playlist)} song(s) in your playlist:'
                for i in list(range(len(playlist))):
                    url = playlist[i]
                    res  = url.split('?v=')[1]
                    api_key=jsonfo["youtube_api_key"]
                    searchUrl=f"https://www.googleapis.com/youtube/v3/videos?id={res}&key="+api_key+"&part=snippet"
                    response = urllib.request.urlopen(searchUrl).read()
                    data = json.loads(response)
                    title = data['items'][0]['snippet']['title']
                    msg = msg+f"\n{i+1}:[{title}]({url})"

                embed=discord.Embed(title='Playlist', description=msg, color=0xff8c00)
                embed.set_author(name=f"DJ {cliname()}", icon_url=client.user.avatar_url)
                await ctx.author.send(embed=embed)



        elif mode=='add':
            playlist = []
            if str(ctx.author.id) in list(playlists.keys()):
                playlist = playlists[str(ctx.author.id)]
            while True:
                try:
                    embed=discord.Embed(title='Turntables', description=f"Do you mind entering the search term of the song you want in your playlist?\nIf you're done adding songs, just wait 15 seconds and this dialog will automatically close.", color=0xff8c00)
                    embed.set_author(name=f"DJ {cliname()}", icon_url=client.user.avatar_url)
                    await ctx.author.send(embed=embed)

                    author = ctx.author

                    def check(text):
                        return type(text.channel) is discord.DMChannel and text.author == author and len(text.content.replace(' ','')) > 0

                    msg = await client.wait_for('message', check=check, timeout=20)
                    query = urllib.parse.urlencode({'search_query':msg.content})
                    rawcon = urllib.request.urlopen(f'https://www.youtube.com/results?{query}')
                    res  = re.findall('href=\"\\/watch\\?v=(.{11})', rawcon.read().decode())
                    res = res[0]
                    url = f'https://www.youtube.com/watch?v={res}'
                    playlist.append(url)
                    video_id=res
                    api_key=jsonfo["youtube_api_key"]
                    searchUrl=f"https://www.googleapis.com/youtube/v3/videos?id={res}&key="+api_key+"&part=snippet"
                    response = urllib.request.urlopen(searchUrl).read()
                    data = json.loads(response)
                    title = data['items'][0]['snippet']['title']
                    thumbnail = data['items'][0]['snippet']['thumbnails']['default']['url']
                    channeler = data['items'][0]['snippet']['channelTitle']
                    embed=discord.Embed(title='**Added to Playlist**', description='**{}**\n[{}]({})'.format(channeler,title, url), color=0xff8c00)
                    embed.set_author(name=f"DJ {cliname()}", icon_url=client.user.avatar_url)
                    embed.set_thumbnail(url=thumbnail)
                    await ctx.author.send(embed=embed)

                except asyncio.TimeoutError:
                    embed=discord.Embed(title='Turntables', description=f"Too Late!", color=0xff8c00)
                    embed.set_author(name=f"DJ {cliname()}", icon_url=client.user.avatar_url)
                    await ctx.author.send(embed=embed)
                    break
                if playlist != []:
                    playlists[str(ctx.author.id)] = playlist
                    db.collection(u'playlists').document(u'playlists').set(playlists)


        elif mode == 'del':
            if str(ctx.author.id) in list(playlists.keys()):
                embed=discord.Embed(title='Turntables', description=f"Enter the number of the song you'd like to delete from your playlist.", color=0xff8c00)
                embed.set_author(name=f"DJ {cliname()}", icon_url=client.user.avatar_url)
                await ctx.author.send(embed=embed)
                def check(text):
                    return type(text.channel) is discord.DMChannel and text.author == ctx.author and checkint(text.content)

                number = await client.wait_for('message', check=check, timeout=20)
                number = int(number.content)
                if number > len(playlists[str(ctx.author.id)]):
                    embed=discord.Embed(title='Turntables', description=f"The index you supplied is too high!.", color=0xff8c00)
                    embed.set_author(name=f"DJ {cliname()}", icon_url=client.user.avatar_url)
                    await ctx.author.send(embed=embed)
                else:
                    playlist = playlists[str(ctx.author.id)]
                    number -= 1
                    playlist.pop(number)
                    playlists[str(ctx.author.id)] = playlist
                    db.collection(u'playlists').document(u'playlists').set(playlists)
                    embed=discord.Embed(title='Turntables', description=f"Your song was deleted!.", color=0xff8c00)
                    embed.set_author(name=f"DJ {cliname()}", icon_url=client.user.avatar_url)
                    await ctx.author.send(embed=embed)


            else:
                embed=discord.Embed(title='Turntables', description=f"You don't seem to have a playlist... maybe work on it with the add mode?", color=0xff8c00)
                embed.set_author(name=f"DJ {cliname()}", icon_url=client.user.avatar_url)
                await ctx.author.send(embed=embed)
                return

        else:
            embed=discord.Embed(title='Turntables', description=f"I'm sorry, but '{mode}' is not one of my modes!", color=0xff8c00)
            embed.set_author(name=f"DJ {cliname()}", icon_url=client.user.avatar_url)
            await ctx.send(embed=embed)

    @commands.command(brief='Make the bot join a voice channel. Defaults to yours.', description="Joins a voice channel. PS: The 'channel' argument is just the name of the channel.")
    async def join(self, ctx, *, channel: discord.VoiceChannel=None):
        if channel==None:
            channel = ctx.author.voice.channel
        if ctx.voice_client is not None:
            await ctx.voice_client.move_to(channel)
        else:
            await channel.connect()
        embed=discord.Embed(title='Movers', description=f"We in da house boi! We jammin in {channel}", color=0xff8c00)
        embed.set_author(name=f"DJ {cliname()}", icon_url=client.user.avatar_url)
        await ctx.send(embed=embed)

    @commands.command(brief='There are some songs you just don\'t like...', description='Entering this will skip to the next track in the queue, if there is one.')
    async def skip(self, ctx):
        global songs
        global prefix
        if ctx.voice_client is not None:
            if len(songs)>0:
                ctx.voice_client.stop()
                embed=discord.Embed(title='Turntables', description="Skipping...", color=0xff8c00)
                embed.set_author(name=f"DJ {cliname()}", icon_url=client.user.avatar_url)
                await ctx.send(embed=embed)
            else:
                embed=discord.Embed(title='Turntables', description=f"There isn't a track for me to skip to... maybe add something to the queue with {prefix}play?", color=0xff8c00)
                embed.set_author(name=f"DJ {cliname()}", icon_url=client.user.avatar_url)
                await ctx.send(embed=embed)
        else:
            embed=discord.Embed(title='Turntables', description="I can't skip if I'm not even playing stuff to begin with!", color=0xff8c00)
            embed.set_author(name=f"DJ {cliname()}", icon_url=client.user.avatar_url)
            await ctx.send(embed=embed)



    @commands.command(brief='Time to break out the myoosic!', description='Enter the command with the name of the song (or just a youtube search), and the bot will play the first video it finds.')
    async def play(self, ctx, *, query: str=None):
        global songs
        global source
        if query is not None:
            async with ctx.typing():
                embed=discord.Embed(title='Turntables', description=":mag: **| Searching the underbelly of youtube**", color=0xff8c00)
                embed.set_author(name=f"DJ {cliname()}", icon_url=client.user.avatar_url)
                await ctx.send(embed=embed)
                query = urllib.parse.urlencode({'search_query':query})
                rawcon = urllib.request.urlopen(f'https://www.youtube.com/results?{query}')
                res  = re.findall('href=\"\\/watch\\?v=(.{11})', rawcon.read().decode())
                res = res[0]
                url = f'https://www.youtube.com/watch?v={res}'
                video_id=res
                api_key= jsonfo["youtube_api_key"]
                searchUrl=f"https://www.googleapis.com/youtube/v3/videos?id={res}&key="+api_key+"&part=snippet%2CcontentDetails"
                response = urllib.request.urlopen(searchUrl).read()
                data = json.loads(response)
                duration=data['items'][0]['contentDetails']['duration']
                duration = duration.replace('PT', '')
                duration = duration.replace('M', ' Minutes, ')
                duration = duration.replace('S', ' Seconds')
                duration = duration.replace('D', ' Days, ')
                duration = duration.replace('H', ' Hours, ')
                title = data['items'][0]['snippet']['title']
                channelTitle = data['items'][0]['snippet']['channelTitle']
        elif query is None:
            await ctx.send('You have to pick something to play doofus.')
            return

        if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
            async with ctx.typing():
                player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
                ctx.voice_client.play(player, after=lambda e: synchelper(e, ctx))
                source = random.randint(1111111111,9999999999)
                embed=discord.Embed(title='**Now Playing**', description='{}\n[{}]({})\n{}'.format(channelTitle, title, url, duration), color=0xff8c00)
                embed.set_author(name=f"DJ {cliname()}", icon_url=client.user.avatar_url)
                embed.set_thumbnail(url=f"http://img.youtube.com/vi/{res}/0.jpg")
                await ctx.send(embed=embed)
        else:
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            playdic = {'src': player, 'url': url, 'duration': duration, 'res': res, 'channtitle':channelTitle, 'title': title}
            songs.append(playdic)
            embed=discord.Embed(title='**Queued Up**', description='**{}**\n[{}]({})\n{}'.format(channelTitle, title, url, duration), color=0xff8c00)
            embed.set_author(name=f"DJ {cliname()}", icon_url=client.user.avatar_url)
            embed.set_thumbnail(url=f"http://img.youtube.com/vi/{res}/0.jpg")
            await ctx.send(embed=embed)

    @commands.command(brief="See what's coming up, or delete something.", description='Use the command with no arguments to see the queue. After seeing the queue, enter the command again with the number of the song you want to delete (i.e `!queue 1`).')
    async def queue(self, ctx,*, remove: int=None):
        global songs
        if remove is not None:
            if remove > len(songs):
                embed=discord.Embed(title='Queue', description=f"The number of the song you wanted to delete was too high... there's only {len(songs)} songs!", color=0xff8c00)
                embed.set_author(name=f"DJ {cliname()}", icon_url=client.user.avatar_url)
                await ctx.send(embed=embed)
            else:
                remove -= 1
                songs.pop(remove)
                embed=discord.Embed(title='Queue', description=f"That song is long gone now...", color=0xff8c00)
                embed.set_author(name=f"DJ {cliname()}", icon_url=client.user.avatar_url)
                await ctx.send(embed=embed)

        else:
            if len(songs) == 0:
                embed=discord.Embed(title='Queue', description="There aren't any songs queued up!", color=0xff8c00)
                embed.set_author(name=f"DJ {cliname()}", icon_url=client.user.avatar_url)
                await ctx.send(embed=embed)
            else:
                msg = f'There\'s {len(songs)} song(s) queued up:\n'
                for i in list(range(len(songs))):
                   msg = msg + f"{i+1}: [{songs[i]['src'].title}]({songs[i]['url']})\n"
                embed=discord.Embed(title='Queue', description=msg, color=0xff8c00)
                embed.set_author(name=f"DJ {cliname()}", icon_url=client.user.avatar_url)
                await ctx.send(embed=embed)


    @commands.command(brief='Change the volume, and see what the volume is.', description='Use the command with no argument to see the volume. Use the command with a positive argument to set the volume.')
    async def volume(self, ctx,*, volume: int=None):
        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")
        if volume is not None:
            ctx.voice_client.source.volume = volume / 100
            embed=discord.Embed(title='Sound', description="Changed volume to {}%".format(volume), color=0xff8c00)
            embed.set_author(name=f"DJ {cliname()}", icon_url=client.user.avatar_url)
            await ctx.send(embed=embed)
        elif volume is None:
            try:
                vol = ctx.voice_client.source.volume * 100
                embed=discord.Embed(title='Sound', description="The volume is {}%".format(vol), color=0xff8c00)
                embed.set_author(name=f"DJ {cliname()}", icon_url=client.user.avatar_url)
                await ctx.send(embed=embed)
            except:
                embed=discord.Embed(title='Sound', description="You can't have a volume if you're not playing anything stupid.", color=0xff8c00)
                embed.set_author(name=f"DJ {cliname()}", icon_url=client.user.avatar_url)
                await ctx.send(embed=embed)

    @commands.command(description='Stops the myoosic, and disconnects the bot.')
    async def stop(self, ctx):
        global songs
        global forced
        if ctx.voice_client is not None:
            songs = []
            forced = True
            await ctx.voice_client.disconnect()
            embed=discord.Embed(title='We the best Myoosic...', description="We out!", color=0xff8c00)
            embed.set_author(name=f"DJ {cliname()}", icon_url=client.user.avatar_url)
            await ctx.send(embed=embed)
        else:
            embed=discord.Embed(title='We the best Myoosic...', description="You can't stop something that doesn't exist!", color=0xff8c00)
            embed.set_author(name=f"DJ {cliname()}", icon_url=client.user.avatar_url)
            await ctx.send(embed=embed)

    @commands.command(brief='Take a break if you need it!',description='You can take a break if you need to... but after 5 minutes the bot stops completely.')
    async def pause(self, ctx):
        global source
        if ctx.voice_client is not None:
            if ctx.voice_client.is_playing():
                ctx.voice_client.pause()
                ctx.sourcepause = source
                embed=discord.Embed(title='Turntables', description="Paused!", color=0xff8c00)
                embed.set_author(name=f"DJ {cliname()}", icon_url=client.user.avatar_url)
                await ctx.send(embed=embed)
            else:
                embed=discord.Embed(title='Turntables', description="You're not playing anything for me to pause!", color=0xff8c00)
                embed.set_author(name=f"DJ {cliname()}", icon_url=client.user.avatar_url)
                await ctx.send(embed=embed)
        else:
            embed=discord.Embed(title='Turntables', description="You're not playing anything for me to pause!", color=0xff8c00)
            embed.set_author(name=f"DJ {cliname()}", icon_url=client.user.avatar_url)
            await ctx.send(embed=embed)

    @commands.command(brief='Done with that break?', description='Resumes your current song.')
    async def resume(self, ctx):
        if ctx.voice_client is not None:
            if ctx.voice_client.is_paused():
                ctx.voice_client.resume()
                embed=discord.Embed(title='Turntables', description="Resuming your song!", color=0xff8c00)
                embed.set_author(name=f"DJ {cliname()}", icon_url=client.user.avatar_url)
                await ctx.send(embed=embed)
            else:
                embed=discord.Embed(title='Turntables', description="You're don't have anything paused for me to resume!", color=0xff8c00)
                embed.set_author(name=f"DJ {cliname()}", icon_url=client.user.avatar_url)
                await ctx.send(embed=embed)
        else:
            embed=discord.Embed(title='Turntables', description="You're don't have anything paused for me to resume!", color=0xff8c00)
            embed.set_author(name=f"DJ {cliname()}", icon_url=client.user.avatar_url)
            await ctx.send(embed=embed)


    @join.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send(":no_entry_sign:  You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")

    @play.before_invoke
    async def playchann(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send(":no_entry_sign:  You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
        if ctx.voice_client and ctx.author.voice:
            if ctx.author.voice.channel != ctx.voice_client.channel:
                await ctx.send(":no_entry_sign: | **You aren't in my channel!**")
                raise commands.CommandError("Author not connected to a voice channel.")


    @queue.before_invoke
    @skip.before_invoke
    async def samechann(self, ctx):
        if ctx.voice_client and ctx.author.voice:
            if ctx.author.voice.channel != ctx.voice_client.channel:
                await ctx.send(":no_entry_sign: | **You aren't in my channel!**")
                raise commands.CommandError("Author not connected to a voice channel.")



    @pause.after_invoke
    async def still_playing(self, ctx):
        global songs
        global forced
        global source
        await asyncio.sleep(300)
        if ctx.voice_client is not None:
            if ctx.voice_client.is_paused() and ctx.sourcepause == source:
                songs = []
                forced = True
                await ctx.voice_client.disconnect()
                embed=discord.Embed(title='We the best Myoosic...', description="It looks like you aren't playing that song anymore... we're out!", color=0xff8c00)
                embed.set_author(name=f"DJ {cliname()}", icon_url=client.user.avatar_url)
                await ctx.send(embed=embed)



client.add_cog(Misc(client))
client.add_cog(CommandErrorHandler(client))
client.add_cog(Utils(client))
client.add_cog(Games(client))
client.add_cog(Code(client))
client.add_cog(Music(client))


@client.event
async def on_message(message):
    global prefix
    global curr
    global blacklist
    global timeouts
    global db
    author = message.author

    # we do not want the bot to reply to itself
    if message.author == client.user:
        return

    elif message.channel == client.get_channel(jsonfo["verif_channel_id"]):
        curr.append(message.author)

        def check(text):
            return type(text.channel) is discord.DMChannel and text.author == author

        await message.delete()
        await message.author.send('Please enter your email address. This dialog times out in 30 seconds.')
        try:
            msg = await client.wait_for('message', check=check, timeout=30)
        except:
            await message.author.send('Too Late!')
            return
        if msg is None:
            await message.author.send('Too late!')
            return
        elif '@' not in msg.content or '.' not in msg.content or ' ' in msg.content:
            await message.author.send("I'm sorry, but that's not a proper email address!")
            return
        elif '@' in msg.content and '.' in msg.content and ' ' not in msg.content:
            verify = random.randint(100000, 1000000)
            with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
                server.login(jsonfo["bot_email"], password)
                sender_email = jsonfo["bot_email"]
                receiver_email = msg.content
                mesg = f"""Your verification code for {message.guild.name} is """+str(verify)+'.'
                server.sendmail(sender_email, receiver_email, mesg)
            await message.author.send('Assuming that that was your email, you were sent an email with a code. Please enter that for verification, within 2 minutes please.')
            try:
                msg = await client.wait_for('message', check=check, timeout=120)
            except:
                await message.author.send('Too Late!')
                return
            if msg is None:
                await message.author.send('Too late!')
            elif msg.content != str(verify):
                await message.author.send("That wasn't the right code! Please attempt verification again by sending another message in the verification channel.")
            elif msg.content == str(verify):
                await message.author.send("That seems about right. Congratulations, you're verified!")
                role = discord.utils.get(message.guild.roles, name=jsonfo["verif_role"])
                await message.author.add_roles(role, reason='Successful Verification With Bot')
            return
    else:
        if message.content.startswith(prefix):
            await client.process_commands(message)
            return

        if not message.guild.get_member(message.author.id).guild_permissions.administrator:
            if any(word.lower() in message.content.lower() for word in blacklist):
                await message.delete()
                return

        try:
            count = antispam_count[str(message.author.id)]

        except KeyError:
            antispam_count[str(message.author.id)] = 1
            antispam_time[str(message.author.id)] = datetime.now()
            return
        print(count)

        time = antispam_time[str(message.author.id)]
        now = datetime.now()
        antispam_time[str(message.author.id)] = now

        if time + timedelta(minutes = 1)  <=  now:
            antispam_count[str(message.author.id)] = 1
            return

        if time + timedelta(seconds=5)  >= now:
            antispam_count[str(message.author.id)]  += 1
            antispam_time[str(message.author.id)]

        if antispam_count[str(message.author.id)] == 20:
            antispam_count[auth_id(message)] = 0
            try:
                offenses = timeouts[auth_id(message)]
            except KeyError:
                timeouts[auth_id(message)] = 0
                offenses =  0
            await punishments[offenses](message)
            timeouts[auth_id(message)] += 1
            db.collection(u'timeouts').document('timeouts').set(timeouts)
            return

@client.event
async def on_member_join(member):
    global prefix
    try:
        await member.send('Check out announcements for any important  information, and use '+prefix+'help anywhere in the server for some help regarding the server. Typing anything in the verify channel will get you verified, which gives you access to the rest of the server.')
    except:
        await client.get_channel(jsonfo["welcome_id"]).send(f'Welcome to {client.get_channel(jsonfo["welcome_id"].guild.name)} {member.mention}!'+'\nPlease verify yourself by typing something in the verify channel.')
        return
    await client.get_channel(jsonfo["welcome_id"]).send(f'Welcome to {client.get_channel(jsonfo["welcome_id"].guild.name)} {member.mention}!')


@client.event
async def on_ready():
    global guild
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    await client.get_channel(jsonfo["home_channel_id"]).send(jsonfo["update"])
    await client.change_presence(activity=discord.Game(name=prefix + 'help'))
    guild = client.get_channel(jsonfo["home_channel_id"]).guild

client.run(TOKEN)
