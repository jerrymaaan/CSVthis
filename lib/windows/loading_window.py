from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt


class LoadingWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Laden...")
        self.setWindowModality(Qt.ApplicationModal)  # prevents interaction with other windows
        self.setFixedSize(400, 100)

        # set styles
        self.load_stylesheet("lib/assets/style.qss")

        # window box and layout
        self.win_layout = QVBoxLayout()
        self.setLayout(self.win_layout)

        # text
        self.label = QLabel("Bitte warten, Daten werden geladen...")
        self.label.setAlignment(Qt.AlignCenter)
        self.win_layout.addWidget(self.label)

    def load_stylesheet(self, filename):
        with open(filename, "r") as qss_file:
            stylesheet = qss_file.read()
            self.setStyleSheet(stylesheet)
