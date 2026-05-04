# init.py
# Copyright (C) 2026 Chai Chaimee
# Licensed under GNU General Public License. See COPYING.txt for details.

import wx
import ui
import tones
import core
import gui
import addonHandler
import globalPluginHandler
import time
from scriptHandler import script
from . import recovery, doctor, menu, recovery_gui, diagnostic, utils

addonHandler.initTranslation()
try:
	_ = addonHandler.getTranslation()
except:
	def _(x): return x

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	def __init__(self):
		super().__init__()
		self._last_tap_time = 0
		self._tap_count = 0
		self._triple_tap_threshold = 0.5
		self._pending_call = None
		core.callLater(3000, self.check_diagnostic_on_startup)

	def check_diagnostic_on_startup(self):
		if diagnostic.load_state():
			core.callLater(500, self.show_safe_dialog)

	def show_safe_dialog(self):
		state = diagnostic.load_state()
		if not state:
			return

		disabled_list = state.get("test_group", [])
		msg = _("Round {round}: {count} add-ons are DISABLED.\n\nIs the problem GONE?").format(
			round=state.get("round", 1),
			count=len(disabled_list)
		)

		def on_response(btn_id):
			if btn_id == wx.ID_YES:
				tones.beep(1000, 100)
				diagnostic.handle_restart_response(symptoms_gone=True)
			elif btn_id == wx.ID_NO:
				tones.beep(600, 100)
				diagnostic.handle_restart_response(symptoms_gone=False)
			else:
				diagnostic.restore_all_and_restart()

		def show():
			diagnostic.NonModalMessageDialog(
				gui.mainFrame,
				msg,
				_("DoctorNVDA Health Check"),
				on_response,
				wx.YES_NO | wx.CANCEL
			).Show()

		wx.CallLater(100, show)

	def _get_flat_menu_items(self):
		items = [
			(_("NVDA Version: {}").format(doctor.get_nvda_version()), "copy_version"),
			(_("Create NVDA Setting Recovery"), "create_rec")
		]
		recs = recovery.get_recovery_list()
		items.append((_("Restore NVDA Setting") if recs else _("Restore NVDA Setting unavailable"), "sub_restore" if recs else "none"))
		items.append((_("Restart NVDA with add-ons disabled"), "restart_safe"))
		ver = doctor.get_nvda_version()
		items.append((_("Restart NVDA {}").format(ver), "restart_normal"))

		if diagnostic.load_state():
			items.append((_("Cancel Add-on Diagnostic and Restore All"), "diag_cancel"))
		else:
			items.append((_("Binary Search Debugging add-on"), "diag_addons"))
		items.append((_("User Config Folder"), "open_user_config"))
		items.append((_("System Info Summary"), "sys_info"))
		return items

	def _menu_callback(self, data):
		if data == "diag_cancel":
			diagnostic.restore_all_and_restart()
		elif data == "diag_addons":
			diagnostic.start_diagnostic_with_confirmation()
		elif data == "sub_restore":
			core.callLater(100, recovery_gui.show_restore_dialog, recovery.get_recovery_list(), recovery.restore_from)
		elif data == "copy_version":
			doctor.copy_version_to_clipboard()
		elif data == "create_rec":
			recovery.create_recovery()
		elif data == "sys_info":
			doctor.copy_sys_info()
		elif data == "restart_safe":
			doctor.restart_nvda()
		elif data == "restart_normal":
			doctor.restart_nvda_normal()
		elif data == "open_user_config":
			utils.open_user_config()

	@script(
		description=_("Single tap: Open DoctorNVDA menu, double tap: Restart NVDA, triple tap: Restart NVDA with add-ons disabled"),
		gesture="kb:alt+windows+d",
		category="DoctorNVDA"
	)
	def script_doctorNVDA_menu(self, gesture):
		current_time = time.time()
		if current_time - self._last_tap_time > self._triple_tap_threshold:
			self._tap_count = 0
		self._tap_count += 1
		self._last_tap_time = current_time

		if self._pending_call is not None:
			self._pending_call.Stop()
			self._pending_call = None

		def execute_action():
			if self._tap_count == 1:
				core.callLater(100, menu.showMenu, self._get_flat_menu_items, self._menu_callback, title=_("DoctorNVDA"))
			elif self._tap_count == 2:
				doctor.restart_nvda_normal()
			elif self._tap_count >= 3:
				doctor.restart_nvda()
			self._tap_count = 0
			self._pending_call = None

		self._pending_call = wx.CallLater(int(self._triple_tap_threshold * 1000), execute_action)