from datetime import datetime
import logging
import asyncio
import random
import string
import os
from pymongo import MongoClient
from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
from os import environ
import time
from status import format_progress_bar  # Assuming this is a custom module
from video import download_video, upload_video  # Assuming these are custom modules
from database.database import present_user, add_user, full_userbase, del_user, db_verify_status, db_update_verify_status  # Assuming these are custom modules
from shortzy import Shortzy  # Assuming this is a custom module
from pymongo.errors import DuplicateKeyError
from web import keep_alive
from config import *

load_dotenv('config.env', override=True)

logging.basicConfig(level=logging.INFO)

ADMINS = list(map(int, os.environ.get('ADMINS', '6695586027').split()))
if not ADMINS:
    logging.error("ADMINS variable is missing! Exiting now")
    exit(1)
    
api_id = os.environ.get('TELEGRAM_API', '')
if not api_id:
    logging.error("TELEGRAM_API variable is missing! Exiting now")
    exit(1)

api_hash = os.environ.get('TELEGRAM_HASH', '')
if not api_hash:
    logging.error("TELEGRAM_HASH variable is missing! Exiting now")
    exit(1)
    
bot_token = os.environ.get('BOT_TOKEN', '')
if not bot_token:
    logging.error("BOT_TOKEN variable is missing! Exiting now")
    exit(1)
dump_id = os.environ.get('DUMP_CHAT_ID', '')
if not dump_id:
    logging.error("DUMP_CHAT_ID variable is missing! Exiting now")
    exit(1)
else:
    dump_id = int(dump_id)

fsub_id = os.environ.get('FSUB_ID', '')
if not fsub_id:
    logging.error("FSUB_ID variable is missing! Exiting now")
    exit(1)
else:
    fsub_id = int(fsub_id)


mongo_url = os.environ.get('MONGO_URL', 'mongodb+srv://hegodal811:rsRu17pspZAcp6V7@cluster0.prsvqax.mongodb.net/?retryWrites=true&w=majority')
client = MongoClient(mongo_url)
db = client['cphdlust']
users_collection = db['users']


def save_user(user_id, username):
    try:
        existing_user = users_collection.find_one({'user_id': user_id})
        if existing_user is None:
            users_collection.insert_one({'user_id': user_id, 'username': username})
            logging.info(f"Saved new user {username} with ID {user_id} to the database.")
        else:
            users_collection.update_one({'user_id': user_id}, {'$set': {'username': username}})
            logging.info(f"Updated user {username} with ID {user_id} in the database.")
    except DuplicateKeyError as e:
        logging.error(f"DuplicateKeyError: {e}")

app = Client("my_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

async def get_shortlink(url, api, link):
    shortzy = Shortzy(api_key=api, base_site=url)
    link = await shortzy.convert(link)
    return link

def get_exp_time(seconds):
    periods = [('days', 86400), ('hours', 3600), ('mins', 60), ('secs', 1)]
    result = ''
    for period_name, period_seconds in periods:
        if seconds >= period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            result += f'{int(period_value)}{period_name} '
    return result

def get_readable_time(seconds: int) -> str:
    count = 0
    up_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]
    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)
    hmm = len(time_list)
    for x in range(hmm):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        up_time += f"{time_list.pop()}, "
    time_list.reverse()
    up_time += ":".join(time_list)
    return up_time

async def get_verify_status(user_id):
    verify = await db_verify_status(user_id)
    return verify


a=True
@app.on_message(filters.command("start"))
async def start_command(client, message):
    user_id = message.from_user.id
    user_mention = message.from_user.mention
    
    # Check if user is present
    if not await present_user(user_id):
        try:
            await add_user(user_id)
            logging.info(f"Added user {user_id} to the database")
        except Exception as e:
            logging.error(f"Failed to add user {user_id} to the database: {e}")

    # Send sticker and delete it after 2 seconds
    sticker_message = await message.reply_sticker("CAACAgUAAxkBAAJgv2Z6WDZMA7DVe4Xt2iwIkepCqL5XAALTCgACTEYQVr4X28SRTmMcNQQ")
    await asyncio.sleep(1.8)
    await sticker_message.delete()

    # Get verification status
    verify_status = True

    text = message.text

    if a :
       
        reply_message = (
            f"Welcome, {user_mention}.\n\n"
            "🌟 I am a terabox downloader bot. Send me any terabox link and I will download it within a few seconds and send it to you ✨."
        )
        join_button = InlineKeyboardButton("Join ❤️🚀", url="https://t.me/corn_channels")
        developer_button = InlineKeyboardButton("Developer ⚡️", url="https://t.me/alien_zx")
        reply_markup = InlineKeyboardMarkup([[join_button, developer_button]])
        await message.reply_text(reply_message, reply_markup=reply_markup)
    else:
        pass
        

@app.on_message(filters.command('broadcast') & filters.user(ADMINS))
async def broadcast_command(client, message):
    if message.reply_to_message:
        query = await full_userbase()
        broadcast_msg = message.reply_to_message
        total = 0
        successful = 0
        blocked = 0
        deleted = 0
        unsuccessful = 0
        
        pls_wait = await message.reply("<i>Broadcasting Message.. This will Take Some Time</i>")
        for chat_id in query:
            try:
                await broadcast_msg.copy(chat_id)
                successful += 1
            except FloodWait as e:
                await asyncio.sleep(e.x)
                await broadcast_msg.copy(chat_id)
                successful += 1
            except UserIsBlocked:
                await del_user(chat_id)
                blocked += 1
            except InputUserDeactivated:
                await del_user(chat_id)
                deleted += 1
            except:
                unsuccessful += 1
                pass
            total += 1
        
        status = f"""<b><u>Broadcast Completed</u></b>

Total Users: <code>{total}</code>
Successful: <code>{successful}</code>
Blocked Users: <code>{blocked}</code>
Deleted Accounts: <code>{deleted}</code>
Unsuccessful: <code>{unsuccessful}</code>"""
        
        await pls_wait.edit(status)
    else:
        msg = await message.reply("Please reply to a message to broadcast it.")
        await asyncio.sleep(8)
        await msg.delete()

@app.on_message(filters.command("stats") & filters.user(ADMINS))
async def stats_command(client, message):
    total_users = users_collection.count_documents({})
    verified_users = users_collection.count_documents({"verify_status.is_verified": True})
    unverified_users = total_users - verified_users

    status = f"""<b><u>Verification Stats</u></b>

Total Users: <code>{total_users}</code>
Verified Users: <code>{verified_users}</code>
Unverified Users: <code>{unverified_users}</code>"""

    await message.reply(status)   

async def is_user_member(client, user_id):
    try:
        member = await client.get_chat_member(fsub_id, user_id)
        logging.info(f"User {user_id} membership status: {member.status}")
        if member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return True
        else:
            return False
    except Exception as e:
        logging.error(f"Error checking membership status for user {user_id}: {e}")
        return False

def is_terabox_link(link):
    return "terabox" in link

@app.on_message(filters.text)
async def handle_message(client, message: Message):
    user_id = message.from_user.id
    if not await present_user(user_id):
        try:
            await add_user(user_id)
        except Exception as e:
            logging.error(f"Failed to add user {user_id} to the database: {e}")

    user_mention = message.from_user.mention
    
    verify_status =True



    is_member = await is_user_member(client, user_id)

    if not is_member:
        join_button = InlineKeyboardButton("Join ❤️🚀", url="https://t.me/corn_Channels")
        reply_markup = InlineKeyboardMarkup([[join_button]])
        await message.reply_text("You must join my channel to use me.", reply_markup=reply_markup)
        return

    terabox_link = message.text.strip()

    if not is_terabox_link(terabox_link):
        await message.reply_text("Please send a valid terabox link.")
        return

    reply_msg = await message.reply_text("Sending you the media...🤤")

    try:
        file_path, thumbnail_path, video_title = await download_video(terabox_link, reply_msg, user_mention, user_id)
        await upload_video(client, file_path, thumbnail_path, video_title, reply_msg, dump_id, user_mention, user_id, message)
    except Exception as e:
        logging.error(f"Error handling message: {e}")
        await reply_msg.edit_text("Failed to process your request.\nIf your file size is more than 120MB, it might fail to download.")


if __name__ == "__main__":
    keep_alive()
    app.run()
