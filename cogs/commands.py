import math
import random
import string
from datetime import datetime, timedelta
from textwrap import dedent

import config 
import discord
from discord.ext import commands
import asyncio

class etc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
 
    @commands.command(name="clear")
    async def _messages_clear(self, ctx):
        def me(m):
            return m.author == self.bot.user

        await ctx.channel.purge(check=me)
        await ctx.message.add_reaction("👌")

    @commands.command(name="recent")
    async def _recent_cases(self, ctx):
        async with self.bot.pool.acquire() as conn:
            cases = await conn.fetch("SELECT * FROM infractions WHERE guild = $1",ctx.guild.id)

            case_list = ""
            for x in cases:
                case_list += f"**{x['real_id']}** | Serial: {x['id']} | {x['moderator']} | {x['target']} | {x['guild']} | {x['time_punished']} | {x['reason']}\n"           
            
            await ctx.send(case_list)

    @commands.command(name="reason")
    async def _update_reason(self,ctx,case,*,new_reason):
        if case.lower() in ['|','^','%','&','/','?','recent','r','~','-']:
            case = self.bot.cases[ctx.guild.id]

        async with self.bot.pool.acquire() as conn:
            fetch_case = await conn.fetchrow("SELECT * FROM infractions WHERE real_id = $1 AND guild = $2",int(case),ctx.guild.id)

            if not fetch_case:
                return await ctx.send(":wood: not a case.")
            
            try:
                await conn.execute("UPDATE infractions SET reason = $1 WHERE real_id = $2 AND guild = $3",new_reason,int(case),ctx.guild.id)
            except Exception as err:
                return await ctx.send(f"There was an error.\n```{err}```")

            await ctx.send(":ok_hand:")

    @commands.command(name="reset")
    async def _reset_cases(self,ctx):
        async with self.bot.pool.acquire() as conn:
            try:
                await conn.execute("DELETE FROM infractions WHERE guild = $1",ctx.guild.id)
                del self.bot.cases[ctx.guild.id]
            except Exception as err:
                return await ctx.send(f"There was an error.\n```{err}```")
            await ctx.send(":ok_hand:")

def setup(bot):
    bot.add_cog(etc(bot))
