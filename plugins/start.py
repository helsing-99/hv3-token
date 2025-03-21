# +++ Made By King [telegram username: @Shidoteshika1] +++

import os
import sys
import random
import asyncio
import subprocess
from bot import Bot
from database.database import kingdb
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from plugins.FORMATS import START_MSG, FORCE_MSG
from pyrogram.enums import ParseMode, ChatAction
from config import CUSTOM_CAPTION, OWNER_ID, PICS
from plugins.autoDelete import auto_del_notification, delete_message
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from helper_func import * #banUser, is_userJoin, is_admin, subscribed, encode, decode, get_messages
from database.verify_db import *
import string as rohit

@Bot.on_message(filters.command('start') & filters.private & ~banUser & subscribed)
async def start_command(client: Client, message: Message): 
    await message.reply_chat_action(ChatAction.CHOOSE_STICKER)
    id = message.from_user.id  
    
    if not await kingdb.present_user(id):
        try: await kingdb.add_user(id)
        except: pass
    
    SHORTLINK_URL = await db.get_shortener_url()
    SHORTLINK_API = await db.get_shortener_api()
    VERIFY_EXPIRE = await db.get_verified_time()
    TUT_VID = await db.get_tut_video()
    
    
    # Check if user is an admin and treat them as verified
    if await kingdb.admin_exist(id):
        verify_status = {
            'is_verified': True,
            'verify_token': None,  # Admins don't need a token
            'verified_time': time.time(),
            'link': ""
        }
    else:
        verify_status = await get_verify_status(id)

        # If TOKEN is enabled, handle verification logic
        if SHORTLINK_URL:
            if verify_status['is_verified'] and VERIFY_EXPIRE < (time.time() - verify_status['verified_time']):
                await update_verify_status(id, is_verified=False)

            if "verify_" in message.text:
                _, token = message.text.split("_", 1)
                if verify_status['verify_token'] != token:
                    return await message.reply("Your token is invalid or expired. Try again by clicking /start.")
                await update_verify_status(id, is_verified=True, verified_time=time.time())
                if verify_status["link"] == "":
                    reply_markup = None
                return await message.reply(
                    f"Your token has been successfully verified and is valid for {get_exp_time(VERIFY_EXPIRE)}",
                    reply_markup=reply_markup,
                    protect_content=False,
                    quote=True
                )

            if not verify_status['is_verified']:
                token = ''.join(random.choices(rohit.ascii_letters + rohit.digits, k=10))
                await update_verify_status(id, verify_token=token, link="")
                link = await get_shortlink(SHORTLINK_URL, SHORTLINK_API, f'https://telegram.dog/{client.username}?start=verify_{token}')
                btn = [
                    [InlineKeyboardButton("• ᴏᴘᴇɴ ʟɪɴᴋ •", url=link)],
                    [InlineKeyboardButton('• ʜᴏᴡ ᴛᴏ ᴏᴘᴇɴ ʟɪɴᴋ •', url=TUT_VID)]
                ]
                return await message.reply(
                    f"<b>Your token has expired. Please refresh your token to continue.\n\nToken Timeout: {get_exp_time(VERIFY_EXPIRE)}\n\nWhat is the token?\n\nThis is an ads token. Passing one ad allows you to use the bot for {get_exp_time(VERIFY_EXPIRE)}</b>",
                    reply_markup=InlineKeyboardMarkup(btn),
                    protect_content=False,
                    quote=True
                )
                
    text = message.text        
    if len(text)>7:
        await message.delete()

        try: base64_string = text.split(" ", 1)[1]
        except: return
                
        string = await decode(base64_string)
        argument = string.split("-")
        
        if len(argument) == 3:
            try:
                start = int(int(argument[1]) / abs(client.db_channel.id))
                end = int(int(argument[2]) / abs(client.db_channel.id))
            except:
                return
                    
            if start <= end:
                ids = range(start,end+1)
            else:
                ids = []
                i = start
                while True:
                    ids.append(i)
                    i -= 1
                    if i < end:
                        break
                            
        elif len(argument) == 2:
            try: ids = [int(int(argument[1]) / abs(client.db_channel.id))]
            except: return
                    
        last_message = None
        await message.reply_chat_action(ChatAction.UPLOAD_DOCUMENT)  
        
        try: messages = await get_messages(client, ids)
        except: return await message.reply("<b><i>Sᴏᴍᴇᴛʜɪɴɢ ᴡᴇɴᴛ ᴡʀᴏɴɢ..!</i></b>")
            
        AUTO_DEL, DEL_TIMER, HIDE_CAPTION, CHNL_BTN, PROTECT_MODE = await asyncio.gather(kingdb.get_auto_delete(), kingdb.get_del_timer(), kingdb.get_hide_caption(), kingdb.get_channel_button(), kingdb.get_protect_content())   
        if CHNL_BTN: button_name, button_link = await kingdb.get_channel_button_link()
            
        for idx, msg in enumerate(messages):
            if bool(CUSTOM_CAPTION) & bool(msg.document):
                caption = CUSTOM_CAPTION.format(previouscaption = "" if not msg.caption else msg.caption.html, filename = msg.document.file_name)

            elif HIDE_CAPTION: #and (msg.document or msg.audio):
                caption = ""

            else:
                caption = "" if not msg.caption else msg.caption.html

            if CHNL_BTN:
                reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(text=button_name, url=button_link)]]) #if msg.document or msg.photo or msg.video or msg.audio else None
            else:
                reply_markup = msg.reply_markup   
                    
            try:
                copied_msg = await msg.copy(chat_id=id, caption=caption, parse_mode=ParseMode.HTML, reply_markup=reply_markup, protect_content=PROTECT_MODE)
                await asyncio.sleep(0.1)

                if AUTO_DEL:
                    asyncio.create_task(delete_message(copied_msg, DEL_TIMER))
                    if idx == len(messages) - 1: last_message = copied_msg

            except FloodWait as e:
                await asyncio.sleep(e.x)
                copied_msg = await msg.copy(chat_id=id, caption=caption, parse_mode=ParseMode.HTML, reply_markup=reply_markup, protect_content=PROTECT_MODE)
                await asyncio.sleep(0.1)
                
                if AUTO_DEL:
                    asyncio.create_task(delete_message(copied_msg, DEL_TIMER))
                    if idx == len(messages) - 1: last_message = copied_msg
                        
        if AUTO_DEL and last_message:
                asyncio.create_task(auto_del_notification(client.username, last_message, DEL_TIMER, message.command[1]))
                        
    else:   
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton('🤖 Aʙᴏᴜᴛ ᴍᴇ', callback_data= 'about'), InlineKeyboardButton('Sᴇᴛᴛɪɴɢs ⚙️', callback_data='setting')]])

        await message.reply_photo(
            photo = random.choice(PICS),
            caption = START_MSG.format(
                first = message.from_user.first_name,
                last = message.from_user.last_name,
                username = None if not message.from_user.username else '@' + message.from_user.username,
                mention = message.from_user.mention,
                id = message.from_user.id
            ),
            reply_markup = reply_markup,
	        message_effect_id=5104841245755180586 #🔥
        )
        try: await message.delete()
        except: pass

   
##===================================================================================================================##

#TRIGGRED START MESSAGE FOR HANDLE FORCE SUB MESSAGE AND FORCE SUB CHANNEL IF A USER NOT JOINED A CHANNEL

##===================================================================================================================##   


@Bot.on_message(filters.command('start') & filters.private & ~banUser)
async def not_joined(client: Client, message: Message):
    temp = await message.reply(f"<i><b>Cʜᴇᴄᴋɪɴɢ...</b></i>")
    
    try:
        if not client.REQFSUB:
            buttons = client.FSUB_BUTTONS[:]

        else:
            user_id = message.from_user.id

            buttons = client.REQ_FSUB_BUTTONS['normal'][:]

            buttons.extend([chat_button for chat_id, chat_button in client.REQ_FSUB_BUTTONS['request'].items() if not await kingdb.reqSent_user_exist(chat_id, user_id)])
                                             
        try:
            buttons.append([InlineKeyboardButton(text='♻️ Tʀʏ Aɢᴀɪɴ', url=f"https://t.me/{client.username}?start={message.command[1]}")])
        except IndexError:
            pass
                     
        await temp.edit(  
            text=FORCE_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name,
                username=None if not message.from_user.username else '@' + message.from_user.username,
                mention=message.from_user.mention,
                id=message.from_user.id,
            ),
            reply_markup=InlineKeyboardMarkup(buttons)
        )
                
        try: await message.delete()
        except: pass
                        
    except Exception as e:
        print(f"Unable to perform forcesub buttons reason : {e}")
        return await temp.edit(f"<b><i>! Eʀʀᴏʀ, Cᴏɴᴛᴀᴄᴛ ᴅᴇᴠᴇʟᴏᴘᴇʀ ᴛᴏ sᴏʟᴠᴇ ᴛʜᴇ ɪssᴜᴇs @Shidoteshika1</i>\n<blockquote expandable>Rᴇᴀsᴏɴ:</b> {e}</blockquote>")



#=====================================================================================##
#......... RESTART COMMAND FOR RESTARTING BOT .......#
#=====================================================================================##

@Bot.on_message(filters.command('restart') & filters.private & filters.user(OWNER_ID))
async def restart_bot(client: Client, message: Message):
    print("Restarting bot...")
    msg = await message.reply(text=f"<b><i><blockquote>⚠️ {client.name} ɢᴏɪɴɢ ᴛᴏ Rᴇsᴛᴀʀᴛ...</blockquote></i></b>")
    try:
        await asyncio.sleep(6)  # Wait for 6 seconds before restarting
        await msg.delete()
        args = [sys.executable, "main.py"]  # Adjust this if your start file is named differently
        os.execl(sys.executable, *args)
    except Exception as e:
        print(f"Error occured while Restarting the bot: {e}")
        return await msg.edit_text(f"<b><i>! Eʀʀᴏʀ, Cᴏɴᴛᴀᴄᴛ ᴅᴇᴠᴇʟᴏᴘᴇʀ ᴛᴏ sᴏʟᴠᴇ ᴛʜᴇ ɪssᴜᴇs @Shidoteshika1</i></b>\n<blockquote expandable><b>Rᴇᴀsᴏɴ:</b> {e}</blockquote>")
    # Optionally, you can add cleanup tasks here
    #subprocess.Popen([sys.executable, "main.py"])  # Adjust this if your start file is named differently
    #sys.exit()


@Bot.on_message(filters.command('token') & filters.private & filters.user(OWNER_ID))
async def set_shortener(client, message):
    await message.reply_chat_action(ChatAction.TYPING)

    try:
        # Fetch shortener URL and API key from the database
        shortener_url = await db.get_shortener_url()  # Fetch the shortener URL
        shortener_api = await db.get_shortener_api()  # Fetch the shortener API key

        if shortener_url and shortener_api:
            # If both URL and API key are available, the shortener is considered "Enabled ✅"
            shortener_status = "Enabled ✅"
            mode_button = InlineKeyboardButton('Disable Shortener ❌', callback_data='disable_shortener')
        else:
            # If either URL or API key is missing, the shortener is "Disabled ❌"
            shortener_status = "Disabled ❌"
            mode_button = InlineKeyboardButton('Enable Shortener ✅', callback_data='set_shortener_details')

        # Send the settings message with the toggle button and other options
        await message.reply_photo(
            photo=random.choice(PICS),
            caption=(
                f"🔗 Shortener Settings\n\n"
                f"Shortener Status: {shortener_status}\n\n"
                f"Use the options below to configure the shortener."
            ),
            reply_markup=InlineKeyboardMarkup([
                [mode_button],
                [InlineKeyboardButton('Set Site', callback_data='set_shortener_details')],
                [
                    InlineKeyboardButton('Settings ⚙️', callback_data='shortener_settings'),
                    InlineKeyboardButton('🔄 Refresh', callback_data='set_shortener')
                ],
                [
                    InlineKeyboardButton('Set Verified Time ⏱', callback_data='set_verify_time'),
                    InlineKeyboardButton('Set Tutorial Video 🎥', callback_data='set_tut_video')
                ],
                [InlineKeyboardButton('Close ✖️', callback_data='close')]
            ])
        )
    except Exception as e:
        # Log the error for debugging purposes
        #logging.error(f"Error in set_shortener command: {e}")
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Close ✖️", callback_data="close")]])
        await message.reply(
            (
                f"❌ Error Occurred:\n\n"
                f"Reason: {e}\n\n"
                f"📩 Contact developer: [Rohit](https://t.me/rohit_1888)"
            ),
            reply_markup=reply_markup
        )