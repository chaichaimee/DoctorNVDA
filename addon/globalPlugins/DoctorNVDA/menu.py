# menu.py

import wx
import addonHandler
import tones
import gui

addonHandler.initTranslation()
try:
	_ = addonHandler.getTranslation()
except:
	def _(x): return x

_instance = None

class DoctorMenu(wx.Frame):
	def __init__(self, items_func, callback, title=_("DoctorNVDA Menu")):
		super(DoctorMenu, self).__init__(
			gui.mainFrame, 
			title=title, 
			size=(450, 400),
			style=wx.DEFAULT_FRAME_STYLE | wx.STAY_ON_TOP
		)
		self.items_func = items_func
		self.callback = callback

		panel = wx.Panel(self)
		vbox = wx.BoxSizer(wx.VERTICAL)

		self.list_box = wx.ListBox(panel, style=wx.LB_SINGLE)
		vbox.Add(self.list_box, 1, wx.EXPAND | wx.ALL, 15)
		panel.SetSizer(vbox)

		self.refresh_list()

		self.list_box.Bind(wx.EVT_LISTBOX_DCLICK, self.on_select)
		self.list_box.Bind(wx.EVT_CHAR_HOOK, self.on_key)
		
		# Auto-close timer (15 seconds)
		self.timer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.on_timeout, self.timer)
		self.timer.Start(15000)

		self.Bind(wx.EVT_CLOSE, self.on_close)
		self.CenterOnScreen()
		self.Show()
		self.Raise()

	def refresh_list(self):
		raw_items = self.items_func()
		self.current_items = raw_items
		self.list_box.Clear()
		self.list_box.AppendItems([item[0] for item in raw_items])
		if self.list_box.GetCount() > 0:
			self.list_box.SetSelection(0)
		self.list_box.SetFocus()

	def on_select(self, event):
		idx = self.list_box.GetSelection()
		if idx != wx.NOT_FOUND:
			data = self.current_items[idx][1]
			# Use CallAfter to ensure the callback runs after the menu is fully closed
			wx.CallAfter(self.callback, data)
			self.Close()

	def on_key(self, event):
		self.timer.Start(15000) # Reset timer on any key press
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
	global _instance
	if _instance:
		_instance.Close()
	_instance = DoctorMenu(items_func, callback, title)