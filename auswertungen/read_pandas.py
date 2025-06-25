
# Paket für Bearbeitung von Tabellen
import pandas as pd
import numpy as np
## zuvor !pip install plotly
## ggf. auch !pip install nbformat
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
from plotly.subplots import make_subplots
pio.renderers.default = 'browser'  # Setzt den Standard-Renderer auf den Browser



def read_my_csv():
    # Einlesen eines Dataframes
    ## "\t" steht für das Trennzeichen in der txt-Datei (Tabulator anstelle von Beistrich)
    ## header = None: es gibt keine Überschriften in der txt-Datei
    df = pd.read_csv("data/activities/activity.csv", sep=",", usecols=["HeartRate","PowerOriginal"], header = 0)
    df["Time"] = np.arange(0, len(df))  # Erstelle eine Zeitspalte in Millisekunden
    return df


def calculate_HR_zone(df, max_Hr_input=180):
  df["HeartZone"] = ""

  for index, observation in df.iterrows():
    if observation["HeartRate"] < max_Hr_input * 0.6:
      heartzone = "Zone 1"
    elif observation["HeartRate"] >= max_Hr_input*0.6 and observation["HeartRate"] < max_Hr_input * 0.75:
      heartzone = "Zone 2"
    elif observation["HeartRate"] >= max_Hr_input * 0.75 and observation["HeartRate"] < max_Hr_input * 0.85:
      heartzone = "Zone 3"
    elif observation["HeartRate"] >= max_Hr_input * 0.85 and observation["HeartRate"] < max_Hr_input * 0.95:
      heartzone = "Zone 4"
    else:
      heartzone = "Zone 5"   
    
    df.at[index, 'HeartZone'] = heartzone


  # making boolean series for a team name
  filter_Zone1 = df.where(df["HeartZone"]=="Zone 1")
  filter_Zone1 = filter_Zone1.dropna()
    
  filter_Zone2 = df.where(df["HeartZone"]=="Zone 2")
  filter_Zone2 = filter_Zone2.dropna()

  filter_Zone3 = df.where(df["HeartZone"]=="Zone 3")
  filter_Zone3 = filter_Zone3.dropna()

  filter_Zone4 = df.where(df["HeartZone"]=="Zone 4")
  filter_Zone4 = filter_Zone4.dropna()

  filter_Zone5 = df.where(df["HeartZone"]=="Zone 5")
  filter_Zone5 = filter_Zone5.dropna()

  zone_boundaries = {
        'Zone 1': (0.50 * max_Hr_input, 0.60 * max_Hr_input),
        'Zone 2': (0.60 * max_Hr_input, 0.70 * max_Hr_input),
        'Zone 3': (0.70 * max_Hr_input, 0.80 * max_Hr_input),
        'Zone 4': (0.80 * max_Hr_input, 0.90 * max_Hr_input),
        'Zone 5': (0.90 * max_Hr_input, 1.00 * max_Hr_input)
    }
  
  return filter_Zone1, filter_Zone2, filter_Zone3, filter_Zone4, filter_Zone5, df, zone_boundaries



def make_plot(df): 
  #fig = go.Figure()
  fig = make_subplots(specs=[[{"secondary_y": True}]], shared_xaxes=True)
  # Define a color palette for the zones (for the markers)
  zone_colors = {
      'Zone 1': '#ADD8E6', # Light blue
      'Zone 2': '#87CEEB', # Sky blue
      'Zone 3': '#FFD700', # Gold
      'Zone 4': '#FFA500', # Orange
      'Zone 5': '#FF4500' # Orange-red
  }

  if 'PowerOriginal' in df.columns: # Stellt sicher, dass die Spalte PowerOriginal existiert
      fig.add_trace(go.Scatter(
          x=df['Time'],
          y=df['PowerOriginal'],
          mode='lines',
          name='Leistung (Watt)', # Name für die Leistungskurve in der Legende
          line=dict(color='gray', width=2), # Graue Farbe für die Leistungskurve
          showlegend=True # Zeigt diesen Trace in der Legende an
      ), secondary_y=True) # Zuweisung zur sekundären Y-Achse

  # Ensure the DataFrame has the 'HeartZone' column
  if 'HeartZone' not in df.columns:
      print("Error: 'HeartZone' column not found. Please calculate zones first.")
      # Fallback: Plot a single line if no zones are available
      fig.add_trace(go.Scatter(x=df['Time'], y=df['HeartRate'], mode='lines', name='Heart Rate', line=dict(color='blue')),secondary_y = False)
      if 'PowerOriginal' in df.columns:
          fig.add_trace(go.Scatter(x=df['Time'], y=df['PowerOriginal'], mode='lines', name='Leistung (Watt)', line=dict(color='gray')), secondary_y=True)
      return fig

  # Create a list of colors for each data point based on its HeartZone
  point_colors = [zone_colors.get(zone, '#000000') for zone in df['HeartZone']]

  # Plot the entire heart rate curve with colored markers
  fig.add_trace(go.Scatter(
      x=df['Time'],
      y=df['HeartRate'],
      mode='lines+markers', # Show both line and markers
      name='Herzfrequenz', # Name for the main line (can be hidden from legend)
      line=dict(color='white', width=2), # A continuous line, e.g., white
      marker=dict(
          color=point_colors, # Color each marker based on its zone
          size=3, # Size of the markers
          line=dict(width=0) # No border around markers
      ),
      showlegend = False # Hide this trace from the legend as we'll create custom ones
      
  ), secondary_y=False # Primary y-axis for heart rate
  )

    # Plottet die Leistungskurve auf der sekundären Y-Achse
  

  # Add dummy traces for the legend to show zone colors
  sorted_zones = [
      'Zone 1', 'Zone 2', 'Zone 3',
      'Zone 4', 'Zone 5'
  ]
  for zone_name in sorted_zones:
      if zone_name in zone_colors: # Only add if the zone has a defined color
          fig.add_trace(go.Scatter(
              x=[None], # Dummy x-coordinate
              y=[None], # Dummy y-coordinate
              mode='markers',
              marker=dict(size=10, color=zone_colors[zone_name], symbol='circle'),
              name=zone_name,
              showlegend=True
          ))

  # Layout of the plot
  fig.update_layout(
      xaxis_title='Zeit (Sekunden)',
      yaxis_title='Herzfrequenz (bpm)',
      hovermode='x unified', # Show information for all traces at an X-point
      legend_title='Legende',
      height=450,
      font=dict(color='white'), # Font color white
      margin=dict(t=20)
  )

  # Aktualisiert die Y-Achsen-Titel und Gitterlinien
  fig.update_yaxes(title_text="Herzfrequenz (bpm)", secondary_y=False, showgrid=True, gridcolor='rgba(255,255,255,0.1)')
  fig.update_yaxes(title_text="Leistung (Watt)", secondary_y=True, showgrid=True, gridcolor='rgba(255,255,255,0.1)')
  fig.update_xaxes(title_text="Zeit (Sekunden)", showgrid=True, gridcolor='rgba(255,255,255,0.1)')

  return fig



def mittelwerte(df):
    # Berechnet den Mittelwert der Spalten "HeartRate" und "PowerOriginal"
    power_original_mean = df["PowerOriginal"].mean()
    power_original_max = df["PowerOriginal"].max()
    
    return power_original_mean , power_original_max




  
    
if __name__ == "__main__":
    df = read_my_csv()
    #fig = make_plot(df)
    #fig.show()
    heartzone1, heartzone2, heartzone3, heartzone4, heartzone5, df, zones = calculate_HR_zone(df, 180)
    fig = make_plot(df, zones)
    fig.show()
# %%
