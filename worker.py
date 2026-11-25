from PyQt6.QtCore import QThread, pyqtSignal

class FilterWorker(QThread):
    finished_processing = pyqtSignal(object)
    def __init__(self, processor, window_size, do_normalize):
        super().__init__()
        self.processor = processor
        self.window_size = window_size
        self.do_normalize = do_normalize
    def run(self):
        ergebnis = self.processor.process(
            window_size=self.window_size,
            do_normalize=self.do_normalize
        )
        self.finished_processing.emit(ergebnis)