from bot import AUTHORIZED_CHATS, SUDO_USERS,FSUB_CHNL, GROUP, INFO-CHNL, dispatcher, DB_URI, LEECH_LOG, LEECH_DUMP, LOG_CHNL
from bot.helper.telegram_helper.message_utils import sendMessage
from telegram.ext import CommandHandler
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.callbacks import Callback
from bot.helper.ext_utils.db_handler import DbManger


def authorize(update, context):
    reply_message = update.message.reply_to_message
    if len(context.args) == 1:
        user_id = int(context.args[0])
        if user_id in AUTHORIZED_CHATS:
            msg = 'User Already Authorized!'
        elif DB_URI is not None:
            msg = DbManger().user_auth(user_id)
            AUTHORIZED_CHATS.add(user_id)
        else:
            AUTHORIZED_CHATS.add(user_id)
            msg = 'User Authorized'
    elif reply_message:
        # Trying to authorize someone by replying
        user_id = reply_message.from_user.id
        if user_id in AUTHORIZED_CHATS:
            msg = 'User Already Authorized!'
        elif DB_URI is not None:
            msg = DbManger().user_auth(user_id)
            AUTHORIZED_CHATS.add(user_id)
        else:
            AUTHORIZED_CHATS.add(user_id)
            msg = 'User Authorized'
    else:
        # Trying to authorize a chat
        chat_id = update.effective_chat.id
        if chat_id in AUTHORIZED_CHATS:
            msg = 'Chat Already Authorized!'
        elif DB_URI is not None:
            msg = DbManger().user_auth(chat_id)
            AUTHORIZED_CHATS.add(chat_id)
        else:
            AUTHORIZED_CHATS.add(chat_id)
            msg = 'Chat Authorized'
    sendMessage(msg, context.bot, update.message)

def unauthorize(update, context):
    reply_message = update.message.reply_to_message
    if len(context.args) == 1:
        user_id = int(context.args[0])
        if user_id in AUTHORIZED_CHATS:
            if DB_URI is not None:
                msg = DbManger().user_unauth(user_id)
            else:
                msg = 'User Unauthorized'
            AUTHORIZED_CHATS.remove(user_id)
        else:
            msg = 'User Already Unauthorized!'
    elif reply_message:
        # Trying to authorize someone by replying
        user_id = reply_message.from_user.id
        if user_id in AUTHORIZED_CHATS:
            if DB_URI is not None:
                msg = DbManger().user_unauth(user_id)
            else:
                msg = 'User Unauthorized'
            AUTHORIZED_CHATS.remove(user_id)
        else:
            msg = 'User Already Unauthorized!'
    else:
        # Trying to unauthorize a chat
        chat_id = update.effective_chat.id
        if chat_id in AUTHORIZED_CHATS:
            if DB_URI is not None:
                msg = DbManger().user_unauth(chat_id)
            else:
                msg = 'Chat Unauthorized'
            AUTHORIZED_CHATS.remove(chat_id)
        else:
            msg = 'Chat Already Unauthorized!'

    sendMessage(msg, context.bot, update.message)

def addSudo(update, context):
    reply_message = update.message.reply_to_message
    if len(context.args) == 1:
        user_id = int(context.args[0])
        if user_id in SUDO_USERS:
            msg = 'Already Sudo!'
        elif DB_URI is not None:
            msg = DbManger().user_addsudo(user_id)
            SUDO_USERS.add(user_id)
        else:
            SUDO_USERS.add(user_id)
            msg = 'Promoted as Sudo'
    elif reply_message:
        # Trying to authorize someone by replying
        user_id = reply_message.from_user.id
        if user_id in SUDO_USERS:
            msg = 'Already Sudo!'
        elif DB_URI is not None:
            msg = DbManger().user_addsudo(user_id)
            SUDO_USERS.add(user_id)
        else:
            SUDO_USERS.add(user_id)
            msg = 'Promoted as Sudo'
    else:
        msg = "Give ID or Reply To message of whom you want to Promote."
    sendMessage(msg, context.bot, update.message)

def removeSudo(update, context):
    reply_message = update.message.reply_to_message
    if len(context.args) == 1:
        user_id = int(context.args[0])
        if user_id in SUDO_USERS:
            msg = DbManger().user_rmsudo(user_id) if DB_URI is not None else 'Demoted'
            SUDO_USERS.remove(user_id)
        else:
            msg = 'Not sudo user to demote!'
    elif reply_message:
        user_id = reply_message.from_user.id
        if user_id in SUDO_USERS:
            msg = DbManger().user_rmsudo(user_id) if DB_URI is not None else 'Demoted'
            SUDO_USERS.remove(user_id)
        else:
            msg = 'Not sudo user to demote!'
    else:
        msg = "Give ID or Reply To message of whom you want to remove from Sudo"
    sendMessage(msg, context.bot, update.message)

def leechauth(update, context):
    message_ = None
    message_ = update.message.text.split(' ')
    if len(message_) == 2:
        user_id = int(message_[1])
        if user_id in LEECH_DUMP:
            msg = 'This Chat Already Present In Leech Dump'
        elif DB_URI is not None:
            msg = DbManger().dump_auth(user_id)
            LEECH_DUMP.add(user_id)
        else:
            LEECH_DUMP.add(user_id)
            msg = 'Added To Leech Dump'
    else:
        msg = 'Send Chat ID With Command'        
    sendMessage(msg, context.bot, update.message)

def leechunauth(update, context):
    message_ = None
    message_ = update.message.text.split(' ')
    if len(message_) == 2:
        user_id = int(message_[1])
        if user_id in LEECH_DUMP:
            if DB_URI is not None:
                msg = DbManger().dump_unauth(user_id)
            else:
                msg = 'Removed Leech Dump'
            LEECH_DUMP.remove(user_id)
        else:
            msg = 'Leech Dump Already Removed!'
    else:
        msg = 'Send Chat ID With Command'        
    sendMessage(msg, context.bot, update.message)

def logauth(update, context):
    message_ = None
    message_ = update.message.text.split(' ')
    if len(message_) == 2:
        user_id = int(message_[1])
        if user_id in LOG_CHNL:
            msg = 'This Chat Already Present In Log Channel!'
        elif DB_URI is not None:
            msg = DbManger().chnl_auth(user_id)
            LOG_CHNL.add(user_id)
        else:
            LOG_CHNL.add(user_id)
            msg = 'Added To Log Channel'
    else:
        msg = 'Send Chat ID With Command'        
    sendMessage(msg, context.bot, update.message)

def logunauth(update, context):
    message_ = None
    message_ = update.message.text.split(' ')
    if len(message_) == 2:
        user_id = int(message_[1])
        if user_id in LOG_CHNL:
            if DB_URI is not None:
                msg = DbManger().chnl_unauth(user_id)
            else:
                msg = 'Removed Log Channel'
            LOG_CHNL.remove(user_id)
        else:
            msg = 'Log Channel Already Removed!'
    else:
        msg = 'Send Chat ID With Command'        
    sendMessage(msg, context.bot, update.message)


def sendAuthChats(update, context):
    user = '' + '\n'.join(f"<code>{uid}</code>" for uid in AUTHORIZED_CHATS)
    sudo = '' + '\n'.join(f"<code>{uid}</code>" for uid in SUDO_USERS)
    dump = '' + '\n'.join(f"<code>{uid}</code>" for uid in LEECH_DUMP)
    chnl = '' + '\n'.join(f"<code>{uid}</code>" for uid in LOG_CHNL)
    whtl = '' + '\n'.join(f"<code>{uid}</code>" for uid in WHITELIST)
    grp = f"<code>{GROUP}</code>"
    icnl = f"<code>{INFO_CHNL}</code>"
    fsub = f"<a href='{Callback.fsublink}'>{FSUB_CHNL}</a>"
    msg = ''
    if AUTHORIZED_CHATS: msg += f'<b><u>Authorized Chats:</u></b>\n{user}'
    if SUDO_USERS: msg += f'\n\n<b><u>Sudo Users:</u></b>\n{sudo}'
    if LEECH_DUMP: msg += f'\n\n<b><u>Leech Dumps:</u></b>\n{dump}'
    if LOG_CHNL: msg += f'\n\n<b><u>Log Channels:</u></b>\n{chnl}'
    if WHITELIST: msg += f'\n\n<b><u>Whitelist Chats:</u></b>\n{whtl}'
    if GROUP: msg += f'\n\n<b><u>Upload Group:</u></b>\n{grp}'
    if INFO_CHNL: msg += f'\n\n<b><u>Info Channel:</u></b>\n{icnl}'
    if FSUB_CHNL: msg += f'\n\n<b><u>ForceSub Channel:</u></b>\n{fsub}'
    sendMessage(msg, context.bot, update.message)


send_auth_handler = CommandHandler(command=BotCommands.AuthorizedUsersCommand, callback=sendAuthChats,
                                    filters=CustomFilters.owner_filter | CustomFilters.sudo_user, run_async=True)
authorize_handler = CommandHandler(command=BotCommands.AuthorizeCommand, callback=authorize,
                                    filters=CustomFilters.owner_filter | CustomFilters.sudo_user, run_async=True)
unauthorize_handler = CommandHandler(command=BotCommands.UnAuthorizeCommand, callback=unauthorize,
                                    filters=CustomFilters.owner_filter | CustomFilters.sudo_user, run_async=True)
addsudo_handler = CommandHandler(command=BotCommands.AddSudoCommand, callback=addSudo,
                                    filters=CustomFilters.owner_filter, run_async=True)
removesudo_handler = CommandHandler(command=BotCommands.RmSudoCommand, callback=removeSudo,
                                    filters=CustomFilters.owner_filter, run_async=True)
adddump_handler = CommandHandler(command=BotCommands.AddDumpCommand, callback=leechauth,
                                    filters=CustomFilters.owner_filter, run_async=True)
removedump_handler = CommandHandler(command=BotCommands.RmDumpCommand, callback=leechunauth,
                                    filters=CustomFilters.owner_filter, run_async=True)
addchnl_handler = CommandHandler(command=BotCommands.AddChnlCommand, callback=logauth,
                                    filters=CustomFilters.owner_filter, run_async=True)
removechnl_handler = CommandHandler(command=BotCommands.RmChnlCommand, callback=logunauth,
                                    filters=CustomFilters.owner_filter, run_async=True)

dispatcher.add_handler(send_auth_handler)
dispatcher.add_handler(authorize_handler)
dispatcher.add_handler(unauthorize_handler)
dispatcher.add_handler(addsudo_handler)
dispatcher.add_handler(removesudo_handler)

dispatcher.add_handler(adddump_handler)
dispatcher.add_handler(removedump_handler)
dispatcher.add_handler(addchnl_handler)
dispatcher.add_handler(removechnl_handler)
