# menu.py

import time
import wx
import addonHandler
import controlTypes
import logHandler
import tones
import gui

addonHandler.initTranslation()
try:
	_ = addonHandler.getTranslation()
except Exception:
	def _(x): return x

_instance = None
_OPEN_SUPPRESS_SECONDS = 1.5
_suppressUntil = 0.0
_suppressedTitle = ""

def _normalizeText(text):
	return " ".join(text.casefold().split())

def _getDialogRoleLabel():
	try:
		return controlTypes.Role.DIALOG.displayString
	except AttributeError:
		logHandler.log.debug("DoctorNVDA: dialog role label is unavailable")
		return ""

def _isDialogAnnouncement(text, titleKey, roleKey):
	remainder = _normalizeText(text)
	if not remainder:
		return False
	for part in (titleKey, roleKey):
		if part:
			remainder = remainder.replace(part, " ")
	return not remainder.strip(" ,.:;")

def filterOpeningSpeech(speechSequence=None, *args, **kwargs):
	if not speechSequence or time.monotonic() >= _suppressUntil:
		return speechSequence
	titleKey = _normalizeText(_suppressedTitle)
	roleKey = _normalizeText(_getDialogRoleLabel())
	filtered = []
	wasDropped = False
	for entry in speechSequence:
		if isinstance(entry, str) and _isDialogAnnouncement(entry, titleKey, roleKey):
			wasDropped = True
			logHandler.log.debug("DoctorNVDA: dropped dialog announcement %r", entry)
			continue
		filtered.append(entry)
	if not wasDropped:
		return speechSequence
	return filtered

class DoctorMenu(wx.Dialog):
	def __init__(self, items_func, callback, title=_("DoctorNVDA Menu")):
		super(DoctorMenu, self).__init__(
			gui.mainFrame,
			title=title,
			size=(450, 400),
			style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
		)
		self.items_func = items_func
		self.callback = callback

		panel = wx.Panel(self)
		vbox = wx.BoxSizer(wx.VERTICAL)

		self.list_box = wx.ListBox(panel, style=wx.LB_SINGLE)
		vbox.Add(self.list_box, 1, wx.EXPAND | wx.ALL, 15)
		panel.SetSizer(vbox)

		self.list_box.Bind(wx.EVT_LISTBOX_DCLICK, self.on_select)
		self.list_box.Bind(wx.EVT_CHAR_HOOK, self.on_key)

		self.timer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.on_timeout, self.timer)
		self.timer.Start(15000)

		self.Bind(wx.EVT_CLOSE, self.on_close)
		self.CenterOnScreen()
		self.refresh_list()
		self.Show()
		self.Raise()
		self.list_box.SetFocus()

	def refresh_list(self):
		try:
			raw_items = self.items_func()
			self.current_items = raw_items
			self.list_box.Clear()
			self.list_box.AppendItems([item[0] for item in raw_items])
			if self.list_box.GetCount() > 0:
				self.list_box.SetSelection(0)
			self.list_box.SetFocus()
		except Exception:
			self.Close()
			raise

	def on_select(self, event):
		idx = self.list_box.GetSelection()
		if idx != wx.NOT_FOUND:
			data = self.current_items[idx][1]
			wx.CallAfter(self.callback, data)
			self.Close()

	def on_key(self, event):
		self.timer.Start(15000)
		key = event.GetKeyCode()
		if key == wx.WXK_RETURN:
			self.on_select(None)
		elif key == wx.WXK_ESCAPE:
			self.Close()
		else:
			event.Skip()

	def on_timeout(self, event):
		tones.beep(100, 100)
		self.Close()

	def on_close(self, event):
		global _instance
		self.timer.Stop()
		_instance = None
		self.Destroy()

def showMenu(items_func, callback, title=_("DoctorNVDA Menu")):
	global _instance, _suppressUntil, _suppressedTitle
	if _instance:
		_instance.Close()
	_suppressedTitle = title
	_suppressUntil = time.monotonic() + _OPEN_SUPPRESS_SECONDS
	_instance = DoctorMenu(items_func, callback, title)

def closeMenu():
	global _suppressUntil
	_suppressUntil = 0.0
	if not _instance:
		return
	try:
		_instance.Close()
	except RuntimeError:
		logHandler.log.debug("DoctorNVDA: menu window was already destroyed")
