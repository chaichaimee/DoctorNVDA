![NVDA Logo](https://www.nvaccess.org/files/nvda/documentation/userGuide/images/nvda.ico)

# DoctorNVDA

Diagnose, repair, and recover NVDA, so your screen reader keeps working when it matters most.

**author:** chai chaimee

**url:** https://github.com/chaichaimee/DoctorNVDA

## Introduction

DoctorNVDA is a first-aid kit for your screen reader. When NVDA falls silent, freezes, crashes, or starts behaving strangely after you install an add-on, DoctorNVDA gives you simple tools to find out what went wrong and to put things right, all without leaving the keyboard.

It can revive a silent speech synthesizer in one key press, read NVDA's log files and explain the problems in plain language, track down a faulty add-on by switching add-ons off in rounds, back up and restore your NVDA settings, copy details about your computer, and clear out leftover cache and temporary files.

Everything is available from one menu, and the two most urgent actions have their own hotkeys.

## Hot Keys

**Alt+Windows+D**

- Single Tap : Open the DoctorNVDA menu
- Double Tap : Restart NVDA
- Triple Tap : Restart NVDA with add-ons disabled

**Alt+Windows+R**

- Single Tap : Emergency Synthesizer Reboot
- Double Tap : Crash Log Analyzer

## Features

### The DoctorNVDA Menu

Press Alt+Windows+D once to open a list of every tool in the add-on. Move through the list with the Up and Down arrow keys, press Enter (or double-click) to run the selected item, and press Escape to close the menu. The menu also closes by itself after a period without any key press.

The menu contains these items, in this order:

- **NVDA Version** : shows your NVDA version. Press Enter to copy it to the clipboard.
- **Create NVDA Setting Recovery** : back up your settings.
- **Restore NVDA Setting** : restore a saved backup. It reads "Restore NVDA Setting unavailable" until you have created at least one backup.
- **Restart NVDA with add-ons disabled**
- **Restart NVDA** : restart normally.
- **Binary Search Debugging add-on** : find a faulty add-on. While a search is in progress, this item changes to **Cancel Add-on Diagnostic and Restore All**.
- **Emergency Synthesizer Reboot**
- **Crash Log Analyzer**
- **User Config Folder**
- **System Info Summary**
- **Clean Add-on Caches**
- **Clean NVDA Temp Files**

### Emergency Synthesizer Reboot

If speech suddenly goes silent, or the synthesizer or its audio output stops responding, this tool forces the current speech synthesizer to shut down and start again, without restarting the whole of NVDA.

Press Alt+Windows+R once. You hear a short beep when the reset begins. When it succeeds, a higher beep sounds and NVDA says "Audio subsystem reset complete". If it fails, you hear a low beep and a message telling you to check the NVDA log.

### Restart Options

You can restart NVDA straight from the keyboard, without opening any dialog:

- Press Alt+Windows+D twice to restart NVDA normally.
- Press Alt+Windows+D three times to restart NVDA with all add-ons disabled. This is useful for checking whether a problem comes from NVDA itself or from an add-on.

The same two restarts are also available from the menu.

### Crash Log Analyzer

The Crash Log Analyzer reads NVDA's current log and the log from your previous session, then opens a plain-language report in a text file. It is written for people who do not read log files, and it explains each finding in everyday words.

Run it at any time by pressing Alt+Windows+R twice, or by choosing Crash Log Analyzer from the menu.

**What the report contains**

- **A health summary** : NVDA health is described as good, mostly good with minor issues, or needing attention, followed by the number of serious problems, warnings, harmless notices, and add-on errors.
- **Add-on errors** : for each error caused by an add-on, the report names the add-on, the file, the line, and the error.
- **NVDA health findings** : each finding shows its severity (Serious problem, Warning, or Harmless notice), what the problem is, where it happened, what it means, and what you can do about it. Repeated problems are listed once with the number of times they occurred.

**What it looks for**

- Moments when NVDA stopped responding, how long they lasted, and which add-on or program was involved. If a freeze points to an add-on, the report suggests using Binary Search Debugging to confirm it.
- Slow NVDA startups.
- Slow window switching and incomplete accessibility information from a program.
- Add-ons that use outdated NVDA or Python features and may stop working after a future update.
- Errors and warnings reported by add-ons or by NVDA, with a plain explanation of the kind of error.
- Whether the previous session ended unexpectedly, such as after a crash or a forced close.

**Automatic check after a crash**

A few seconds after NVDA starts, DoctorNVDA quietly checks the previous session's log. If that session ended in a crash, the report opens automatically. A normal restart never opens a report by itself, and the same log is never reported twice.

If no problems are found, NVDA says so. When NVDA's Logging Level is not set to Debug, the message also suggests setting it to Debug in General Settings for more thorough detection. If no log file can be found, NVDA says "Log file not found."

**Note:** The report is saved as CrashReport.txt inside the DoctorNVDA folder in your NVDA user configuration folder. Each new report replaces the previous one.

### Binary Search Debugging

When something is wrong with NVDA and you suspect an add-on but do not know which one, this tool finds it for you. Instead of disabling add-ons one at a time, it disables half of them, restarts NVDA, and asks whether the problem is still there. Each answer cuts the list of suspects in half until only one add-on remains. DoctorNVDA itself is never disabled during the search.

**Step-by-step**

1. Open the DoctorNVDA menu with Alt+Windows+D and choose **Binary Search Debugging add-on**. If there are no active add-ons, NVDA tells you there is nothing to diagnose.
2. A confirmation dialog explains that NVDA will restart and disable half of your active add-ons. Choose **Yes** to begin. Choosing No or Cancel leaves everything unchanged.
3. NVDA restarts with the first group of add-ons disabled.
4. After the restart, a dialog titled DoctorNVDA Health Check opens. It reads "Round" followed by the round number and the number of add-ons that are disabled, with the names of those add-ons listed. You can read it with the arrow keys.
5. Test NVDA and check whether the problem you were seeing has gone, then answer in the dialog:
   - **Yes** : the problem is gone. The disabled add-ons are the suspects, and the others are cleared.
   - **No** : the problem is still there. The disabled add-ons are cleared, and the add-ons that were still running are the suspects.
   - **Cancel** : stop the search, turn all of your add-ons back on as they were, and restart NVDA.
6. After Yes or No, NVDA restarts with a smaller group of suspects disabled, and the dialog appears again for the next round. Repeat steps 4 and 5.
7. When only one suspect is left, you hear a long beep. DoctorNVDA keeps that add-on disabled, turns every other add-on back on as it was before the search, and announces "Diagnostic complete. Found and disabled" followed by the add-on's name.

**Note:** If you want to abandon a search at any time, open the menu and choose **Cancel Add-on Diagnostic and Restore All**. Every add-on returns to its original state and NVDA restarts. Your progress is saved between restarts, so the search continues correctly after each one.

### Create NVDA Setting Recovery

This creates a backup of your NVDA settings, so you can return to a known good configuration if something goes wrong. Choose **Create NVDA Setting Recovery** from the menu. NVDA first saves your current settings, then copies them in the background so NVDA stays responsive.

The backup includes your configuration profiles, speech dictionaries, keyboard gesture assignments, the main NVDA settings file, and update check information. The exact list of files adapts to your NVDA release, and also covers items such as add-on state and MathCAT settings where they apply.

Each backup is stored in its own folder named with the date and time. When it finishes, you hear a beep and NVDA announces "Recovery created" followed by the folder name. You can create as many backups as you like.

### Restore NVDA Setting

This brings back one of your saved backups.

**Step-by-step**

1. Open the menu and choose **Restore NVDA Setting**. If you have no backups yet, the item reads "Restore NVDA Setting unavailable".
2. The Select Recovery Folder window opens with your backups listed, newest first. Use the arrow keys to choose one.
3. Press Enter, double-click, or choose the **Restore** button.
4. NVDA prepares the files in the background, puts them in place, announces "Restore completed, restarting NVDA...", and restarts. Your restored settings take effect after the restart.

**Managing backups in this window**

- Press **Delete** to remove the selected backup, after confirming.
- Choose **Remove All** to delete every backup, after confirming.
- Press **Escape** or choose **Cancel** to close the window without changing anything.

### System Info Summary

Choose **System Info Summary** to copy the key details of your computer to the clipboard, ready to paste into an email or a support request. NVDA announces "System info copied" when it is done.

The summary contains:

- Windows edition, version, build number, and 32-bit or 64-bit architecture
- Processor name
- Installed memory, including the memory type and speed when Windows can report them
- Motherboard maker and model

### User Config Folder

Choose **User Config Folder** to open your NVDA user configuration folder in File Explorer. This is where NVDA keeps your settings, so it is handy when someone asks you to look at or send a file from it. If the folder cannot be opened or is missing, NVDA tells you.

### Clean Add-on Caches

Add-ons leave behind cache folders, called `__pycache__`, that can sometimes become stale after an update and cause odd behavior. This tool clears them from every installed add-on and from your scratchpad folder. DoctorNVDA's own files are left alone.

**Step-by-step**

1. Open the menu and choose **Clean Add-on Caches**.
2. DoctorNVDA searches every add-on folder and the scratchpad folder and empties each cache folder it finds.
3. NVDA announces how many files were cleaned, in how many cache folders, and how much space was freed. NVDA then restarts to finish applying the cleanup.

If there is nothing to clean, NVDA says "No `__pycache__` folders found. Everything is clean." and does not restart.

### Clean NVDA Temp Files

This removes leftover temporary files (.tmp) and files waiting to be deleted (.delete) from your NVDA user configuration folder, your installed add-ons, and your scratchpad folder. Stale temporary files can interfere with NVDA reading its settings or removing an add-on.

**Step-by-step**

1. Open the menu and choose **Clean NVDA Temp Files**.
2. DoctorNVDA scans for .tmp and .delete files.
3. If any are found, they are deleted. NVDA announces how many were removed and how much space was freed, then restarts.

If none are found, NVDA says "No temporary or .delete NVDA files found." and does not restart.

### Shortcut Hotkey Protection

If you start NVDA from a desktop shortcut that has a hotkey assigned, Windows can attach that hotkey to NVDA's own hidden window. The shortcut then stops working as a way to restart NVDA, because pressing it only wakes that window instead of starting a fresh copy.

A few seconds after every startup, DoctorNVDA removes this hotkey link from NVDA's windows, so your shortcut can restart NVDA again. It works automatically and needs nothing from you.

## Support Me

If this tool has made your life easier, consider fueling the next update with a small donation.

[![Support me](https://img.shields.io/badge/Donate-Support%20Me-blue?style=for-the-badge&logo=stripe)](https://buy.stripe.com/dRm9AU1xQ3Ds22N6VK1VK01)

Your support means the world. Let's build something great together

© 2026 Chai Chaimee NVDA Add-on Released under GNU GPL
