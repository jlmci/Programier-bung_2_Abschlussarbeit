# Programier-bung_2_Abschlussarbeit
# Trainingstagebuch

## Angestrebter Aufbau
Es soll ein Art Trainingstagebuch App mit Leistungsanalysefunktionen gebaut werden.
Dazu soll man sich zuerst einloggen.
![Diagramm](pictures_readme/Login.png)

Nach dem Einloggen kommt man auf die Startseite. Hier wird eine Leistungsübersicht angezeigt. Dieses Design soll vorerst so gewählt werden:
![Diagramm](pictures_readme/standardansicht.png)

Links in der Sidebar sollen dann noch andere Bereiche ausgewählt werden können.
Unter Profil bekommt man folgende Ansicht:
![Diagramm](pictures_readme/Profil.png)
Der Diagnostiker/Admin hat außerdem ein Feld wo er Personen auswählen darf:
![Diagramm](pictures_readme/personauswählen.png)
unter Pforfil bekommt er die Person angezeigt, die er gerade anschaut.

Weiter kann man die Tagebuchfuktion links auswählen. Da gibt es das Feld einen neuen Eintrag hinzuzufügen, das schaut dann so aus:
![Diagramm](pictures_readme/addTraining.png)

Wenn man dann ein Training anzeigen möchte, kann man entweder ein spezielles Training angezeigt bekommen oder es so machen, dass alle Trainings untereinander angezeigt werden.
Die Darstellung soll etwa so sein.
![Diagramm](pictures_readme/darstellungTagebuch.png)









# Trainingstagebuch App im Stramlit

Diese Streamlit-Anwendung ermöglicht die Verfolgung sportlicher Aktivitäten, die Einsicht in detaillierte Statistiken und die Überwachung von Fortschritten. Administratoren haben zusätzlich die Möglichkeit, Profile zu verwalten und die Daten anderer Benutzer einzusehen.

---

## Inhaltsverzeichnis

- Funktionen
- Installation und Setup
- Anleitung zur Nutzung der App
- Login
- Dashboard
- Profil
- Workout hinzufügen
- Trainingsliste
- Für Administratoren: Person anschauen
- Für Administratoren: Profil hinzufügen
- Code-Struktur und wichtige Komponenten
- Fehlerbehebung

---

## 1. Funktionen

- *Benutzerverwaltung:* Sicheres Login-System mit config.yaml.
- *Profilverwaltung:* Persönliche Daten einsehen und bearbeiten, inklusive Profilbild und Maximalpuls.
- *Workout-Erfassung:* Hinzufügen neuer Trainingseinheiten mit Details wie Sportart, Dauer, Distanz, Puls, Kalorien, Anstrengung und Bewertung.
- *Dateianhänge:* Hochladen und Analysieren von GPX- (GPS-Tracks, Höhenprofile) und FIT-Dateien (Herzfrequenz, Leistung, Trittfrequenz, Geschwindigkeit). EKG-Daten können ebenfalls verlinkt werden.
- *Trainingsübersicht:* Eine detaillierte Liste aller aufgezeichneten Trainings mit Bearbeitungs- und Löschfunktionen.
- *Interaktives Dashboard:* Visualisierung aggregierter Trainingsdaten wie Gesamtdistanz, Gesamtzeit und eine akkumulierte Power Curve. Diese sind von mehreren Trainings zusammengefasst, um gegebenenfalls eine Leistungsverbesserung über die Zeit feststellen zu können.

### Admin-Funktionen:

- Neue Benutzerprofile mit zugehörigen Login-Konten erstellen.
- Die Ansicht auf die Daten anderer Benutzer wechseln.
- Passwörter von Benutzern zurücksetzen (als Admin).

---

## 2. Installation und Setup

Die Webapp ist über streamlit share öfentlich gemacht. Folgender Link bringt Sie zur Website:

- https://programier-bung2abschlussarbeit-jh-jl.streamlit.app/Trainingsliste


Zur lokalen Ausführung der App sind folgende Schritte erforderlich:

-  1 Klone das Repository von Git
 - 1.1 gehe auf das repository, dann auf code und kopiere den code
 - 1.2 Öffne ein neues Fenster auf VS Studio
 - 1.3 Klicke auf repository klonen und füge den Link ein
- 2 aktiviere das virtual environment mit pdm install wir empfehlen Python version 3.10.4 für reibungslosen ablauf
 - 2.1 öffne das powershell Terminal in
 - 2.2 gib "pdm install" ein
- 3 starte die App indem Sie im terminal im ordern des repositories pdm run streamlit run main.py eingeben.
 

Nun sollte das Repository geklont und das virtual environment aufgebaut sein und die App starten.


---

## 3. Anleitung zur Nutzung der App

Diese Sektion führt durch die Funktionen der Trainingstagebuch App.

### Login

- Beim Start der App wird der Login-Bildschirm angezeigt.
- Geben Sie den Benutzernamen und das Passwort ein, die in der config.yaml Datei festgelegt sind.
- Führen Sie den Login durch. Bei korrekten Daten erfolgt die Weiterleitung zum Dashboard. Bei falschen Daten wird eine entsprechende Meldung angezeigt.
![Login Fenster](/pictures_readme/Login%20fenster.PNG)

### Dashboard

Das Dashboard bietet einen schnellen Überblick über die Trainingsdaten:

- *Gesamtdistanz:* Summe aller zurückgelegten Kilometer.
- *Gesamtzeit:* Kumulierte Dauer aller Trainingseinheiten.
- *Max. Herzfrequenz (Angabe):* Persönlich eingetragener Maximalpuls aus dem Profil.
- *Max. Herzfrequenz (Gemessen aus Dateien):* Höchster Puls, der in hochgeladenen FIT-Dateien gemessen wurde.
- *Höhenmeter:* Umschaltbare Anzeige für aufwärts oder abwärts zurückgelegte Höhenmeter.
- *Akkumulierte Power Curve:* Grafische Darstellung der besten durchschnittlichen Leistungen über verschiedene Zeiträume, basierend auf FIT-Dateien.
![Dashboard fenseter](/pictures_readme/Dashboard%20fenster.PNG)

### Profil

Auf der Profilseite können persönliche Daten verwaltet und aktualisiert werden:
- *Persönliche Informationen:* Bearbeiten Sie Maximalpuls. Das ändern der anderen Daten ist den Admins vorbehalten
- *Profilbild hochladen:* Laden Sie ein Bild von Ihrem Computer hoch.
- *Änderungen speichern:* Sichern Sie die aktualisierten Informationen.
- *Benutzername oder Passwort ändern:* Geben Sie das aktuelle Passwort zur Bestätigung ein. Geben Sie dann einen neuen Benutzernamen (optional) und/oder ein neues Passwort ein. Nach dem Ändern des Benutzernamens ist eine erneute Anmeldung mit dem neuen Namen erforderlich.
![Profil fenster](/pictures_readme/Profil%20fenster.PNG)

### Workout hinzufügen

Diese Seite dient der Erfassung neuer Trainingseinheiten oder der Bearbeitung bestehender.

- *Neues Workout hinzufügen:*
  - Details eingeben: Füllen Sie Felder wie Name, Datum, Sportart, Dauer, Distanz, Puls, Kalorien, Anstrengung und Bewertung aus. Fügen Sie eine detaillierte Beschreibung hinzu.
  - Dateien hochladen: Laden Sie passende Bilder, GPX-Dateien (für GPS-Track und Höhenprofil), FIT-Dateien (für detaillierte Leistungsdaten) oder EKG-Dateien hoch.
  - Speichern: Fügen Sie das Training zur Datenbank hinzu.
  ![Workout hinzufügen fenster](/pictures_readme/Workout%20hinzufügen%20fenster.PNG)

- *Training bearbeiten:*
  - Wählen Sie ein Training aus der "Trainingsliste" zum Bearbeiten aus. Die Seite öffnet sich mit den vorhandenen Daten.
  - Nehmen Sie Änderungen vor und speichern Sie diese. Mit "Abbrechen" kehren Sie zur Trainingsliste zurück.

### Alle Trainings: Trainingstagebuch

Hier finden Sie eine vollständige Liste aller erfassten Trainings.

- *Übersicht:* Jedes Training wird als aufklappbarer Bereich (Expander) mit Name, Datum und Sportart angezeigt.
- *Details anzeigen:* Klicken Sie auf die Überschrift eines Trainings, um alle Details und Analysen der hochgeladenen Dateien zu sehen.
- *Interaktive Diagramme:* Für FIT-Dateien können Sie über Checkboxen auswählen, welche Diagramme (Herzfrequenz, Leistung, Geschwindigkeit, Trittfrequenz) angezeigt werden sollen.
- *Bearbeiten:* Klicken Sie auf "Bearbeiten 📝", um das Training im Formular "Workout hinzufügen" zu öffnen.
- *Löschen:* Klicken Sie auf "Löschen 🗑️", um ein Training dauerhaft aus der Datenbank zu entfernen. Diese Aktion kann nicht rückgängig gemacht werden.
![Trainings liste](/pictures_readme/traiings%20liste.PNG)
![Trainingsfenster 1](/pictures_readme/Trainingsfenster%201.PNG)
![Trainingsfenster 2](/pictures_readme/Trainingsfenster%202.PNG)
![Trainingsfenster 3](/pictures_readme/Trainingsfenster%203.PNG)
---

### Für Administratoren: Person anschauen

(Diese Seite ist nur sichtbar, wenn Sie als Administrator angemeldet sind.)

- Als Administrator können Sie hier die Ansicht auf die Daten anderer Benutzer wechseln.
- *Person aus Liste auswählen:* Wählen Sie eine Person aus der Dropdown-Liste oder suchen Sie nach ID/Namen.
- *Ansicht wechseln:* Klicken Sie auf "Als '[Name der Person]' ansehen". Die App zeigt dann die Daten dieser Person an. Um zu den eigenen Daten zurückzukehren, wählen Sie "Mich selbst" aus der Liste.
- Passwort der Person ist auch von Admin einsehbar
![Person wechseln fesnter](/pictures_readme/beutzer%20wechseln%20fenster.PNG)

---

### Für Administratoren: Profil hinzufügen

(Diese Seite ist nur sichtbar, wenn Sie als Administrator angemeldet sind.)

- Als Administrator können Sie hier neue Benutzerprofile erstellen und die zugehörigen Login-Daten in die config.yaml eintragen.
- *Profildaten eingeben:* Füllen Sie die Informationen für die neue Person aus.
- *Profilbild hochladen:* Laden Sie ein Profilbild für das neue Konto hoch.
- *Login-Daten festlegen:* Geben Sie einen Benutzernamen und ein initiales Passwort ein.
- *Profil & Benutzerkonto erstellen:* Speichern Sie das neue Profil und die Login-Daten.

*Wichtiger Hinweis:* Nach dem Erstellen eines neuen Profils muss die App neu gestartet werden, damit der neue Benutzer im Login-Bildschirm sichtbar wird.

![Profil hinzufügen fenster](/pictures_readme/Profil%20hinzufügen%20fenster.PNG)

---

## 4. Erfüllte Aufgabe:

Alle Basisaufgaben wurden erfüllt
- Es wurde jdeoch gewisse abwandlungen gemacht da dies  mit dem Stile der App besser zusammenpasst
  - Die Testdauer wird in Studnen und Minuten (statt nur in Minuten)
  - Die Auswahl der zeitberiche der Plots ist nur bei den EKG plots möglich, da bei den FIT-Plots die Kurven des gesammten trainings zuzeigen, logischer ist
  
  
Bei den zusatzaufgaben wurde folgendes erledigt

 **1. Dateisystem**
* **Datenimport:**
    * Unterstützung für das Einlesen von Daten aus verschiedenen Quellen:
        * `.fit`-Dateien
        * `.txt`-Dateien
        * `.csv`-Dateien
        * `.gpx`-Dateien
* **Datenbank:**
    * Effiziente Speicherung aller Trainingsdaten in einer **TinyDB**.

---

 **2. Benutzer- und Berechtigungsmanagement**

Hier werden die Funktionen für die Nutzerverwaltung und die Zugriffsrechte innerhalb der Anwendung beschrieben.

* **Authentifizierung:**
    * Sicheres **Login-System** mit Benutzername und Passwort.
* **Berechtigungssystem:**
    * Differenzierung zwischen **Nutzer- und Admin-Rollen** für angepasste Zugriffsrechte.
* **Passwortverwaltung:**
    * Möglichkeit zur **Passwortänderung** sowohl für Nutzer als auch für Admins.
* **Admin-Funktionen:**
    * **"Profile hinzufügen"**: Admins können neue Nutzer- oder Sportlerprofile anlegen.
    * **"In Ansicht von Nutzer wechseln"**: Admins können die Anwendung aus der Perspektive eines Nutzers sehen, um Support zu leisten oder Einstellungen zu überprüfen.

---

 **3. Analyse und Visualisierung von Einzeltrainings**

Dieser Abschnitt konzentriert sich auf die detaillierte Auswertung und Darstellung spezifischer Trainingseinheiten.

* **GPS-basierte Analysen (`.gpx`):**
    * Interaktive **Kartendarstellung** von `.gpx`-Trainings-Files.
    * Detaillierte Anzeige des **Höhenprofils** aus `.gpx`-Dateien.
* **Fit-File-Analysen (`.fit`):**
    * Eine Vielzahl von **Fit-File-Plots** zur Auswahl, um verschiedene Metriken (z.B. Geschwindigkeit, Trittfrequenz, Leistung) zu visualisieren.
* **Allgemeine Metriken pro Training:**
    * Anzeige der **Herzrate** im sinnvollen gleitenden Durchschnitt als übersichtlicher Plot.
    * Berechnung und Visualisierung der **Power Curve** pro Training.
    * Detaillierte Angaben zu **Höhenmetern** (hoch und runter).
    * Gesamte **Distanz** des Trainings.
    * Gesamte **Zeitdauer** des Trainings.
    * Berechnung des **Maximalpulses** (pro Training).
* **Bewertung von Trainings:**
    * Möglichkeit, individuelle **Bewertungen** oder Notizen zu jedem Training hinzuzufügen.

---

 **4. Akkumulierte Daten und Fortschrittsanalyse**

Dieser Bereich ermöglicht die langfristige Auswertung über mehrere Trainingseinheiten hinweg, um den Fortschritt zu verfolgen.

* **Akkumulierte Trainingsdaten:**
    * Übersichtliche Darstellung aller gesammelten Trainingsdaten über einen längeren Zeitraum.
    * Umfassende **Power Curve** über mehrere Trainings hinweg (oder basierend auf ausgewählten Zeiträumen).
    * Weitere aggregierte Metriken wie die Gesamtstrecke aller Trainings, die kumulierte Trainingszeit und die gesamten Höhenmeter.
---

## 5. Nutzer der App:
relevante Nutzer der App, liste kann natürlich erweitert werden
  - mmustermann:
    - name: Max Mustermann
    - password: '1234'
    - person_doc_id: 3
  - jhubermci:
    - name: Julian Huber
    - password: '1234'
    - person_doc_id: 9
  - jvolmer:
    - name: Jasper Volmer
    - password: '1234'
    - person_doc_id: 10
  - miamusterfrau:
    - name: Mia Musterfrau
    - password: '1234'
    - person_doc_id: 11

## 6. Probleme
- Wenn mehrere Trainings hintereindaer hinzugefügt werden wird bis auf den Namen und die files nichts gelöscht bzw bleiben die alten Daten bestehen/vorausgefüllt
  - Wir wissen nicht ganz wieso es nicht geht aber setzten uns noch einmal dran. 
  - Unter normaler nutzung der APP wird pro login immer nur ein Training hochgeladen (und zwar das soeben absolvierte) nach erneutem login sind die Felder dann auch wider frei. Das Problem besteht also in der realen Benutzung nicht.

- Wenn in der Streamlit share änderungen an den files gemacht werden und die pfade der Dateien somit neu in die datenbang gespeichrt werden, werden sie nur in dieser session gespeichert aber nicht in das richtige github repository gespeichert. Das bedeutet, dass die änderungen bei erneutem öffnen der APP nicht gespeichert sind
