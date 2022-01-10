import pyqtgraph as pg
import PyQt5
from PyQt5 import QtWidgets, Qt
from PyQt5.QtWidgets import QFileDialog
import sys
import hyperspy.api as hs
import numpy as np
import cv2
import os
import file
from pathlib import Path
from PyQt5.QtCore import QItemSelectionModel


# w2 = w.addLayout(row=0, col=1)
# label2 = w2.addLabel(text, row=0, col=0)
# v2a = w2.addViewBox(row=1, col=0, lockAspect=True)
# r2a = pg.PolyLineROI([[0,0], [10,10], [10,30], [30,10]], closed=True)
# v2a.addItem(r2a)

# def init_ui():
#     # widget = QtWidgets.QWidget()
#     # layout = QtWidgets.QHBoxLayout()
#     # layout.addWidget(QtWidgets.QPushButton(""))
#
#     # pg.ImageView()
#     # layout.addWidget(gwidget)
#     # w1 = gwidget.addLayout(row=0, col=0)
#     #
#     # v2a = w1.addViewBox(row=1, col=0, lockAspect=True)
#     # r2a = pg.PolyLineROI([[0,0], [10,10], [10,30], [30,10]], closed=True)
#     # v2a.addItem(r2a)
#     window = QtWidgets.QWidget()
#     layout = QtWidgets.QVBoxLayout()
#     layout.addWidget(QtWidgets.QPushButton('Top'))
#     layout.addWidget(QtWidgets.QPushButton('Bottom'))
#     window.setLayout(layout)
#     window.show()
#
#     # widget.setLayout(layout)
#     # widget.show()
#
#
class RoiCreater(QtWidgets.QWidget):
    def __init__(self, image, save_mask_folder=None, mask=None, func_after_mask_selected=None):
        QtWidgets.QWidget.__init__(self)
        self.func_after_mask_selected = func_after_mask_selected
        self.setWindowFlags(self.windowFlags() | Qt.Qt.Window)

        if isinstance(image, pg.ImageView):
            image = image.image

        layout = QtWidgets.QVBoxLayout()
        self.imageView = pg.ImageView()
        self.save_mask_folder = save_mask_folder
        layout_bottom = QtWidgets.QHBoxLayout()
        self.lbl_name = QtWidgets.QLabel("Name:")
        self.lbl_name.setMaximumWidth(100)
        self.txt_name = QtWidgets.QTextEdit()
        self.txt_name.setMaximumHeight(30)
        self.txt_name.setMaximumWidth(200)
        self.btn_ok = QtWidgets.QPushButton("OK")
        self.btn_cancel = QtWidgets.QPushButton("Cancel")
        layout_bottom.addWidget(self.lbl_name)
        layout_bottom.addWidget(self.txt_name)
        layout_bottom.addWidget(self.btn_ok)
        layout_bottom.addWidget(self.btn_cancel)

        layout.addWidget(self.imageView)
        layout.addLayout(layout_bottom)
        self.setLayout(layout)
        # self.setBaseSize(800,800)
        self.setMinimumSize(800,700)


        self.image_load(image)
        self.draw_roi()

        self.binding()

        self.setWindowTitle("Masking")


    def image_load(self, img):
        self.imageView.setImage(img)



    def draw_roi(self):
        self.poly_line_roi = pg.PolyLineROI([[0,0], [10,10], [10,30], [30,10]], closed=True)
        self.imageView.addItem(self.poly_line_roi)
        pass

    def binding(self):
        self.btn_ok.clicked.connect(self.btn_ok_clicked)
        self.btn_cancel.clicked.connect(self.btn_cancel_clicked)

    def btn_ok_clicked(self):
        handles = [handle.pos() for handle in self.poly_line_roi.getHandles()]
        handles = np.array(handles)
        img = np.zeros(self.imageView.image.shape)
        cv2.fillPoly(img, pts=[handles.astype(np.int)], color=(255, 255, 255))

        if self.save_mask_folder is None:
            fp, _ = QFileDialog.getSaveFileName()
            if fp == "":
                return
        else:
            name = self.txt_name.toPlainText()
            fp = os.path.join(self.save_mask_folder,name)

        Path(fp).mkdir(parents=True, exist_ok=True)

        if os.path.splitext(fp)[1] is None or os.path.splitext(fp)[1] != ".csv":
            fp = fp + ".csv"
        np.savetxt(fp, img, delimiter=',', fmt='%s')
        print("save to {}".format(fp))
        self.func_after_mask_selected()
        self.close()
        return

    def btn_cancel_clicked(self):
        self.close()
        return

class MaskDropdown(QtWidgets.QComboBox):
    def __init__(self, image, mask_folder, func_after_mask_selected=None):
        """
        Args:
            image: 2d numpy array or pyqtgraph.ImageViewer
            mask_save_folder_path: folder where mask array will be saved
            after_mask_selected: function that will be excu
        """
        QtWidgets.QComboBox.__init__(self)
        self.image = image
        self.mask_folder = mask_folder
        self.func_after_mask_selected = func_after_mask_selected
        self.func_after_mask_selected = self.mask_load

        self.mask_dict = None
        self.mask_widget = None

        self.mask_load()
        self.currentIndexChanged.connect(self.dropdown_event)

    def mask_load(self):
        self.mask_dict = self.mask_data_load()
        self.mask_reload()

    def mask_data_load(self):
        fps = file.get_file_list_from_path(self.mask_folder, ".csv")
        rs = {}
        for fp in fps:
            name = os.path.splitext(os.path.split(fp)[1])[0]
            dic = {
                "fp": fp,
                "data": None
            }
            rs.update({name:dic})
        return rs

    def mask_reload(self):
        self.clear()
        self.addItem("None")
        self.addItems(self.mask_dict.keys())
        self.addItem("Edit ...")

    def get_current_mask(self):
        if not self.mask_dict:
            return
        if self.currentIndex() in [0, len(self.mask_dict)+1]:
            return
        if self.mask_dict[self.currentText()]['data'] is None:
            self.mask_dict[self.currentText()]['data'] = np.loadtxt(self.mask_dict[self.currentText()]['fp'],delimiter=',').astype(np.uint8)
        return self.mask_dict[self.currentText()]['data']



    def dropdown_event(self, idx):
        if idx == len(self.mask_dict)+1:
            #todo: finish list view
            # self.listWidget = ListWidget(list(self.mask_dict.keys()))
            # self.listWidget.show()
            self.mask_widget = RoiCreater(image=self.image, save_mask_folder=self.mask_folder, func_after_mask_selected=self.func_after_mask_selected)
            self.mask_widget.show()
            self.mask_widget.update()


class ListWidget(QtWidgets.QWidget):
    def __init__(self, items):
        super().__init__()
        self.items = list(items)
        self.QList = QtWidgets.QListWidget()
        self.QList.addItems(self.items)
        # self.QList.itemDoubleClicked.connect()
        self.layout = QtWidgets.QGridLayout()
        self.setLayout(self.layout)

        self.btn_move_up = QtWidgets.QPushButton("△")
        self.btn_move_down = QtWidgets.QPushButton("▽")
        self.btn_new = QtWidgets.QPushButton("new")
        self.btn_del = QtWidgets.QPushButton("del")
        self.btn_edit = QtWidgets.QPushButton("edit")
        self.btn_edit.setEnabled(False)

        self.btn_move_up.clicked.connect(self.btn_move_up_clicked)
        self.btn_move_down.clicked.connect(self.btn_move_down_clicked)
        self.btn_new.clicked.connect(self.btn_new_clicked)
        self.btn_del.clicked.connect(self.btn_del_clicked)

        self.layout.addWidget(self.QList, 0, 0, 2, 2)
        self.layout.addWidget(self.btn_move_up, 0, 2)
        self.layout.addWidget(self.btn_move_down, 1, 2)
        self.layout.addWidget(self.btn_new, 3, 0)
        self.layout.addWidget(self.btn_del, 3, 1)
        self.layout.addWidget(self.btn_edit, 3, 2)

    def btn_move_up_clicked(self):
        indexes = self.QList.selectedIndexes()
        if len(indexes) > 0:
            try:
                indexes.sort()
                first_row = indexes[0].row() - 1
                if first_row >= 0:
                    for idx in indexes:
                        if idx != None:
                            row = idx.row()
                            self.items.insert(row-1,self.items[row])
                            self.items.pop(row+1)
                            self.QList.clear()
                            self.QList.addItems(self.items)
            except Exception as e:
                print(e)
        else:
            print('Select at least one item from list!')

    def btn_move_down_clicked(self):
        max_row = len(self.items)
        indexes = self.QList.selectedIndexes()
        if len(indexes) > 0:
            try:
                indexes.sort()
                last_row = indexes[-1].row() + 1
                if last_row < max_row:
                    for idx in indexes:
                        if idx != None:
                            row = idx.row()
                            self.items.insert(row + 2,self.items[row])
                            self.items.pop(row)
                            self.QList.clear()
                            self.QList.addItems(self.items)
            except Exception as e:
                print(e)
        else:
            print('Select at least one item from list!')
        pass

    def mask_data(self):

        pass

    def btn_new_clicked(self):
        maskWidget = RoiCreater()
        maskWidget.show()
        self.close()
        pass

    def btn_del_clicked(self):
        reply = QtWidgets.QMessageBox.question(None,"Delete","Are you sure to delete {}?".format(self.QList.currentItem().text()),QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:

            indexes = self.QList.selectedIndexes()
            for idx in indexes[::-1]:
                self.items.pop(idx)

            self.QList.clear()
            self.QList.addItems(self.items)