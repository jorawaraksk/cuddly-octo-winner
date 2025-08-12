import os
import subprocess
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message

API_ID = int(os.environ.get("API_ID", 647615905110))
API_HASH = os.environ.get("API_HASH", "9BBD3D12EE2C673A60BD8C2A76C07905")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "7078710813:AAEewmdbVbBK9F67F1h2IwOl0IVAI8YXYlo")

app = Client("compress_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Store user compression mode {user_id: "audio" or "video"}
user_modes = {}


# -------- Start Command -------- #
@app.on_message(filters.command("start") & filters.private)
async def start_handler(_, message: Message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎵 Compress Audio", callback_data="mode_audio")],
        [InlineKeyboardButton("🎥 Compress Video", callback_data="mode_video")]
    ])
    await message.reply_text(
        "Hi! Choose what you want to compress:",
        reply_markup=keyboard
    )


# -------- Button Callback -------- #
@app.on_callback_query()
async def callback_handler(_, query: CallbackQuery):
    user_id = query.from_user.id
    if query.data == "mode_audio":
        user_modes[user_id] = "audio"
        await query.message.reply_text("✅ Audio compression mode set.\nNow send me an audio/voice file.")
    elif query.data == "mode_video":
        user_modes[user_id] = "video"
        await query.message.reply_text("✅ Video compression mode set.\nNow send me a video/animation file.")
    await query.answer()


# -------- File Handler -------- #
@app.on_message(filters.private & (filters.audio | filters.voice | filters.video | filters.animation))
async def file_handler(_, message: Message):
    user_id = message.from_user.id
    mode = user_modes.get(user_id)

    if not mode:
        await message.reply_text("⚠ Please choose a mode first using /start.")
        return

    # Download file
    status = await message.reply_text("⬇ Downloading file...")
    file_path = await app.download_media(message)
    await status.edit("⚙ Compressing...")

    try:
        if mode == "audio":
            output_path = f"compressed_{os.path.basename(file_path)}"
            cmd = [
                "ffmpeg", "-y", "-i", file_path,
                "-b:a", "64k", "-ac", "1", output_path
            ]
        else:  # video mode
            output_path = f"compressed_{os.path.basename(file_path)}"
            cmd = [
                "ffmpeg", "-y", "-i", file_path,
                "-vcodec", "libx264", "-crf", "28", "-preset", "veryfast",
                "-acodec", "aac", "-b:a", "64k", output_path
            ]

        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        await status.edit("📤 Uploading compressed file...")
        await message.reply_document(output_path, caption="✅ Compressed file")

    except subprocess.CalledProcessError as e:
        await status.edit(f"❌ Compression failed:\n`{e}`")
    finally:
        # Cleanup
        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(output_path):
            os.remove(output_path)
        await status.delete()

app.run()
