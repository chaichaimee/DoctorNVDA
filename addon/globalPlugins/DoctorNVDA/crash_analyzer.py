# crash_analyzer.py

import os
import re
import threading
import logging
import tempfile
import wx
import ui
import tones
import addonHandler
import logHandler
from globalVars import appArgs

addonHandler.initTranslation()
try:
	_ = addonHandler.getTranslation()
except:
	def _(x): return x

_LOG_ENTRY_RE = re.compile(r"^[A-Z]+ - .+\(\d{2}:\d{2}:\d{2}\.\d+\)")
_TRACEBACK_START = "Traceback (most recent call last):"
_FRAME_RE = re.compile(r'File "([^"]+)", line (\d+)')
_ADDON_PATH_RE = re.compile(r"[\\/]addons[\\/]([^\\/]+)[\\/]")

# Same heuristic used by the LogViewerPlugin add-on already present in this
# environment to distinguish a real crash from a normal restart: a crash
# leaves one of these markers on the very last line of nvda-old.log.
_CRASH_INDICATORS = ("Traceback", "ERROR - unhandled exception", "CRASH")


def _state_file_path():
	return os.path.join(appArgs.configPath, "ChaiChaimee", "DoctorNVDA", "crash_analyzer_state.txt")


def _load_state():
	"""Read the plain-text state file (simple 'key: value' lines) rather
	than JSON, so it stays readable if a user opens it directly."""
	path = _state_file_path()
	if not os.path.exists(path):
		return None
	state = {}
	try:
		with open(path, "r", encoding="utf-8") as f:
			for line in f:
				line = line.strip()
				if not line or ":" not in line:
					continue
				key, _sep, value = line.partition(":")
				key = key.strip()
				value = value.strip()
				try:
					state[key] = float(value) if "." in value else int(value)
				except ValueError:
					state[key] = value
	except OSError:
		return None
	return state


def _save_state(state):
	"""Write the state as simple 'key: value' lines instead of JSON, so
	the file stays readable if a user opens it directly."""
	path = _state_file_path()
	directory = os.path.dirname(path)
	if not os.path.exists(directory):
		os.makedirs(directory)
	try:
		with open(path, "w", encoding="utf-8") as f:
			for key, value in state.items():
				f.write(f"{key}: {value}\n")
	except OSError as e:
		logHandler.log.error("Failed to save crash analyzer state: %s", e)


def _get_report_dir():
	path = os.path.join(appArgs.configPath, "ChaiChaimee", "DoctorNVDA", "Reports")
	if not os.path.exists(path):
		os.makedirs(path)
	return path


def _report_file_path():
	return os.path.join(_get_report_dir(), "CrashReport.txt")


def _iter_log_handlers():
	"""Yield every handler that could plausibly hold NVDA's log file: the
	ones attached directly to logHandler.log, any attached to its parent
	loggers via the standard logging propagation chain, and finally the
	root logger's own handlers. NVDA does not always attach its file
	handler to the same logger object across versions/configurations, so
	checking logHandler.log.handlers alone is not reliable.

	Must be called from NVDA's main thread only: these are the standard
	library logging module's own handler lists, and NVDA's main thread
	can mutate/rotate them at any time. Iterating them concurrently from
	a background thread can raise "RuntimeError: list changed size during
	iteration"."""
	seen_ids = set()

	logger = logHandler.log
	while logger is not None:
		for handler in logger.handlers:
			if id(handler) not in seen_ids:
				seen_ids.add(id(handler))
				yield handler
		logger = logger.parent

	for handler in logging.root.handlers:
		if id(handler) not in seen_ids:
			seen_ids.add(id(handler))
			yield handler


def _get_log_file_path():
	"""Resolve the active nvda.log path. Logging handlers are checked
	first since they reflect a custom -f command line path if one was
	given, then a well-known default is used as a fallback: NVDA writes
	its live log to nvda.log directly under the Windows temp directory
	(confirmed against a known-working reference add-on that reads NVDA's
	own log files: logViewer.txt uses tempfile.gettempdir()).

	Must be called from NVDA's main thread only (see _iter_log_handlers).
	Callers should resolve this once on the main thread and pass the
	returned string into any background worker thread, rather than
	calling this function from the worker itself."""
	for handler in _iter_log_handlers():
		base_filename = getattr(handler, "baseFilename", None)
		if base_filename:
			return base_filename

		stream = getattr(handler, "stream", None)
		stream_name = getattr(stream, "name", None)
		if stream_name and os.path.isfile(stream_name):
			return stream_name

	default_path = os.path.join(tempfile.gettempdir(), "nvda.log")
	if os.path.isfile(default_path):
		return default_path

	logHandler.log.error(
		"Crash analyzer could not resolve the nvda.log path from any known "
		"handler or the default temp directory location."
	)
	return None


def _old_log_path(current_log_path):
	"""Path to the previous session's log. NVDA renames nvda.log to
	nvda-old.log in the same directory when it starts a fresh log, so a
	freeze or crash traceback that ended a session is usually found at
	the end of nvda-old.log, not in the current (nearly empty) nvda.log."""
	directory = os.path.dirname(current_log_path) if current_log_path else tempfile.gettempdir()
	return os.path.join(directory, "nvda-old.log")


def _iter_traceback_blocks(file_obj):
	"""Stream a log file one line at a time and yield each traceback block
	as it completes, so the full log is never held in memory as a single
	string. A block starts at 'Traceback (most recent call last):' and
	ends at the next recognizable log entry line, or at end of file;
	only the lines belonging to the current block are ever buffered."""
	block_lines = []
	in_traceback = False
	for line in file_obj:
		if in_traceback and _LOG_ENTRY_RE.match(line):
			yield "".join(block_lines)
			block_lines = []
			in_traceback = False
			# The log entry line that closed the block could itself be the
			# start of an immediately adjacent traceback.
			if _TRACEBACK_START in line:
				in_traceback = True
				block_lines.append(line)
			continue

		if not in_traceback and _TRACEBACK_START in line:
			in_traceback = True
			block_lines = [line]
			continue

		if in_traceback:
			block_lines.append(line)

	if in_traceback and block_lines:
		yield "".join(block_lines)


def _collect_addon_issues_from_blocks(blocks):
	issues = []
	for block in blocks:
		frames = _FRAME_RE.findall(block)
		addon_frame = None
		for file_path, line_no in reversed(frames):
			match = _ADDON_PATH_RE.search(file_path)
			if match:
				addon_frame = (match.group(1), file_path, line_no)
				break
		if not addon_frame:
			continue

		addon_internal, file_path, line_no = addon_frame
		summary_lines = [ln for ln in block.strip().splitlines() if ln.strip()]
		exception_summary = summary_lines[-1].strip() if summary_lines else _("Unknown error")
		issues.append({
			"addon": addon_internal,
			"line": line_no,
			"error": exception_summary,
			"file": os.path.basename(file_path),
		})
	return issues


def _addon_display_name(internal_name):
	for addon in addonHandler.getAvailableAddons():
		if addon.name == internal_name:
			return addon.manifest.get("name", internal_name)
	return internal_name


def _build_plain_language_report(issues):
	"""Plain, header-free report: just the add-on, file, line, and cause
	for each issue found, so it reads easily for a non-technical user."""
	entries = []
	for issue in issues:
		display_name = _addon_display_name(issue["addon"])
		entries.append("\n".join([
			_("add-on: {addon}").format(addon=display_name),
			_("file: {file}").format(file=issue["file"]),
			_("line: {line}").format(line=issue["line"]),
			_("error: {error}").format(error=issue["error"]),
		]))
	return "\n\n".join(entries)


def _clear_previous_report():
	path = _report_file_path()
	if os.path.exists(path):
		try:
			os.remove(path)
		except OSError as e:
			logHandler.log.error("Failed to clear previous crash report: %s", e)


def _write_report(content):
	path = _report_file_path()
	try:
		with open(path, "w", encoding="utf-8") as f:
			f.write(content)
		return path
	except OSError as e:
		logHandler.log.error("Failed to write crash report: %s", e)
		return None


def _open_report(path):
	try:
		os.startfile(path)
	except OSError as e:
		logHandler.log.error("Failed to open crash report: %s", e)


def _old_log_indicates_crash(old_log_path):
	"""True only if the previous session actually crashed/froze and NVDA
	restarted itself, not for a normal restart (first Windows login, or
	NVDA/DoctorNVDA restarting cleanly). Checks only the last non-empty
	line of nvda-old.log, matching the LogViewerPlugin add-on's own crash
	detection so the two stay consistent in this environment. Reads the
	file line-by-line rather than with readlines(), so only the current
	candidate last line is ever held in memory instead of the whole file."""
	last_line = ""
	try:
		with open(old_log_path, "r", encoding="utf-8", errors="replace") as f:
			for line in f:
				stripped = line.strip()
				if stripped:
					last_line = stripped
	except OSError:
		return False
	if not last_line:
		return False
	return any(indicator in last_line for indicator in _CRASH_INDICATORS)


def analyze_and_report():
	"""Run once at NVDA startup, on the main thread (invoked via
	core.callLater). A report is opened automatically only when the
	previous session actually crashed and NVDA restarted itself (see
	_old_log_indicates_crash). A normal restart never opens a report on
	its own; that only happens when the user explicitly runs "Crash Log
	Analyzer" from the menu."""
	# Resolve the log path here, on the main thread this function is
	# invoked on, and hand only the resulting string to the worker below.
	# _get_log_file_path()/_iter_log_handlers() touch the standard
	# library logging module's handler lists, which are not safe to
	# iterate concurrently with NVDA's main thread from a worker thread.
	log_path = _get_log_file_path()
	old_log_path = _old_log_path(log_path)

	def worker():
		state = _load_state() or {}

		if not os.path.isfile(old_log_path):
			return

		try:
			old_mtime = os.path.getmtime(old_log_path)
			old_size = os.path.getsize(old_log_path)
		except OSError:
			return

		already_checked = (
			state.get("old_log_mtime") == old_mtime and state.get("old_log_size") == old_size
		)
		state["old_log_mtime"] = old_mtime
		state["old_log_size"] = old_size
		_save_state(state)

		# Already looked at this exact previous-session log; don't repeat.
		if already_checked:
			return

		if not _old_log_indicates_crash(old_log_path):
			return

		try:
			with open(old_log_path, "r", encoding="utf-8", errors="replace") as f:
				issues = _collect_addon_issues_from_blocks(_iter_traceback_blocks(f))
		except OSError as e:
			logHandler.log.error("Crash analyzer could not read the previous session log: %s", e)
			return

		_clear_previous_report()
		if not issues:
			return

		report_text = _build_plain_language_report(issues)
		report_path = _write_report(report_text)
		if report_path:
			wx.CallAfter(_open_report, report_path)

	threading.Thread(target=worker, daemon=True).start()


def _logging_level_is_debug():
	"""True if NVDA's Logging Level is set to Debug. Verified against
	this environment's own nvda.ini, where the setting is stored as
	config.conf["general"]["loggingLevel"] == "DEBUG". Used only to hint
	the user when a manual scan finds nothing, in case the setting is
	filtering out detail rather than there truly being no issue.

	Must be called from NVDA's main thread only: config.conf is a
	ConfigManager that the main thread mutates, and reading its
	dictionaries from a worker thread at the same time can race that
	mutation."""
	try:
		import config
		return str(config.conf["general"]["loggingLevel"]).strip().upper() == "DEBUG"
	except Exception:
		return True  # Assume debug if the setting cannot be read, to avoid a false hint.


def run_manual_check():
	"""Perform an on-demand full scan of both the current nvda.log and the
	previous session's nvda-old.log, and open a plain-language report.
	Independent of the automatic startup check's saved read position.
	Used by the "Crash Log Analyzer" menu item/gesture, both of which
	NVDA dispatches on the main thread. Each log is streamed line-by-line
	rather than being read fully into memory and concatenated, so a large
	debug log cannot spike memory or starve the main thread."""
	tones.beep(600, 80)
	# Both of these touch state that must only be read on the main
	# thread (config.conf, and the logging module's handler lists via
	# _get_log_file_path). Resolve them here, since this function itself
	# always runs on the main thread, and hand only plain values into the
	# worker closure below.
	is_debug_logging = _logging_level_is_debug()
	log_path = _get_log_file_path()
	old_log_path = _old_log_path(log_path)

	def worker():
		issues = []
		found_any_log = False

		if log_path and os.path.isfile(log_path):
			found_any_log = True
			try:
				with open(log_path, "r", encoding="utf-8", errors="replace") as f:
					issues.extend(_collect_addon_issues_from_blocks(_iter_traceback_blocks(f)))
			except OSError as e:
				logHandler.log.error("Crash analyzer could not read log file: %s", e)

		if os.path.isfile(old_log_path):
			found_any_log = True
			try:
				with open(old_log_path, "r", encoding="utf-8", errors="replace") as f:
					issues.extend(_collect_addon_issues_from_blocks(_iter_traceback_blocks(f)))
			except OSError as e:
				logHandler.log.error("Crash analyzer could not read the previous session log: %s", e)

		if not found_any_log:
			wx.CallAfter(ui.message, _("Log file not found."))
			return

		if not issues:
			if is_debug_logging:
				wx.CallAfter(ui.message, _("No add-on related issues found in the current log."))
			else:
				wx.CallAfter(ui.message, _(
					"No add-on related issues found in the current log. For more thorough "
					"detection, consider setting NVDA's Logging Level to Debug in General Settings."
				))
			return

		report_text = _build_plain_language_report(issues)
		report_path = _write_report(report_text)
		if report_path:
			wx.CallAfter(_open_report, report_path)

	threading.Thread(target=worker, daemon=True).start()
