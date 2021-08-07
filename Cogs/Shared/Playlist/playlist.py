from time import time
import discord
from discord.ext import commands
from random import choice
from asyncio import sleep,Future
from os import listdir
from json import load as jsonread
from mutagen.mp3 import MP3
from math import floor
from wavelink import Client,WavelinkMixin

class Playlist(commands.Cog,WavelinkMixin):
    location = "./Cogs/Shared/Playlist/"
    names = ["playlist"]
    ready = False
    prefixes = ["~"]
    description = "Plays Hopper's favourite songs in a radio-like fashion with commands for viewing information about the songs"
    handling = False
    ignoreError = False
    currentsong = None

    async def cog_check(self,ctx):
        config = await self.bot.main.getCogConfig(self.names,ctx.guild)
        ctx.checkDefinitions = ["is disabled in this server","is disabled in this channel","is in a cog that is not ready yet",f"uses prefix `{self.prefixes[0]}` but `{ctx.prefix}` was entered"]
        ctx.checkResults = [config != None,config["commandsChannel"] == ctx.channel.id,self.ready,ctx.prefix in self.prefixes]
        return not False in ctx.checkResults

    async def is_owner(ctx):
        ctx.checkDefinitions = ["it can only be used by HopperElec"]
        ctx.checkResults = [ctx.author.id == 348083986989449216]
        return ctx.checkResults[0]

    def __init__(self,bot):
        self.bot = bot

        with open(self.location+"songs.json","r") as jsonfile:
            self.songs = jsonread(jsonfile)
        self.servers,self.configs = self.bot.main.setup(self.names)
        bot.loop.create_task(self.setup())

    async def setup(self):
        self.wavelink = Client(bot=self.bot)
        await self.wavelink.initiate_node(host='127.0.0.1',port=2333,rest_uri='http://127.0.0.1:2333',password='pw',identifier='HopperRadio',region='europe')
        self.players = {}
        for server in self.servers:
            self.players[server["id"]] = self.wavelink.get_player(server["id"])
            await self.players[server["id"]].connect(self.configs[server["id"]]["voiceChannel"])
        await self.setTrack()
        self.bot.main.started(self.names[0])
        self.ready = True

        await self.bot.get_guild(769709381808816198).get_channel(770754252712443964).send(str([[i["Title"],i["URL"]] for i in self.songs.values()])[:1998])
        await self.bot.get_guild(769709381808816198).get_channel(770754252712443964).send(str([[i["Title"],i["URL"]] for i in self.songs.values()])[1998:])

    async def setTrack(self,forcedsong=None):
        self.done = 0
        self.currentsong = forcedsong if forcedsong else choice([song for song in listdir(self.location+"Songs/") if song != self.currentsong])
        self.track = (await self.wavelink.get_tracks('Songs/'+self.currentsong))[0]
        self.bot.main.log(self,"Now playing: "+self.currentsong)
        await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=self.songs[self.currentsong]["Title"]))
        for player in self.players.values():
            await player.stop()
            await sleep(0.1)
            await player.play(self.track)

    @WavelinkMixin.listener()
    async def on_track_end(self,node,payload):
        if payload.reason == "FINISHED":
            self.done += 1
            if self.done == len(self.players):
                await self.setTrack()

    def getGeniusLyrics(self):
        from json import dump as jsonwrite
        import lyricsgenius
        from os import getenv
        genius = lyricsgenius.Genius(getenv("GENIUS"))
        for song in self.songs:
            print("-="*32+"-\n"+song+":")
            if song["Lyrics"] == []:
                try:
                    result = [line for line in genius.search_song(song.split(".")[0].split(" - ")[1],song.split(".")[0].split(" - ")[0]).lyrics.split("\n") if not "[" in line]
                    self.songs[song]["lyrics"] = result
                except:
                    print("None")
            else:
                print("Already has lyrics!")
        with open(self.location+"songs.json","w") as jsonfile:
            jsonwrite(self.songs,jsonfile,indent=4)

    @commands.command(aliases=["playlist","songs"],description="Returns the list of all songs currently in the playlist")
    async def songlist(self,ctx):
        await ctx.send("```asciidoc\n= List of songs in my playlist ="+"".join(["\n- "+".".join(song.split(".")[:-1]) for song in sorted(list(self.songs))])+"```")

    def getSong(self,song,postTest=None):
        outTests = {
            "file name": lambda s: s,
            "original title": lambda s: self.songs[s]['Title'],
            "author(s)": lambda s: " ".join(self.songs[s]['Authors'])+" "+", ".join(self.songs[s]['Authors']),
            "singer(s)": lambda s: " ".join(self.songs[s]['Singers'])+" "+", ".join(self.songs[s]['Singers']),
            "lyrics (space-seperated)": lambda s: " ".join(self.songs[s]['Lyrics']),
            "lyrics (line-seperated)": lambda s: "\n ".join(self.songs[s]['Lyrics']),
            "note": lambda s: self.songs[s]['Note'],
            "youtube URL": lambda s: f"https://youtu.be/{self.songs[s]['URL']} https://youtube.com/watch?={self.songs[s]['URL']}"
        }
        song,reason = self.bot.main.getSimilar(song,self.songs.keys(),outTests,"song")
        if postTest == None:
            return song,reason
        else:
            return song,postTest(song),reason

    @commands.command(hidden=True)
    @commands.check(is_owner)
    async def forceSong(self,ctx,*song):
        if song == ():
            await ctx.send(f"Must enter name of a song, {ctx.author.mention}!")
        else:
            song,reason = self.getSong(" ".join(song))
            await ctx.message.add_reaction("👍")
            await ctx.send(f"Playing `{song}` as the input is {reason}, {ctx.author.mention}!")
            await self.setTrack(forcedsong=song)

    @staticmethod
    def lengthFormat(length):
        decimal = str(round(length%60))
        return f"{floor(length/60)}:{('0' if len(decimal) == 1 else '')+decimal}"

    @commands.command(description="Shows the currently playing song and/or information about a song of your choosing")
    async def songinfo(self,ctx,*song):
        if song == ():
            song,info,reason = self.currentsong,self.songs[self.currentsong],"what is currently playing"
        else:
            song,info,reason = self.getSong(" ".join(song),lambda s: self.songs[s])

        await ctx.send(f"Showing information for `{song}` as the input is {reason}, {ctx.author.mention}!")
        embed = discord.Embed(title=f"Song info ({song})", color=0xe31313)
        embed.set_image(url="https://img.youtube.com/vi/"+info["URL"]+"/hqdefault.jpg")
        embed.add_field(name="Title", value=info["Title"], inline=False)
        embed.add_field(name="Authors" if len(info["Authors"]) > 1 else "Author", value=", ".join(info["Authors"]), inline=False)
        if info["Singers"] != []:
            embed.add_field(name="Singers" if len(info["Singers"]) > 1 else "Singer", value=", ".join(info["Singers"]), inline=False)
        embed.add_field(name="Length", value=self.lengthFormat(MP3(self.location+"Songs/"+song).info.length), inline=True)
        if song == self.currentsong:
            embed.add_field(name="Played", value=self.lengthFormat(int(list(self.players.values())[0].position/1000)), inline=True)
        embed.add_field(name="Video", value="https://youtu.be/"+info["URL"], inline=False)
        if info["Note"] != "":
            embed.add_field(name="Note", value=info["Note"], inline=False)
        embed.add_field(name="Lyrics", value="Unavailable" if info["Lyrics"] == [] else f"Available ({self.prefixes[0]}lyrics {song})", inline=False)
        embed.set_footer(text="Created by HopperElecYT#3060")
        await ctx.send(embed=embed)

    @commands.command(aliases=["songlyrics"],description="Shows lyrics for the currently playing song or  a song of your choosing")
    @commands.cooldown(rate=1,per=60,type=commands.BucketType.guild)
    async def lyrics(self,ctx,*song):
        async def sendEmbeds(subsets,length):
            for subset in subsets:
                embed = discord.Embed(title="Lyrics", color=0xe31313)
                embed.add_field(name=song, value="\n".join(subset), inline=False)
                embed.set_footer(text="Created by HopperElecYT#3060")
                if length:
                    await ctx.send(embed=embed,delete_after=length)
                else:
                    await ctx.send(embed=embed)

        song = self.currentsong if song == () else " ".join(song)
        song,lyrics,reason = self.getSong(song,lambda s: self.songs[s]["Lyrics"])
        await ctx.send(f"Showing lyrics information for `{song}` as the input is {reason}, {ctx.author.mention}!")
        if lyrics == []:
            await ctx.send(f"Lyrics aren't available for this song, {ctx.author.mention}!")
        else:
            try:
                await sendEmbeds([lyrics],None)
            except discord.errors.HTTPException: 
                length = MP3(self.location+"Songs/"+song).info.length
                message = await ctx.send(f"These lyrics are very long so it will be spread over a couple or few messages and may take a bit to process. They'll be deleted in {self.lengthFormat(length)}!")
                await sleep(5)
                try:
                    await sendEmbeds([lyrics[:int(len(lyrics)/2)],lyrics[int(len(lyrics)/2):]],length)
                except discord.errors.HTTPException:
                    await ctx.channel.purge(limit=1)
                    await sendEmbeds([lyrics[:int(len(lyrics)/3)],lyrics[int(len(lyrics)/3):int(len(lyrics)/3*2)],lyrics[int(len(lyrics)/3*2):]],length)
                await sleep(length)
                await message.edit(content=message.content+" (deleted)")

    # @commands.Cog.listener()
    # async def on_voice_state_update(self,member,before,after):
    #     if member.id == 769709648092856331 and after.channel == None:
    #         id = before.channel.guild.id
    #         await self.players[id].connect(self.configs[id]["voiceChannel"])
    #         await self.players[id].play(self.track,start=self.players[id].position)

def setup(bot):
    bot.add_cog(Playlist(bot))
