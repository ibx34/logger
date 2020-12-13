import collections
import os
import random
import sys

import aiohttp
import aioredis
import asyncpg
import discord
from discord.ext import commands

import collections
import config


class Logger(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=self.get_pre,
            case_insensitive=True,
            reconnect=True,
            status=discord.Status.idle,
            intents=discord.Intents(
                messages=True,
                guilds=True,
                members=True,
                guild_messages=True,
                dm_messages=True,
                reactions=True,
                guild_reactions=True,
                dm_reactions=True,
                voice_states=True,
                presences=True,
            ),
        )
        self.config = config
        self.session = None
        self.pool = None
        self.redis = None
        self.used = 0
        self.cases = collections.defaultdict(lambda: 0)

    async def get_pre(self, bot, message):

        return commands.when_mentioned_or(*config.prefix)(bot, message)

    async def start(self):
        self.session = aiohttp.ClientSession(loop=self.loop)

        await super().start(config.token)

    async def on_ready(self):
        try:
            self.pool = await asyncpg.create_pool(**self.config.db, max_size=150)
            self.redis = await aioredis.create_redis_pool(
                "redis://localhost", loop=self.loop
            )
        except Exception as err:
            print(err)

        self.guild = self.get_guild(config.guild)
        self.log = self.guild.get_channel(config.channel)

        for i in await self.pool.fetch("SELECT * FROM infractions ORDER BY real_id ASC"):
            self.cases[i["guild"]] = i["real_id"]

        await self.change_presence(
            status=discord.Status.online
        )
        print("Bot started loading modules")

        for ext in config.extensions:
            try:
                self.load_extension(f"{ext}")
            except Exception as e:
                print(f"Failed to load {ext}, {e}")
                print(ext)

        print(f"Bot started. Guilds: {len(self.guilds)} Users: {len(self.users)}")

    async def on_message(self, message):

        if message.author.bot:
            return

        ctx = await self.get_context(message)

        if ctx.command:
            await self.process_commands(message, ctx)

    async def process_commands(self, message, ctx):

        if ctx.command is None:
            return

        self.used += 1
        await self.invoke(ctx)


if __name__ == "__main__":
    Logger().run()
