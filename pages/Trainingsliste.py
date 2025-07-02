
# File: pages/Trainingsliste.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import folium
import gpxpy
import gpxpy.gpx
from streamlit_folium import folium_static
import os
import sys
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import fitparse
from tinydb import TinyDB, Query

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from Module.ekgdata import EKGdata


IMAGE_DIR = "images"
DATA_DIR = "data"
UPLOAD_DIR = "uploaded_files"

def initialize_directories():
    """
    Stellt sicher, dass die für die Anwendung notwendigen Verzeichnisse existieren.
    Konkret werden die in `IMAGE_DIR`, `DATA_DIR` und `UPLOAD_DIR` definierten Pfade erstellt,
    falls sie noch nicht vorhanden sind.

    Args:
        None: Diese Funktion nimmt keine Argumente entgegen. Die Verzeichnisnamen
              (IMAGE_DIR, DATA_DIR, UPLOAD_DIR) werden als globale Konstanten angenommen.

    Returns:
        None: Diese Funktion gibt keinen Wert zurück. Sie führt eine Seitenwirkung aus,
              indem sie Verzeichnisse im Dateisystem erstellt.
    """
    os.makedirs(IMAGE_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(UPLOAD_DIR, exist_ok=True)


db = TinyDB('dbtests.json')
dp = TinyDB('dbperson.json')
Person = Query()
Test = Query()



def load_gpx_data(gpx_filepath):
    """
    Lädt und parst eine GPX-Datei vom angegebenen Pfad.

    Args:
        gpx_filepath (str): Der absolute oder relative Pfad zur GPX-Datei.

    Returns:
        gpxpy.gpx.GPX or None: Ein `gpxpy.gpx.GPX`-Objekt, das die geparsten GPX-Daten enthält,
                               wenn die Datei erfolgreich geladen und geparst wurde.
                               Gibt `None` zurück, wenn der Pfad leer ist, die Datei nicht existiert,
                               die Datei nicht gefunden wurde, ein Fehler beim Parsen auftritt
                               oder ein anderer unerwarteter Fehler während des Ladevorgangs auftritt.
                               Fehlermeldungen werden über `st.error` (falls Streamlit verfügbar ist) ausgegeben.
    """
    abs_filepath = gpx_filepath
    if not abs_filepath or not os.path.exists(abs_filepath):
        return None
    try:
        with open(abs_filepath, 'r') as gpx_file:
            gpx = gpxpy.parse(gpx_file)
            return gpx
    except FileNotFoundError:
        st.error(f"Fehler: GPX-Datei {repr(gpx_filepath)} wurde nicht gefunden.")
        return None
    except gpxpy.gpx.GPXException as e:
        st.error(f"Fehler beim Parsen der GPX-Datei {repr(gpx_filepath)}: {e}.")
        return None
    except Exception as e:
        st.error(f"Ein unerwarteter Fehler ist aufgetreten beim Laden von {repr(gpx_filepath)}: {e}")
        return None

def load_ekg_data(ekg_filepath):
    """
    Lädt EKG-Daten aus einer TXT- oder CSV-Datei, parst diese und erstellt ein EKGdata-Objekt.
    Die Funktion behandelt verschiedene Fehlerfälle wie fehlende Dateien, leere Dateien
    oder nicht unterstützte Dateiformate.

    Args:
        ekg_filepath (str): Der absolute oder relative Pfad zur EKG-Datei (.txt oder .csv).

    Returns:
        EKGdata or None: Ein instanziiertes EKGdata-Objekt, das die geladenen und verarbeiteten
                         EKG-Daten enthält. Gibt `None` zurück, wenn die Datei nicht gefunden wird,
                         leer ist, das Format nicht unterstützt wird oder ein Fehler beim Laden/Parsen auftritt.
    """
    abs_filepath = ekg_filepath 
    
    if not abs_filepath or not os.path.exists(abs_filepath):
        return None
    
    _, file_extension = os.path.splitext(abs_filepath)
    df = None
    try:
        if file_extension.lower() == '.txt':
            df = pd.read_csv(abs_filepath, sep='\t', header=None, names=['Messwerte in mV', 'Zeit in ms'])
        elif file_extension.lower() == '.csv':
            df = pd.read_csv(abs_filepath, header=None, names=['Messwerte in mV', 'Zeit in ms'])
        else:
            st.error(f"Fehler: Dateiformat {file_extension} wird nicht unterstützt. Bitte verwenden Sie .txt oder .csv.")
            return None

        if df.empty:
            st.warning(f"Warnung: Die Datei {abs_filepath} wurde geladen, ist aber leer.")
            return None

        ekg_dict_for_class = {
            "id": os.path.basename(abs_filepath),
            "date": "Unbekannt",
            "result_link": abs_filepath
        }
        
        ekg_obj = EKGdata(ekg_dict_for_class)
        
        if ekg_obj.df is None or ekg_obj.df.empty:
            st.error(f"Fehler: EKGdata-Klasse konnte die Daten aus {repr(abs_filepath)} nicht laden oder parsen.")
            return None
        
        return ekg_obj
        
    except pd.errors.EmptyDataError:
        st.warning(f"Warnung: Die Datei {abs_filepath} ist leer oder enthält keine Daten zum Parsen.")
        return None
    except Exception as e:
        st.error(f"Fehler beim Laden oder Verarbeiten der EKG-Datei {repr(abs_filepath)}: {e}")
        return None

def display_ekg_data_ui(ekg_obj, training_id_for_key):
    """
    Zeigt das EKG-Diagramm mit interaktiven Funktionen (Zeitbereichs-Slider) in einer Streamlit-Anwendung an.
    Die Funktion visualisiert EKG-Messwerte und optional die berechnete Herzfrequenz.

    Args:
        ekg_obj (EKGdata or None): Ein EKGdata-Objekt, das die EKG-Daten enthält.
                                   Wenn None oder das enthaltene DataFrame leer ist, wird kein Diagramm angezeigt.
        training_id_for_key (int or str): Eine eindeutige ID, die für die Generierung von Streamlit-Widget-Schlüsseln
                                          verwendet wird, um Konflikte zu vermeiden, wenn mehrere Diagramme auf einer Seite sind.

    Returns:
        None: Die Funktion rendert UI-Komponenten direkt in der Streamlit-Anwendung.
    """
    if ekg_obj is None or ekg_obj.df.empty:
        st.markdown("Keine EKG-Daten zum Anzeigen vorhanden.")
        return

    st.subheader("EKG-Analyse")
    
    
    t0 = ekg_obj.df["Zeit in ms"].iloc[0]
    ekg_obj.df["Zeit in s"] = (ekg_obj.df["Zeit in ms"] - t0) / 1000
    
    min_time = ekg_obj.df["Zeit in s"].min()
    max_time = ekg_obj.df["Zeit in s"].max()

    
    default_end_time = min(max_time, min_time + 10) if max_time > min_time else max_time
    
    time_range = st.slider(
        "Wähle den Zeitbereich (Sekunden)",
        min_value=float(min_time),
        max_value=float(max_time),
        value=(float(min_time), float(default_end_time)),
        step=0.1,
        key=f"ekg_time_slider_{training_id_for_key}"
    )

    start_time, end_time = time_range

    filtered_df = ekg_obj.df[(ekg_obj.df["Zeit in s"] >= start_time) & (ekg_obj.df["Zeit in s"] <= end_time)]

    if filtered_df.empty:
        st.warning("Keine Daten im ausgewählten Zeitbereich gefunden.")
        return

    
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=filtered_df["Zeit in s"],
            y=filtered_df["Messwerte in mV"],
            mode="lines",
            name="EKG-Messwerte", 
            line=dict(color="skyblue") 
        )
    )

   
    fig.update_xaxes(title="Zeit (s)")
    fig.update_yaxes(title="Messwerte (mV)")

   
    all_peaks = ekg_obj.find_peaks(respacing_factor=5)
    
    
    peak_times_all = ekg_obj.df.loc[all_peaks, "Zeit in s"]
    peak_values_all = ekg_obj.df.loc[all_peaks, "Messwerte in mV"]

    
    peaks_in_view_indices = peak_times_all[
        (peak_times_all >= start_time) & (peak_times_all <= end_time)
    ].index.tolist()

    if peaks_in_view_indices:
        
        peak_times_in_view = ekg_obj.df.loc[peaks_in_view_indices, "Zeit in s"]
        peak_values_in_view = ekg_obj.df.loc[peaks_in_view_indices, "Messwerte in mV"]


    heart_rate_df_full = None
    try:
        heart_rate_df_full = ekg_obj.estimate_heart_rate()
        
        
        heart_rate_df_in_view = heart_rate_df_full[
            (heart_rate_df_full["Zeit in s"] >= start_time) & 
            (heart_rate_df_full["Zeit in s"] <= end_time)
        ]

        if not heart_rate_df_in_view.empty:
            fig.add_trace(
                go.Scatter(
                    x=heart_rate_df_in_view["Zeit in s"],
                    y=heart_rate_df_in_view["Herzfrequenz (BPM)"],
                    mode="lines",
                    line=dict(color="green", dash="dot"),
                    yaxis="y2",
                    name="Herzfrequenz (BPM)"
                )
            )

            
            fig.update_layout(
                yaxis2=dict(
                    title="Herzfrequenz (BPM)",
                    overlaying="y",
                    side="right",
                    showgrid=False
                )
            )
    except ValueError as e:
        st.info(f"Herzfrequenz konnte nicht für diesen Zeitbereich berechnet werden: {e}")
    except Exception as e:
        st.warning(f"Fehler beim Laden der Herzfrequenzdaten: {e}")


    st.plotly_chart(fig, use_container_width=True, key=f"ekg_chart_{training_id_for_key}")

    
    if heart_rate_df_full is not None and not heart_rate_df_full.empty:
        average_hr_overall = heart_rate_df_full["Herzfrequenz (BPM)"].mean()
        st.markdown(f"**Durchschnittliche der EKG Datenreihe:** {average_hr_overall:.2f} BPM")
    else:
        st.info("Für dieses Training sind keine Herzfrequenzdaten zur Berechnung des Durchschnitts verfügbar.")

def load_fit_data(fit_filepath):
    """
    Lädt und parst eine FIT-Datei, extrahiert relevante Trainingsdaten und konvertiert
    diese in ein Pandas DataFrame. Dabei werden spezifische Felder wie Zeit, Geschwindigkeit,
    Herzfrequenz, Distanz, Trittfrequenz, Leistung sowie GPS-Koordinaten (Längen- und Breitengrad)
    berücksichtigt. Fehlende Datenpunkte werden mit der vorhergehenden und nachfolgenden gültigen
    Messung aufgefüllt.

    Während des Lade- und Verarbeitungsvorgangs wird ein Streamlit-Spinner angezeigt.

    Args:
        fit_filepath (str): Der absolute oder relative Pfad zur FIT-Datei.

    Returns:
        pandas.DataFrame or None: Ein Pandas DataFrame, das die extrahierten und bereinigten
                                  Trainingsdaten enthält. Die Spalten sind: 'time', 'velocity',
                                  'heart_rate', 'distance', 'cadence', 'power', 'latitude', 'longitude'.
                                  Gibt `None` zurück, wenn der angegebene Pfad ungültig ist, die Datei
                                  nicht existiert, ein Fehler beim Parsen der FIT-Datei auftritt oder
                                  ein anderer unerwarteter Fehler während des Vorgangs auftritt.
                                  Fehlermeldungen werden über `st.error` ausgegeben.
    """
    abs_filepath = fit_filepath
    if not abs_filepath or not os.path.exists(abs_filepath):
        return None
    
    
    with st.spinner(f"Lade und verarbeite FIT-Daten ..."):
        try:
            fitfile = fitparse.FitFile(abs_filepath)

            time_data = []
            velocity_data = []
            heartrate_data = []
            distance_data = []
            cadence_data = []
            power_data = []
            latitude_data = []
            longitude_data = []

            for record in fitfile.get_messages('record'):
                
                timestamp = None
                speed_val = None
                hr_val = None
                dist_val = None
                cadence_val = None
                power_val = None
                lat_val = None
                lon_val = None

                
                record_values = {data.name: data.value for data in record}

                
                timestamp = record_values.get("timestamp")
                speed_val = record_values.get("speed")
                hr_val = record_values.get("heart_rate")
                dist_val = record_values.get("distance")
                cadence_val = record_values.get("cadence")
                power_val = record_values.get("power")
                
                
                lat_semicircles = record_values.get("position_lat")
                lon_semicircles = record_values.get("position_long")

                if lat_semicircles is not None:
                    lat_val = lat_semicircles * (180.0 / 2**31)
                if lon_semicircles is not None:
                    lon_val = lon_semicircles * (180.0 / 2**31)

                
                time_data.append(timestamp)
                velocity_data.append(speed_val)
                heartrate_data.append(hr_val)
                distance_data.append(dist_val)
                cadence_data.append(cadence_val)
                power_data.append(power_val)
                latitude_data.append(lat_val)
                longitude_data.append(lon_val)

            df = pd.DataFrame({
                "time": time_data,
                "velocity": velocity_data,
                "heart_rate": heartrate_data,
                "distance": distance_data,
                "cadence": cadence_data,
                "power": power_data,
                "latitude": latitude_data,
                "longitude": longitude_data
            })
            
            df = df.fillna(method='ffill').fillna(method='bfill')
            return df

        except FileNotFoundError:
            st.error(f"Fehler: FIT-Datei {repr(fit_filepath)} wurde nicht gefunden.")
            return None
        except fitparse.FitParseError as e:
            st.error(f"Fehler beim Parsen der FIT-Datei {repr(fit_filepath)}: {e}.")
            return None
        except Exception as e:
            st.error(f"Ein unerwarteter Fehler ist aufgetreten beim Laden von {repr(fit_filepath)}: {e}")
            return None


# --- Power Curve Funktionen ---
def find_best_effort(df, window_size, power_col="power"):
    """
    Findet den besten durchschnittlichen Wert (z.B. maximale Leistung) über ein gleitendes Fenster
    in einem Pandas DataFrame.

    Args:
        df (pandas.DataFrame): Das Eingabe-DataFrame, das die Daten enthält.
                               Es muss die Spalte `power_col` (standardmäßig 'power') enthalten.
        window_size (int): Die Größe des gleitenden Fensters, über das der Durchschnitt berechnet wird.
                           Muss größer als 0 sein und darf die Anzahl der Zeilen im DataFrame nicht überschreiten.
        power_col (str, optional): Der Name der Spalte im DataFrame, die die numerischen Werte enthält,
                                   für die der beste Durchschnitt gesucht wird (z.B. Leistungswerte).
                                   Standardwert ist **"power"**.

    Returns:
        int or None: Der maximale durchschnittliche Wert als Ganzzahl, gefunden über das angegebene Fenster.
                     Gibt `None` zurück, wenn:
                     - Das DataFrame leer ist.
                     - Die angegebene Spalte (`power_col`) nicht existiert.
                     - Alle Werte in der Spalte `power_col` fehlen (NaN).
                     - Die `window_size` größer ist als die Anzahl der Zeilen im DataFrame.
    """
    if df.empty or power_col not in df.columns or df[power_col].isnull().all():
        return None
    
    
    if window_size > len(df):
        return None
    max_value = df[power_col].rolling(window=window_size).mean()
    return int(max_value.max()) if not max_value.empty and not pd.isna(max_value.max()) else None

def create_power_curve(df, power_col="power"):
    """
    Erstellt eine Power-Kurve aus den bereitgestellten Trainingsdaten.
    Die Power-Kurve zeigt die höchsten durchschnittlichen Leistungswerte (Best Effort)
    für verschiedene, vordefinierte Zeitfenster (z.B. 10 Sekunden, 1 Minute, 1 Stunde).

    Diese Funktion verwendet `find_best_effort`, um für jede Fenstergröße den maximalen
    durchschnittlichen Leistungswert im DataFrame zu ermitteln. Während der Berechnung
    wird ein Streamlit-Spinner angezeigt.

    Args:
        df (pandas.DataFrame): Das Eingabe-DataFrame, das die Leistungsdaten enthält.
                               Es muss eine Spalte mit dem Namen `power_col` (standardmäßig 'power') besitzen.
        power_col (str, optional): Der Name der Spalte im DataFrame, die die Leistungswerte in Watt enthält.
                                   Standardwert ist **"power"**.

    Returns:
        pandas.DataFrame: Ein DataFrame, das die Power-Kurve darstellt. Der Index dieses DataFrames
                          sind die Zeitfenster in Sekunden, und es enthält eine Spalte **'BestEffort'**
                          mit den entsprechenden maximalen durchschnittlichen Leistungswerten.
                          Gibt einen leeren DataFrame zurück, wenn:
                          - Das Eingabe-DataFrame leer ist.
                          - Die angegebene Leistungsspalte fehlt oder nur fehlende Werte enthält.
                          - Keine gültigen Fenstergrößen basierend auf der Datenlänge gefunden werden können.
                          - Nach der Berechnung keine Best-Effort-Werte ermittelt wurden.
    """
    
    window_sizes = [10, 30, 60, 120, 300, 600, 900, 1200, 1500, 1800, 3600, 7200] 
    best_efforts = {}
    
    if df.empty or power_col not in df.columns or df[power_col].isnull().all():
        return pd.DataFrame() 

    
    valid_window_sizes = [s for s in window_sizes if s < len(df)]

    if not valid_window_sizes:
        
        return pd.DataFrame() 

    
    with st.spinner("Berechne Power Curve..."):
        for size in valid_window_sizes:
            best_effort = find_best_effort(df, size, power_col)
            if best_effort is not None:
                best_efforts[size] = best_effort
    
    if not best_efforts:
        return pd.DataFrame() 

    power_curve_df = pd.DataFrame.from_dict(best_efforts, orient='index', columns=['BestEffort'])
    return power_curve_df

def format_time(s):
    """
    Formatiert eine gegebene Anzahl von Sekunden in eine prägnante, lesbare Zeitangabe.
    Die Ausgabe erfolgt in Sekunden (s), Minuten (m) oder Stunden (h), je nach Dauer.

    Args:
        s (int): Die Zeitdauer in Sekunden.

    Returns:
        str: Eine formatierte Zeichenkette, die die Dauer darstellt.
             Beispiele: "30s" für 30 Sekunden, "5m" für 300 Sekunden, "2h" für 7200 Sekunden.
    """
    if s < 60:
        return f"{s}s"
    elif s < 3600:
        return f"{s//60}m"
    else:
        return f"{s//3600}h"

def plot_power_curve(power_curve_df):
    """
    Plottet eine Leistungskurve (Power Curve) unter Verwendung von Plotly Express.

    Diese Funktion visualisiert die "Best Effort"-Leistungswerte über verschiedene Zeitdauern
    und bietet eine interaktive Darstellung der Leistungsfähigkeit.

    Args:
        power_curve_df (pandas.DataFrame): Ein DataFrame, das die Power Curve Daten enthält.
                                           Der Index des DataFrames sollte die Zeitdauern in Sekunden darstellen,
                                           und es muss eine Spalte mit dem Namen 'BestEffort' vorhanden sein,
                                           die die entsprechenden Leistungswerte in Watt enthält.

    Returns:
        plotly.graph_objects.Figure or None: Ein Plotly Figure-Objekt, das die interaktive Power Curve darstellt.
                                             Gibt `None` zurück, wenn der Eingabe-DataFrame leer ist.
    """
    if power_curve_df.empty:
        return None

    power_curve_df["formated_Time"] = power_curve_df.index.map(format_time)

    fig = px.line(
        power_curve_df,
        x="formated_Time",
        y="BestEffort",
        title="Power Curve"
    )

    fig.update_layout(
        xaxis_title="Zeit",
        yaxis_title="Leistung (Watt)",
        template="plotly_white"
    )
    return fig

# --- UI-Komponenten als Funktionen ---

def display_gpx_on_map_ui(gpx_object, training_id_for_key):
    """
    Zeigt einen GPX-Track auf einer interaktiven Folium-Karte in der Streamlit-Benutzeroberfläche an.
    Die Karte zentriert sich auf den Track und passt den Zoom so an, dass der gesamte Track sichtbar ist.

    Args:
        gpx_object (gpxpy.gpx.GPX or None): Ein `gpxpy.gpx.GPX`-Objekt, das die GPS-Trackdaten enthält.
                                             Wenn None oder keine Tracks/Segmente/Punkte vorhanden sind,
                                             wird eine entsprechende Meldung oder Warnung angezeigt.
        training_id_for_key (int or str): Eine eindeutige ID, die verwendet wird, um den Schlüssel
                                          für das Folium-Karten-Widget zu generieren. Dies ist wichtig,
                                          wenn mehrere Karten auf derselben Streamlit-Seite gerendert werden.

    Returns:
        None: Die Funktion rendert die Karte direkt in der Streamlit-Anwendung.
    """
    if not gpx_object or not gpx_object.tracks:
        st.markdown("Keine GPX-Daten zum Anzeigen vorhanden.")
        return

    has_points = False
    for track in gpx_object.tracks:
        for segment in track.segments:
            if segment.points:
                has_points = True
                break
        if has_points:
            break
    
    if not has_points:
        st.warning("GPX-Track hat keine Punkte für die Karte.")
        return

    first_point = None
    for track in gpx_object.tracks:
        if track.segments and track.segments[0].points:
            first_point = track.segments[0].points[0]
            break
    
    if not first_point:
        st.warning("Konnte keinen Startpunkt für die Karte finden.")
        return

    m = folium.Map(location=[first_point.latitude, first_point.longitude], zoom_start=13)

    for track in gpx_object.tracks:
        for segment in track.segments:
            points = [(point.latitude, point.longitude) for point in segment.points]
            if points:
                folium.PolyLine(points, color="red", weight=2.5, opacity=1).add_to(m)

    bounds = gpx_object.get_bounds()
    if bounds:
        m.fit_bounds([[bounds.min_latitude, bounds.min_longitude], [bounds.max_latitude, bounds.max_longitude]])

    folium_static(m)


def display_fit_map_ui(fit_df, training_id_for_key):
    """
    Displays a GPS track from FIT data on an interactive Folium map within a Streamlit application.

    The function extracts latitude and longitude from the provided DataFrame, filters out
    any invalid (NaN) coordinates, and then draws a polyline on the map. The map is
    automatically centered and zoomed to fit the entire track.

    Args:
        fit_df (pandas.DataFrame): A DataFrame containing FIT data, expected to have
                                   'latitude' and 'longitude' columns.
        training_id_for_key (int or str): A unique identifier used to generate a key
                                          for the Folium map widget. This is important
                                          when rendering multiple maps on the same
                                          Streamlit page to prevent key conflicts.

    Returns:
        None: This function renders the map directly into the Streamlit application.
              It displays warnings if no valid GPS coordinates are found or if there
              are too few points to draw a line.
    """
    # Filtere NaN-Werte für Lat/Lon, da `folium.PolyLine` keine NaNs verarbeiten kann
    track_points = fit_df[['latitude', 'longitude']].dropna()

    if track_points.empty:
        st.warning("Keine gültigen GPS-Koordinaten in der FIT-Datei gefunden.")
        return

    # Überprüfen, ob es mindestens zwei Punkte gibt, um eine Linie zu zeichnen
    if len(track_points) < 2:
        st.warning("Zu wenige GPS-Punkte in der FIT-Datei, um eine Strecke zu zeichnen.")
        return

    first_point = track_points.iloc[0]
    m = folium.Map(location=[first_point['latitude'], first_point['longitude']], zoom_start=13)

    points = [(row['latitude'], row['longitude']) for index, row in track_points.iterrows()]
    
    folium.PolyLine(points, color="blue", weight=2.5, opacity=1).add_to(m)

    # Versuche, die Karte an die Grenzen der Strecke anzupassen
    min_lat, max_lat = track_points['latitude'].min(), track_points['latitude'].max()
    min_lon, max_lon = track_points['longitude'].min(), track_points['longitude'].max()
    m.fit_bounds([[min_lat, min_lon], [max_lat, max_lon]])

    folium_static(m) 


def display_elevation_profile_ui(gpx_object, training_id_for_key):
    """
    Displays an elevation profile plot based on GPX data in a Streamlit application.

    The function extracts elevation and cumulative distance from the GPX object's tracks
    and segments, then plots this data using Plotly. The plot shows the elevation (m)
    against the distance (km) and is interactive.

    Args:
        gpx_object (gpxpy.gpx.GPX or None): A `gpxpy.gpx.GPX` object containing the
                                             GPS track data with elevation information.
                                             If None, or if no tracks/elevation data are found,
                                             an appropriate message or warning is displayed.
        training_id_for_key (int or str): A unique identifier used to generate a key
                                          for the Plotly chart widget. This is important
                                          when rendering multiple charts on the same
                                          Streamlit page to prevent key conflicts.

    Returns:
        None: This function renders the plot directly into the Streamlit application.
              It displays warnings if no elevation information is found in the GPX file.
    """
    if not gpx_object or not gpx_object.tracks:
        st.markdown("Keine GPX-Daten für das Höhenprofil vorhanden.")
        return

    elevations = []
    distances = []
    total_distance_km = 0.0

    for track in gpx_object.tracks:
        for segment in track.segments:
            for i, point in enumerate(segment.points):
                if point.elevation is not None:
                    elevations.append(point.elevation)
                    if i > 0:
                        dist_inc_m = point.distance_2d(segment.points[i-1])
                        total_distance_km += dist_inc_m / 1000.0
                    distances.append(total_distance_km)

    if not elevations:
        st.warning("Keine Höheninformationen in der GPX-Datei gefunden.")
        return

    df_elevation = pd.DataFrame({
        'Distanz (km)': distances,
        'Höhe (m)': elevations
    })

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_elevation['Distanz (km)'],
        y=df_elevation['Höhe (m)'],
        mode='lines',
        name='Höhenprofil',
        line=dict(width=3, color='rgb(63, 103, 126)'),
        fill='tozeroy',
        fillcolor='rgba(120, 171, 203, 0.4)'
    ))

    fig.update_layout(
        title_text='Höhenprofil',
        title_x=0.5,
        xaxis_title='Distanz (km)',
        yaxis_title='Höhe (m)',
        hovermode="x unified",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='black'),
        margin=dict(l=40, r=40, t=40, b=40)
    )

    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='LightGrey',
        zeroline=True,
        zerolinewidth=2,
        zerolinecolor='LightGrey'
    )
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='LightGrey',
        zeroline=True,
        zerolinewidth=2,
        zerolinecolor='LightGrey'
    )

    st.plotly_chart(fig, use_container_width=True, key=f"elevation_profile_{training_id_for_key}")

def display_fit_data_ui(fit_df, training_id_for_key):
    """
    Zeigt verschiedene Diagramme und Analysen basierend auf FIT-Trainingsdaten in einer Streamlit-Anwendung an.
    Dazu gehören interaktive Diagramme für Herzfrequenz, Leistung, Geschwindigkeit, Trittfrequenz und eine Power Curve,
    sowie eine Karte des Trainings-Tracks, falls GPS-Daten vorhanden sind.

    Die Funktion überprüft das Vorhandensein relevanter Daten in der FIT-Datei und bietet dem Benutzer Checkboxen an,
    um auszuwählen, welche Diagramme angezeigt werden sollen.

    Args:
        fit_df (pandas.DataFrame or None): Ein Pandas DataFrame, das die aus einer FIT-Datei geladenen Trainingsdaten enthält.
                                           Es wird erwartet, dass es Spalten wie 'time', 'heart_rate', 'power',
                                           'velocity', 'cadence', 'latitude', 'longitude' enthält.
                                           Wenn None oder leer, werden keine Daten angezeigt.
        training_id_for_key (int or str): Eine eindeutige ID, die für die Generierung der Streamlit-Widget-Schlüssel
                                          verwendet wird, um Konflikte zu vermeiden, wenn mehrere Trainings
                                          auf derselben Seite angezeigt werden.

    Returns:
        None: Die Funktion rendert UI-Komponenten und Diagramme direkt in der Streamlit-Anwendung.
              Sie gibt Warnungen oder Informationen aus, wenn bestimmte Daten nicht verfügbar sind
              oder Fehler bei der Datenverarbeitung auftreten.
    """
    if fit_df is None or fit_df.empty:
        st.markdown("Keine FIT-Daten zum Anzeigen vorhanden.")
        return

    st.subheader("FIT-Daten Analyse")

    if not pd.api.types.is_datetime64_any_dtype(fit_df['time']):
        try:
            with st.spinner("Konvertiere Zeitdaten..."):
                fit_df['time'] = pd.to_datetime(fit_df['time'])
        except Exception:
            st.error("Konnte 'time' Spalte in FIT-Daten nicht in Datetime konvertieren.")
            return

    
    has_gps_data = 'latitude' in fit_df.columns and 'longitude' in fit_df.columns and \
                   fit_df[['latitude', 'longitude']].dropna().shape[0] >= 2

    
    has_power_data = 'power' in fit_df.columns and fit_df['power'].dropna().any()

    st.markdown("Wähle die anzuzeigenden FIT-Diagramme:")
    
    
    checkboxes = []

    if has_power_data:
        checkboxes.append(("Power Curve", True, f"show_power_curve_{training_id_for_key}"))
    
    if has_gps_data:
        checkboxes.append(("Karte", True, f"show_fit_map_checkbox_{training_id_for_key}")) 
    
    checkboxes.append(("Herzfrequenz", False, f"show_hr_checkbox_{training_id_for_key}"))
    
    if has_power_data:
        checkboxes.append(("Leistung", False, f"show_power_checkbox_{training_id_for_key}"))
    
    checkboxes.append(("Geschwindigkeit", False, f"show_velocity_checkbox_{training_id_for_key}"))
    checkboxes.append(("Trittfrequenz", False, f"show_cadence_checkbox_{training_id_for_key}"))

    
    num_cols = min(len(checkboxes), 4) 
    cols = st.columns(num_cols)
    
    
    checkbox_states = {}

    for i, (label, default_value, key) in enumerate(checkboxes):
        with cols[i % num_cols]: 
            checkbox_states[label] = st.checkbox(label, value=default_value, key=key)

    # --- Display der Diagramme basierend auf den Checkbox-States ---

    
    if "Karte" in checkbox_states and checkbox_states["Karte"]:
        if has_gps_data:
            st.markdown("### FIT-Track auf Karte")
            
            with st.spinner("Rendere Karte..."):
                display_fit_map_ui(fit_df, training_id_for_key)
        else:
            st.info("Keine GPS-Daten in der FIT-Datei gefunden, daher keine Karte verfügbar.")
    elif "Karte" in checkbox_states: 
        pass


    
    if "Power Curve" in checkbox_states and checkbox_states["Power Curve"]:
        if has_power_data:
            st.markdown("### Power Curve")
            
            power_curve_df = create_power_curve(fit_df)
            if not power_curve_df.empty:
                
                with st.spinner("Erstelle Power Curve Diagramm..."):
                    fig_power_curve = plot_power_curve(power_curve_df)
                    st.plotly_chart(fig_power_curve, use_container_width=True, key=f"power_curve_{training_id_for_key}")
            else:
                st.info("Konnte Power Curve nicht erstellen, möglicherweise nicht genügend Leistungsdaten.")
        else: 
            st.info("Keine Leistungsdaten in der FIT-Datei gefunden, daher keine Power Curve verfügbar.")
    elif "Power Curve" in checkbox_states: 
        pass


    if "Herzfrequenz" in checkbox_states and checkbox_states["Herzfrequenz"]:
        if 'heart_rate' in fit_df.columns and fit_df['heart_rate'].dropna().any():
            with st.spinner("Erstelle Herzfrequenzdiagramm..."):
                fig_hr = px.line(fit_df, x='time', y='heart_rate', title='Herzfrequenz über die Zeit',
                                 labels={'time': 'Zeit', 'heart_rate': 'Herzfrequenz (bpm)'})
                fig_hr.update_layout(hovermode="x unified")
                st.plotly_chart(fig_hr, use_container_width=True, key=f"hr_chart_{training_id_for_key}")
        else:
            st.info("Keine Herzfrequenzdaten in der FIT-Datei gefunden.")
    
    if "Leistung" in checkbox_states and checkbox_states["Leistung"]:
        if has_power_data:
            with st.spinner("Erstelle Leistungsdiagramm..."):
                fig_power = px.line(fit_df, x='time', y='power', title='Leistung über die Zeit',
                                     labels={'time': 'Zeit', 'power': 'Leistung (Watt)'})
                fig_power.update_layout(hovermode="x unified")
                st.plotly_chart(fig_power, use_container_width=True, key=f"power_chart_{training_id_for_key}")
        else:
            st.info("Keine Leistungsdaten in der FIT-Datei gefunden.")

    if "Geschwindigkeit" in checkbox_states and checkbox_states["Geschwindigkeit"]:
        if 'velocity' in fit_df.columns and fit_df['velocity'].dropna().any():
            with st.spinner("Erstelle Geschwindigkeitsdiagramm..."):
                fig_vel = px.line(fit_df, x='time', y='velocity', title='Geschwindigkeit über die Zeit',
                                     labels={'time': 'Zeit', 'velocity': 'Geschwindigkeit (m/s)'})
                fig_vel.update_layout(hovermode="x unified")
                st.plotly_chart(fig_vel, use_container_width=True, key=f"velocity_chart_{training_id_for_key}")
        else:
            st.info("Keine Geschwindigkeitsdaten in der FIT-Datei gefunden.")

    if "Trittfrequenz" in checkbox_states and checkbox_states["Trittfrequenz"]:
        if 'cadence' in fit_df.columns and fit_df['cadence'].dropna().any():
            with st.spinner("Erstelle Trittfrequenzdiagramm..."):
                fig_cad = px.line(fit_df, x='time', y='cadence', title='Trittfrequenz über die Zeit',
                                     labels={'time': 'Zeit', 'cadence': 'Trittfrequenz (rpm)'})
                fig_cad.update_layout(hovermode="x unified")
                st.plotly_chart(fig_cad, use_container_width=True, key=f"cadence_chart_{training_id_for_key}")
        else:
            st.info("Keine Trittfrequenzdaten in der FIT-Datei gefunden.")


# --- Callback-Funktionen ---
def set_training_to_edit(training_id):
    """
    Sets the ID of the training to be edited in Streamlit's session state
    and then redirects the user to the "add workout" page for editing.

    This function is typically called when a user selects a specific training
    from a list (e.g., on a 'Trainingsliste' page) and wants to modify its details.

    Args:
        training_id (str or int): The unique identifier of the training
                                  that is intended for editing. This ID
                                  will be stored in `st.session_state.editing_training_id`.

    Returns:
        None: This function does not return a value but triggers a page redirection
              within the Streamlit application.
    """
    st.session_state.editing_training_id = training_id
    if 'last_editing_id' in st.session_state:
        del st.session_state.last_editing_id
    st.switch_page("pages/add workout.py")

def delete_training_from_db(training_id, person_id):
    """
    Löscht ein spezifisches Training aus der Trainingsdatenbank und entfernt dessen ID
    aus der Liste der EKG-Tests, die einer Person in der Personendatenbank zugeordnet sind.

    Diese Funktion führt zwei Hauptschritte aus:
    1. Löscht den Trainingsdatensatz direkt aus der Trainingsdatenbank (`db`).
    2. Sucht den entsprechenden Personendatensatz in der Personendatenbank (`dp`)
       und entfernt die `training_id` aus deren `ekg_tests`-Liste.

    Args:
        training_id (int or str): Die eindeutige ID des zu löschenden Trainings.
                                   Dies sollte dem `doc_id` in der `db`-Datenbank entsprechen.
        person_id (int or str): Die eindeutige ID der Person, der das Training zugeordnet ist.
                                Dies sollte dem `doc_id` in der `dp`-Datenbank entsprechen.

    Returns:
        None: Die Funktion gibt keinen Wert zurück. Sie zeigt Erfolgs- oder Fehlermeldungen
              direkt in der Streamlit-Benutzeroberfläche an (`st.success`, `st.warning`, `st.error`).
    """
    try:
        db.remove(doc_ids=[training_id])
        st.success(f"Training mit ID {training_id} erfolgreich aus der Trainingsdatenbank gelöscht.")

        person_doc = dp.get(doc_id=int(person_id))
        if person_doc:
            current_ekg_tests = person_doc.get('ekg_tests', [])
            if training_id in current_ekg_tests:
                current_ekg_tests.remove(training_id)
                dp.update({'ekg_tests': current_ekg_tests}, doc_ids=[int(person_id)])
                st.success(f"Training ID {training_id} erfolgreich aus der Personendatenbank für Person {person_id} entfernt.")
            else:
                st.warning(f"Training ID {training_id} wurde nicht in der EKG-Testliste für Person {person_id} gefunden.")
        else:
            st.error(f"Fehler: Person mit ID {person_id} nicht in der Personendatenbank gefunden.")
    except Exception as e:
        st.error(f"Fehler beim Löschen des Trainings: {e}")

# --- UI für Details und Liste ---

def display_training_details_ui(training_data, on_delete_callback, on_edit_callback, expanded=False):
    """
    Displays the detailed information of a single training session within a Streamlit expander.
    It includes general training metrics, an associated image (if available), and visual analyses
    from linked GPX, FIT, and EKG files. Users can also choose to edit or delete the training.

    Args:
        training_data (dict or tinydb.database.Document): A dictionary-like object containing
                                                          the training details. It should have
                                                          keys like 'name', 'date', 'sportart',
                                                          'dauer', 'distanz', 'puls', 'kalorien',
                                                          'avg_speed_kmh', 'elevation_gain_pos',
                                                          'elevation_gain_neg', 'anstrengung',
                                                          'star_rating', 'description', 'image',
                                                          'gpx_file', 'fit_file', 'ekg_file'.
                                                          If it's a TinyDB Document, it might
                                                          have a `doc_id` attribute.
        on_delete_callback (callable): A function to call when the delete button is pressed.
                                       It should accept `training_id` and `person_id` as arguments.
        on_edit_callback (callable): A function to call when the edit button is pressed.
                                     It should accept `training_id` as an argument.
        expanded (bool, optional): If True, the expander will be open by default when rendered.
                                   Defaults to False.

    Returns:
        None: This function directly renders UI components into the Streamlit application.
              It handles data loading and display for various file types and provides
              interactive buttons for editing and deleting.
    """
    training_id_str = str(training_data.doc_id) if hasattr(training_data, 'doc_id') else str(training_data.get('id', 'no_id'))
    
    expander_title = f"**{training_data['name']}** - {training_data['date']} ({training_data['sportart']})"
    
    with st.expander(expander_title, expanded=expanded):
        st.markdown(f"<span style='font-size:30px; font-weight:bold'>{training_data['name']}</span>", unsafe_allow_html=True)
        st.markdown(f"**Datum:** {training_data['date']}")
        st.markdown(f"**Sportart:** {training_data['sportart']}")
        
        duration_minutes = training_data.get('dauer')
        if duration_minutes is not None:
            try:
                duration_minutes = int(duration_minutes)
                hours = duration_minutes // 60
                minutes = duration_minutes % 60
                duration_display = f"{hours} Std. {minutes} Min."
            except ValueError:
                duration_display = "N/A"
        else:
            duration_display = "N/A"
        st.markdown(f"**Dauer:** {duration_display}") 

        st.markdown(f"**Distanz:** {training_data.get('distanz', 'N/A')} km")
        st.markdown(f"**Durchschnittlicher Puls:** {training_data.get('puls', 'N/A')} bpm ")
        st.markdown(f"**Kalorien verbraucht:** {training_data.get('kalorien', 'N/A')} kcal")
        
        avg_speed = training_data.get('avg_speed_kmh')
        if avg_speed is not None:
            st.markdown(f"**Durchschnittsgeschwindigkeit:** {avg_speed:.2f} km/h")
        
        elevation_gain_pos = training_data.get('elevation_gain_pos')
        if elevation_gain_pos is not None:
            st.markdown(f"**Höhenmeter aufwärts:** {elevation_gain_pos} m")
        elevation_gain_neg = training_data.get('elevation_gain_neg')
        if elevation_gain_neg is not None:
            st.markdown(f"**Höhenmeter abwärts:** {elevation_gain_neg} m")
        
        anstrengung_map = {
            "good": "😃 Sehr leicht",
            "ok": "🙂 leicht",
            "neutral": "😐 Neutral",
            "acceptable": "😟 anstrengend",
            "bad": "🥵 sehr anstrengend"
        }
        st.markdown(f"**Anstrengung:** {anstrengung_map.get(training_data.get('anstrengung', ''), 'N/A')}")
        st.markdown(f"**Bewertung:** {'⭐' * training_data.get('star_rating', 0)}")

        description = training_data.get('description', '')
        st.markdown(f"**Beschreibung:** : {description if description else 'Keine Beschreibung vorhanden.'}")
        

        image_path_from_db = training_data.get('image')
        local_image_path = image_path_from_db
        if local_image_path and os.path.exists(local_image_path):
            st.image(local_image_path, caption=f"", use_container_width=True)
        elif image_path_from_db and image_path_from_db != "-":
            st.warning(f"Bilddatei {repr(image_path_from_db)} konnte nicht gefunden werden.")

        st.markdown("---")
        gpx_file_path_from_db = training_data.get('gpx_file')
        # Spinner für GPX-Daten
        with st.spinner("Lade GPX-Daten..."):
            gpx_data = load_gpx_data(gpx_file_path_from_db)
        if gpx_data:
            st.markdown("### GPX-Track auf Karte")
            # Spinner für die Kartendarstellung
            with st.spinner("Rendere GPX-Karte..."):
                display_gpx_on_map_ui(gpx_data, training_id_str)
            st.markdown("### Höhenprofil")
            # Spinner für das Höhenprofil
            with st.spinner("Erstelle Höhenprofil..."):
                display_elevation_profile_ui(gpx_data, training_id_str)
        else:
            if gpx_file_path_from_db and gpx_file_path_from_db != "-":
                st.warning(f"GPX-Datei {repr(gpx_file_path_from_db)} konnte nicht geladen oder geparst werden.")
            else:
                st.markdown("Keine GPX-Datei verlinkt.")

        fit_file_path_from_db = training_data.get('fit_file')
        # Spinner für FIT-Daten ist bereits in load_fit_data()
        fit_data_df = load_fit_data(fit_file_path_from_db)
        if fit_data_df is not None and not fit_data_df.empty:
            st.markdown("---")
            st.markdown("### FIT-Dateianalyse")
            display_fit_data_ui(fit_data_df, training_id_str)
        else:
            if fit_file_path_from_db and fit_file_path_from_db != "-":
                st.warning(f"FIT-Datei {repr(fit_file_path_from_db)} konnte nicht geladen oder geparst werden.")
            else:
                st.markdown("Keine FIT-Datei verlinkt.")

        ekg_file_path_from_db = training_data.get('ekg_file')
        with st.spinner("Lade EKG-Daten..."):
            ekg_obj = load_ekg_data(ekg_file_path_from_db)
        if ekg_obj:
            st.markdown("---")
            display_ekg_data_ui(ekg_obj, training_id_str)
        else:
            if ekg_file_path_from_db and ekg_file_path_from_db != "-":
                st.warning(f"EKG-Datei {repr(ekg_file_path_from_db)} konnte nicht geladen werden.")
            # This 'else' block ensures that "Keine weiteren Dateien verlinkt." is only shown if no other file types were found
            elif not (gpx_file_path_from_db and gpx_file_path_from_db != "-") and \
                 not (fit_file_path_from_db and fit_file_path_from_db != "-"):
                st.markdown("Keine weiteren Dateien verlinkt.")

        st.markdown("---")

        col_edit, col_delete, col_spacer = st.columns([0.2, 0.2, 0.6])
        with col_edit:
            if st.button("Training Bearbeiten 📝", key=f"edit_btn_{training_id_str}"):
                on_edit_callback(training_data.doc_id)
        with col_delete:
            if st.button("Training Löschen 🗑️", key=f"delete_btn_{training_id_str}"):
                on_delete_callback(training_data.doc_id, st.session_state.current_user_id)
                st.success(f"Training '{training_data['name']}' vom {training_data['date']} wurde gelöscht.")
                st.rerun()

def display_training_list_ui(trainings):
    """
    Zeigt eine Liste aller Trainings für die aktuell ausgewählte Person an.
    Jedes Training wird in einem aufklappbaren Expander dargestellt, der detaillierte Informationen
    und Optionen zum Bearbeiten oder Löschen des Trainings bietet. Die Liste ist nach Datum absteigend sortiert,
    und das neueste Training wird standardmäßig aufgeklappt angezeigt.

    Args:
        trainings (list): Eine Liste von Trainings-Dokumenten (z.B. TinyDB-Dokumente),
                          wobei jedes Dokument ein Wörterbuch mit Trainingsdetails wie
                          'name', 'date', 'sportart', 'dauer', etc. ist und idealerweise
                          ein `doc_id`-Attribut für die eindeutige Identifizierung hat.

    Returns:
        None: Die Funktion rendert die Trainingsliste direkt in der Streamlit-Benutzeroberfläche.
              Wenn keine Trainings vorhanden sind, wird eine entsprechende Informationsmeldung
              angezeigt und ein Button zum Hinzufügen von Trainings angeboten.
    """
    if not trainings:
        st.info("Es sind noch keine Trainings für diese Person vorhanden. Füge Trainings hinzu, damit sie hier angezeigt werden! ")
        if st.button("Trainings hinzufügen"):
            st.switch_page("pages/add workout.py")
        return

    sorted_trainings = sorted(
        trainings,
        key=lambda x: datetime.strptime(x['date'], "%Y-%m-%d"),
        reverse=True
    )

    if 'last_expanded_training_id' not in st.session_state:
        st.session_state.last_expanded_training_id = None

    if sorted_trainings and st.session_state.get('initial_expand_done', False) == False:
        st.session_state.last_expanded_training_id = sorted_trainings[0].doc_id
        st.session_state.initial_expand_done = True

    for i, training in enumerate(sorted_trainings):
        is_expanded = (training.doc_id == st.session_state.last_expanded_training_id)
        display_training_details_ui(training, delete_training_from_db, set_training_to_edit, expanded=is_expanded)

# --- Datenbank-Operationen ---

def get_trainings_for_current_user():
    """
    Loads all training records associated with the currently selected user from the TinyDB.

    This function retrieves the `current_user_id` from Streamlit's session state,
    then fetches the corresponding person's data from the person database (`dp`).
    It uses the list of `ekg_tests` (which are essentially training IDs) linked to that person
    to filter and retrieve only the relevant training records from the main training database (`db`).

    Returns:
        list: A list of TinyDB Document objects, where each object represents a training
              record belonging to the current user. Returns an empty list if no user
              is selected, the user data is not found, or the user has no linked trainings.
    """

    if "current_user_id" not in st.session_state:
        return []
    
    person_doc_id = int(st.session_state["current_user_id"])
    person_data = dp.get(doc_id=person_doc_id)

    if person_data and 'ekg_tests' in person_data:
        ekg_test_ids = person_data['ekg_tests']
        all_trainings = db.all()
        # Stellen Sie sicher, dass doc_id in den Trainingsdaten vorhanden ist, bevor Sie darauf zugreifen
        user_trainings = [t for t in all_trainings if hasattr(t, 'doc_id') and t.doc_id in ekg_test_ids]
        return user_trainings
    return []

# --- Hauptanwendung ---
def main():
    st.title("Dein Trainings-Tagebuch 🏋️‍♂️")
    st.markdown("---")

    initialize_directories()



    if "current_user_id" not in st.session_state:
        st.info("Bitte warten")
        return

    if 'editing_training_id' not in st.session_state:
        st.session_state.editing_training_id = None
    
    if 'initial_expand_done' not in st.session_state:
        st.session_state.initial_expand_done = False

    st.subheader("Deine Trainingsübersicht")
    trainings_for_user = get_trainings_for_current_user()
    display_training_list_ui(trainings_for_user)

if __name__ == "__main__":
    main()