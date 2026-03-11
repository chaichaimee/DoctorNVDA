# doctor.py

import os
import datetime
import ui
import api
import platform
import core
import speech
import tones
import queueHandler
import subprocess
import ctypes
import ctypes.wintypes
import winreg
from globalVars import appArgs
import addonHandler
import csv                # Added for reading CSV
from io import StringIO   # Added for converting string to virtual file

addonHandler.initTranslation()
try:
	_ = addonHandler.getTranslation()
except:
	def _(x): return x

CRITICAL_FILES = ["nvda.ini", "gestures.ini", "profiles", "speechDicts", "addons"]

class MEMORYSTATUSEX(ctypes.Structure):
	_fields_ = [
		("dwLength", ctypes.wintypes.DWORD),
		("dwMemoryLoad", ctypes.wintypes.DWORD),
		("ullTotalPhys", ctypes.c_ulonglong),
		("ullAvailPhys", ctypes.c_ulonglong),
		("ullTotalPageFile", ctypes.c_ulonglong),
		("ullAvailPageFile", ctypes.c_ulonglong),
		("ullTotalVirtual", ctypes.c_ulonglong),
		("ullAvailVirtual", ctypes.c_ulonglong),
		("ullAvailExtendedVirtual", ctypes.c_ulonglong),
	]

def get_report_path():
	path = os.path.join(appArgs.configPath, "ChaiChaimee", "DoctorNVDA", "Reports")
	if not os.path.exists(path):
		os.makedirs(path)
	return path

def cleanup_reports():
	path = get_report_path()
	try:
		if os.path.exists(path):
			for f in os.listdir(path):
				if f.endswith(".txt"):
					os.remove(os.path.join(path, f))
	except:
		pass

def speak_now(text, is_error=False):
	if is_error:
		tones.beep(300, 200)
	else:
		tones.beep(800, 100)
	queueHandler.queueFunction(queueHandler.eventQueue, speech.cancelSpeech)
	core.callLater(100, ui.message, text)

def get_os_info():
	"""Get correct OS information from Registry and RtlGetVersion"""
	try:
		# Open Registry key for Windows NT version
		key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
		product_name = winreg.QueryValueEx(key, "ProductName")[0]
		build = winreg.QueryValueEx(key, "CurrentBuildNumber")[0]
		try:
			ubr = winreg.QueryValueEx(key, "UBR")[0]
		except FileNotFoundError:
			ubr = 0
		display_version = winreg.QueryValueEx(key, "DisplayVersion")[0]
		build_lab = winreg.QueryValueEx(key, "BuildLabEx")[0]
		winreg.CloseKey(key)

		# Use RtlGetVersion to get correct build number (including UBR)
		class RTL_OSVERSIONINFOEXW(ctypes.Structure):
			_fields_ = [
				("dwOSVersionInfoSize", ctypes.wintypes.DWORD),
				("dwMajorVersion", ctypes.wintypes.DWORD),
				("dwMinorVersion", ctypes.wintypes.DWORD),
				("dwBuildNumber", ctypes.wintypes.DWORD),
				("dwPlatformId", ctypes.wintypes.DWORD),
				("szCSDVersion", ctypes.wintypes.WCHAR * 128),
			]
		ver = RTL_OSVERSIONINFOEXW()
		ver.dwOSVersionInfoSize = ctypes.sizeof(ver)
		ntdll = ctypes.windll.ntdll
		ntdll.RtlGetVersion(ctypes.byref(ver))
		full_build = ver.dwBuildNumber

		# Correct product name (e.g., Windows 10 IoT Enterprise LTSC 2024 -> Windows 11)
		# If DisplayVersion >= 10.0.22000, consider it Windows 11
		if full_build >= 22000 and "Windows 10" in product_name:
			product_name = product_name.replace("Windows 10", "Windows 11")

		architecture = platform.machine()
		if architecture == "AMD64":
			arch_str = "64-bit"
		elif architecture == "x86":
			arch_str = "32-bit"
		else:
			arch_str = architecture

		return {
			"product": product_name,
			"version": display_version,
			"build": f"{build}.{ubr}",
			"full_build": full_build,
			"build_lab": build_lab,
			"arch": arch_str,
		}
	except Exception as e:
		# Fallback
		return {
			"product": platform.system(),
			"version": platform.release(),
			"build": platform.version(),
			"full_build": 0,
			"build_lab": "N/A",
			"arch": platform.architecture()[0],
		}

def get_cpu_info():
	"""Read CPU name from Registry"""
	try:
		key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
		name = winreg.QueryValueEx(key, "ProcessorNameString")[0]
		winreg.CloseKey(key)
		return " ".join(name.split())  # Remove extra spaces
	except Exception:
		return "Unknown CPU"

def get_ram_info():
	"""
	Get RAM information:
	- Total size from GlobalMemoryStatusEx
	- DDR type and speed from wmic memorychip (using CSV reader for accuracy)
	"""
	try:
		# Total RAM size
		mem = MEMORYSTATUSEX()
		mem.dwLength = ctypes.sizeof(mem)
		ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(mem))
		total_gb = mem.ullTotalPhys / (1024**3)

		# Get caption and speed of each module with wmic in CSV format
		result = subprocess.run(
			["wmic", "memorychip", "get", "caption, speed", "/format:csv"],
			capture_output=True,
			text=True,
			timeout=5,
			check=True
		)
		# Use csv.reader to handle CSV correctly
		f = StringIO(result.stdout)
		reader = csv.reader(f)
		rows = list(reader)
		if len(rows) < 2:
			return f"{total_gb:.2f} GB"
		# First line is header: ["Node", "Caption", "Speed"] (may vary slightly)
		header = rows[0]
		# Find indices of Caption and Speed columns
		try:
			cap_idx = header.index("Caption")
			speed_idx = header.index("Speed")
		except ValueError:
			# If not found, assume indices 1 and 2 respectively
			cap_idx = 1
			speed_idx = 2

		ddr_versions = []
		speeds = []
		for row in rows[1:]:
			if len(row) <= max(cap_idx, speed_idx):
				continue
			caption = row[cap_idx].strip()
			speed_str = row[speed_idx].strip()
			# Detect DDR from Caption (case-insensitive)
			upper_cap = caption.upper()
			if "DDR5" in upper_cap:
				ddr_versions.append(5)
			elif "DDR4" in upper_cap:
				ddr_versions.append(4)
			elif "DDR3" in upper_cap:
				ddr_versions.append(3)
			elif "DDR2" in upper_cap:
				ddr_versions.append(2)
			elif "DDR" in upper_cap:
				ddr_versions.append(1)  # Original DDR
			# Speed
			if speed_str.isdigit():
				speeds.append(int(speed_str))

		# Summarize DDR information
		ddr_text = ""
		if ddr_versions:
			max_ddr = max(ddr_versions)  # Use highest version found
			ddr_text = f"DDR{max_ddr}"
		speed_text = ""
		if speeds:
			avg_speed = int(sum(speeds) / len(speeds))
			speed_text = f" ({avg_speed} MHz)"

		if ddr_text:
			return f"{total_gb:.2f} GB {ddr_text}{speed_text}"
		else:
			return f"{total_gb:.2f} GB"

	except Exception:
		# On error, use only size
		try:
			mem = MEMORYSTATUSEX()
			mem.dwLength = ctypes.sizeof(mem)
			ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(mem))
			total_gb = mem.ullTotalPhys / (1024**3)
			return f"{total_gb:.2f} GB"
		except:
			return "Unknown RAM"

def get_motherboard_info():
	"""Read motherboard information from Registry or WMI"""
	try:
		# Try Registry first (BIOS info)
		key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\BIOS")
		manufacturer = winreg.QueryValueEx(key, "BaseBoardManufacturer")[0]
		product = winreg.QueryValueEx(key, "BaseBoardProduct")[0]
		winreg.CloseKey(key)
		if manufacturer and product:
			return f"{manufacturer} {product}"
		else:
			raise Exception("No registry data")
	except Exception:
		try:
			# Use wmic as fallback
			result = subprocess.run(
				["wmic", "baseboard", "get", "manufacturer,product", "/format:csv"],
				capture_output=True,
				text=True,
				timeout=5,
				check=True
			)
			lines = result.stdout.strip().splitlines()
			if len(lines) >= 2:
				parts = lines[1].split(',')
				if len(parts) >= 3:
					manufacturer = parts[1].strip()
					product = parts[2].strip()
					if manufacturer and product:
						return f"{manufacturer} {product}"
		except Exception:
			pass
		return "Unknown Motherboard"

def get_detailed_sys_info():
	os_info = get_os_info()
	cpu = get_cpu_info()
	ram = get_ram_info()
	mobo = get_motherboard_info()

	lines = []
	lines.append(f"OS: {os_info['product']}")
	lines.append(f"Version: {os_info['version']}")
	lines.append(f"Build: {os_info['build']} ({os_info['build_lab']})")
	lines.append(f"Architecture: {os_info['arch']}")
	lines.append(f"CPU: {cpu}")
	lines.append(f"RAM: {ram}")
	lines.append(f"Motherboard: {mobo}")
	return "\n".join(lines)

def copy_sys_info():
	info = get_detailed_sys_info()
	api.copyToClip(info)
	speak_now(_("System info copied"))

def run_health_scan():
	missing = [i for i in CRITICAL_FILES if not os.path.exists(os.path.join(appArgs.configPath, i))]
	if not missing:
		speak_now(_("All configuration files present"))
	else:
		speak_now(_("Missing {n} configuration files").format(n=len(missing)), is_error=True)
		report = f"DoctorNVDA userConfig Scan - ISSUES\nDate: {datetime.datetime.now()}\n---\nMissing:\n" + "\n".join(missing)
		save_and_open_report("ConfigScan", report)

def save_and_open_report(report_type, content):
	now = datetime.datetime.now().strftime("%H-%M-%S")
	filename = f"{report_type}_ISSUE_{now}.txt"
	full_path = os.path.join(get_report_path(), filename)
	try:
		with open(full_path, "w", encoding="utf-8") as f:
			f.write(content)
		os.startfile(full_path)
		return full_path
	except:
		return None

def check_addons():
	inactive = [a.manifest['name'] for a in addonHandler.getAvailableAddons() if not a.isRunning]
	if not inactive:
		speak_now(_("All addons active"))
	else:
		speak_now(_("Found {n} inactive addons Opening report").format(n=len(inactive)), is_error=True)
		report = f"DoctorNVDA Addon Check - INACTIVE\nDate: {datetime.datetime.now()}\n---\n" + "\n".join(inactive)
		save_and_open_report("AddonCheck", report)

def restart_nvda():
	"""Restart NVDA in safe mode (add-ons disabled)."""
	core.callLater(100, core.restart, disableAddons=True)

# --- Functions for NVDA Version (moved from version.py) ---
def get_nvda_version():
	"""Return NVDA version string like '2025.3.3 (2025.3.3.54605)'."""
	try:
		from buildVersion import version, version_year, version_major, version_minor
		if version == "unknown":
			return _("Unknown NVDA version")
		return f"{version_year}.{version_major}.{version_minor} ({version})"
	except ImportError:
		return _("Unknown NVDA version")

def copy_version_to_clipboard():
	"""Copy NVDA version to clipboard and announce."""
	ver = get_nvda_version()
	api.copyToClip(ver)
	tones.beep(800, 100)
	ui.message(_("Copied to clipboard: {}").format(ver))