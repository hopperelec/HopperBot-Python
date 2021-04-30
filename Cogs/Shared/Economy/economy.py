import discord
from discord.ext import commands,tasks
from random import randint,choice,choices
from string import ascii_letters,digits
from datetime import datetime,timedelta
from math import floor
from humanreadable import Time as humanReadable
import aiomysql
from dotenv import load_dotenv
from os import getenv
from pymysql.err import OperationalError

class Economy(commands.Cog):
    location = "./Cogs/Shared/Economy/"
    names = ["economy"]
    prefixes = ["$","£"]
    description = "Allows for members to get virtual rewards for interacting with the server through a virtual economy"
    mmhm = False
    ready = False
    loops = 0
    items = []
    cooldownTypes = {}

    def __init__(self,bot):
        self.bot = bot

    async def cog_check(self,ctx):
        config = await self.bot.main.getCogConfig(self.names,ctx.guild)
        ctx.checkDefinitions = ["is disabled in this channel",f"uses prefix `{self.prefixes[0]}` but `{ctx.prefix}` was entered","isn't ready yet, try again in a few seconds"]
        ctx.checkResults = [config["commandsChannel"] == ctx.channel.id,ctx.prefix in self.prefixes,self.ready]
        if not False in ctx.checkResults:
            try:
                await self.mysql.execute("SELECT * FROM members WHERE user_id = %s and server_id = %s",(ctx.author.id,ctx.guild.id))
            except OperationalError:
                await self.mysqlReconnect()
                await self.mysql.execute("SELECT * FROM members WHERE user_id = %s and server_id = %s",(ctx.author.id,ctx.guild.id))
            if await self.mysql.fetchall() == ():
                await self.mysql.execute("INSERT INTO `members` (`user_id`,`server_id`,`cash`,`bank`) VALUES (%s,%s,%s,%s)",(ctx.author.id,ctx.guild.id,config["defaultData"]["cash"],config["defaultData"]["bank"]))
            await self.mysql.execute("UPDATE members SET inactiveTime = (now() + INTERVAL 3 day) WHERE user_id = %s and server_id = %s",(ctx.author.id,ctx.guild.id))
        return not False in ctx.checkResults

    async def is_owner(ctx):
        ctx.checkDefinitions = ["it can only be used by HopperElec"]
        ctx.checkResults = [ctx.author.id == 348083986989449216]
        return ctx.checkResults[0]

    async def hasBank(self,member):
        await self.mysql.execute("SELECT * FROM economy.members AS m INNER JOIN economy.inventories AS inv ON m.user_id=inv.user_id AND m.server_id=inv.server_id INNER JOIN economy.items AS i ON i.item_id=inv.item_id WHERE m.user_id = %s AND i.name = 'bank account'",(member.id,))
        return (await self.mysql.fetchall()) != ()\

    async def getCooldownTypes(self,cooldowns):
        cooldownTypes = []
        for cooldown in cooldowns:
            await self.mysql.execute("SELECT * FROM cooldownTypes WHERE name = %s",(cooldown,))
            cooldownTypes += [await self.mysql.fetchone()]
        return cooldownTypes

    async def onCooldown(self,user_id,server_id,cooldowns=[]):
        cooldowns = await self.getCooldownTypes(cooldowns+["global"])
        for cooldown in cooldowns:
            if cooldown["bucket"] == "user":
                await self.mysql.execute("SELECT * FROM cooldowns WHERE user_id = %s AND name = %s AND expiry > now() AND usages = %s",(user_id,cooldown["name"],cooldown["number"],))
            elif cooldown["bucket"] == "member":
                await self.mysql.execute("SELECT * FROM cooldowns WHERE user_id = %s AND server_id = %s AND name = %s AND expiry > now() AND usages = %s",(user_id,server_id,cooldown["name"],cooldown["number"],))
            else:
                await self.mysql.execute("SELECT * FROM cooldowns WHERE server_id = %s AND name = %s AND expiry > now() AND usages = %s",(server_id,cooldown["name"],cooldown["number"],))
            res = await self.mysql.fetchall()
            if res != ():
                embed = self.embeds["Cooldown"].copy()
                embed.add_field(name="User",value=f"{self.bot.get_user(user_id).name}#{self.bot.get_user(user_id).discriminator}")
                embed.add_field(name="Cooldown name",value=cooldown["name"])
                embed.add_field(name="Cooldown bucket",value=cooldown["bucket"])
                embed.add_field(name="Usages",value=cooldown["number"])
                embed.add_field(name="Length",value=cooldown["length"])
                embed.add_field(name="Expiry",value=res[0]["expiry"])
                embed.add_field(name="Countdown",value=f"https://google.com/search?q={int((res[0]['expiry']-datetime.now()).total_seconds())}s+timer")
                await self.bot.get_guild(server_id).get_channel(self.configs[server_id]["commandsChannel"]).send(embed=embed)
                return True
        await self.addCooldown(user_id,server_id,["global"])
        return False

    async def addCooldown(self,user_id,server_id,cooldowns):
        cooldowns = await self.getCooldownTypes(cooldowns)
        for cooldown in cooldowns:
            if cooldown["bucket"] == "user":
                await self.mysql.execute("SELECT usages FROM cooldowns WHERE user_id = %s AND name = %s",(user_id,cooldown["name"]))
            elif cooldown["bucket"] == "member":
                await self.mysql.execute("SELECT usages FROM cooldowns WHERE user_id = %s AND server_id = %s AND name = %s",(user_id,server_id,cooldown["name"]))
            else:
                await self.mysql.execute("SELECT usages FROM cooldowns WHERE server_id = %s AND name = %s",(server_id,cooldown["name"]))
            res = await self.mysql.fetchall()
            if res == ():
                await self.mysql.execute("INSERT INTO cooldowns (`user_id`,`server_id`,`name`,`expiry`) VALUES (%s,%s,%s,%s)",(user_id,server_id,cooldown["name"],datetime.now()+timedelta(seconds=humanReadable(cooldown["length"]).seconds)))
            else:
                if res[0]["usages"] == cooldown["number"]:
                    expiry = datetime.now()+timedelta(seconds=humanReadable(cooldown["length"]).seconds)
                    if cooldown["bucket"] == "user":
                        await self.mysql.execute("UPDATE cooldowns SET usages = 1, expiry = %s WHERE user_id = %s AND name = %s",(expiry,user_id,cooldown["name"]))
                    elif cooldown["bucket"] == "member":
                        await self.mysql.execute("UPDATE cooldowns SET usages = 1, expiry = %s WHERE user_id = %s AND server_id = %s AND name = %s",(expiry,user_id,server_id,cooldown["name"]))
                    else:
                        await self.mysql.execute("UPDATE cooldowns SET usages = 1, expiry = %s WHERE server_id = %s AND name = %s",(expiry,server_id,cooldown["name"]))
                else:
                    if cooldown["bucket"] == "user":
                        await self.mysql.execute("UPDATE cooldowns SET usages = usages + 1 WHERE user_id = %s AND name = %s",(user_id,cooldown["name"]))
                    elif cooldown["bucket"] == "member":
                        await self.mysql.execute("UPDATE cooldowns SET usages = usages + 1 WHERE user_id = %s AND server_id = %s AND name = %s",(user_id,server_id,cooldown["name"]))
                    else:
                        await self.mysql.execute("UPDATE cooldowns SET usages = usages + 1 WHERE server_id = %s AND name = %s",(server_id,cooldown["name"]))

    async def mysqlReconnect(self):
        self.mysql = await (await aiomysql.connect(host='127.0.0.1',port=3306,user='root',password=getenv("MYSQL"),db='economy',loop=self.bot.loop,autocommit=True)).cursor(aiomysql.DictCursor)

    @commands.Cog.listener()
    async def on_ready(self):
        self.servers,self.configs = self.bot.main.setup(self.names)

        load_dotenv()
        await self.mysqlReconnect()
        await self.mysql.execute("SELECT * FROM hidden_config")
        self.hidden_config = {option["key"]:option["value"] for option in await self.mysql.fetchall()}
        await self.mysql.execute("SELECT * FROM cooldownTypes")
        self.cooldownTypes = {cooldownType["name"]:cooldownType for cooldownType in await self.mysql.fetchall()}
        self.embeds = {
            "Store": "List of all items that can be bought through $buy",
            "Economy leaderboard": "List of peoples' money in the economy in order of balance",
            "Economy CASH leaderboard": "List of peoples' money in the economy in order of cash balance",
            "Cooldown": "This user is currently on one or more cooldowns that effects the above command!",
            "Jackpot": "Current money placed in jackpot. One of these members will be chosen based on their bet to win the total on the hour."
        }
        for title,description in self.embeds.items():
            self.embeds[title] = discord.Embed(title=title,description=description,color=0xe31313).set_footer(text="Created by HopperElecYT#3060")
        self.ecoloop.start()

        self.bot.main.started(self.names[0])
        self.ready = True

        if "mmhm" in self.bot.main.config["enabled_addons"]:
            from Cogs.Shared.Economy.mcrcon import mcrsend
            if mcrsend(["say HopperBot has connected through RCON successfully"],self,"StartMessage",None):
                self.MMHMservers,self.MMHMonfigs = self.bot.main.setup("mmhm")
                self.bot.main.started("mmhm")
                self.mmhm = True

    @tasks.loop(minutes=1)
    async def ecoloop(self):
        try:
            await self.mysql.execute("SELECT * FROM serverNames")
        except OperationalError:
            await self.mysqlReconnect()
            await self.mysql.execute("SELECT * FROM serverNames")

        servers = {server['server_id']:server['serverName'] for server in await self.mysql.fetchall()}
        for server in self.configs:
            name =  self.bot.get_guild(server).name
            if server in servers:
                if not name == servers[server]:
                    await self.mysql.execute("UPDATE serverNames SET serverName = %s WHERE server_id = %s",(name,server))
            else:
                await self.mysql.execute("INSERT INTO `serverNames` (`serverName`,`server_id`) VALUES (%s,%s)",(name,server))
                
        await self.mysql.execute("SELECT * FROM usernames")
        users = {user['user_id']:user['username'] for user in await self.mysql.fetchall()}
        await self.mysql.execute("SELECT DISTINCT user_id FROM members")
        for member in await self.mysql.fetchall():
            user = self.bot.get_user(member['user_id'])
            name = f"{user.name}#{user.discriminator}"
            if member['user_id'] in users:
                if not name == users[member['user_id']]:
                    await self.mysql.execute("UPDATE usernames SET username = %s WHERE user_id = %s",(name,member['user_id']))
            else:
                await self.mysql.execute("INSERT INTO `usernames` (`username`,`user_id`) VALUES (%s,%s)",(name,member['user_id']))

        await self.mysql.execute("SELECT * FROM items ORDER BY item_id")
        items = await self.mysql.fetchall()
        if self.items != items:
            self.items = items
            self.storeEmbed = self.embeds["Store"].copy()
            for item in self.items:
                self.storeEmbed.add_field(name=f"{item['name']} | ${item['cost']} per {item['duration']}",value=item['description'])

        await self.mysql.execute("SELECT * FROM inventories")
        inventories = await self.mysql.fetchall()
        currentTime = datetime.now()
        for inv in inventories:
            name = items[inv['item_id']-1]['name']
            if inv["expiry"] < currentTime:
                mention = self.bot.get_guild(inv["server_id"]).get_member(inv["user_id"])
                channel = self.bot.get_guild(inv["server_id"]).get_channel(self.configs[inv["server_id"]]["commandsChannel"])
                item = items[inv["item_id"]-1]
                if inv["auto-renew"] == b'\x01':
                    await self.mysql.execute("SELECT cash FROM members WHERE user_id = %s",(inv["user_id"],))
                    if (await self.mysql.fetchone())["cash"] >= item["cost"]:
                        await self.mysql.execute("UPDATE members SET cash = cash-%s WHERE user_id = %s AND server_id = %s",(item["cost"],inv["user_id"],inv["server_id"]))
                        await self.mysql.execute("UPDATE inventories SET expiry = %s WHERE item_id = %s AND user_id = %s AND server_id = %s",(currentTime+timedelta(seconds=humanReadable(item["duration"]).seconds),inv["item_id"],inv["user_id"],inv["server_id"]))
                        await channel.send(f"Your {name} has been renewed for a cost of {item['cost']}, {mention}!")
                        continue
                    await channel.send(f"Your {name} has expired but has not been renewed because you don't have enough money available in your cash balance, {mention}!")
                else:
                    await channel.send(f"Your {name} has expired, {mention}!")
                await self.mysql.execute("DELETE FROM inventories WHERE user_id = %s and server_id = %s and item_id = %s",(inv["user_id"],inv["server_id"],inv["item_id"]))

        if currentTime.minute == 0:
            for server in self.configs:
                await self.mysql.execute("SELECT user_id,jackpot FROM members WHERE server_id = %s AND jackpot > 0",(server,))
                res = await self.mysql.fetchall()
                if res != ():
                    guild = self.bot.get_guild(server)
                    amounts = [member["jackpot"] for member in res]
                    winner = choices([member["user_id"] for member in res],weights=amounts,k=1)
                    total = sum(amounts)
                    await guild.get_channel(self.configs[server]["commandsChannel"]).send(f"Congratulations, {guild.get_member(winner[0]).mention}, on winning the jackpot of {total}!")
                    await self.mysql.execute("UPDATE members SET cash = cash + %s WHERE user_id = %s AND server_id = %s",(total,winner[0],server))
            await self.mysql.execute("UPDATE members SET jackpot = 0")

    async def getMember(self,ctx,getFrom):
        if ctx.message.mentions != []:
            member = ctx.message.mentions[0]
            await ctx.send(f"{ctx.author.mention} Using {member.name}#{member.discriminator} because they're the first person in your mentions")
        else:
            inList = [member for member in ctx.guild.members if not member.bot]
            outTests = {"name": lambda s: s.name+"#"+s.discriminator,"id": lambda s: str(s.id)}
            member,reason = self.bot.main.getSimilar(getFrom,inList,outTests,"member")
            await ctx.send(f"{ctx.author.mention} Using {member.name}#{member.discriminator} because what you entered is {reason}")
        return member

    @commands.Cog.listener()
    async def on_message(self,message):
        if self.ready and message.channel.id in self.configs[message.guild.id]["textChannels"] and len(message.content) >= 7 and not message.content[0] in ['/','$','£','!','?'] and not message.author.bot:
            await self.mysql.execute("SELECT allowMsg,inactiveTime FROM members WHERE user_id = %s and server_id = %s",(message.author.id,message.guild.id))
            res = await self.mysql.fetchall()
            if res != ():
                currentTime = datetime.now()
                if currentTime > res[0]["allowMsg"] and currentTime < res[0]["inactiveTime"]:
                    await self.mysql.execute("UPDATE members SET allowMsg = %s, cash = cash+FLOOR(RAND()*5) WHERE user_id = %s and server_id = %s",(datetime.now()+timedelta(seconds=self.hidden_config["messageTime"]),message.author.id,message.guild.id))

    @commands.command(description="Displays the user's balance",aliases=["bal","bank","cash","bankbal","bankbalance"])
    async def balance(self,ctx,*member):
        if not await self.onCooldown(ctx.author.id,ctx.guild.id,["checkBalances"]):
            if member == ():
                member = ctx.author
            else:
                member = await self.getMember(ctx," ".join(member))
            await self.mysql.execute("SELECT cash,bank FROM members WHERE user_id = %s and server_id = %s",(member.id,ctx.guild.id))
            data = await self.mysql.fetchone()
            await ctx.send(embed=(discord.Embed(
                title=f"Balance of {member.name}#{member.discriminator}",
                description=f"Bank : {data['bank']} | Cash : {data['cash']}",
                color=0xe31313).set_footer(text=f"Requested by {ctx.author}\nCreated by HopperElecYT#3060")).set_thumbnail(url=member.avatar_url))
            await self.addCooldown(ctx.author.id,ctx.guild.id,["checkBalances"])

    @commands.command(description="Lists all members in the server in order of how much money they have",aliases=["lb"])
    async def leaderboard(self,ctx,cash=None):
        if not await self.onCooldown(ctx.author.id,ctx.guild.id,["checkBalances"]):
            if cash:
                if await self.onCooldown(ctx.author.id,ctx.guild.id,["lbCash"]):
                    return
                embed = self.embeds["Economy CASH leaderboard"].copy()
                await self.mysql.execute("SELECT user_id,cash,bank FROM members WHERE server_id = %s and inactiveTime > now() ORDER BY cash DESC",(ctx.guild.id,))
            else:
                if await self.onCooldown(ctx.author.id,ctx.guild.id,["lbTotal"]):
                    return
                embed = self.embeds["Economy leaderboard"].copy()
                await self.mysql.execute("SELECT user_id,cash,bank FROM members WHERE server_id = %s and inactiveTime > now() ORDER BY cash+bank DESC",(ctx.guild.id,))
            members = await self.mysql.fetchall()
            for i,member in enumerate(members):
                obj = ctx.guild.get_member(member["user_id"])
                if obj:
                    name = f"{obj.name}#{obj.discriminator}"
                else:
                    name = "Unknown member (they likely left the server)"
                embed.add_field(name=f"{i+1}. {name}",value=f"Cash: {member['cash']} | Bank: {member['bank']}",inline=False)
            await ctx.send(embed=embed)
            await self.addCooldown(ctx.author.id,ctx.guild.id,["checkBalances"])

    @commands.command(description="Moves money from cash to a bank, if available",aliases=["dep"])
    async def deposit(self,ctx,amount="all"):
        if not await self.onCooldown(ctx.author.id,ctx.guild.id,["deposit"]):
            if await self.hasBank(ctx.author):
                await self.mysql.execute("SELECT cash FROM members WHERE user_id = %s and server_id = %s",(ctx.author.id,ctx.guild.id))
                cash = (await self.mysql.fetchone())["cash"]
                if amount == "all":
                    if cash > 0:
                        amount = cash
                    else:
                        await ctx.send(f"You have nothing to deposit, {ctx.author.mention}!")
                        return
                try:
                    amount = abs(int(amount))
                except ValueError:
                    await ctx.send(f"Invalid amount '{amount}', {ctx.author.mention}!")
                else:
                    if cash >= amount:
                        await ctx.send(f"Depositing {amount} into the bank, {ctx.author.mention}!")
                        await self.mysql.execute("UPDATE members SET cash = cash-%s, bank = bank+%s WHERE user_id = %s and server_id = %s",(amount,amount,ctx.author.id,ctx.guild.id))
                        await self.addCooldown(ctx.author.id,ctx.guild.id,["deposit"])
                    else:
                        await ctx.send(f"You don't have {amount} to deposit, {ctx.author.mention}!")
            else:
                await ctx.send(f"You don't own a bank account yet, {ctx.author.mention}! $buy it from the $store")
    
    @commands.command(description="Moves money from bank to cash, if available",aliases=["with"])
    async def withdraw(self,ctx,amount="all"):
        if not await self.onCooldown(ctx.author.id,ctx.guild.id,["withdraw"]):
            if await self.hasBank(ctx.author):
                await self.mysql.execute("SELECT bank FROM members WHERE user_id = %s and server_id = %s",(ctx.author.id,ctx.guild.id))
                bank = (await self.mysql.fetchone())["bank"]
                if amount == "all":
                    if bank > 1:
                        amount = bank-1
                    else:
                        await ctx.send(f"You have nothing to withdraw, {ctx.author.mention}!")
                        return
                try:
                    amount = abs(int(amount))
                except ValueError:
                    await ctx.send(f"Invalid amount '{amount}', {ctx.author.mention}!")
                else:
                    if bank > amount:
                        await ctx.send(f"Withdrawing {amount} from the bank, {ctx.author.mention}!")
                        await self.mysql.execute("UPDATE members SET bank = bank-%s-1, cash = cash+%s WHERE user_id = %s and server_id = %s",(amount,amount,ctx.author.id,ctx.guild.id))
                        await self.addCooldown(ctx.author.id,ctx.guild.id,["withdraw"])
                    elif bank == amount:
                        await ctx.send(f"There is a $1 fee for withdraw, so you are unable to withdraw all of your money at once, {ctx.author.mention}!")
                    else:
                        await ctx.send(f"You don't have {amount} to withdraw, {ctx.author.mention}!")
            else:
                await ctx.send(f"You haven't unlocked the bank yet, {ctx.author.mention}! $buy it from the $store")

    @commands.command(description="Gambling at it's finest",aliases=["gamble","roll"])
    async def bet(self,ctx,amount):
        if not await self.onCooldown(ctx.author.id,ctx.guild.id,["bet"]):
            try:
                amount = abs(int(amount))
            except ValueError:
                await ctx.send(f"Invalid amount '{amount}', {ctx.author.mention}!")
            else:
                await self.mysql.execute("SELECT cash FROM members WHERE user_id = %s and server_id = %s",(ctx.author.id,ctx.guild.id))
                if (await self.mysql.fetchone())["cash"] >= amount:
                    if amount >= self.hidden_config["betMinimum"]:
                        if amount <= self.hidden_config["betMaximum"]:
                            if randint(1,100) <= self.hidden_config["betChance"]:
                                await ctx.send(f"{ctx.author.mention}, you won! Adding {amount} to your cash balance")
                                await self.mysql.execute("UPDATE members SET cash = cash+%s WHERE user_id = %s and server_id = %s",(amount,ctx.author.id,ctx.guild.id))
                            else:
                                await ctx.send(f"{ctx.author.mention}, you lost... Taking {amount} from your cash balance")
                                await self.mysql.execute("UPDATE members SET cash = cash-%s WHERE user_id = %s and server_id = %s",(amount,ctx.author.id,ctx.guild.id))
                            await self.addCooldown(ctx.author.id,ctx.guild.id,["bet"])
                        else:
                            await ctx.send(f"You must bet less than {self.hidden_config['betMaximum']}, {ctx.author.mention}!")
                    else:
                        await ctx.send(f"You must bet more than {self.hidden_config['betMinimum']}, {ctx.author.mention}!")
                else:
                    await ctx.send(f"You don't have {amount} in your cash balance available to bet, {ctx.author.mention}")

    @commands.command(description="Bet more money for a higher chance at taking it all back!",aliases=["jp"])
    async def jackpot(self,ctx,amount="info"):
        if amount == "info":
            if not await self.onCooldown(ctx.author.id,ctx.guild.id,["jackpotView"]):
                await self.mysql.execute("SELECT user_id,jackpot FROM members WHERE server_id = %s AND jackpot > 0",(ctx.guild.id,))
                res = await self.mysql.fetchall()
                embed = self.embeds["Jackpot"].copy()
                total = 0
                for member in res:
                    total += member["jackpot"]
                    user = ctx.guild.get_member(member["user_id"])
                    embed.add_field(name=f"{user.name}#{user.discriminator}",value=member["jackpot"])
                embed.add_field(name="Total",value=total,inline=False)
                await ctx.send(ctx.author.mention,embed=embed)
                await self.addCooldown(ctx.author.id,ctx.guild.id,["jackpotView"])
        else:
            if not await self.onCooldown(ctx.author.id,ctx.guild.id,["jackpotAdd"]):
                try:
                    amount = abs(int(amount))
                except ValueError:
                    await ctx.send(f"Invalid amount '{amount}', {ctx.author.mention}!")
                else:
                    await self.mysql.execute("SELECT cash FROM members WHERE user_id = %s and server_id = %s",(ctx.author.id,ctx.guild.id))
                    if (await self.mysql.fetchone())["cash"] >= amount:
                        await self.mysql.execute("UPDATE members SET cash = cash-%s, jackpot = jackpot+%s WHERE user_id = %s and server_id = %s",(amount,amount,ctx.author.id,ctx.guild.id))
                        await ctx.message.add_reaction("👍")
                        await self.addCooldown(ctx.author.id,ctx.guild.id,["jackpotAdd"])
                    else:
                        await ctx.send(f"You don't have {amount} in your cash balance available to bet, {ctx.author.mention}")

    @commands.command(description="Tries to steal some money from other members",aliases=["steal"])
    async def rob(self,ctx,amount,*member):
        if not await self.onCooldown(ctx.author.id,ctx.guild.id,["rob"]):
            try:
                amount = abs(int(amount))
            except ValueError:
                await ctx.send(f"Invalid amount '{amount}', {ctx.author.mention}")
            else:
                if member != ():
                    member = await self.getMember(ctx," ".join(member))
                    if member == ctx.author:
                        await ctx.send(f"You can't rob yourself, {ctx.author.mention}!")
                        return
                    await self.mysql.execute("SELECT cash FROM members WHERE user_id = %s and server_id = %s",(member.id,ctx.guild.id))
                    cash = (await self.mysql.fetchone())["cash"]
                else:
                    await self.mysql.execute("SELECT cash,user_id FROM members WHERE user_id <> %s and server_id = %s and cash > %s and inactiveTime > now()",(ctx.author.id,ctx.guild.id,amount))
                    choices = await self.mysql.fetchall()
                    if len(choices) == 0:
                        await ctx.send(f"There are no active members with a cash balance over {amount}, {ctx.author.mention}!")
                        return
                    else:
                        obj = choice(choices)
                        cash = obj["cash"]
                        member = ctx.guild.get_member(obj["user_id"])
                        await ctx.send(f"No member was specified, {ctx.author.mention}, so I have chosen {member.name}#{member.discriminator} by random!")
                if cash >= amount:
                    await self.mysql.execute("SELECT inactiveTime FROM members WHERE user_id = %s and server_id = %s",(ctx.author.id,ctx.guild.id))
                    if (await self.mysql.fetchone())["inactiveTime"] >= datetime.now():
                        if amount >= self.hidden_config["robMinimum"]:
                            if amount <= self.hidden_config["robMaximum"]:
                                variance = int(amount/100*self.hidden_config["robVariance"])
                                if randint(1,100) <= self.hidden_config["robChance"]:
                                    mode = randint(1,3)
                                    if mode == 1:
                                        await ctx.send(f"{ctx.author.mention}, the robbery was successful! You stole exactly {amount}")
                                        await self.mysql.execute("UPDATE members SET cash = cash+%s WHERE user_id = %s and server_id = %s",(amount,ctx.author.id,ctx.guild.id))
                                        await self.mysql.execute("UPDATE members SET cash = cash-%s WHERE user_id = %s and server_id = %s",(amount,member.id,ctx.guild.id))
                                    elif mode == 2:
                                        loss = randint(1,variance)
                                        await ctx.send(f"{ctx.author.mention}, the robbery was successful! However, you lost {loss} in the getaway so you ended up with {amount-loss}")
                                        await self.mysql.execute("UPDATE members SET cash = cash+%s WHERE user_id = %s and server_id = %s",(amount-loss,ctx.author.id,ctx.guild.id))
                                        await self.mysql.execute("UPDATE members SET cash = cash-%s WHERE user_id = %s and server_id = %s",(amount,member.id,ctx.guild.id))
                                    elif mode == 3:
                                        gain = randint(1,variance)
                                        await ctx.send(f"{ctx.author.mention}, the robbery was successful! You even gained an extra {gain} with the spare time so you ended up with {amount+gain}")
                                        await self.mysql.execute("UPDATE members SET cash = cash+%s WHERE user_id = %s and server_id = %s",(amount+gain,ctx.author.id,ctx.guild.id))
                                        await self.mysql.execute("UPDATE members SET cash = cash-%s WHERE user_id = %s and server_id = %s",(amount,member.id,ctx.guild.id))
                                else:
                                    loss = randint(amount-variance,amount+variance)
                                    await ctx.send(f"You were caught, {ctx.author.mention}... Taking a fine of {loss} from your cash balance")
                                    await self.mysql.execute("UPDATE members SET cash = cash-%s WHERE user_id = %s and server_id = %s",(loss,ctx.author.id,ctx.guild.id))
                                await self.addCooldown(ctx.author.id,ctx.guild.id,["rob"])
                            else:
                                await ctx.send(f"You must rob less than {self.hidden_config['robMaximum']}, {ctx.author.mention}!")
                        else:
                            await ctx.send(f"You must rob more than {self.hidden_config['robMinimum']}, {ctx.author.mention}!")
                    else:
                        await ctx.send(f"{member.name}#{member.discriminator} hasn't been active for 3 days so you cannot rob them right now, {ctx.author.mention}!")
                else:
                    await ctx.send(f"{member.name}#{member.discriminator} doesn't have {amount} in their cash balance to steal, {ctx.author.mention}!")

    @commands.command(description="Allows you to give other members some money")
    async def pay(self,ctx,amount,*member):
        if not await self.onCooldown(ctx.author.id,ctx.guild.id,["sendPay"]):
            try:
                amount = abs(int(amount))
            except ValueError:
                await ctx.send(f"Invalid amount '{amount}', {ctx.author.mention}")
            else:
                if member != ():
                    member = await self.getMember(ctx," ".join(member))
                    if member == ctx.author:
                        await ctx.send(f"You can't pay yourself, {ctx.author.mention}!")
                        return
                else:
                    await self.mysql.execute("SELECT user_id FROM members WHERE inactiveTime > now()")
                    choices = [member for member in [ctx.guild.get_member(member["user_id"]) for member in await self.mysql.fetchall()] if member != ctx.author and member.status != discord.Status.offline]
                    if len(choices) == 0:
                        await ctx.send(f"There are no online members available to give money to, {ctx.author.mention}. You can still manually select an offline member, though!")
                    else:
                        member = choice(choices)
                await self.mysql.execute("SELECT cash FROM members WHERE user_id = %s and server_id = %s",(ctx.author.id,ctx.guild.id))
                if (await self.mysql.fetchone())["cash"] >= amount:
                    if not await self.onCooldown(member.id,ctx.guild.id,["recievePay"]):
                        await self.mysql.execute("UPDATE members SET cash = cash-%s WHERE user_id = %s and server_id = %s",(amount,ctx.author.id,ctx.guild.id))
                        await self.mysql.execute("UPDATE members SET cash = cash+%s WHERE user_id = %s and server_id = %s",(amount,member.id,ctx.guild.id))
                        await ctx.message.add_reaction("👍")
                        await self.addCooldown(ctx.author.id,ctx.guild.id,["sendPay"])
                        await self.addCooldown(member.id,ctx.guild.id,["recievePay"])
                else:
                    await ctx.send(f"You don't have {amount} in your cash balance available to donate, {ctx.author.mention}!")

    @commands.command(description="Allows you to generously share your money among other active members in the server's economy",aliases=["donate"])
    async def share(self,ctx,amount):
        if not await self.onCooldown(ctx.author.id,ctx.guild.id,["sendPay"]):
            try:
                amount = abs(int(amount))
            except ValueError:
                await ctx.send(f"Invalid amount '{amount}', {ctx.author.mention}")
            else:
                await self.mysql.execute("SELECT cash FROM members WHERE user_id = %s and server_id = %s",(ctx.author.id,ctx.guild.id))
                if (await self.mysql.fetchone())["cash"] >= amount:
                    await self.mysql.execute("SELECT * FROM members WHERE server_id = %s AND inactiveTime > now() AND user_id <> %s",(ctx.guild.id,ctx.author.id))
                    amount = floor(amount/len(await self.mysql.fetchall()))
                    await self.mysql.execute("UPDATE members SET cash = cash-%s WHERE user_id = %s and server_id = %s",(amount,ctx.author.id,ctx.guild.id))
                    await self.mysql.execute("UPDATE members SET cash = cash+%s WHERE server_id = %s AND inactiveTime > now() AND user_id <> %s",(amount,ctx.guild.id,ctx.author.id))
                    await ctx.message.add_reaction("👍")
                    await self.addCooldown(ctx.author.id,ctx.guild.id,["sendPay"])
                else:
                    await ctx.send(f"You don't have {amount} in your cash balance available to donate, {ctx.author.mention}!")

    @commands.command(description="Lists all available items that can be bought using $buy",aliases=["shop"])
    async def store(self,ctx):
        if not await self.onCooldown(ctx.author.id,ctx.guild.id,["store"]):
            await ctx.send(embed=self.storeEmbed)
            await self.addCooldown(ctx,["store"])

    @commands.command(description="Buy an item listed in the $store")
    async def buy(self,ctx,item,renew="no"):
        if not await self.onCooldown(ctx.author.id,ctx.guild.id):
            originalItem,foundItem = item.lower().replace("_"," "),None
            for item in self.items:
                if item["name"] == originalItem:
                    foundItem = item
            if foundItem != None:
                await self.mysql.execute("SELECT * FROM inventories WHERE user_id = %s and server_id = %s and item_id = %s",(ctx.author.id,ctx.guild.id,foundItem["item_id"]))
                if len(await self.mysql.fetchall()) == 0:
                    await self.mysql.execute("SELECT cash FROM members WHERE user_id = %s and server_id = %s",(ctx.author.id,ctx.guild.id))
                    if (await self.mysql.fetchone())["cash"] >= foundItem["cost"]:
                        await self.mysql.execute("UPDATE members SET cash = cash-%s WHERE user_id = %s and server_id = %s",(foundItem["cost"],ctx.author.id,ctx.guild.id))
                        await self.mysql.execute("INSERT INTO `inventories` (`item_id`,`user_id`,`server_id`,`expiry`,`auto-renew`) VALUES (%s,%s,%s,%s,%s)",(foundItem["item_id"],ctx.author.id,ctx.guild.id,datetime.now()+timedelta(seconds=humanReadable(foundItem["duration"]).seconds),0 if renew == "no" else 1))
                        await ctx.message.add_reaction("👍")
                    else:
                        await ctx.send(f"You don't have {foundItem['cost']} in your cash balance available to spend on {item['name']}, {ctx.author.mention}!")
                else:
                    await ctx.send(f"You already own this item, {ctx.author.mention}!")
            else:
                await ctx.send(f"Cannot find an item by the name {originalItem} in the store, {ctx.author.mention}!")

    @commands.command(description="If you've discovered a reward code, use this command in the server it is valid in to redeem it!")
    async def redeem(self,ctx,code):
        await self.mysql.execute("SELECT * FROM rewardCodes WHERE code = %s",(code,))
        res = await self.mysql.fetchall()
        if res != ():
            if res[0]["server_id"] == ctx.guild.id:
                await self.mysql.execute("UPDATE members SET cash = cash + %s WHERE user_id = %s AND server_id = %s",(res[0]["reward"],ctx.author.id,ctx.guild.id))
                await self.mysql.execute("DELETE FROM rewardCodes WHERE code = %s",(code))
                await ctx.send(f"Congratulations, {ctx.author.mention}, for finding the reward code! {res[0]['reward']} has been added to your cash balance.")
            else:
                await ctx.send(f"This code is intended for a different server, {ctx.author.mention}!")
        else:
            await ctx.send(f"There is not a reward for this code, {ctx.author.mention}!")

    @commands.command(hidden=True)
    @commands.check(is_owner)
    async def generateCode(self,ctx,reward="360",code="random"):
        if code == "random":
            code = ''.join(choices(ascii_letters+digits,k=15))
            await ctx.author.send(f"The generated code for the ${reward} reward in `{ctx.guild.name}` is `{code}`")
        await self.mysql.execute("INSERT INTO `rewardCodes` (`server_id`,`code`,`reward`) VALUES (%s,%s,%s)",(ctx.guild.id,code,int(reward)))
        await ctx.message.add_reaction("👍")

    @commands.command(hidden=True)
    @commands.check(is_owner)
    async def resetEconomy(self,ctx):
        await self.mysql.execute("DELETE FROM inventories")
        await self.mysql.execute("DELETE FROM members")
        await ctx.send("Reset economy")

def setup(bot):
    bot.add_cog(Economy(bot))
