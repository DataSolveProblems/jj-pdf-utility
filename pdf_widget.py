import os
from pathlib import Path
from PyQt6.QtWidgets import (QWidget, QLabel, QPushButton, QLineEdit, QFileDialog, 
                             QComboBox, QListWidget, QAbstractItemView, QStyledItemDelegate,
                             QMenuBar, QTableWidget, QTableWidgetItem, QHBoxLayout, QVBoxLayout)
from PyQt6.QtGui import QKeySequence, QShortcut, QColor
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from pdf_utility import PDFUtility

def check_if_file_exists(file_path):
    if not os.path.exists(file_path):
        return False
    return True

class EncryptPDFThread(QThread):
    finished = pyqtSignal(str)

    def __init__(self, target_file: str, password: str, pdf_utility: PDFUtility, parent=None):
        super().__init__(parent)
        self.target_file = Path(target_file)
        self.password = password
        self.pdf_utility = pdf_utility

    def run(self):
        try:
            # Generate the encrypted file name
            original_file_path = Path(self.target_file)
            encrypted_file_name = original_file_path.stem + '_encrypted.pdf'
            encrypted_file_path = original_file_path.parent / encrypted_file_name
            
            # Perform the encryption
            self.pdf_utility.encrypt_pdf(self.target_file, self.password, encrypted_file_path)
            
            # Emit the finished signal with the encrypted file name
            self.finished.emit('Success')            
        except Exception as e:
            self.finished.emit(str(e))

class DecryptPDFThread(QThread):
    finished = pyqtSignal(str)

    def __init__(self, target_file: str, password: str, pdf_utility: PDFUtility, parent=None):       
        super().__init__(parent)
        self.target_file = Path(target_file)
        self.password = password
        self.pdf_utility = pdf_utility

    def run(self):
        try:
            self.pdf_utility.decrypt_pdf(self.target_file, self.password)
            self.finished.emit('Success')
        except Exception as e:
            self.finished.emit(str(e))

class GridLineDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        
        # Draw gridlines
        painter.save()
        pen = painter.pen()
        pen.setColor(QColor(200, 200, 200))  # Light gray color for gridlines
        painter.setPen(pen)
        
        # Draw bottom line
        painter.drawLine(option.rect.bottomLeft(), option.rect.bottomRight())

        # Draw right line
        painter.drawLine(option.rect.topRight(), option.rect.bottomRight())
        
        painter.restore()

class DecryptPDFWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.pdf_utility = PDFUtility()

        self.setAcceptDrops(True)
        self.layout = {'main': QVBoxLayout()}
        self.setLayout(self.layout['main'])

        self.init_ui()
        self.config_signals()

    def _init_container(self):
        self.label = {}
        self.button = {}
        self.lineedit = {}
        self.tablewidget = {}
        self.added_files = set()

    def init_ui(self):
        self._init_container()

        self.layout['password_input'] = QHBoxLayout()
        self.layout['main'].addLayout(self.layout['password_input'])

        self.label['pdf_password'] = QLabel('Password:')
        self.layout['password_input'].addWidget(self.label['pdf_password'])

        self.lineedit['pdf_password'] = QLineEdit()
        self.lineedit['pdf_password'].setPlaceholderText('Enter password')
        self.layout['password_input'].addWidget(self.lineedit['pdf_password'])

        self.tablewidget['pdf_files'] = QTableWidget()
        self.tablewidget['pdf_files'].setColumnCount(2)
        self.tablewidget['pdf_files'].setHorizontalHeaderLabels(['PDF File', 'Status'])
        self.tablewidget['pdf_files'].horizontalHeader().setStretchLastSection(True)
        self.tablewidget['pdf_files'].setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tablewidget['pdf_files'].setColumnWidth(0, 600)
        self.layout['main'].addWidget(self.tablewidget['pdf_files'])

        self.layout['buttons'] = QHBoxLayout()
        self.layout['main'].addLayout(self.layout['buttons'])

        self.button['add_pdf'] = QPushButton('&Add PDF')
        self.layout['buttons'].addWidget(self.button['add_pdf'])

        self.button['decrypt_pdf'] = QPushButton('&Decrypt PDFs')
        self.layout['buttons'].addWidget(self.button['decrypt_pdf'])

        self.button['remove_pdf'] = QPushButton('&Remove PDF')
        self.layout['buttons'].addWidget(self.button['remove_pdf'])

        self.button['clear_list'] = QPushButton('&Clear List')
        self.layout['buttons'].addWidget(self.button['clear_list'])

    def config_signals(self):
        self.button['add_pdf'].clicked.connect(self.add_pdf)
        self.button['decrypt_pdf'].clicked.connect(self.decrypt_pdf)
        self.button['remove_pdf'].clicked.connect(self.remove_selected_pdf)
        self.button['clear_list'].clicked.connect(self.clear_list)

    def decrypt_pdf(self):
        if self.tablewidget['pdf_files'].rowCount() == 0:
            self.parent.status_bar.showMessage('No PDFs to decrypt')
            return

        password = self.lineedit['pdf_password'].text()
        if password == '':
            self.parent.status_bar.showMessage('Enter password')
            return

        self.threads = []  # Keep references to threads

        for row in range(self.tablewidget['pdf_files'].rowCount()):
            file_path = self.tablewidget['pdf_files'].item(row, 0).text()
            if not check_if_file_exists(file_path):
                self.tablewidget['pdf_files'].item(row, 1).setText('File not found')
                continue

            # Create a thread for each PDF file
            thread = DecryptPDFThread(file_path, password, self.pdf_utility)
            thread.finished.connect(lambda result, row=row: self.on_decrypt_pdf_finished(result, row))
            self.threads.append(thread)
            thread.start()

        self.parent.status_bar.showMessage('Encrypting PDFs...')

    def on_decrypt_pdf_finished(self, result, row):
        # Handle the result of the decryption
        if result == 'Success':
            self.tablewidget['pdf_files'].item(row, 1).setText('Decrypted')
        else:
            self.tablewidget['pdf_files'].item(row, 1).setText(result)

        # Check if all threads have finished
        if all(not thread.isRunning() for thread in self.threads):
            self.parent.status_bar.showMessage('PDFs decrypted')

    def on_encrypt_pdf_finished(self, result, row):
        # Handle the result of the encryption
        if result == 'Success':
            self.tablewidget['pdf_files'].item(row, 1).setText('Encrypted')
        else:
            self.tablewidget['pdf_files'].item(row, 1).setText(result)

        # Check if all threads have finished
        if all(not thread.isRunning() for thread in self.threads):
            self.parent.status_bar.showMessage('PDFs encrypted')

    def add_pdf(self):
        file_paths, _ = QFileDialog.getOpenFileNames(self, 'Add PDFs', '', 'PDF Files (*.pdf)')
        if file_paths:
            for file_path in file_paths:
                if file_path not in self.added_files:
                    row_position = self.tablewidget['pdf_files'].rowCount()
                    self.tablewidget['pdf_files'].insertRow(row_position)
                    self.tablewidget['pdf_files'].setItem(row_position, 0, QTableWidgetItem(file_path))

                    # status column
                    item = QTableWidgetItem('N/A')
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.tablewidget['pdf_files'].setItem(row_position, 1, item)
                    self.added_files.add(file_path)
            self.parent.status_bar.showMessage('PDFs added')

    def clear_list(self):
        self.tablewidget['pdf_files'].setRowCount(0)
        self.added_files.clear()
        self.parent.status_bar.showMessage('Cleared')

    def remove_selected_pdf(self):
        selected_items = self.tablewidget['pdf_files'].selectedItems()
        if not selected_items:
            self.parent.status_bar.showMessage('No PDF selected to remove')
            return

        rows_to_remove = set()
        for item in selected_items:
            row = self.tablewidget['pdf_files'].row(item)
            rows_to_remove.add(row)
            file_path = item.text()  # Retrieve file path before removing the item
            self.added_files.discard(file_path)  # Remove the file path from the added_files set if needed

        for row in sorted(rows_to_remove, reverse=True):
            self.tablewidget['pdf_files'].removeRow(row)

        self.parent.status_bar.showMessage('Selected PDFs removed')

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.endswith('.pdf'):
                    if file_path not in self.added_files:
                        row_position = self.tablewidget['pdf_files'].rowCount()

                        self.tablewidget['pdf_files'].insertRow(row_position)
                        self.tablewidget['pdf_files'].setItem(row_position, 0, QTableWidgetItem(file_path))
                        self.added_files.add(file_path)

                        # status column
                        item = QTableWidgetItem('N/A')
                        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        self.tablewidget['pdf_files'].setItem(row_position, 1, item)
        else:
            event.ignore()

class EncryptPDFWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.pdf_utility = PDFUtility()

        self.setAcceptDrops(True)
        self.layout = {'main': QVBoxLayout()}
        self.setLayout(self.layout['main'])

        self.init_ui()
        self.config_signals()

    def _init_container(self):
        self.label = {}
        self.button = {}
        self.lineedit = {}
        self.tablewidget = {}
        self.added_files = set()

    def init_ui(self):
        self._init_container()

        self.layout['password_input'] = QHBoxLayout()
        self.layout['main'].addLayout(self.layout['password_input'])

        self.label['pdf_password'] = QLabel('Password:')
        self.layout['password_input'].addWidget(self.label['pdf_password'])

        self.lineedit['pdf_password'] = QLineEdit()
        self.lineedit['pdf_password'].setPlaceholderText('Enter password')
        self.layout['password_input'].addWidget(self.lineedit['pdf_password'])

        self.tablewidget['pdf_files'] = QTableWidget()
        self.tablewidget['pdf_files'].setColumnCount(2)
        self.tablewidget['pdf_files'].setHorizontalHeaderLabels(['PDF File', 'Status'])
        self.tablewidget['pdf_files'].horizontalHeader().setStretchLastSection(True)
        self.tablewidget['pdf_files'].setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tablewidget['pdf_files'].setColumnWidth(0, 600)
        self.layout['main'].addWidget(self.tablewidget['pdf_files'])

        self.layout['buttons'] = QHBoxLayout()
        self.layout['main'].addLayout(self.layout['buttons'])

        self.button['add_pdf'] = QPushButton('&Add PDF')
        self.layout['buttons'].addWidget(self.button['add_pdf'])

        self.button['encrypt_pdf'] = QPushButton('&Encrypt PDFs')
        self.layout['buttons'].addWidget(self.button['encrypt_pdf'])

        self.button['remove_pdf'] = QPushButton('&Remove PDF')
        self.layout['buttons'].addWidget(self.button['remove_pdf'])

        self.button['clear_list'] = QPushButton('&Clear List')
        self.layout['buttons'].addWidget(self.button['clear_list'])


    def config_signals(self):
        self.button['add_pdf'].clicked.connect(self.add_pdf)
        self.button['encrypt_pdf'].clicked.connect(self.encrypt_pdf)
        self.button['remove_pdf'].clicked.connect(self.remove_selected_pdf)
        self.button['clear_list'].clicked.connect(self.clear_list)

    def encrypt_pdf(self):
        if self.tablewidget['pdf_files'].rowCount() == 0:
            self.parent.status_bar.showMessage('No PDFs to encrypt')
            return

        password = self.lineedit['pdf_password'].text()
        if password == '':
            self.parent.status_bar.showMessage('Enter password')
            return

        self.threads = []  # Keep references to threads

        for row in range(self.tablewidget['pdf_files'].rowCount()):
            file_path = self.tablewidget['pdf_files'].item(row, 0).text()
            if not check_if_file_exists(file_path):
                self.tablewidget['pdf_files'].item(row, 1).setText('File not found')
                continue

            # Create a thread for each PDF file
            thread = EncryptPDFThread(file_path, password, self.pdf_utility)
            thread.finished.connect(lambda result, row=row: self.on_encrypt_pdf_finished(result, row))
            self.threads.append(thread)  # Keep a reference to the thread
            thread.start()

        self.parent.status_bar.showMessage('Encrypting PDFs...')

    def on_encrypt_pdf_finished(self, result, row):
        # Handle the result of the encryption
        if result == 'Success':
            self.tablewidget['pdf_files'].item(row, 1).setText('Encrypted')
        else:
            self.tablewidget['pdf_files'].item(row, 1).setText(result)

        # Check if all threads have finished
        if all(not thread.isRunning() for thread in self.threads):
            self.parent.status_bar.showMessage('PDFs encrypted')

    def add_pdf(self):
        file_paths, _ = QFileDialog.getOpenFileNames(self, 'Add PDFs', '', 'PDF Files (*.pdf)')
        if file_paths:
            for file_path in file_paths:
                if file_path not in self.added_files:
                    row_position = self.tablewidget['pdf_files'].rowCount()
                    self.tablewidget['pdf_files'].insertRow(row_position)
                    self.tablewidget['pdf_files'].setItem(row_position, 0, QTableWidgetItem(file_path))

                    # status column
                    item = QTableWidgetItem('N/A')
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.tablewidget['pdf_files'].setItem(row_position, 1, item)
                    self.added_files.add(file_path)
            self.parent.status_bar.showMessage('PDFs added')

    def clear_list(self):
        self.tablewidget['pdf_files'].setRowCount(0)
        self.added_files.clear()
        self.parent.status_bar.showMessage('Cleared')

    def remove_selected_pdf(self):
        selected_items = self.tablewidget['pdf_files'].selectedItems()
        if not selected_items:
            self.parent.status_bar.showMessage('No PDF selected to remove')
            return

        rows_to_remove = set()
        for item in selected_items:
            row = self.tablewidget['pdf_files'].row(item)
            rows_to_remove.add(row)
            file_path = item.text()  # Retrieve file path before removing the item
            self.added_files.discard(file_path)  # Remove the file path from the added_files set if needed

        for row in sorted(rows_to_remove, reverse=True):
            self.tablewidget['pdf_files'].removeRow(row)

        self.parent.status_bar.showMessage('Selected PDFs removed')

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.endswith('.pdf'):
                    if file_path not in self.added_files:
                        row_position = self.tablewidget['pdf_files'].rowCount()

                        self.tablewidget['pdf_files'].insertRow(row_position)
                        self.tablewidget['pdf_files'].setItem(row_position, 0, QTableWidgetItem(file_path))
                        self.added_files.add(file_path)

                        # status column
                        item = QTableWidgetItem('N/A')
                        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        self.tablewidget['pdf_files'].setItem(row_position, 1, item)
        else:
            event.ignore()

class SplitPDFWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.pdf_utility = PDFUtility()

        self.setAcceptDrops(True)
        self.layout = {'main': QVBoxLayout()}
        self.setLayout(self.layout['main'])

        self.init_ui()
        self.config_signals()

        # self.test()

    def test(self):
        self.lineedit['pdf_input'].setText(r'E:\PythonVenv\desktop-pdf-reader\Python Data Model.pdf')
        self.lineedit['pdf_output_dir'].setText(r'E:\PythonVenv\desktop-pdf-reader\splitted')

    def init_ui(self):
        self._init_container()

        self.layout['input'] = QHBoxLayout()
        self.layout['main'].addLayout(self.layout['input'])

        self.label['pdf_input'] = QLabel('Source PDF:')
        self.layout['input'].addWidget(self.label['pdf_input'])

        self.lineedit['pdf_input'] = QLineEdit()
        self.layout['input'].addWidget(self.lineedit['pdf_input'])

        self.button['browse_file'] = QPushButton('Br&owse')
        self.layout['input'].addWidget(self.button['browse_file'])

        self.layout['pdf_config'] = QVBoxLayout()
        self.layout['main'].addLayout(self.layout['pdf_config'])

        self.label['page'] = QLabel('Pages')
        self.layout['pdf_config'].addWidget(self.label['page'])

        self.combobox['page'] = QComboBox()
        # self.combobox['page'].setFixedWidth(100)
        self.combobox['page'].addItems(['All', 'Odd', 'Even', 'Custom'])
        self.layout['pdf_config'].addWidget(self.combobox['page'])

        self.lineedit['custom_pages'] = QLineEdit()
        self.lineedit['custom_pages'].setPlaceholderText('e.g. 2-5, 9, 12-16')
        self.lineedit['custom_pages'].hide()  # Initially hide the custom pages line edit
        self.layout['pdf_config'].addWidget(self.lineedit['custom_pages'])

        # self.layout['pdf_config'].addStretch()
        self.layout['pdf_config'].addStretch()
        
        self.layout['output_dir'] = QHBoxLayout()
        self.layout['pdf_config'].addLayout(self.layout['output_dir'])
        
        self.label['pdf_output_dir'] = QLabel('Output Dir:')
        self.layout['output_dir'].addWidget(self.label['pdf_output_dir'])

        self.lineedit['pdf_output_dir'] = QLineEdit()
        self.layout['output_dir'].addWidget(self.lineedit['pdf_output_dir'])

        self.button['browse_output_dir'] = QPushButton('&Browse')
        self.layout['output_dir'].addWidget(self.button['browse_output_dir'])


        self.button['split_pdf'] = QPushButton('&Split PDF')
        self.layout['pdf_config'].addWidget(self.button['split_pdf'])

    def _init_container(self):
        self.label = {}
        self.lineedit = {}
        self.combobox = {}
        self.button = {}

    def config_signals(self):
        self.button['browse_file'].clicked.connect(self.browse_file)
        self.combobox['page'].currentIndexChanged.connect(self.on_combobox_page_changed)
        self.button['browse_output_dir'].clicked.connect(self.browser_dir)
        self.button['split_pdf'].clicked.connect(self.split_pdf)

    def on_combobox_page_changed(self, index):
        if self.combobox['page'].currentText() == 'Custom':
            self.lineedit['custom_pages'].show()
        else:
            self.lineedit['custom_pages'].hide()            

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'PDF File Path', '', 'PDF Files (*.pdf)')
        if file_path:
            self.lineedit['pdf_input'].setText(file_path)

    def browser_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, 'Output Directory', '')
        if dir_path:
            self.lineedit['pdf_output_dir'].setText(dir_path)

    def split_pdf(self):
        if self.lineedit['pdf_input'].text() == '':
            self.parent.status_bar.showMessage('Enter output file path')
            return
        elif not check_if_file_exists(self.lineedit['pdf_input'].text()):
            self.parent.status_bar.showMessage('File not found')
            return
        elif not self.lineedit['pdf_input'].text().endswith('.pdf'):
            self.parent.status_bar.showMessage('Invalid PDF file')
            return

        if not check_if_file_exists(self.lineedit['pdf_input'].text()):
            self.parent.status_bar.showMessage('File not found')
            return

        if self.lineedit['pdf_output_dir'].text() == '':
            self.parent.status_bar.showMessage('Output directory path is required')
            return
        
        input_file = self.lineedit['pdf_input'].text()
        output_dir = self.lineedit['pdf_output_dir'].text()
        
        split_type = self.combobox['page'].currentText()

        try:
            if split_type == 'Custom':
                custom_pages = self.lineedit['custom_pages'].text()
                if custom_pages == '':
                    self.parent.status_bar.showMessage('Enter custom pages')
                    return
                
                # check invalid custom pages
                pages = custom_pages.split(',')
                for page_range in pages:
                    if '-' in page_range:
                        start, end = map(int, page_range.split('-'))
                        if start > end:
                            self.parent.status_bar.showMessage(f'Invalid range: {start}-{end}. Start page must be smaller than end page.')
                            return

                self.pdf_utility.split_pdf(input_file, output_dir, split_type, custom_pages)
            else:
                self.pdf_utility.split_pdf(input_file, output_dir, split_type)

            self.parent.status_bar.showMessage(f'PDF splitted at {output_dir}')
        except Exception as e:
            self.parent.status_bar.showMessage(str(e))
            return
 
class MergePDFWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.pdf_utility = PDFUtility()

        self.setAcceptDrops(True)
        self.layout = {'main': QVBoxLayout()}
        self.setLayout(self.layout['main'])

        self.init_ui()
        self.set_stylesheet()
        self.config_signals()

    def set_stylesheet(self):
        # increase button width
        self.setStyleSheet('''
            QPushButton {
                min-width: 100px;
                height: 20px;       
            }
        ''')

    def _init_container(self):
        self.label = {}
        self.button = {}
        self.listwidget = {}
        self.lineedit = {}
        self.added_files = set()

    def _init_menu_bar(self):
        self.menu_bar = QMenuBar()
        self.layout['main'].addWidget(self.menu_bar)


    def init_ui(self):
        self._init_container()

        self._init_menu_bar()

        # Input File
        self.layout['input'] = QHBoxLayout()
        self.layout['main'].addLayout(self.layout['input'])

        self.layout['submain'] = QHBoxLayout()
        self.layout['main'].addLayout(self.layout['submain'])

        self.label['pdf_output'] = QLabel('PDF File Path (ALT+P):')
        self.layout['input'].addWidget(self.label['pdf_output'])

        self.lineedit['pdf_output'] = QLineEdit()
        self.layout['input'].addWidget(self.lineedit['pdf_output'])

        # PDF list listwidget configuration
        self.listwidget['pdf_files'] = QListWidget()
        self.listwidget['pdf_files'].setAcceptDrops(True)
        self.listwidget['pdf_files'].setDragEnabled(True)
        self.listwidget['pdf_files'].setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.listwidget['pdf_files'].setDefaultDropAction(Qt.DropAction.MoveAction)       
        self.listwidget['pdf_files'].setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)

        # Set custom delegate for gridlines
        self.listwidget['pdf_files'].setItemDelegate(GridLineDelegate())
        self.layout['submain'].addWidget(self.listwidget['pdf_files'])

        self.layout['buttons'] = QVBoxLayout()
        self.layout['submain'].addLayout(self.layout['buttons'])

        self.button['add_pdf'] = QPushButton('&Add PDF')
        self.layout['buttons'].addWidget(self.button['add_pdf'])

        self.button['merge_pdf'] = QPushButton('&Merge PDFs')
        self.layout['buttons'].addWidget(self.button['merge_pdf'])

        self.button['remove_pdf'] = QPushButton('&Remove PDF')
        self.layout['buttons'].addWidget(self.button['remove_pdf'])

        self.button['sort_pdf_asc'] = QPushButton('Sort PDF (ASC)')
        self.layout['buttons'].addWidget(self.button['sort_pdf_asc'])

        self.button['sort_pdf_desc'] = QPushButton('Sort PDF (DESC)')
        self.layout['buttons'].addWidget(self.button['sort_pdf_desc'])

        self.button['clear_list'] = QPushButton('&Clear List')
        self.layout['buttons'].addWidget(self.button['clear_list'])

        self.layout['buttons'].addStretch()

    def config_signals(self):
        self.button['add_pdf'].clicked.connect(self.add_pdf)
        self.button['merge_pdf'].clicked.connect(self.merge_pdf)
        self.button['remove_pdf'].clicked.connect(self.remove_selected_pdf)
        self.button['sort_pdf_asc'].clicked.connect(lambda: self.sort_list(True))
        self.button['sort_pdf_desc'].clicked.connect(lambda: self.sort_list(False))
        self.button['clear_list'].clicked.connect(self.clear_list)

        shortcut = QShortcut(QKeySequence('Alt+P'), self)
        shortcut.activated.connect(self.lineedit['pdf_output'].setFocus)

    def add_pdf(self):
        file_paths, _ = QFileDialog.getOpenFileNames(self, 'Add PDFs', '', 'PDF Files (*.pdf)')
        if file_paths:
            for file_path in file_paths:
                if file_path not in self.added_files:
                    self.listwidget['pdf_files'].addItem(file_path)
                    self.added_files.add(file_path)
            self.parent.status_bar.showMessage('PDFs added')

    def merge_pdf(self):
        if self.listwidget['pdf_files'].count() == 0:
            self.parent.status_bar.showMessage('No PDFs to merge')
            return
        
        if self.lineedit['pdf_output'].text() == '':
            self.parent.status_bar.showMessage('Enter output file path')
            return

        output_file = self.lineedit['pdf_output'].text()
        if not output_file.endswith('.pdf'):
            output_file += '.pdf'
        
        try:
            pdfs = [self.listwidget['pdf_files'].item(i).text() for i in range(self.listwidget['pdf_files'].count())]
            self.pdf_utility.merge_pdfs(pdfs, output_file)
            self.parent.status_bar.showMessage(f'PDF saved at {output_file}')
        except Exception as e:
            self.parent.status_bar.showMessage(f'Error: {e}')       

    def remove_selected_pdf(self):
        if len(self.listwidget['pdf_files'].selectedItems()) > 0:
            for item in self.listwidget['pdf_files'].selectedItems():
                self.listwidget['pdf_files'].takeItem(self.listwidget['pdf_files'].row(item))
                self.added_files.remove(item.text())
            self.parent.status_bar.showMessage('PDF removed')

    def clear_list(self):
        self.listwidget['pdf_files'].clear()
        self.added_files.clear()
        self.parent.status_bar.showMessage('Cleared')

    def sort_list(self, ascending=True):
        if ascending:
            self.listwidget['pdf_files'].sortItems(Qt.SortOrder.AscendingOrder)
            self.parent.status_bar.showMessage('Sorted in ascending order')
        else:
            self.listwidget['pdf_files'].sortItems(Qt.SortOrder.DescendingOrder)
            self.parent.status_bar.showMessage('Sorted in descending order')

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.endswith('.pdf'):
                    if file_path not in self.added_files:
                        self.listwidget['pdf_files'].addItem(file_path)
                        self.added_files.add(file_path)
        else:
            event.ignore()