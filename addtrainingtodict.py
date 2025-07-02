from tinydb import TinyDB, Query

db = TinyDB('dbtests.json')
dp = TinyDB('dbperson.json')
def add_training_to_dict(Personid, date, sportart, dauer, distanz, puls, kalorien, anstrengung, star_rating, description, image=None, gpx_file=None, ekg_file=None, fit_file=None, avg_speed_kmh=0.0, elevation_gain_pos=0, elevation_gain_neg=0):
    """
    Füge ein neues Training zu der Datenbank hinzu.
    
    Args:
        Personid (int): Die ID der Person, der das Training zugeordnet werden soll.
        date (str): Datum des Trainings im Format 'YYYY-MM-DD'.
        sportart (str): Sportart des Trainings.
        dauer (int): Dauer des Trainings in Minuten.
        distanz (float): Distanz des Trainings in Kilometern.
        puls (int): Durchschnittlicher Puls während des Trainings.
        kalorien (int): Verbrauchte Kalorien während des Trainings.
        anstrengung (str): Anstrengung des Trainings, z.B. "good", "ok", "neutral", "acceptable", "bad".
        star_rating (int): Sternebewertung des Trainings von 1 bis 5.
        description (str): Beschreibung des Trainings.
        image (str, optional): Base64-kodiertes Bild des Trainings. Standard ist None.
        gpx_file (str, optional): Base64-kodierte GPX-Datei des Trainings. Standard ist None.
        ekg_file (str, optional): Base64-kodierte EKG-Datei des Trainings. Standard ist None.
        fit_file (str, optional): Base64-kodierte FIT-Datei des Trainings. Standard ist None.
        avg_speed_kmh (float, optional): Durchschnittsgeschwindigkeit in km/h. Standard ist 0.0.
        elevation_gain_pos (int, optional): Höhenmeter aufwärts in Metern. Standard ist 0.
        elevation_gain_neg (int, optional): Höhenmeter abwärts in Metern. Standard ist 0.
    """
    # Füge das Training zur Datenbank hinzu

    try:
        new_test_id = db.insert({
            "name": "", # Name wird jetzt vom Formular übergeben
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
            "ekg_file": ekg_file,
            "fit_file": fit_file,
            "avg_speed_kmh": avg_speed_kmh,
            "elevation_gain_pos": elevation_gain_pos,
            "elevation_gain_neg": elevation_gain_neg
        })
        print(f"Neuer Test mit ID {new_test_id} hinzugefügt.")

        # Aktualisiere den Personen-Datensatz in der 'dbperson' Datenbank
        # Finde den Personen-Datensatz anhand der Personid
        PersonQuery = Query()
        person_doc = dp.get(doc_id=Personid)

        if person_doc:
            # Stelle sicher, dass 'ekg_tests' ein Array ist (oder initialisiere es, wenn es fehlt)
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
        star_rating=5,
        description='Ein schöner Morgenlauf.',
        image=None, # Hier würde ein Base64-String stehen
        gpx_file=None, # Hier würde ein Base64-String stehen
        ekg_file=None, # Hier würde ein Base64-String stehen
        fit_file=None, # Hier würde ein Base64-String stehen
        avg_speed_kmh=10.0,
        elevation_gain_pos=50,
        elevation_gain_neg=20
    )
