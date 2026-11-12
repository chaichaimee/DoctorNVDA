# healthCheck.py

import re
import addonHandler

addonHandler.initTranslation()
try:
	_ = addonHandler.getTranslation()
except Exception:
	def _(x): return x

_ENTRY_HEADER_RE = re.compile(
	r"^(?P<level>[A-Z]+) - (?P<source>.+?) \((?P<time>\d{2}:\d{2}:\d{2})\.\d+\) - "
	r"(?P<thread>.+?) \((?P<thread_id>\d+)\):\s*$"
)
_FRAME_RE = re.compile(r'File "([^"]+)", line (\d+)')
_ADDON_PATH_RE = re.compile(r"[\\/]addons[\\/]([^\\/]+)[\\/]")
_EXTERNAL_SOURCE_RE = re.compile(
	r"^external:(?:globalPlugins|appModules|synthDrivers|brailleDisplayDrivers|visionEnhancementProviders)\.([^.]+)"
)
_EXCEPTION_LINE_RE = re.compile(r"^(?P<name>[A-Za-z_][\w.]*(?:Error|Exception|Warning|Exit|Interrupt))\b\s*:?\s*(?P<text>.*)$")
_SECONDS_RE = re.compile(r"(\d+(?:\.\d+)?) (?:sec|seconds)\b")
_FOREGROUND_RE = re.compile(r"Foreground still \d+ \((\w+)\)")
_PYTHON_WARNING_RE = re.compile(r"(\w+Warning): (.*)$")
_PATH_SEGMENT_RE = re.compile(r"[\\/]")
_TRACEBACK_START = "Traceback (most recent call last):"

_MAX_ENTRY_LINES = 300
_MAX_TEXT_LENGTH = 250
_MAX_FINDINGS_LISTED = 60
_SERIOUS_FREEZE_SECONDS = 5.0
_QUIET_LEVELS = ("DEBUG", "INFO", "IO")
_APP_WAIT_MODULES = ("oleacc", "UIAHandler", "IAccessibleHandler")

SEVERITY_ORDER = ("serious", "warning", "notice")


def iter_entries(file_obj):
	"""Stream a log file and yield one dict per log entry. Only the lines
	of the entry being read are buffered, and an entry body is capped, so
	a very large log never has to be held in memory."""
	current = None
	for raw_line in file_obj:
		line = raw_line.rstrip("\r\n")
		match = _ENTRY_HEADER_RE.match(line)
		if match:
			if current is not None:
				yield current
			current = {
				"level": match.group("level"),
				"source": match.group("source"),
				"time": match.group("time"),
				"body": [],
			}
			continue
		if current is not None and len(current["body"]) < _MAX_ENTRY_LINES:
			current["body"].append(line)
	if current is not None:
		yield current


def _first_text(body):
	for line in body:
		stripped = line.strip()
		if stripped:
			return stripped[:_MAX_TEXT_LENGTH]
	return ""


def _file_name(path):
	return _PATH_SEGMENT_RE.split(path)[-1]


def _module_stem(path):
	name = _file_name(path)
	return name.rsplit(".", 1)[0] if "." in name else name


def _has_traceback(body):
	return any(_TRACEBACK_START in line for line in body)


def _addon_from_frames(body):
	for line in reversed(body):
		frame = _FRAME_RE.search(line)
		if not frame:
			continue
		match = _ADDON_PATH_RE.search(frame.group(1))
		if match:
			return match.group(1)
	return None


def _addon_from_entry(entry):
	addon = _addon_from_frames(entry["body"])
	if addon:
		return addon
	match = _EXTERNAL_SOURCE_RE.match(entry["source"])
	return match.group(1) if match else None


def _exception_info(body):
	if not _has_traceback(body):
		return None
	for line in reversed(body):
		stripped = line.strip()
		if not stripped:
			continue
		match = _EXCEPTION_LINE_RE.match(stripped)
		if match:
			return match.group("name").rsplit(".", 1)[-1], match.group("text")[:_MAX_TEXT_LENGTH]
		return None
	return None


def _explain_exception(name):
	programming = ("TypeError", "AttributeError", "NameError", "KeyError", "IndexError", "ValueError", "ImportError", "ModuleNotFoundError", "UnboundLocalError", "AssertionError", "SyntaxError")
	if name == "PermissionError":
		return _("Windows refused access to a file, folder or process.")
	if name in ("FileNotFoundError", "NotADirectoryError"):
		return _("A file or folder that was needed could not be found.")
	if name == "COMError":
		return _("A Windows accessibility component returned an error. The program in use may not support accessibility fully.")
	if name == "MemoryError":
		return _("The computer ran out of memory.")
	if name in ("TimeoutError", "ConnectionError", "ConnectionResetError", "ConnectionRefusedError"):
		return _("A connection or an operation took too long or was refused.")
	if name in ("UnicodeDecodeError", "UnicodeEncodeError"):
		return _("Some text could not be read because of an encoding problem.")
	if name == "OSError":
		return _("Windows reported a system error.")
	if name == "RuntimeError":
		return _("The program stopped an operation because of an unexpected state.")
	if name in programming:
		return _("This is a mistake in the program code ({name}), not a problem with your computer.").format(name=name)
	return _("An error of type {name} occurred.").format(name=name)


def _main_thread_frames(body):
	frames = []
	collecting = False
	for line in body:
		if line.startswith("Python stack for thread"):
			collecting = "(MainThread)" in line
			if collecting:
				frames = []
			continue
		if collecting:
			match = _FRAME_RE.search(line)
			if match:
				frames.append((match.group(1), match.group(2)))
	return frames


def _freeze_location(frames):
	for path, line_no in reversed(frames):
		match = _ADDON_PATH_RE.search(path)
		if match:
			return {"addon": match.group(1), "file": _file_name(path), "line": line_no}
	if not frames:
		return {}
	path, line_no = frames[-1]
	return {"module": _module_stem(path), "line": line_no}


def _normalize(text):
	return re.sub(r"\d+", "#", text)[:120]


def _record(findings, key, severity, kind, data, time_text, log_label):
	existing = findings.get(key)
	if existing is None:
		findings[key] = {
			"severity": severity,
			"kind": kind,
			"data": data,
			"count": 1,
			"time": time_text,
			"log": log_label,
		}
		return
	existing["count"] += 1
	if SEVERITY_ORDER.index(severity) < SEVERITY_ORDER.index(existing["severity"]):
		existing["severity"] = severity
	if data.get("seconds", 0) > existing["data"].get("seconds", 0):
		existing["data"]["seconds"] = data["seconds"]


def _record_freeze(findings, log_label, freeze, seconds):
	location = freeze.get("location", {})
	severity = "warning"
	if seconds is None or seconds >= _SERIOUS_FREEZE_SECONDS:
		severity = "serious"
	kind = "freeze" if seconds is not None else "freeze_unrecovered"
	key = (log_label, kind, location.get("addon"), location.get("module"))
	data = {"location": location, "seconds": seconds or 0}
	_record(findings, key, severity, kind, data, freeze["time"], log_label)


def _handle_watchdog_entry(entry, pending_freeze, findings, log_label):
	first = _first_text(entry["body"])
	if first.startswith("Starting freeze recovery"):
		if pending_freeze is not None:
			_record_freeze(findings, log_label, pending_freeze, None)
		return {"time": entry["time"], "location": {}}
	if pending_freeze is None:
		return None
	if first.startswith("Listing stacks"):
		pending_freeze["location"] = _freeze_location(_main_thread_frames(entry["body"]))
		return pending_freeze
	if first.startswith("Recovered from freeze"):
		match = _SECONDS_RE.search(first)
		seconds = float(match.group(1)) if match else 0.0
		_record_freeze(findings, log_label, pending_freeze, seconds)
		return None
	return pending_freeze


def _classify_known(entry, first, log_label, findings):
	"""Record a finding for a message NVDA is known to write. Returns True
	when the entry was handled, so the generic rules skip it."""
	time_text = entry["time"]
	if first.startswith("Slow starting core"):
		match = _SECONDS_RE.search(first)
		_record(findings, (log_label, "slow_start"), "warning", "slow_start", {"seconds": float(match.group(1)) if match else 0.0}, time_text, log_label)
		return True
	if "Foreground took too long to change" in first:
		match = _FOREGROUND_RE.search(first)
		window_class = match.group(1) if match else ""
		_record(findings, (log_label, "foreground_slow", window_class), "warning", "foreground_slow", {"window_class": window_class}, time_text, log_label)
		return True
	if first.startswith("Unable to open process for processId"):
		_record(findings, (log_label, "process_denied"), "notice", "process_denied", {}, time_text, log_label)
		return True
	if first.startswith("Unable to get process handle for process"):
		return True
	if "error walking up to an element with a valid windowHandle" in first:
		_record(findings, (log_label, "window_handle"), "notice", "window_handle", {}, time_text, log_label)
		return True
	if first.startswith("No locale gesture map for language"):
		_record(findings, (log_label, "no_gesture_map"), "notice", "no_gesture_map", {"text": first}, time_text, log_label)
		return True
	if first.startswith("Touch only supported on installed copies"):
		_record(findings, (log_label, "touch_portable"), "notice", "touch_portable", {}, time_text, log_label)
		return True
	if "is deprecated" in first and entry["level"] == "WARNING":
		addon = _addon_from_entry(entry)
		_record(findings, (log_label, "deprecated", addon, first), "warning", "deprecated", {"addon": addon, "text": first}, time_text, log_label)
		return True
	if entry["source"] == "Python warning":
		match = _PYTHON_WARNING_RE.search(first)
		if match:
			path_match = _ADDON_PATH_RE.search(first)
			addon = path_match.group(1) if path_match else None
			data = {"addon": addon, "name": match.group(1), "text": match.group(2)}
			_record(findings, (log_label, "python_warning", addon, first), "warning", "python_warning", data, time_text, log_label)
			return True
	return False


def _classify_generic(entry, first, log_label, findings):
	body = entry["body"]
	has_traceback = _has_traceback(body)
	addon = _addon_from_entry(entry)
	if has_traceback and _addon_from_frames(body):
		# Already listed by the add-on error scan.
		return
	level = entry["level"]
	if level in ("ERROR", "CRITICAL"):
		severity = "serious"
	elif level == "WARNING":
		severity = "warning"
	elif has_traceback:
		severity = "warning"
	else:
		severity = "notice"
	exception = _exception_info(body)
	data = {
		"addon": addon,
		"source": entry["source"],
		"text": first,
		"exception": exception[0] if exception else None,
		"exception_text": exception[1] if exception else "",
	}
	key = (log_label, "generic", severity, addon or entry["source"], _normalize(first))
	_record(findings, key, severity, "generic", data, entry["time"], log_label)


def analyze_entries(entries, log_label):
	"""Return a list of findings for one log. Every distinct problem is
	listed once with the number of times it was seen."""
	findings = {}
	pending_freeze = None
	for entry in entries:
		if entry["source"] == "watchdog.waitForFreezeRecovery":
			pending_freeze = _handle_watchdog_entry(entry, pending_freeze, findings, log_label)
			continue
		if entry["level"] in _QUIET_LEVELS:
			continue
		first = _first_text(entry["body"])
		if not first:
			continue
		if _classify_known(entry, first, log_label, findings):
			continue
		_classify_generic(entry, first, log_label, findings)
	if pending_freeze is not None:
		_record_freeze(findings, log_label, pending_freeze, None)
	return list(findings.values())


def make_crash_finding(log_label):
	return {"severity": "serious", "kind": "crash", "data": {}, "count": 1, "time": "", "log": log_label}


def _describe(finding, display_name):
	kind = finding["kind"]
	data = finding["data"]
	where = ""
	meaning = ""
	advice = ""
	if kind in ("freeze", "freeze_unrecovered"):
		location = data.get("location", {})
		if kind == "freeze":
			problem = _("NVDA stopped responding for about {seconds:.1f} seconds and then recovered.").format(seconds=data["seconds"])
		else:
			problem = _("NVDA stopped responding and the log ends before it recovered. NVDA was probably closed or restarted while frozen.")
		if location.get("addon"):
			where = _("The add-on {addon} was running at that moment (file {file}, line {line}).").format(
				addon=display_name(location["addon"]), file=location["file"], line=location["line"]
			)
			advice = _("Use Binary Search Debugging in this menu to confirm whether this add-on is the cause.")
		elif location.get("module") in _APP_WAIT_MODULES:
			where = _("NVDA was waiting for the program in front of you to answer an accessibility request. That program is probably the cause.")
		elif location:
			where = _("NVDA was busy inside {module} (line {line}).").format(module=location["module"], line=location["line"])
	elif kind == "slow_start":
		problem = _("NVDA took {seconds:.1f} seconds to start, which is slower than normal.").format(seconds=data["seconds"])
		advice = _("Many add-ons or a slow disk can cause this. Binary Search Debugging can help find a slow add-on.")
	elif kind == "foreground_slow":
		problem = _("Windows was slow to switch the active window, so NVDA may have announced it late.")
		if data.get("window_class"):
			where = _("Window class: {name}.").format(name=data["window_class"])
	elif kind == "process_denied":
		problem = _("NVDA could not look inside a protected Windows process. This is normal and harmless.")
	elif kind == "window_handle":
		problem = _("A program gave NVDA incomplete accessibility information. This is usually harmless.")
		advice = _("If it keeps happening while you use one program, that program has an accessibility problem.")
	elif kind == "no_gesture_map":
		problem = _("NVDA has no separate keyboard command map for your language, so the default commands are used. This is normal.")
	elif kind == "touch_portable":
		problem = _("Touch screen support is off because this is a portable copy of NVDA. This is normal.")
	elif kind == "deprecated":
		if data.get("addon"):
			problem = _("The add-on {addon} uses an outdated NVDA feature.").format(addon=display_name(data["addon"]))
		else:
			problem = _("An add-on or NVDA component uses an outdated NVDA feature.")
		meaning = data["text"]
		advice = _("It works for now but may stop working after a future NVDA update. The add-on author should update it.")
	elif kind == "python_warning":
		if data.get("addon"):
			problem = _("The add-on {addon} uses a Python feature that is being removed or changed.").format(addon=display_name(data["addon"]))
		else:
			problem = _("A component uses a Python feature that is being removed or changed.")
		meaning = data["text"]
	elif kind == "crash":
		problem = _("The previous NVDA session ended unexpectedly (a crash or a forced close).")
	else:
		who = display_name(data["addon"]) if data.get("addon") else data["source"]
		if finding["severity"] == "serious":
			problem = _("{who} reported an error: {text}").format(who=who, text=data["text"])
		elif finding["severity"] == "warning":
			problem = _("{who} reported a problem that NVDA handled: {text}").format(who=who, text=data["text"])
		else:
			problem = _("{who} left a minor note: {text}").format(who=who, text=data["text"])
		if data.get("exception"):
			meaning = _explain_exception(data["exception"])
	return problem, where, meaning, advice


def _severity_label(severity):
	if severity == "serious":
		return _("Serious problem")
	if severity == "warning":
		return _("Warning")
	return _("Harmless notice")


def _format_finding(finding, display_name):
	problem, where, meaning, advice = _describe(finding, display_name)
	lines = [
		_("severity: {label}").format(label=_severity_label(finding["severity"])),
		_("problem: {text}").format(text=problem),
	]
	if where:
		lines.append(_("where: {text}").format(text=where))
	if meaning:
		lines.append(_("meaning: {text}").format(text=meaning))
	if advice:
		lines.append(_("advice: {text}").format(text=advice))
	if finding["time"] and finding["count"] > 1:
		lines.append(_("when: first at {time} in {log}, seen {count} times").format(time=finding["time"], log=finding["log"], count=finding["count"]))
	elif finding["time"]:
		lines.append(_("when: {time} in {log}").format(time=finding["time"], log=finding["log"]))
	else:
		lines.append(_("when: {log}").format(log=finding["log"]))
	return "\n".join(lines)


def build_findings_text(findings, display_name):
	ordered = sorted(findings, key=lambda item: (SEVERITY_ORDER.index(item["severity"]), -item["count"]))
	listed = ordered[:_MAX_FINDINGS_LISTED]
	entries = [_format_finding(item, display_name) for item in listed]
	hidden = len(ordered) - len(listed)
	if hidden > 0:
		entries.append(_("{count} more minor items were not listed.").format(count=hidden))
	return "\n\n".join(entries)


def build_summary(findings, addon_error_count):
	counts = {name: 0 for name in SEVERITY_ORDER}
	for item in findings:
		counts[item["severity"]] += 1
	if counts["serious"] or addon_error_count:
		verdict = _("NVDA health: needs attention.")
	elif counts["warning"]:
		verdict = _("NVDA health: mostly good, with minor issues.")
	else:
		verdict = _("NVDA health: good.")
	totals = _("Serious problems: {serious}. Warnings: {warning}. Harmless notices: {notice}. Add-on errors: {addons}.").format(
		serious=counts["serious"], warning=counts["warning"], notice=counts["notice"], addons=addon_error_count
	)
	return verdict + "\n" + totals
