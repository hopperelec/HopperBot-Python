import discord
from discord.ext import commands
from random import random
from json import load as jsonread
from os import environ,listdir
environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
from aitextgen import aitextgen
from aitextgen.utils import GPT2ConfigCPU
import matplotlib.pyplot as plt
from matplotlib.ticker import StrMethodFormatter
from nltk import ngrams
from re import sub
from emojis.db import get_emojis_by_category
chars = ".,-' `?!/()"+''.join([inner for outer in [[''.join(emoji.emoji) for emoji in get_emojis_by_category(category)] for category in ['Smileys & Emotion','People & Body']] for inner in outer])

class AI(commands.Cog):
    location = "./Cogs/Shared/AI/"
    names = ["ai"]
    prefixes = ["?"]
    description = "Cog for Hopper's Discord AI projects"
    whitelist = ["HopperElecYT","TheFuturisticIdiot","CmeRuler","AzureAqua","wuulfy","ridler04","Tortoise Phrog","Non-Existing","Diego Being Hated"]

    def __init__(self,bot):
        self.bot = bot

    async def cog_check(self,ctx):
        ctx.checkDefinitions = ["is disabled in this server",f"uses prefix `{self.prefixes[0]}` but `{ctx.prefix}` was entered","you are not included in the dataset (either not active enough or haven't given consent"]
        ctx.checkResults = [await self.bot.main.getCogConfig(self.names,ctx.guild) != None,ctx.prefix in self.prefixes,ctx.author.id in self.whitelist]
        return not False in ctx.checkResults

    @commands.Cog.listener()
    async def on_ready(self):
        self.servers,self.configs = self.bot.main.setup(self.names)

        with open(self.location+"authorCounts.json","r") as jsonfile:
            self.authorcounts = jsonread(jsonfile)
        with open(self.location+"messages/all.txt","r") as txtfile:
            self.allmessages = txtfile.read().lower()

        self.authorMessageCount = {}
        self.authorMessageLength = {}
        for filename in listdir(self.location+"data"):
            with open(self.location+"data/"+filename,"r") as jsonfile:
                for message in jsonread(jsonfile)["messages"]:
                    if message["author"]["name"] in self.authorMessageCount:
                        self.authorMessageCount[message["author"]["name"]] += 1
                        self.authorMessageLength[message["author"]["name"]] += len(message["content"])
                    else:
                        self.authorMessageCount[message["author"]["name"]] = 1
                        self.authorMessageLength[message["author"]["name"]] = len(message["content"])
        self.authorMessageCount = dict(sorted(self.authorMessageCount.items(), key=lambda item: item[1], reverse=True))
        self.authorMessageLength = dict(sorted([(i[0],int(i[1]/self.authorMessageCount[i[0]])) for i in self.authorMessageLength.items()], key=lambda item: item[1], reverse=True))

        plt.plot([v for v in self.authorMessageCount.values() if v > 1])
        plt.ylabel("Messages sent")
        plt.yscale("log")
        plt.gcf().gca().yaxis.set_major_formatter(StrMethodFormatter('{x:.0f}'))
        plt.savefig(self.location+"authorMessageCountGraph.png")
        self.authorMessageCountGraph = discord.File(self.location+"authorMessageCountGraph.png")

        self.topSendersEmbed = discord.Embed(title="Top senders",description="The 15 people included in the dataset who have sent the most messages on Discord",color=0xe31313).set_footer(text="Created by HopperElecYT#3060")
        self.longestWritersEmbed = discord.Embed(title="Longest writers",description="The 15 people included in the dataset who write the longest messages on Discord",color=0xe31313).set_footer(text="Created by HopperElecYT#3060")
        self.predictAuthorEmbed = discord.Embed(title="Most likely authors",description="Everyone in the filtered dataset, sorted by their likeliness to write the above message",color=0xe31313).set_footer(text="Created by HopperElecYT#3060")

        self.bot.main.started(self.names[0])

    @commands.command(description="Shows the top 100 ngrams (words or phrases) scored by generateCounts.py for a person")
    async def aitop100ngrams(self,ctx,*name):
        name = " ".join(name)
        if name in self.authorcounts:
            await ctx.send("`"+"`, `".join(sorted(self.authorcounts[name].keys(),key=lambda item: self.authorcounts[name][item],reverse=True)[:99])+"`")
        else:
            await ctx.send(f"A member by the name `{name}`` isn't listed in authorCounts. Use `?aiactive` to view options")

    @commands.command(description="Gets the (index)th ngram for a person sorted by generateCounts.py")
    async def aingram(self,ctx,index,*name):
        name = " ".join(name)
        try:
            index = int(index)
        except ValueError:
            await ctx.send(f"Invalid index '{index}', {ctx.author.mention}!")
        if name in self.authorcounts:
            if index < len(self.authorcounts[name]) and index > 0:
                await ctx.send(sorted(self.authorcounts[name].keys(),key=lambda item: self.authorcounts[name][item],reverse=True)[index+1])
            else:
                await ctx.send(f"`{name}` doesn't have {index} ngrams, {ctx.author.mention}!")
        else:
            await ctx.send(f"A member by the name `{name}` isn't listed in authorCounts. Use `?aiactive` to view options, {ctx.author.mention}!")

    @commands.command(description="Counts the number of times a word or phrase appears in the dataset")
    async def aicount(self,ctx,*countee):
        count = self.allmessages.count(" ".join(countee).lower())
        if count < 5:
            await ctx.send("Fewer than 5 (not shown to prevent abuse)")
        else:
            await ctx.send(count)

    @commands.command(description="Shows who the AI has enough data for in order to produce models of")
    async def aiactive(self,ctx):
        await ctx.send("`"+"`, `".join(self.authorcounts.keys())+"`")

    @commands.command(description="Generates a message based on a starting sequence and what it's learned from the dataset (use | to seperate the starting sequence and author. Use %n as the starting sequence to start from scratch. Use GPT2 as the author to use raw GPT2 data (not a particulare member). Example: ?aigenerate Hello, I am | HopperElecYT)")
    async def aigenerate(self,ctx,*data):
        if data.count("|") == 1 and data[0] != "|" and data[-1] != "|":
            data = " ".join(data).split(" | ")
            prefix,name = data[0],data[1]
            if name in listdir(self.location+"GPT2-models"):
                loc = self.location+"GPT2-models/"+name+"/"
                textgen = aitextgen(model=loc+"pytorch_model.bin", vocab_file=loc+name+"-vocab.json", merges_file=loc+name+"-merges.txt", config=GPT2ConfigCPU(), cache_dir=loc, bos_token="", eos_token="", unk_token="")
            elif name == "GPT2":
                # textgen = aitextgen(bos_token="", eos_token="", unk_token="")
                await ctx.send("This feature does not work yet!")
                return
            else:
                await ctx.send(f"A member by the name `{name}` doesn't have a trained model. Use `?aiactive` to view options, {ctx.author.mention}!")
                return
            if prefix == "%n":
                prefix = ""
            else:
                prefix = sub(r' {2,}',' ',''.join([(char if char in chars or char.isalnum() else ' ') for char in sub(r'(https|http)?:\/\/(\w|\.|\/|\?|\=|\&|\%)*\b','',prefix)])).strip()
            message = await ctx.send("Please be patient, this may take a few seconds...")
            await message.edit(content=textgen.generate_one(min_length=len(prefix)+4, max_length=2000, prompt=prefix, temperature=random()).split("\n")[0])
        else:
            await ctx.send("Please the starting message (or %n for it to make from scratch), then a |, then the author name")

    @commands.command(description="Shows how many messages by a person are in the unfiltered data")
    async def aimessagesby(self,ctx,*name):
        name = " ".join(name)
        if name in self.authorMessageCount:
            await ctx.send(self.authorMessageCount[name])
        else:
            await ctx.send(f"Nobody by the name {name} found in dataset, {ctx.author.mention}!")

    @commands.command(description="Shows how many messages by a person are in the unfiltered data")
    async def aitopsenders(self,ctx):
        place = 1
        embed = self.topSendersEmbed.copy()
        for sender in list(self.authorMessageCount.keys())[:15]:
            embed.add_field(name=f"{place}: {sender}",value=self.authorMessageCount[sender])
            place += 1
        await ctx.send(embed=embed)

    @commands.command(description="Displays aa graph showing the number of messages sent by members")
    async def aimessagegraph(self,ctx):
        await ctx.send(file=self.authorMessageCountGraph)

    @commands.command(description="Displays aa graph showing the number of messages sent by members")
    async def aiaveragelength(self,ctx,*name):
        name = " ".join(name)
        if name in self.authorMessageCount:
            await ctx.send(self.authorMessageLength[name])
        else:
            await ctx.send(f"Nobody by the name {name} found in dataset, {ctx.author.mention}!")

    @commands.command(description="Shows who writes the longest messages on average")
    async def ailongestwriters(self,ctx,minMessages="0"):
        try:
            minMessages = int(minMessages)
        except ValueError:
            await ctx.send(f"Invalid integer '{minMessages}', {ctx.author.mention}!")
        place = 0
        embed = self.longestWritersEmbed.copy()
        for sender in [k for k in self.authorMessageLength.keys() if self.authorMessageCount[k] >= minMessages][:15]:
            place += 1
            embed.add_field(name=f"{place}: {sender}",value=self.authorMessageLength[sender])
        await ctx.send(embed=embed)

    @commands.command(description="Shows who the AI believes is most likely to send a message")
    async def aipredictauthor(self,ctx,message):
        message = sub(r' {2,}',' ',message).strip()
        scores = {k:sum([v[gram] for gram in [inner for outer in [result for result in [[' '.join(ngram) for ngram in ngrams(message.split(' '),n)] for n in range(1,7)] if result != []] for inner in outer] if gram in v]) for k,v in self.authorcounts.items()}

        if sum(scores.values()) == 0:
            await ctx.send("Nobody in the dataset has ever used anything in that messages, so no predictions can be made")
        else:
            place = 0
            embed = self.predictAuthorEmbed.copy()
            for author in sorted(list(self.authorcounts.keys()),key=lambda item: scores[item],reverse=True):
                place += 1
                embed.add_field(name=f"{place}: {author}",value=str(int(scores[author]/sum(scores.values())*1000)/10)+"%")
            await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(AI(bot))
  