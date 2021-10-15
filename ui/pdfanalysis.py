import typing

import file
from datacube import DataCube
import pyqtgraph as pg
import util
from calculate import pdf_calculator
from PyQt5.QtWidgets import QMessageBox
import ui.ui_util as ui_util
from PyQt5 import QtCore, QtWidgets, QtGui
import os
import numpy as np
import definitions
from calculate.q_range_selector import find_first_peak

pg.setConfigOptions(antialias=True)


class PdfAnalysis(QtWidgets.QWidget):
    def __init__(self, Dataviewer):
        super().__init__()
        self.Dataviewer = Dataviewer
        self.datacube = DataCube()
        self.datacube.analyser = self
        if self.datacube.element_nums is None:
            self.datacube.element_nums = []
            self.datacube.element_ratio = []
        self.instant_update = False



        self.initui()
        self.initgraph()
        self.element_presets = file.load_element_preset()
        self.update_preset_enablility()

        # datacube control
        self.load_default_setting()
        self.put_data_to_ui()
        self.update_initial_iq()

        self.sig_binding()

        # self.update_parameter()

        self.update_graph()

    def put_datacube(self,datacube):
        self.controlPanel.blockSignals(True)
        self.datacube = datacube
        if self.datacube.element_nums is None:
            self.datacube.element_nums = []
            self.datacube.element_ratio = []
        self.load_default_setting()
        self.put_data_to_ui()
        self.update_initial_iq()
        self.update_graph()
        self.update_initial_iq_graph()
        self.controlPanel.blockSignals(False)

    def btn_select_clicked(self):
        azavg = self.dc.azavg
        if self.dc.azavg is None:
            return
        first_peak_idx, second_peak_idx = q_range_selector.find_multiple_peaks(self.dc.azavg)
        self.profile_graph_panel.plotWidget.create_circle([first_peak_idx, azavg[first_peak_idx]],
                                                          [second_peak_idx, azavg[second_peak_idx]])

        #
        self.left.hide()

        l = q_range_selector.find_first_nonzero_idx(self.dc.azavg)
        r = l + int((len(self.dc.azavg) - l) / 4)
        self.profile_graph_panel.plotWidget.setXRange(l, r, padding=0.1)

        self.profile_graph_panel.plotWidget.select_mode = True
        self.profile_graph_panel.plotWidget.select_event = self.azav_select_event
        #
        # self.left.show()

    def azav_select_event(self):
        self.left.show()
        self.profile_graph_panel.plotWidget.select_mode = False
        self.profile_graph_panel.plotWidget.first_dev_plot.clear()
        self.profile_graph_panel.plotWidget.first_dev_plot = None
        self.profile_graph_panel.plotWidget.second_dev_plot.clear()
        self.profile_graph_panel.plotWidget.second_dev_plot = None

    def update_initial_iq(self):
        if self.datacube.azavg is None:
            return
        if self.datacube.pixel_start_n is None:
            self.datacube.pixel_start_n = find_first_peak(self.datacube.azavg)
            self.datacube.pixel_end_n = len(self.datacube.azavg) - 1

        azavg_px = np.arange(len(self.datacube.azavg))
        self.datacube.all_q = pdf_calculator.pixel_to_q(azavg_px,self.datacube.ds)

        self.datacube.Iq = self.datacube.azavg[self.datacube.pixel_start_n:self.datacube.pixel_end_n+1]
        px = np.arange(self.datacube.pixel_start_n,self.datacube.pixel_end_n+1)
        self.datacube.q = pdf_calculator.pixel_to_q(px,self.datacube.ds)

    def update_initial_iq_graph(self):
        if self.datacube.all_q is None:
            return
        self.graph_Iq_Iq.setData(self.datacube.all_q,self.datacube.azavg)

        self.graph_Iq_panel.setting.spinBox_range_right.blockSignals(True)
        self.graph_Iq_panel.setting.spinBox_range_right.setMaximum(self.datacube.all_q[-1])
        self.graph_Iq_panel.setting.spinBox_range_left.setMaximum(self.datacube.all_q[-1])
        self.graph_Iq_panel.setting.spinBox_range_right.setSingleStep(self.datacube.ds * 2 * np.pi)
        self.graph_Iq_panel.setting.spinBox_range_left.setSingleStep(self.datacube.ds * 2 * np.pi)
        self.graph_Iq_panel.setting.spinBox_range_right.blockSignals(False)
        ui_util.update_value(self.graph_Iq_panel.region,
                             pdf_calculator.pixel_to_q([self.datacube.pixel_start_n,self.datacube.pixel_end_n],self.datacube.ds))

    def initui(self):
        self.controlPanel = ControlPanel(self.Dataviewer)
        self.graph_Iq_panel = GraphIqPanel()
        self.graph_phiq_panel = GraphPhiqPanel()
        self.graph_Gr_panel = GraphGrPanel()

        self.upper_left = self.controlPanel
        self.bottom_left = self.graph_Iq_panel
        self.upper_right = self.graph_phiq_panel
        self.bottom_right = self.graph_Gr_panel

        self.splitter_left_vertical = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        self.splitter_left_vertical.addWidget(self.upper_left)
        self.splitter_left_vertical.addWidget(self.bottom_left)
        self.splitter_left_vertical.setStretchFactor(1, 1)

        self.splitter_right_vertical = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        self.splitter_right_vertical.addWidget(self.upper_right)
        self.splitter_right_vertical.addWidget(self.bottom_right)

        self.left = self.splitter_left_vertical
        self.right = self.splitter_right_vertical

        self.splitter_horizontal = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.splitter_horizontal.addWidget(self.left)
        self.splitter_horizontal.addWidget(self.right)
        self.splitter_horizontal.setStretchFactor(0, 10)
        self.splitter_horizontal.setStretchFactor(1, 10)

        self.layout = QtWidgets.QHBoxLayout()
        self.layout.addWidget(self.splitter_horizontal)

    def initgraph(self):
        self.graph_Iq = self.graph_Iq_panel.graph
        self.graph_phiq = self.graph_phiq_panel.graph
        self.graph_Gr = self.graph_Gr_panel.graph

        self.graph_Iq.addLegend(offset=(-30, 30))
        self.graph_phiq.addLegend(offset=(-30, 30))
        self.graph_Gr.addLegend(offset=(-30, 30))

        self.graph_Iq_Iq = self.graph_Iq.plot(pen=pg.mkPen(255, 0, 0, width=2), name='I')
        self.graph_Iq_AutoFit = self.graph_Iq.plot(pen=pg.mkPen(0, 255, 0, width=2), name='AutoFit')
        self.graph_phiq_phiq = self.graph_phiq.plot(pen=pg.mkPen(255, 0, 0, width=2), name='phiq')
        self.graph_phiq_damp = self.graph_phiq.plot(pen=pg.mkPen(0, 255, 0, width=2), name='phiq_damp')
        self.graph_Gr_Gr = self.graph_Gr.plot(pen=pg.mkPen(255, 0, 0, width=2), name='Gr')

        self.setLayout(self.layout)


    def load_default_setting(self):
        if util.default_setting.calibration_factor is not None and self.datacube.ds is None:
            # self.controlPanel.fitting_factors.spinbox_ds.setValue(util.default_setting.calibration_factor)
            self.datacube.ds = util.default_setting.calibration_factor
        if util.default_setting.dr is not None and self.datacube.dr is None:
            # self.controlPanel.fitting_factors.spinbox_dr.setValue(util.default_setting.dr)
            self.datacube.dr = util.default_setting.dr
        if util.default_setting.damping is not None and self.datacube.damping is None:
            # self.controlPanel.fitting_factors.spinbox_damping.setValue(util.default_setting.damping)
            self.datacube.damping = util.default_setting.damping
        if util.default_setting.rmax is not None and self.datacube.rmax is None:
            # self.controlPanel.fitting_factors.spinbox_rmax.setValue(util.default_setting.rmax)
            self.datacube.rmax = util.default_setting.rmax
        if util.default_setting.electron_voltage is not None and self.datacube.electron_voltage is None:
            # self.controlPanel.fitting_factors.spinbox_electron_voltage.setText(util.default_setting.electron_voltage)
            self.datacube.electron_voltage = util.default_setting.electron_voltage

        # steps
        if util.default_setting.calibration_factor_step is not None:
            self.controlPanel.fitting_factors.spinbox_ds_step.setText(util.default_setting.calibration_factor_step)
        if util.default_setting.fit_at_q_step is not None:
            self.controlPanel.fitting_factors.spinbox_fit_at_q_step.setText(util.default_setting.fit_at_q_step)
        if util.default_setting.N_step is not None:
            self.controlPanel.fitting_factors.spinbox_N_step.setText(util.default_setting.N_step)
        if util.default_setting.dr_step is not None:
            self.controlPanel.fitting_factors.spinbox_dr_step.setText(util.default_setting.dr_step)
        if util.default_setting.damping_step is not None:
            self.controlPanel.fitting_factors.spinbox_damping_step.setText(util.default_setting.damping_step)
        if util.default_setting.rmax_step is not None:
            self.controlPanel.fitting_factors.spinbox_rmax_step.setText(util.default_setting.rmax_step)

    def save_element(self, preset_num):
        text, ok = QtWidgets.QInputDialog.getText(self, 'Input Dialog', 'Enter preset name:')
        if ok is False:
            return
        data = {}
        for idx, widget in enumerate(self.controlPanel.fitting_elements.element_group_widgets):
            data.update({"element" + str(idx):[widget.combobox.currentIndex(), widget.element_ratio.value()]})
        self.element_presets[preset_num] = [text, data]
        file.save_element_preset(self.element_presets)
        self.update_preset_enablility()

    def load_element(self, preset_num):
        data = self.element_presets[preset_num][1]
        for idx, widget in enumerate(self.controlPanel.fitting_elements.element_group_widgets):
            if "element"+str(idx) in data.keys():
                ui_util.update_value(widget.combobox, data["element"+str(idx)][0])
                ui_util.update_value(widget.element_ratio, data["element"+str(idx)][1])
            else:
                ui_util.update_value(widget.combobox, 0)
                ui_util.update_value(widget.element_ratio, 0)

    def del_element(self, preset_num):
        self.element_presets[preset_num] = None
        file.save_element_preset(self.element_presets)
        self.update_preset_enablility()

    def update_preset_enablility(self):
        for idx, action in enumerate(self.controlPanel.fitting_elements.actions_load_preset):
            if self.element_presets[idx] is not None:
                action.setDisabled(False)
                action.setText(self.element_presets[idx][0])
            else:
                action.setDisabled(True)
                action.setText('None')
        for idx, action in enumerate(self.controlPanel.fitting_elements.actions_del_preset):
            if self.element_presets[idx] is not None:
                action.setDisabled(False)
                action.setText(self.element_presets[idx][0])
            else:
                action.setDisabled(True)
                action.setText('None')
        for idx, action in enumerate(self.controlPanel.fitting_elements.actions_save_preset):
            if self.element_presets[idx] is not None:
                action.setText(self.element_presets[idx][0])
            else:
                action.setText('None')

    def put_data_to_ui(self):
        # elements
        if self.datacube.element_nums is not None:
            # for i in range(len(self.datacube.element_nums)):
            #     self.controlPanel.fitting_elements.element_group_widgets[i].combobox.setCurrentIndex(self.datacube.element_nums[i])
            #     self.controlPanel.fitting_elements.element_group_widgets[i].element_ratio.setValue(self.datacube.element_ratio[i])
            for idx, widget in enumerate(self.controlPanel.fitting_elements.element_group_widgets):
                if idx < len(self.datacube.element_nums) and self.datacube.element_nums[idx] is not None:
                    ui_util.update_value(widget.combobox,self.datacube.element_nums[idx])
                    ui_util.update_value(widget.element_ratio,self.datacube.element_ratio[idx])
                else:
                    ui_util.update_value(widget.combobox, 0)
                    ui_util.update_value(widget.element_ratio, 0)

        # factors
        if self.datacube.fit_at_q is not None:
            ui_util.update_value(self.controlPanel.fitting_factors.spinbox_fit_at_q,self.datacube.fit_at_q)
        elif self.datacube.q is not None:
            ui_util.update_value(self.controlPanel.fitting_factors.spinbox_fit_at_q, self.datacube.q[-1])
        if self.datacube.ds is not None:
            ui_util.update_value(self.controlPanel.fitting_factors.spinbox_ds,self.datacube.ds)
        if self.datacube.N is not None:
            ui_util.update_value(self.controlPanel.fitting_factors.spinbox_N,self.datacube.N)
        if self.datacube.damping is not None:
            ui_util.update_value(self.controlPanel.fitting_factors.spinbox_damping,self.datacube.damping)
        if self.datacube.dr is not None:
            ui_util.update_value(self.controlPanel.fitting_factors.spinbox_dr,self.datacube.dr)
        if self.datacube.rmax is not None:
            ui_util.update_value(self.controlPanel.fitting_factors.spinbox_rmax, self.datacube.rmax)
        if self.datacube.is_full_q is not None:
            if self.datacube.is_full_q:
                ui_util.update_value(self.controlPanel.fitting_factors.radio_full_range,True)
            else:
                ui_util.update_value(self.controlPanel.fitting_factors.radio_tail,True)
                self.btn_radiotail_clicked()
        if self.datacube.pixel_end_n is not None:
            q_l = pdf_calculator.pixel_to_q(self.datacube.pixel_start_n,self.datacube.ds)
            q_r = pdf_calculator.pixel_to_q(self.datacube.pixel_end_n,self.datacube.ds)
            ui_util.update_value(self.graph_Iq_panel.setting.spinBox_range_left, q_l)
            ui_util.update_value(self.graph_Iq_panel.setting.spinBox_range_right, q_r)
            ui_util.update_value(self.graph_Iq_panel.region,[q_l,q_r])



    def update_graph(self):
        ######## graph I(q) ########
        self.graph_Iq_panel.datacube = self.datacube
        if self.datacube.q is not None:
            # self.graph_Iq_half_tail_Iq.setData(self.datacube.q, self.datacube.Iq)
            self.graph_Iq_Iq.setData(self.datacube.all_q, self.datacube.azavg)
            self.graph_Iq_panel.range_to_dialog()
        else:
            self.graph_Iq_Iq.setData([0])

        if self.datacube.Autofit is not None:
            # self.graph_Iq_half_tail_AutoFit.setData(self.datacube.q, self.datacube.Autofit)
            # self.graph_Iq_half_tail.setXRange(self.datacube.q.max()/2,self.datacube.q.max())
            # self.graph_Iq_half_tail.YScaling()
            self.graph_Iq_AutoFit.setData(self.datacube.q, self.datacube.Autofit)
        else:
            self.graph_Iq_AutoFit.setData([0])

        ######## graph phi(q) ########
        if self.datacube.phiq is not None:
            self.graph_phiq_phiq.setData(self.datacube.q, self.datacube.phiq)
            self.graph_phiq_damp.setData(self.datacube.q, self.datacube.phiq_damp)
        else:
            # self.graph_phiq_phiq.clear() # i don't know why but it doens't work. It only works on the debug mode..
            self.graph_phiq_phiq.setData([0])
            self.graph_phiq_damp.setData([0])

        ######## graph G(r) ########
        if self.datacube.Gr is not None:
            self.graph_Gr_Gr.setData(self.datacube.r, self.datacube.Gr)
        else:
            self.graph_Gr_Gr.setData([0])

    def sig_binding(self):
        self.controlPanel.fitting_factors.btn_auto_fit.clicked.connect(self.autofit)
        self.controlPanel.fitting_factors.btn_manual_fit.clicked.connect(self.manualfit)

        # instant fit
        self.controlPanel.fitting_factors.spinbox_N.valueChanged.connect(self.instantfit)
        self.controlPanel.fitting_factors.spinbox_dr.valueChanged.connect(self.instantfit)
        self.controlPanel.fitting_factors.spinbox_rmax.valueChanged.connect(self.instantfit)
        self.controlPanel.fitting_factors.spinbox_damping.valueChanged.connect(self.instantfit)
        self.controlPanel.fitting_factors.spinbox_fit_at_q.valueChanged.connect(self.instantfit)
        self.controlPanel.fitting_factors.spinbox_ds.valueChanged.connect(self.instantfit)
        for widget in self.controlPanel.fitting_elements.element_group_widgets:
            widget.combobox.currentIndexChanged.connect(self.instantfit)
            widget.element_ratio.valueChanged.connect(self.instantfit)
        self.graph_Iq_panel.setting.spinBox_range_left.valueChanged.connect(self.instantfit)
        self.graph_Iq_panel.setting.spinBox_range_right.valueChanged.connect(self.instantfit)
        self.graph_Iq_panel.region.sigRegionChangeFinished.connect(self.instantfit)
        self.controlPanel.fitting_elements.combo_scattering_factor.currentIndexChanged.connect(self.instantfit)
        self.controlPanel.fitting_factors.spinbox_electron_voltage.textChanged.connect(self.instantfit)
        self.controlPanel.fitting_factors.radio_tail.clicked.connect(self.btn_radiotail_clicked)
        self.controlPanel.fitting_factors.radio_full_range.clicked.connect(self.btn_ratiofull_clicked)
        # self.controlPanel.fitting_factors.spinbox_q_range_left.valueChanged.connect(self.fitting_q_range_changed)
        # self.controlPanel.fitting_factors.spinbox_q_range_right.valueChanged.connect(self.fitting_q_range_changed)

        for idx, action in enumerate(self.controlPanel.fitting_elements.actions_load_preset):
            action.triggered.connect(lambda state, x=idx: (self.load_element(x),self.instantfit()))
        for idx, action in enumerate(self.controlPanel.fitting_elements.actions_save_preset):
            action.triggered.connect(lambda state, x=idx: self.save_element(x))
        for idx, action in enumerate(self.controlPanel.fitting_elements.actions_del_preset):
            action.triggered.connect(lambda state, x=idx: self.del_element(x))

    def btn_radiotail_clicked(self):
        if hasattr(self.graphPanel.graph_Iq, "region") and self.graphPanel.graph_Iq.region is not None:
            return
        self.controlPanel.fitting_factors.spinbox_q_range_left.setEnabled(True)
        self.controlPanel.fitting_factors.spinbox_q_range_right.setEnabled(True)
        ui_util.update_value(self.controlPanel.fitting_factors.spinbox_q_range_left,6.28)
        ui_util.update_value(self.controlPanel.fitting_factors.spinbox_q_range_right,self.datacube.q[-1])
        self.datacube.q_fitting_range_l = self.controlPanel.fitting_factors.spinbox_q_range_left.value()
        self.datacube.q_fitting_range_r = self.controlPanel.fitting_factors.spinbox_q_range_right.value()
        self.graphPanel.graph_Iq.region = pg.LinearRegionItem([self.datacube.q_fitting_range_l,self.datacube.q_fitting_range_r])
        self.graphPanel.graph_Iq.addItem(self.graphPanel.graph_Iq.region)

        self.graphPanel.graph_Iq.region.sigRegionChangeFinished.connect(self.range_to_dialog)
        self.controlPanel.fitting_factors.spinbox_q_range_left.valueChanged.connect(self.dialog_to_range)
        self.controlPanel.fitting_factors.spinbox_q_range_right.valueChanged.connect(self.dialog_to_range)
        self.range_fit()

    def btn_ratiofull_clicked(self):
        self.controlPanel.fitting_factors.spinbox_q_range_left.setEnabled(False)
        self.controlPanel.fitting_factors.spinbox_q_range_right.setEnabled(False)
        self.graphPanel.graph_Iq.removeItem(self.graphPanel.graph_Iq.region)
        self.graphPanel.graph_Iq.region = None
        self.autofit()


    def dialog_to_range(self):
        left = self.controlPanel.fitting_factors.spinbox_q_range_left.value()
        right = self.controlPanel.fitting_factors.spinbox_q_range_right.value()
        ui_util.update_value(self.graphPanel.graph_Iq.region,[left,right])
        self.datacube.q_fitting_range_l = left
        self.datacube.q_fitting_range_r = right
        self.range_fit()

    def range_to_dialog(self):
        left, right = self.graphPanel.graph_Iq.region.getRegion()
        left = np.round(left,1)
        right = np.round(right,1)
        if right > self.datacube.q[-1]:
            right = self.datacube.q[-1]
        if left < 0:
            left = 0
        ui_util.update_value(self.graphPanel.graph_Iq.region,[left, right])
        ui_util.update_value(self.controlPanel.fitting_factors.spinbox_q_range_left,left)
        ui_util.update_value(self.controlPanel.fitting_factors.spinbox_q_range_right,right)
        self.datacube.q_fitting_range_l = left
        self.datacube.q_fitting_range_r = right
        self.range_fit()

    def update_parameter(self):
        # default setting
        util.default_setting.calibration_factor = self.controlPanel.fitting_factors.spinbox_ds.value()
        util.default_setting.calibration_factor_step = self.controlPanel.fitting_factors.spinbox_ds_step.text()
        util.default_setting.electron_voltage = self.controlPanel.fitting_factors.spinbox_electron_voltage.text()
        util.default_setting.fit_at_q_step = self.controlPanel.fitting_factors.spinbox_fit_at_q_step.text()
        util.default_setting.N_step = self.controlPanel.fitting_factors.spinbox_N_step.text()
        util.default_setting.dr = self.controlPanel.fitting_factors.spinbox_dr.value()
        util.default_setting.dr_step = self.controlPanel.fitting_factors.spinbox_dr_step.text()
        util.default_setting.damping = self.controlPanel.fitting_factors.spinbox_damping.value()
        util.default_setting.damping_step = self.controlPanel.fitting_factors.spinbox_damping_step.text()
        util.default_setting.rmax = self.controlPanel.fitting_factors.spinbox_rmax.value()
        util.default_setting.rmax_step = self.controlPanel.fitting_factors.spinbox_rmax_step.text()

        # elements
        self.datacube.element_nums.clear()
        self.datacube.element_ratio.clear()
        for element_widget in self.controlPanel.fitting_elements.element_group_widgets:  # todo: test
            self.datacube.element_nums.append(element_widget.combobox.currentIndex())
            self.datacube.element_ratio.append(element_widget.element_ratio.value())
        self.datacube.fit_at_q = self.controlPanel.fitting_factors.spinbox_fit_at_q.value()
        self.datacube.N = self.controlPanel.fitting_factors.spinbox_N.value()
        self.datacube.damping = self.controlPanel.fitting_factors.spinbox_damping.value()
        self.datacube.rmax = self.controlPanel.fitting_factors.spinbox_rmax.value()
        self.datacube.dr = self.controlPanel.fitting_factors.spinbox_dr.value()
        self.datacube.ds = self.controlPanel.fitting_factors.spinbox_ds.value()
        self.datacube.is_full_q = self.controlPanel.fitting_factors.radio_full_range.isChecked()
        self.datacube.scattering_factor = self.controlPanel.fitting_elements.combo_scattering_factor.currentText()
        self.datacube.electron_voltage = self.controlPanel.fitting_factors.spinbox_electron_voltage.text()
        # fitting range parameters are reactively saved

    def autofit(self):
        if not self.check_condition():
            return
        if self.controlPanel.fitting_factors.radio_tail.isChecked():
            self.range_fit()
            return
        self.update_parameter()
        self.datacube.q, self.datacube.r, self.datacube.Iq, self.datacube.Autofit, self.datacube.phiq, self.datacube.phiq_damp, self.datacube.Gr, self.datacube.SS, self.datacube.fit_at_q, self.datacube.N = pdf_calculator.calculation(
            self.datacube.ds,
            self.datacube.pixel_start_n,
            self.datacube.pixel_end_n,
            self.datacube.element_nums,
            self.datacube.element_ratio,
            self.datacube.azavg,
            self.datacube.is_full_q,
            self.datacube.damping,
            self.datacube.rmax,
            self.datacube.dr,
            self.datacube.electron_voltage,
            scattering_factor_type=self.datacube.scattering_factor
        )
        ui_util.update_value(self.controlPanel.fitting_factors.spinbox_fit_at_q,self.datacube.fit_at_q)
        ui_util.update_value(self.controlPanel.fitting_factors.spinbox_N,self.datacube.N)
        # todo: add SS
        self.update_graph()
        if self.Dataviewer.top_menu.combo_dataQuality.currentIndex() == 0:
            self.Dataviewer.top_menu.combo_dataQuality.setCurrentIndex(1)

    def manualfit(self):
        if not self.check_condition_instant_fit():
            return
        if not self.check_condition():
            return
        self.update_parameter()
        self.datacube.q, self.datacube.r, self.datacube.Iq, self.datacube.Autofit, self.datacube.phiq, self.datacube.phiq_damp, self.datacube.Gr, self.datacube.SS, self.datacube.fit_at_q, self.datacube.N = pdf_calculator.calculation(
            self.datacube.ds,
            self.datacube.pixel_start_n,
            self.datacube.pixel_end_n,
            self.datacube.element_nums,
            self.datacube.element_ratio,
            self.datacube.azavg,
            self.datacube.is_full_q,
            self.datacube.damping,
            self.datacube.rmax,
            self.datacube.dr,
            self.datacube.electron_voltage,
            self.datacube.fit_at_q,
            self.datacube.N,
            self.datacube.scattering_factor
        )
        self.update_graph()

    def instantfit(self):
        self.update_parameter()
        if not self.controlPanel.fitting_factors.chkbox_instant_update.isChecked():
            # print("not checked")
            return
        if not self.check_condition_instant_fit():
            return
        if not self.check_condition(False):
            return
        self.datacube.q, self.datacube.r, self.datacube.Iq, self.datacube.Autofit, self.datacube.phiq, self.datacube.phiq_damp, self.datacube.Gr, self.datacube.SS, self.datacube.fit_at_q, self.datacube.N = pdf_calculator.calculation(
            self.datacube.ds,
            self.datacube.pixel_start_n,
            self.datacube.pixel_end_n,
            self.datacube.element_nums,
            self.datacube.element_ratio,
            self.datacube.azavg,
            self.datacube.is_full_q,
            self.datacube.damping,
            self.datacube.rmax,
            self.datacube.dr,
            self.datacube.electron_voltage,
            self.datacube.fit_at_q,
            self.datacube.N,
            self.datacube.scattering_factor
        )
        self.update_graph()

    def range_fit(self):
        if not self.check_condition():
            return
        self.update_parameter()
        print("range fit:",self.datacube.q_fitting_range_l,self.datacube.q_fitting_range_r)
        self.datacube.q, self.datacube.r, self.datacube.Iq, self.datacube.Autofit, self.datacube.phiq, self.datacube.phiq_damp, self.datacube.Gr, self.datacube.SS, self.datacube.fit_at_q, self.datacube.N = pdf_calculator.calculation(
            self.datacube.ds,
            self.datacube.pixel_start_n,
            self.datacube.pixel_end_n,
            self.datacube.element_nums,
            self.datacube.element_ratio,
            self.datacube.azavg,
            self.datacube.is_full_q,
            self.datacube.damping,
            self.datacube.rmax,
            self.datacube.dr,
            self.datacube.electron_voltage,
            self.datacube.fit_at_q,
            None,
            self.datacube.scattering_factor,
            [self.datacube.q_fitting_range_l,self.datacube.q_fitting_range_r]
        )
        ui_util.update_value(self.controlPanel.fitting_factors.spinbox_fit_at_q,self.datacube.fit_at_q)
        ui_util.update_value(self.controlPanel.fitting_factors.spinbox_N,self.datacube.N)
        self.update_graph()

    def check_condition(self, message:bool=True):
        if self.datacube.azavg is None:
            if message:
                QMessageBox.about(self, "info", "azimuthally averaged intensity is not calculated yet.")
            return False
        if np.array(self.datacube.element_nums).sum() == 0:
            if message:
                QMessageBox.about(self, "info", "set element first")
            return False
        if np.array(self.datacube.element_ratio).sum() == 0:
            if message:
                QMessageBox.about(self, "info", "set element ratio first")
            return False
        return True

    def check_condition_instant_fit(self):
        if self.datacube.fit_at_q == 0 or self.datacube.fit_at_q is None:
            return False
        return True

class GraphIqPanel(ui_util.ProfileGraphPanel):
    def __init__(self):
        ui_util.ProfileGraphPanel.__init__(self,"I(q)")
        self.graph = self.plotWidget
        self.axis = pg.InfiniteLine(angle=0)
        self.graph.addItem(self.axis)
        self.setting.lbl_range.setText("Q Range")


class GraphPhiqPanel(QtWidgets.QWidget):
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        self.layout = QtWidgets.QVBoxLayout()
        self.graph = ui_util.CoordinatesPlotWidget(title='Φ(q)')
        self.axis = pg.InfiniteLine(angle=0)
        self.graph.addItem(self.axis)
        self.layout.addWidget(self.graph)
        self.layout.setContentsMargins(5,5,5,5)
        self.setLayout(self.layout)

class GraphGrPanel(QtWidgets.QWidget):
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        self.layout = QtWidgets.QVBoxLayout()
        self.graph = ui_util.CoordinatesPlotWidget(title='G(r)')
        self.axis = pg.InfiniteLine(angle=0)
        self.graph.addItem(self.axis)
        self.layout.addWidget(self.graph)
        self.layout.setContentsMargins(5,5,5,5)
        self.setLayout(self.layout)


class ControlPanel(QtWidgets.QWidget):
    def __init__(self, mainWindow: QtWidgets.QMainWindow):
        QtWidgets.QWidget.__init__(self)
        self.layout = QtWidgets.QHBoxLayout()
        self.fitting_elements = self.FittingElements(mainWindow)
        self.fitting_factors = self.FittingFactors()

        self.layout.addWidget(self.fitting_elements)
        self.layout.addWidget(self.fitting_factors)

        # self.resize(600,1000)
        self.setLayout(self.layout)
        self.layout.setContentsMargins(2,2,2,2)



    class FittingElements(QtWidgets.QGroupBox):
        def __init__(self, mainWindow:QtWidgets.QMainWindow):
            QtWidgets.QGroupBox.__init__(self)
            self.setTitle("Element")
            layout = QtWidgets.QVBoxLayout()
            layout.setSpacing(0)
            # layout.setContentsMargins(10, 0, 5, 5)
            menubar = self.create_menu(mainWindow)
            layout.addWidget(menubar,alignment=QtCore.Qt.AlignCenter)
            layout.addWidget(self.scattering_factors_widget())


            self.element_group_widgets = [ControlPanel.element_group("Element" + str(num)) for num in range(1, 6)]
            for element_group_widgets in self.element_group_widgets:
                layout.addWidget(element_group_widgets)
            self.setLayout(layout)

        def scattering_factors_widget(self):
            widget = QtWidgets.QWidget()
            layout = QtWidgets.QHBoxLayout()
            layout.setSpacing(0)
            layout.setContentsMargins(2,2,2,2)
            widget.setLayout(layout)
            self.lbl_scattering_factor = QtWidgets.QLabel("Scattering Factor")
            layout.addWidget(self.lbl_scattering_factor)
            self.combo_scattering_factor = QtWidgets.QComboBox()
            self.combo_scattering_factor.addItems(["Kirkland","Lobato"])
            layout.addWidget(self.combo_scattering_factor)
            return widget


        def create_menu(self, mainWindow: QtWidgets.QMainWindow):
            menubar = mainWindow.menuBar()
            menubar.setNativeMenuBar(False)
            # menu_frame_widget_layout.setSpacing(0)

            load_menu = menubar.addMenu("  &Load  ")
            self.actions_load_preset = []
            preset_num = 5
            for i in range(preset_num):
                self.actions_load_preset.append(QtWidgets.QAction("None", self))
                load_menu.addAction(self.actions_load_preset[i])

            save_menu = menubar.addMenu("  &Save  ")
            self.actions_save_preset = []
            for i in range(preset_num):
                self.actions_save_preset.append(QtWidgets.QAction("None", self))
                save_menu.addAction(self.actions_save_preset[i])

            del_menu = menubar.addMenu("  &Del  ")
            self.actions_del_preset = []
            for i in range(preset_num):
                self.actions_del_preset.append(QtWidgets.QAction("None", self))
                del_menu.addAction(self.actions_del_preset[i])

            menubar.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

            return menubar

    class FittingFactors(QtWidgets.QGroupBox):
        def __init__(self):
            QtWidgets.QGroupBox.__init__(self)
            self.setTitle("Factors")
            layout = QtWidgets.QGridLayout()

            lbl_calibration_factor = QtWidgets.QLabel("Calibration factors")
            self.spinbox_ds = ui_util.DoubleSpinBox()
            self.spinbox_ds.setValue(0.001)
            self.spinbox_ds_step = ui_util.DoubleLineEdit()
            self.spinbox_ds_step.textChanged.connect(
                lambda : self.spinbox_ds.setSingleStep(float(self.spinbox_ds_step.text())))
            self.spinbox_ds.setRange(0,1e+10)
            self.spinbox_ds_step.setText("0.01")

            lbl_fitting_q_range = QtWidgets.QLabel("Fitting Q Range")
            self.radio_full_range = QtWidgets.QRadioButton("full range")
            self.radio_tail = QtWidgets.QRadioButton("select")
            self.radio_full_range.setChecked(True)
            ########### Temporary disable ##############
            lbl_fitting_q_range.setDisabled(True)
            self.radio_full_range.setDisabled(True)
            self.radio_tail.setDisabled(True)
            #############################################

            self.btn_auto_fit = QtWidgets.QPushButton("A\nu\nt\no")
            self.btn_auto_fit.setMaximumWidth(30)
            self.btn_auto_fit.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed,QtWidgets.QSizePolicy.Policy.Expanding)

            lbl_fit_at_q = QtWidgets.QLabel("Fit at q")
            self.spinbox_fit_at_q = QtWidgets.QDoubleSpinBox()
            self.spinbox_fit_at_q.setDecimals(3)
            self.spinbox_fit_at_q_step = ui_util.DoubleLineEdit()
            self.spinbox_fit_at_q_step.textChanged.connect(
                lambda : self.spinbox_fit_at_q.setSingleStep(float(self.spinbox_fit_at_q_step.text())))
            self.spinbox_fit_at_q.setRange(0,1e+10)
            self.spinbox_fit_at_q_step.setText("0.1")

            self.spinbox_q_range_left = ui_util.DoubleSpinBox()
            self.spinbox_q_range_left.setSingleStep(0.1)
            self.spinbox_q_range_left.setEnabled(False)
            self.spinbox_q_range_right = ui_util.DoubleSpinBox()
            self.spinbox_q_range_right.setSingleStep(0.1)
            self.spinbox_q_range_right.setEnabled(False)


            lbl_N = QtWidgets.QLabel("N")
            self.spinbox_N = QtWidgets.QDoubleSpinBox()
            self.spinbox_N.setDecimals(3)
            self.spinbox_N_step = ui_util.DoubleLineEdit()
            self.spinbox_N_step.textChanged.connect(
                lambda: self.spinbox_N.setSingleStep(float(self.spinbox_N_step.text())))
            self.spinbox_N.setRange(0, 1e+10)
            self.spinbox_N_step.setText("0.1")

            lbl_damping = QtWidgets.QLabel("Damping")
            self.spinbox_damping = ui_util.DoubleSpinBox()
            self.spinbox_damping_step = ui_util.DoubleLineEdit()
            self.spinbox_damping_step.textChanged.connect(
                lambda: self.spinbox_damping.setSingleStep(float(self.spinbox_damping_step.text())))
            self.spinbox_damping.setRange(0, 1e+10)
            self.spinbox_damping_step.setText("0.1")

            lbl_rmax = QtWidgets.QLabel("r(max)")
            self.spinbox_rmax = ui_util.DoubleSpinBox()
            self.spinbox_rmax_step = ui_util.DoubleLineEdit()
            self.spinbox_rmax_step.textChanged.connect(
                lambda: self.spinbox_rmax.setSingleStep(float(self.spinbox_rmax_step.text())))
            self.spinbox_rmax.setRange(0, 1e+10)
            self.spinbox_rmax_step.setText("1")

            lbl_dr = QtWidgets.QLabel("dr")
            self.spinbox_dr = ui_util.DoubleSpinBox()
            self.spinbox_dr_step = ui_util.DoubleLineEdit()
            self.spinbox_dr_step.textChanged.connect(
                lambda: self.spinbox_dr.setSingleStep(float(self.spinbox_dr_step.text())))
            self.spinbox_dr.setRange(0, 1e+10)

            lbl_electron_voltage = QtWidgets.QLabel("EV / kW")
            self.spinbox_electron_voltage = ui_util.DoubleLineEdit()
            self.spinbox_electron_voltage.setMaximumWidth(30)
            self.spinbox_electron_voltage.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed,QtWidgets.QSizePolicy.Policy.Fixed)


            self.btn_manual_fit = QtWidgets.QPushButton("Manual")
            self.btn_manual_fit = QtWidgets.QPushButton("M\na\nn\nu\na\nl")
            self.btn_manual_fit.setMaximumWidth(30)
            self.btn_manual_fit.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Expanding)

            lbl_instant_update = QtWidgets.QLabel("instant update")
            self.chkbox_instant_update = QtWidgets.QCheckBox()

            layout.addWidget(lbl_calibration_factor, 0, 0)
            layout.addWidget(self.spinbox_ds, 0, 2, 1, 1)
            layout.addWidget(self.spinbox_ds_step, 0, 3, 1, 1)

            layout.addWidget(lbl_fitting_q_range, 1, 0, 1, 2)
            layout.addWidget(self.radio_full_range, 1, 2)
            layout.addWidget(self.radio_tail, 1, 3)
            layout.addWidget(self.spinbox_q_range_left, 2, 2, 1, 1)
            layout.addWidget(self.spinbox_q_range_right, 2, 3, 1, 1)

            layout.addWidget(self.btn_auto_fit, 0, 4, 3, 1)

            layout.addWidget(ui_util.QHLine(),3,0,1,5)

            layout.addWidget(lbl_fit_at_q, 4, 0, 1, 2)
            layout.addWidget(self.spinbox_fit_at_q, 4, 2, 1, 1)
            layout.addWidget(self.spinbox_fit_at_q_step, 4, 3, 1, 1)

            layout.addWidget(lbl_N, 5, 0, 1, 2)
            layout.addWidget(self.spinbox_N, 5, 2, 1, 1)
            layout.addWidget(self.spinbox_N_step, 5, 3, 1, 1)

            layout.addWidget(lbl_damping, 6, 0, 1, 2)
            layout.addWidget(self.spinbox_damping, 6, 2, 1, 1)
            layout.addWidget(self.spinbox_damping_step, 6, 3, 1, 1)

            layout.addWidget(lbl_rmax, 7, 0, 1, 2)
            layout.addWidget(self.spinbox_rmax, 7, 2, 1, 1)
            layout.addWidget(self.spinbox_rmax_step, 7, 3, 1, 1)

            layout.addWidget(lbl_dr, 8, 0, 1, 2)
            layout.addWidget(self.spinbox_dr, 8, 2, 1, 1)
            layout.addWidget(self.spinbox_dr_step, 8, 3, 1, 1)

            layout.addWidget(self.btn_manual_fit, 4, 4, 5, 1)

            layout.addWidget(ui_util.QHLine(), 9, 0, 1, 5)

            layout.addWidget(lbl_instant_update, 10, 0,1,2)
            layout.addWidget(self.chkbox_instant_update, 10, 2)

            layout.addWidget(lbl_electron_voltage, 10, 3)
            layout.addWidget(self.spinbox_electron_voltage, 10, 4)

            layout.setSpacing(1)
            # layout.setContentsMargins(0,0,0,0)

            self.setLayout(layout)

    class element_group(QtWidgets.QWidget):
        def __init__(self, label: str):
            QtWidgets.QWidget.__init__(self)
            layout = QtWidgets.QHBoxLayout()
            layout.setContentsMargins(0,0,0,0)
            layout.setSpacing(0)
            lbl = QtWidgets.QLabel(label)
            self.combobox = QtWidgets.QComboBox()
            self.combobox.addItems(util.get_atomic_number_symbol())
            # todo: combobox
            self.element_ratio = QtWidgets.QSpinBox()
            self.element_ratio.setMaximum(10000000)
            layout.addWidget(lbl)
            layout.addWidget(self.combobox)
            layout.addWidget(self.element_ratio)
            self.setLayout(layout)


if __name__ == "__main__":
    qtapp = QtWidgets.QApplication([])
    # QtWidgets.QMainWindow().show()
    window = PdfAnalysis(DataCube())
    window.show()
    qtapp.exec()