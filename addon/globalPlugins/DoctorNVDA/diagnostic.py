# diagnostic.py

import os
import json
import wx
import addonHandler
import core
import ui
import gui
import config
import tones
from globalVars import appArgs

addonHandler.initTranslation()
try:
	_ = addonHandler.getTranslation()
except:
	def _(x): return x

STATE_FILE = os.path.join(appArgs.configPath, "ChaiChaimee", "DoctorNVDA", "diagnostic_state.json")
MY_ADDON_INTERNAL = "DoctorNVDA"  # Must match this addon's folder name

class AccessibleMessageDialog(wx.Dialog):
	"""
	Dialog that NVDA will read the full message by focusing on a read-only TextCtrl
	and always stays on top.
	"""
	def __init__(self, parent, message, title, style=wx.YES_NO | wx.CANCEL):
		super().__init__(parent, title=title, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.STAY_ON_TOP)
		self.message = message
		self.style = style

		panel = wx.Panel(self)
		sizer = wx.BoxSizer(wx.VERTICAL)

		# Use read-only TextCtrl so it can receive focus and NVDA reads the message
		self.text_ctrl = wx.TextCtrl(
			panel,
			value=message,
			style=wx.TE_READONLY | wx.TE_MULTILINE | wx.TE_NO_VSCROLL,
			size=(400, -1)
		)
		self.text_ctrl.SetBackgroundColour(panel.GetBackgroundColour())  # Blend in
		sizer.Add(self.text_ctrl, 1, wx.EXPAND | wx.ALL, 15)

		# Separator line
		sizer.Add(wx.StaticLine(panel), 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

		# Buttons according to style
		btnSizer = wx.BoxSizer(wx.HORIZONTAL)
		buttons = []
		if style & wx.YES:
			yesBtn = wx.Button(panel, wx.ID_YES, _("&Yes"))
			buttons.append(yesBtn)
		if style & wx.NO:
			noBtn = wx.Button(panel, wx.ID_NO, _("&No"))
			buttons.append(noBtn)
		if style & wx.CANCEL:
			cancelBtn = wx.Button(panel, wx.ID_CANCEL, _("&Cancel"))
			buttons.append(cancelBtn)
		if style & wx.OK:
			okBtn = wx.Button(panel, wx.ID_OK, _("&OK"))
			buttons.append(okBtn)

		for btn in buttons:
			btnSizer.Add(btn, 0, wx.ALL, 5)
			btn.Bind(wx.EVT_BUTTON, self.onButton)

		sizer.Add(btnSizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)

		panel.SetSizer(sizer)
		sizer.Fit(self)

		# Set focus to TextCtrl so NVDA reads the message immediately
		self.text_ctrl.SetFocus()

		self.CentreOnParent()
		self.Raise()  # Ensure it stays on top

	def onButton(self, event):
		btn_id = event.GetId()
		self.EndModal(btn_id)

def apply_addon_states(to_disable_list, original_active):
	"""Enable/disable add-ons using addon.enable() which automatically saves to config"""
	addons = addonHandler.getAvailableAddons()
	addon_dict = {a.name: a for a in addons}

	# Disable according to to_disable_list
	for name in to_disable_list:
		if name in addon_dict and name != MY_ADDON_INTERNAL:
			addon_dict[name].enable(False)  # disable

	# Enable according to original_active that are not in to_disable_list
	for name in original_active:
		if name in addon_dict and name not in to_disable_list and name != MY_ADDON_INTERNAL:
			addon_dict[name].enable(True)   # enable

	# Always keep this addon enabled
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
		# No state or cancelled without starting diagnostic
		core.restart()

def start_diagnostic_with_confirmation():
	active_addons = [a.name for a in addonHandler.getAvailableAddons() if a.isRunning and a.name != MY_ADDON_INTERNAL]

	if not active_addons:
		ui.message(_("No active add-ons found to diagnose."))
		return

	# Use AccessibleMessageDialog so NVDA reads the message
	dlg = AccessibleMessageDialog(
		gui.mainFrame,
		_("Ready to start diagnostic? NVDA will restart and disable half of your active add-ons."),
		_("DoctorNVDA"),
		style=wx.YES_NO | wx.CANCEL
	)
	result = dlg.ShowModal()
	dlg.Destroy()

	if result == wx.ID_YES:
		tones.beep(880, 200)
		state = {
			"original_active": active_addons,
			"candidates": active_addons,
			"round": 1
		}
		save_state(state)
		run_diagnostic_round(state)
	# No or Cancel do nothing

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
	if not state: return

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

	wx.CallAfter(gui.mainFrame.Raise)
	core.callLater(1000, ui.message, _("Diagnostic complete. Found and disabled: {name}").format(name=culprit_display))