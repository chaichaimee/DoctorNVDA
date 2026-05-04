<p align="center">
  <img src="https://www.nvaccess.org/wp-content/uploads/2015/11/NVDA_logo_blue_600px.png" alt="NVDA Logo" width="120">
</p>

<br>

# <p align="center">DoctorNVDA</p>

<br>

<p align="center">The ultimate diagnostic and recovery companion for NVDA users, transforming how you maintain your screen reader's health.</p>

<br>

<p align="center">
  <b>author:</b> chai chaimee
</p>

<p align="center">
  <b>url:</b> <a href="https://github.com/chaichaimee/DoctorNVDA">https://github.com/chaichaimee/DoctorNVDA</a>
</p>

---

<br>

## <p align="center">Description</p>

<br>

Is your NVDA feeling sluggish? Are strange errors popping up after installing new add-ons? **DoctorNVDA** acts as a personal physician for your software. It provides high-precision tools to diagnose conflicts and restore health instantly, ensuring you never lose your configuration or your time.

<br>

This add-on is designed for every user, regardless of technical skill. It simplifies complex troubleshooting into a few simple clicks, allowing you to manage backups, identify problematic add-ons, and perform emergency restarts without ever needing to touch complicated system files or the Windows Task Manager.

<br>

## <p align="center">Hot Keys</p>

<br>

DoctorNVDA uses an intelligent **Multi-Tap** system. This means you only need to remember one primary key combination to perform multiple recovery actions.

<br>

> **Main Command: ALT + Windows + D**
>
> *   **Single Tap:** Open the **DoctorNVDA Main Menu** to access all features.
>
> *   **Double Tap:** Instantly **Restart NVDA** (Normal Mode).
>
> *   **Triple Tap:** Emergency **Restart with Add-ons Disabled** (Safe Mode).

<br>

## <p align="center">Features</p>

<br>

### 1. Binary Search Debugging (The Add-on Detective)

<br>

Finding a single broken add-on among dozens is like finding a needle in a haystack. This feature automates the "Binary Search" method to find the culprit for you.

<br>

**Step-by-Step Guide:**
1. Launch the diagnostic from the DoctorNVDA menu.
2. NVDA will restart with half of your add-ons disabled.
3. A dialog will ask: **"Is the problem GONE?"**
4. If you answer **Yes**, the detective knows the problem is in the disabled half. If **No**, it's in the active half.
5. The process repeats, narrowing down the group until the exact problematic add-on is isolated.

<br>

### 2. Create & Restore NVDA Settings (Time Machine)

<br>

Protect your custom dictionaries, gestures, and profiles. This feature creates a **"Recovery Point"** that you can return to at any time.

<br>

**Step-by-Step Guide:**
1. **To Backup:** Select "Create Recovery" when your NVDA is working perfectly.
2. **To Restore:** If your settings get messed up, select "Restore NVDA Setting" from the menu.
3. Choose a recovery date from the list.
4. DoctorNVDA will automatically replace the corrupted files and restart NVDA for you.

<br>

### 3. System Info Summary

<br>

Need to report a bug or check your system's health? This tool gathers all vital statistics in one place—no technical knowledge required.

<br>

**Step-by-Step Guide:**
1. Select "System Info Summary" from the menu.
2. A clean report will appear showing your NVDA version, Windows version, and system architecture.
3. This info is automatically formatted to be easy to read and share with developers or support teams.

<br>

### 4. Instant User Config Access

<br>

Skip the deep-diving into hidden Windows folders. Get direct access to where NVDA stores your soul (your settings).

<br>

```text
%APPDATA%\nvda