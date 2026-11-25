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

if __name__ == "__main__":
    processor = DataProcessor()
    signal = processor.generate_signal()
    print("Anzahl Punkte:", signal.shape)
    print("Erste 5 Werte:", np.round(signal[:5], 3))