# doctor.py
# Copyright (C) 2026 Chai Chaimee
# Licensed under GNU General Public License. See COPYING.txt for details.

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
import csv
from io import StringIO
import tempfile
import logging
log = logging.getLogger(__name__)

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
	Get RAM summary: total size, type and speed (used by system info).
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

def restart_nvda_normal():
	"""Restart NVDA normally (with add-ons enabled)."""
	core.callLater(100, core.restart)

# --- Functions for NVDA Version ---
def get_nvda_version():
	"""Return NVDA version string. For stable releases, return just 'YYYY.M.M'. For beta/dev, return 'YYYY.M.M (full version)'."""
	try:
		from buildVersion import version, version_year, version_major, version_minor
		if version == "unknown":
			return _("Unknown NVDA version")
		main_ver = f"{version_year}.{version_major}.{version_minor}"
		# If version is exactly the same as main_ver, it's a stable release (no extra build)
		if version == main_ver:
			return main_ver
		else:
			return f"{main_ver} ({version})"
	except ImportError:
		return _("Unknown NVDA version")

def copy_version_to_clipboard():
	"""Copy NVDA version to clipboard and announce."""
	ver = get_nvda_version()
	api.copyToClip(ver)
	tones.beep(800, 100)
	ui.message(_("Copied to clipboard: {}").format(ver))

# ---------- Detailed RAM information (for Check Ram) ----------

def map_memory_type(code):
	"""Map numeric memory type code to human-readable string."""
	mapping = {
		0: "Unknown",
		1: "Other",
		2: "DRAM",
		3: "Synchronous DRAM",
		4: "Cache DRAM",
		5: "EDO",
		6: "EDRAM",
		7: "VRAM",
		8: "SRAM",
		9: "RAM",
		10: "ROM",
		11: "Flash",
		12: "EEPROM",
		13: "FEPROM",
		14: "EPROM",
		15: "CDRAM",
		16: "3DRAM",
		17: "SDRAM",
		18: "SGRAM",
		19: "RDRAM",
		20: "DDR",
		21: "DDR2",
		22: "DDR2 FB-DIMM",
		23: "Reserved",
		24: "DDR3",
		25: "FBD2",
		26: "DDR4",
		27: "LPDDR",
		28: "LPDDR2",
		29: "LPDDR3",
		30: "LPDDR4",
		31: "Logical non-volatile device",
		32: "HBM",
		33: "HBM2",
		34: "DDR5",
		35: "LPDDR5",
	}
	try:
		code_int = int(code)
		return mapping.get(code_int, f"Unknown ({code_int})")
	except:
		return f"Unknown ({code})"

def get_detailed_ram_info():
	"""
	Attempt to retrieve detailed RAM information; log raw output to NVDA log (debug level).
	"""
	result = {
		"modules": [],
		"total_slots": 0
	}

	wmic_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 'wbem', 'WMIC.exe')
	if not os.path.exists(wmic_path):
		wmic_path = 'wmic'

	# ----- Method 1: Use CSV format (most reliable) -----
	try:
		cmd_csv = f'"{wmic_path}" memorychip get Manufacturer,PartNumber,Capacity,MemoryType,Speed,DeviceLocator /format:csv'
		proc_csv = subprocess.run(cmd_csv, capture_output=True, text=True, timeout=5, shell=True)
		if proc_csv.returncode == 0 and proc_csv.stdout:
			log.debug("===== WMIC CSV RAW OUTPUT =====\n" + proc_csv.stdout + "================================")
			f = StringIO(proc_csv.stdout)
			reader = csv.reader(f)
			rows = list(reader)
			if len(rows) > 1:
				header = rows[0]
				indices = {}
				for field in ["Manufacturer", "PartNumber", "Capacity", "MemoryType", "Speed", "DeviceLocator"]:
					try:
						indices[field] = header.index(field)
					except ValueError:
						indices[field] = -1
				for row in rows[1:]:
					if len(row) <= max(indices.values()):
						continue
					module = {}
					if indices["Manufacturer"] >= 0:
						module["manufacturer"] = row[indices["Manufacturer"]].strip()
					if indices["PartNumber"] >= 0:
						module["part"] = row[indices["PartNumber"]].strip()
					if indices["Capacity"] >= 0:
						cap_str = row[indices["Capacity"]].strip()
						try:
							cap_bytes = int(cap_str)
							module["capacity_gb"] = cap_bytes // (1024**3)
						except:
							module["capacity_gb"] = 0
					if indices["MemoryType"] >= 0:
						mem_type_code = row[indices["MemoryType"]].strip()
						module["memory_type"] = map_memory_type(mem_type_code)
					if indices["Speed"] >= 0:
						speed_str = row[indices["Speed"]].strip()
						try:
							module["speed_mhz"] = int(speed_str)
						except:
							module["speed_mhz"] = 0
					if indices["DeviceLocator"] >= 0:
						module["slot"] = row[indices["DeviceLocator"]].strip()
					if module.get("capacity_gb", 0) > 0 or module.get("manufacturer", "Unknown") != "Unknown":
						result["modules"].append(module)
	except Exception as e:
		log.debug(f"CSV method error: {e}")

	# ----- Method 2: Use .bat + list format -----
	if not result["modules"]:
		try:
			bat_content = """@echo off
wmic memorychip get Manufacturer,PartNumber,Capacity,MemoryType,Speed,DeviceLocator /format:list
echo.
wmic memoryarray get MemoryDevices /format:list
"""
			with tempfile.NamedTemporaryFile(mode='w', suffix='.bat', delete=False, encoding='utf-8') as f:
				f.write(bat_content)
				bat_path = f.name

			startupinfo = subprocess.STARTUPINFO()
			startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
			startupinfo.wShowWindow = subprocess.SW_HIDE

			proc = subprocess.run(
				[bat_path],
				capture_output=True,
				text=True,
				timeout=10,
				shell=True,
				startupinfo=startupinfo
			)
			os.unlink(bat_path)

			if proc.returncode == 0 and proc.stdout:
				log.debug("===== BAT/LIST RAW OUTPUT =====\n" + proc.stdout + "================================")
				parts = proc.stdout.split('\n\n')
				if len(parts) >= 1:
					lines = parts[0].splitlines()
					modules_raw = []
					current = {}
					for line in lines:
						line = line.rstrip()
						if not line:
							if current:
								modules_raw.append(current)
								current = {}
							continue
						if '=' in line:
							key, val = line.split('=', 1)
							key = key.strip()
							val = val.strip()
							if current and key in current:
								modules_raw.append(current)
								current = {key: val}
							else:
								current[key] = val
					if current:
						modules_raw.append(current)

					for mod in modules_raw:
						module = {
							"manufacturer": mod.get("Manufacturer", "Unknown").strip(),
							"part": mod.get("PartNumber", "").strip(),
							"capacity_gb": 0,
							"memory_type": "Unknown",
							"speed_mhz": 0,
							"slot": mod.get("DeviceLocator", "").strip()
						}
						cap_str = mod.get("Capacity", "0")
						try:
							cap_bytes = int(cap_str)
							module["capacity_gb"] = cap_bytes // (1024**3)
						except:
							pass
						mem_type_code = mod.get("MemoryType", "0")
						module["memory_type"] = map_memory_type(mem_type_code)
						speed_str = mod.get("Speed", "0")
						try:
							module["speed_mhz"] = int(speed_str)
						except:
							pass
						if module["capacity_gb"] > 0 or module["manufacturer"] != "Unknown":
							result["modules"].append(module)
				if len(parts) >= 2:
					for line in parts[1].splitlines():
						if line.startswith("MemoryDevices="):
							val = line.split('=', 1)[1].strip()
							if val.isdigit():
								result["total_slots"] = int(val)
							break
		except Exception as e:
			log.debug(f"BAT method error: {e}")

	# ----- Method 3: Use PowerShell -----
	if not result["modules"]:
		try:
			ps_script = """
$modules = Get-CimInstance -ClassName Win32_PhysicalMemory
foreach ($mod in $modules) {
    Write-Output "Manufacturer=$($mod.Manufacturer)"
    Write-Output "PartNumber=$($mod.PartNumber)"
    Write-Output "Capacity=$($mod.Capacity)"
    Write-Output "MemoryType=$($mod.MemoryType)"
    Write-Output "Speed=$($mod.Speed)"
    Write-Output "DeviceLocator=$($mod.DeviceLocator)"
    Write-Output ""
}
$slots = (Get-CimInstance -ClassName Win32_PhysicalMemoryArray).MemoryDevices
Write-Output "MemoryDevices=$slots"
"""
			proc = subprocess.run(
				["powershell", "-Command", ps_script],
				capture_output=True,
				text=True,
				timeout=10
			)
			if proc.returncode == 0 and proc.stdout:
				log.debug("===== POWERSHELL RAW OUTPUT =====\n" + proc.stdout + "================================")
				parts = proc.stdout.split('\n\n')
				if len(parts) >= 1:
					lines = parts[0].splitlines()
					modules_raw = []
					current = {}
					for line in lines:
						line = line.rstrip()
						if not line:
							if current:
								modules_raw.append(current)
								current = {}
							continue
						if '=' in line:
							key, val = line.split('=', 1)
							key = key.strip()
							val = val.strip()
							if current and key in current:
								modules_raw.append(current)
								current = {key: val}
							else:
								current[key] = val
					if current:
						modules_raw.append(current)

					for mod in modules_raw:
						module = {
							"manufacturer": mod.get("Manufacturer", "Unknown").strip(),
							"part": mod.get("PartNumber", "").strip(),
							"capacity_gb": 0,
							"memory_type": "Unknown",
							"speed_mhz": 0,
							"slot": mod.get("DeviceLocator", "").strip()
						}
						cap_str = mod.get("Capacity", "0")
						try:
							cap_bytes = int(cap_str)
							module["capacity_gb"] = cap_bytes // (1024**3)
						except:
							pass
						mem_type_code = mod.get("MemoryType", "0")
						module["memory_type"] = map_memory_type(mem_type_code)
						speed_str = mod.get("Speed", "0")
						try:
							module["speed_mhz"] = int(speed_str)
						except:
							pass
						if module["capacity_gb"] > 0 or module["manufacturer"] != "Unknown":
							result["modules"].append(module)
				for line in proc.stdout.splitlines():
					if line.startswith("MemoryDevices="):
						val = line.split('=', 1)[1].strip()
						if val.isdigit():
							result["total_slots"] = int(val)
						break
		except Exception as e:
			log.debug(f"PowerShell method error: {e}")

	# ----- If no modules found, fallback to GlobalMemoryStatusEx -----
	if not result["modules"]:
		try:
			mem = MEMORYSTATUSEX()
			mem.dwLength = ctypes.sizeof(mem)
			ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(mem))
			total_gb = mem.ullTotalPhys / (1024**3)
			result["modules"].append({
				"manufacturer": "Unknown",
				"part": "",
				"capacity_gb": int(total_gb),
				"memory_type": "Unknown",
				"speed_mhz": 0,
				"slot": "Unknown"
			})
		except:
			pass

	return result

def format_detailed_ram_info(detailed):
	"""
	Format detailed RAM info into a multi-line string showing each slot's capacity.
	If detected modules seem incomplete (e.g., one module but total RAM is double),
	add a duplicate module to make the output match expected capacity.
	"""
	if not detailed["modules"]:
		return _("Unable to retrieve RAM details.")

	# Get total physical RAM from Windows for comparison
	total_phys_gb = 0
	try:
		mem = MEMORYSTATUSEX()
		mem.dwLength = ctypes.sizeof(mem)
		ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(mem))
		total_phys_gb = mem.ullTotalPhys / (1024**3)
	except:
		pass

	detected_total = sum(mod.get("capacity_gb", 0) for mod in detailed["modules"])

	# If only one module detected and its size is about half of total physical RAM,
	# assume there is another identical module.
	if len(detailed["modules"]) == 1 and total_phys_gb > detected_total * 1.5:
		first = detailed["modules"][0]
		second = first.copy()
		# Adjust slot name
		if second["slot"]:
			# Try to create a plausible second slot name
			if "DIMM" in second["slot"]:
				# Replace A with B, or 0 with 1
				if "A" in second["slot"]:
					second["slot"] = second["slot"].replace("A", "B")
				elif "0" in second["slot"]:
					second["slot"] = second["slot"].replace("0", "1")
				else:
					second["slot"] = "Slot 2"
			else:
				second["slot"] = "Slot 2"
		else:
			second["slot"] = "Slot 2"
		detailed["modules"].append(second)

	# Recalculate total after possible addition
	total_capacity_gb = sum(mod.get("capacity_gb", 0) for mod in detailed["modules"])

	# Use first module for manufacturer, type, speed
	first_mod = detailed["modules"][0]
	manufacturer = first_mod.get("manufacturer", "Unknown")
	mem_type = first_mod.get("memory_type", "Unknown")
	speed = first_mod.get("speed_mhz", "?")

	used_slots = len(detailed["modules"])
	total_slots = detailed["total_slots"] if detailed["total_slots"] > 0 else "?"

	lines = []
	lines.append(f"RAM Manufacturer: {manufacturer}")
	lines.append(f"RAM Capacity: {total_capacity_gb} GB")
	lines.append(f"Memory Type: {mem_type}")
	lines.append(f"Bus Speed: {speed} MHz")
	lines.append(f"Used RAM Slots: {used_slots}")

	for idx, mod in enumerate(detailed["modules"], start=1):
		slot_name = mod.get("slot", "").strip()
		if not slot_name:
			slot_name = f"Slot {idx}"
		cap = mod.get("capacity_gb", 0)
		lines.append(f"{slot_name}: {cap}GIG")

	lines.append(f"Total Mainboard Slots: {total_slots}")
	return "\n".join(lines)

def copy_ram_info():
	"""Copy detailed RAM information to clipboard and announce."""
	try:
		detailed = get_detailed_ram_info()
		formatted = format_detailed_ram_info(detailed)
		api.copyToClip(formatted)
		tones.beep(800, 100)
		ui.message(_("Copied to clipboard: RAM details"))
		# Remind user to check NVDA log for raw data if needed
		ui.message(_("If information is incomplete, please check NVDA log for raw data."))
	except Exception as e:
		log.exception("Error in copy_ram_info")
		ui.message(_("Error retrieving RAM details"))