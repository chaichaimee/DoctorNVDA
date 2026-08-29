<p align="center">
  <img src="https://www.nvaccess.org/wp-content/uploads/2015/11/NVDA_logo_blue_600px.png" alt="NVDA Logo" width="120">
</p>

<h1 align="center">DoctorNVDA</h1>

<p align="center">
  <strong>author:</strong> chai chaimee<br>
  <strong>url:</strong> <a href="https://github.com/chaichaimee/DoctorNVDA">https://github.com/chaichaimee/DoctorNVDA</a>
</p>

---

## Introduction

DoctorNVDA is an NVDA add-on that lets you quickly save and access frequently used configuration files and folders, while acting as a comprehensive diagnostic and recovery companion for your screen reader. Whether your speech synthesizer suddenly stops responding, a newly installed add-on causes a system crash, or you simply need a safe backup of your highly customized settings, DoctorNVDA serves as a personal physician for your software. It simplifies complex technical troubleshooting into a few intuitive keystrokes, ensuring you maintain optimal accessibility without ever needing advanced technical skills.

## Features

* **Emergency Synthesizer Reboot:**

  Instantly recover your speech when NVDA goes completely silent, without needing to fully restart the screen reader or lose your current place on the screen.

  **Step-by-Step Guide:**
  1. Press the emergency recovery hotkey: **ALT + Windows + R** (Single Tap).
  2. DoctorNVDA will forcefully terminate and reinitialize the current speech synthesizer and audio output.
  3. You will hear a distinct confirmation beep once the audio subsystem is reset and your speech is successfully restored.

* **Crash Log Analyzer:**

  Automatically detect and understand exactly what caused NVDA to crash or freeze during your previous session using plain, readable English instead of confusing code.

  **Step-by-Step Guide:**
  1. If NVDA crashes and restarts on its own, DoctorNVDA automatically analyzes the crash log in the background. If a specific add-on caused the crash, a clear text report will open automatically.
  2. To check your logs manually at any time, double-tap the recovery hotkey (**ALT + Windows + R**), or select "Crash Log Analyzer" from the DoctorNVDA main menu.
  3. Read the plain-language text report to see the exact add-on name, file, and line of code that caused the error.

* **Binary Search Debugging (The Add-on Detective):**

  Finding a single broken add-on among dozens is a frustrating, time-consuming task. This automated feature uses a smart "halving" method to isolate the culprit for you in minutes.

  **Step-by-Step Guide:**
  1. Press **ALT + Windows + D** to open the DoctorNVDA menu and select "Binary Search Debugging add-on".
  2. Confirm the prompt. NVDA will automatically restart with half of your active add-ons temporarily disabled.
  3. A dialog box will appear asking: "Is the problem GONE?"
  4. If you select **Yes**, the add-on knows the broken tool is in the disabled half. If you select **No**, it knows it is in the active half.
  5. The process repeats, intelligently narrowing down the group until the exact problematic add-on is identified and safely disabled for you.

* **Create & Restore NVDA Settings (Time Machine):**

  Protect your custom pronunciation dictionaries, personalized gestures, profiles, and active add-on states by creating instant, reliable recovery points.

  **Step-by-Step Guide:**
  1. **To Backup:** Open the menu (**ALT + Windows + D**) and select "Create NVDA Setting Recovery" when your NVDA is working perfectly. A timestamped backup is saved in seconds.
  2. **To Restore:** If your settings become corrupted or confusing, open the menu and select "Restore NVDA Setting".
  3. Choose your desired recovery date and time from the list and hit "Restore". DoctorNVDA will automatically replace the corrupted configuration files and safely restart NVDA.

* **System Info Summary:**

  Easily gather all vital system statistics to share with developers, support teams, or community forums when reporting a bug.

  **Step-by-Step Guide:**
  1. Open the DoctorNVDA menu and select "System Info Summary".
  2. DoctorNVDA quietly compiles your exact NVDA version, Windows OS version, CPU, RAM, and Motherboard details.
  3. The neatly formatted text is automatically copied to your clipboard. Simply press **CTRL + V** to paste it into an email or support ticket.

* **Clean Add-on Caches & Temp Files:**

  Keep your NVDA environment responsive, stable, and lightweight by clearing out leftover installation or background cache files.

  **Step-by-Step Guide:**
  1. Open the DoctorNVDA menu.
  2. Select either "Clean Add-on Caches" or "Clean NVDA Temp Files" depending on what you want to optimize.
  3. DoctorNVDA will safely delete unnecessary files, announce exactly how much storage space was freed, and restart NVDA to finalize the clean-up.

## Benefits

* **Saves Time:** Eliminates the need to manually dig through hidden Windows directories, reinstall add-ons one-by-one, or sift through hundreds of lines in confusing error logs.
* **Reduces Keystroke Fatigue:** Provides simple, memorable multi-tap hotkeys that trigger complex recovery sequences, saving you from navigating endless nested menus.
* **Prevents Data Loss:** Ensures your highly customized gestures, voice profiles, and specialized dictionaries are always safely backed up and restorable in seconds.
* **Lowers the Technical Barrier:** Transforms complex, developer-level debugging methods into straightforward, plain-language prompts suitable for everyday users.
* **Boosts Productivity:** Keeps your screen reader environment stable and responsive, allowing you to focus on your work, reading, or browsing rather than fixing frustrating software bugs.

## Why Use DoctorNVDA?

Screen reader stability is absolutely essential for daily digital independence. However, managing silent add-on conflicts, sudden audio freezes, or accidentally corrupted user profiles can entirely disrupt your workflow and leave you stranded. DoctorNVDA solves these critical problems by providing a reliable, automated safety net. It takes the guesswork out of troubleshooting and equips you with immediate, practical tools to fix severe issues on the fly, making it an indispensable utility for anyone who relies heavily on NVDA.

## Take Control of Your Screen Reader

Don't wait for a crash to ruin your productivity or compromise your accessibility. Take full control of your NVDA's health, streamline your configuration backups, and enjoy a faster, far more resilient screen reading experience. Download DoctorNVDA today to give yourself the ultimate peace of mind, knowing your essential digital setup is protected, easily diagnosed, and always performing at its absolute best.

## Support Me

If this tool has made your life easier, consider fueling the next update with a small donation.

<p align="center">
  <a href="https://buy.stripe.com/dRm9AU1xQ3Ds22N6VK1VK01">
    <img src="https://img.shields.io/badge/Donate-Support%20Me-blue?style=for-the-badge&logo=stripe" alt="Support me">
  </a>
</p>

Your support means the world. Let's build something great together

<p align="center">
  <sub>© 2026 Chai Chaimee NVDA Add-on Released under GNU</sub>
</p>