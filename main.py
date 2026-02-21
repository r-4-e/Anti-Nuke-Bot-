import discord
import asyncio
import os
from flask import Flask
from threading import Thread
from discord.ext import commands

# ===== LOAD TOKEN FROM ENV =====
TOKEN = os.getenv("DISCORD_TOKEN")

if TOKEN is None:
    raise ValueError("No DISCORD_TOKEN found in environment variables.")

# ===== LOAD PORT FOR RENDER =====
PORT = int(os.environ.get("PORT", 10000))

# ===== WEB SERVER (REQUIRED FOR RENDER) =====
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running."

def run_web():
    app.run(host="0.0.0.0", port=PORT)

def keep_alive():
    thread = Thread(target=run_web)
    thread.start()
    
# ===== INTENTS =====
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ===== WHITELIST (USER IDS) =====
whitelist = set()

# ===== BAN WITH RETRY =====
async def ban_with_retry(guild, target, reason, tries=3):
    for attempt in range(1, tries + 1):
        try:
            await guild.ban(target, reason=reason)
            print(f"[SUCCESS] Banned {target} on attempt {attempt}")
            return
        except Exception as e:
            print(f"[FAIL] Attempt {attempt} failed for {target}: {e}")
            await asyncio.sleep(1)

# ===== READY =====
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    print("Anti-bot-add / anti-nuke system ACTIVE")

# ===== ADD TO WHITELIST =====
@bot.command()
@commands.has_permissions(administrator=True)
async def whitelist(ctx, member: discord.Member):
    whitelist.add(member.id)
    await ctx.send(f"✅ {member.mention} added to whitelist.")

# ===== REMOVE FROM WHITELIST =====
@bot.command()
@commands.has_permissions(administrator=True)
async def unwhitelist(ctx, member: discord.Member):
    whitelist.discard(member.id)
    await ctx.send(f"❌ {member.mention} removed from whitelist.")

# ===== SHOW WHITELIST =====
@bot.command()
@commands.has_permissions(administrator=True)
async def whitelistlist(ctx):
    if not whitelist:
        await ctx.send("📜 Whitelist is empty.")
        return

    names = []
    for uid in whitelist:
        user = ctx.guild.get_member(uid)
        if user:
            names.append(user.mention)

    await ctx.send("📜 **Whitelisted Users:**\n" + "\n".join(names))

# ===== BOT JOIN DETECTION =====
@bot.event
async def on_member_join(member):
    # Ignore humans
    if not member.bot:
        return

    guild = member.guild

    # Small delay to ensure audit log is ready
    await asyncio.sleep(1)

    async for entry in guild.audit_logs(
        limit=5,
        action=discord.AuditLogAction.bot_add
    ):
        if entry.target.id != member.id:
            continue

        adder = entry.user

        # If adder is NOT whitelisted → ban both
        if adder.id not in whitelist:
            print(f"[ALERT] Non-whitelisted user {adder} added bot {member}")

            await ban_with_retry(
                guild,
                adder,
                "Attempted nuke"
            )

            await ban_with_retry(
                guild,
                member,
                "Attempted nuke"
            )
        else:
            print(f"[OK] Bot {member} added by whitelisted user {adder}")

        break  # stop after matching entry

# ===== RUN =====
keep_alive()
bot.run(TOKEN)
            
