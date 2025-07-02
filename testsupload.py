import json
import os
import shutil
from datetime import datetime

# Der Pfad zur JSON-Datei, in der die Personendaten gespeichert sind
PERSON_DB_PATH = "data/person.json"
DATA_DIR = "data" # Hauptdatenverzeichnis

class Person:
    def _init_(self, data):
        self.id = data.get("id")
        self.date_of_birth = data.get("date_of_birth")
        self.firstname = data.get("firstname")
        self.lastname = data.get("lastname")
        self.gender = data.get("gender")
        # Pfade beim Initialisieren normalisieren
        self.picture_path = Person.normalize_path(data.get("picture_path")) # Call as staticmethod
        self.health_data = [self.normalize_health_entry(entry) for entry in data.get("health_data", [])]

        # Spezieller Getter für den Pfad der Gesundheitsdaten-CSV
        self.healthdata_path = self.get_healthdata_csv_path()

    @staticmethod # Made this a staticmethod
    def normalize_path(path):
        """
        Normalisiert einen Dateipfad, indem Backslashes durch Forward-Slashes ersetzt
        und der Pfad dann mit os.path.normpath bereinigt wird.
        """
        if path:
            # Ersetze Backslashes durch Forward-Slashes
            normalized_path = path.replace("\\", "/")
            # os.path.normpath bereinigt den Pfad (z.B. entfernt unnötige '.' oder '..')
            return os.path.normpath(normalized_path)
        return path

    def normalize_health_entry(self, entry):
        """
        Normalisiert den result_link innerhalb eines health_data Eintrags.
        """
        if entry and "result_link" in entry:
            entry["result_link"] = Person.normalize_path(entry["result_link"]) # Call as staticmethod
        return entry

    def get_healthdata_csv_path(self):
        # Annahme: Es gibt immer nur einen Eintrag unter "health_data" oder der erste ist der relevante
        if self.health_data and isinstance(self.health_data, list) and len(self.health_data) > 0:
            return self.health_data[0].get("result_link")
        return None

    @staticmethod
    def load_person_data():
        if not os.path.exists(PERSON_DB_PATH):
            return []
        try:
            with open(PERSON_DB_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: {PERSON_DB_PATH} is empty or malformed. Returning empty list.")
            return []
        except Exception as e:
            print(f"Error loading person data from {PERSON_DB_PATH}: {e}")
            return []

    @staticmethod
    def save_person_data(data):
        # Erstelle den 'data'-Ordner, falls er nicht existiert
        os.makedirs(os.path.dirname(PERSON_DB_PATH), exist_ok=True)
        with open(PERSON_DB_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def calculate_age(self):
        current_year = datetime.now().year
        return current_year - self.date_of_birth

def generate_new_person_id(person_list):
    if not person_list:
        return 1
    return max(p["id"] for p in person_list) + 1

def save_uploaded_file(uploaded_file, subfolder, existing_path=None):
    """
    Speichert eine hochgeladene Datei in einem Unterordner innerhalb von 'data/'.
    Gibt den Pfad der gespeicherten Datei zurück.
    Wenn ein existing_path gegeben ist, wird versucht, diese Datei zu löschen.
    """
    if uploaded_file is None:
        return existing_path # Behalte den alten Pfad, wenn keine neue Datei hochgeladen wird

    # Lösche die bestehende Datei, falls vorhanden und neu hochgeladen wird
    if existing_path and os.path.exists(existing_path):
        try:
            # WICHTIG: Normalisiere den existing_path, bevor du ihn zu löschen versuchst
            normalized_existing_path = Person.normalize_path(existing_path) # Call as staticmethod
            if os.path.exists(normalized_existing_path): # Zusätzliche Prüfung
                os.remove(normalized_existing_path)
                print(f"DEBUG: Alte Datei gelöscht: {normalized_existing_path}")
            else:
                print(f"DEBUG: Alte Datei nicht gefunden zum Löschen (Pfad: {normalized_existing_path}), eventuell schon gelöscht oder Pfadfehler.")
        except OSError as e:
            print(f"ERROR: Konnte alte Datei nicht löschen {normalized_existing_path}: {e}")

    upload_dir = os.path.join(DATA_DIR, subfolder)
    os.makedirs(upload_dir, exist_ok=True)

    file_path = os.path.join(upload_dir, uploaded_file.name)
    # Sicherstellen, dass der Dateiname eindeutig ist, um Überschreiben zu vermeiden
    base, ext = os.path.splitext(uploaded_file.name)
    counter = 1
    while os.path.exists(file_path):
        file_path = os.path.join(upload_dir, f"{base}_{counter}{ext}")
        counter += 1

    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path # os.path.join gibt bereits den korrekten Pfad zurück

def add_new_person_to_db(new_person_data):
    """
    Fügt eine neue Person zur JSON-Datenbank hinzu.
    """
    person_list = Person.load_person_data()
    new_id = generate_new_person_id(person_list)
    new_person_data["id"] = new_id
    person_list.append(new_person_data)
    Person.save_person_data(person_list)

def update_person_in_db(updated_person_data):
    """
    Aktualisiert die Daten einer bestehenden Person in der JSON-Datenbank.
    """
    person_list = Person.load_person_data()
    person_id_to_update = updated_person_data["id"]
    found = False
    for i, person in enumerate(person_list):
        if person["id"] == person_id_to_update:
            person_list[i] = updated_person_data
            found = True
            break
    if found:
        Person.save_person_data(person_list)
    else:
        raise ValueError(f"Person mit ID {person_id_to_update} nicht gefunden zum Aktualisieren.")

def delete_person_from_db(person_id_to_delete):
    """
    Löscht eine Person aus der JSON-Datenbank und die zugehörigen Dateien (Bild, CSV).
    """
    person_list = Person.load_person_data()
    # Finde die Person, die gelöscht werden soll
    person_to_delete = next((p for p in person_list if p["id"] == person_id_to_delete), None)

    if person_to_delete:
        # Lösche die zugehörigen Dateien
        picture_path_to_delete = Person.normalize_path(person_to_delete.get("picture_path")) # Call as staticmethod
        if picture_path_to_delete and os.path.exists(picture_path_to_delete):
            try:
                os.remove(picture_path_to_delete)
                print(f"DEBUG: Bild gelöscht: {picture_path_to_delete}")
            except OSError as e:
                print(f"ERROR: Konnte Bild nicht löschen {picture_path_to_delete}: {e}")

        # Annahme: Gesundheitsdaten sind eine Liste, und der Pfad ist in "result_link"
        for health_entry in person_to_delete.get("health_data", []):
            csv_path = Person.normalize_path(health_entry.get("result_link")) # Call as staticmethod
            if csv_path and os.path.exists(csv_path):
                try:
                    os.remove(csv_path)
                    print(f"DEBUG: CSV gelöscht: {csv_path}")
                except OSError as e:
                    print(f"ERROR: Konnte CSV nicht löschen {csv_path}: {e}")

        # Entferne die Person aus der Liste
        person_list = [p for p in person_list if p["id"] != person_id_to_delete]
        Person.save_person_data(person_list)
    else:
        raise ValueError(f"Person mit ID {person_id_to_delete} nicht gefunden.")