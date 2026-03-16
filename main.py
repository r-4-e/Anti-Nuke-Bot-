import discord
import asyncio
import os
import json
from discord import app_commands
from colorama import Fore, init

# ================= COLORAMA SETUP =================
init(autoreset=True)
r = Fore.RED
g = Fore.GREEN
ora = Fore.YELLOW
p = Fore.MAGENTA
s = Fore.CYAN
wh = Fore.WHITE

# ===== LOAD TOKEN =====
TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN is None:
    raise ValueError("No DISCORD_TOKEN found.")

# ================= INTENTS =================
intents = discord.Intents.default()
intents.members = True
intents.guilds = True

bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

# ================= DATA =================
whitelist_file = "whitelist.json"

def load_whitelist():
    if os.path.exists(whitelist_file):
        with open(whitelist_file, "r") as f:
            return set(json.load(f))
    return set()

def save_whitelist():
    with open(whitelist_file, "w") as f:
        json.dump(list(whitelist), f)

whitelist = load_whitelist()
welcome_channels = {}
farewell_channels = {}
invite_cache = {}

# ================= BAN WITH RETRY =================
async def ban_with_retry(guild, target, reason, tries=3):
    for attempt in range(1, tries + 1):
        try:
            await guild.ban(target, reason=reason)
            print(f"[SUCCESS] Banned {target}")
            return
        except discord.Forbidden:
            print("[ERROR] Missing permission to ban.")
            return
        except Exception as e:
            print(f"[FAIL] Attempt {attempt}: {e}")
            await asyncio.sleep(1)

# ================= READY =================
@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.online)
    await tree.sync()

    for guild in bot.guilds:
        try:
            invite_cache[guild.id] = await guild.invites()
        except:
            invite_cache[guild.id] = []

    print(f"{g}Bot online as {bot.user}")

# ================= ERROR HANDLER =================
@tree.error
async def on_app_command_error(interaction, error):
    try:
        await interaction.response.send_message(
            f"❌ Error: {error}", ephemeral=True
        )
    except:
        pass

# ================= WHITELIST =================
@tree.command(name="whitelist")
@app_commands.checks.has_permissions(administrator=True)
async def whitelist_cmd(interaction: discord.Interaction, member: discord.Member):
    whitelist.add(member.id)
    save_whitelist()
    await interaction.response.send_message(f"✅ {member.mention} added", ephemeral=True)

@tree.command(name="unwhitelist")
@app_commands.checks.has_permissions(administrator=True)
async def unwhitelist_cmd(interaction: discord.Interaction, member: discord.Member):
    whitelist.discard(member.id)
    save_whitelist()
    await interaction.response.send_message(f"❌ {member.mention} removed", ephemeral=True)

@tree.command(name="whitelistlist")
async def whitelistlist_cmd(interaction: discord.Interaction):
    if not whitelist:
        await interaction.response.send_message("Empty.", ephemeral=True)
        return

    names = []
    for uid in whitelist:
        user = interaction.guild.get_member(uid)
        if user:
            names.append(user.mention)

    await interaction.response.send_message("\n".join(names), ephemeral=True)

# ================= CHANNEL SETUP =================
@tree.command(name="add_welcome")
async def add_welcome(interaction: discord.Interaction, channel: discord.TextChannel):
    welcome_channels[interaction.guild.id] = channel.id
    await interaction.response.send_message(f"Set to {channel.mention}", ephemeral=True)

@tree.command(name="add_byebye")
async def add_byebye(interaction: discord.Interaction, channel: discord.TextChannel):
    farewell_channels[interaction.guild.id] = channel.id
    await interaction.response.send_message(f"Set to {channel.mention}", ephemeral=True)

# ================= MEMBER JOIN =================
@bot.event
async def on_member_join(member):
    guild = member.guild

    # Anti-bot add (safer)
    if member.bot:
        await asyncio.sleep(1)
        async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.bot_add):
            if entry.target.id == member.id:
                adder = entry.user
                if adder.id not in whitelist:
                    print(f"[WARN] {adder} added bot {member}")
                break
        return

    inviter = "Unknown"

    try:
        new_invites = await guild.invites()
    except:
        new_invites = []

    old_invites = invite_cache.get(guild.id, [])

    for new in new_invites:
        for old in old_invites:
            if new.code == old.code and new.uses > old.uses:
                inviter = new.inviter.mention
                break

    invite_cache[guild.id] = new_invites

    if guild.id in welcome_channels:
        channel = guild.get_channel(welcome_channels[guild.id])
        if channel:
            await channel.send(
                f"{member.mention} invited by {inviter} | Members: {guild.member_count}"
            )

# ================= MEMBER LEAVE =================
@bot.event
async def on_member_remove(member):
    guild = member.guild

    if guild.id in farewell_channels:
        channel = guild.get_channel(farewell_channels[guild.id])
        if channel:
            await channel.send(
                f"{member.mention} left | Members: {guild.member_count}"
            )

# ================= RUN =================
bot.run(TOKEN)
