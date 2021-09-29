import file
from calculate import image_process

import os
import cv2
import numpy as np

class DataCube:
    _use_cupy = False
    try:
        import cupy as cp
        _use_cupy = True
    except ImportError:
        _use_cupy = False

    def __init__(self, file_path=None, file_type=None):
        """
        :param file_path: str
        :param file_type: preset, azavg, image
        """
        self.raw_img = None
        self.img = None
        self.center = [None,None]
        self.azavg = None
        self.azvar = None
        self.pixel_start_n = None
        self.pixel_end_n = None
        self.ds = None
        self.display_img = None

        self.fit_at_q = None
        self.N = None
        self.damping = None
        self.rmax = None
        self.dr = None
        self.is_full_q = None

        self.q = None
        self.r = None

        self.Iq = None
        self.Gr = None

        self.SS = None
        self.phiq = None
        self.phiq_damp = None
        self.Autofit = None
        self.analyser = None
        self.element_nums = None
        self.element_ratio = None
        self.scattering_factor = None
        self.electron_voltage = None


        self.load_file_path = file_path
        self.preset_file_path = None
        self.azavg_file_path = None
        self.mrc_file_path = None
        if file_type == "preset":
            self.preset_file_path = self.load_file_path
            file.load_preset(self,self.preset_file_path)
        elif file_type == "azavg":
            self.azavg_file_path = self.load_file_path
            self.azavg = file.load_azavg(self.azavg_file_path)
        elif file_type == "image":
            self.mrc_file_path = self.load_file_path
            # file.load_mrc_img(self,self.mrc_file_path)


    def image_ready(self):
        if self.mrc_file_path is not None:
            self.raw_img, self.img = file.load_mrc_img(self.mrc_file_path)

    def release(self):
        self.raw_img, self.img = None, None

    def calculate_center(self, intensity_range, step_size):
        if self.img is None:
            return
        self.center = list(image_process.calculate_center_gradient(self.img, intensity_range, step_size))
        print("selected center: ", self.center)
        return self.center

    def calculate_azimuthal_average(self, intensity_range=None, step_size=None):
        if self.img is None:
            raise Exception("You don't have img data")
        if self.center[0] is None:
            if (intensity_range is not None) and (step_size is not None):
                self.calculate_center(intensity_range, step_size)
            else:
                raise Exception("You need to calculate center first")
        self.azavg, self.azvar = image_process.calculate_azimuthal_average(self.raw_img, self.center)
        return self.azavg, self.azvar

    def save_azimuthal_data(self, intensity_start, intensity_end, intensity_slice, imgPanel=None, draw_center_line=False, masking=False):
        if self.center[0] is None:
            self.calculate_center((intensity_start, intensity_end), intensity_slice)
        if self.azavg is None:
            self.calculate_azimuthal_average()

        i_list = [intensity_start,intensity_end,intensity_slice]
        file.save_current_azimuthal(self.azavg, self.mrc_file_path, True, i_slice=i_list) # todo: seperate method
        file.save_current_azimuthal(self.azvar, self.mrc_file_path, False, i_slice=i_list)

        folder_path, file_full_name = os.path.split(self.mrc_file_path)
        file_name, ext = os.path.splitext(file_full_name)

        update_img = self.img.copy()

        if masking == True:
            update_img = cv2.bitwise_and(self.img, self.img, mask=np.bitwise_not(image_process.mask))

        if draw_center_line == True:
            update_img = image_process.draw_center_line(update_img, self.center)
            imgPanel.update_img(update_img)

        if imgPanel is not None:
            img_file_path = os.path.join(folder_path, file.ePDFpy_analysis_folder_name, file_name + "_img.tiff")
            imgPanel.imageView.export(img_file_path)
