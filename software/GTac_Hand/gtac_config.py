# this configuration file is for GTac-Gripper.
import numpy as np
import sklearn

COLUMNS_RAW_FINGER_DATA = ['mag_x1', 'mag_y1', 'mag_z1',
                           'mag_x2', 'mag_y2', 'mag_z2',
                           'mag_x3', 'mag_y3', 'mag_z3',
                           'mag_x4', 'mag_y4', 'mag_z4',
                           'mag_x5', 'mag_y5', 'mag_z5',
                           'mag_x6', 'mag_y6', 'mag_z6',
                           'mag_x7', 'mag_y7', 'mag_z7',
                           'mag_x8', 'mag_y8', 'mag_z8',
                           'mag_x9', 'mag_y9', 'mag_z9',
                           'mag_x10', 'mag_y10', 'mag_z10',
                           'mag_x11', 'mag_y11', 'mag_z11',
                           'mag_x12', 'mag_y12', 'mag_z12',
                           'mag_x13', 'mag_y13', 'mag_z13',
                           'mag_x14', 'mag_y14', 'mag_z14',
                           'mag_x15', 'mag_y15', 'mag_z15',
                           'mat1', 'mat2', 'mat3', 'mat4',
                           'mat5', 'mat6', 'mat7', 'mat8',
                           'mat9', 'mat10', 'mat11', 'mat12',
                           'mat13', 'mat14', 'mat15', 'mat16',
                           'mat17', 'mat18', 'mat19', 'mat20',
                           'mat1', 'mat2', 'mat3', 'mat4',
                           'mat5', 'mat6', 'mat7', 'mat8',
                           'mat9', 'mat10', 'mat11', 'mat12',
                           'mat13', 'mat14', 'mat15', 'mat16',
                           'mat17', 'mat18', 'mat19', 'mat20',
                           'mat1', 'mat2', 'mat3', 'mat4',
                           'mat5', 'mat6', 'mat7', 'mat8',
                           'mat9', 'mat10', 'mat11', 'mat12',
                           'mat13', 'mat14', 'mat15', 'mat16',
                           'mat17', 'mat18', 'mat19', 'mat20',
                           'mat1', 'mat2', 'mat3', 'mat4',
                           'mat5', 'mat6', 'mat7', 'mat8',
                           'mat9', 'mat10', 'mat11', 'mat12',
                           'mat13', 'mat14', 'mat15', 'mat16',
                           'mat17', 'mat18', 'mat19', 'mat20',
                           'mat1', 'mat2', 'mat3', 'mat4',
                           'mat5', 'mat6', 'mat7', 'mat8',
                           'mat9', 'mat10', 'mat11', 'mat12',
                           'mat13', 'mat14', 'mat15', 'mat16',
                           'mat17', 'mat18', 'mat19', 'mat20',
                           'mat1', 'mat2', 'mat3', 'mat4',
                           'mat5', 'mat6', 'mat7', 'mat8',
                           'mat9', 'mat10', 'mat11', 'mat12',
                           'mat13', 'mat14', 'mat15', 'mat16',
                           'mat17', 'mat18', 'mat19', 'mat20',
                           'mat1', 'mat2', 'mat3', 'mat4',
                           'mat5', 'mat6', 'mat7', 'mat8',
                           'mat9', 'mat10', 'mat11', 'mat12',
                           'mat13', 'mat14', 'mat15', 'mat16',
                           'mat17', 'mat18', 'mat19', 'mat20',
                           'mat1', 'mat2', 'mat3', 'mat4',
                           'mat5', 'mat6', 'mat7', 'mat8',
                           'mat9', 'mat10', 'mat11', 'mat12',
                           'mat13', 'mat14', 'mat15', 'mat16',
                           'mat17', 'mat18', 'mat19', 'mat20',
                           'mat1', 'mat2', 'mat3', 'mat4',
                           'mat5', 'mat6', 'mat7', 'mat8',
                           'mat9', 'mat10', 'mat11', 'mat12',
                           'mat13', 'mat14', 'mat15', 'mat16',
                           'mat17', 'mat18', 'mat19', 'mat20',
                           'mat1', 'mat2', 'mat3', 'mat4',
                           'mat5', 'mat6', 'mat7', 'mat8',
                           'mat9', 'mat10', 'mat11', 'mat12',
                           'mat13', 'mat14', 'mat15', 'mat16',
                           'mat17', 'mat18', 'mat19', 'mat20',
                           'mat1', 'mat2', 'mat3', 'mat4',
                           'mat5', 'mat6', 'mat7', 'mat8',
                           'mat9', 'mat10', 'mat11', 'mat12',
                           'mat13', 'mat14', 'mat15', 'mat16',
                           'mat17', 'mat18', 'mat19', 'mat20',
                           'mat1', 'mat2', 'mat3', 'mat4',
                           'mat5', 'mat6', 'mat7', 'mat8',
                           'mat9', 'mat10', 'mat11', 'mat12',
                           'mat13', 'mat14', 'mat15', 'mat16',
                           'mat17', 'mat18', 'mat19', 'mat20',
                           'servo_1', 'servo_2', 'servo_3', 'servo_4', 'servo_5', 'servo_6',
                           'Hz', 'milliseconds']

COLUMNS_Finger = ['mat_x1y1', 'mat_x1y2', 'mat_x1y3', 'mat_x1y4',
                  'mat_x2y1', 'mat_x2y2', 'mat_x2y3', 'mat_x2y4',
                  'mat_x3y1', 'mat_x3y2', 'mat_x3y3', 'mat_x3y4',
                  'mat_x4y1', 'mat_x4y2', 'mat_x4y3', 'mat_x4y4',
                  'mag_x', 'mag_y', 'mag_z',
                  'finger', 'section', 'milliseconds', 'Sample Index'
                  ]

COLUMNS_Sec_Features = ['press_location_r', 'press_location_c',
                        'FA_sum', 'feature_d_FA_sum',
                        'feature_SFA_x', 'feature_SFA_y', 'feature_SFA_z',
                        'feature_dSA_x', 'feature_dSA_y', 'feature_dSA_z',
                        'feature_FA_event',
                        'feature_SA_event_x', 'feature_SA_event_y', 'feature_SA_event_z',
                        'finger', 'section', 'milliseconds', 'Sample Index'
                        ]

RF_MAT_ROW = np.array([[0, 0, 0, 0], [1, 1, 1, 1], [3, 3, 3, 3], [2, 2, 2, 2]])
RF_MAT_COL = np.array([[2, 3, 1, 0], [2, 3, 1, 0], [2, 3, 1, 0], [2, 3, 1, 0]])

LF_MAT_ROW = np.array([[0, 0, 0, 0], [1, 1, 1, 1], [3, 3, 3, 3], [2, 2, 2, 2]])
LF_MAT_COL = np.array([[0, 1, 3, 2], [0, 1, 3, 2], [0, 1, 3, 2], [0, 1, 3, 2]])

UP_MAT_ROW = np.array([[2, 3, 1, 0], [2, 3, 1, 0], [2, 3, 1, 0], [2, 3, 1, 0]])
UP_MAT_COL = np.array([[2, 2, 2, 2], [3, 3, 3, 3], [1, 1, 1, 1], [0, 0, 0, 0]])

MAT_ORIENT_ROW = np.array([[LF_MAT_ROW, LF_MAT_ROW, LF_MAT_ROW],
                           [RF_MAT_ROW, LF_MAT_ROW, LF_MAT_ROW],
                           [RF_MAT_ROW, RF_MAT_ROW, RF_MAT_ROW],
                           [LF_MAT_ROW, LF_MAT_ROW, LF_MAT_ROW],
                           [RF_MAT_ROW, LF_MAT_ROW, LF_MAT_ROW]])
MAT_ORIENT_COL = np.array([[LF_MAT_COL, LF_MAT_COL, LF_MAT_COL],
                           [RF_MAT_COL, LF_MAT_COL, LF_MAT_COL],
                           [RF_MAT_COL, RF_MAT_COL, RF_MAT_COL],
                           [LF_MAT_COL, LF_MAT_COL, LF_MAT_COL],
                           [RF_MAT_COL, LF_MAT_COL, LF_MAT_COL]])

MAG_NUM = 45
MAT_NUM = 16
ALL_GTAC_NUM = 285
COL_INDEX = np.array([[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11]])
COL_NUM = 12
FINGER_NUM = 5
SEC_NUM = 3
FINGER_NAME = ['THUMB', 'INDEX', 'MIDDLE', 'RING', 'LITTLE']
SEC_NAME = ['Palm', 'Middle', 'Distal']
FINGER_MOTOR = ['Thumb Fle', 'Thumb Abd', 'Middle', 'Index', 'Little', 'Ring']

SENSOR_MAP = [0, 4, 3, 1]
MOTOR_MAP = [[1, 5], [2, 6], [3, 7], [4, 8]]
MOTOR_NUM = 8
FINGER_FLEX_MOTOR_IND = [0, 3, 2, 5, 4]
SA_II_preprocess_x = [[1, 1, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]]
SA_II_preprocess_y = []
SA_II_preprocess_ = []
PALM_GTAC_INDEX = [[0, 0], [0, 1], [1, 0], [2, 0], [3, 0], [4, 0]]

ECS_LABEL_REORDER = [8, 3, 1, 0, 4, 5, 7, 2, 6]
# Sharpness Detection
SD_LABEL_REORDER = [3, 0, 4, 2, 1]
SD_NEW_LABEL_REORDER = [0, 1, 2]

fname_backward = 'fig/ECS/arrow_backward.png'
fname_forward = 'fig/ECS/arrow_forward.png'
fname_right = 'fig/ECS/arrow_right.png'
fname_left = 'fig/ECS/arrow_left.png'
fname_pull = 'fig/ECS/arrow_pull.png'
fname_push = 'fig/ECS/arrow_push.png'
fname_clk = 'fig/ECS/arrow_clk.png'
fname_anti_clk = 'fig/ECS/arrow_anti_clk.png'
fname_none = 'fig/ECS/none.png'

fname_none_ball = 'fig/ECS/none_ball.png'
fname_left_ball = 'fig/ECS/left_ball.png'
fname_right_ball = 'fig/ECS/right_ball.png'



fname_img = {'none': fname_none,
             'forward': fname_forward,
             'backward': fname_backward,
             'right': fname_right,
             'left': fname_left,
             'pull': fname_pull,
             'push': fname_push,
             'twist_clk': fname_clk,
             'twist_anti_clk': fname_anti_clk,
             }

fname_img_ball = {'none': fname_none_ball,
             'forward': fname_forward,
             'backward': fname_backward,
             'right': fname_right,
             'left': fname_left,
             'pull': fname_pull,
             'push': fname_push,
             'twist_clk': fname_left_ball,
             'twist_anti_clk': fname_right_ball,
             }
title_ball = {'none': 'None',
             'forward': 'forward',
             'backward': 'backward',
             'right': 'right',
             'left': 'left',
             'pull': 'pull',
             'push': 'push',
             'twist_clk': 'Left Hit',
             'twist_anti_clk': 'Right Hit',
             }


CNN_classes = ['backward',
               'forward',
               'left',
               'none',
               'pull',
               'push',
               'right',
               'twist_anti_clk',
               'twist_clk']

# ML_model_type = [sklearn.discriminant_analysis.QuadraticDiscriminantAnalysis,
#                  sklearn.svm._classes.SVC,
#                  sklearn.discriminant_analysis.LinearDiscriminantAnalysis]
