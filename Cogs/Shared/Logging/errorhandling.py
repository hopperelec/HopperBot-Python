import discord
from discord.ext import commands

class ErrorHandling(commands.Cog):
    location = "./Cogs/Shared/Logging/"
    names = ["errorhandling","all"]
    prefixes = []
    description = "Lets command users know that their command failed and why"

    async def temp(self,ctx,text):
        self.bot.main.log(self,f"{str(ctx.author)} attempted to use the command {ctx.command} but got an error!\n{text}",ctx.guild)
        if type(ctx.channel) == discord.TextChannel:
            await ctx.send(text+f", {ctx.author.mention}",delete_after=10); await ctx.message.delete(delay=10)
        else:
            await ctx.send(text)

    @commands.Cog.listener()
    async def on_command_error(self,ctx,error):
        if await self.bot.main.getCogConfig(self.names,ctx.guild) != None:
            self.bot.main.log(self,error,ctx.guild)
            if isinstance(error,commands.CheckFailure):
                await self.temp(ctx,f"Command disabled here! `{ctx.command}` {', '.join([check for i,check in enumerate(ctx.checkDefinitions) if not ctx.checkResults[i]])}")
            elif isinstance(error,commands.CommandNotFound):
                pass
            elif isinstance(error,commands.DisabledCommand):
                await self.temp(ctx,f"`{ctx.command}` has been temperarily disabled, {ctx.author.mention}")
            elif isinstance(error,commands.TooManyArguments):
                await self.temp(ctx,f"Too many arguments entered into `{ctx.command}`, {ctx.author.mention}")
            elif isinstance(error,commands.CommandOnCooldown):
                await self.temp(ctx,f"'{ctx.command} is on cooldown, {ctx.author.mention}. It can be used {error.cooldown.rate} times per {int(error.cooldown.per)/60} minutes. There is {int(error.retry_after)} seconds left till your cooldown ends!")
            elif isinstance(error,commands.MissingRequiredArgument):
                await self.temp(ctx,f"Missing required arguments for `{ctx.command}`! Review help information for it's cog below")
                await self.bot.get_command("help").callback(ctx,ctx,ctx.command.cog_name)
            else:
                raise error
                await self.temp(ctx,error)
        else:
            self.bot.main.log(self,f"{str(ctx.author)} attempted to use the command {ctx.command} but got an error! However, ErrorHandling is disabled for this server, so nothing will happen.",ctx.guild)

    def __init__(self,bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.servers,self.configs = self.bot.main.setup(self.names)
        self.bot.main.started(self.names[0])

def setup(bot):
  bot.add_cog(ErrorHandling(bot))
  