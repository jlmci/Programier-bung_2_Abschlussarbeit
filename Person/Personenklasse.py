from tinydb import TinyDB, Query

# Datenbankpfade (könnten auch als Argumente an Methoden übergeben werden)
PERSON_DB_PATH = 'dbperson.json'
EKG_TESTS_DB_PATH = 'dbtests.json'

# TinyDB-Verbindungen (am besten einmalig initialisieren)
# Für dieses Beispiel initialisieren wir sie global.
# In größeren Anwendungen könntest du einen DB-Manager verwenden oder die DB-Objekte übergeben.
person_db = TinyDB(PERSON_DB_PATH)
ekg_tests_db = TinyDB(EKG_TESTS_DB_PATH)

# --- Person Klasse Definition ---
class Person:
    def __init__(self, doc_id: int, date_of_birth: int, firstname: str, lastname: str,
                 picture_path: str, gender: str, ekg_test_ids: list):
        self.doc_id = doc_id
        self.date_of_birth = date_of_birth
        self.firstname = firstname
        self.lastname = lastname
        self.picture_path = picture_path
        self.gender = gender
        self.ekg_test_ids = ekg_test_ids

        from datetime import datetime
        heute = datetime.now() # Holt das aktuelle Datum und die aktuelle Uhrzeit

        alter = heute.year - self.date_of_birth
        self.age = alter

    def __repr__(self):
        return (f"Person(ID={self.doc_id}, Name='{self.firstname} {self.lastname}', "
                f"DOB={self.date_of_birth}, Gender='{self.gender}', "
                f"EKG Tests={self.ekg_test_ids})")

    def get_full_name(self):
        return f"{self.firstname} {self.lastname}"

    def get_all_ekg_tests(self):
        tests = []
        for test_id in self.ekg_test_ids:
            ekg_test_data = ekg_tests_db.get(doc_id=test_id)
            if ekg_test_data:
                tests.append(ekg_test_data)
            else:
                print(f"Warnung: EKG-Test mit ID {test_id} (referenziert von Person {self.doc_id}) nicht gefunden in {EKG_TESTS_DB_PATH}")
        return tests

    @classmethod
    def from_tinydb_doc(cls, doc):
        """Erstellt eine Person-Instanz aus einem TinyDB-Dokumentobjekt."""
        return cls(
            doc_id=doc.doc_id,
            date_of_birth=doc.get('date_of_birth'),
            firstname=doc.get('firstname'),
            lastname=doc.get('lastname'),
            picture_path=doc.get('picture_path'),
            gender=doc.get('gender'),
            ekg_test_ids=doc.get('ekg_tests', [])
        )

    # --- NEUE STATIC METHOD HIER ---
    @staticmethod
    def get_by_id(person_id: int):
        """
        Gibt ein Person-Objekt basierend auf seiner doc_id zurück.
        
        Args:
            person_id (int): Die doc_id der zu suchenden Person.

        Returns:
            Person: Ein Person-Objekt, wenn gefunden, sonst None.
        """
        person_doc = person_db.get(doc_id=person_id)
        if person_doc:
            return Person.from_tinydb_doc(person_doc)
        return None

    def to_tinydb_doc(self):
        """Konvertiert die Person-Instanz zurück in ein für TinyDB geeignetes Dictionary-Format."""
        return {
            'date_of_birth': self.date_of_birth,
            'firstname': self.firstname,
            'lastname': self.lastname,
            'picture_path': self.picture_path,
            'gender': self.gender,
            'ekg_tests': self.ekg_test_ids
        }

    def save(self):
        """Speichert oder aktualisiert die Person-Instanz in der Datenbank."""
        if self.doc_id is None:
            self.doc_id = person_db.insert(self.to_tinydb_doc())
            print(f"Neue Person '{self.get_full_name()}' eingefügt mit ID: {self.doc_id}")
        else:
            person_db.update(self.to_tinydb_doc(), doc_ids=[self.doc_id])
            print(f"Person '{self.get_full_name()}' (ID: {self.doc_id}) aktualisiert.")

    def add_ekg_test_id(self, test_id: int):
        """Fügt eine EKG-Test-ID zur Liste der Person hinzu, wenn sie noch nicht existiert."""
        if test_id not in self.ekg_test_ids:
            self.ekg_test_ids.append(test_id)
            self.save()
            print(f"EKG-Test-ID {test_id} zu {self.get_full_name()} hinzugefügt.")
        else:
            print(f"EKG-Test-ID {test_id} existiert bereits für {self.get_full_name()}.")

    def remove_ekg_test_id(self, test_id: int):
        """Entfernt eine EKG-Test-ID aus der Liste der Person."""
        if test_id in self.ekg_test_ids:
            self.ekg_test_ids.remove(test_id)
            self.save()
            print(f"EKG-Test-ID {test_id} von {self.get_full_name()} entfernt.")
        else:
            print(f"EKG-Test-ID {test_id} nicht gefunden für {self.get_full_name()}.")
    
    def max_hr(self):
        maxhr = 220 - self.age
        return maxhr


# --- Beispielhafte Verwendung ---
if __name__ == "__main__":
    # Sicherstellen, dass die Datenbanken initialisiert sind
    if not person_db.all():
        print("Initialisiere dbperson.json mit Daten...")
        person_db.insert({
            "date_of_birth": 1967, "firstname": "Yannic", "lastname": "Heyer",
            "picture_path": "data/pictures/js.jpg", "gender": "male", "ekg_tests": [3, 5]
        })
        person_db.insert({
            "date_of_birth": 1989, "firstname": "Julian", "lastname": "Huber",
            "picture_path": "data/pictures/tb.jpg", "gender": "male", "ekg_tests": [1, 2]
        })
        person_db.insert({
            "date_of_birth": 1973, "firstname": "Yunus", "lastname": "Schmirander",
            "picture_path": "data/pictures/bl.jpg", "gender": "male", "ekg_tests": [4]
        })
        
    if not ekg_tests_db.all():
        print("Initialisiere dbtests.json mit Daten...")
        ekg_tests_db.insert({"date": "2023-10-01", "result_link": "data/ekg_data/01_Ruhe.txt"}) # doc_id 1
        ekg_tests_db.insert({"date": "11.3.2023", "result_link": "data/ekg_data/04_Belastung.txt"}) # doc_id 2
        ekg_tests_db.insert({"date": "10.2.2023", "result_link": "data/ekg_data/02_Ruhe.txt"}) # doc_id 3
        ekg_tests_db.insert({"date": "11.3.2023", "result_link": "data/ekg_data/03_Ruhe.txt"}) # doc_id 4
        ekg_tests_db.insert({"date": "05.05.2024", "result_link": "data/ekg_data/05_New.txt"}) # doc_id 5


    # --- Julian-Objekt über die neue staticmethod erstellen ---
    print("\n--- Erstelle Julian-Objekt mit Person.get_by_id(2) ---")
    julian = Person.get_by_id(2) # Julians doc_id ist 2 in deiner Datenbank

    if julian:
        print("Julian-Objekt erfolgreich erstellt:")
        print(julian)
        print(f"Julians EKG-Tests: {julian.get_all_ekg_tests()}")
    else:
        print("Julian wurde nicht gefunden (oder Person mit ID 2 existiert nicht).")

    print("\n--- Erstelle Yannic-Objekt mit Person.get_by_id(1) ---")
    yannic = Person.get_by_id(1) # Yannics doc_id ist 1
    if yannic:
        print("Yannic-Objekt erfolgreich erstellt:")
        print(yannic)
        print(f"Yannics EKG-Tests: {yannic.get_all_ekg_tests()}")
    else:
        print("Yannic wurde nicht gefunden (oder Person mit ID 1 existiert nicht).")

    print("\n--- Versuch, eine nicht-existente Person zu holen (ID 99) ---")
    non_existent_person = Person.get_by_id(99)
    if non_existent_person:
        print("Unerwartet: Person mit ID 99 gefunden:", non_existent_person)
    else:
        print("Person mit ID 99 nicht gefunden, wie erwartet.")


    # Datenbankverbindungen schließen
    person_db.close()
    ekg_tests_db.close()
    print("\nDatenbankverbindungen geschlossen.")