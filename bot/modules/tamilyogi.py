from telegram.ext import CommandHandler
from telegram import Bot, Update
from bot import Interval, DOWNLOAD_DIR, DOWNLOAD_STATUS_UPDATE_INTERVAL, dispatcher, LOGGER
from bot.helper.ext_utils.bot_utils import setInterval
from bot.helper.telegram_helper.message_utils import update_all_messages, sendMessage, sendStatusMessage
from bot.helper.mirror_utils.download_utils.aria2_download import AriaDownloadHelper
from .mirror import MirrorListener
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.ext_utils.exceptions import DirectDownloadLinkException
from bs4 import BeautifulSoup
import requests


def _tamilyogi(bot: Bot, update, isTar=False):
    mssg = update.message.text
    message_args = mssg.split(' ')
    name_args = mssg.split('|')
    try:
        link = message_args[1]
    except IndexError:
        msg = f"/{BotCommands.TamilyogiCommand} [TamilYogi supported link] [quality] |[CustomName] to mirror with TamilYogi.\n\n"
        msg += "<b>Note: Quality and custom name are optional</b>\n\Qualities Are: 720, 360, 240."
        msg += "\n\nIf you want to use custom filename, enter it after |"
        msg += f"\n\nExample:\n<code>/{BotCommands.TamilyogiCommand} http://tamilyogi.best/the-tomorrow-war-2021-tamil-dubbed-movie-hd-720p-watch-online/ 720 | The Tomorrow War (2021)</code>\n\n"
        msg += "This file will be downloaded in 720p quality and it's name will be <b> The Tomorrow War (2021)</b>"
        sendMessage(msg, bot, update)
        return
    try:
      if "|" in mssg:
        mssg = mssg.split("|")
        qual = mssg[0].split(" ")[2]
        if qual == "":
          raise IndexError
      else:
        qual = message_args[2]
      if not qual:
        qual = "720"
    except IndexError:
      qual = "720"
    try:
      name = name_args[1]
    except IndexError:
      name = ""
    try:
      link = tamilyogidl(link, qual)
    except DirectDownloadLinkException as e:
      LOGGER.info(f'{link}: {e}')
      sendMessage(f"ERROR: {e}", bot, update)
      return
    reply_to = update.message.reply_to_message
    if reply_to is not None:
        tag = reply_to.from_user.username
    else:
        tag = None
    pswd = ""
    listener = MirrorListener(bot, update, pswd, isTar, tag)
    ariaDlManager = AriaDownloadHelper()
    ariaDlManager.start_listener()
    ariaDlManager.add_download(link, f'{DOWNLOAD_DIR}/{listener.uid}/', listener, name)
    sendStatusMessage(update, bot)
    if len(Interval) == 0:
        Interval.append(setInterval(DOWNLOAD_STATUS_UPDATE_INTERVAL, update_all_messages))


def tamilyogidl(link, quality):
  error, result = tamilyogi_dl(link, quality)
  if error:
    raise DirectDownloadLinkException(result)
  else:
    return result


def tamilyogi_dl(url, quality):
	quality = check_quality(quality)
	error = None
	if "tamilyogi" in url:
		if quality == "HD 720p" or quality == "NQ 360p" or quality == "LQ 240p":
			req = requests.get(url)
			if req.status_code == 200:
				soup = BeautifulSoup(req.content, 'html.parser')
				iframe = soup.find("iframe")
				if iframe:
					link  = tamilyogi_get_dl(iframe["src"])
					if link:
						if quality in link:
							link = link[quality]
						else:
							error =	"Unknown Error"
					else:
						error =	"Unknown Error"
				else:
					error = "Unknown URL"
			else:
				error = f"There's Some Issue With Your URL\nStatus Code:- {req.status_code}\nReason:- {req.reason}"
		else:
			error = "Wrong Quality"
	else:
		error = "Please Send Tamilyogi Link"

	if error:
		return True, error
	else:
		return False, link


def check_quality(quality):
	if quality == "720p" or quality == "720" or quality == "HD 720p":
		return "HD 720p"
	elif quality == "360p" or quality == "360" or quality == "NQ 360p":
		return "NQ 360p"
	elif quality == "240p" or quality == "240" or quality == "LQ 240p":
		return "LQ 240p"
	else:
		return quality


def tamilyogi_get_dl(url):
	headers_mobile = { 'User-Agent' : 'Mozilla/5.0 (iPhone; CPU iPhone OS 9_1 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13B137 Safari/601.1'}
	req = requests.get(url, headers=headers_mobile)
	soup = BeautifulSoup(req.content, 'html.parser')
	link = {}
	for a in soup.findAll('a', href=True):
		link[a.text] = a["href"].replace(" ","%C2%A0")
	return link


def tamilyogiTar(update, context):
    _tamilyogi(context.bot, update, True)


def tamilyogi(update, context):
    _tamilyogi(context.bot, update)


mirror_handler = CommandHandler(BotCommands.TamilyogiCommand, tamilyogi,
                                filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
tar_mirror_handler = CommandHandler(BotCommands.TarTamilyogiCommand, tamilyogiTar,
                                    filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
dispatcher.add_handler(mirror_handler)
dispatcher.add_handler(tar_mirror_handler)
