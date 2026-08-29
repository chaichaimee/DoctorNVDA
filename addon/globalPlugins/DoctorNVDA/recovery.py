# recovery.py

import os
import shutil
import tempfile
import threading
import datetime
import ui
import core
import config
import tones
import wx
import addonHandler
import logHandler
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

def _move_directory_contents(staged_src, dst):
	"""Move every file from staged_src into dst using os.replace instead
	of copying bytes again. staged_src always lives on the same
	filesystem as dst (both are under appArgs.configPath), so each
	os.replace is an atomic, near-instant directory-entry swap rather
	than a byte-for-byte copy. This is what lets the final apply step
	run on the main thread without noticeably blocking it, even for a
	large profiles or speechDicts folder: the expensive copying already
	happened once, on the worker thread, into the staging area."""
	if not os.path.exists(dst):
		os.makedirs(dst)
	for root, dirs, files in os.walk(staged_src):
		rel_path = os.path.relpath(root, staged_src)
		dest_dir = os.path.join(dst, rel_path) if rel_path != '.' else dst
		if not os.path.exists(dest_dir):
			os.makedirs(dest_dir)
		for file in files:
			os.replace(os.path.join(root, file), os.path.join(dest_dir, file))

def create_recovery():
	"""Copy configuration files into a timestamped recovery folder on a
	worker thread so large profiles do not stall the NVDA main event loop.

	config.conf.save() is called synchronously on the main thread first,
	so any pending in-memory changes are flushed to disk before the
	worker starts reading. Without this, the worker could read nvda.ini
	or a profile file mid-write if NVDA's config manager happens to flush
	changes at the same moment, producing a corrupted backup. This only
	reads from the live config and writes into a brand new recovery
	folder, so it never competes with NVDA's own config saves."""
	try:
		config.conf.save()
	except Exception as e:
		# config.conf.save() can fail for several unrelated reasons
		# (validation errors, a read-only profile, etc.); none of those
		# should block making a recovery from whatever is already on
		# disk, so this is logged and not fatal.
		logHandler.log.error("Could not flush configuration before creating recovery: %s", e)

	def worker():
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
		except OSError as e:
			logHandler.log.error("Create recovery failed: %s", e)
			wx.CallAfter(ui.message, _("Create recovery failed"))
			return

		wx.CallAfter(tones.beep, 1000, 150)
		wx.CallAfter(ui.message, _("Recovery created: {n}").format(n=now))

	threading.Thread(target=worker, daemon=True).start()

def get_recovery_list():
	base = get_recovery_base_path()
	if not os.path.exists(base): return []
	dirs = [d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d))]
	dirs.sort(reverse=True)  # Most recent first
	return dirs

def _cleanup_tmp_files(target_dir):
	"""Remove all .tmp files from the target directory (root level only)
	to prevent NVDA from reading stale temporary configs during restore."""
	if not os.path.isdir(target_dir):
		return
	try:
		all_entries = os.listdir(target_dir)
	except OSError as e:
		logHandler.log.error("Unable to list directory for tmp cleanup: %s", e)
		return

	tmp_deleted = 0
	for entry in all_entries:
		full_path = os.path.join(target_dir, entry)
		if os.path.isfile(full_path) and entry.lower().endswith(".tmp"):
			try:
				os.remove(full_path)
				tmp_deleted += 1
			except OSError as e:
				logHandler.log.exception("Failed to delete tmp file %s", full_path)
	if tmp_deleted:
		logHandler.log.info("Cleaned up %d .tmp file(s) before restore", tmp_deleted)

def _apply_staged_restore(staging_dir):
	"""Runs on NVDA's main thread. Only cheap os.replace() renames happen
	here (see _move_directory_contents), never a byte-copy of profiles or
	speechDicts, so this cannot noticeably block the main event pump even
	for a large recovery set. Because it runs on the same thread NVDA's
	own config manager uses for its atomic saves, it also cannot
	interleave with an in-progress save the way a background thread
	could."""
	try:
		_cleanup_tmp_files(appArgs.configPath)
		for item in os.listdir(staging_dir):
			staged_path = os.path.join(staging_dir, item)
			dst_path = os.path.join(appArgs.configPath, item)
			if os.path.isdir(staged_path):
				_move_directory_contents(staged_path, dst_path)
			else:
				os.replace(staged_path, dst_path)
	except OSError as e:
		logHandler.log.error("Restore failed: %s", e)
		ui.message(_("Restore failed"))
		return
	finally:
		shutil.rmtree(staging_dir, ignore_errors=True)

	# NVDA's own exit sequence saves the in-memory configuration back to
	# nvda.ini when saveConfigurationOnExit is enabled. Without disabling
	# it here, that save would run during core.restart()'s shutdown and
	# silently overwrite the nvda.ini/addonsState.pickle files just
	# restored above, making the restore a no-op. This flag only needs to
	# be turned off for this one exit; the fresh NVDA process started by
	# core.restart() reloads it from the just-restored nvda.ini anyway.
	try:
		config.conf["general"]["saveConfigurationOnExit"] = False
	except Exception as e:
		logHandler.log.error("Could not disable save-on-exit before restore restart: %s", e)

	ui.message(_("Restore completed, restarting NVDA..."))
	core.callLater(500, core.restart)

def restore_from(folder_name):
	"""Restore configuration files from a recovery folder.

	The expensive part (copying potentially large profiles/speechDicts
	out of the recovery folder) runs on a background worker thread into
	a private staging directory under appArgs.configPath, so it never
	touches NVDA's live config and cannot block the main event pump long
	enough to trip the Watchdog. Only the final, cheap step of putting
	those already-copied files into place (see _apply_staged_restore) is
	marshaled onto the main thread via wx.CallAfter, immediately before
	core.restart(); since that step is just renames rather than copies,
	it finishes fast enough not to freeze the UI while still guaranteeing
	it can't race NVDA's own config auto-save.
	"""
	source = os.path.join(get_recovery_base_path(), folder_name)
	if not os.path.exists(source):
		return

	def worker():
		staging_dir = tempfile.mkdtemp(prefix="restoreStaging_", dir=appArgs.configPath)
		try:
			for item in RECOVERY_ITEMS:
				src_path = os.path.join(source, item)
				if not os.path.exists(src_path):
					continue  # Skip if not in recovery
				staged_path = os.path.join(staging_dir, item)
				if os.path.isdir(src_path):
					shutil.copytree(src_path, staged_path)
				else:
					shutil.copy2(src_path, staged_path)
		except OSError as e:
			logHandler.log.error("Restore staging failed: %s", e)
			shutil.rmtree(staging_dir, ignore_errors=True)
			wx.CallAfter(ui.message, _("Restore failed"))
			return

		wx.CallAfter(tones.beep, 800, 200)
		wx.CallAfter(_apply_staged_restore, staging_dir)

	threading.Thread(target=worker, daemon=True).start()

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
