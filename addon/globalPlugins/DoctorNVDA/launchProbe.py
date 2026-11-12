# launchProbe.py

import ctypes
import ctypes.wintypes as wintypes
import os
import sys
import threading

import gui
import logHandler
import winUser

_NVDA_WINDOW_CLASS = "wxWindowClassNR"
_NVDA_WINDOW_TITLE = "NVDA"
_PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
_MAX_CANDIDATES = 16
_WM_SETHOTKEY = 0x0032
_WM_GETHOTKEY = 0x0033
_SMTO_ABORTIFHUNG = 0x0002
_SEND_TIMEOUT_MS = 200
_WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

_user32 = ctypes.WinDLL("user32", use_last_error=True)
_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

_user32.FindWindowExW.argtypes = [wintypes.HWND, wintypes.HWND, wintypes.LPCWSTR, wintypes.LPCWSTR]
_user32.FindWindowExW.restype = wintypes.HWND
_user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
_user32.GetWindowThreadProcessId.restype = wintypes.DWORD
_user32.IsWindowVisible.argtypes = [wintypes.HWND]
_user32.IsWindowVisible.restype = wintypes.BOOL
_user32.EnumWindows.argtypes = [_WNDENUMPROC, wintypes.LPARAM]
_user32.EnumWindows.restype = wintypes.BOOL
_user32.SendMessageTimeoutW.argtypes = [
	wintypes.HWND,
	wintypes.UINT,
	wintypes.WPARAM,
	wintypes.LPARAM,
	wintypes.UINT,
	wintypes.UINT,
	ctypes.POINTER(ctypes.c_size_t),
]
_user32.SendMessageTimeoutW.restype = ctypes.c_ssize_t
_kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
_kernel32.OpenProcess.restype = wintypes.HANDLE
_kernel32.QueryFullProcessImageNameW.argtypes = [
	wintypes.HANDLE,
	wintypes.DWORD,
	wintypes.LPWSTR,
	ctypes.POINTER(wintypes.DWORD),
]
_kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
_kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
_kernel32.CloseHandle.restype = wintypes.BOOL


def _getProcessImageName(processId):
	handle = _kernel32.OpenProcess(_PROCESS_QUERY_LIMITED_INFORMATION, False, processId)
	if not handle:
		return "unavailable"
	try:
		size = wintypes.DWORD(1024)
		buffer = ctypes.create_unicode_buffer(size.value)
		if _kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
			return os.path.basename(buffer.value)
		return "unavailable"
	finally:
		_kernel32.CloseHandle(handle)


def _findNvdaWindows():
	"""Return every top-level window a second nvda.exe could pick, in lookup order.

	Each entry is (hwnd, processId, threadId, imageName, isVisible).
	"""
	candidates = []
	previous = None
	for _ in range(_MAX_CANDIDATES):
		hwnd = _user32.FindWindowExW(None, previous, _NVDA_WINDOW_CLASS, _NVDA_WINDOW_TITLE)
		if not hwnd:
			break
		processId = wintypes.DWORD(0)
		threadId = _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(processId))
		candidates.append(
			(hwnd, processId.value, threadId, _getProcessImageName(processId.value), bool(_user32.IsWindowVisible(hwnd)))
		)
		previous = hwnd
	return candidates


def logLaunchState(stage):
	"""Log how this session was launched and which window a second nvda.exe would target.

	A second nvda.exe (for example from a desktop shortcut hotkey) takes the first window
	of class wxWindowClassNR titled NVDA, posts WM_QUIT to it and waits for its process.
	If that window belongs to another or an already-dying process, the running session
	is never asked to quit.
	"""
	ownPid = os.getpid()
	candidates = []
	try:
		candidates = _findNvdaWindows()
	except OSError:
		logHandler.log.debugWarning("DoctorNVDA: window enumeration failed", exc_info=True)
	ownHwnd = 0
	ownClass = ""
	try:
		ownHwnd = gui.mainFrame.GetHandle()
		ownClass = winUser.getClassName(ownHwnd)
	except (AttributeError, RuntimeError, OSError):
		logHandler.log.debugWarning("DoctorNVDA: could not read the NVDA main window", exc_info=True)
	firstIsOwnProcess = bool(candidates) and candidates[0][1] == ownPid
	nonDaemonThreads = [
		thread.name for thread in threading.enumerate() if not thread.daemon and thread is not threading.main_thread()
	]
	logHandler.log.info(
		f"DoctorNVDA launch probe ({stage}): pid={ownPid} argv={sys.argv[1:]!r} ownFrame={ownHwnd} "
		f"ownClass={ownClass!r} firstTargetIsOwnProcess={firstIsOwnProcess} "
		f"targets(hwnd,pid,tid,image,visible)={candidates!r} nonDaemonThreads={nonDaemonThreads!r}"
	)


def _sendTimed(hwnd, message, wParam):
	"""Send a message to a window of this process without risking an endless wait."""
	result = ctypes.c_size_t(0)
	sent = _user32.SendMessageTimeoutW(
		hwnd, message, wParam, 0, _SMTO_ABORTIFHUNG, _SEND_TIMEOUT_MS, ctypes.byref(result)
	)
	if not sent:
		return None
	return result.value


def _getOwnTopLevelWindows():
	ownPid = os.getpid()
	handles = []

	def collect(hwnd, lParam):
		processId = wintypes.DWORD(0)
		_user32.GetWindowThreadProcessId(hwnd, ctypes.byref(processId))
		if processId.value == ownPid:
			handles.append(hwnd)
		return True

	callback = _WNDENUMPROC(collect)
	_user32.EnumWindows(callback, 0)
	return handles


def clearShortcutHotkey():
	"""Remove the shortcut hotkey that Windows attaches to this session's own window.

	When NVDA is started from a shortcut that has a hotkey, Windows hands the hotkey to the
	first eligible top-level window the process creates (WM_SETHOTKEY). Pressing the hotkey
	then only activates that hidden window instead of starting a second nvda.exe, so the
	shortcut can no longer restart the running session. Clearing the association lets the
	shell start the second instance again.
	"""
	try:
		handles = _getOwnTopLevelWindows()
	except OSError:
		logHandler.log.debugWarning("DoctorNVDA: window enumeration failed", exc_info=True)
		return
	cleared = []
	for hwnd in handles:
		hotkey = _sendTimed(hwnd, _WM_GETHOTKEY, 0)
		if not hotkey:
			continue
		_sendTimed(hwnd, _WM_SETHOTKEY, 0)
		after = _sendTimed(hwnd, _WM_GETHOTKEY, 0)
		cleared.append((hwnd, hex(hotkey), hex(after) if after is not None else "timeout"))
	logHandler.log.info(
		f"DoctorNVDA hotkey cleanup: pid={os.getpid()} ownWindows={len(handles)} "
		f"cleared(hwnd,hotkey,after)={cleared!r}"
	)
