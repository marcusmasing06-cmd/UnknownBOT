import discord
from discord.ext import commands
import json
import os
import time
import random
import asyncio
from PIL import Image, ImageDraw, ImageFont

# ============================
# INTENTS
# ============================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True

# ============================
# BOT OBJECT
# ============================

bot = commands.Bot(command_prefix="!", intents=intents)

# ============================
# DATA SETUP
# ============================

if not os.path.exists("rankdata.json"):
    with open("rankdata.json", "w") as f:
        json.dump({}, f)


def load_data():
    with open("rankdata.json", "r") as f:
        return json.load(f)


def save_data(data):
    with open("rankdata.json", "w") as f:
        json.dump(data, f, indent=4)


def get_level_xp(level):
    return 1000 * level


# ============================
# READY EVENT
# ============================

@bot.event
async def on_ready():
    print("UnknownBOT is online")


# ============================
# XP + TOKEN SYSTEM
# ============================

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    data = load_data()
    user_id = str(message.author.id)
    current_hour = int(time.time() // 3600)

    if user_id not in data:
        data[user_id] = {
            "xp": 0,
            "level": 1,
            "xp_this_hour": 0,
            "last_xp_hour": current_hour,
            "tokens": 0
        }

    user = data[user_id]

    if "xp_this_hour" not in user:
        user["xp_this_hour"] = 0
    if "last_xp_hour" not in user:
        user["last_xp_hour"] = current_hour
    if "tokens" not in user:
        user["tokens"] = 0

    if user["last_xp_hour"] != current_hour:
        user["xp_this_hour"] = 0
        user["last_xp_hour"] = current_hour

    if user["xp_this_hour"] < 1520:
        user["xp"] += 5
        user["xp_this_hour"] += 5

        xp = user["xp"]
        level = user["level"]
        needed = get_level_xp(level)

        if xp >= needed:
            user["level"] += 1
            user["xp"] = xp - needed
            await message.channel.send(
                f"🎉 {message.author.mention} leveled up to **Level {level + 1}**!"
            )

    if random.random() <= 0.02:
        drop = random.randint(1, 3)
        user["tokens"] += drop
        await message.channel.send(
            f"💰 {message.author.mention} found **{drop} UnknownTokens**!"
        )

    save_data(data)
    await bot.process_commands(message)


# ============================
# RANK CARD GENERATOR
# ============================

def generate_rank_card(user, level, xp, needed_xp, tokens, avatar_path):
    width, height = 934, 282
    card = Image.new("RGB", (width, height), (20, 20, 20))
    draw = ImageDraw.Draw(card)

    for i in range(height):
        shade = 20 + int(i * 0.3)
        draw.line([(0, i), (width, i)], fill=(shade, shade, shade))

    avatar = Image.open(avatar_path).convert("RGBA").resize((180, 180))
    mask = Image.new("L", (180, 180), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, 180, 180), fill=255)
    card.paste(avatar, (40, 50), mask)

    try:
        font_title = ImageFont.truetype("Orbitron-Bold.ttf", 40)
        font_stats = ImageFont.truetype("arial.ttf", 30)
    except:
        font_title = ImageFont.truetype("arial.ttf", 40)
        font_stats = ImageFont.truetype("arial.ttf", 30)

    draw.text((250, 40), f"{user.name}", font=font_title, fill=(255, 255, 255))
    draw.text((250, 100), f"Level: {level}", font=font_stats, fill=(200, 200, 200))
    draw.text((250, 140), f"Tokens: {tokens}", font=font_stats, fill=(200, 200, 200))

    bar_x, bar_y = 250, 180
    bar_width, bar_height = 600, 20
    draw.rectangle((bar_x, bar_y, bar_x + bar_width, bar_y + bar_height), fill=(50, 50, 50))

    fill = int((xp / needed_xp) * bar_width) if needed_xp > 0 else 0
    draw.rectangle((bar_x, bar_y, bar_x + fill, bar_y + bar_height), fill=(180, 180, 180))

    draw.text((250, 210), f"{xp} / {needed_xp} XP", font=font_stats, fill=(220, 220, 220))

    card.save("rankcard.png")


# ============================
# LEADERBOARD CARD GENERATOR
# ============================

def generate_leaderboard_card(entries):
    width, height = 934, 600
    card = Image.new("RGB", (width, height), (20, 20, 20))
    draw = ImageDraw.Draw(card)

    for i in range(height):
        shade = 20 + int(i * 0.3)
        draw.line([(0, i), (width, i)], fill=(shade, shade, shade))

    try:
        font_title = ImageFont.truetype("Orbitron-Bold.ttf", 55)
        font_name = ImageFont.truetype("Orbitron-Bold.ttf", 32)
        font_stats = ImageFont.truetype("arial.ttf", 28)
    except:
        font_title = ImageFont.truetype("arial.ttf", 55)
        font_name = ImageFont.truetype("arial.ttf", 32)
        font_stats = ImageFont.truetype("arial.ttf", 28)

    title = "LEADERBOARD"
    bbox = draw.textbbox((0, 0), title, font=font_title)
    tw = bbox[2] - bbox[0]
    draw.text(((width - tw) // 2, 20), title, font=font_title, fill=(255, 60, 60))

    y = 120

    for rank, entry in enumerate(entries, start=1):
        avatar = Image.open(entry["avatar"]).convert("RGBA").resize((80, 80))
        mask = Image.new("L", (80, 80), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, 80, 80), fill=255)
        card.paste(avatar, (40, y), mask)

        draw.text((150, y + 5), f"#{rank}  {entry['name']}", font=font_name, fill=(255, 255, 255))
        draw.text(
            (150, y + 45),
            f"LVL {entry['level']} | {entry['xp']} XP | {entry['tokens']} UT",
            font=font_stats,
            fill=(200, 200, 200)
        )

        draw.rectangle((40, y + 95, width - 40, y + 100), fill=(255, 60, 60))
        y += 110

    card.save("leaderboard.png")


# ============================
# RANK COMMAND
# ============================

@bot.command()
async def rank(ctx, member: discord.Member = None):
    member = member or ctx.author

    data = load_data()
    user_id = str(member.id)

    if user_id not in data:
        data[user_id] = {
            "xp": 0,
            "level": 1,
            "xp_this_hour": 0,
            "last_xp_hour": 0,
            "tokens": 0
        }
        save_data(data)

    xp = data[user_id]["xp"]
    level = data[user_id]["level"]
    tokens = data[user_id]["tokens"]
    needed = get_level_xp(level)

    avatar_bytes = await member.avatar.read()
    with open("avatar.png", "wb") as f:
        f.write(avatar_bytes)

    generate_rank_card(member, level, xp, needed, tokens, "avatar.png")

    await ctx.send(file=discord.File("rankcard.png"))


# ============================
# BALANCE COMMANDS
# ============================

@bot.command()
async def balance(ctx, member: discord.Member = None):
    member = member or ctx.author
    data = load_data()
    user_id = str(member.id)

    if user_id not in data:
        await ctx.send("User has no data.")
        return

    tokens = data[user_id]["tokens"]
    await ctx.send(f"💰 **{member.name}** has **{tokens} UnknownTokens**.")


@bot.command()
async def bal(ctx, member: discord.Member = None):
    await balance(ctx, member)


# ============================
# GIVE TOKENS (PLAYER)
# ============================

@bot.command()
async def givetokens(ctx, member: discord.Member, amount: int):
    if amount <= 0:
        await ctx.send("Amount must be positive.")
        return

    if member == ctx.author:
        await ctx.send("You cannot give tokens to yourself.")
        return

    data = load_data()
    sender = str(ctx.author.id)
    receiver = str(member.id)

    if sender not in data:
        await ctx.send("You have no data.")
        return

    if receiver not in data:
        data[receiver] = {
            "xp": 0,
            "level": 1,
            "xp_this_hour": 0,
            "last_xp_hour": 0,
            "tokens": 0
        }

    if data[sender]["tokens"] < amount:
        await ctx.send("You don't have enough tokens.")
        return

    data[sender]["tokens"] -= amount
    data[receiver]["tokens"] += amount
    save_data(data)

    await ctx.send(f"🤝 **{ctx.author.name}** gave **{amount} UnknownTokens** to **{member.name}**!")


# ============================
# GIVE TOKENS (ADMIN)
# ============================

@bot.command()
@commands.has_permissions(administrator=True)
async def admingivetokens(ctx, member: discord.Member, amount: int):
    if amount <= 0:
        await ctx.send("Amount must be positive.")
        return

    data = load_data()
    uid = str(member.id)

    if uid not in data:
        data[uid] = {
            "xp": 0,
            "level": 1,
            "xp_this_hour": 0,
            "last_xp_hour": 0,
            "tokens": 0
        }

    data[uid]["tokens"] += amount
    save_data(data)

    await ctx.send(f"🛠️ Admin gave **{amount} UnknownTokens** to **{member.name}**.")


# ============================
# MINIGAME: DICE
# ============================

@bot.command()
async def dice(ctx, amount: int):
    data = load_data()
    user_id = str(ctx.author.id)

    if amount <= 0:
        await ctx.send("Bet must be positive.")
        return

    if user_id not in data or data[user_id]["tokens"] < amount:
        await ctx.send("Not enough tokens.")
        return

    user_roll = random.randint(1, 6) + random.randint(1, 6)
    bot_roll = random.randint(1, 6) + random.randint(1, 6)

    if user_roll > bot_roll:
        data[user_id]["tokens"] += amount
        result = f"🎲 You win! {user_roll} vs {bot_roll}"
    elif user_roll < bot_roll:
        data[user_id]["tokens"] -= amount
        result = f"🎲 You lose! {user_roll} vs {bot_roll}"
    else:
        result = f"🎲 It's a tie! {user_roll} vs {bot_roll}"

    save_data(data)
    await ctx.send(result)


# ============================
# MINIGAME: MINES
# ============================

@bot.command()
async def mines(ctx, amount: int, tile: int):
    if tile < 1 or tile > 5:
        await ctx.send("Pick a tile between 1 and 5.")
        return

    data = load_data()
    user_id = str(ctx.author.id)

    if user_id not in data or data[user_id]["tokens"] < amount:
        await ctx.send("Not enough tokens.")
        return

    mine = random.randint(1, 5)

    if tile == mine:
        data[user_id]["tokens"] -= amount
        save_data(data)
        await ctx.send(f"💥 BOOM! Tile {tile} was the mine. You lost {amount}.")
    else:
        winnings = int(amount * 1.5)
        data[user_id]["tokens"] += winnings
        save_data(data)
        await ctx.send(f"✨ Safe! You won {winnings} UnknownTokens.")


# ============================
# MINIGAME: COINFLIP (55% BOT WIN)
# ============================

@bot.command()
async def coinflip(ctx, choice: str, amount: int):
    choice = choice.lower()
    if choice not in ["heads", "tails"]:
        await ctx.send("Choose **heads** or **tails**.")
        return

    data = load_data()
    user_id = str(ctx.author.id)

    if user_id not in data or data[user_id]["tokens"] < amount:
        await ctx.send("Not enough tokens.")
        return

    bot_wins = random.random() < 0.55

    if bot_wins:
        data[user_id]["tokens"] -= amount
        save_data(data)
        await ctx.send(f"🪙 Bot wins! You lost {amount}.")
        return

    data[user_id]["tokens"] += amount
    save_data(data)
    await ctx.send(f"🪙 You win! You gained {amount} UnknownTokens.")


# ============================
# GIVEAWAY SYSTEM
# ============================

active_giveaways = {}


@bot.command(aliases=["giveaway"])
async def tokengiveaway(ctx, amount: int, winners: int, seconds: int):
    if amount <= 0:
        await ctx.send("Amount must be positive.")
        return

    if winners <= 0:
        await ctx.send("Winners must be at least 1.")
        return

    embed = discord.Embed(
        title="🎉 TOKEN GIVEAWAY 🎉",
        description=f"**Prize:** {amount} UnknownTokens EACH\n"
                    f"**Winners:** {winners}\n"
                    f"**Ends in:** {seconds} seconds\n\n"
                    f"React with 🎉 to enter!",
        color=0x00ff99
    )

    msg = await ctx.send(embed=embed)
    await msg.add_reaction("🎉")

    active_giveaways[msg.id] = {
        "amount": amount,
        "winners": winners,
        "host": ctx.author.id,
        "ended": False
    }

    for remaining in range(seconds, 0, -1):
        if active_giveaways[msg.id]["ended"]:
            return

        embed.description = (
            f"**Prize:** {amount} UnknownTokens EACH\n"
            f"**Winners:** {winners}\n"
            f"**Ends in:** {remaining} seconds\n\n"
            f"React with 🎉 to enter!"
        )
        await msg.edit(embed=embed)
        await asyncio.sleep(1)

    active_giveaways[msg.id]["ended"] = True

    msg = await ctx.channel.fetch_message(msg.id)

    reaction = None
    for r in msg.reactions:
        if str(r.emoji) == "🎉":
            reaction = r
            break

    if reaction is None:
        await ctx.send("No one reacted with 🎉.")
        return

    users = await reaction.users().flatten()
    users = [u for u in users if not u.bot]

    if len(users) == 0:
        await ctx.send("No one entered the giveaway.")
        return

    winners = min(winners, len(users))
    chosen = random.sample(users, winners)

    data = load_data()
    for user in chosen:
        uid = str(user.id)
        if uid not in data:
            data[uid] = {
                "xp": 0,
                "level": 1,
                "xp_this_hour": 0,
                "last_xp_hour": 0,
                "tokens": 0
            }
        data[uid]["tokens"] += amount

    save_data(data)

    winner_names = ", ".join([u.name for u in chosen])
    await ctx.send(f"🎉 **Winners:** {winner_names}\nEach received **{amount} UnknownTokens**!")


@bot.command()
async def cancelgiveaway(ctx, message_id: int):
    if message_id not in active_giveaways:
        await ctx.send("No active giveaway with that ID.")
        return

    g = active_giveaways[message_id]

    if ctx.author.id != g["host"]:
        await ctx.send("Only the giveaway host can cancel it.")
        return

    g["ended"] = True
    await ctx.send("❌ Giveaway cancelled.")


@bot.command()
async def reroll(ctx, message_id: int):
    if message_id not in active_giveaways:
        await ctx.send("No giveaway found with that ID.")
        return

    g = active_giveaways[message_id]

    if not g["ended"]:
        await ctx.send("Giveaway has not ended yet.")
        return

    msg = await ctx.channel.fetch_message(message_id)

    reaction = None
    for r in msg.reactions:
        if str(r.emoji) == "🎉":
            reaction = r
            break

    if reaction is None:
        await ctx.send("No one reacted with 🎉.")
        return

    users = await reaction.users().flatten()
    users = [u for u in users if not u.bot]

    if len(users) == 0:
        await ctx.send("No participants to reroll.")
        return

    winner = random.choice(users)

    data = load_data()
    uid = str(winner.id)
    if uid not in data:
        data[uid] = {
            "xp": 0,
            "level": 1,
            "xp_this_hour": 0,
            "last_xp_hour": 0,
            "tokens": 0
        }

    data[uid]["tokens"] += g["amount"]
    save_data(data)

    await ctx.send(f"🔄 Rerolled winner: **{winner.name}** received **{g['amount']} UnknownTokens**!")


# ============================
# LEADERBOARD COMMAND
# ============================

@bot.command()
async def leaderboard(ctx):
    data = load_data()

    lb = []
    for user_id, stats in data.items():
        member = ctx.guild.get_member(int(user_id))
        if member:
            avatar_bytes = await member.avatar.read()
            avatar_path = f"lb_avatar_{user_id}.png"
            with open(avatar_path, "wb") as f:
                f.write(avatar_bytes)

            lb.append({
                "name": member.name,
                "level": stats["level"],
                "xp": stats["xp"],
                "tokens": stats["tokens"],
                "avatar": avatar_path
            })

    lb.sort(key=lambda x: (x["level"], x["xp"], x["tokens"]), reverse=True)
    top10 = lb[:10]

    if not top10:
        await ctx.send("No leaderboard data yet.")
        return

    generate_leaderboard_card(top10)
    await ctx.send(file=discord.File("leaderboard.png"))


# ============================
# BASIC COMMANDS
# ============================

@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")


@bot.command()
async def hello(ctx):
    await ctx.send(f"Hello {ctx.author.name}!")


@bot.command()
async def say(ctx, *, message):
    await ctx.send(message)


# ============================
# RUN BOT
# ============================

bot.run("Bot_Token")
