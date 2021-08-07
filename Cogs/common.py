import discord
from discord.ext import commands,tasks
from linecache import getline
import tracemalloc
from time import time

class Common(commands.Cog):
    location = "./"
    names = ["common"]

    def __init__(self,bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.main.started("bot")
        self.servers,self.configs = {},{}
        # await self.startTracemalloc()

    async def startTracemalloc(self):
        from asyncio import sleep
        tracemalloc.start()
        await sleep(5)
        self.logMemoryUsage.start()
        
    @commands.Cog.listener()
    async def on_command(self,ctx):
        self.bot.main.log("main",f"{str(ctx.author)} has run command `{ctx.prefix}{ctx.command.name} {' '.join([arg for arg in ctx.args[2:] if arg])}`",ctx.guild)

    @commands.command(description="Gives a simple overview of all the commands enabled in the guild")
    async def help(self,ctx,category=""):
        async def sendHelp(commands,description):
            embed = discord.Embed(title="Help", description=description,color=0xe31313)
            for command in commands:
                commandInfo = {
                    "usage": f"{command.cog.prefixes[0]}{command.name} {command.signature}",
                    "description": command.description,
                    "alises": ", ".join(command.aliases)
                }
                embed.add_field(name=command.name,value="\n".join([f"{key}: {commandInfo[key]}" for key in commandInfo]),inline=False)
            embed.set_footer(text="Created by HopperElecYT#2211")
            await ctx.send(embed=embed)

        cogs = [self.bot.cogs[cog] for cog in self.bot.cogs if ctx.guild.id in self.bot.cogs[cog].configs]
        folders = list(set([cog.location.split("/")[-2] for cog in cogs]))
        commands = [inner for outer in [cog.get_commands() for cog in cogs] for inner in outer if not inner.hidden]
        if category in folders:
            await sendHelp([command for command in commands if command.cog.location.split("/")[-2] == category],"List of enabled commands in folder "+category)
        elif category.lower() in [inner.lower() for outer in [cog.names for cog in cogs] for inner in outer]:
            await sendHelp([command for command in commands if command.cog_name.lower() == category.lower()],"List of enabled commands in cog "+category.lower())
        elif category in [inner for outer in [command.aliases+[command.name] for command in commands] for inner in outer]:
            await sendHelp([command for command in commands if command.name == category.lower()])
        else:
            embed = discord.Embed(title="Help", description="Category not entered or invalid. Run the command with one of the categories below",color=0xe31313)
            for folder in folders:
                embed.add_field(name=folder, value="\n".join([f"{cog.names[0]}: {cog.description}" for cog in cogs if cog.location.split("/")[-2] == folder]), inline=False)
            embed.set_footer(text="Created by HopperElecYT#2211")
            await ctx.send(embed=embed)

    @commands.command(description="Displays a list of servers the bot is in")
    async def server(self,ctx):
        embed = discord.Embed(title="Info",color=0xe31313)
        for server in self.bot.guilds:
            embed.add_field(name=self.bot.main.config[str(server.id)]["name"], value=self.bot.main.config[str(server.id)]["invite"], inline=False)

    @commands.command(description="Used for finding the bots latency (time between when Discord recieves a message to when the bot recieves and processes it)")
    async def ping(self,ctx):
        await ctx.send(f"Pong! {int(round(self.bot.latency,3)*1000)}ms")
        
    previousTotal = 0
    @tasks.loop(minutes=1)
    async def logMemoryUsage(self):
        starttime = time()
        topStatsSnapshot = tracemalloc.take_snapshot()
        filterLocations = ["<frozen importlib._bootstrap>","<frozen importlib._bootstrap_external>","/usr/lib/python3.8/tracemalloc.py","/usr/lib/python3.8/linecache.py",""]
        topStatsFiltered = topStatsSnapshot.filter_traces((tracemalloc.Filter(False, location) for location in filterLocations)).statistics('lineno')
        limit = 5
        print(f"{'-='*32}-\nTop {limit} lines")
        for index,stat in enumerate(topStatsFiltered[:limit],1):
            frame = stat.traceback[0]
            print(f"#{index}: {frame.filename}:{frame.lineno} ({round(stat.size/1024,1)} KiB):")
            line = getline(frame.filename, frame.lineno).strip()
            print('    '+line)
        other = topStatsFiltered[limit:]
        if other:
            print(f"{len(other)} other: {round(sum(stat.size for stat in other)/1024,1)} KiB")
        total = round(sum(stat.size for stat in topStatsFiltered)/1024,1)
        difference = total-self.previousTotal
        print(f"Total {total} KiB - Difference: {'+' if difference >= 0 else ''}{round(difference,1)} KiB\nCalculated in {int((time()-starttime)*1000)}ms\n{'-='*32}-")
        # print(f"Total unfiltered: {round(sum(stat.size for stat in topStatsSnapshot.statistics('lineno'))/1024,1)} KiB - Total filtered: {total} KiB - Difference: {'+' if difference >= 0 else ''}{round(difference,1)} KiB\n{'-='*32}-")
        self.previousTotal = total

def setup(bot):
  bot.add_cog(Common(bot))
  