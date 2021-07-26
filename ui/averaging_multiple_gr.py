from PyQt5 import QtWidgets
import ui.main as main
import pyqtgraph as pg
import os
import glob
from pathlib import Path

class Viewer(QtWidgets.QWidget):

    str_parameter = r"\Parameters.csv"
    str_data_r = r"\Data_r.csv"
    str_data_q = r"\Data_q.csv"

    def __init__(self):
        super().__init__()
        self.initui()
        self.grCubes = []

    def initui(self):
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)
        self.leftPanel = LeftPanel()
        self.rightPanel = GraphPanel()
        self.layout.addWidget(self.leftPanel)
        self.layout.addWidget(self.rightPanel)

    def binding(self):
        self.leftPanel.btn_open_folder.clicked.connect()

    def open_btn_clicked(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(self,'open')
        if path == "":
            return
        units = self.get_csv_files_from_folder(path)
        for unit in units:
            grCube = GrCube()
            grCube.unit_path = unit
            grCube.unit_path
            self.grCubes.append()



    def get_csv_files_from_folder(self, folder):
        csvfiles = Path("/mnt/experiment/TEM diffraction/").rglob("Data_r.csv")
        fps = set()
        for file in csvfiles:
            if file.name in ["diagonal.csv", "diagonal_1.csv", "line.csv"]:
                continue
            if "r30" in file.name:
                continue
            fp = str(file.absolute())
            idx = fp.find('\\')
            fps.add(fp[:idx])
        fps = list(fps)
        fps.sort()
        return fps


class GrCube:
    def __init__(self):
        self.parameter_path = None
        self.data_r_path = None
        self.data_q_path = None

        self.folder_path = None
        self.unit_path = None
        self.unit_name = None
        self.Gr_path = None
        self.plotItem = None
        self.chkbox = None
        self.Gr = None


class GraphPanel(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)
        self.graphView = pg.PlotWidget(title='G(r)')
        self.layout.addWidget(self.graphView)

class LeftPanel(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        self.btn_open_folder = QtWidgets.QPushButton("Open Folder")
        self.graphGroup = GraphGroup()

        self.layout.addWidget(self.btn_open_folder)
        self.layout.addWidget(self.graphGroup)

class GraphGroup(QtWidgets.QGroupBox):
    def __init__(self):
        super().__init__()
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        box1 = GraphModule()
        box1.set_text("Hello")
        box1.set_color("Yellow")
        layout.addWidget(box1)


class GraphModule(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)
        self.chkbox = QtWidgets.QCheckBox("")
        layout.addWidget(self.chkbox)

    def set_text(self,text):
        self.chkbox.setText(text)
        pass

    def set_color(self,color):
        self.chkbox.setStyleSheet("background-color: {}".format(color))
        pass



if __name__ == "__main__":
    qtapp = QtWidgets.QApplication([])
    # QtWidgets.QMainWindow().show()
    viewer = Viewer()
    viewer.show()
    qtapp.exec()