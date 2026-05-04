# diagnostic.py
# Copyright (C) 2026 Chai Chaimee
# Licensed under GNU General Public License. See COPYING.txt for details.

import os
import json
import wx
import core
import gui
import addonHandler
import ui
import config
import tones
from globalVars import appArgs

addonHandler.initTranslation()
try:
	_ = addonHandler.getTranslation()
except:
	def _(x): return x

STATE_FILE = os.path.join(appArgs.configPath, "ChaiChaimee", "DoctorNVDA", "diagnostic_state.json")
MY_ADDON_INTERNAL = "DoctorNVDA"

def apply_addon_states(to_disable_list, original_active):
	addons = addonHandler.getAvailableAddons()
	addon_dict = {a.name: a for a in addons}
	for name in to_disable_list:
		if name in addon_dict and name != MY_ADDON_INTERNAL:
			addon_dict[name].enable(False)
	for name in original_active:
		if name in addon_dict and name not in to_disable_list and name != MY_ADDON_INTERNAL:
			addon_dict[name].enable(True)
	if MY_ADDON_INTERNAL in addon_dict:
		addon_dict[MY_ADDON_INTERNAL].enable(True)
	config.conf.save()

def save_state(state):
	path = os.path.dirname(STATE_FILE)
	if not os.path.exists(path):
		os.makedirs(path)
	with open(STATE_FILE, 'w', encoding='utf-8') as f:
		json.dump(state, f)

def load_state():
	if os.path.exists(STATE_FILE):
		try:
			with open(STATE_FILE, 'r', encoding='utf-8') as f:
				return json.load(f)
		except:
			return None
	return None

def clear_state():
	if os.path.exists(STATE_FILE):
		try:
			os.remove(STATE_FILE)
		except:
			pass

def restore_all_and_restart():
	state = load_state()
	if state and "original_active" in state:
		tones.beep(440, 200)
		original_active = state["original_active"]
		addons = addonHandler.getAvailableAddons()
		addon_dict = {a.name: a for a in addons}
		for name, addon in addon_dict.items():
			if name == MY_ADDON_INTERNAL:
				addon.enable(True)
			else:
				addon.enable(name in original_active)
		config.conf.save()
		clear_state()
		core.restart()
	else:
		core.restart()

def start_diagnostic_with_confirmation():
	active_addons = [a.name for a in addonHandler.getAvailableAddons() if a.isRunning and a.name != MY_ADDON_INTERNAL]
	if not active_addons:
		ui.message(_("No active add-ons found to diagnose."))
		return

	def on_response(btn_id):
		if btn_id == wx.ID_YES:
			tones.beep(880, 200)
			state = {
				"original_active": active_addons,
				"candidates": active_addons,
				"round": 1
			}
			save_state(state)
			run_diagnostic_round(state)

	def show_dialog():
		NonModalMessageDialog(
			gui.mainFrame,
			_("Ready to start diagnostic? NVDA will restart and disable half of your active add-ons."),
			_("DoctorNVDA"),
			on_response,
			wx.YES_NO | wx.CANCEL
		).Show()

	wx.CallLater(100, show_dialog)

def run_diagnostic_round(state):
	candidates = state["candidates"]
	if len(candidates) == 1:
		finalize_diagnostic(candidates[0], state["original_active"])
		return

	mid = len(candidates) // 2
	test_group = candidates[:mid]
	state["test_group"] = test_group
	save_state(state)

	apply_addon_states(test_group, state["original_active"])
	core.restart()

def handle_restart_response(symptoms_gone):
	state = load_state()
	if not state:
		return

	if symptoms_gone:
		state["candidates"] = state["test_group"]
	else:
		test_group = state.get("test_group", [])
		state["candidates"] = [c for c in state["candidates"] if c not in test_group]

	state["round"] += 1
	run_diagnostic_round(state)

def finalize_diagnostic(culprit, original_active):
	tones.beep(1320, 500)
	apply_addon_states([culprit], original_active)
	clear_state()

	addons = {a.name: a.manifest['name'] for a in addonHandler.getAvailableAddons()}
	culprit_display = addons.get(culprit, culprit)

	core.callLater(100, gui.mainFrame.Raise)
	core.callLater(1000, ui.message, _("Diagnostic complete. Found and disabled: {name}").format(name=culprit_display))

class NonModalMessageDialog(wx.Dialog):
	def __init__(self, parent, message, title, callback, style=wx.OK):
		super().__init__(parent, title=title, style=wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP)
		self.callback = callback

		panel = wx.Panel(self)
		sizer = wx.BoxSizer(wx.VERTICAL)

		msg_text = wx.StaticText(panel, label=message)
		sizer.Add(msg_text, 1, wx.EXPAND | wx.ALL, 15)

		btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
		buttons = []
		if style & wx.YES:
			btn = wx.Button(panel, wx.ID_YES, _("&Yes"))
			btn.Bind(wx.EVT_BUTTON, self.on_button)
			buttons.append(btn)
		if style & wx.NO:
			btn = wx.Button(panel, wx.ID_NO, _("&No"))
			btn.Bind(wx.EVT_BUTTON, self.on_button)
			buttons.append(btn)
		if style & wx.CANCEL:
			btn = wx.Button(panel, wx.ID_CANCEL, _("&Cancel"))
			btn.Bind(wx.EVT_BUTTON, self.on_button)
			buttons.append(btn)
		if style & wx.OK:
			btn = wx.Button(panel, wx.ID_OK, _("&OK"))
			btn.Bind(wx.EVT_BUTTON, self.on_button)
			buttons.append(btn)

		for btn in buttons:
			btn_sizer.Add(btn, 0, wx.ALL, 5)

		sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)
		panel.SetSizer(sizer)
		sizer.Fit(self)
		self.CentreOnParent()
		self.Raise()
		core.callLater(100, self._setFocus)

	def _setFocus(self):
		try:
			self.SetFocus()
		except:
			pass

	def on_button(self, event):
		btn_id = event.GetId()
		self.Destroy()
		if self.callback:
			self.callback(btn_id)