from asyncio import get_event_loop
from faulthandler import enable as faulthandler_enable
from json import loads as jsnloads
from logging import INFO, FileHandler, StreamHandler, basicConfig
from logging import error as log_error
from logging import getLogger
from logging import info as log_info
from logging import warning as log_warning
from os import environ, getcwd
from os import path as ospath
from os import remove as osremove
from socket import setdefaulttimeout
from subprocess import Popen, check_output
from subprocess import run as srun
from threading import Lock, Thread
from time import sleep, time

from aria2p import API as ariaAPI
from aria2p import Client as ariaClient
from dotenv import load_dotenv
from megasdkrestclient import MegaSdkRestClient
from megasdkrestclient import errors as mega_err
from pyrogram import Client, enums
from qbittorrentapi import Client as qbClient
from requests import get as rget
from telegram.ext import Updater as tgUpdater

main_loop = get_event_loop()

faulthandler_enable()

setdefaulttimeout(600)

botStartTime = time()

basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[FileHandler('log.txt'), StreamHandler()],
                    level=INFO)

LOGGER = getLogger(__name__)

CONFIG_FILE_URL = environ.get('CONFIG_FILE_URL')
try:
    if len(CONFIG_FILE_URL) == 0:
        raise TypeError
    try:
        res = rget(CONFIG_FILE_URL)
        if res.status_code == 200:
            with open('config.env', 'wb+') as f:
                f.write(res.content)
        else:
            log_error(f"Failed to download config.env {res.status_code}")
    except Exception as e:
        log_error(f"CONFIG_FILE_URL: {e}")
except Exception:
    pass

load_dotenv('config.env', override=True)

def getConfig(name: str):
    return environ[name]

try:
    NETRC_URL = getConfig('NETRC_URL')
    if len(NETRC_URL) == 0:
        raise KeyError
    try:
        res = rget(NETRC_URL)
        if res.status_code == 200:
            with open('.netrc', 'wb+') as f:
                f.write(res.content)
        else:
            log_error(f"Failed to download .netrc {res.status_code}")
    except Exception as e:
        log_error(f"NETRC_URL: {e}")
except Exception:
    pass

try:
    TORRENT_TIMEOUT = getConfig('TORRENT_TIMEOUT')
    if len(TORRENT_TIMEOUT) == 0:
        raise KeyError
    TORRENT_TIMEOUT = int(TORRENT_TIMEOUT)
except Exception:
    TORRENT_TIMEOUT = None

PORT = environ.get('PORT')
Popen([f"gunicorn web.wserver:app --bind 0.0.0.0:{PORT}"], shell=True)
srun(["last-randi", "-d", "--profile=."])
if not ospath.exists('.netrc'):
    srun(["touch", ".netrc"])
srun(["cp", ".netrc", "/root/.netrc"])
srun(["chmod", "600", ".netrc"])
trackers = check_output(["curl -Ns https://raw.githubusercontent.com/XIU2/TrackersListCollection/master/all.txt https://ngosang.github.io/trackerslist/trackers_all_http.txt https://newtrackon.com/api/all https://raw.githubusercontent.com/hezhijie0327/Trackerslist/main/trackerslist_tracker.txt | awk '$0' | tr '\n\n' ','"], shell=True).decode('utf-8').rstrip(',')
if TORRENT_TIMEOUT is not None:
    with open("a2c.conf", "a+") as a:
        a.write(f"bt-stop-timeout={TORRENT_TIMEOUT}\n")
with open("a2c.conf", "a+") as a:
    a.write(f"bt-tracker={trackers}")
CWD = getcwd()
srun(["extra-randi", f"--conf-path={CWD}/a2c.conf"])
alive = Popen(["python3", "alive.py"])
sleep(0.5)

Interval = []
DRIVES_NAMES = []
DRIVES_IDS = []
INDEX_URLS = []

try:
    if bool(getConfig('_____REMOVE_THIS_LINE_____')):
        log_error('The README.md file there to be read! Exiting now!')
        exit()
except Exception:
    pass

aria2 = ariaAPI(
    ariaClient(
        host="http://localhost",
        port=6800,
        secret="",
    )
)

def get_client():
    return qbClient(host="localhost", port=8090)

DOWNLOAD_DIR = None
BOT_TOKEN = None

download_dict_lock = Lock()
status_reply_dict_lock = Lock()
# Key: update.effective_chat.id
# Value: telegram.Message
status_reply_dict = {}
# Key: update.message.message_id
# Value: An object of Status
download_dict = {}


AUTHORIZED_CHATS = set()
SUDO_USERS = set()
AS_DOC_USERS = set()
AS_MEDIA_USERS = set()
EXTENSION_FILTER = set()
LEECH_DUMP = set()
LOG_CHNL = set()
WHITELIST = set()
BLACKLIST = set()

try:
    aid = getConfig('AUTHORIZED_CHATS')
    aid = aid.split()
    for _id in aid:
        AUTHORIZED_CHATS.add(int(_id.strip()))
except Exception:
    pass
try:
    aid = getConfig('SUDO_USERS')
    aid = aid.split()
    for _id in aid:
        SUDO_USERS.add(int(_id.strip()))
except Exception:
    pass
try:
    aid = getConfig('LEECH_DUMP')
    aid = aid.split()
    for _id in aid:
        LEECH_DUMP.add(int(_id.strip()))
except Exception:
    pass
try:
    aid = getConfig('LOG_CHNL')
    aid = aid.split()
    for _id in aid:
        LOG_CHNL.add(int(_id.strip()))
except Exception:
    pass
try:
    aid = getConfig('WHITELIST')
    aid = aid.split()
    for _id in aid:
        WHITELIST.add(int(_id.strip()))
except Exception:
    pass
try:
    fx = getConfig('EXTENSION_FILTER')
    if len(fx) > 0:
        fx = fx.split()
        for x in fx:
            EXTENSION_FILTER.add(x.strip().lower())
except Exception:
    pass
try:
    BOT_TOKEN = getConfig('BOT_TOKEN')
    parent_id = getConfig('GDRIVE_FOLDER_ID')
    DOWNLOAD_DIR = getConfig('DOWNLOAD_DIR')
    if not DOWNLOAD_DIR.endswith("/"):
        DOWNLOAD_DIR = f'{DOWNLOAD_DIR}/'
    DOWNLOAD_STATUS_UPDATE_INTERVAL = int(getConfig('DOWNLOAD_STATUS_UPDATE_INTERVAL'))
    OWNER_ID = int(getConfig('OWNER_ID'))
    AUTO_DELETE_MESSAGE_DURATION = int(getConfig('AUTO_DELETE_MESSAGE_DURATION'))
    TELEGRAM_API = getConfig('TELEGRAM_API')
    TELEGRAM_HASH = getConfig('TELEGRAM_HASH')
except Exception as e:
    log_error(str(e) + " One or more env variables missing! Exiting now")
    exit(1)

LOGGER.info("Generating BOT_SESSION_STRING")
app = Client(name='pyrogram', api_id=int(TELEGRAM_API), api_hash=TELEGRAM_HASH, bot_token=BOT_TOKEN, parse_mode=enums.ParseMode.HTML, no_updates=True)

try:
    HEROKU_API_KEY = getConfig('HEROKU_API_KEY')
except KeyError:
    HEROKU_API_KEY = None
try:
    HEROKU_APP_NAME = getConfig('HEROKU_APP_NAME')
except KeyError:
    HEROKU_APP_NAME = None    

try:
    BASE_URL = getConfig('BASE_URL_OF_BOT').rstrip("/")
    if len(BASE_URL) == 0:
        raise KeyError
except KeyError:
    if HEROKU_APP_NAME:
        BASE_URL = f"https://{HEROKU_APP_NAME}.herokuapp.com"
    else:    
        log_warning('BASE_URL_OF_BOT not provided!')
        BASE_URL = None

try:
    MEGA_KEY = getConfig('MEGA_API_KEY')
    if len(MEGA_KEY) == 0:
        raise KeyError
except Exception:
    MEGA_KEY = None
    LOGGER.info('MEGA_API_KEY not provided!')
try:
    MEGA_USERNAME = getConfig('MEGA_EMAIL_ID')
    MEGA_PASSWORD = getConfig('MEGA_PASSWORD')
    if len(MEGA_USERNAME) == 0 or len(MEGA_PASSWORD) == 0:
        raise KeyError
except KeyError:
    LOGGER.warning('MEGA Credentials not provided!')
    MEGA_USERNAME = None
    MEGA_PASSWORD = None    
try:
    DB_URI = getConfig('DATABASE_URL')
    if len(DB_URI) == 0:
        raise KeyError
except Exception:
    DB_URI = None
try:
    TG_SPLIT_SIZE = getConfig('TG_SPLIT_SIZE')
    if len(TG_SPLIT_SIZE) == 0 or int(TG_SPLIT_SIZE) > 2097151000:
        raise KeyError
    TG_SPLIT_SIZE = int(TG_SPLIT_SIZE)
except Exception:
    TG_SPLIT_SIZE = 2097151000
try:
    KEYWORD = getConfig('KEYWORD')
    if len(KEYWORD) == 0:
        raise KeyError
except KeyError:
    KEYWORD = None        

if KEYWORD is not None:
    STATUS_LIMIT = 2
else:
    try:
        STATUS_LIMIT = getConfig('STATUS_LIMIT')
        if len(STATUS_LIMIT) == 0:
            raise KeyError
        else:
            STATUS_LIMIT = int(STATUS_LIMIT)
    except KeyError:
        STATUS_LIMIT = None
try:
    UPTOBOX_TOKEN = getConfig('UPTOBOX_TOKEN')
    if len(UPTOBOX_TOKEN) == 0:
        raise KeyError
except Exception:
    UPTOBOX_TOKEN = None
try:
    INDEX_URL = getConfig('INDEX_URL').rstrip("/")
    if len(INDEX_URL) == 0:
        raise KeyError
    INDEX_URLS.append(INDEX_URL)
except Exception:
    INDEX_URL = None
    INDEX_URLS.append(None)
try:
    SEARCH_API_LINK = getConfig('SEARCH_API_LINK').rstrip("/")
    if len(SEARCH_API_LINK) == 0:
        raise KeyError
except Exception:
    SEARCH_API_LINK = None
try:
    SEARCH_LIMIT = getConfig('SEARCH_LIMIT')
    if len(SEARCH_LIMIT) == 0:
        raise KeyError
    SEARCH_LIMIT = int(SEARCH_LIMIT)
except Exception:
    SEARCH_LIMIT = 0
try:
    CMD_INDEX = getConfig('CMD_INDEX')
    if len(CMD_INDEX) == 0:
        raise KeyError
except Exception:
    CMD_INDEX = ''
try:
    TORRENT_DIRECT_LIMIT = getConfig('TORRENT_DIRECT_LIMIT')
    if len(TORRENT_DIRECT_LIMIT) == 0:
        raise KeyError
    TORRENT_DIRECT_LIMIT = float(TORRENT_DIRECT_LIMIT)
except Exception:
    TORRENT_DIRECT_LIMIT = None
try:
    CLONE_LIMIT = getConfig('CLONE_LIMIT')
    if len(CLONE_LIMIT) == 0:
        raise KeyError
    CLONE_LIMIT = float(CLONE_LIMIT)
except Exception:
    CLONE_LIMIT = None
try:
    MEGA_LIMIT = getConfig('MEGA_LIMIT')
    if len(MEGA_LIMIT) == 0:
        raise KeyError
    MEGA_LIMIT = float(MEGA_LIMIT)
except Exception:
    MEGA_LIMIT = None
try:
    STORAGE_THRESHOLD = getConfig('STORAGE_THRESHOLD')
    if len(STORAGE_THRESHOLD) == 0:
        raise KeyError
    STORAGE_THRESHOLD = float(STORAGE_THRESHOLD)
except Exception:
    STORAGE_THRESHOLD = None
try:
    ZIP_UNZIP_LIMIT = getConfig('ZIP_UNZIP_LIMIT')
    if len(ZIP_UNZIP_LIMIT) == 0:
        raise KeyError
    ZIP_UNZIP_LIMIT = float(ZIP_UNZIP_LIMIT)
except Exception:
    ZIP_UNZIP_LIMIT = None
try:
    BUTTON_FOUR_NAME = getConfig('BUTTON_FOUR_NAME')
    BUTTON_FOUR_URL = getConfig('BUTTON_FOUR_URL')
    if len(BUTTON_FOUR_NAME) == 0 or len(BUTTON_FOUR_URL) == 0:
        raise KeyError
except Exception:
    BUTTON_FOUR_NAME = None
    BUTTON_FOUR_URL = None
try:
    BUTTON_FIVE_NAME = getConfig('BUTTON_FIVE_NAME')
    BUTTON_FIVE_URL = getConfig('BUTTON_FIVE_URL')
    if len(BUTTON_FIVE_NAME) == 0 or len(BUTTON_FIVE_URL) == 0:
        raise KeyError
except Exception:
    BUTTON_FIVE_NAME = None
    BUTTON_FIVE_URL = None
try:
    BUTTON_SIX_NAME = getConfig('BUTTON_SIX_NAME')
    BUTTON_SIX_URL = getConfig('BUTTON_SIX_URL')
    if len(BUTTON_SIX_NAME) == 0 or len(BUTTON_SIX_URL) == 0:
        raise KeyError
except Exception:
    BUTTON_SIX_NAME = None
    BUTTON_SIX_URL = None
try:
    INCOMPLETE_TASK_NOTIFIER = getConfig('INCOMPLETE_TASK_NOTIFIER')
    INCOMPLETE_TASK_NOTIFIER = INCOMPLETE_TASK_NOTIFIER.lower() == 'true'
except Exception:
    INCOMPLETE_TASK_NOTIFIER = False
try:
    STOP_DUPLICATE = getConfig('STOP_DUPLICATE')
    STOP_DUPLICATE = STOP_DUPLICATE.lower() == 'true'
except Exception:
    STOP_DUPLICATE = False
try:
    VIEW_LINK = getConfig('VIEW_LINK')
    VIEW_LINK = VIEW_LINK.lower() == 'true'
except Exception:
    VIEW_LINK = False
try:
    IS_TEAM_DRIVE = getConfig('IS_TEAM_DRIVE')
    IS_TEAM_DRIVE = IS_TEAM_DRIVE.lower() == 'true'
except Exception:
    IS_TEAM_DRIVE = False
try:
    USE_SERVICE_ACCOUNTS = getConfig('USE_SERVICE_ACCOUNTS')
    USE_SERVICE_ACCOUNTS = USE_SERVICE_ACCOUNTS.lower() == 'true'
except Exception:
    USE_SERVICE_ACCOUNTS = False
try:
    WEB_PINCODE = getConfig('WEB_PINCODE')
    WEB_PINCODE = WEB_PINCODE.lower() == 'true'
except Exception:
    WEB_PINCODE = False
try:
    SHORTENER = getConfig('SHORTENER')
    SHORTENER_API = getConfig('SHORTENER_API')
    if len(SHORTENER) == 0 or len(SHORTENER_API) == 0:
        raise KeyError
except Exception:
    SHORTENER = None
    SHORTENER_API = None
try:
    IGNORE_PENDING_REQUESTS = getConfig("IGNORE_PENDING_REQUESTS")
    IGNORE_PENDING_REQUESTS = IGNORE_PENDING_REQUESTS.lower() == 'true'
except Exception:
    IGNORE_PENDING_REQUESTS = False
try:
    AS_DOCUMENT = getConfig('AS_DOCUMENT')
    AS_DOCUMENT = AS_DOCUMENT.lower() == 'true'
except Exception:
    AS_DOCUMENT = False
try:
    EQUAL_SPLITS = getConfig('EQUAL_SPLITS')
    EQUAL_SPLITS = EQUAL_SPLITS.lower() == 'true'
except Exception:
    EQUAL_SPLITS = False
try:
    QB_SEED = getConfig('QB_SEED')
    QB_SEED = QB_SEED.lower() == 'true'
except Exception:
    QB_SEED = False
try:
    CUSTOM_FILENAME = getConfig('CUSTOM_FILENAME')
    if len(CUSTOM_FILENAME) == 0:
        raise KeyError
except Exception:
    CUSTOM_FILENAME = None
try:
    GDTOT = getConfig('GDTOT')
    if len(GDTOT) == 0:
        raise KeyError
except Exception:
    GDTOT = None
try:
    APPDRIVE = getConfig('APPDRIVE')
    if len(APPDRIVE) == 0:
        raise KeyError
except Exception:
    APPDRIVE = None    
try:
    FOLDER_ID = getConfig('FOLDER_ID')
    SHARED_DRIVE_ID = getConfig("SHARED_DRIVE_ID")
    if len(FOLDER_ID) == 0 and len(SHARED_DRIVE_ID) == 0:
        raise KeyError
except Exception:
    FOLDER_ID = None
    SHARED_DRIVE_ID = None    
try:
    TOKEN_PICKLE_URL = getConfig('TOKEN_PICKLE_URL')
    if len(TOKEN_PICKLE_URL) == 0:
        raise KeyError
    try:
        res = rget(TOKEN_PICKLE_URL)
        if res.status_code == 200:
            with open('token.pickle', 'wb+') as f:
                f.write(res.content)
        else:
            log_error(f"Failed to download token.pickle, link got HTTP response: {res.status_code}")
    except Exception as e:
        log_error(f"TOKEN_PICKLE_URL: {e}")
except Exception:
    pass
try:
    ACCOUNTS_ZIP_URL = getConfig('ACCOUNTS_ZIP_URL')
    if len(ACCOUNTS_ZIP_URL) == 0:
        raise KeyError
    try:
        res = rget(ACCOUNTS_ZIP_URL)
        if res.status_code == 200:
            with open('accounts.zip', 'wb+') as f:
                f.write(res.content)
        else:
            log_error(f"Failed to download accounts.zip, link got HTTP response: {res.status_code}")
    except Exception as e:
        log_error(f"ACCOUNTS_ZIP_URL: {e}")
        raise KeyError
    srun(["unzip", "-q", "-o", "accounts.zip"])
    srun(["chmod", "-R", "777", "accounts"])
    osremove("accounts.zip")
except Exception:
    pass
try:
    MULTI_SEARCH_URL = getConfig('MULTI_SEARCH_URL')
    if len(MULTI_SEARCH_URL) == 0:
        raise KeyError
    try:
        res = rget(MULTI_SEARCH_URL)
        if res.status_code == 200:
            with open('drive_folder', 'wb+') as f:
                f.write(res.content)
        else:
            log_error(f"Failed to download drive_folder, link got HTTP response: {res.status_code}")
    except Exception as e:
        log_error(f"MULTI_SEARCH_URL: {e}")
except Exception:
    pass
try:
    YT_COOKIES_URL = getConfig('YT_COOKIES_URL')
    if len(YT_COOKIES_URL) == 0:
        raise KeyError
    try:
        res = rget(YT_COOKIES_URL)
        if res.status_code == 200:
            with open('cookies.txt', 'wb+') as f:
                f.write(res.content)
        else:
            log_error(f"Failed to download cookies.txt, link got HTTP response: {res.status_code}")
    except Exception as e:
        log_error(f"YT_COOKIES_URL: {e}")
except Exception:
    pass
try:
  CHAT_NAME = getConfig('CHAT_NAME')
  if len(CHAT_NAME) == 0:
    raise KeyError
except KeyError:
  CHAT_NAME = "Gᴀᴜᴛᴀᴍ'S Mɪʀʀᴏʀ"    
  
DRIVES_NAMES.append(CHAT_NAME)
DRIVES_IDS.append(parent_id)
if ospath.exists('drive_folder'):
    with open('drive_folder', 'r+') as f:
        lines = f.readlines()
        for line in lines:
            try:
                temp = line.strip().split()
                DRIVES_IDS.append(temp[1])
                DRIVES_NAMES.append(temp[0].replace("_", " "))
            except Exception:
                pass
            try:
                INDEX_URLS.append(temp[2])
            except Exception:
                INDEX_URLS.append(None)
try:
    SEARCH_PLUGINS = getConfig('SEARCH_PLUGINS')
    if len(SEARCH_PLUGINS) == 0:
        raise KeyError
    SEARCH_PLUGINS = jsnloads(SEARCH_PLUGINS)
except Exception:
    SEARCH_PLUGINS = None
try:
    FORCE_PM = getConfig('FORCE_PM')
    FORCE_PM = FORCE_PM.lower() == 'true'
except KeyError:
    FORCE_PM = False   
try:
    INFO_CHNL = getConfig('INFO_CHNL')
    if len(INFO_CHNL) == 0:
        raise KeyError
except KeyError:
    INFO_CHNL = 1    
try:
  FSUB_CHNL = getConfig('FSUB_CHNL')
  if len(FSUB_CHNL) == 0:
    raise KeyError
except KeyError:
  FSUB_CHNL = None
try:
    GROUP = int(getConfig('GROUP'))
    if GROUP == 0:
        raise KeyError
except KeyError:
    GROUP = None
try:
    MAX_TASKS = int(getConfig('MAX_TASKS'))
    if MAX_TASKS == 0:
        raise KeyError
except KeyError:
    MAX_TASKS = 7   

try:
    AUTO_DELETE_UPLOAD = int(getConfig('AUTO_DELETE_UPLOAD'))
    if AUTO_DELETE_UPLOAD == 0:
        raise KeyError
except KeyError:
    AUTO_DELETE_UPLOAD = -1

def aria2c_init():
    try:
        log_info("Initializing Aria2c")
        link = "https://linuxmint.com/torrents/lmde-5-cinnamon-64bit.iso.torrent"
        dire = DOWNLOAD_DIR.rstrip("/")
        aria2.add_uris([link], {'dir': dire})
        sleep(3)
        downloads = aria2.get_downloads()
        sleep(20)
        for download in downloads:
            aria2.remove([download], force=True, files=True)
    except Exception as e:
        log_error(f"Aria2c initializing error: {e}")
Thread(target=aria2c_init).start()

def mega_init():
    try:
        if MEGA_KEY is not None:
            # Start megasdkrest binary
            try:
                Popen(["megasdkrest", "--apikey", MEGA_KEY,"--port", "6090"])
            except FileNotFoundError:
                LOGGER.error("Please install Megasdkrest Binary, Exiting..")
                exit(0)
            except OSError:
                LOGGER.error("Megasdkrest Binary might have got damaged, Please Check ..")
                exit(0)    
            sleep(3)  # Wait for the mega server to start listening
            mega_client = MegaSdkRestClient('http://localhost:6090')
            if len(MEGA_USERNAME) > 0 and len(MEGA_PASSWORD) > 0:
                try:
                    mega_client.login(MEGA_USERNAME, MEGA_PASSWORD)
                    LOGGER.info("Mega Rest Initialized")
                    return True
                except mega_err.MegaSdkRestClientException as e:
                    LOGGER.error(e.message['message'])
                    exit(0)
        else:
            LOGGER.info("Mega API KEY provided but credentials not provided. Starting mega in anonymous mode!")
            sleep(1.5)
    except Exception as e:
        log_error(f"Megarest initializing error: {e}")
try:
    MEGAREST = getConfig('MEGAREST')
    MEGAREST = MEGAREST.lower() == 'true'
except KeyError:
    MEGAREST = False
if MEGAREST:                
    Thread(target=mega_init).start()        

# For Easy Configuration
try:
    MIRROR = getConfig('MIRROR')
    MIRROR = MIRROR.lower() == 'true'
except KeyError:
    MIRROR = True
try:
    LEECH = getConfig('LEECH')
    LEECH = LEECH.lower() == 'true'
except KeyError:
    LEECH = False
try:
    SEARCH = getConfig('SEARCH')
    SEARCH = SEARCH.lower() == 'true'
except KeyError:
    SEARCH = False
try:
    CLONE = getConfig('CLONE')
    CLONE = CLONE.lower() == 'true'
except KeyError:
    CLONE = True
try:
    YTDL = getConfig('YTDL')
    YTDL = YTDL.lower() == 'true'
except KeyError:
    YTDL = True
try:
    DEV = getConfig('DEV')
    DEV = DEV.lower() == 'true'
except KeyError:
    DEV = False
try:
    BL_URL = getConfig('BL_URL')
    if len(BL_URL) == 0:
        raise KeyError
    try:
        res = rget(BL_URL)
        if res.status_code == 200:
            with open('blocklist.txt', 'wb+') as f:
                f.write(res.content)
        else:
            log_error(f"Failed to download blocklist.txt, link got HTTP response: {res.status_code}")
    except Exception as e:
        log_error(f"BL_URL: {e}")
except KeyError:
    pass
if ospath.exists('blocklist.txt'):
    with open('blocklist.txt', 'r+') as f:
        lines = f.readlines()
        for line in lines:
            BLACKLIST.add(line.split()[0])    

updater = tgUpdater(token=BOT_TOKEN, request_kwargs={'read_timeout': 20, 'connect_timeout': 15})
bot = updater.bot
dispatcher = updater.dispatcher
job_queue = updater.job_queue
botname = bot.username
