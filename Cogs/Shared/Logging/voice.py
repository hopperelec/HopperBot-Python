from discord.ext import commands

class LogVoice(commands.Cog):
    location = "./Cogs/Shared/Logging/"
    names = ["logVoice","logging","all"]
    prefixes = []
    description = "Automatically logs every time a user joins or leaves a voice channel"

    def __init__(self,bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(self,member,before,after):
        if after.channel != before.channel and not member.bot:
            if after.channel == None:
                self.bot.main.log(self,f"`{member.display_name}` has left VC `{before.channel.name}`",before.channel.guild)
            else:
                self.bot.main.log(self,f"`{member.display_name}` has joined VC `{after.channel.name}`",after.channel.guild)

    @commands.Cog.listener()
    async def on_ready(self):
        self.servers,self.configs = self.bot.main.setup(self.names)
        self.bot.main.started(self.names[0])

def setup(bot):
  bot.add_cog(LogVoice(bot))
  