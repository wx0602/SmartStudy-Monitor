import json
from modules.behavior.hand_behavior import HandBadHabitsDetector
from modules.behavior.phone_detector import PhoneDetector
from modules.behavior.seat_occupancy_detector import SeatOccupancyDetector


class BehaviorDetector:
    """
    行为检测总调度器
    负责整合多个行为检测模块的结果
    """

    def __init__(self, config):
        self.hand_detector = HandBadHabitsDetector(config)
        self.phone_detector = PhoneDetector(config)
        self.seat_detector = SeatOccupancyDetector(config)

    def process(self, results, frame=None):
        """
        对单帧结果进行行为检测。
        
        Args:
            results: MediaPipe 或其他模块的前置检测结果
            frame: 当前视频帧
            
        Returns:
            dict: 包含各项行为检测状态的字典
        """
        hand_result = self.hand_detector.detect_hand_bad_habits(results)
        phone_result = self.phone_detector.detect(results, frame=frame)
        seat_result = self.seat_detector.detect(results)

        return {
            "手部行为": hand_result,
            "手机使用": phone_result,
            "离席检测": seat_result
        }

    def process_json(self, results, frame=None):
        """
        返回 JSON 字符串（方便调试 / 输出）。
        """
        return json.dumps(
            self.process(results, frame=frame),
            ensure_ascii=False,
            indent=4
        )