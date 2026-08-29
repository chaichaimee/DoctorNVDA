# audio_reset.py

import core
import config
import tones
import ui
import addonHandler
import logHandler

addonHandler.initTranslation()
try:
	_ = addonHandler.getTranslation()
except:
	def _(x): return x


def reinit_audio_subsystem():
	"""Force the current speech synthesizer, and the audio stream it owns,
	to terminate and reinitialize. Intended as an emergency recovery action
	for when speech has gone silent or the synth driver has stopped
	responding, without requiring a full NVDA restart.

	synthDriverHandler.setSynth() must run on NVDA's main thread: SAPI5 and
	other synth drivers depend on COM objects that are apartment-bound to
	the thread that created them. Switching synths from a worker thread
	corrupts that COM state and permanently deadlocks the synth's own
	speak thread instead of recovering it (confirmed via NVDA's Watchdog
	freeze-recovery stack dump, which showed the SAPI5 speak thread
	deadlocked shortly after setSynth ran on a worker thread).
	"""
	tones.beep(500, 80)
	core.callLater(50, _do_reinit_on_main_thread)


def _do_reinit_on_main_thread():
	try:
		import synthDriverHandler
		current_synth = synthDriverHandler.getSynth()
		synth_name = current_synth.name if current_synth else config.conf["speech"]["synth"]
		synthDriverHandler.setSynth(synth_name)
	except Exception:
		logHandler.log.exception("Emergency audio reset failed")
		tones.beep(200, 300)
		ui.message(_("Audio reset failed. Check NVDA log."))
		return

	tones.beep(1200, 100)
	ui.message(_("Audio subsystem reset complete"))
