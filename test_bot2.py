import asyncio
from telegram import Bot
import io

async def test():
    bot = Bot(token="8776121523:AAHOQ74ZJR4nIJHSZ5K7t-x96tI7j858jiQ")
    # send a message first
    msg = await bot.send_message(chat_id=6106398184, text="To be deleted")
    await msg.delete()
    try:
        await msg.reply_text("Replying to deleted")
        print("reply_text worked")
    except Exception as e:
        print(f"reply_text failed: {type(e).__name__}: {e}")

    bio = io.BytesIO(b"Hello world")
    bio.name = "test.md"
    try:
        await msg.reply_document(document=bio, filename="test.md")
        print("reply_document worked")
    except Exception as e:
        print(f"reply_document failed: {type(e).__name__}: {e}")

asyncio.run(test())
