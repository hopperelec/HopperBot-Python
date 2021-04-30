from discord.ext import commands

class LogCommand(commands.Cog):
    location = "./Cogs/Shared/Logging/"
    names = ["logs"]
    prefixes = ["!"]
    description = "Allows the bot to log debug information into a channel on the server"

    def __init__(self,bot):
        self.bot = bot

    async def cog_check(self,ctx):
        config = await self.bot.main.getCogConfig(self.names,ctx.guild)
        perms = ctx.author.permissions_in(ctx.guild.get_channel(config["channel"]))
        ctx.checkDefinitions = ["is disabled in this server","requires the 'send messages' permission in the log channel","requires the 'read message history' permission in the log channel",f"uses prefix `{self.prefixes[0]}` but `{ctx.prefix}` was entered"]
        ctx.checkResults = [config != None,perms.send_messages,perms.read_message_history,ctx.prefix == "!"]
        return not False in ctx.checkResults

    @commands.command(description="Logs a message locally. Logging sends a message to the relevant server, log file and bot console.")
    async def log(self,ctx,*message):
        if len(message) == 0:
            ctx.send("Must provide message to log!")
        else:
            self.bot.main.log(self," ".join(message),ctx.guild)

    @commands.Cog.listener()
    async def on_ready(self):
        self.servers,self.configs = self.bot.main.setup(self.names)
        self.bot.main.started(self.names[0])

def setup(bot):
  bot.add_cog(LogCommand(bot))
  