from asyncio import run_coroutine_threadsafe
from json import load as jsonload
from datetime import datetime
from time import time
from difflib import SequenceMatcher
from random import choice
from re import sub

class Common:
    def __init__(self,bot):
        self.bot = bot
        # self.clearLogs()

        with open("config.json","r") as jsonfile:
            self.config = jsonload(jsonfile)

    def setup(self,names):
        servers = [server for server in self.config["servers"] if any(name in [extension["name"] for extension in server["used_extensions"]] for name in names)]
        configs = {server["id"]:next((extension for extension in server["used_extensions"] if extension["name"] == names[0]),{}) for server in servers}
        return servers,configs

    def log(self,cog,message,server=None):
        def toServer(server):
            config = next((extension for extension in next(serverConfig for serverConfig in self.config["servers"] if serverConfig["id"] == server.id)["used_extensions"] if extension["name"] == "logs"), None)
            channel = None
            try:
                if cog != "main" and "logChannel" in cog.configs.keys():
                    channel = cog.configs["logChannel"]
                elif config != None:
                    channel = config["channel"]
                if channel != None:
                    run_coroutine_threadsafe(server.get_channel(channel).send(f"**{cogname}:** {sub('<@![0-9]{17,19}>','{mention}',str(message))}"),self.bot.loop)
            except:
                pass

        cogname = cog if cog == "main" else cog.names[0]
        coglocation = "./" if cog == "main" else cog.location
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {cogname}{'' if server == None else f'[Server: {server.id} / {server.name}]'}: {message}")
        with open(coglocation+"logs.txt","a+") as logfile:
            logfile.write(f"[{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}]{'' if server == None else str(server.id)+'/'+server.name+':'} {message}\n")
        if server != None:
            toServer(server)
        else:
            for server in self.config["servers"]:
                toServer(self.bot.get_guild(server["id"]))

    def started(self,name):
        self.log("main",f"{name} started after {int((time()-self.bot.extensiontime)*1000)}ms")

    def clearLogs(self):
        from os import walk
        for root, dirs, files in walk("./", topdown=False):
            for name in files:
                if name == "logs.txt":
                    with open(root+"/logs.txt","w") as logfile:
                        logfile.write("")

    def getSimilar(self,getFrom,inList,outTests,name):
        def similar(data,cutoff):
            result = (None,0)
            s = SequenceMatcher()
            s.set_seq2(getFrom)
            for x in data.keys():
                s.set_seq1(data[x])
                if s.ratio() >= cutoff and s.real_quick_ratio() >= cutoff and s.quick_ratio() >= cutoff and s.ratio() >= result[1]:
                    result = (x,s.ratio())
            if result[0] == None:
                raise ValueError
            else:
                return result[0]

        for outTest in outTests.keys():
            try:
                getFrom = choice([s for s in inList if getFrom.lower() in outTests[outTest](s).lower()])
                return getFrom,f"in the {name}'s {outTest}"
            except:
                pass
        for outTest in outTests.keys():
            try:
                getFrom = similar({s:outTests[outTest](s) for s in inList},0.5)
                return getFrom,f"somewhat similar to the {name}'s {outTest}"
            except:
                pass
        getFrom = similar({s:"\n ".join([outTests[outTest](s) for outTest in outTests.keys()]) for s in inList},0)
        return getFrom,f"not very similar to any of the other {name}s"

    async def getCogConfig(self,names,server):
        return next((extension for extension in next(serverConfig for serverConfig in self.config["servers"] if serverConfig["id"] == server.id)["used_extensions"] if extension["name"] in names), None)

