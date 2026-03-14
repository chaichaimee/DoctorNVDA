# recovery_gui.py
import wx
import os
import shutil
import addonHandler
import ui
import gui
from . import recovery

addonHandler.initTranslation()
try:
	_ = addonHandler.getTranslation()
except:
	def _(x): return x

class RestoreDialog(wx.Dialog):
	def __init__(self, parent, folders, restore_callback):
		super().__init__(parent, title=_("Select Recovery Folder"), size=(450, 350),
						 style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.STAY_ON_TOP)
		self.folders = folders
		self.restore_callback = restore_callback
		self.selected_folder = None

		panel = wx.Panel(self)
		sizer = wx.BoxSizer(wx.VERTICAL)

		# Create ListCtrl in report mode
		self.listCtrl = wx.ListCtrl(panel, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
		self.listCtrl.AppendColumn(_("Recovery Folder"), width=350)
		self.refresh_list()

		sizer.Add(self.listCtrl, 1, wx.EXPAND | wx.ALL, 5)

		btnSizer = wx.BoxSizer(wx.HORIZONTAL)
		restoreBtn = wx.Button(panel, wx.ID_OK, _("Restore"))
		restoreBtn.Bind(wx.EVT_BUTTON, self.onRestore)
		removeAllBtn = wx.Button(panel, wx.ID_ANY, _("Remove All"))
		removeAllBtn.Bind(wx.EVT_BUTTON, self.onRemoveAll)
		cancelBtn = wx.Button(panel, wx.ID_CANCEL, _("Cancel"))
		btnSizer.Add(restoreBtn, 0, wx.ALL, 5)
		btnSizer.Add(removeAllBtn, 0, wx.ALL, 5)
		btnSizer.Add(cancelBtn, 0, wx.ALL, 5)
		sizer.Add(btnSizer, 0, wx.ALIGN_CENTER)

		panel.SetSizer(sizer)

		self.listCtrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.onRestore)
		self.listCtrl.Bind(wx.EVT_KEY_DOWN, self.onKeyDown)
		self.listCtrl.Bind(wx.EVT_RIGHT_DOWN, self.onRightClick)

		self.CentreOnParent()
		self.Raise()  # Ensure it stays on top

	def refresh_list(self):
		self.listCtrl.DeleteAllItems()
		for folder in self.folders:
			index = self.listCtrl.GetItemCount()
			self.listCtrl.InsertItem(index, os.path.basename(folder))

	def getSelectedFolder(self):
		index = self.listCtrl.GetFirstSelected()
		if index == -1:
			return None
		return self.folders[index]

	def onRestore(self, event):
		folder = self.getSelectedFolder()
		if folder:
			self.selected_folder = folder
			self.EndModal(wx.ID_OK)
		else:
			wx.MessageBox(_("Please select a folder."), _("No selection"), wx.OK | wx.ICON_WARNING)

	def onRemoveAll(self, event):
		if wx.MessageBox(_("Are you sure you want to remove all recovery points?"),
						 _("Confirm remove all"), wx.YES_NO | wx.ICON_QUESTION) == wx.YES:
			recovery.remove_all_recoveries()
			self.folders = []
			self.refresh_list()
			ui.message(_("All recoveries removed"))

	def onKeyDown(self, event):
		key = event.GetKeyCode()
		if key == wx.WXK_DELETE:
			self.deleteSelected()
		else:
			event.Skip()

	def onRightClick(self, event):
		# Find clicked position
		pos = event.GetPosition()
		index = self.listCtrl.HitTest(pos)[0]  # HitTest returns (item, flags)
		if index != -1:
			self.listCtrl.Select(index)
			self.showDeletePopup(event.GetPosition())
		else:
			event.Skip()

	def showDeletePopup(self, pos):
		menu = wx.Menu()
		deleteItem = menu.Append(wx.ID_ANY, _("Delete"))
		self.Bind(wx.EVT_MENU, self.onDeletePopup, deleteItem)
		self.PopupMenu(menu, pos)
		menu.Destroy()

	def onDeletePopup(self, event):
		self.deleteSelected()

	def deleteSelected(self):
		folder = self.getSelectedFolder()
		if not folder:
			return
		if wx.MessageBox(_("Are you sure you want to delete {}?").format(os.path.basename(folder)),
						 _("Confirm delete"), wx.YES_NO | wx.ICON_QUESTION) == wx.YES:
			try:
				# Construct full path using recovery base path
				full_path = os.path.join(recovery.get_recovery_base_path(), folder)
				shutil.rmtree(full_path)
				index = self.listCtrl.GetFirstSelected()
				self.listCtrl.DeleteItem(index)
				self.folders.pop(index)
				ui.message(_("Deleted."))
			except Exception as e:
				wx.MessageBox(_("Error deleting: {}").format(str(e)), _("Error"), wx.OK | wx.ICON_ERROR)

def show_restore_dialog(folders, restore_callback):
	dialog = RestoreDialog(gui.mainFrame, folders, restore_callback)
	if dialog.ShowModal() == wx.ID_OK:
		selected = dialog.selected_folder
		dialog.Destroy()
		if selected:
			restore_callback(selected)
	else:
		dialog.Destroy()