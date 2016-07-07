#  ================================================================
#  Created by Gregory Kramida on 7/7/16.
#  Copyright (c) 2016 Gregory Kramida
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#  ================================================================

import cv2
import cve
import os.path
import numpy as np
from enum import Enum


class MaskLabel(Enum):
    FOREGROUND_LABEL = 255
    PERSISTENCE_LABEL = 180
    SHADOW_LABEL = 80
    BACKGROUND_LABEL = 0

class ConnectedComponentThreshold(Enum):
    HIDDEN = 1200
    BBOX_THRESH = 6500
    TRACK_DIST_THRESH = 60.

class BackgroundSubtractor():
    @staticmethod
    def prep_parser(parser):
        # ====================IMBS parameters========================== #
        parser.add_argument("--fps", type=float, default=60.0)

        parser.add_argument("--fg_threshold", type=int, default=15)
        parser.add_argument("--association_threshold", type=int, default=5)

        parser.add_argument("-sis", "--sampling_interval_start_frame", type=int, default=-1)
        parser.add_argument("-sie", "--sampling_interval_end_frame", type=int, default=-1)

        parser.add_argument("--sampling_interval", type=float, default=250.0,
                            help="Duration, in ms, of the sampling interval between frames"
                                 " used to build initial background model")
        parser.add_argument("--num_samples", type=int, default=30)

        parser.add_argument("--min_bin_height", type=int, default=2)

        # *** shadow ***
        parser.add_argument("--alpha", type=float, default=0.65,
                            help="Lower bound on the value ratio between image & " +
                                 "model for the pixel to be labeled shadow")
        parser.add_argument("--beta", type=float, default=1.15,
                            help="Upper bound on the value ratio between image & " +
                                 "model for the pixel to be labeled shadow")
        parser.add_argument("--tau_s", type=float, default=60.,
                            help="Upper bound on the saturation difference between image & model "
                                 "for the pixel to be labeled as shadow")
        parser.add_argument("--tau_h", type=float, default=40.,
                            help="Upper bound on the hue difference between image & model "
                                 "for the pixel to be labeled as shadow")
        # ***************
        parser.add_argument("--min_area", type=float, default=1.15,
                            help="")

        parser.add_argument("--persistence_period", type=float, default=10000.0,
                            help="Duration of the persistence period in ms")
        parser.add_argument("-m", "--use_morphological_filtering", help="Use morphological filtering (open, close) on "
                                                                        "the result.", default=False,
                            action='store_true')
        # ============================================================= #

        parser.add_argument("-mf", "--mask_file", default=None)

    def __init__(self, args):
        self.__dict__.update(vars(args))
        self.subtractor = cve.BackgroundSubtractorIMBS(self.fps, self.fg_threshold, self.association_threshold,
                                                       self.sampling_interval, self.min_bin_height, self.num_samples,
                                                       self.alpha, self.beta, self.tau_s, self.tau_h,
                                                       self.min_area, self.persistence_period,
                                                       self.use_morphological_filtering, False)
        if self.mask_file is not None:
            self.mask_file = os.path.join(self.datapath, self.mask_file)
            if not os.path.isfile(self.mask_file):
                raise ValueError("Could not find preliminary mask file at {:s}.".format(self.mask_file))
            self.prelim_mask = cv2.imread(self.mask_file, cv2.IMREAD_COLOR)
        else:
            self.prelim_mask = None
        self.mask = None
