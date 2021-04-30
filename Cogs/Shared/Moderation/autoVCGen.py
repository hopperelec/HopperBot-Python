from discord.ext import commands

class AutoVCGen(commands.Cog):
    location = "./Cogs/Shared/Moderation/"
    names = ["autoVCGen"]
    prefixes = []
    description = "Automatically makes sure there is always only one available voice channel per category"

    def __init__(self,bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.servers,self.configs = self.bot.main.setup(self.names)
        self.originalChannels = [inner for outer in [[self.bot.get_guild(guild).get_channel(channel) for channel in self.configs[guild]["originalChannels"]] for guild in self.configs.keys()] for inner in outer]
        self.originalChannelNames = [vc.name[:-1] for vc in self.originalChannels]
        for vc in self.originalChannels:
            await self.handleVoiceChannel(vc)
        self.bot.main.started(self.names[0])

    async def handleVoiceChannel(self,channel):
        if channel.name[:-1] in self.originalChannelNames:
            keepSorting = True
            while keepSorting:
                keepSorting = False
                found = 0
                typevcs = sorted([guildchannel for guildchannel in channel.guild.channels if guildchannel.name[:-2] == channel.name[:-2]], key=lambda guildchannel: guildchannel.name)
                for i,typevc in enumerate(typevcs):
                    if len(typevc.members) == 0:
                        found += 1
                        if found >= 2:
                            self.bot.main.log(self,"An "+channel.name[:-2]+" VC has been removed!",channel.guild)  
                            await typevc.delete()
                    elif found == 1:
                        keepSorting = True
                        for member in typevc.members:
                            self.bot.main.log(self,f"{member.display_name} (`{member.name}#{member.discriminator}`) has been moved back to `{typevcs[i-1].name}`!",channel.guild)
                            await member.move_to(typevcs[i-1])
                if found == 0:
                    newChannel = await channel.clone()
                    self.bot.main.log(self,"An "+channel.name[:-2]+" VC has been added!",channel.guild)
                    await newChannel.edit(name=channel.name[:-1]+str(len(typevcs)+1))
                    await newChannel.edit(position=channel.position+1)
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if after.channel != None:
            await self.handleVoiceChannel(after.channel)
        if before.channel != None:
            await self.handleVoiceChannel(before.channel)

def setup(bot):
  bot.add_cog(AutoVCGen(bot))
  