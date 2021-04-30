from discord.ext import commands

class Poll(commands.Cog):
    location = "./Cogs/Shared/Fun/"
    names = ["poll","fun","all"]
    prefixes = ["?"]
    description = "Allows users to generate polls"

    def __init__(self,bot):
        self.bot = bot

    async def cog_check(self,ctx):
        ctx.checkDefinitions = ["is disabled in this server",f"uses prefix `{self.prefixes[0]}` but `{ctx.prefix}` was entered"]
        ctx.checkResults = [await self.bot.main.getCogConfig(self.names,ctx.guild) != None,ctx.prefix in self.prefixes]
        return not False in ctx.checkResults

    @commands.command(description="Deletes (limit) of the previous messages in the channel")
    async def poll(self,ctx,*question):
        await ctx.message.delete()
        message = await ctx.channel.send(" ".join(question))
        await message.add_reaction('👍')
        await message.add_reaction('👎')
        await message.add_reaction('🤷')

    @commands.Cog.listener()
    async def on_ready(self):
        self.servers,self.configs = self.bot.main.setup(self.names)
        self.bot.main.started(self.names[0])

def setup(bot):
    bot.add_cog(Poll(bot))
  