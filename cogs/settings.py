import math
import random
import string
from datetime import datetime, timedelta
from textwrap import dedent

import config 
import discord
from discord.ext import commands
import asyncio

class settigs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.group(name="logs",usage="<channel> (Leave channel none to disable)",description="Set your server's channel where audit log actions will be logged. aka modlogs",invoke_without_command=True)
    async def _logs(self, ctx, *, channel: discord.TextChannel = None):
        async with self.bot.pool.acquire() as conn:
            try:
                await conn.execute(
                    "UPDATE guild SET log_channel = $1 WHERE guild = $2",
                    None if channel is None else channel.id,
                    ctx.guild.id,
                )
            except Exception as err:
                return await ctx.send(f"There was an error.\n```{err}```")

            await ctx.send(
                f""":wood: Set your log channel to {channel.mention if channel is not None else "disabled"}."""
            )

    @_logs.command(name="hush",usage="<true / false>",description="Toggle whether your logs are active or disabled.")
    async def _logs_hush(self,ctx,option:bool=False):
        async with self.bot.pool.acquire() as conn:
            try:
                await conn.execute(
                    "UPDATE guild SET logs_hush = $1 WHERE guild = $2",
                    not option,
                    ctx.guild.id,
                )
            except Exception as err:
                return await ctx.send(f"There was an error.\n```{err}```")

            await ctx.send(
                f""":wood: Your logs were {"hushed" if option else "unhushed"}."""
            )

    @_logs.command(name="ping_user",usage="<true / false>",description="Toggle whether your logs should ping the user or not.")
    async def _logs_ping_user(self,ctx,option:bool=False):
        async with self.bot.pool.acquire() as conn:
            try:
                await conn.execute(
                    "UPDATE guild SET ping_user = $1 WHERE guild = $2",
                    option,
                    ctx.guild.id,
                )
            except Exception as err:
                return await ctx.send(f"There was an error.\n```{err}```")

            await ctx.send(
                f""":wood: Users will now {"be pinged" if option else "not be pinged"}."""
            )

    @commands.command(name="default_reason",usage="<default reason>",description="Set the reason for every action that doesn't have one.")
    async def _default_reason(self,ctx,*,reason):
        if len(reason) > 100:
            return await ctx.send(f":wood: default_reason's length may not be over **100** characters. Yours was **{len(reason)}** characters.")

        async with self.bot.pool.acquire() as conn:
            try:
                await conn.execute(
                    "UPDATE guild SET default_reason = $1 WHERE guild = $2",
                    reason,
                    ctx.guild.id,
                )
            except Exception as err:
                return await ctx.send(f"There was an error.\n```{err}```")

            await ctx.send(
                f":wood: Your default reason is now```{discord.utils.escape_markdown(text=reason)}```"
            )   


def setup(bot):
    bot.add_cog(settigs(bot))
