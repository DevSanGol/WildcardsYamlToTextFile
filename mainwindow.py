# This Python file uses the following encoding: utf-8
import sys
from PySide6.QtWidgets import QApplication, QWidget, QMainWindow, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QFileDialog
from PySide6.QtCore import QTextStream, QFile, QIODevice, QRunnable, QThreadPool, QIODeviceBase

class FileWriter(QRunnable):
    def __init__(self, file_name, list_of_lines, parent = None):
        super().__init__(parent)

        self.file_name = file_name
        self.lines = list_of_lines

    def run(self):
        file = QFile(self.file_name)
        if file.open(QIODeviceBase.OpenModeFlag.NewOnly | QIODeviceBase.OpenModeFlag.Text):
            out = QTextStream(file)
            for line in self.lines:
                out << line << "\n"
        else:
            print("File " + file.fileName() + " already exists")



class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Yaml wildcards to .txt collection")

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout_main = QVBoxLayout()
        self.layout_file_browse = QHBoxLayout()
        self.layout_target_folder_select = QHBoxLayout()


        self.lbl_file_select = QLabel()
        self.lbl_file_select.setText("Select .txt or .yaml file")
        self.file_name = QLineEdit()
        self.file_name.setReadOnly(True)
        self.file_name.textChanged.connect(lambda: self.check_ready_start())
        self.btn_search = QPushButton()
        self.btn_search.setText("Browse")
        self.btn_search.clicked.connect(lambda: self.browse_source_file())

        self.lbl_folder_select = QLabel()
        self.lbl_folder_select.setText("Select target folder (where to save result files)")
        self.target_folder = QLineEdit()
        self.target_folder.setReadOnly(True)
        self.target_folder.textChanged.connect(lambda: self.check_ready_start())
        self.btn_select_folder = QPushButton()
        self.btn_select_folder.setText("Browse")
        self.btn_select_folder.clicked.connect(lambda: self.select_target_folder())

        self.btn_start = QPushButton()
        self.btn_start.setEnabled(False)
        self.btn_start.setText("Start")
        self.btn_start.clicked.connect(lambda: self.process_file())

        self.layout_file_browse.addWidget(self.file_name, 2)
        self.layout_file_browse.addWidget(self.btn_search)
        self.layout_target_folder_select.addWidget(self.target_folder, 2)
        self.layout_target_folder_select.addWidget(self.btn_select_folder)
        self.layout_main.addWidget(self.lbl_file_select)
        self.layout_main.addLayout(self.layout_file_browse, 2)
        self.layout_main.addWidget(self.lbl_folder_select)
        self.layout_main.addLayout(self.layout_target_folder_select, 2)
        self.layout_main.addWidget(self.btn_start)

        self.centralWidget().setLayout(self.layout_main)

        self.directory = ""

    def browse_source_file(self):
        file_selected = QFileDialog.getOpenFileName(self, "Select source file", '/',"Text files (*.txt);;Source file (*.yaml)")
        if file_selected:
            self.file_name.setText(file_selected[0])

    def select_target_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select folder to save results", '/', QFileDialog.Option.ShowDirsOnly)
        if folder:
            self.target_folder.setText(folder)

    def check_ready_start(self):
        if not (self.file_name.text() == "" or self.target_folder.text() == ""):
            self.btn_start.setEnabled(True)
            self.directory = self.target_folder.text()
        else:
            self.btn_start.setEnabled(False)
            self.directory = ""

    def process_file(self):
        file = QFile(self.file_name.text())
        if file.open(QIODevice.ReadOnly | QIODevice.Text):
            stream = QTextStream(file)
            wildcards_file_name = ""
            list_of_file_lines = []
            filling_list = False
            # count quantity of tabs in the line, which means the nested level of wildcards
            nested_level_counter = 0
            while not stream.atEnd():
                line = stream.readLine()
                # copy of the line to check \t symbols quantity (nested level)
                copy_line = line
                line = line.strip()
                if line == "":
                    continue
                if line.endswith(":"):
                    nested_level_counter = copy_line.count(' '*4)
                    # DEBUG
                    #print("Count of \t == " + str(nested_level_counter))
                    if filling_list:
                        # send data to runnable that will write it in new file
                        new_file_abs_name = self.directory + "/" + wildcards_file_name + ".txt"
                        # DEBUG
                        #self.print_lines_and_filename(new_file_abs_name, list_of_file_lines, nested_level_counter)
                        QThreadPool.globalInstance().start(FileWriter(new_file_abs_name,list_of_file_lines))
                        filling_list = False
                        wildcards_levels = wildcards_file_name.split('_')[0:nested_level_counter]
                        wildcards_file_name = wildcards_levels[0] if len(wildcards_levels) == 1 else ('_').join(wildcards_levels)
                        if not wildcards_file_name == "":
                            wildcards_file_name += "_"
                        list_of_file_lines = []    
                    # remove ':' ending from the line
                    line = line[:-1]
                    wildcards_file_name = wildcards_file_name + line + "_"
                elif line.startswith('- '):
                    if line.endswith(">-"):
                        continue
                    if not filling_list:
                        # remove '_' ending from new file name
                        wildcards_file_name = wildcards_file_name[:-1]
                        filling_list = True
                    line = line[2:]
                    list_of_file_lines.append(line)
                else:
                    continue
            new_file_abs_name = self.directory + "/" + wildcards_file_name + ".txt"
            QThreadPool.globalInstance().start(FileWriter(new_file_abs_name,list_of_file_lines))
            QThreadPool.globalInstance().waitForDone()
            file.close()
        else:
            print("Can't open file: " + file.fileName())

    def print_lines_and_filename(self, file_name, lines, nested_level):
            print("File name will be: " + file_name)
            print("Current nested level is " + str(nested_level))
            for line in lines:
                print("\t" + line)


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
