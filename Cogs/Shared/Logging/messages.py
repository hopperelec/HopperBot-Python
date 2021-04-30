from discord.ext import commands

class LogMessages(commands.Cog):
    location = "./Cogs/Shared/Logging/"
    names = ["logMessages","logging","all"]
    prefixes = []
    description = "Automatically logs every time a user message is edited or deleted"

    def __init__(self,bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if not message.author.bot and not message.content.startswith("!purge"):
            self.bot.main.log(self,f"A message by `{message.author.display_name}` ({message.author.name}#{message.author.discriminator}) in `{message.channel.name}` that said `{message.content}` was deleted!",message.guild)
 
    @commands.Cog.listener()
    async def on_message_edit(self, message_before, message_after):
        if not message_before.author.bot and not message_before.content == message_after.content:
            self.bot.main.log(self,f"Message with ID `{message_before.id}` by `{message_before.author.display_name}` (`{message_before.author.name}#{message_before.author.discriminator}`) in `{message_before.channel.name}` has been edited from saying `{message_before.content}` to say `{message_after.content}`",message_before.guild)

    @commands.Cog.listener()
    async def on_ready(self):
        self.servers,self.configs = self.bot.main.setup(self.names)
        self.bot.main.started(self.names[0])

def setup(bot):
  bot.add_cog(LogMessages(bot))
  