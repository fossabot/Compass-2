# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import datetime
import asyncpraw
import random
import aiohttp
import io
import discord
import sr_api
import cse
from utils import embeds, hurricane_generator
from discord.ext import commands


class APIs(commands.Cog, description='This cog just pulls from websites.'):
    def __init__(self, bot):
        self.bot = bot
        self.engine = cse.Search(self.bot.config['googleapikey'])
        self.client = sr_api.Client()
        self.reddit = asyncpraw.Reddit(client_id=self.bot.config['redditauth'][1], client_secret=self.bot.config['redditauth'][0],
                                       password=self.bot.config['password'], user_agent=self.bot.config['redditauth'][2],
                                       username="Sovietica")

    @commands.cooldown(1, 5)
    @commands.command()
    async def google(self, ctx, *, arg):
        results = await self.engine.search(f"{arg}")
        if results[0].snippet is not None:
            snippet = str(results[0].snippet)
        else:
            snippet = "No snippet available."
        embed = embeds.twoembed(results[0].title,
                                snippet)
        embed.add_field(name="URL", value=results[0].link, inline=True)
        embed.set_image(url=f"{results[0].image}")
        await ctx.send(embed=embed)

    @google.error
    async def google_error(self, ctx, error):
        if isinstance(error, KeyError):
            return await ctx.send(embed=embeds.failembed("No results!",
                                                         "Try searching something else."))

    @commands.command(help="Posts a cat.")
    async def cat(self, ctx):
        image = await self.client.get_image("cat")
        buffer = io.BytesIO(await image.read())
        file = discord.File(fp=buffer, filename="cat.png")
        embed = discord.Embed(color=0x202225, title="Your cat!")
        embed.set_image(url="attachment://cat.png")
        await ctx.send(embed=embed, file=file)

    @commands.command(help="Posts a dog.")
    async def dog(self, ctx):
        image = await self.client.get_image("dog")
        buffer = io.BytesIO(await image.read())
        file = discord.File(fp=buffer, filename="dog.png")
        embed = discord.Embed(color=0x202225, title="Your dog!")
        embed.set_image(url="attachment://dog.png")
        await ctx.send(embed=embed, file=file)

    @commands.command(help="Posts the status of Discord.")
    async def discordstatus(self, ctx):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://srhpyqt94yxb.statuspage.io/api/v2/incidents.json") as page:
                json = await page.json()
        incident = json['incidents'][0]
        embed = embeds.twoembed(incident['name'] + " | " + incident['impact'], incident['incident_updates'][0]['body'],
                                timestamp=False)
        embed.url = incident['shortlink']
        embed.add_field(name="Created At", value=incident['created_at'].replace("T", " "), inline=True)
        if 'monitoring_at' in incident:
            embed.add_field(name="Monitoring At", value=incident['monitoring_at'].replace("T", " "), inline=True)
        if 'resolved_at' in incident:
            embed.add_field(name="Resolved At", value=incident['resolved_at'].replace("T", " "), inline=True)
        embed.add_field(name="ID", value=incident['page_id'].replace("T", " "), inline=True)
        embed.timestamp = datetime.datetime.strptime(incident['updated_at'].replace("T", " "), '%Y-%m-%d %H:%M:%S.%f%z')
        await ctx.send(embed=embed)

    @commands.command(help='Posts the most recent NHC advisory in a basin. You are required to give a basin')
    async def advisory(self, ctx, *, basin: str):
        if basin in hurricane_generator.atlantic_list:
            number = 0
        elif basin in hurricane_generator.epac_list:
            number = 1
        elif basin in hurricane_generator.cpac_list:
            number = 2
        else:
            raise commands.BadArgument("This basin isn't in the list of basins.")
        params = {"rss_url": "https://www.nhc.noaa.gov/gtwo.xml"}
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.rss2json.com/v1/api.json", params=params) as website:
                api = await website.json()
        grabbed_basin = api["items"][number]
        embed = embeds.twoembed(grabbed_basin["title"], grabbed_basin["description"], timestamp=False)
        embed.set_thumbnail(url=api["feed"]["image"])
        embed.url = grabbed_basin["link"]
        embed.timestamp = datetime.datetime.strptime(grabbed_basin["pubDate"], '%Y-%m-%d %H:%M:%S')
        await ctx.send(embed=embed)

    @commands.command(help="Posts the stupidest things to come from Donald J. Trump")
    async def trump(self, ctx):
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.tronalddump.io/random/quote') as r:
                res = await r.json()
            embed = embeds.twoembed("Your Trump quote!",
                                    res['value'])
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/777248921205866546/797288910282948608/kUuht00m.png")
            await ctx.send(embed=embed)

    @commands.command(help="Posts the NASA image of the day.", aliases=['nasa'])
    async def space(self, ctx):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.nasa.gov/planetary/apod?api_key={self.bot.config['nasakey']}") as nasa_raw:
                nasa_json = await nasa_raw.json()
            embed = embeds.twoembed(nasa_json['title'],
                                    nasa_json['explanation'])
            if 'copyright' in nasa_json:
                embed.add_field(name="Copyright", value=nasa_json['copyright'], inline=True)
            embed.set_image(url=nasa_json['hdurl'])
            await ctx.send(embed=embed)

    @commands.command(help="Posts the current location of the ISS (International Space Station.)", aliases=['internationalspacestation'])
    async def iss(self, ctx):
        async with aiohttp.ClientSession() as session:
            async with session.get("http://api.open-notify.org/iss-now") as raw:
                iss_info = await raw.json()
        embed = embeds.twoembed("Location of the International Space Station!",
                                "Up, up and away.")
        embed.add_field(name="Longitude", value=iss_info['iss_position']['longitude'], inline=True)
        embed.add_field(name="Latitude", value=iss_info['iss_position']['latitude'], inline=True)
        await ctx.send(embed=embed)

    @commands.command(help="Responds with yes or no or maybe even maybe.")
    async def yesorno(self, ctx):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://yesno.wtf/api") as rawversion:
                yes_or_no_api = await rawversion.json()
        if yes_or_no_api['answer'] == "yes":
            emoji = self.bot.get_emoji(797916243281707008)
        elif yes_or_no_api['answer'] == "no":
            emoji = self.bot.get_emoji(797916257558331432)
        elif yes_or_no_api['answer'] == "maybe":
            emoji = self.bot.get_emoji(798298058495361025)
        embed = embeds.imgembed(f"{emoji} {str(yes_or_no_api['answer']).title()}.", yes_or_no_api['image'])
        await ctx.send(embed=embed)

    @commands.command(help="Posts a meme from r/dankmemes.")
    async def reddit(self, ctx):
        memes = []
        subreddit = await self.reddit.subreddit("dankmemes")
        async for submission in subreddit.hot(limit=20):
            memes.append(submission)
        meme = random.choice(memes)
        embed = embeds.twoembed(f"{meme.title}",
                                f"{meme.score} upvotes")
        embed.url = f"http://reddit.com/r/dankmemes/comments/{meme.id}"
        embed.set_image(url=meme.url)
        await ctx.send(embed=embed)

    @commands.command(help="Posts a random image from [inspirobot.](https://inspirobot.me/)")
    async def inspirobot(self, ctx):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://inspirobot.me/api?generate=true") as inspirobotraw:
                url = (str(await inspirobotraw.read()).split("'"))[1]
            embed = embeds.imgembed("An inspirational quote!", url, url)
            await ctx.send(embed=embed)

    @commands.command(help="Posts the definition and example for a search term on Urban Dictionary.")
    async def urban(self, ctx, *, term: str):
        headers = {"x-rapidapi-key": self.bot.config["urbankey"],
                   "x-rapidapi-host": "mashape-community-urban-dictionary.p.rapidapi.com"}
        async with ctx.channel.typing():
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get("https://mashape-community-urban-dictionary.p.rapidapi.com/define",
                                       params={"term": term}) as thing:
                    response = await thing.json()
        definition = response["list"][0]
        embed = embeds.twoembed(f"Definition for {term} on Urban Dictionary!",
                                definition["definition"].replace(r"\n", "\n").replace(r"\r", "\n"))
        embed.add_field(name="Example", value=definition["example"].replace(r"\n", "\n").replace(r"\r", "\n"), inline=True)
        embed.set_footer(text=f":thumbsup: {definition['thumbs_up']} | {definition['thumbs_down']} :thumbsdown:")
        await ctx.send(embed=embed)

    @commands.command(help="Posts weather information for a given location.")
    async def weather(self, ctx, *, city: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://api.openweathermap.org/data/2.5/weather?appid={self.bot.config['weatherapikey']}&q={city}") as r:
                x = await r.json()
        if x["cod"] != "404":
            embed = embeds.twoembed(f"{city}'s weather!",
                                    f"{str(x['weather'][0]['description'])}\n"
                                    f"Humidity: {x['main']['humidity']}\n"
                                    f"Temperature (Celsius): {str(round(x['main']['temp'] - 273.15))}\n"
                                    f"Temperature (Fahrenheit): {str(round((round(x['main']['temp'] - 273.15) * 9 / 5) + 32))}\n "
                                    f"Pressure: {x['main']['pressure']}\n")
            await ctx.send(embed=embed)
        else:
            raise commands.BadArgument(f"{city} doesn't exist!")

    @commands.command(help="Posts a random Taylor Swift quote.")
    async def taylor(self, ctx):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.taylor.rest") as taylorquoteraw:
                taylorquoteget = await taylorquoteraw.json()
            async with session.get(f"https://api.taylor.rest/image") as imageraw:
                imagegrab = await imageraw.json()
        embed = embeds.twoembed("Your Taylor Swift quote!",
                                taylorquoteget['quote'])
        embed.set_thumbnail(url=imagegrab['url'])
        await ctx.send(embed=embed)

    @commands.command(help="Posts a quote from Kanye West.")
    async def kanye(self, ctx):
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.kanye.rest') as r:
                res = await r.json()
            embed = embeds.twoembed("Your Kanye quote!",
                                    res['quote'])
            await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(APIs(bot))
