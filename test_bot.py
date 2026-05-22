import asyncio
from telegram import Bot
import io

async def test():
    bot = Bot(token="8776121523:AAHOQ74ZJR4nIJHSZ5K7t-x96tI7j858jiQ")
    bio = io.BytesIO(b"Hello world")
    bio.seek(0)
    try:
        await bot.send_document(
            chat_id=6106398184,
            document=bio,
            filename="test.md",
            caption="📄 <b>Hasil</b>",
            parse_mode="HTML"
        )
        print("Success")
    except Exception as e:
        print(f"Failed: {type(e).__name__}: {e}")

asyncio.run(test())
