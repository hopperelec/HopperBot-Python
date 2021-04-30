from discord.ext import commands

class Info(commands.Cog):
    location = "./Cogs/Shared/Info/"
    names = ["info"]
    prefixes = ["?"]
    description = "Allows admins to add informational commands to quickly respond to people's questions or promote something"

    def __init__(self,bot):
        self.bot = bot

    async def cog_check(self,ctx):
        ctx.checkDefinitions = [f"uses prefix `{self.prefixes[0]}` but `{ctx.prefix}` was entered"]
        ctx.checkResults = [ctx.prefix in self.prefixes]
        return not False in ctx.checkResults

    @commands.Cog.listener()
    async def on_ready(self):
        self.servers,self.configs = self.bot.main.setup(self.names)
        
        for guild,config in self.configs.items():
            for name,response in config["info"].items():
                @commands.command(name=name, description="Info command")
                @self.guild_check(guild)
                async def cmd(self, ctx):
                    await ctx.send(response)
                cmd.cog = self
                self.__cog_commands__ += (cmd,)
                self.bot.add_command(cmd)
        
        self.bot.main.started(self.names[0])
        
    def guild_check(self,guild):
        async def predicate(ctx):
            print(ctx.guild.id)
            print(guild)
            return ctx.guild.id == guild
        return commands.check(predicate)

def setup(bot):
  bot.add_cog(Info(bot))
  