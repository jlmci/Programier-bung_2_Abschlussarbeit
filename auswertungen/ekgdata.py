import json
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.io as pio
pio.renderers.default = 'browser'  # Setzt den Standard-Renderer auf den Browser

# %% Objekt-Welt

# Klasse EKG-Data für Peakfinder, die uns ermöglicht peaks zu finden

class EKGdata:

## Konstruktor der Klasse soll die Daten einlesen

    def __init__(self, ekg_dict):
        #pass
        self.id = ekg_dict["id"]
        self.date = ekg_dict["date"]
        self.data = ekg_dict["result_link"]
        self.df = pd.read_csv(self.data, sep='\t', header=None, names=['Messwerte in mV','Zeit in ms',])


    def plot_time_series(self):

        # Erstellte einen Line Plot, der ersten 2000 Werte mit der Zeit aus der x-Achse
        self.fig = px.line(self.df.head(2000), x="Zeit in ms", y="Messwerte in mV")
        #return self.fig 

    @staticmethod
    def load_by_id(id):
        with open("data/person_db.json") as file:
            person_data = json.load(file)
        ekg_test = None

        for person in person_data:
            for ekg_test_it in person.get("ekg_tests", []):
                #print("Ekg Test:", ekg_test)
                if ekg_test_it["id"] == id:
                    ekg_test = ekg_test_it
                    break
        return ekg_test
   

    def find_peaks(self, respacing_factor=5):
        """
        A function to find the peaks in a series completely without explicit loops.

        Args:
            respacing_factor (int): The factor to respace the series.

        Returns:
            list: A list of the indices of the peaks.
        """
        series = self.df["Messwerte in mV"].iloc[::respacing_factor]

        threshold = series.mean() + 2 * series.std() + 5

        # Berechne die Differenzen zu den vorherigen und nächsten Werten
        # .shift() verschiebt die Werte, so dass wir den vorherigen und nächsten Wert vergleichen können.
        # fill_value=np.nan ist wichtig, um NaN an den Rändern zu haben,
        # die dann beim Vergleich ignoriert werden.
        diff_prev = series.diff(periods=1)
        diff_next = series.diff(periods=-1) # periods=-1 schaut nach vorne

        # Ein Peak liegt vor, wenn:
        # 1. Der aktuelle Wert größer oder gleich dem vorherigen Wert ist (diff_prev >= 0)
        # 2. Der aktuelle Wert größer oder gleich dem nächsten Wert ist (diff_next <= 0, da es die Differenz "current - next" ist)
        # 3. Der aktuelle Wert über dem Schwellenwert liegt

        is_peak = (diff_prev >= 0) & (diff_next <= 0) & (series > threshold)

        # Holen Sie sich die Indizes, wo alle Bedingungen True sind
        peaks_indices = series[is_peak].index.tolist()

        return peaks_indices
        
    def estimate_heart_rate_avarage(self):
        # Wir nehmen die Peaks und berechnen die Herzfrequenz
        peaks = self.find_peaks()
        sample_rate = 500  # 500 Hz

        if len(peaks) < 2:
            raise ValueError("Nicht genug Peaks zur Berechnung der Herzfrequenz.")

        # ➤ RR-Intervalle und BPM berechnen
        peak_intervals = np.diff(peaks)  # Abstand in Samples
        rr_intervals_sec = peak_intervals / sample_rate  # Abstand in Sekunden
        bpm_values = 60 / rr_intervals_sec

        # ➤ Unplausible BPM-Werte entfernen (> 300 BPM)
        bpm_values = bpm_values[bpm_values <= 300]

        if len(bpm_values) == 0:
            raise ValueError("Alle berechneten BPM-Werte sind ungültig (z. B. > 300).")

        average_bpm = np.mean(bpm_values)
        return average_bpm
    
    def estimate_heart_rate(self):
        sample_rate = 500  # 500 Hz
        window_size = 10
        max_bpm_threshold = 300

        peaks = self.find_peaks()
        if len(peaks) < window_size + 1:
            raise ValueError("Nicht genug Peaks für Herzfrequenzberechnung.")

        # RR-Intervalle und BPM berechnen
        peak_intervals = np.diff(peaks)
        rr_intervals_sec = peak_intervals / sample_rate
        bpm_values = 60 / rr_intervals_sec

        # Nur gültige BPMs (z. B. < 300 BPM)
        valid_indices = bpm_values <= max_bpm_threshold
        bpm_values = bpm_values[valid_indices]
        valid_peaks = [peaks[i + 1] for i, valid in enumerate(valid_indices) if valid]

        if len(bpm_values) < window_size:
            raise ValueError("Nicht genug gültige BPM-Werte für Sliding Window.")

        # Sliding Average
        avg_bpm = []
        peak_times = []

        for i in range(len(bpm_values)):
            if i < window_size:
                mean_bpm = np.mean(bpm_values[:window_size])  # Konstante Anfangswerte
            else:
                mean_bpm = np.mean(bpm_values[i - window_size:i])

            peak_index = valid_peaks[i]
            peak_time = (self.df["Zeit in ms"].iloc[peak_index] - self.df["Zeit in ms"].iloc[0]) / 1000

            avg_bpm.append(mean_bpm)
            peak_times.append(peak_time)

        heart_rate_df = pd.DataFrame({
            "Zeit in s": peak_times,
            "Herzfrequenz (BPM)": avg_bpm
        })

        return heart_rate_df
        
    def plot_time_series(self):
        """
        Plot the time series of the EKG data with peak overlay.
        """
        # Zeit relativ zum Start in Sekunden berechnen
        t0 = self.df["Zeit in ms"].iloc[0]
        self.df["Zeit in s"] = (self.df["Zeit in ms"] - t0) / 1000

        # Basis-Linienplot
        self.fig = px.line(
            self.df,
            x="Zeit in s",
            y="Messwerte in mV",
            title=f"EKG Data for ID {self.id}"
        )

        # Initialer Zoombereich: 0–10 Sekunden
        self.fig.update_xaxes(range=[10, 30], title="Zeit (s)")
        self.fig.update_yaxes(title="Messwerte (mV)")

        # ➕ Peaks berechnen
        peaks = self.find_peaks(respacing_factor=5)

        # Zeit- & Messwertwerte der Peaks extrahieren
        peak_times = self.df.loc[peaks, "Zeit in s"]
        peak_values = self.df.loc[peaks, "Messwerte in mV"]
        #print('Size peak df: {0}, {1}'.format(len(peak_times), len(peak_values)))

        # ➕ Scatter-Plot für Peaks hinzufügen
        self.fig.add_scatter(
            x=peak_times,
            y=peak_values,
            mode="markers",
            marker=dict(color="red", size=8, symbol="circle"),
            name="Peaks"
        )
        try:
            heart_rate_df = self.estimate_heart_rate()
            self.fig.add_scatter(
                x=heart_rate_df["Zeit in s"],
                y=heart_rate_df["Herzfrequenz (BPM)"],
                mode="lines",
                line=dict(color="green", dash="dot"),
                yaxis="y2",
                name="Herzfrequenz (BPM)"
            )

            # ➕ Sekundäre Y-Achse für Herzfrequenz aktivieren
            self.fig.update_layout(
                yaxis2=dict(
                    title="Herzfrequenz (BPM)",
                    overlaying="y",
                    side="right",
                    showgrid=False
                )
            )
        except Exception as e:
                print("Herzfrequenz konnte nicht berechnet werden:", e)

        return self.fig




if __name__ == "__main__":
    print("This is a module with some functions to read the EKG data")
    ekg_3_dict = EKGdata.load_by_id(3)
    ekg_3 = EKGdata(ekg_3_dict)
    #print('Size original df: {0}, {1}'.format(len(ekg_3.df['Messwerte in mV']), len(ekg_3.df['Zeit in ms'])))
    peaks_in3 = ekg_3.find_peaks()
    #print("Peaks in EKG 3:", peaks_in3)
    ekg_hr = ekg_3.estimate_heart_rate()
    print(ekg_hr)
    ekg_hr_mean = ekg_3.estimate_heart_rate_avarage()
    print("Durchschnittliche Herzfrequenz:", ekg_hr_mean)
    fig= ekg_3.plot_time_series()
    fig.show()

    

    #file = open("data/person_db.json")
    #person_data = json.load(file)
    #ekg_dict = person_data[0]["ekg_tests"][0]
    #print(ekg_dict)
    #ekg = EKGdata(ekg_dict)
    #print(ekg.df.head())