# utils.py

import os
import subprocess
import addonHandler
import ui
import logHandler
from globalVars import appArgs

addonHandler.initTranslation()
try:
	_ = addonHandler.getTranslation()
except:
	def _(x): return x

def open_user_config():
	"""Open the NVDA user configuration directory in File Explorer."""
	path = appArgs.configPath
	if os.path.isdir(path):
		try:
			os.startfile(path)
		except OSError:
			# logHandler has no getLogger() function; the module-level
			# logger object is logHandler.log itself.
			logHandler.log.exception("Error opening user config folder")
			ui.message(_("Failed to open user config folder"))
	else:
		ui.message(_("User config folder not found"))
