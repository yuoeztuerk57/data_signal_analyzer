import numpy as np

class DataProcessor:
    def __init__(self):
        self.raw_data = None
        self.processed_data = None
    def generate_signal(self, num_points=1_000_000):
        t = np.linspace(0, 50, num_points)
        sauberes_signal = np.sin(2 * np.pi * 1.0 * t) + 0.5 * np.sin(2 * np.pi * 5.0 * t)
        rauschen = np.random.normal(0, 0.4, num_points)
        self.raw_data = sauberes_signal + rauschen
        self.processed_data = self.raw_data.copy()
        return self.raw_data
    def load_csv(self, dateipfad, delimiter=";"):
        daten = np.genfromtxt(dateipfad, delimiter=delimiter, skip_header=1)
        if daten.ndim > 1:
            daten = daten[:, -1]
        daten = daten[~np.isnan(daten)]
        self.raw_data = daten
        self.processed_data = self.raw_data.copy()
        return self.raw_data
    def apply_moving_average(self, daten, window_size=50):
        if window_size <= 1:
            return daten.copy()
        kernel = np.ones(window_size) / window_size
        return np.convolve(daten, kernel, mode="same")
    def normalize(self, daten):
        min_wert = np.min(daten)
        max_wert = np.max(daten)
        if max_wert == min_wert:
            return np.zeros_like(daten)
        return (daten - min_wert) / (max_wert - min_wert)
    def downsample(self, daten, step=100):
        if step <= 1:
            return daten
        return daten[::step]
    def process(self, window_size=1, do_normalize=False):
        if self.raw_data is None:
            return None
        ergebnis = self.apply_moving_average(self.raw_data, window_size)
        if do_normalize:
            ergebnis = self.normalize(ergebnis)
        self.processed_data = ergebnis
        return self.processed_data
    def save_npz(self, dateipfad):
        if self.raw_data is None or self.processed_data is None:
            raise ValueError("Keine Daten zum Speichern vorhanden.")
        if not dateipfad.endswith(".npz"):
            dateipfad += ".npz"
        np.savez_compressed(
            dateipfad,
            raw_data=self.raw_data,
            processed_data=self.processed_data
        )
    def load_npz(self, dateipfad):
        with np.load(dateipfad) as archiv:
            self.raw_data = archiv["raw_data"]
            if "processed_data" in archiv:
                self.processed_data = archiv["processed_data"]
            else:
                self.processed_data = self.raw_data.copy()
        return self.processed_data

if __name__ == "__main__":
    processor = DataProcessor()
    signal = processor.generate_signal()
    print("Anzahl Punkte:", signal.shape)
    print("Erste 5 Werte:", np.round(signal[:5], 3))
    gefiltert = processor.process(window_size=100, do_normalize=True)
    vorschau = processor.downsample(gefiltert, step=100)
    print("Länge nach Filter:", gefiltert.shape)
    print("Min / Max:", round(np.min(gefiltert), 2), "/", round(np.max(gefiltert), 2))
    print("Länge nach Downsampling:", vorschau.shape)