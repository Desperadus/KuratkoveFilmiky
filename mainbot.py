#!/usr/bin/env python3
import discord
from discord.ui import Button, View, Modal, TextInput, Select

import random
import secret
from kuratkovefilmiky import *

intents = discord.Intents.all()
client = discord.Client(command_prefix='!', intents=intents)
#print(secret.url)

async def list_people(message):
    res = parse_remote_sheet_via_stdlib(secret.url)[1]
    people = []
    for person in res:
        people.append(person.name)
    
    embed = discord.Embed(title="Seznam uživatelů",
                                color=0x0000FF)
    for x in range(0, len(people)):
        embed.add_field(name=str(x+1)+". "+people[x], value="----------------", inline=False)
    
    await message.channel.send(embed=embed)

    

def choose_random_gif():
    rng = random.randint(0, 5)
    if rng == 0:
        return "https://media.tenor.com/OAZ6t5iGLGQAAAAM/movie-time.gif"
    elif rng == 1:
        return "https://media4.giphy.com/media/tmH5eUto7WumOdTvRG/giphy.gif"
    elif rng == 2:
        return "https://custom-doodle.com/wp-content/uploads/doodle/movie-time-yellow-text/movie-time-yellow-text-doodle.gif"
    elif rng == 3:
        return "https://media.tenor.com/5KF3BqrpKs8AAAAM/eating-popcorn-watching-a-movie.gif"
    elif rng == 4:
        return "https://gifdb.com/images/high/popcorn-panda-movie-time-87zj3il8jv83y1lv.gif"
    else:
        return "https://thumbs.gfycat.com/AdolescentFaintAfricangoldencat-max-1mb.gif"


async def add_reactions(message, channel, amount):
    for i in range(1, amount+1):
        try:
            await message.add_reaction(str(i) + u'\u20E3')
        except:
            await channel.send("Problem s pridavanim reakci")
            break


async def show_top_movies(amount, movies, watching, message):
    channel = message.channel
    watching_str=""

    for i,user in enumerate(watching):
        edited = "*"+user+"*"
        if i == len(watching)-1:
            watching_str += edited
        else:
            watching_str += edited + ", "

    if len(watching) != 0:
        embed = discord.Embed(title="Top "+ str(amount)+" filmů",
                                description="dle preferencí od: "+ watching_str + "\n\n Hlasujte pomocí reakcí pro:",
                                color=0x00FF00)
    else:
        embed = discord.Embed(title="Top "+ str(amount)+" filmů",
                                description="Hlasujte pomocí reakcí pro:",
                                color=0x00FF00)
    
    for x in range(0, len(movies)):
        embed.add_field(name=str(x+1)+". "+str(movies[x]), value ="", inline=False)
    
    embed.set_image(url=choose_random_gif())

    movie_message = await channel.send(embed=embed)

    await add_reactions(movie_message, channel, amount)


async def parse_top_movies(amount, message,  remote_sheet_url, participants=[]):
    movies = []
    res = gimme_a_happy_movie_night_for_me_and_my_lil_happy_frens(amount, remote_sheet_url=remote_sheet_url, participants=participants)
    for movie in res:
        movies.append(movie.name)
    await show_top_movies(amount, movies, participants, message)


@client.event
async def on_message(message):
    channel = message.channel


    if message.content.startswith('!movies'):
        #await show_top_movies(5, movies, watching, message)
        split = message.content.split(" ")

        if message.content == "!movies":
            await parse_top_movies(5, message = message, remote_sheet_url = secret.url, participants=[])
        elif len(split) == 2:
            try:
                amount = int(split[1])
                await parse_top_movies(amount, message = message, remote_sheet_url = secret.url, participants=[])
            except:
                await channel.send("Nespravny format prikazu, pouzij !movies <pocet filmu> <uživatelé>")
        elif len(split) > 2:
            try:
                amount = int(split[1])
                participants = split[2:]
                await parse_top_movies(amount, message = message, remote_sheet_url = secret.url, participants=participants)
            except:
                await channel.send("Nespravny format prikazu, pouzij !movies <pocet filmu> <uživatelé>")

    
    if message.content == "!moviehelp":
        await message.channel.send("Použij **!movies <pocet filmu> <uživatelé>** pro zobrazení top filmů.\nNapř: *!movies 5 Pika Kickin Sandrini* \n\n **!moviespeople** pro zobrazení seznamu uživatelů.")

    if message.content == "!movieshelp":
        await message.channel.send("Použij **!movies <pocet filmu> <uživatelé>** pro zobrazení top filmů.\nNapř: *!movies 5 Pika Kickin Sandrini* \n\n **!moviespeople** pro zobrazení seznamu uživatelů.")

    
    
    if message.content == "!moviespeople":
        await list_people(message)
        
        

        



client.run(secret.token)
