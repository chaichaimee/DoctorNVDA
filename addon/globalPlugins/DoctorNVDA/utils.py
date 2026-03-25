# utils.py
import os
import subprocess
import addonHandler
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
		except Exception as e:
			import logHandler
			log = logHandler.getLogger()
			log.exception("Error opening user config folder")
			ui.message(_("Failed to open user config folder"))
	else:
		ui.message(_("User config folder not found"))