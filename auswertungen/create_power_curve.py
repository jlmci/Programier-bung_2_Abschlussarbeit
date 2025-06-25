import pandas as pd
import numpy as np
## zuvor !pip install plotly
## ggf. auch !pip install nbformat
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
from plotly.subplots import make_subplots
pio.renderers.default = 'browser'  # Setzt den Standard-Renderer auf den Browser


def read_csv(path):
    # Einlesen eines Dataframes
    ## "\t" steht für das Trennzeichen in der txt-Datei (Tabulator anstelle von Beistrich)
    ## header = None: es gibt keine Überschriften in der txt-Datei
    df = pd.read_csv(path, sep=",", header=0)
    df["Time"] = np.arange(0, len(df))  # Erstelle eine Zeitspalte in Millisekunden
    return df

def find_best_effort(df, window_size, power_col="PowerOriginal"):
   max_value = df[power_col].rolling(window=window_size).mean()
   max_value = max_value.max()
   return int(max_value)

def create_power_curve(df, window_size=[10,30,60,120,300,600,900,1200,1500,1800,6000,9000,1800,3600,7200], power_col="PowerOriginal"):
    """
    Create a power curve from the DataFrame.
    
    Parameters:
    df (DataFrame): The input DataFrame containing power data.
    window_size (list): List of window sizes in seconds for calculating best efforts.
    power_col (str): The column name containing power data.
    
    Returns:
    DataFrame: A DataFrame with the best efforts for each window size.
    """
    best_efforts = {}
    
    
    for size in window_size:
        if size < len(df):
            #print(size)
            best_effort = find_best_effort(df, size, power_col)
            #print(best_effort)
            best_efforts.update({size: best_effort})
        else:
            break
    #print("Best Efforts:", best_efforts)
    
    # Convert the dictionary to a DataFrame
    power_curve_df = df = pd.DataFrame.from_dict(best_efforts, orient='index', columns=['BestEffort'])
    
    return power_curve_df

import plotly.express as px
import pandas as pd



# Labels manuell umwandeln
def format_time(s):
    if s < 60:
        return f"{s}s"
    elif s < 3600:
        return f"{s//60}m"
    else:
        return f"{s//3600}h"


def plot_power_curve(power_curve_df):
    """
    Plot the power curve using Plotly.

    Parameters:
    power_curve_df (DataFrame): The DataFrame containing 'Seconds' and 'BestEffort'.
    """
    # Neue Spalte für formatierten Zeitwert
    power_curve_df["formated_Time"] = ""

    power_curve_df["formated_Time"] = power_curve_df.index.map(format_time)

    # Plot mit formatierten Zeitwerten auf der X-Achse
    fig = px.line(
        power_curve_df,
        x="formated_Time",
        y="BestEffort",
        title="Power Curve"
    )

    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Power (Watts)",
        template="plotly_dark"
    )
    #Auskommentiert damit das Bild nicht jedes mal gespeichert wird
    #fig.write_image("pictures_readme/power_curve.png")
    return fig




if __name__ == "__main__":
    # Pfad zur CSV-Datei
    path = "data/activities/activity.csv"
    
    # Lese die CSV-Datei ein
    df = read_csv(path)
    # Erstelle die Power-Kurve
    power_curve_df = create_power_curve(df)
    #print(power_curve_df)
    fig = (plot_power_curve(power_curve_df))
    fig.show()
    #print(find_best_effort(df, 1000, power_col="PowerOriginal"))