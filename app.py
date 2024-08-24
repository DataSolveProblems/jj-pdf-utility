import sys
import os
from PyQt6.QtWidgets import (QApplication, QWidget, QTabWidget, QStatusBar,
                             QVBoxLayout, QHBoxLayout)
from PyQt6.QtGui import (QIcon, QFont)
from pdf_widget import SplitPDFWidget, MergePDFWidget, EncryptPDFWidget, DecryptPDFWidget


class AppWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('PDF Utility')
        self.setWindowIcon(QIcon('./resource/icon.webp'))

        self.width, self.height = 800, 600
        self.setMinimumSize(self.width, self.height)

        self.layout = {'main': QVBoxLayout()}
        self.setLayout(self.layout['main'])
        
        self.init_ui()

    def _init_container(self):
        self.label = {}
        self.button = {}
        self.listwidget = {}
        self.lineedit = {}
        self.added_files = set()

    def init_ui(self):
        self._init_container()

        self.tab = QTabWidget()
        self.layout['main'].addWidget(self.tab) 

        self.tab.addTab(MergePDFWidget(self), 'Merge PDFs')
        self.tab.addTab(SplitPDFWidget(self), 'Split PDF')
        self.tab.addTab(EncryptPDFWidget(self), 'Encrypt PDF')
        self.tab.addTab(DecryptPDFWidget(self), 'Decrypt PDF')

        self.status_bar = QStatusBar()
        self.layout['main'].addWidget(self.status_bar)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setFont(QFont('Arial', 10))

    app_window = AppWindow()
    app_window.show()

    sys.exit(app.exec())