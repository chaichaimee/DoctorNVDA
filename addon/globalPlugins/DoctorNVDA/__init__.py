# __init__.py
# Copyright (C) 2026 Chai Chaimee
# Licensed under GNU General Public License. See COPYING.txt for details.

import wx
import ui
import tones
import core
import gui
import addonHandler
import globalPluginHandler
from . import recovery, doctor, menu, recovery_gui, diagnostic

addonHandler.initTranslation()
try:
	_ = addonHandler.getTranslation()
except:
	def _(x): return x

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	def __init__(self):
		super().__init__()
		core.callLater(3000, self.check_diagnostic_on_startup)

	def check_diagnostic_on_startup(self):
		if diagnostic.load_state():
			wx.CallAfter(self.show_safe_dialog)

	def show_safe_dialog(self):
		state = diagnostic.load_state()
		if not state: return

		disabled_list = state.get("test_group", [])
		msg = _("Round {round}: {count} add-ons are DISABLED.\n\nIs the problem GONE?").format(
			round=state.get("round", 1),
			count=len(disabled_list)
		)

		# Use AccessibleMessageDialog which NVDA will read entirely
		dlg = diagnostic.AccessibleMessageDialog(
			gui.mainFrame,
			msg,
			_("DoctorNVDA Health Check"),
			style=wx.YES_NO | wx.CANCEL
		)
		result = dlg.ShowModal()
		dlg.Destroy()

		if result == wx.ID_YES:
			tones.beep(1000, 100)
			diagnostic.handle_restart_response(symptoms_gone=True)
		elif result == wx.ID_NO:
			tones.beep(600, 100)
			diagnostic.handle_restart_response(symptoms_gone=False)
		else:  # wx.ID_CANCEL
			diagnostic.restore_all_and_restart()

	def _get_flat_menu_items(self):
		items = [
			(_("NVDA Version: {}").format(doctor.get_nvda_version()), "copy_version"),
			(_("Create NVDA Setting Recovery"), "create_rec")
		]
		recs = recovery.get_recovery_list()
		items.append((_("Restore NVDA Setting") if recs else _("Restore NVDA Setting unavailable"), "sub_restore" if recs else "none"))
		items.append((_("Restart NVDA with add-ons disabled"), "restart_safe"))

		if diagnostic.load_state():
			items.append((_("Cancel Add-on Diagnostic and Restore All"), "diag_cancel"))
		else:
			items.append((_("Binary Search Debugging add-on"), "diag_addons"))

		# Insert Check Ram here
		items.append((_("Check Ram"), "check_ram"))
		items.append((_("System Info Summary"), "sys_info"))
		return items

	def _menu_callback(self, data):
		if data == "diag_cancel": diagnostic.restore_all_and_restart()
		elif data == "diag_addons": diagnostic.start_diagnostic_with_confirmation()
		elif data == "sub_restore": wx.CallAfter(recovery_gui.show_restore_dialog, recovery.get_recovery_list(), recovery.restore_from)
		elif data == "copy_version": doctor.copy_version_to_clipboard()
		elif data == "create_rec": recovery.create_recovery()
		elif data == "sys_info": doctor.copy_sys_info()
		elif data == "restart_safe": doctor.restart_nvda()
		elif data == "check_ram": doctor.copy_ram_info()  # New handler

	def script_doctorNVDA_menu(self, gesture):
		wx.CallAfter(menu.showMenu, self._get_flat_menu_items, self._menu_callback, title=_("DoctorNVDA"))

	__gestures = {"kb:alt+windows+d": "doctorNVDA_menu"}