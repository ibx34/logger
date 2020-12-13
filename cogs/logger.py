import math
import random
import string
from datetime import datetime, timedelta
from textwrap import dedent

import config 
import discord
from discord.ext import commands
import asyncio

actinos_to_search = [
    discord.AuditLogAction.ban,
    discord.AuditLogAction.unban,
    discord.AuditLogAction.kick,
    discord.AuditLogAction.member_role_update,
]
class action_loggers():
    
    @staticmethod
    async def role_update_log(entry,case):
        
        true_or_false = False
        if entry.before.roles:
            if entry.before.roles[0].id in config.roles_to_watch:
                true_or_false = True
            else:
                return
        elif entry.after.roles:
            if entry.after.roles[0].id in config.roles_to_watch:
                true_or_false = False
            else:
                return
        
        if true_or_false:
            return f"""**Sepcial Role Removed** | Case {case}\n**User**: {entry.target} ({entry.target.id})\n**Role**: {''.join([f"{x.name} ({x.id})" for x in entry.before.roles])}\n**Reason**: {entry.reason}\n**Responsible moderator**: {entry.user}"""
        return f"""**Sepcial Role Added** | Case {case}\n**User**: {entry.target} ({entry.target.id})\n**Role**: {''.join([f"{x.name} ({x.id})" for x in entry.after.roles])}\n**Reason**: {entry.reason}\n**Responsible moderator**: {entry.user}"""    
    
    @staticmethod
    async def kick_log(entry,case):

        return f"""**Kick** | Case {case}\n**User**: {entry.target} ({entry.target.id})\n**Reason**: {entry.reason}\n**Responsible moderator**: {entry.user}"""

    @staticmethod
    async def ban_log(entry,case):

        return f"""**Ban** | Case {case}\n**User**: {entry.target} ({entry.target.id})\n**Reason**: {entry.reason}\n**Responsible moderator**: {entry.user}"""

    @staticmethod
    async def unban_log(entry,case):

        return f"""**Unban** | Case {case}\n**User**: {entry.target} ({entry.target.id})\n**Reason**: {entry.reason}\n**Responsible moderator**: {entry.user}"""

class _logger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_audit_log_id = None
        self.audit_check_task = self.bot.loop.create_task(self.audit_check())
        self.task_check = self.bot.loop.create_task(self.task_check_task())

    async def new_case(self,entry):
        async with self.bot.pool.acquire() as conn:
            try:
                self.bot.cases[entry.user.guild.id] += 1
                update = await conn.fetchrow(
                    "INSERT INTO infractions(target,moderator,reason,real_id,time_punished,guild) VALUES($1,$2,$3,$4,$5,$6) RETURNING *",
                    entry.target.id,
                    entry.user.id,
                    entry.reason,
                    self.bot.cases[entry.user.guild.id],
                    entry.created_at,
                    entry.user.guild.id
                )
            except Exception as err:
                print(err)
        
        return update


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

    def cog_unload(self):
        try:
            self.audit_check_task.cancel()
        except:
            pass

    async def task_check_task(self):
        if self.audit_check_task.done():
            self.audit_check_task.cancel()
            self.audit_check_task = self.bot.loop.create_task(self.audit_check())

    async def audit_check(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            latest_entry = await self.bot.guild.audit_logs(limit=1).flatten()
            self.last_audit_log_id = latest_entry[0].id

            await asyncio.sleep(1)

            try:
                entries = await self.bot.guild.audit_logs(limit=1).flatten()
                if entries[0].id == self.last_audit_log_id:
                    pass
                else:
                    if entries[0].action not in actinos_to_search:
                        pass
                    else:
                        
                        case_id = await self.new_case(entry=entries[0])

                        if entries[0].action == discord.AuditLogAction.member_role_update:
                            try:
                                embed = await action_loggers.role_update_log(entry=entries[0],case=case_id['real_id'])
                                await self.bot.log.send(embed)
                            except Exception as err:
                                print(err)
                        elif entries[0].action == discord.AuditLogAction.kick:
                            try:
                                embed = await action_loggers.kick_log(entry=entries[0],case=case_id['real_id'])
                                await self.bot.log.send(embed)        
                            except Exception as err:
                                print(err)
                        elif entries[0].action == discord.AuditLogAction.ban:
                            try:
                                embed = await action_loggers.ban_log(entry=entries[0],case=case_id['real_id'])
                                await self.bot.log.send(embed) 
                            except Exception as err:
                                print(err)
                        elif entries[0].action == discord.AuditLogAction.unban:
                            try:
                                embed = await action_loggers.unban_log(entry=entries[0],case=case_id['real_id'])
                                await self.bot.log.send(embed) 
                            except Exception as err:
                                print(err)

                        self.last_audit_log_id = entries[0].id

            except Exception as err:
                print(err)


def setup(bot):
    bot.add_cog(_logger(bot))
