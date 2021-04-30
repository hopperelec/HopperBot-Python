from discord.ext import commands

class Wiki(commands.Cog):
    location = "./Cogs/dSMP/"
    names = ["wiki","dSMP"]
    prefixes = ["?"]
    description = "Allows for people to quickly respond to questions by linking them to a page on the Wiki"

    def __init__(self,bot):
        self.bot = bot

    async def cog_check(self,ctx):
        ctx.checkDefinitions = ["is disabled in this server",f"uses prefix `{self.prefixes[0]}` but `{ctx.prefix}` was entered"]
        ctx.checkResults = [await self.bot.main.getCogConfig(self.names,ctx.guild) != None,ctx.prefix in self.prefixes]
        return not False in ctx.checkResults

    @commands.command(description="Responds with a link to the page on the wiki")
    async def wiki(self,ctx,*page):
        if page == []:
            page = ["Demonetized","SMP","Wiki"]
        await ctx.send("https://demonetized-smp.fandom.com/wiki/"+"_".join(page))

    @commands.Cog.listener()
    async def on_ready(self):
        self.servers,self.configs = self.bot.main.setup(self.names)
        self.bot.main.started(self.names[0])

def setup(bot):
  bot.add_cog(Wiki(bot))
  