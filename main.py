import discord
import asyncio
import random
from discord import app_commands
from discord.ext import commands
from colorama import Fore, init
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")

# ================= COLORAMA SETUP =================
init(autoreset=True)
r   = Fore.RED
g   = Fore.GREEN
ora = Fore.YELLOW
p   = Fore.MAGENTA
s   = Fore.CYAN
wh  = Fore.WHITE

# ================= INTENTS & BOT =================
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ================= DATA STRUCTURES =================
whitelist = set()
welcome_channels = {}
farewell_channels = {}
invite_cache = {}

# ================= HERO SYSTEM DATA =================
HERO_OWNER = "rehanbrine."
hero_entries = {}       # { name: description }
hero_permitted = set()  # usernames allowed to use /heroadd and /heroaddperm

def is_hero_authorized(interaction: discord.Interaction) -> bool:
    return interaction.user.name == HERO_OWNER or interaction.user.name in hero_permitted

# ================= BAN WITH RETRY =================
async def ban_with_retry(guild, target, reason, tries=3):
    for attempt in range(1, tries + 1):
        try:
            await guild.ban(target, reason=reason)
            print(f"[SUCCESS] Banned {target} on attempt {attempt}")
            return
        except Exception as e:
            print(f"[FAIL] Attempt {attempt} failed for {target}: {e}")
            await asyncio.sleep(1)

# ================= READY EVENT =================
@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.online)
    await tree.sync()
    for guild in bot.guilds:
        try:
            invite_cache[guild.id] = await guild.invites()
        except Exception:
            invite_cache[guild.id] = []

    print(f"""
                                {r} █▓███   ▄▄▄      
                                {r}▓██  ██ ██▓▓████▄    
                                {r}▓██ ██▓  ██  ▀█▄  
                                {r}▒██▄█▓  ▒██▄▄▄▄██ 
                                {r}▒██   ▒  ▓█   ▓██▒
                                {r}▒▓▒   ▒  ▒▒   ▓▒█▒
                                {ora}▒▒ ▒       ▒   ▒▒ ▒
                                {ora}▒▒         ▒   ▒   
                                {ora}             ▒  ▒

{g}████████ ██   ██ ███████     ████████ ██████   ██████  ██    ██ ██████  ██      ███████ 
{g}   ██    ██   ██ ██             ██    ██   ██ ██    ██ ██    ██ ██   ██ ██      ██      
{g}   ██    ███████ █████          ██    ██████  ██    ██ ██    ██ ██████  ██      █████   
{g}   ██    ██   ██ ██             ██    ██   ██ ██    ██ ██    ██ ██   ██ ██      ██      
{g}   ██    ██   ██ ███████        ██    ██   ██  ██████   ██████  ██████  ███████ ███████ 
                                                                                        
{ora}{p} {s}- [{Fore.GREEN}+{s}] {wh}Logged in as {bot.user.name}
{ora}{p} {s}- [{Fore.GREEN}+{s}] {wh}Nuke command is {p}!getdiddyed
    """)

# ================= WHITELIST COMMANDS =================
@tree.command(name="whitelist", description="Add user to whitelist")
@app_commands.checks.has_permissions(administrator=True)
async def whitelist_cmd(interaction: discord.Interaction, member: discord.Member):
    whitelist.add(member.id)
    await interaction.response.send_message(f"✅ {member.mention} added to whitelist.", ephemeral=True)

@tree.command(name="unwhitelist", description="Remove user from whitelist")
@app_commands.checks.has_permissions(administrator=True)
async def unwhitelist_cmd(interaction: discord.Interaction, member: discord.Member):
    whitelist.discard(member.id)
    await interaction.response.send_message(f"❌ {member.mention} removed from whitelist.", ephemeral=True)

@tree.command(name="whitelistlist", description="Show whitelist")
@app_commands.checks.has_permissions(administrator=True)
async def whitelistlist_cmd(interaction: discord.Interaction):
    if not whitelist:
        await interaction.response.send_message("Whitelist is empty.", ephemeral=True)
        return
    names = []
    for uid in whitelist:
        user = interaction.guild.get_member(uid)
        if user:
            names.append(user.mention)
    await interaction.response.send_message("\n".join(names) if names else "No members found.", ephemeral=True)

# ================= WELCOME / FAREWELL CHANNELS =================
@tree.command(name="add_welcome", description="Set welcome channel")
@app_commands.checks.has_permissions(administrator=True)
async def add_welcome(interaction: discord.Interaction, channel: discord.TextChannel):
    welcome_channels[interaction.guild.id] = channel.id
    await interaction.response.send_message(f"Welcome messages set to {channel.mention}", ephemeral=True)

@tree.command(name="add_byebye", description="Set farewell channel")
@app_commands.checks.has_permissions(administrator=True)
async def add_byebye(interaction: discord.Interaction, channel: discord.TextChannel):
    farewell_channels[interaction.guild.id] = channel.id
    await interaction.response.send_message(f"Farewell messages set to {channel.mention}", ephemeral=True)

# ================= MASS DM =================
@tree.command(name="dm", description="Mass DM everyone or a specific role")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(message="Message to send", role="Optional: only DM members with this role")
async def mass_dm(interaction: discord.Interaction, message: str, role: discord.Role = None):
    guild = interaction.guild
    members = role.members if role else [m for m in guild.members if not m.bot]

    await interaction.response.send_message(
        f"📨 Starting mass DM to **{len(members)}** members. This may take a while...",
        ephemeral=True
    )

    success = 0
    failed = 0

    for member in members:
        try:
            await member.send(message)
            success += 1
            print(f"[DM] Sent to {member} ({success}/{len(members)})")
        except Exception as e:
            failed += 1
            print(f"[DM] Failed for {member}: {e}")

        await asyncio.sleep(random.randint(30, 60))

    try:
        await interaction.followup.send(
            f"✅ Done! Sent: **{success}** | Failed: **{failed}**",
            ephemeral=True
        )
    except Exception:
        pass

# ================= CREATE ROLE =================
@tree.command(name="createrole", description="Create a new role in the server")
@app_commands.checks.has_permissions(manage_roles=True)
@app_commands.describe(name="Name of the role to create")
async def create_role(interaction: discord.Interaction, name: str):
    try:
        role = await interaction.guild.create_role(name=name)
        await interaction.response.send_message(
            f"✅ Role {role.mention} created successfully!", ephemeral=True
        )
    except Exception as e:
        await interaction.response.send_message(f"❌ Failed to create role: {e}", ephemeral=True)

# ================= ADD ROLE =================
@tree.command(name="addrole", description="Add a role to a user")
@app_commands.checks.has_permissions(manage_roles=True)
@app_commands.describe(role="Role to assign", user="User to give the role to")
async def add_role(interaction: discord.Interaction, role: discord.Role, user: discord.Member):
    try:
        await user.add_roles(role)
        await interaction.response.send_message(
            f"✅ Added {role.mention} to {user.mention}!", ephemeral=True
        )
    except Exception as e:
        await interaction.response.send_message(f"❌ Failed to add role: {e}", ephemeral=True)

# ================= HERO SYSTEM =================

# /heroaddperm — rehanbrine. AND anyone they permitted can grant others access
@tree.command(name="heroaddperm", description="Grant a user permission to use /heroadd and /heroaddperm")
@app_commands.describe(member="User to grant permission to")
async def heroaddperm(interaction: discord.Interaction, member: discord.Member):
    if not is_hero_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    hero_permitted.add(member.name)
    await interaction.response.send_message(
        f"✅ **{member.name}** can now use /heroadd and /heroaddperm.", ephemeral=True
    )

# /heroadd — rehanbrine. and permitted users can add hero entries
@tree.command(name="heroadd", description="Add a hero entry with a name and description")
@app_commands.describe(name="The hero name", description="The hero description")
async def heroadd(interaction: discord.Interaction, name: str, description: str):
    if not is_hero_authorized(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    hero_entries[name.lower()] = description
    await interaction.response.send_message(
        f"✅ Hero **{name}** added successfully!", ephemeral=True
    )

# Autocomplete for /hero
async def hero_name_autocomplete(interaction: discord.Interaction, current: str):
    return [
        app_commands.Choice(name=name.title(), value=name)
        for name in hero_entries
        if current.lower() in name.lower()
    ][:25]

# /hero — anyone can look up a hero, result only visible to them
@tree.command(name="hero", description="Look up a hero's description")
@app_commands.describe(name="The hero name to look up")
@app_commands.autocomplete(name=hero_name_autocomplete)
async def hero(interaction: discord.Interaction, name: str):
    entry = hero_entries.get(name.lower())
    if not entry:
        await interaction.response.send_message(
            f"❌ No hero found with the name **{name}**.", ephemeral=True
        )
        return
    await interaction.response.send_message(
        f"📖 **{name.title()}**\n{entry}", ephemeral=True
    )

# ================= MEMBER JOIN =================
@bot.event
async def on_member_join(member):
    guild = member.guild

    # Bot anti-nuke
    if member.bot:
        await asyncio.sleep(1)
        async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.bot_add):
            if entry.target.id == member.id:
                adder = entry.user
                if adder.id not in whitelist:
                    await ban_with_retry(guild, adder, "Attempted nuke")
                    await ban_with_retry(guild, member, "Attempted nuke")
                break
        return

    # Invite tracking
    inviter = "Unknown"
    try:
        new_invites = await guild.invites()
        old_invites = invite_cache.get(guild.id, [])

        for new in new_invites:
            for old in old_invites:
                if new.code == old.code and new.uses > old.uses:
                    inviter = new.inviter.mention if new.inviter else "Unknown"
                    break

        invite_cache[guild.id] = new_invites
    except Exception:
        pass

    if guild.id in welcome_channels:
        channel = guild.get_channel(welcome_channels[guild.id])
        if channel:
            await channel.send(
                f"{member.mention} was invited by {inviter}, {guild.name} now has {guild.member_count} members!"
            )

# ================= MEMBER LEAVE =================
@bot.event
async def on_member_remove(member):
    guild = member.guild
    if guild.id in farewell_channels:
        channel = guild.get_channel(farewell_channels[guild.id])
        if channel:
            await channel.send(
                f"{member.mention} left the server. {guild.name} now has {guild.member_count} members."
            )

# ================= RUN =================
bot.run(TOKEN)
