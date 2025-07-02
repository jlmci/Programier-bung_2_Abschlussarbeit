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
from auswertungen.ekgdata import EKGdata

# --- Konfiguration und Initialisierung ---
IMAGE_DIR = "images"
DATA_DIR = "data"
UPLOAD_DIR = "uploaded_files"

def initialize_directories():
    """Stellt sicher, dass notwendige Verzeichnisse existieren."""
    os.makedirs(IMAGE_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- Datenbank-Initialisierung ---
db = TinyDB('dbtests.json')
dp = TinyDB('dbperson.json')
Person = Query()
Test = Query()

# --- Hilfsfunktionen für die Datenverarbeitung und Dateihandhabung ---

def load_gpx_data(gpx_filepath):
    """
    Lädt und parst eine GPX-Datei.
    Gibt ein gpxpy.GPX-Objekt oder None bei Fehler zurück.
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
    Lädt EKG-Daten aus einer TXT- oder CSV-Datei, erstellt ein EKGdata-Objekt
    und gibt das Plotly-Diagramm der EKG-Zeitreihe zurück.
    """
    abs_filepath = ekg_filepath 
    
    if not abs_filepath or not os.path.exists(abs_filepath):
        if abs_filepath == None:
            st.write("Keine EKG-Datei verlinkt.")
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
        
        fig = ekg_obj.plot_time_series()
        st.plotly_chart(fig, use_container_width=True)
        return True
        
    except pd.errors.EmptyDataError:
        st.warning(f"Warnung: Die Datei {abs_filepath} ist leer oder enthält keine Daten zum Parsen.")
        return None
    except Exception as e:
        st.error(f"Fehler beim Laden oder Verarbeiten der EKG-Datei {repr(abs_filepath)}: {e}")
        return None

def load_fit_data(fit_filepath):
    """
    Lädt und parst eine FIT-Datei und extrahiert relevante Daten, inkl. GPS-Koordinaten.
    Handhabt fehlende Felder, indem sie None setzt.
    Gibt ein Pandas DataFrame mit Zeit, Herzfrequenz, Leistung, Lat/Lon usw. zurück oder None bei Fehler.
    Ein Spinner wird angezeigt, während die Daten geladen und verarbeitet werden.
    """
    abs_filepath = fit_filepath
    if not abs_filepath or not os.path.exists(abs_filepath):
        return None
    
    # Spinner für FIT-Dateiladevorgang
    with st.spinner(f"Lade und verarbeite FIT-Daten aus {os.path.basename(abs_filepath)}..."):
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
                # Initialize all values to None for each record
                timestamp = None
                speed_val = None
                hr_val = None
                dist_val = None
                cadence_val = None
                power_val = None
                lat_val = None
                lon_val = None

                # Collect all data points for the current record
                record_values = {data.name: data.value for data in record}

                # Use .get() method with a default of None to safely access values
                timestamp = record_values.get("timestamp")
                speed_val = record_values.get("speed")
                hr_val = record_values.get("heart_rate")
                dist_val = record_values.get("distance")
                cadence_val = record_values.get("cadence")
                power_val = record_values.get("power")
                
                # GPS coordinates often need conversion from semicircles to degrees
                lat_semicircles = record_values.get("position_lat")
                lon_semicircles = record_values.get("position_long")

                if lat_semicircles is not None:
                    lat_val = lat_semicircles * (180.0 / 2**31)
                if lon_semicircles is not None:
                    lon_val = lon_semicircles * (180.0 / 2**31)

                # Append values to lists
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
            # Füllen Sie NaN-Werte vor und zurück auf, um durchgehende Linien in Plots zu gewährleisten
            # Dies ist besonders nützlich, wenn Daten für kurze Zeitspannen fehlen.
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
    """Findet den besten Durchschnittswert für eine gegebene Fenstergröße."""
    if df.empty or power_col not in df.columns or df[power_col].isnull().all():
        return None
    
    # Stellen Sie sicher, dass der window_size nicht größer ist als die DataFrame-Länge
    if window_size > len(df):
        return None
    max_value = df[power_col].rolling(window=window_size).mean()
    return int(max_value.max()) if not max_value.empty and not pd.isna(max_value.max()) else None

def create_power_curve(df, power_col="power"):
    """
    Erstellt eine Power-Kurve aus dem DataFrame.
    """
    # Standard-Fenstergrößen für die Power-Kurve in Sekunden
    window_sizes = [10, 30, 60, 120, 300, 600, 900, 1200, 1500, 1800, 3600, 7200] 
    best_efforts = {}
    
    if df.empty or power_col not in df.columns or df[power_col].isnull().all():
        return pd.DataFrame() # Leeren DataFrame zurückgeben, wenn keine Power-Daten

    # Filtern der Fenstergrößen, die größer sind als die Länge des Dataframes
    valid_window_sizes = [s for s in window_sizes if s < len(df)]

    if not valid_window_sizes:
        #st.warning("Keine gültigen Fenstergrößen für die Power Curve Berechnung basierend auf der Datenlänge.")
        return pd.DataFrame() # Leeren DataFrame zurückgeben

    # Spinner für die Power Curve Berechnung
    with st.spinner("Berechne Power Curve..."):
        for size in valid_window_sizes:
            best_effort = find_best_effort(df, size, power_col)
            if best_effort is not None:
                best_efforts[size] = best_effort
    
    if not best_efforts:
        return pd.DataFrame() # Leeren DataFrame zurückgeben

    power_curve_df = pd.DataFrame.from_dict(best_efforts, orient='index', columns=['BestEffort'])
    return power_curve_df

def format_time(s):
    """Formatiert Sekunden in lesbare Zeitangaben (s, m, h)."""
    if s < 60:
        return f"{s}s"
    elif s < 3600:
        return f"{s//60}m"
    else:
        return f"{s//3600}h"

def plot_power_curve(power_curve_df):
    """Plottet die Power-Kurve mit Plotly."""
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
    """Zeigt einen GPX-Track auf einer Folium-Karte an."""
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
    """Zeigt den Track aus FIT-Daten auf einer Folium-Karte an."""
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
    """Zeigt ein Höhenprofil basierend auf GPX-Daten an."""
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
    """Zeigt Herzfrequenz-, Leistungs-, Geschwindigkeits-, Trittfrequenzkurven und Power Curve aus FIT-Daten an."""
    if fit_df is None or fit_df.empty:
        st.markdown("Keine FIT-Daten zum Anzeigen vorhanden.")
        return

    st.subheader("FIT-Daten Analyse")

    if not pd.api.types.is_datetime64_any_dtype(fit_df['time']):
        try:
            # Spinner für Datetime-Konvertierung
            with st.spinner("Konvertiere Zeitdaten..."):
                fit_df['time'] = pd.to_datetime(fit_df['time'])
        except Exception:
            st.error("Konnte 'time' Spalte in FIT-Daten nicht in Datetime konvertieren.")
            return

    # Überprüfen, ob GPS-Daten vorhanden sind (mindestens 2 nicht-NaN-Punkte für eine Linie)
    has_gps_data = 'latitude' in fit_df.columns and 'longitude' in fit_df.columns and \
                   fit_df[['latitude', 'longitude']].dropna().shape[0] >= 2

    # Überprüfen, ob Leistungsdaten vorhanden sind
    has_power_data = 'power' in fit_df.columns and fit_df['power'].dropna().any()

    st.markdown("Wähle die anzuzeigenden FIT-Diagramme:")
    
    # Eine Liste für die Checkboxen, um sie dynamisch zu erstellen
    checkboxes = []

    if has_power_data:
        checkboxes.append(("Power Curve", True, f"show_power_curve_{training_id_for_key}"))
    
    if has_gps_data:
        checkboxes.append(("Strecke (FIT-Karte)", True, f"show_fit_map_checkbox_{training_id_for_key}")) 
    
    checkboxes.append(("Herzfrequenz", False, f"show_hr_checkbox_{training_id_for_key}"))
    
    if has_power_data:
        checkboxes.append(("Leistung", False, f"show_power_checkbox_{training_id_for_key}"))
    
    checkboxes.append(("Geschwindigkeit", False, f"show_velocity_checkbox_{training_id_for_key}"))
    checkboxes.append(("Trittfrequenz", False, f"show_cadence_checkbox_{training_id_for_key}"))

    # Erstelle Spalten basierend auf der Anzahl der Checkboxen (max. 4 pro Zeile)
    num_cols = min(len(checkboxes), 4) # Beschränke auf max 4 Spalten
    cols = st.columns(num_cols)
    
    # Dictionary, um den Status der Checkboxen zu speichern
    checkbox_states = {}

    for i, (label, default_value, key) in enumerate(checkboxes):
        with cols[i % num_cols]: # Platziere Checkboxen in den Spalten, zyklisch wiederholend
            checkbox_states[label] = st.checkbox(label, value=default_value, key=key)

    # --- Display der Diagramme basierend auf den Checkbox-States ---

    # Display FIT Map
    if "Strecke (FIT-Karte)" in checkbox_states and checkbox_states["Strecke (FIT-Karte)"]:
        if has_gps_data:
            st.markdown("### FIT-Track auf Karte")
            # Spinner für die Kartendarstellung
            with st.spinner("Rendere Karte..."):
                display_fit_map_ui(fit_df, training_id_for_key)
        else:
            st.info("Keine GPS-Daten in der FIT-Datei gefunden, daher keine Karte verfügbar.")
    elif "Strecke (FIT-Karte)" in checkbox_states: 
        pass


    # Display Power Curve
    if "Power Curve" in checkbox_states and checkbox_states["Power Curve"]:
        if has_power_data:
            st.markdown("---")
            st.markdown("### Power Curve")
            # Spinner für die Power Curve Generierung ist bereits in create_power_curve()
            power_curve_df = create_power_curve(fit_df)
            if not power_curve_df.empty:
                # Spinner für das Plotten der Power Curve
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
            st.markdown("---")
            with st.spinner("Erstelle Herzfrequenzdiagramm..."):
                fig_hr = px.line(fit_df, x='time', y='heart_rate', title='Herzfrequenz über die Zeit',
                                 labels={'time': 'Zeit', 'heart_rate': 'Herzfrequenz (bpm)'})
                fig_hr.update_layout(hovermode="x unified")
                st.plotly_chart(fig_hr, use_container_width=True, key=f"hr_chart_{training_id_for_key}")
        else:
            st.info("Keine Herzfrequenzdaten in der FIT-Datei gefunden.")
    
    if "Leistung" in checkbox_states and checkbox_states["Leistung"]:
        if has_power_data:
            st.markdown("---")
            with st.spinner("Erstelle Leistungsdiagramm..."):
                fig_power = px.line(fit_df, x='time', y='power', title='Leistung über die Zeit',
                                     labels={'time': 'Zeit', 'power': 'Leistung (Watt)'})
                fig_power.update_layout(hovermode="x unified")
                st.plotly_chart(fig_power, use_container_width=True, key=f"power_chart_{training_id_for_key}")
        else:
            st.info("Keine Leistungsdaten in der FIT-Datei gefunden.")

    if "Geschwindigkeit" in checkbox_states and checkbox_states["Geschwindigkeit"]:
        if 'velocity' in fit_df.columns and fit_df['velocity'].dropna().any():
            st.markdown("---")
            with st.spinner("Erstelle Geschwindigkeitsdiagramm..."):
                fig_vel = px.line(fit_df, x='time', y='velocity', title='Geschwindigkeit über die Zeit',
                                     labels={'time': 'Zeit', 'velocity': 'Geschwindigkeit (m/s)'})
                fig_vel.update_layout(hovermode="x unified")
                st.plotly_chart(fig_vel, use_container_width=True, key=f"velocity_chart_{training_id_for_key}")
        else:
            st.info("Keine Geschwindigkeitsdaten in der FIT-Datei gefunden.")

    if "Trittfrequenz" in checkbox_states and checkbox_states["Trittfrequenz"]:
        if 'cadence' in fit_df.columns and fit_df['cadence'].dropna().any():
            st.markdown("---")
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
    Setzt die ID des Trainings, das bearbeitet werden soll, im Session State
    und wechselt zur Bearbeitungsseite.
    """
    st.session_state.editing_training_id = training_id
    if 'last_editing_id' in st.session_state:
        del st.session_state.last_editing_id
    st.switch_page("pages/add workout.py")

def delete_training_from_db(training_id, person_id):
    """Löscht ein Training aus dbtests und seine ID aus der ekg_tests Liste in dbperson."""
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
    Zeigt die Details eines einzelnen Trainings in einem Expander an.
    `expanded` steuert, ob der Expander beim Laden offen ist.
    """
    training_id_str = str(training_data.doc_id) if hasattr(training_data, 'doc_id') else str(training_data.get('id', 'no_id'))
    
    expander_title = f"**{training_data['name']}** - {training_data['date']} ({training_data['sportart']})"
    
    with st.expander(expander_title, expanded=expanded):
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
        st.markdown(f"**Puls:** {training_data.get('puls', 'N/A')} bpm (avg)")
        st.markdown(f"**Kalorien:** {training_data.get('kalorien', 'N/A')} kcal")
        
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

        st.markdown(f"**Beschreibung:**")
        description = training_data.get('description', '')
        if description:
            st.info(description)
        else:
            st.markdown("Keine Beschreibung vorhanden.")

        image_path_from_db = training_data.get('image')
        local_image_path = image_path_from_db
        if local_image_path and os.path.exists(local_image_path):
            st.image(local_image_path, caption=f"Bild für {training_data['name']}", use_container_width=True)
        elif image_path_from_db and image_path_from_db != "-":
            st.warning(f"Bilddatei {repr(image_path_from_db)} konnte nicht gefunden werden.")

        st.markdown("**Verlinkte Dateien:**")

        gpx_file_path_from_db = training_data.get('gpx_file')
        # Spinner für GPX-Daten
        with st.spinner("Lade GPX-Daten..."):
            gpx_data = load_gpx_data(gpx_file_path_from_db)
        if gpx_data:
            st.markdown("### GPX-Track auf Karte")
            # Spinner für die Kartendarstellung
            with st.spinner("Rendere GPX-Karte..."):
                display_gpx_on_map_ui(gpx_data, training_id_str)
            st.markdown("---")
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
        # Spinner für EKG-Daten
        with st.spinner("Lade EKG-Daten..."):
            ekg_content = load_ekg_data(ekg_file_path_from_db)
        if not ekg_content:
            if ekg_file_path_from_db and ekg_file_path_from_db != "-":
                st.warning(f"EKG-Datei {repr(ekg_file_path_from_db)} konnte nicht geladen werden.")
            else:
                if not (gpx_file_path_from_db and gpx_file_path_from_db != "-") and \
                   not (fit_file_path_from_db and fit_file_path_from_db != "-"):
                    st.markdown("Keine weiteren Dateien verlinkt.")

        st.markdown("---")

        col_edit, col_delete, col_spacer = st.columns([0.15, 0.15, 0.7])
        with col_edit:
            if st.button("Bearbeiten 📝", key=f"edit_btn_{training_id_str}"):
                on_edit_callback(training_data.doc_id)
        with col_delete:
            if st.button("Löschen 🗑️", key=f"delete_btn_{training_id_str}"):
                on_delete_callback(training_data.doc_id, st.session_state.current_user_id)
                st.success(f"Training '{training_data['name']}' vom {training_data['date']} wurde gelöscht.")
                st.rerun()

def display_training_list_ui(trainings):
    """
    Zeigt die Liste aller Trainings an.
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
    Lädt die Trainings für die aktuell ausgewählte Person aus der TinyDB.
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