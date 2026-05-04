<p align="center">
  <img src="https://www.nvaccess.org/wp-content/uploads/2015/11/NVDA_logo_blue_600px.png" alt="NVDA Logo" width="120">
</p>

<br>

# <p align="center">DoctorNVDA</p>

<br>

<p align="center">Der ultimative Diagnose- und Wiederherstellungsbegleiter für NVDA-Benutzer, der die Wartung Ihres Screenreaders revolutioniert.</p>

<br>

<p align="center">
  <b>author:</b> chai chaimee
</p>

<p align="center">
  <b>url:</b> <a href="https://github.com/chaichaimee/DoctorNVDA">https://github.com/chaichaimee/DoctorNVDA</a>
</p>

---

<br>

## <p align="center">Beschreibung</p>

<br>

Fühlt sich Ihr NVDA träge an? Treten nach der Installation neuer Add-ons seltsame Fehler auf? **DoctorNVDA** fungiert als persönlicher Arzt für Ihre Software. Es bietet hochpräzise Werkzeuge, um Konflikte zu diagnostizieren und die Funktionsfähigkeit sofort wiederherzustellen, damit Sie weder Ihre Konfiguration noch Ihre Zeit verlieren.

<br>

Dieses Add-on wurde für jeden Benutzer entwickelt, unabhängig von den technischen Kenntnissen. Es vereinfacht komplexe Fehlerbehebungen mit wenigen Klicks. Sie können Backups verwalten, problematische Add-ons identifizieren und Notfall-Restarts durchführen, ohne jemals komplizierte Systemdateien oder den Windows Task-Manager berühren zu müssen.

<br>

## <p align="center">Tastenkombinationen</p>

<br>

DoctorNVDA verwendet ein intelligentes **Multi-Tap**-System. Das bedeutet, dass Sie sich nur eine primäre Tastenkombination merken müssen, um mehrere Wiederherstellungsaktionen durchzuführen.

<br>

> **Hauptbefehl: ALT + Windows + D**
>
> *   **Einfaches Tippen:** Öffnet das **DoctorNVDA-Hauptmenü**, um auf alle Funktionen zuzugreifen.
>
> *   **Doppeltes Tippen:** Sofortiger **NVDA-Neustart** (Normaler Modus).
>
> *   **Dreifaches Tippen:** Notfall-**Neustart mit deaktivierten Add-ons** (Abgesicherter Modus).

<br>

## <p align="center">Funktionen</p>

<br>

### 1. Binäre Suche Debugging (Der Add-on-Detektiv)

<br>

Ein einzelnes defektes Add-on unter Dutzenden zu finden, ist wie die Suche nach der Stecknadel im Heuhaufen. Diese Funktion automatisiert die "Binäre Suche", um den Übeltäter für Sie zu finden.

<br>

**Schritt-für-Schritt-Anleitung:**
1. Starten Sie die Diagnose über das DoctorNVDA-Menü.
2. NVDA wird neu gestartet, wobei die Hälfte Ihrer Add-ons deaktiviert ist.
3. Ein Dialog fragt: **"Ist das Problem BEHOBEN?"**
4. Wenn Sie mit **Ja** antworten, weiß der Detektiv, dass das Problem in der deaktivierten Hälfte liegt. Wenn **Nein**, liegt es in der aktiven Hälfte.
5. Der Vorgang wird wiederholt und die Gruppe eingegrenzt, bis das exakte problematische Add-on isoliert ist.

<br>

### 2. NVDA-Einstellungen erstellen & wiederherstellen (Zeitmaschine)

<br>

Schützen Sie Ihre benutzerdefinierten Wörterbücher, Gesten und Profile. Diese Funktion erstellt einen **"Wiederherstellungspunkt"**, zu dem Sie jederzeit zurückkehren können.

<br>

**Schritt-für-Schritt-Anleitung:**
1. **Zum Sichern:** Wählen Sie "Wiederherstellungspunkt erstellen", wenn Ihr NVDA einwandfrei funktioniert.
2. **Zum Wiederherstellen:** Wenn Ihre Einstellungen fehlerhaft sind, wählen Sie "NVDA-Einstellung wiederherstellen" aus dem Menü.
3. Wählen Sie ein Wiederherstellungsdatum aus der Liste.
4. DoctorNVDA ersetzt automatisch die beschädigten Dateien und startet NVDA für Sie neu.

<br>

### 3. Systeminfo-Zusammenfassung

<br>

Müssen Sie einen Fehler melden oder den Zustand Ihres Systems überprüfen? Dieses Tool sammelt alle wichtigen Statistiken an einem Ort – keine technischen Kenntnisse erforderlich.

<br>

**Schritt-für-Schritt-Anleitung:**
1. Wählen Sie "Systeminfo-Zusammenfassung" aus dem Menü.
2. Ein übersichtlicher Bericht erscheint mit Ihrer NVDA-Version, Windows-Version und Systemarchitektur.
3. Diese Informationen sind automatisch so formatiert, dass sie leicht zu lesen und mit Entwicklern oder Support-Teams zu teilen sind.

<br>

### 4. Sofortiger Zugriff auf die Benutzerkonfiguration

<br>

Überspringen Sie das tiefe Eintauchen in versteckte Windows-Ordner. Erhalten Sie direkten Zugriff auf den Ort, an dem NVDA Ihre Einstellungen speichert.

<br>

```text
%APPDATA%\nvda