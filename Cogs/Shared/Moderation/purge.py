from discord.ext import commands

class Purge(commands.Cog):
    location = "./Cogs/Shared/Moderation/"
    names = ["purge","moderation","all"]
    prefixes = ["!"]
    description = "Allows the mass deletion of messages through the bot"

    def __init__(self,bot):
        self.bot = bot

    async def cog_check(self,ctx):
        ctx.checkDefinitions = ["is disabled in this server","requires the 'manage messages' permission in the channel",f"uses prefix `{self.prefixes[0]}` but `{ctx.prefix}` was entered"]
        ctx.checkResults = [await self.bot.main.getCogConfig(self.names,ctx.guild) != None,ctx.author.permissions_in(ctx.channel).manage_messages,ctx.prefix in self.prefixes]
        return not False in ctx.checkResults

    @commands.command(description="Deletes (limit) of the previous messages in the channel")
    async def purge(self,ctx,limit="2047"):
        await ctx.channel.purge(limit=int(limit)+1)

    @commands.Cog.listener()
    async def on_ready(self):
        self.servers,self.configs = self.bot.main.setup(self.names)
        self.bot.main.started(self.names[0])

def setup(bot):
  bot.add_cog(Purge(bot))
  