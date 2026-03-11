<p align="center">
  <img src="https://www.nvaccess.org/wp-content/uploads/2015/11/NVDA_logo_blue_600px.png" alt="NVDA Logo" width="120">
</p>

<h1 align="center">DoctorNVDA</h1>

<p align="center">
  The ultimate diagnostic and recovery companion for NVDA users, transforming how you maintain your screen reader's health.
</p>

<p align="center">
  author: chai chaimee<br>
  url: <a href="https://github.com/chaichaimee/DoctorNVDA">https://github.com/chaichaimee/DoctorNVDA</a>
</p>

<br>

---

<br>

## Professional Care for Your Screen Reader

<br>

Is your NVDA feeling sluggish? Are strange errors popping up after installing new add-ons? **DoctorNVDA** acts as a personal physician for your software. It provides high-precision tools to diagnose conflicts and restore health instantly, ensuring you never lose your configuration or your time.

<br>

> **Main Menu Shortcut:** Press **Alt + Windows + D**

<br>

## Detailed Feature Guide

<br>

### • NVDA Version Control
<br>
Provides your exact NVDA build information at a glance. Perfect for professional reporting or checking compatibility, it automatically copies the version details to your clipboard for immediate use.

<br>

### • Create & Restore NVDA Setting
<br>
Your settings are precious. This feature creates a **"Point-in-Time"** recovery of your perfect configuration including profiles, gestures, and dictionaries.

<br>

**The Safety Workflow:**
1. **Create Recovery:** Save your current stable settings. You can create as many recovery points as you need, acting as a historical backup.
2. **The Problem:** If your configuration becomes unstable or speech dictionaries get corrupted.
3. **Instant Restore:** Simply pick your desired recovery date from the menu, and DoctorNVDA will roll back all core files and restart NVDA automatically.

<br>

### • Restart NVDA with Add-ons Disabled
<br>
Instantly enter "Safe Mode". This allows you to verify if an issue persists without any add-ons running, providing a clear starting point for troubleshooting.

<br>

### • Binary Search Debugging (The Add-on Detective)
<br>
When you have dozens of add-ons, finding the one causing a conflict is like finding a needle in a haystack. DoctorNVDA uses an automated **Binary Search** process to find it for you.

<br>

**Case Study: Finding 1 problematic add-on among 40**
- **1. The Split:** DoctorNVDA disables 20 add-ons (Group A) and leaves 20 running (Group B), then restarts NVDA.
- **2. The Health Check:** A dialog appears asking: **"Is the problem GONE?"**
    - **If you answer YES:** The "culprit" is among the 20 add-ons we just disabled. DoctorNVDA will split it again to 10 in the next round.
    - **If you answer NO:** The "culprit" is still active in the other group. DoctorNVDA will switch to narrow it down.
- **3. The Result:** The process continues until the exact problematic add-on is isolated and disabled.

<br>

**How to Abort & Recovery:**
If you wish to stop the diagnostic: Press **Cancel** on the diagnostic dialog or select **"Cancel Add-on Diagnostic and Restore All"** in the menu.

<br>

### • System Info Summary
<br>
Generates a detailed "Health Report" of your environment. It captures OS builds, CPU specs, Motherboard details, and **Total RAM capacity**.

<br>

**Doctor's Order:** Always create a recovery point before installing major new add-ons or making significant changes to your configuration.

<br>

---
<p align="center">© 2026 Chai Chaimee. Engineered for NVDA stability and reliability.</p>