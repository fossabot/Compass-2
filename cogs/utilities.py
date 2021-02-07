# MIT License
#
# Copyright (c) 2021 Compass
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import discord
import objectfile
import datetime
import typing
import time
import inspect
import sys
import humanize
import psutil
import aiosqlite
import asyncio
import pkg_resources
import os
from bot import has_admin
from .server import blacklisted_or_not
from datetime import datetime
from discord.ext import commands

checkfail = objectfile.newfailembed("You aren't a bot admin!",
                                    "Try harder.")

support_channel_id = 803375502433189888

class Utilities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.process = psutil.Process()
        self.memory = self.process.memory_full_info()
        self.version = sys.version_info

    @commands.Cog.listener()
    async def on_command(self, ctx):
        self.bot.command_num += 1
        member_dictionary = self.bot.command_users
        if ctx.author.id in member_dictionary:
            member_dictionary[ctx.author.id] += 1
        else:
            member_dictionary[ctx.author.id] = 1
        guild_dictionary = self.bot.command_guilds
        if ctx.guild is not None:
            if f"{ctx.guild} ({ctx.guild.id})" not in guild_dictionary:
                guild_dictionary[f"{ctx.guild} ({ctx.guild.id})"] = 1
            else:
                guild_dictionary[f"{ctx.guild} ({ctx.guild.id})"] += 1

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.webhook_id is not None:
            return
        else:
            other_dictionary = self.bot.guild_senders
            if message.guild is not None:
                if f"{message.guild} ({message.guild.id})" not in other_dictionary:
                    other_dictionary[f"{message.guild} ({message.guild.id})"] = 1
                else:
                    other_dictionary[f"{message.guild} ({message.guild.id})"] += 1
            self.bot.total_messages += 1
            member_dictionary = self.bot.message_senders
            if message.author.id in member_dictionary:
                member_dictionary[message.author.id] += 1
            else:
                member_dictionary[message.author.id] = 1

    @has_admin()
    @commands.command(help="Adds a meme to the database of memes. Admin only command.")
    async def addmeme(self, ctx, *, link:str):
        try:
            async with aiosqlite.connect('compassdb.db') as db:
                await db.execute(f"""INSERT INTO Memes VALUES ("{link}", "{ctx.author.name}#{ctx.author.discriminator}");""")
                await db.commit()
        except aiosqlite.Error:
            async with aiosqlite.connect('compassdb.db') as db:
                await db.execute(f"""CREATE TABLE Memes (link, author)""")
                await db.execute(f"""INSERT INTO Memes VALUES ("{link}", "{ctx.author.name}#{ctx.author.discriminator}");""")
                await db.commit()
        await ctx.send(f"Success!")

    @has_admin()
    @commands.command(help="Adds a quote to the database of quotes. Admin only command.")
    async def addquote(self, ctx, *, quote:str):
        try:
            async with aiosqlite.connect('compassdb.db') as db:
                await db.execute(f"""INSERT INTO Quotes VALUES ("{quote}", "{ctx.author.name}#{ctx.author.discriminator}");""")
                await db.commit()
                await ctx.send(f"Success!")
        except aiosqlite.Error:
            async with aiosqlite.connect('compassdb.db') as db:
                await db.execute('''CREATE TABLE Quotes (quote, author)''')
                await asyncio.sleep(0.1)
                await db.execute(f"""INSERT INTO Quotes VALUES ("{quote}", "{ctx.author.name}#{ctx.author.discriminator}");""")
                await db.commit()
                await ctx.send(f"Success!")

    async def uptime(self):
        delta_uptime = datetime.utcnow() - self.bot.launch_time
        hours, remainder = divmod(int(delta_uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)
        uptime_total = []
        if days != 0:
            uptime_total.append(f"{days} days")
        if hours != 0:
            uptime_total.append(f"{hours} hours")
        if minutes != 0:
            uptime_total.append(f"{minutes} minutes")
        if seconds != 0:
            uptime_total.append(f"{seconds} seconds")
        return str(uptime_total).replace("[", "").replace("]", "").replace("'", "")

    async def typing_speed(self, ctx):
        start1 = time.perf_counter()
        async with ctx.channel.typing():
            end1 = time.perf_counter()
        return f"{round((end1 - start1) * 1000)}ms"

    async def db_speed(self):
        start2 = time.perf_counter()
        await aiosqlite.connect('compassdb.db')
        end2 = time.perf_counter()
        return f"{round((end2 - start2) * 1000)}ms"

    @commands.command(help="Pong.")
    async def ping(self, ctx):
        start = time.perf_counter()
        message = await ctx.send(embed=objectfile.twoembed("Pinging...",
                                                           "Sit tight!"))
        end = time.perf_counter()
        embed = discord.Embed(colour=0x202225, title="Pong!", description=str(round((end - start) * 1000)) + "ms")
        embed.add_field(name="Websocket", value=str(round(self.bot.latency * 1000)) + "ms", inline=True)
        embed.add_field(name="Typing", value=await self.typing_speed(ctx), inline=True)
        embed.add_field(name="Database (Aiosqlite)", value=await self.db_speed(), inline=True)
        await message.edit(embed=embed)

    @commands.command(help="Posts some cool analytics.", aliases=["stats", "analytics"])
    async def about(self, ctx):
        cogs_list = str(list(map(str, self.bot.cogs))).replace(']', '').replace('[', '').replace("'", '')
        embed = objectfile.twoembed(f"About",
                                    f"Owner: DTOG#0001 721029142602056328\n"
                                    f"Uptime: {await self.uptime()}\n")
        try:
            objectfile.add_field(embed, "Top Bot Users", f"{await objectfile.users(self.bot)}", True)
            objectfile.add_field(embed, "Top No-Lifers", f"{await objectfile.noliferusers(self.bot)}", True)
            objectfile.add_field(embed, "Top Guild Bot Users", f"{await objectfile.guilds(self.bot)}", False)
            objectfile.add_field(embed, "Top Guild No-Lifers", f"{await objectfile.noliferguilds(self.bot)}", False)
        except Exception:
            pass
        objectfile.add_field(embed, "Stats", f"Cogs: {len(self.bot.cogs):,} ({cogs_list})\n"
                                             f"Servers: {len(self.bot.guilds):,}\n"
                                             f"Members: {len(self.bot.users):,}\n"
                                             f"Total Sent Messages: {self.bot.total_messages:,}\n"
                                             f"Commands Used Since Restart: {self.bot.command_num:,}", False)
        embed.add_field(name="Operating Stats",
                             value=f"Memory Usage: {humanize.naturalsize(self.memory.rss)} physical, {humanize.naturalsize(self.memory.vms)} virtual, {humanize.naturalsize(self.memory.uss)} dedicated to the bot\nCPU Usage: {round(self.process.cpu_percent() / psutil.cpu_count())}%\nOperating System: {sys.platform}", inline=False)
        embed.set_footer(text=f"Made in discord.py {pkg_resources.get_distribution('discord.py').version} + "
                              f"Python {self.version.major}.{self.version.minor}.{self.version.micro}!")
        objectfile.add_field(embed, "Links",
                             f"Invite me [here!](https://discord.com/oauth2/authorize?client_id=769308147662979122&permissions=2147352567&scope=bot)\n"
                             f"Go to my GitHub [here!](https://github.com/Compass-Bot-Team/Compass)\n"
                             f"View my website + future dashboard [here!](https://compasswebsite.dev)\n"
                             f"Join the support server [here!](https://discord.gg/H5cBqhy4RD)", False)
        await ctx.send(embed=embed)

    @commands.command(aliases=['servermessages', 'server_messages', 'guild_messages'], help='Shows the daily messages in the current guild.')
    async def guildmessages(self, ctx):
        _dict = self.bot.guild_senders
        if f"{ctx.guild} ({ctx.guild.id})" not in _dict:
            _dict[f"{ctx.guild} ({ctx.guild.id})"] = 0
        guild = f"{ctx.guild} ({ctx.guild.id})"
        embed = objectfile.twoembed(f"Current standings for {ctx.guild}!",
                                    f"""{_dict[guild]:,} human messages\n""")
        embed.set_thumbnail(url=ctx.guild.icon_url)
        await ctx.send(embed=embed)

    @commands.command(help="Posts the message author's whitelist status.")
    async def amiwhitelisted(self, ctx):
        validusers = objectfile.valids
        whitelistedyes = objectfile.successembed("You're whitelisted!",
                                                 "Congrats.",
                                                 "Go nuts!")
        whitelistedno = objectfile.failembed("You're not whitelisted!",
                                             "You're a casual.",
                                             "Contact <@721029142602056328> for access to whitelist commands.")
        if ctx.message.author.id in validusers:
            await ctx.send(embed=whitelistedyes)
        else:
            await ctx.send(embed=whitelistedno)

    @commands.command(help="Posts a suggestion to public voting in the Compass server.")
    async def suggest(self, ctx, *, suggestion=None):
        if ctx.message.author.id in objectfile.blacklistedusers:
            await ctx.send(embed=objectfile.blacklisted)
        else:
            if suggestion is None:
                await ctx.send(embed=objectfile.failembed("You don't have a suggestion?",
                                                          "You need to suggest something!",
                                                          "Example: compass!suggest blablablah"))
            else:
                current_time = datetime.datetime.now()
                author = ctx.message.author
                author_avatar = ctx.message.author.avatar_url
                server = ctx.message.guild
                suggestion = suggestion
                channel = ctx.message.channel
                suggestion_chat = self.bot.get_channel(777248717400571934)
                await ctx.send(embed=objectfile.successembed("Suggestion processed!",
                                                             "We'll get back to you when your suggestion is in.",
                                                             f"{suggestion}"))

                embed = discord.Embed(color=0x202225, title="New suggestion!")
                embed.set_thumbnail(url=f"{author_avatar}")
                embed.add_field(name=f"Suggestion by {author}",
                                value=f"{suggestion}\n**Server:** {server}\n**Channel:** {channel}", inline=False)
                embed.set_footer(text=f"{current_time}")
                await suggestion_chat.send(embed=embed)

    @commands.command(help="Shows information about a specified user.")
    async def user(self, ctx, user: typing.Union[discord.Member, discord.User] = None):
        if user is None:
            user = ctx.message.author
        embed = discord.Embed(color=0x202225)
        if user.display_name == user.name:
            embed.title = f"{str(user)}"
        else:
            embed.title = f"{str(user)} ({str(user.display_name)})"
        embed.set_thumbnail(url=str(user.avatar_url))
        embed.add_field(name="ID", value=str(user.id), inline=False)
        embed.add_field(name="Status", value=f"{str(user.status).title()}", inline=False)
        embed.add_field(name="On Mobile", value=str(user.is_on_mobile()), inline=False)
        embed.add_field(name="Created At", value=str(user.created_at), inline=True)
        embed.add_field(name="Joined At", value=str(user.joined_at), inline=True)
        list_of_roles = []
        for role in user.roles:
            if role.name == "@everyone":
                list_of_roles.append(f"{role.name}")
            else:
                list_of_roles.append(f"<@&{role.id}>")
        embed.add_field(name=f"Roles ({len(user.roles)})", value=str(list_of_roles).replace("[", "").replace("]", "").replace("'", ""), inline=False)
        await ctx.send(embed=embed)

    @commands.command(help="Shows information about the current server.")
    async def server(self, ctx):
        server = ctx.message.guild
        embed = discord.Embed(color=0x202225,
                              title=str(server))
        embed.set_thumbnail(url=str(server.icon_url))
        embed.add_field(name="ID", value=str(server.id), inline=True)
        embed.add_field(name="Owner", value=str(server.owner), inline=True)
        embed.add_field(name="Created At", value=str(server.created_at), inline=True)
        embed.add_field(name="Members", value="{:,}".format(len(server.members)), inline=True)
        embed.add_field(name="Bots", value="{:,}".format(sum(m.bot for m in server.members)), inline=True)
        embed.add_field(name="Humans", value="{:,}".format(sum(not m.bot for m in server.members)), inline=True)
        embed.add_field(name="Role Count", value="{:,}".format(len(server.roles)), inline=True)
        if server.premium_subscription_count > 0:
            embed.add_field(name="Boosts", value=f"Level {str(server.premium_tier)} "
                                                 f"({str(server.premium_subscription_count)} boosts)", inline=True)
        if server.description is not None:
            embed.add_field(name="Description", value=str(server.description), inline=False)
        embed.set_image(url=str(server.banner_url))
        await ctx.send(embed=embed)

    @commands.command(help="Posts a user's or your avatar.")
    async def avatar(self, ctx, user: discord.User = None):
        if user is None:
            user = ctx.message.author
        embed = objectfile.twoembed(f"{user}'s avatar!",
                                    f"[URL]({user.avatar_url})")
        embed.set_image(url=f"{user.avatar_url}")
        await ctx.send(embed=embed)

    @commands.group(help="The Compass bot's poll command. You can use poll classic or poll number 1-10.")
    async def poll(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(embed=objectfile.twoembed("The two sub commands for poll are;",
                                                     f"{ctx.prefix}poll classic or {ctx.prefix}poll number [1-10]!"))

    @poll.command(help="The original poll command.")
    async def classic(self, ctx, *, question=None):
        if question is None:
            question = "N/A"
        embed = objectfile.mainembed(f"Question asked by {ctx.message.author}!", f"{question}",
                                     "<:green_square:779529584201695272> = Yes\n<:yellow_square:779529584201695272> = "
                                     "Neutral\n<:red_square:779529584201695272> = "
                                     "No\n<:purple_square:779530441450848277> = "
                                     "Other\n<:grey_question:779529584201695272> = Maybe")
        embed.set_thumbnail(url=f"{ctx.message.author.avatar_url}")
        msg = await ctx.send(embed=embed)
        await objectfile.poll_classic(msg)

    @poll.command(help="A number poll. You can specify a number from 1-10 but it is not required.", name="number")
    async def number(self, ctx, num: int = None):
        await objectfile.number_poll(ctx.message, num)

    async def timer(self, second):
        if second == 0:
            embed = objectfile.twoembed(f"Timer over.",
                                        f"oh shit")
        else:
            embed = objectfile.twoembed(f"{time}.",
                                        f"oh shit")
        await asyncio.sleep(1)
        return embed

    @commands.command(help="A timer where you specify the time in seconds. [BROKEN]")
    async def timer(self, ctx, time: int):
        second = time
        message = await ctx.send(embed=await self.timer(second))
        for _ in range(time):
            second -= 1
        if second % 10 == 0:
            await message.edit(embed=await self.timer(second))

    @commands.command(help="Shows the GitHub URL of a command.")
    async def source(self, ctx, *, command:str=None):
        # This command was mostly ripped from R-Danny (but not all of it.)
        # This is allowed under mozilla license.
        url = "https://github.com/Compass-Bot-Team/Compass"
        branch = "main"
        if command is None:
            return await ctx.send(embed=objectfile.twoembed("My source!",
                                                            url))
        else:
            if command == 'help':
                src = type(self.bot.help_command)
                module = src.__module__
                filename = inspect.getsourcefile(src)
            else:
                obj = self.bot.get_command(command.replace('.', ' '))
                if obj is None:
                    return await ctx.send(embed=objectfile.twoembed("My source!",
                                                                    url))
                src = obj.callback.__code__
                module = obj.callback.__module__
                filename = src.co_filename
        lines, firstlineno = inspect.getsourcelines(src)
        if not module.startswith('discord'):
            location = os.path.relpath(filename).replace('\\', '/')
        else:
            location = module.replace('.', '/') + '.py'
        await ctx.send(embed=objectfile.twoembed(f"Source for {command}!",
                                                 f'{url}/blob/{branch}/{location}#L{firstlineno}-L{firstlineno + len(lines) - 1}'))

    @blacklisted_or_not()
    @commands.command(help="Sends a support question to the bot support team.")
    async def support(self, ctx, *, question:str):
        try:
            support_channel = self.bot.get_channel(support_channel_id)
            embed = objectfile.twoembed(f"Question from {ctx.author}!",
                                        question)
            embed.add_field(name="Channel ID", value=ctx.channel.id, inline=True)
            embed.add_field(name="Author ID", value=ctx.author.id, inline=True)
            await support_channel.send(embed=embed)
            await ctx.send(embed=objectfile.twoembed("Sent to the support team!",
                                                     "Join the support server at [this link.](https://discord.gg/SymdusT)"))
        except commands.CheckFailure:
            await ctx.send(embed=objectfile.newfailembed("You're blacklisted!",
                                                         "Behave."))

    @has_admin()
    @commands.command(help="Replies to a support query. Owner only command.")
    async def reply(self, ctx, channel:int, author:int, *, response:str):
        try:
            channel_redux = self.bot.get_channel(channel)
            await ctx.send("Success!")
            await channel_redux.send(f"<@{author}>", embed=objectfile.twoembed(f"Response from {ctx.author}!",response))
        except commands.CheckFailure:
            await ctx.send(embed=checkfail)

    @commands.group(invoke_without_command=True, help="Shows information about an invite.")
    async def invite(self, ctx, invite: discord.Invite):
        embed = discord.Embed(colour=0x202225, title=f"Information for {invite}!", description=f"Invite created by {invite.inviter}")
        embed.set_footer(text=f"Invite created at {invite.created_at}")
        embed.add_field(name="Invite Uses", value=invite.uses, inline=True)
        embed.add_field(name="Temporary Membership", value=invite.temporary, inline=True)
        embed.add_field(name="Revoked", value=invite.revoked, inline=True)
        embed.add_field(name="Invite Channel", value=f"<#{invite.channel.id}>", inline=True)
        embed.add_field(name="Invite Server", value=invite.guild.name, inline=True)
        if invite.max_age is not None:
            embed.add_field(name="Max Age in seconds", value=invite.max_age, inline=True)
        await ctx.send(embed=embed)

    @commands.command(help="Shows information about a specified bot.")
    async def bot(self, ctx, bot: typing.Union[discord.Member, discord.User]):
        if bot.bot:
            embed = objectfile.twoembed(f"Information about {bot}!",
                                        f"You can invite {bot} by [clicking here.](https://discord.com/api/oauth2/authorize?client_id={bot.id}&permissions=8&scope=bot)")
            embed.set_thumbnail(url=bot.avatar_url)
            embed.add_field(name="Bot Permissions", value=f"[{bot.guild_permissions.value}](https://discordapi.com/permissions.html#{bot.guild_permissions.value})", inline=True)
            async with aiosqlite.connect('compassdb.db') as db:
                server = await db.execute(f"""SELECT server FROM SupportServers WHERE bot = "{bot.id}";""")
                grabbed_server = str(await server.fetchone()).replace("('", "").replace(")", "").replace("%27,", "").replace("',", "")
                embed.add_field(name="Support Server", value=grabbed_server.replace("None", "None (request a support server by joining [here.](https://discord.gg/SymdusT))"), inline=True)
            await ctx.send(embed=embed)
        else:
            await ctx.send(embed=objectfile.newfailembed("This user is not a bot!",
                                                         "Try again later."))

    @has_admin()
    @commands.command(help="Adds a server to the bot server database. "
                           "Owner only command.", aliases=['add_bot_server'])
    async def addbotserver(self, ctx, server: str, bot: typing.Union[discord.User, discord.Member]):
        if bot.bot:
            async with aiosqlite.connect('compassdb.db') as db:
                await db.execute(f"""INSERT INTO SupportServers VALUES ("{server}", "{bot.id}");""")
                await db.commit()
            await ctx.send(f"Success!")
        else:
            await ctx.send("This is not a bot.")

    @commands.command(help="Shows information about a specified role.")
    async def role(self, ctx, *, role: discord.Role):
        query = f"""http://www.colourlovers.com/img/{hex(role.colour.value).replace("0x", "")}/100/100/"""
        embed = discord.Embed(colour=0x202225, title=f"Information about {role.name} (ID {role.id}!)")
        embed.set_thumbnail(url=query.replace("/img/0/100/100/", "/img/8B99A4/100/100/"))
        embed.add_field(name="Permissions", value=f"[{role.permissions.value}](https://discordapi.com/permissions.html#{role.permissions.value})", inline=True)
        embed.add_field(name="Hoisted", value=role.hoist, inline=True)
        embed.add_field(name="Position", value=f"{role.position}/{len(ctx.guild.roles)}", inline=True)
        embed.add_field(name="Mentionable", value=role.mentionable, inline=True)
        embed.add_field(name="Managed by 3rd party", value=role.managed, inline=True)
        embed.add_field(name="Is Managed", value=role.is_bot_managed(), inline=True)
        embed.add_field(name="Is the Boost Role", value=role.is_premium_subscriber(), inline=True)
        embed.add_field(name="Is an Integration", value=role.is_integration(), inline=True)
        embed.set_footer(text=f"Role created at {role.created_at}.")
        member_count = 0
        members = ""
        for member in role.members:
            if member_count == 0:
                members += f"<@{member.id}>"
            else:
                members += f", <@{member.id}>"
            member_count += 1
        try:
            embed.add_field(name=f"Role Members ({len(role.members)})", value=members, inline=False)
        except discord.errors.HTTPException:
            embed.add_field(name=f"Role Members ({len(role.members)})", value="There was too much to put here.", inline=False)
        await ctx.send(embed=embed)

    @role.error
    async def role_error(self, ctx, error):
        return await ctx.send("This role doesn't exist!")

def setup(bot):
    bot.add_cog(Utilities(bot))
