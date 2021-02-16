import datetime
import discord
import logging
import yaml
import os
import time
import asyncio
import inspect
from utils import embeds
from utils.useful_functions import prefix
from discord.ext import commands
from utils import useful_functions

logging.basicConfig(**{"format": f"[%(asctime)s %(name)s %(levelname)s] %(message)s", "level": logging.INFO})
logging.Formatter.converter = time.gmtime
os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True"
os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
os.environ["JISHAKU_HIDE"] = "True"


async def lavalink():
    lavalink_directory = f"{os.getcwd()}/lavalink"  # change this
    request = f"cd {lavalink_directory} & java -jar Lavalink.jar"
    await asyncio.create_subprocess_shell(request, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)

bot = commands.Bot(command_prefix=prefix, description="Compass is an all-in-one bot coded in discord.py.",
                   intents=discord.Intents.all())
bot.launch_time = datetime.datetime.utcnow()
bot.config = yaml.safe_load(open("config.yml"))
bot.owner_ids = bot.config["owners"]

# Cache
bot.message_num = 0
bot.command_num = 0
bot.message_senders = {}
bot.guild_senders = {}
bot.command_users = {}
bot.command_guilds = {}

# DON'T LOAD cogs.tasks - BROKEN
bot.cogs_tuple = ("cogs.antolib", "cogs.apis", "cogs.developer", "cogs.error_handling",
                  "cogs.fun", "cogs.images", "cogs.music", "cogs.utilities")

# Loads cogs
for cog in bot.cogs_tuple:
    bot.load_extension(cog)
    useful_functions.logger.info(f"Loaded cog {cog}")

bot.load_extension("jishaku")
useful_functions.logger.info(f"Loaded cog jishaku (outside of main folder)")


async def source(command):
    url = "https://github.com/Compass-Bot-Team/Compass"
    branch = "rewrite"
    if command == 'help':
        src = type(bot.help_command)
        module = src.__module__
        filename = inspect.getsourcefile(src)
    else:
        obj = bot.get_command(command.replace('.', ' '))
        src = obj.callback.__code__
        module = obj.callback.__module__
        filename = src.co_filename
    lines, firstlineno = inspect.getsourcelines(src)
    if not module.startswith('discord'):
        location = os.path.relpath(filename).replace('\\', '/')
    else:
        location = module.replace('.', '/') + '.py'
    return f'{url}/blob/{branch}/{location}#L{firstlineno}-L{firstlineno + len(lines) - 1}'


class Compass_Help(commands.HelpCommand):
    def get_command_signature(self, command):
        returned = command.qualified_name
        if command.aliases:
            for alias in command.aliases:
                returned += f"/{alias}"
        return returned

    async def send_command_help(self, command):
        channel = self.get_destination()
        async with channel.typing():
            title = self.get_command_signature(command)
            if command.signature:
                title += f" {command.signature}"
            embed = embeds.twoembed(f"``{title}``", command.help)
            embed.url = await source(command.qualified_name)
        await channel.send(embed=embed)

    async def send_group_help(self, group):
        channel = self.get_destination()
        async with channel.typing():
            title = self.get_command_signature(group)
            if group.signature:
                title += f" {group.signature}"
            embed = embeds.twoembed(f"``{title}``", group.short_doc)
            embed.url = await source(group.qualified_name)
            subcommand_count = 0
            subcommands = ""
            if group.commands:
                for subcommand in group.commands:
                    if subcommand_count == 0:
                        subcommands += f"``{subcommand}``"
                    else:
                        subcommands += f", ``{subcommand}``"
                    subcommand_count += 1
                embed.add_field(name="Subcommands", value=subcommands)
        await channel.send(embed=embed)

    async def send_cog_help(self, cog):
        channel = self.get_destination()
        embed = embeds.twoembed(f"``{cog.qualified_name}``", cog.description)
        await channel.send(embed=embed)

    async def send_bot_help(self, mapping):
        embed = discord.Embed(title="Compass Help!", color=0x202225, timestamp=datetime.datetime.utcnow())
        channel = self.get_destination()
        async with channel.typing():
            for cog, commands in mapping.items():
                command_amount = 0
                filtered = await self.filter_commands(commands, sort=True)
                command_signatures = [self.get_command_signature(c) for c in filtered]
                if command_signatures:
                    cog_name = getattr(cog, "qualified_name", "Other")
                    if cog_name != "Other":
                        _commands = ""
                        for command in command_signatures:
                            if command_amount == 0:
                                _commands += f"``{str(command)}``"
                            else:
                                _commands += f", ``{str(command)}``"
                            command_amount += 1
                        embed.add_field(name=cog_name,
                                        value=_commands,
                                        inline=False)
        await channel.send(embed=embed)


bot.help_command = Compass_Help(command_attrs={'help': "Posts this message."})
bot.run(bot.config["token"])
