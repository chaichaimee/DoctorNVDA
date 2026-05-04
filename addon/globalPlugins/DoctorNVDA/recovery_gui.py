# recovery_gui.py
# Copyright (C) 2026 Chai Chaimee
# Licensed under GNU General Public License. See COPYING.txt for details.

import wx
import os
import shutil
import core
import addonHandler
import ui
import gui
from . import recovery

addonHandler.initTranslation()
try:
	_ = addonHandler.getTranslation()
except:
	def _(x): return x

_active_frame = None

class RestoreFrame(wx.Frame):
	def __init__(self, parent, folders, restore_callback):
		global _active_frame
		if _active_frame:
			try:
				_active_frame.Close()
			except:
				pass
		super().__init__(parent, title=_("Select Recovery Folder"), size=(500, 400),
						 style=wx.DEFAULT_FRAME_STYLE | wx.STAY_ON_TOP)
		self.restore_callback = restore_callback
		self.folders = folders
		_active_frame = self

		panel = wx.Panel(self)
		vbox = wx.BoxSizer(wx.VERTICAL)

		# Use ListBox instead of ListCtrl for simplicity and stability
		self.list_box = wx.ListBox(panel, style=wx.LB_SINGLE)
		vbox.Add(self.list_box, 1, wx.EXPAND | wx.ALL, 10)

		btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
		restore_btn = wx.Button(panel, wx.ID_OK, _("Restore"))
		restore_btn.Bind(wx.EVT_BUTTON, self.on_restore)
		remove_all_btn = wx.Button(panel, wx.ID_ANY, _("Remove All"))
		remove_all_btn.Bind(wx.EVT_BUTTON, self.on_remove_all)
		cancel_btn = wx.Button(panel, wx.ID_CANCEL, _("Cancel"))
		cancel_btn.Bind(wx.EVT_BUTTON, self.on_cancel)
		btn_sizer.Add(restore_btn, 0, wx.ALL, 5)
		btn_sizer.Add(remove_all_btn, 0, wx.ALL, 5)
		btn_sizer.Add(cancel_btn, 0, wx.ALL, 5)
		vbox.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)

		panel.SetSizer(vbox)

		self.refresh_list()

		self.list_box.Bind(wx.EVT_LISTBOX_DCLICK, self.on_restore)
		self.list_box.Bind(wx.EVT_CHAR_HOOK, self.on_key_down)

		self.Bind(wx.EVT_CLOSE, self.on_close)

		self.CentreOnParent()
		self.Raise()
		wx.CallLater(100, self._set_initial_focus)

	def refresh_list(self):
		self.list_box.Clear()
		if not self.folders:
			self.list_box.Append(_("(No recovery points available)"))
			return
		for folder in self.folders:
			self.list_box.Append(folder)

	def get_selected_folder(self):
		idx = self.list_box.GetSelection()
		if idx == wx.NOT_FOUND or not self.folders:
			return None
		try:
			return self.folders[idx]
		except IndexError:
			return None

	def on_restore(self, event):
		folder = self.get_selected_folder()
		if not folder:
			wx.MessageBox(_("Please select a recovery folder first."), _("No selection"), wx.OK | wx.ICON_WARNING)
			return
		self.restore_callback(folder)
		self.Close()

	def on_remove_all(self, event):
		if wx.MessageBox(_("Are you sure you want to remove all recovery points?"),
						 _("Confirm remove all"), wx.YES_NO | wx.ICON_QUESTION) == wx.YES:
			recovery.remove_all_recoveries()
			self.folders = []
			self.refresh_list()
			ui.message(_("All recoveries removed"))

	def on_cancel(self, event):
		self.Close()

	def on_key_down(self, event):
		key = event.GetKeyCode()
		if key == wx.WXK_DELETE:
			self.delete_selected()
		elif key == wx.WXK_ESCAPE:
			self.Close()
		else:
			event.Skip()

	def delete_selected(self):
		folder = self.get_selected_folder()
		if not folder:
			return
		if wx.MessageBox(_("Are you sure you want to delete {}?").format(folder),
						 _("Confirm delete"), wx.YES_NO | wx.ICON_QUESTION) == wx.YES:
			try:
				full_path = os.path.join(recovery.get_recovery_base_path(), folder)
				shutil.rmtree(full_path)
				idx = self.list_box.GetSelection()
				self.folders.pop(idx)
				self.refresh_list()
				ui.message(_("Deleted."))
				if self.folders:
					self.list_box.SetSelection(0 if idx == 0 else idx - 1)
				else:
					self.refresh_list()
			except Exception as e:
				wx.MessageBox(_("Error deleting: {}").format(str(e)), _("Error"), wx.OK | wx.ICON_ERROR)

	def on_close(self, event):
		global _active_frame
		_active_frame = None
		self.Destroy()

	def _set_initial_focus(self):
		if self.list_box.GetCount() == 0:
			return
		self.list_box.SetFocus()
		if self.folders:
			self.list_box.SetSelection(0)
		self.Raise()


def show_restore_dialog(folders, restore_callback):
	if not folders:
		ui.message(_("No recovery points available. Create a recovery first."))
		return
	wx.CallAfter(RestoreFrame, gui.mainFrame, folders, restore_callback)