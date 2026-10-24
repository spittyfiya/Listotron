import json
import os
from datetime import datetime
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)


TOKEN = "ENTER TOKEN HERE"

PLAYERS_FILE = "players.json"
LEADERBOARD_FILE = "leaderboard.json"


POINTS = {
    1: 10,
    2: 8,
    3: 6,
    4: 4,
    5: 2,
}


def load_json(filename, default):
    if not os.path.exists(filename):
        return default

    try:
        with open(filename, "r") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return default


def save_json(filename, data):
    with open(filename, "w") as file:
        json.dump(data, file, indent=4)


players = load_json(PLAYERS_FILE, {})

leaderboard_data = load_json(
    LEADERBOARD_FILE,
    {
        "season": 1,
        "games": []
    }
)


def save_players():
    save_json(PLAYERS_FILE, players)


def save_leaderboard():
    save_json(LEADERBOARD_FILE, leaderboard_data)


def normalize_username(username):
    return username.replace("@", "").strip().lower()


def find_player_by_telegram(username):
    username = normalize_username(username)

    for user_id, player in players.items():
        if normalize_username(player["telegram"]) == username:
            return user_id, player

    return None, None


def find_player_by_poker_name(poker_name):
    poker_name = poker_name.strip().lower()

    for user_id, player in players.items():
        if player["poker"].strip().lower() == poker_name:
            return user_id, player

    return None, None

#==============
# ADMIN CHECK
#=============
async def is_admin(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    chat = update.effective_chat
    user = update.effective_user

    if not chat or not user:
	return False

    if chat.type == "private"
	return False

    member = await context.bot.get_chat_member(
        chat_id=chat.id,
        user_id=user.id,
    )

    return member.status in (
        "administrator",
        "creator",
        "owner",
    )



#================
#JOIN
#=======================
async def join(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    user = update.effective_user

    if not context.args:
        await update.message.reply_text(
            "Use:\n/join PokerNowUsername"
        )
        return

    poker_name = " ".join(context.args).strip()

    players[str(user.id)] = {
        "telegram": user.username or user.first_name,
        "poker": poker_name,
        "user_id": user.id,
        "dm_enabled": False,
        "added_by_admin": False,
    }

    save_players()

    await update.message.reply_text(
        f"✅ Added"
        f"{user.username}"
    )


# ============================================================
# ADMIN ADD
# ============================================================

async def add_user(
	update: Update, 
	context: ContextTypes.DEFAULT_TYPE
	):
    if not update.message.reply_to_message:
	await update.message.reply_text(
	"Please reply to a user's message with /add to register them."
	)
	return

	user = update.target_user

    players[str(user.id)] = {
        "telegram": user.username or user.first_name,
        "poker": poker_name,
	"username": target_user.username or "No Username"
	 "dm_enabled": False,
	"added_by_admin": True,
	}

	save_players()

	await update.message.reply_text(f"✅ Added {username} (ID: `{user_id}`) to the poker system!")

  #CHECK DUPLICATES
    _, existing = find_player_by_telegram(
        telegram_username
      )
    if existing:
        await update.message.reply_text(
            f"⚠️ @{telegram_username} is already "
            f"on the buy-in list."
        )
        return

    _, existing_poker = find_player_by_poker_name(
       poker_name
      )

    if existing_poker:
        await update.message.reply_text(
            f"⚠️ PokerNow username "
            f"'{poker_name}' is already on the list."
        )
        return

    manual_id = f"manual_{target_user.username}"
    players[manual_id] = {
        "user_id": target_user.id,
        "dm_enabled": False,
        "added_by_admin": True,
    }
    save_players()

    await update.message.reply_text(
        f"✅ Added @{telegram_username} - "
        f"{poker_name}\n"
        f"👤 Added manually by admin."
    )

#============
# BUY-IN LIST
async def list_players(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not players:
        await update.message.reply_text(
            "No players registered."
        )
        return

    text = "♠ BUY-IN LIST "
    for number, player in enumerate(
        players.values(),
        start=1
    ):
        text += (
            f"{number}. @{player['telegram']} - "
            f"{player['poker']}\n"
        )

    text += f"\n👥 Total players: {len(players)}"

    await update.message.reply_text(text)


# LEAVE
async def leave(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    user = update.effective_user
    user_id = str(user.id)

    if user_id in players:
        del players[user_id]
        save_players()

        await update.message.reply_text(
            "✅ Removed from tournament."
        )
    else:
        await update.message.reply_text(
            "You are not on the list."
        )


# REMOVE PLAYER(ADMIN REMOVE)
async def remove_player(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not await is_admin(update, context):
        await update.message.reply_text(
            "❌ Only admins can remove players."
        )
        return

    if not context.args:
        await update.message.reply_text(
            "Usage:\n"
            "/remove PokerNowUsername\n"
            "or\n"
            "/remove @TelegramUsername"
        )
        return

    name_to_remove = (
        " ".join(context.args)
        .strip()
        .lower()
        .replace("@", "")
    )

    for user_id, info in list(players.items()):

        poker_name = (
            info["poker"]
            .strip()
            .lower()
        )

        telegram_name = (
            info["telegram"]
            .strip()
            .lower()
            .replace("@", "")
        )

        if (
            poker_name == name_to_remove
            or telegram_name == name_to_remove
        ):
            del players[user_id]
            save_players()

            await update.message.reply_text(
                f"✅ Removed {info['poker']} "
                f"from the list."
            )
            return

    await update.message.reply_text(
        "Player not found."
    )


# EDIT PLAYER====
async def edit_player(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not await is_admin(update, context):
        await update.message.reply_text(
            "❌ Only admins can edit players."
        )
        return

    if len(context.args) < 2:
        await update.message.reply_text(
            "Usage:\n"
            "/edit @TelegramUsername NewPokerNowName"
        )
        return

    telegram_name = (
        context.args[0]
        .replace("@", "")
        .strip()
        .lower()
    )

    new_poker_name = " ".join(
        context.args[1:]
    ).strip()

    for info in players.values():

        saved_telegram_name = (
            info["telegram"]
            .replace("@", "")
            .strip()
            .lower()
        )

        if saved_telegram_name == telegram_name:

            old_poker_name = info["poker"]
            info["poker"] = new_poker_name

            save_players()

            await update.message.reply_text(
                f"✅ Updated @{info['telegram']}\n"
                f"Old: {old_poker_name}\n"
                f"New: {new_poker_name}"
            )
            return

    await update.message.reply_text(
        "Player not found."
    )


# CLEAR CURRENT BUY-IN LIST
async def clear_list(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not await is_admin(update, context):
        await update.message.reply_text(
            "❌ Only admins can clear the list."
        )
        return

    players.clear()
    save_players()

    await update.message.reply_text(
        "✅ The current player list has been cleared.\n"
        "🏆 Leaderboard history was NOT affected."
    )


# ============================================================
# GAME HISTORY, POINTS, LDB (VILLIANS TABLE STATS
# ============================================================

async def record_results(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not await is_admin(update, context):
        await update.message.reply_text(
            "❌ Only admins can record results."
        )
        return

    if len(context.args) != 5:
        await update.message.reply_text(
            "Usage:\n"
            "/results Player1 Player2 Player3 Player4 Player5\n\n"
            "Order must be:\n"
            "1st 2nd 3rd 4th 5th"
        )
        return

    result_names = [
        arg.strip()
        for arg in context.args
    ]

    resolved_players = []

    for name in result_names:

        _, player = find_player_by_telegram(name)

        if not player:
            _, player = find_player_by_poker_name(name)

        if not player:
            await update.message.reply_text(
                f"❌ Could not find player: {name}\n\n"
                f"Use their Telegram username or "
                f"PokerNow username."
            )
            return

        resolved_players.append(player)

    player_keys = [
        (
            normalize_username(p["telegram"]),
            p["poker"].lower()
        )
        for p in resolved_players
    ]

    if len(set(player_keys)) != 5:
        await update.message.reply_text(
            "❌ A player cannot appear more than once "
            "in the same result."
        )
        return

    game_number = len(
        leaderboard_data["games"]
    ) + 1

    game = {
        "game_number": game_number,
        "date": datetime.now().strftime(
            "%Y-%m-%d %H:%M"
        ),
        "results": []
    }

    text = (
        f"🏆 VILLAINS TABLE — GAME #{game_number}\n\n"
    )

    for place, player in enumerate(
        resolved_players,
        start=1
    ):
        points = POINTS[place]

        game["results"].append({
            "place": place,
            "telegram": player["telegram"],
            "poker": player["poker"],
            "points": points,
        })

        if place == 1:
            emoji = "🥇"
        elif place == 2:
            emoji = "🥈"
        elif place == 3:
            emoji = "🥉"
        elif place == 4:
            emoji = "4️⃣"
        else:
            emoji = "5️⃣"

        text += (
            f"{emoji} @{player['telegram']} "
            f"— {points} points\n"
        )

    text += (
        "\n💰 Total points awarded: 30\n"
        f"📅 {game['date']}"
    )

    leaderboard_data["games"].append(game)
    save_leaderboard()

    await update.message.reply_text(text)

def calculate_leaderboard():

    stats = {}

    for game in leaderboard_data["games"]:

        for result in game["results"]:

            key = normalize_username(
                result["telegram"]
            )

            if key not in stats:
                stats[key] = {
                    "telegram": result["telegram"],
                    "poker": result["poker"],
                    "points": 0,
                    "games": 0,
                    "first": 0,
                    "second": 0,
                    "third": 0,
                    "fourth": 0,
                    "fifth": 0,
                }

            player = stats[key]

            player["points"] += result["points"]
            player["games"] += 1

            place = result["place"]

            if place == 1:
                player["first"] += 1
            elif place == 2:
                player["second"] += 1
            elif place == 3:
                player["third"] += 1
            elif place == 4:
                player["fourth"] += 1
            elif place == 5:
                player["fifth"] += 1

    return sorted(
        stats.values(),
        key=lambda x: (
            -x["points"],
            -x["first"],
            -x["second"],
            -x["third"],
        )
    )



async def leaderboard(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    standings = calculate_leaderboard()

    if not standings:
        await update.message.reply_text(
            "🏆 No leaderboard results yet."
        )
        return

    text = (
        "🏆 VILLAINS TABLE LEADERBOARD\n\n"
        f"🎰 Games completed: "
        f"{len(leaderboard_data['games'])}\n"
        f"💰 Points distributed: "
        f"{len(leaderboard_data['games']) * 30}\n\n"
    )

    for rank, player in enumerate(
        standings,
        start=1
    ):
        if rank == 1:
            emoji = "🥇"
        elif rank == 2:
            emoji = "🥈"
        elif rank == 3:
            emoji = "🥉"
        else:
            emoji = f"{rank}."

        text += (
            f"{emoji} @{player['telegram']} "
            f"— **{player['points']} pts**\n"
        )

    await update.message.reply_text(
        text,
        parse_mode="Markdown"
    )

async def my_points(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    user = update.effective_user

    username = user.username

    if not username:
        await update.message.reply_text(
            "❌ You need a Telegram username "
            "to use /mypoints."
        )
        return

    username = normalize_username(username)

    standings = calculate_leaderboard()

    for rank, player in enumerate(
        standings,
        start=1
    ):

        if normalize_username(
            player["telegram"]
        ) == username:

            text = (
                f"🎰 @{player['telegram']}\n\n"
                f"🏆 Rank: #{rank}\n"
                f"⭐ Points: {player['points']}\n"
                f"🎮 Games scored: {player['games']}\n\n"
                f"🥇 Wins: {player['first']}\n"
                f"🥈 2nd place: {player['second']}\n"
                f"🥉 3rd place: {player['third']}\n"
                f"4️⃣ 4th place: {player['fourth']}\n"
                f"5️⃣ 5th place: {player['fifth']}"
            )

            await update.message.reply_text(text)
            return

    await update.message.reply_text(
        "You don't have any leaderboard points yet."
    )


async def games(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not leaderboard_data["games"]:
        await update.message.reply_text(
            "No games have been recorded yet."
        )
        return

    text = "🎰 VILLAINS TABLE GAME HISTORY\n\n"

    for game in leaderboard_data["games"]:

        text += (
            f"🏆 Game #{game['game_number']} "
            f"— {game['date']}\n"
        )

        for result in game["results"]:
            text += (
                f"{result['place']}. "
                f"@{result['telegram']} "
                f"(+{result['points']})\n"
            )

        text += "\n"

    await update.message.reply_text(text)



async def game_result(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not context.args:
        await update.message.reply_text(
            "Usage:\n/gameresult GameNumber\n\n"
            "Example:\n/gameresult 3"
        )
        return

    try:
        game_number = int(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "❌ Game number must be a number."
        )
        return

    game = next(
        (
            game
            for game in leaderboard_data["games"]
            if game["game_number"] == game_number
        ),
        None
    )

    if not game:
        await update.message.reply_text(
            f"❌ Game #{game_number} was not found."
        )
        return

    text = (
        f"🏆 VILLAINS TABLE — GAME #{game_number}\n"
        f"📅 {game['date']}\n\n"
    )

    for result in game["results"]:

        place = result["place"]

        if place == 1:
            emoji = "🥇"
        elif place == 2:
            emoji = "🥈"
        elif place == 3:
            emoji = "🥉"
        elif place == 4:
            emoji = "4️⃣"
        else:
            emoji = "5️⃣"

        text += (
            f"{emoji} @{result['telegram']} "
            f"— {result['points']} points\n"
        )

    await update.message.reply_text(text)



async def undo_results(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not await is_admin(update, context):
        await update.message.reply_text(
            "❌ Only admins can undo results."
        )
        return

    if not leaderboard_data["games"]:
        await update.message.reply_text(
            "There are no recorded games to undo."
        )
        return

    last_game = leaderboard_data["games"].pop()

    save_leaderboard()

    text = (
        f"↩️ Game #{last_game['game_number']} "
        f"has been removed.\n\n"
        "The leaderboard has been recalculated."
    )

    await update.message.reply_text(text)


# ============================================================
#REMINDED


async def send_admin_dm_reminder(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    reminder_text: str,
    confirmation_name: str,
):
    if not await is_admin(update, context):
        await update.message.reply_text(
            "❌ Only group admins can use this command."
        )
        return

    if not players:
        await update.message.reply_text(
            "No registered players."
        )
        return

    sent = 0
    failed = 0

    for info in players.values():
        if not info.get("user_id"):
            continue

        try:
            await context.bot.send_message(
                chat_id=info["user_id"],
                text=reminder_text,
            )
            sent += 1

        except Exception as error:
            failed += 1
            print(
                f"Could not message "
                f"{info.get('telegram', 'Unknown player')}: {error}"
            )

    manual_count = sum(
        1
        for info in players.values()
        if not info.get("user_id")
    )

    response = (
        f"✅ {confirmation_name} sent to "
        f"{sent} player(s)."
    )

    if failed:
        response += (
            f"\n⚠️ Could not message "
            f"{failed} player(s)."
        )

    if manual_count:
        response += (
            f"\nℹ️ {manual_count} manually registered "
            f"player(s) skipped (no user ID)."
        )

    await update.message.reply_text(response)




#REMINDER COMMANDS
#===========
async def remind_poker(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    await send_admin_dm_reminder(
        update=update,
        context=context,
        reminder_text=(
            "♠ Poker starts soon! "
            "Get to your tables!"
        ),
        confirmation_name="Poker reminder",
    )


async def remind15(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    await send_admin_dm_reminder(
        update=update,
        context=context,
        reminder_text=(
            "⏰ Game starts in fifteen minutes!"
        ),
        confirmation_name="15-minute reminder",
    )


async def link_reminder(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    await send_admin_dm_reminder(
        update=update,
        context=context,
        reminder_text=(
            "🔗 Link is out, go register!"
        ),
        confirmation_name="Registration-link reminder",
    )

#======≠=============
# HELP
async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    text = (
        "🎰 LISTOTRON BOT\n"
        "♠ PLAYER COMMANDS\n"
        "/join PokerNowUsername\n"
        "/leave\n"
        "/buyinlist\n"
        "/leaderboard\n"
        "/mypoints\n"
        "/games\n"
        "/gameresult GameNumber\n\n"

        "🛠️ ADMIN COMMANDS\n"
        "/add @TelegramUsername PokerNowUsername"
        "/remove PokerNowUsername\n"
        "/edit @TelegramUsername NewPokerName\n"
        "/clearlist\n"
        "/results Player1 Player2 Player3 Player4 Player5\n"
        "/undoresults\n"
        "/remindpoker\n"
        "/remind15\n"
        "/link\n\n"

        "🏆 POINT SYSTEM\n"
        "🥇 1st — 10 points\n"
        "🥈 2nd — 8 points\n"
        "🥉 3rd — 6 points\n"
        "4️⃣ 4th — 4 points\n"
        "5️⃣ 5th — 2 points\n\n"

        "30 total points are awarded "
        "per Saturday game."
    )

    await update.message.reply_text(text)


def main():

    app = (
        ApplicationBuilder()
        .token(TOKEN)
        .build()
    )

    # Player commands
    app.add_handler(
        CommandHandler("join", join)
    )

    app.add_handler(
        CommandHandler("leave", leave)
    )

    app.add_handler(
        CommandHandler("buyinlist", list_players)
    )

    # Leaderboard commands
    app.add_handler(
        CommandHandler("leaderboard", leaderboard)
    )

    app.add_handler(
        CommandHandler("mypoints", my_points)
    )

    app.add_handler(
        CommandHandler("games", games)
    )

    app.add_handler(
        CommandHandler("gameresult", game_result)
    )

    # Admin commands
    app.add_handler(
        CommandHandler("add", add_user)
    )

    app.add_handler(
        CommandHandler("remove", remove_player)
    )

    app.add_handler(
        CommandHandler("edit", edit_player)
    )

    app.add_handler(
        CommandHandler("clearlist", clear_list)
    )

    app.add_handler(
        CommandHandler("results", record_results)
    )

    app.add_handler(
        CommandHandler("undoresults", undo_results)
    )

    # Reminder commands
    app.add_handler(
        CommandHandler("remindpoker", remind_poker)
    )

    app.add_handler(
        CommandHandler("remind15", remind15)
    )

    app.add_handler(
        CommandHandler("link", link_reminder)
    )

    app.add_handler(
        CommandHandler("help", help_command)
    )

    print("Listotron is running...")

    app.run_polling()


if __name__ == "__main__":
    main()

