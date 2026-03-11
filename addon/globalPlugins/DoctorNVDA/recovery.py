# recovery.py

import os
import shutil
import datetime
import ui
import core
import tones
import addonHandler
from globalVars import appArgs

addonHandler.initTranslation()
try:
	_ = addonHandler.getTranslation()
except:
	def _(x): return x

# Determine NVDA version to select appropriate recovery items
try:
	from buildVersion import version_year, version_major
	# NVDA 2026.1 or later uses different set of core config files
	if version_year > 2026 or (version_year == 2026 and version_major >= 1):
		RECOVERY_ITEMS = [
			'profiles',
			'speechDicts',
			'addonsState.pickle',
			'gestures.ini',
			'mathcat.yaml',
			'nvda.ini',
			'updateCheckState.pickle'
		]
	else:
		# NVDA 2025.x and earlier
		RECOVERY_ITEMS = [
			'profiles',
			'speechDicts',
			'gestures.ini',
			'guiState.ini',
			'nvda.ini',
			'nvda3208.pickle',
			'profileTriggers.ini',
			'updateCheckState.pickle'
		]
except ImportError:
	# Fallback to a safe minimal set if version cannot be determined
	RECOVERY_ITEMS = [
		'profiles',
		'speechDicts',
		'gestures.ini',
		'nvda.ini',
		'updateCheckState.pickle'
	]

def get_recovery_base_path():
	path = os.path.join(appArgs.configPath, "ChaiChaimee", "DoctorNVDA", "Recovery")
	if not os.path.exists(path):
		os.makedirs(path)
	return path

def _merge_directory(src, dst):
	"""Copy files from src to dst recursively, overwriting existing files,
	but never deleting files in dst that are not present in src."""
	if not os.path.exists(dst):
		os.makedirs(dst)
	for root, dirs, files in os.walk(src):
		rel_path = os.path.relpath(root, src)
		dest_dir = os.path.join(dst, rel_path) if rel_path != '.' else dst
		if not os.path.exists(dest_dir):
			os.makedirs(dest_dir)
		for file in files:
			src_file = os.path.join(root, file)
			dst_file = os.path.join(dest_dir, file)
			shutil.copy2(src_file, dst_file)

def create_recovery():
	now = datetime.datetime.now().strftime("%d%B%Y_%H-%M")
	dest_base = get_recovery_base_path()
	dest = os.path.join(dest_base, now)
	try:
		os.makedirs(dest, exist_ok=True)
		for item in RECOVERY_ITEMS:
			src = os.path.join(appArgs.configPath, item)
			dst = os.path.join(dest, item)
			if os.path.isdir(src):
				# Use dirs_exist_ok=True to merge into existing folder (if any)
				shutil.copytree(src, dst, dirs_exist_ok=True)
			elif os.path.isfile(src):
				shutil.copy2(src, dst)
			# If doesn't exist, skip
		tones.beep(1000, 150)  # Success Beep
		ui.message(_("Recovery created: {n}").format(n=now))
	except Exception as e:
		ui.message(_("Create recovery failed"))

def get_recovery_list():
	base = get_recovery_base_path()
	if not os.path.exists(base): return []
	dirs = [d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d))]
	dirs.sort(reverse=True)  # Most recent first
	return dirs

def restore_from(folder_name):
	source = os.path.join(get_recovery_base_path(), folder_name)
	if not os.path.exists(source):
		return

	tones.beep(800, 200)
	try:
		# Restore only the items that were backed up, without deleting other files that may exist in destination
		for item in RECOVERY_ITEMS:
			src_path = os.path.join(source, item)
			dst_path = os.path.join(appArgs.configPath, item)
			if not os.path.exists(src_path):
				continue  # Skip if not in recovery

			if os.path.isdir(src_path):
				# Use merge instead of deleting and copying the whole folder
				_merge_directory(src_path, dst_path)
			else:
				# If file, copy over (existing file will be replaced)
				shutil.copy2(src_path, dst_path)

		core.callLater(500, core.restart)
		ui.message(_("Restore completed, restarting NVDA..."))
	except Exception as e:
		ui.message(_("Restore failed"))

def remove_recovery(folder_name):
	path = os.path.join(get_recovery_base_path(), folder_name)
	if os.path.exists(path):
		shutil.rmtree(path)
		ui.message(_("Removed: {n}").format(n=folder_name))

def remove_all_recoveries():
	path = get_recovery_base_path()
	if os.path.exists(path):
		shutil.rmtree(path)
		os.makedirs(path)
		ui.message(_("All recoveries removed"))