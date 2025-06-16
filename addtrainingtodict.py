from tinydb import TinyDB, Query

db = TinyDB('dbtests.json')
dp = TinyDB('dbperson.json')
def add_training_to_dict(Personid, date, sportart, dauer, distanz, puls, kalorien, anstrengung, star_rating, description, image=None, gpx_file=None, ekg_file=None):
    """
    Füge ein neues Training zu der Datenbank hinzu.
    
    Args:
        date (str): Datum des Trainings im Format 'YYYY-MM-DD'.
        sportart (str): Sportart des Trainings.
        dauer (int): Dauer des Trainings in Minuten.
        distanz (float): Distanz des Trainings in Kilometern.
        puls (int): Durchschnittlicher Puls während des Trainings.
        kalorien (int): Verbrauchte Kalorien während des Trainings.
        anstrengung (str): Anstrengung des Trainings, z.B. "good", "ok", "neutral", "acceptable", "bad".
        star_rating (int): Sternebewertung des Trainings von 1 bis 5.
        description (str): Beschreibung des Trainings.
        image (file, optional): Bild des Trainings. Standard ist None.
        gpx_file (file, optional): GPX-Datei des Trainings. Standard ist None.
        ekg_file (file, optional): EKG-Datei des Trainings. Standard ist None.
    """
    # Füge das Training zur Datenbank hinzu

    try:
        new_test_id = db.insert({
            "date": date,
            "sportart": sportart,
            "dauer": dauer,
            "distanz": distanz,
            "puls": puls,
            "kalorien": kalorien,
            "anstrengung": anstrengung,
            "star_rating": star_rating,
            "description": description,
            "image": image,
            "gpx_file": gpx_file,
            "ekg_file": ekg_file
        })
            

        Person = Query()
        person_doc = dp.get(doc_id=Personid) # Retrieve by doc_id is more direct

        if person_doc:
            # Hol die aktuelle Liste der EKG-Test-IDs (oder eine leere Liste, falls nicht vorhanden)
            # Nutze .get() um sicherzustellen, dass 'ekg_tests' existiert
            current_ekg_tests = person_doc.get('ekg_tests', [])

            # Füge die neue Test-ID hinzu, wenn sie noch nicht existiert
            if new_test_id not in current_ekg_tests:
                current_ekg_tests.append(new_test_id)
                
                # Aktualisiere den Personen-Datensatz in der 'dbperson' Datenbank
                dp.update({'ekg_tests': current_ekg_tests}, doc_ids=[Personid])
                print(f"EKG-Test-ID {new_test_id} erfolgreich zu Person {Personid} hinzugefügt.")
            else:
                print(f"EKG-Test-ID {new_test_id} war bereits für Person {Personid} registriert.")
        else:
            print(f"Fehler: Person mit ID {Personid} nicht in der 'dbperson' Datenbank gefunden.")

    except Exception as e:
        print(f"Ein Fehler ist aufgetreten: {e}")

if __name__ == "__main__":
    # Beispielaufruf der Funktion
    add_training_to_dict(
        Personid=1,
        date='2023-10-01',
        sportart='Laufen',
        dauer=30,
        distanz=5.0,
        puls=150,
        kalorien=300,
        anstrengung='good',
        star_rating=4,
        description='Ein tolles Lauftraining.',
        image=None,  # Hier könnte ein Bildpfad angegeben werden
        gpx_file=None,  # Hier könnte eine GPX-Datei angegeben werden
        ekg_file=None  # Hier könnte eine EKG-Datei angegeben werden
    )

    