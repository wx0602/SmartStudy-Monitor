import cv2
import mediapipe as mp
import numpy as np
import math

class PostureDetector:
    def __init__(self, thresholds):
        """
        初始化：加载模型，设置阈值
        :param thresholds: 从 config/thresholds.yaml 读取到的配置字典
        """
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False, 
            model_complexity=1, 
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # 保存阈值
        self.config = thresholds 
        
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
            "hunchback": False,          # 是否驼背
            "head_forward": False,       # 头部是否前伸
            "shoulder_tilt": 0.0,        # 肩膀倾斜角度
            "dist_screen": "normal",     # 距离屏幕: near/normal/far
            "stability_score": 100,      # 稳定性评分
            "landmarks": [],            # (可选) 返回关键点给前端画图用
            "neck_tilt": 0.0,            # 脖子侧倾 (新功能)
            "body_lean": "centered",     # 躯干位置 (新功能: left/right/centered)
        }


        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            h, w, _ = image.shape

            # 获取关键点坐标，计算基础数据
            # 鼻子(0), 左耳(7), 右耳(8), 左肩(11), 右肩(12)，嘴巴（13）
            nose = np.array([landmarks[0].x * w, landmarks[0].y * h, landmarks[0].z * w]) 
            l_ear = np.array([landmarks[7].x * w, landmarks[7].y * h])
            r_ear = np.array([landmarks[8].x * w, landmarks[8].y * h])
            l_shoulder = np.array([landmarks[11].x * w, landmarks[11].y * h, landmarks[11].z * w])
            r_shoulder = np.array([landmarks[12].x * w, landmarks[12].y * h, landmarks[12].z * w])

            shoulder_mid = (l_shoulder + r_shoulder) / 2
            ear_mid = (l_ear + r_ear) / 2
            shoulder_width = np.linalg.norm(l_shoulder[:2] - r_shoulder[:2]) # 只取xy计算宽度

            # === A. 计算肩膀倾斜 ===
            # 计算两肩连线的斜率或角度
            dy = r_shoulder[1] - l_shoulder[1]
            dx = r_shoulder[0] - l_shoulder[0]
            angle = math.degrees(math.atan2(dy, dx))
            output_data["shoulder_tilt"] = round(angle, 2)
            
            # === B. 判断头部前伸 ===
            # 逻辑：比较鼻子Z和肩膀中点Z，Z越小越近。如果鼻子比肩膀近太多，就是探头。
            # 归一化：除以肩膀宽度，防止离远离近影响数值
            if shoulder_width > 0:
                z_diff = (shoulder_mid[2] - nose[2]) / shoulder_width
            else:
                z_diff = 0
            forward_thresh = self.config.get('head_forward_z_threshold', 2.0)
            if z_diff > forward_thresh:
                output_data["head_forward"] = True

            # === C. 判断驼背耸肩 ===
            # 逻辑：计算脖子视觉长度（嘴巴Y到肩膀Y的距离），如果长度变短，就是驼背
            if shoulder_width > 0:
                neck_ratio = (shoulder_mid[1] - ear_mid[1]) / shoulder_width
            else:
                neck_ratio = 0
        
            hunchback_thresh = self.config.get('hunchback_ratio_threshold', 0.25)
            if neck_ratio < hunchback_thresh:
                output_data["hunchback"] = True
            
            # === D. 计算颈部侧倾角度 ===
            # 计算两耳连线的角度
            dy_ear = r_ear[1] - l_ear[1]
            dx_ear = r_ear[0] - l_ear[0]
            head_angle = math.degrees(math.atan2(dy_ear, dx_ear))
            output_data["neck_tilt"] = round(head_angle, 2)

            # === E. 判断是否距离屏幕过近 ===
            # 逻辑：肩膀宽度超过画面宽度的 50% 算太近
            screen_width_ratio = shoulder_width / w
            dist_limit = self.config.get('max_shoulder_width_ratio', 0.5)
            
            if screen_width_ratio > dist_limit:
                output_data["dist_screen"] = "too_close"
            elif screen_width_ratio < 0.2: 
                output_data["dist_screen"] = "far"

            # === F. 判断躯干偏移 ===
            # 逻辑：肩膀中点 X 坐标是否偏离画面中心 (0.5 * w)
            # 归一化偏差： (中点X - 画面中心) / 画面宽
            center_x = shoulder_mid[0]
            img_center = w / 2
            lean_ratio = (center_x - img_center) / w
            
            if lean_ratio > 0.15:
                output_data["body_lean"] = "leaning_right" # 画面右侧
            elif lean_ratio < -0.15:
                output_data["body_lean"] = "leaning_left"  # 画面左侧

            # === G. 稳定性分析 (修正版) ===
            # 计算当前肩膀中心点 (像素坐标)
            current_center = (l_shoulder + r_shoulder) / 2
            self.history.append(current_center)
            
            # 只保留最近 20 帧
            if len(self.history) > 20:
                self.history.pop(0)
            
            # 计算标准差 (抖动程度)
            if len(self.history) > 5:
                # 1. 转成 numpy 矩阵，形状是 (N, 2)
                history_array = np.array(self.history)
                
                # 2. 关键修正：axis=0
                # axis=0 表示“沿着纵轴”计算，也就是分别算 X列的std 和 Y列的std
                # 结果会是类似 [1.5, 2.3] 这样的数组
                std_devs = np.std(history_array, axis=0)
                
                # 3. 综合抖动值 (取 X抖动 和 Y抖动 的平均值)
                avg_jitter = np.mean(std_devs)
                
                # 4. 打分逻辑优化
                # 正常坐着呼吸，像素抖动可能在 0.5 ~ 2.0 之间
                # 乱动的时候，抖动可能会到 10.0 以上
                # 建议：系数设为 5，即抖动 1像素扣5分，抖动 8像素就扣满40分
                deduction = min(avg_jitter * 5, 40)
                
                stability = 100 - deduction
                output_data["stability_score"] = int(stability)
            


            # 塞入关键点，方便界面上画骨架
            output_data["landmarks"] = results.pose_landmarks

        return output_data