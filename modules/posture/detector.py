import cv2
import mediapipe as mp
import numpy as np
import math
from .config import (
    SHOULDER_TILT_THRESH, 
    HEAD_FORWARD_THRESH, 
    HUNCHBACK_THRESH,
    NECK_TILT_THRESH,
    SCREEN_RATIO_THRESH,
    LEAN_DEGREE_THRESH
)

class PostureDetector:
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False, 
            model_complexity=1, 
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # 用于稳定性分析的历史数据
        self.history = [] 

    def process_frame(self, image):
        """
        接收一帧图像，返回分析结果
        """

        # 图像预处理
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.pose.process(image_rgb)

        # 初始化返回数据
        output_data = {
            # 评估结果
            "is_shoulder_tilted": False,        # 肩膀是否倾斜
            "is_head_forward": False,           # 头部是否前伸
            "is_hunchback": False,              # 是否驼背
            "is_neck_tilted": False,            # 颈部是否侧倾
            "dist_screen": "normal",            # 距离屏幕: too_close/normal
            "body_lean": "centered",            # 躯干位置
            
            # 各项评分和角度
            "shoulder_tilt_angle": 0.0,         # 肩膀倾斜角度
            "head_forward_degree": 0.0,         # 头部前伸程度
            "hunchback_degree": 0.0,            # 驼背程度
            "neck_tilt": 0.0,                   # 颈部侧倾角度
            "shoulder_screen_ratio": 0.0,       # 肩膀宽度与屏幕宽度比
            "lean_degree":0,                    # 躯干偏移程度
            "stability_score": 100,             # 稳定性评分
            "landmarks": [],                    # 返回关键点给前端画图用
        }


        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            h, w, _ = image.shape

            # 返回关键点，方便前端界面上画骨架
            output_data["landmarks"] = results.pose_landmarks

            # 获取关键点坐标，计算基础数据
            nose = np.array([landmarks[0].x * w, landmarks[0].y * h, landmarks[0].z * w]) 
            l_ear = np.array([landmarks[7].x * w, landmarks[7].y * h])
            r_ear = np.array([landmarks[8].x * w, landmarks[8].y * h])
            l_shoulder = np.array([landmarks[11].x * w, landmarks[11].y * h, landmarks[11].z * w])
            r_shoulder = np.array([landmarks[12].x * w, landmarks[12].y * h, landmarks[12].z * w])
            shoulder_mid = (l_shoulder + r_shoulder) / 2
            ear_mid = (l_ear + r_ear) / 2
            shoulder_width = np.linalg.norm(l_shoulder[:2] - r_shoulder[:2]) # 只取xy计算宽度

            # 计算肩膀倾斜
            dy = r_shoulder[1] - l_shoulder[1]
            dx = r_shoulder[0] - l_shoulder[0]
            angle = math.degrees(math.atan2(dy, dx))
            output_data["shoulder_tilt_angle"] = round(angle, 2)
            if abs(angle) > SHOULDER_TILT_THRESH:
                output_data["is_shoulder_tilted"] = True
            
            # 判断头部前伸
            if shoulder_width > 0:
                z_diff = (shoulder_mid[2] - nose[2]) / shoulder_width
            else:
                z_diff = 0
            head_forward_degree = z_diff
            output_data["head_forward_degree"] = head_forward_degree
            if z_diff > HEAD_FORWARD_THRESH:
                output_data["is_head_forward"] = True
            
            # 判断驼背
            if shoulder_width > 0:
                neck_ratio = (shoulder_mid[1] - ear_mid[1]) / shoulder_width
            else:
                neck_ratio = 0
            hunchback_degree = neck_ratio
            if neck_ratio < HUNCHBACK_THRESH:
                output_data["is_hunchback"] = True
            output_data["hunchback_degree"] = hunchback_degree
            
            # 计算颈部侧倾
            dy_ear = r_ear[1] - l_ear[1]
            dx_ear = r_ear[0] - l_ear[0]
            head_angle = math.degrees(math.atan2(dy_ear, dx_ear))
            output_data["neck_tilt"] = round(head_angle, 2)
            if abs(head_angle) > NECK_TILT_THRESH:
                output_data["is_neck_tilted"] = True

            # 判断是否距离屏幕过近
            shoulder_screen_ratio = shoulder_width / w
            output_data["shoulder_screen_ratio"] = round(shoulder_screen_ratio, 2)
            if shoulder_screen_ratio > SCREEN_RATIO_THRESH:
                output_data["dist_screen"] = "too_close"

            # 判断躯干偏移
            center_x = shoulder_mid[0]
            img_center = w / 2
            lean_degree = (center_x - img_center) / w
            output_data["lean_degree"]=lean_degree
            if lean_degree > LEAN_DEGREE_THRESH:
                output_data["body_lean"] = "leaning_right" # 画面右侧
            elif lean_degree < -LEAN_DEGREE_THRESH:
                output_data["body_lean"] = "leaning_left"  # 画面左侧

            # 稳定性分析
            current_center = (l_shoulder + r_shoulder) / 2
            self.history.append(current_center)
            if len(self.history) > 50:
                self.history.pop(0)
            if len(self.history) > 5:
                history_array = np.array(self.history)
                std_devs = np.std(history_array, axis=0)
                # 归一化：将像素抖动转为相对于画面宽度的比例
                normalized_jitter = (std_devs[0] / w + std_devs[1] / h) / 2 * 1000
                deduction = min(normalized_jitter * 5, 60) 
                output_data["stability_score"] = int(100 - deduction)

        return output_data
    
    def close(self):
        self.pose.close()