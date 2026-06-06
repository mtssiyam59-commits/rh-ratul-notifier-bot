import os
import requests
import xml.etree.ElementTree as ET
import asyncio
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TELEGRAM_TOKEN = os.environ.get("8811293766:AAHJir3yAp5FFoPcB9IhbTdLbMBe9-4Plho")
CHANNEL_ID     = "UC4_ot3DUs7i0tCj2uwZrG6A"
CHECK_INTERVAL = 60
USERS_FILE     = "subscribers.json"
RSS_URL        = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"
CREDIT         = "👨‍💻 Developer : RH .RATUL"
seen_videos    = set()


def load_users():
    try:
        with open(USERS_FILE, "r") as f:
            return set(json.load(f))
    except:
        return set()

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(list(users), f)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user  = update.effective_user
    users = load_users()
    if user.id not in users:
        users.add(user.id)
        save_users(users)
        msg = (
            f"✅ *স্বাগতম {user.first_name}!*\n\n"
            "আপনি সফলভাবে subscribe করেছেন। 🔔\n"
            "নতুন ভিডিও আসলে notification পাবেন!\n\n"
            f"{CREDIT}"
        )
    else:
        msg = f"✅ *{user.first_name}, আপনি আগে থেকেই subscribed!*\n\n{CREDIT}"
    await update.message.reply_text(msg, parse_mode="Markdown")


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user  = update.effective_user
    users = load_users()
    if user.id in users:
        users.discard(user.id)
        save_users(users)
        msg = (
            f"❌ *{user.first_name}, আপনি unsubscribe করেছেন।*\n\n"
            "আর notification পাবেন না।\n"
            "আবার পেতে /start দিন।\n\n"
            f"{CREDIT}"
        )
    else:
        msg = "আপনি subscribe করেননি। /start দিন।"
    await update.message.reply_text(msg, parse_mode="Markdown")


async def count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = load_users()
    await update.message.reply_text(
        f"👥 মোট subscriber: *{len(users)}* জন\n\n{CREDIT}",
        parse_mode="Markdown"
    )


def get_latest_videos():
    response = requests.get(RSS_URL, timeout=10)
    root     = ET.fromstring(response.content)
    ns       = {"atom": "http://www.w3.org/2005/Atom"}
    videos   = []
    for entry in root.findall("atom:entry", ns):
        videos.append({
            "id"   : entry.find("atom:id", ns).text,
            "title": entry.find("atom:title", ns).text,
            "link" : entry.find("atom:link", ns).attrib["href"],
        })
    return videos


async def broadcast(app, video):
    users = load_users()
    if not users:
        return
    message = (
        "🔔 *নতুন ভিডিও আপলোড হয়েছে!*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"🎬 *{video['title']}*\n\n"
        f"🔗 [▶️ ভিডিও দেখুন]({video['link']})\n\n"
        "⬇️ ডাউনলোড করতে লিংকটি Downloader Bot এ পাঠান\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"{CREDIT}"
    )
    success = 0
    for user_id in list(users):
        try:
            await app.bot.send_message(
                chat_id    = user_id,
                text       = message,
                parse_mode = "Markdown"
            )
            success += 1
        except Exception as e:
            print(f"❌ {user_id} কে পাঠানো যায়নি: {e}")
            if "blocked" in str(e).lower():
                users.discard(user_id)
                save_users(users)
        await asyncio.sleep(0.05)
    print(f"✅ Broadcast — {success} জনকে পাঠানো হয়েছে")


async def poll_youtube(app):
    print("🔄 YouTube polling শুরু হয়েছে... (১ মিনিট পর পর)")
    videos = get_latest_videos()
    for v in videos:
        seen_videos.add(v["id"])
    print(f"ℹ️ {len(seen_videos)} টি পুরানো ভিডিও skip করা হয়েছে।")
    while True:
        await asyncio.sleep(CHECK_INTERVAL)
        try:
            videos = get_latest_videos()
            for video in videos:
                if video["id"] not in seen_videos:
                    print(f"🆕 নতুন ভিডিও: {video['title']}")
                    await broadcast(app, video)
                    seen_videos.add(video["id"])
        except Exception as e:
            print(f"❌ Polling error: {e}")


async def main():
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  Notifier Bot চালু হয়েছে")
    print("  Developer : RH .RATUL")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    while True:
        try:
            app = Application.builder().token(TELEGRAM_TOKEN).build()
            app.add_handler(CommandHandler("start", start))
            app.add_handler(CommandHandler("stop",  stop))
            app.add_handler(CommandHandler("count", count))
            async with app:
                await app.start()
                await app.updater.start_polling(drop_pending_updates=True)
                await poll_youtube(app)
        except Exception as e:
            print(f"❌ Bot crash: {e}")
            print("🔄 ৫ সেকেন্ড পর restart...")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
