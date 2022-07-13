from re import match as re_match, findall as re_findall
from threading import Thread, Event
from time import time
from math import ceil
from html import escape
from psutil import disk_usage, cpu_percent, swap_memory, cpu_count, virtual_memory, net_io_counters, boot_time
from requests import head as rhead
from urllib.request import urlopen
from telegram import InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot import download_dict, download_dict_lock, STATUS_LIMIT, botStartTime, DOWNLOAD_DIR, dispatcher
from bot.helper.telegram_helper.button_build import ButtonMaker

MAGNET_REGEX = r"magnet:\?xt=urn:btih:[a-zA-Z0-9]*"

URL_REGEX = r"(?:(?:https?|ftp):\/\/)?[\w/\-?=%.]+\.[\w/\-?=%.]+"

COUNT = 0
PAGE_NO = 1


class MirrorStatus:
    STATUS_UPLOADING = "Uploading...📤"
    STATUS_DOWNLOADING = "Downloading...📥"
    STATUS_CLONING = "Cloning...♻️"
    STATUS_WAITING = "Queued...💤"
    STATUS_FAILED = "Failed 🚫. Cleaning Download..."
    STATUS_PAUSE = "Paused...⛔️"
    STATUS_ARCHIVING = "Archiving...🔐"
    STATUS_EXTRACTING = "Extracting...📂"
    STATUS_SPLITTING = "Splitting...✂️"
    STATUS_CHECKING = "CheckingUp...📝"
    STATUS_SEEDING = "Seeding...🌧"
    
    
class EngineStatus:
    STATUS_ARIA = "Aria2c v1.35.0"
    STATUS_GD = "Google Api v2.51.0"
    STATUS_MEGA = "MegaSDK v3.12.0"
    STATUS_QB = "qBittorrent v4.4.2"
    STATUS_TG = "Pyrogram v2.0.27"
    STATUS_YT = "YT-dlp v22.5.18"
    STATUS_EXT = "pExtract"
    STATUS_SPLIT = "FFmpeg v2.9.1"
    STATUS_ZIP = "p7zip v16.02"    

SIZE_UNITS = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']


class setInterval:
    def __init__(self, interval, action):
        self.interval = interval
        self.action = action
        self.stopEvent = Event()
        thread = Thread(target=self.__setInterval)
        thread.start()

    def __setInterval(self):
        nextTime = time() + self.interval
        while not self.stopEvent.wait(nextTime - time()):
            nextTime += self.interval
            self.action()

    def cancel(self):
        self.stopEvent.set()

def get_readable_file_size(size_in_bytes) -> str:
    if size_in_bytes is None:
        return '0B'
    index = 0
    while size_in_bytes >= 1024:
        size_in_bytes /= 1024
        index += 1
    try:
        return f'{round(size_in_bytes, 2)}{SIZE_UNITS[index]}'
    except IndexError:
        return 'The File too large'

def getDownloadByGid(gid):
    with download_dict_lock:
        for dl in list(download_dict.values()):
            status = dl.status()
            if (
                status
                not in [
                    MirrorStatus.STATUS_ARCHIVING,
                    MirrorStatus.STATUS_EXTRACTING,
                    MirrorStatus.STATUS_SPLITTING,
                ]
                and dl.gid() == gid
            ):
                return dl
    return None

def getAllDownload(req_status: str):
    with download_dict_lock:
        for dl in list(download_dict.values()):
            status = dl.status()
            if status not in [MirrorStatus.STATUS_ARCHIVING, MirrorStatus.STATUS_EXTRACTING, MirrorStatus.STATUS_SPLITTING] and dl:
                if req_status == 'down' and (status not in [MirrorStatus.STATUS_SEEDING,
                                                            MirrorStatus.STATUS_UPLOADING,
                                                            MirrorStatus.STATUS_CLONING]):
                    return dl
                elif req_status == 'up' and status == MirrorStatus.STATUS_UPLOADING:
                    return dl
                elif req_status == 'clone' and status == MirrorStatus.STATUS_CLONING:
                    return dl
                elif req_status == 'seed' and status == MirrorStatus.STATUS_SEEDING:
                    return dl
                elif req_status == 'all':
                    return dl
    return None

def get_progress_bar_string(status):
    completed = status.processed_bytes() / 8
    total = status.size_raw() / 8
    p = 0 if total == 0 else round(completed * 100 / total)
    p = min(max(p, 0), 100)
    cFull = p // 8
    p_str = '⬤' * cFull
    p_str += '○' * (12 - cFull)
    p_str = f"[{p_str}]"
    return p_str

def get_readable_message():
    with download_dict_lock:
        num_active = 0
        num_all = 0
        for stats in list(download_dict.values()):
            if stats.status() not in [MirrorStatus.STATUS_WAITING, MirrorStatus.STATUS_FAILED, MirrorStatus.STATUS_PAUSE, MirrorStatus.STATUS_CHECKING]:
                num_active += 1
            num_all += 1
        msg = f'<b><i><u>Bot Of {CHAT_NAME}</u></i></b>\n\n'
        msg += f"<b><i>Active: {num_active}/{num_all}</i></b>\n\n"
        if STATUS_LIMIT is not None:
            tasks = len(download_dict)
            global pages
            pages = ceil(tasks/STATUS_LIMIT)
            if PAGE_NO > pages and pages != 0:
                globals()['COUNT'] -= STATUS_LIMIT
                globals()['PAGE_NO'] -= 1
        for index, download in enumerate(list(download_dict.values())[COUNT:], start=1):
            msg += f"<b>{download.status()}:</b> <code>{escape(str(download.name()))}</code>"
            if download.status() not in [
                MirrorStatus.STATUS_ARCHIVING,
                MirrorStatus.STATUS_EXTRACTING,
                MirrorStatus.STATUS_SPLITTING,
                MirrorStatus.STATUS_SEEDING,
            ]:
                msg += f"\n{get_progress_bar_string(download)} {download.progress()}"
                if download.status() == MirrorStatus.STATUS_CLONING:
                    msg += f"\n<b>Cloned:</b> {get_readable_file_size(download.processed_bytes())} of {download.size()}"
                elif download.status() == MirrorStatus.STATUS_UPLOADING:
                    msg += f"\n<b>Uploaded:</b> {get_readable_file_size(download.processed_bytes())} of {download.size()}"
                else:
                    msg += f"\n<b>Downloaded:</b> {get_readable_file_size(download.processed_bytes())} of {download.size()}"
                msg += f"\n<b>Speed:</b> {download.speed()} | <b>ETA:</b> {download.eta()}"
                try:
                    msg += f"\n<b>Seeders:</b> {download.aria_download().num_seeders}" \
                           f" | <b>Peers:</b> {download.aria_download().connections}"
                except:
                    pass
                try:
                    msg += f"\n<b>Seeders:</b> {download.torrent_info().num_seeds}" \
                           f" | <b>Leechers:</b> {download.torrent_info().num_leechs}"
                 except Exception:
                    pass
                msg += f'\n<b>Adder:</b> {download.message.from_user.first_name} (<code>{download.message.from_user.id}</code>)'
                msg += f"\n<code>/{BotCommands.CancelMirror[0]} {download.gid()}</code>"
            elif download.status() == MirrorStatus.STATUS_SEEDING:
                msg += f"\n<b>Size: </b>{download.size()}"
                msg += f"\n<b>Elapsed Time:</b> {download.elapsed()}" 
                msg += f"\n<b>Speed: </b>{get_readable_file_size(download.torrent_info().upspeed)}/s"
                msg += f" | <b>Uploaded: </b>{get_readable_file_size(download.torrent_info().uploaded)}"
                msg += f"\n<b>Ratio: </b>{round(download.torrent_info().ratio, 3)}"
                msg += f" | <b>Time: </b>{get_readable_time(download.torrent_info().seeding_time)}"
                msg += f'\n<b>Adder:</b> {download.message.from_user.first_name} (<code>{download.message.from_user.id}</code>)'
                msg += f"\n<code>/{BotCommands.CancelMirror[0]} {download.gid()}</code>"
            else:
                msg += f"\n<b>Size: </b>{download.size()}"
                msg += f"\n<b>Elapsed Time:</b> {download.elapsed()}"
            msg += "\n\n"
            if STATUS_LIMIT is not None and index == STATUS_LIMIT:
                break
        bmsg = f"\n<b>_____________________________________</b>"        
        bmsg = f"<b>CPU:</b> {cpu_percent()}% | <b>FREE:</b> {get_readable_file_size(disk_usage(DOWNLOAD_DIR).free)}"
        bmsg += f"\n<b>RAM:</b> {virtual_memory().percent}% | <b>UPTIME:</b> {get_readable_time(time() - botStartTime)}"
        dlspeed_bytes = 0
        upspeed_bytes = 0
        for download in list(download_dict.values()):
            spd = download.speed()
            if download.status() == MirrorStatus.STATUS_DOWNLOADING:
                if 'K' in spd:
                    dlspeed_bytes += float(spd.split('K')[0]) * 1024
                elif 'M' in spd:
                    dlspeed_bytes += float(spd.split('M')[0]) * 1048576
            elif download.status() == MirrorStatus.STATUS_UPLOADING:
                if 'KB/s' in spd:
                    upspeed_bytes += float(spd.split('K')[0]) * 1024
                elif 'MB/s' in spd:
                    upspeed_bytes += float(spd.split('M')[0]) * 1048576
        bmsg += f"\n<b>DL:</b> {get_readable_file_size(dlspeed_bytes)}/s | <b>UL:</b> {get_readable_file_size(upspeed_bytes)}/s"
        buttons = ButtonMaker()
        if STATUS_LIMIT is not None and tasks > STATUS_LIMIT:
            buttons.sbutton("Previous", "status pre")
            buttons.sbutton(f"{PAGE_NO}/{pages}", "ex refresh")
            buttons.sbutton("Next", "status nex")
        buttons.sbutton("Close", "ex close")
        button = InlineKeyboardMarkup(buttons.build_menu(3))
        return msg + bmsg, button

def turn(data):
    try:
        with download_dict_lock:
            global COUNT, PAGE_NO
            if data[1] == "nex":
                if PAGE_NO == pages:
                    COUNT = 0
                    PAGE_NO = 1
                else:
                    COUNT += STATUS_LIMIT
                    PAGE_NO += 1
            elif data[1] == "pre":
                if PAGE_NO == 1:
                    COUNT = STATUS_LIMIT * (pages - 1)
                    PAGE_NO = pages
                else:
                    COUNT -= STATUS_LIMIT
                    PAGE_NO -= 1
        return True
    except Exception:
        return False

def get_readable_time(seconds: int) -> str:
    result = ''
    (days, remainder) = divmod(seconds, 86400)
    days = int(days)
    if days != 0:
        result += f'{days}d'
    (hours, remainder) = divmod(remainder, 3600)
    hours = int(hours)
    if hours != 0:
        result += f'{hours}h'
    (minutes, seconds) = divmod(remainder, 60)
    minutes = int(minutes)
    if minutes != 0:
        result += f'{minutes}m'
    seconds = int(seconds)
    result += f'{seconds}s'
    return result

def is_url(url: str):
    url = re_findall(URL_REGEX, url)
    return bool(url)

def is_gdrive_link(url: str):
    return "drive.google.com" in url

def is_gdtot_link(url: str):
    url = re_match(r'https?://.+\.gdtot\.\S+', url)
    return bool(url)

def is_appdrive_link(url: str):
    url = re_match(r'https?://(?:\S*\.)?(?:appdrive|driveapp)\.in/\S+', url)
    return bool(url)
def is_mega_link(url: str):
    return "mega.nz" in url or "mega.co.nz" in url

def get_mega_link_type(url: str):
    if "folder" in url:
        return "folder"
    elif "file" in url:
        return "file"
    elif "/#F!" in url:
        return "folder"
    return "file"

def is_magnet(url: str):
    magnet = re_findall(MAGNET_REGEX, url)
    return bool(magnet)

def new_thread(fn):
    """To use as decorator to make a function call threaded.
    Needs import
    from threading import Thread"""

    def wrapper(*args, **kwargs):
        thread = Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread

    return wrapper

def get_content_type(link: str) -> str:
    try:
        res = rhead(link, allow_redirects=True, timeout=5, headers = {'user-agent': 'Wget/1.12'})
        content_type = res.headers.get('content-type')
    except Exception:
        try:
            res = urlopen(link, timeout=5)
            info = res.info()
            content_type = info.get_content_type()
        except Exception:
            content_type = None
    return content_type

def CheckAdmin(message, user_id: int):
    msg = message
    if msg.chat.type == "private" \
        or user_id in [OWNER_ID] \
        or user_id in SUDO_USERS \
        or bot.get_chat_member(msg.chat.id, msg.from_user.id).status in ['creator', 'administrator'] \
        or user_id == 1087968824 \
        or (msg.reply_to_message and msg.reply_to_message.sender_chat is not None and msg.reply_to_message.sender_chat.type != "channel"):
        return True
    

def CheckUser(message, user_id: int):
    admins = bool(CheckAdmin(message, user_id))
    reply_to = message.reply_to_message
    try:
        if not FSUB_CHNL:
            return True
        if not admins:
            user = dispatcher.bot.getChatMember(chat_id=f'{FSUB_CHNL}', user_id=user_id)
            if user.status == 'member' or user.status not in ['left', 'kicked']:
                return True
            elif user.status == 'left':
                LOGGER.info("User is Not Member")
                Fsub= message_utils.sendFsub(bot, message)
                Thread(target=message_utils.auto_delete_message, args=(bot, message, Fsub)).start() 
                if reply_to is not None:
                    reply_to.delete()       
                return False
            else:
                LOGGER.info("User Banned")
                Fsub= message_utils.sendMessage("You Are Banned For Using Me", bot, message)
                Thread(target=message_utils.auto_delete_message, args=(bot, message, Fsub)).start()  
                if reply_to is not None:
                    reply_to.delete()    
                return False       
    except (Unauthorized, BadRequest) as e:
            LOGGER.error(str(e))
            return True
        
def CheckPM(bot, message) -> bool:
    reply_to = message.reply_to_message
    sendpm = bool(FORCE_PM)
    if sendpm and message.chat.type != "private":
        pmcheck = message_utils.sendPm(".", bot, message)
        if pmcheck:
            message_utils.deleteMessage(bot, pmcheck)
        else:
            FStart = message_utils.sendPMTxt(bot, message)
            Thread(target=message_utils.auto_delete_message, args=(bot, message, FStart)).start()
            if reply_to is not None:
                    reply_to.delete()
            return False
    else:
        return True        

def Verify(listener, message, name:str, size:int, mega=None, clone=None) -> bool:
    admins = bool(CheckAdmin(message, message.from_user.id))
    BLACKLIST_TEXT="<b>Blacklisted Word Detected</b>\n\n<b>User: {}</b>(<code>{}</code>)\n\n<b>Name:</b> <code>{}</code>\n\n<b>Blacklist Word: {}</b>\n\n<b>Note: If You Think It's An Error, Tag @admin For Verification</b>\n<b>Only An Admin Can Add This Task.</b>\n\n#Report {}"
    tag = f"<a href='tg://user?id={message.from_user.id}'>{message.from_user.first_name}</a>"
    if admins:
        LOGGER.info("Admin Detected")
        return True
    if BLACKLIST:
        LOGGER.info('Checking Blacklist')
        for bword in BLACKLIST:
            bword = bword + ' '
            if bword.lower() in name.lower():
                LOGGER.info("Blacklisted Word Detected")
                text = BLACKLIST_TEXT.format(tag, message.from_user.id, name, bword, message.chat.title)
                msg = message_utils.sendMessage(text, bot, message)
                if AUTO_DELETE_UPLOAD != -1 and message.chat.id not in WHITELIST and message.chat.type != 'private':
                    Thread(target=message_utils.auto_delete_upload, args=(bot, message, msg)).start()    
                return False

    if any([ZIP_UNZIP_LIMIT, STORAGE_THRESHOLD, TORRENT_DIRECT_LIMIT, CLONE_LIMIT]):
        arch = clone is None and any([listener.extract, listener.isZip, listener.isTar])
        limit = None
        if STORAGE_THRESHOLD is not None and clone is None:
            acpt = check_storage_threshold(size, arch)
            if not acpt:
                msg1 = f'You must leave {STORAGE_THRESHOLD}GB free storage.'
                msg1 += f'\nYour File/Folder size is {get_readable_file_size(size)}'
                msg = message_utils.sendMessage(msg1, bot, message)
                if AUTO_DELETE_UPLOAD != -1 and message.chat.id not in WHITELIST and message.chat.type != 'private':
                    Thread(target=message_utils.auto_delete_upload, args=(bot, message, msg1)).start()
                return False
        if clone and CLONE_LIMIT is not None:
            mssg = f'Failed, Clone limit is {CLONE_LIMIT}GB'
            limit = CLONE_LIMIT    
        elif ZIP_UNZIP_LIMIT is not None and arch:
            mssg = f'Zip/Unzip limit is {ZIP_UNZIP_LIMIT}GB'
            limit = ZIP_UNZIP_LIMIT
        elif mega and MEGA_LIMIT is not None:
            mssg = f'Failed, Mega limit is {MEGA_LIMIT}GB'
            limit = MEGA_LIMIT
        elif mega is None and clone is None and TORRENT_DIRECT_LIMIT is not None:
            mssg = f'Torrent/Direct limit is {TORRENT_DIRECT_LIMIT}GB'
            limit = TORRENT_DIRECT_LIMIT
        if limit is not None:
            LOGGER.info('Checking File/Folder Size...')
            if size > limit * 1024**3:
                msg2 = f'{mssg}.\nYour File/Folder size is {get_readable_file_size(size)}.'
                msg = message_utils.sendMessage(msg2, bot, message)    
                if AUTO_DELETE_UPLOAD != -1 and message.chat.id not in WHITELIST and message.chat.type != 'private':
                    Thread(target=message_utils.auto_delete_upload, args=(bot, message, msg)).start()
                return False
    if not STOP_DUPLICATE or clone is None and listener.isLeech:
        return True
    LOGGER.info('Checking File/Folder if already in Drive...')
    if clone is None:
        if listener.isZip:
            name += ".zip"
        elif listener.isTar:
            name += ".tar"
        elif listener.extract:
            try:
                name = get_base_name(name)
            except Exception:
                pass
    if name is not None:
        gmsg, button = GoogleDriveHelper().drive_list(name, True)
        if gmsg:
            text = "File/Folder is already available in Drive.\nHere are the search results:"
            msg = message_utils.sendMessage(text, bot, message, button)
            if AUTO_DELETE_UPLOAD != -1 and message.chat.id not in WHITELIST and message.chat.type != 'private':
                Thread(target=message_utils.auto_delete_upload, args=(bot, message, msg)).start()
            return False         
        
def scbb(update, context):
    query = update.callback_query
    chat = update.effective_chat
    admin = chat.get_member(query.from_user.id).status in ["creator", "administrator"] or query.from_user.id in [OWNER_ID] or int(query.from_user.id) in SUDO_USERS
    data = query.data
    data = data.split(' ')
    if data[1] == "refresh":
        try:
            if KEYWORD is not None:
                query.edit_message_caption(caption="Refreshing Status...⏳")
            else:     
                query.edit_message_text(text="Refreshing Status...⏳")
            message_utils.update_all_messages()
            query.answer(text="Refreshed", show_alert=False)
        except Exception:
            query.answer(text="Query Too Old", show_alert=False)
            query.message.delete()
    elif data[1] == "close":
        if admin:
            query.answer(text="Closed", show_alert=False)
            message_utils.delete_all_messages()
        else:
            qmsg = f"{query.from_user.first_name} I Am Bound To Work For Admins Only"
            query.answer(text=qmsg, show_alert=True)    
                        

dispatcher.add_handler(CallbackQueryHandler(scbb, pattern='ex', run_async=True))

# Workaround for circular imports
from bot.helper.mirror_utils.upload_utils.gdriveTools import GoogleDriveHelper
