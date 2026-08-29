# cleanup.py

import os
import shutil
import threading
import addonHandler
import core
import ui
import tones
import logHandler
import wx
from globalVars import appArgs

addonHandler.initTranslation()
try:
	_ = addonHandler.getTranslation()
except:
	def _(x): return x


def _find_pycache_dirs(search_paths):
	"""Yield full paths of __pycache__ directories under search_paths."""
	for root_path in search_paths:
		if not os.path.isdir(root_path):
			continue
		for dirpath, dirnames, _ in os.walk(root_path, topdown=True):
			if '__pycache__' in dirnames:
				cache_path = os.path.join(dirpath, '__pycache__')
				yield cache_path
				dirnames.remove('__pycache__')  # don't recurse into it


def _empty_directory(dir_path):
	"""Remove all files and subdirectories inside dir_path without removing the directory itself.
	Returns number of files removed and total freed bytes (approximate).
	"""
	freed_bytes = 0
	removed_count = 0
	entries = os.listdir(dir_path)
	for entry in entries:
		full_path = os.path.join(dir_path, entry)
		try:
			if os.path.isfile(full_path) or os.path.islink(full_path):
				freed_bytes += os.path.getsize(full_path)
				os.unlink(full_path)
				removed_count += 1
			elif os.path.isdir(full_path):
				shutil.rmtree(full_path, ignore_errors=False)
				removed_count += 1
		except OSError as e:
			logHandler.log.error("Failed to delete %s: %s", full_path, e)
	return removed_count, freed_bytes


def _find_temp_files(search_paths):
	"""Walk search_paths and yield paths of .tmp files (non-recursive by default)."""
	for root_path in search_paths:
		if not os.path.isdir(root_path):
			continue
		for dirpath, dirnames, filenames in os.walk(root_path, topdown=True):
			for fname in filenames:
				if fname.lower().endswith('.tmp'):
					yield os.path.join(dirpath, fname)
			if '__pycache__' in dirnames:
				dirnames.remove('__pycache__')


def _find_delete_files(search_paths):
	"""Walk search_paths and yield paths of .delete files."""
	for root_path in search_paths:
		if not os.path.isdir(root_path):
			continue
		for dirpath, dirnames, filenames in os.walk(root_path, topdown=True):
			for fname in filenames:
				if fname.lower().endswith('.delete'):
					yield os.path.join(dirpath, fname)
			if '__pycache__' in dirnames:
				dirnames.remove('__pycache__')


def run_cache_cleanup():
	"""Clean __pycache__ folders, then restart NVDA immediately to finish applying the cleanup."""
	tones.beep(600, 50)

	addons = addonHandler.getAvailableAddons()
	self_name = None
	try:
		self_name = addonHandler.getCodeAddon().manifest['name']
	except Exception:
		self_name = "DoctorNVDA"

	scan_paths = []
	for addon in addons:
		if addon.name == self_name:
			continue
		if os.path.isdir(addon.path):
			scan_paths.append(addon.path)

	scratchpad = os.path.join(appArgs.configPath, "scratchpad")
	if os.path.isdir(scratchpad):
		scan_paths.append(scratchpad)

	if not scan_paths:
		core.callLater(0, ui.message, _("No add-on directories found to clean."))
		return

	def worker():
		try:
			total_files = 0
			total_bytes = 0
			dirs_found = 0
			for cache_dir in _find_pycache_dirs(scan_paths):
				dirs_found += 1
				files, bytes_freed = _empty_directory(cache_dir)
				total_files += files
				total_bytes += bytes_freed
				logHandler.log.info("Cleaned %d file(s) from %s (%d bytes)", files, cache_dir, bytes_freed)

			if dirs_found == 0:
				wx.CallAfter(ui.message, _("No __pycache__ folders found. Everything is clean."))
				wx.CallAfter(tones.beep, 1000, 100)
				return

			msg = _("Cleaned {files} file(s) in {dirs} cache folder(s). Freed {size} bytes. Restarting NVDA now.").format(
				files=total_files, dirs=dirs_found, size=total_bytes
			)
			wx.CallAfter(ui.message, msg)
			wx.CallAfter(tones.beep, 1000, 150)
			wx.CallAfter(core.callLater, 1500, core.restart)
		except Exception as e:
			logHandler.log.exception("Cache cleanup failed")
			wx.CallAfter(ui.message, _("Cache cleanup encountered an error. Check NVDA log."))
			wx.CallAfter(tones.beep, 200, 300)

	t = threading.Thread(target=worker, daemon=True)
	t.start()


def _delete_temp_files_on_main_thread(temp_paths):
	"""Runs on NVDA's main thread. Some of temp_paths live directly under
	appArgs.configPath (e.g. nvda.ini.tmp) and are the staging files
	NVDA's config manager uses for its own atomic saves on the main
	thread; deleting them from a background thread can race an in-progress
	save and raise OSError, or leave the save half-applied. Deleting them
	here instead guarantees the deletion cannot interleave with any other
	main-thread config activity, and restarting right afterward keeps the
	brief blocking window unnoticeable to the user."""
	deleted_files = 0
	freed_bytes = 0
	for tmp_path in temp_paths:
		try:
			freed_bytes += os.path.getsize(tmp_path)
			os.remove(tmp_path)
			deleted_files += 1
			logHandler.log.info("Deleted temp/delete file: %s", tmp_path)
		except OSError as e:
			logHandler.log.error("Failed to delete temp/delete file %s: %s", tmp_path, e)

	if deleted_files == 0:
		ui.message(_("No temporary or .delete NVDA files found."))
		tones.beep(1000, 100)
		return

	msg = _("Deleted {count} temporary/.delete file(s). Freed {size} bytes. Restarting NVDA now.").format(
		count=deleted_files, size=freed_bytes
	)
	ui.message(msg)
	tones.beep(1000, 150)
	core.callLater(1500, core.restart)


def run_temp_cleanup():
	"""Remove .tmp and .delete files from userConfig and addon folders, then restart NVDA immediately.

	Finding the files is read-only and stays on a worker thread so a large
	scan does not stall the main event loop. Actually deleting them is
	marshaled onto the main thread (see _delete_temp_files_on_main_thread)
	since some of those files are NVDA's own config auto-save staging
	files."""
	tones.beep(600, 50)

	scan_roots = [appArgs.configPath]
	addons = addonHandler.getAvailableAddons()
	for addon in addons:
		if os.path.isdir(addon.path):
			scan_roots.append(addon.path)
	scratchpad = os.path.join(appArgs.configPath, "scratchpad")
	if os.path.isdir(scratchpad):
		scan_roots.append(scratchpad)

	def worker():
		try:
			temp_paths = list(_find_temp_files(scan_roots)) + list(_find_delete_files(scan_roots))
		except OSError as e:
			logHandler.log.error("Temp file scan failed: %s", e)
			wx.CallAfter(ui.message, _("Temp file cleanup encountered an error. Check NVDA log."))
			wx.CallAfter(tones.beep, 200, 300)
			return

		if not temp_paths:
			wx.CallAfter(ui.message, _("No temporary or .delete NVDA files found."))
			wx.CallAfter(tones.beep, 1000, 100)
			return

		wx.CallAfter(_delete_temp_files_on_main_thread, temp_paths)

	t = threading.Thread(target=worker, daemon=True)
	t.start()
