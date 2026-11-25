import numpy as np
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QSlider, QCheckBox, QGroupBox,
    QFileDialog, QMessageBox
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
from processor import DataProcessor
from worker import FilterWorker


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Real-Time Data & Signal Analyzer")
        self.resize(1100, 650)

        self.processor = DataProcessor()
        self.processor.generate_signal()

        self.worker = None
        self.pending_update = False

        self._setup_ui()
        self._connect_signals()
        self._update_plot()

    def _setup_ui(self):
        zentral = QWidget()
        self.setCentralWidget(zentral)
        haupt_layout = QHBoxLayout(zentral)

        # --- Linke Seitenleiste (Steuerung) ---
        sidebar = QWidget()
        sidebar.setFixedWidth(280)
        sidebar_layout = QVBoxLayout(sidebar)

        daten_box = QGroupBox("Datenquelle & Export")
        daten_layout = QVBoxLayout(daten_box)
        self.btn_generieren = QPushButton("Neues Signal (1 Mio. Punkte)")
        self.btn_csv_laden = QPushButton("CSV-Datei laden")
        self.btn_npz_speichern = QPushButton("Als .npz speichern")
        self.btn_npz_laden = QPushButton(".npz-Archiv laden")
        daten_layout.addWidget(self.btn_generieren)
        daten_layout.addWidget(self.btn_csv_laden)
        daten_layout.addWidget(self.btn_npz_speichern)
        daten_layout.addWidget(self.btn_npz_laden)
        sidebar_layout.addWidget(daten_box)

        filter_box = QGroupBox("Signal-Verarbeitung")
        filter_layout = QVBoxLayout(filter_box)

        self.lbl_glaettung = QLabel("Glättung (Moving Average): 1")
        self.slider_glaettung = QSlider(Qt.Orientation.Horizontal)
        self.slider_glaettung.setRange(1, 500)
        self.slider_glaettung.setValue(1)

        self.chk_normalisieren = QCheckBox("Normalisieren (0 bis 1)")

        self.lbl_downsample = QLabel("Downsampling-Schritt: 100")
        self.slider_downsample = QSlider(Qt.Orientation.Horizontal)
        self.slider_downsample.setRange(1, 500)
        self.slider_downsample.setValue(100)

        filter_layout.addWidget(self.lbl_glaettung)
        filter_layout.addWidget(self.slider_glaettung)
        filter_layout.addWidget(self.chk_normalisieren)
        filter_layout.addWidget(self.lbl_downsample)
        filter_layout.addWidget(self.slider_downsample)
        sidebar_layout.addWidget(filter_box)

        self.lbl_status = QLabel("Status: Bereit")
        sidebar_layout.addWidget(self.lbl_status)

        sidebar_layout.addStretch()
        haupt_layout.addWidget(sidebar)

        # --- Rechter Bereich (Matplotlib-Diagramm) ---
        chart_bereich = QWidget()
        chart_layout = QVBoxLayout(chart_bereich)

        self.figure = Figure(figsize=(8, 5))
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        self.ax = self.figure.add_subplot(111)

        chart_layout.addWidget(self.toolbar)
        chart_layout.addWidget(self.canvas)
        haupt_layout.addWidget(chart_bereich)

    def _connect_signals(self):
        self.btn_generieren.clicked.connect(self._on_generate_clicked)
        self.btn_csv_laden.clicked.connect(self._on_load_csv_clicked)
        self.btn_npz_speichern.clicked.connect(self._on_save_npz_clicked)
        self.btn_npz_laden.clicked.connect(self._on_load_npz_clicked)
        self.slider_glaettung.valueChanged.connect(self._on_filter_changed)
        self.chk_normalisieren.stateChanged.connect(self._on_filter_changed)
        self.slider_downsample.valueChanged.connect(self._on_downsample_changed)

    def _on_generate_clicked(self):
        self.processor.generate_signal()
        self._on_filter_changed()

    def _on_load_csv_clicked(self):
        dateipfad, _ = QFileDialog.getOpenFileName(
            self, "CSV-Messdaten auswählen", "data", "CSV-Dateien (*.csv);;Alle Dateien (*)"
        )
        if not dateipfad:
            return
        try:
            daten = self.processor.load_csv(dateipfad)
            if len(daten) == 0:
                raise ValueError("Die CSV-Datei enthält keine gültigen Zahlenwerte.")
            self._on_filter_changed()
        except Exception as fehler:
            QMessageBox.warning(self, "Fehler beim Laden", f"Datei konnte nicht geladen werden:\n{fehler}")

    def _on_save_npz_clicked(self):
        dateipfad, _ = QFileDialog.getSaveFileName(
            self, "Signal komprimiert speichern", "data/signal_export.npz", "NumPy Archiv (*.npz)"
        )
        if not dateipfad:
            return
        try:
            self.processor.save_npz(dateipfad)
            self.lbl_status.setText("Status: .npz gespeichert")
        except Exception as fehler:
            QMessageBox.warning(self, "Fehler beim Speichern", f"Speichern fehlgeschlagen:\n{fehler}")

    def _on_load_npz_clicked(self):
        dateipfad, _ = QFileDialog.getOpenFileName(
            self, "NumPy-Archiv laden", "data", "NumPy Archiv (*.npz)"
        )
        if not dateipfad:
            return
        try:
            self.processor.load_npz(dateipfad)
            self.slider_glaettung.blockSignals(True)
            self.chk_normalisieren.blockSignals(True)
            self.slider_glaettung.setValue(1)
            self.chk_normalisieren.setChecked(False)
            self.slider_glaettung.blockSignals(False)
            self.chk_normalisieren.blockSignals(False)
            self.lbl_glaettung.setText("Glättung (Moving Average): 1")
            self._update_plot()
            self.lbl_status.setText("Status: .npz geladen")
        except Exception as fehler:
            QMessageBox.warning(self, "Fehler beim Laden", f"Archiv konnte nicht geladen werden:\n{fehler}")

    def _on_filter_changed(self):
        fenster = self.slider_glaettung.value()
        self.lbl_glaettung.setText(f"Glättung (Moving Average): {fenster}")

        if self.worker is not None and self.worker.isRunning():
            self.pending_update = True
            return

        self._start_worker()

    def _start_worker(self):
        fenster = self.slider_glaettung.value()
        normalisieren = self.chk_normalisieren.isChecked()

        self.lbl_status.setText("Status: Berechne...")
        self.worker = FilterWorker(self.processor, fenster, normalisieren)
        self.worker.finished_processing.connect(self._on_worker_finished)
        self.worker.start()

    def _on_worker_finished(self):
        self._update_plot()
        if self.pending_update:
            self.pending_update = False
            self._start_worker()
        else:
            self.lbl_status.setText("Status: Bereit")

    def _on_downsample_changed(self):
        schritt = self.slider_downsample.value()
        self.lbl_downsample.setText(f"Downsampling-Schritt: {schritt}")
        self._update_plot()

    def _update_plot(self):
        daten = self.processor.processed_data
        if daten is None or len(daten) == 0:
            return

        schritt = self.slider_downsample.value()
        y_vorschau = self.processor.downsample(daten, step=schritt)
        x_vorschau = np.arange(0, len(daten), schritt)

        self.ax.clear()
        self.ax.plot(x_vorschau, y_vorschau, color="#1f77b4", linewidth=0.8)
        self.ax.set_title(f"Signal-Analyse ({len(y_vorschau):,} von {len(daten):,} Punkten angezeigt)")
        self.ax.set_xlabel("Messpunkt (Index)")
        self.ax.set_ylabel("Amplitude")
        self.ax.grid(True, alpha=0.3)
        self.canvas.draw()