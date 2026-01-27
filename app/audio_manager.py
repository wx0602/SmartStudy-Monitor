import os
from pathlib import Path
from PyQt5.QtCore import QObject, QUrl
from PyQt5.QtMultimedia import QSoundEffect
import winsound  # 作为自定义声音导入失败的备用方案

class AudioManager(QObject):
    def __init__(self):
        super().__init__()
        self.sounds = {}
        self.volume = 0.5  # 默认音量
        
        # 定位到 assets/sounds 目录
        self.root = Path(__file__).resolve().parents[1]
        self.sound_dir = self.root / "assets" / "sounds"
        
        # 定义需要加载的音效名称（已经在对应文件中重命名）
        self.sound_map = {
            "alert": "alert.wav",   # 提示音
            "alarm": "alarm.wav",   # 闹钟音
            "click": "click.wav",   # 点击音，此音效未被使用
            "timer": "timer.wav",   # 时钟和计时器专用音效
        }
        
        self._init_sounds()

    def _init_sounds(self):
        """加载所有音效资源"""
        #如果音效不存在，进行错误输出
        if not self.sound_dir.exists():
            print(f"音效目录不存在: {self.sound_dir}")
            return

        for name, filename in self.sound_map.items():
            path = self.sound_dir / filename
            if path.exists():
                effect = QSoundEffect()
                effect.setSource(QUrl.fromLocalFile(str(path)))
                effect.setVolume(self.volume)
                self.sounds[name] = effect
            else:
                pass

    def set_volume(self, value_0_to_100):
        #设置全局音量
        self.volume = max(0.0, min(1.0, value_0_to_100 / 100.0))
        for effect in self.sounds.values():
            effect.setVolume(self.volume)

    def play(self, name):
        #播放指定音效，如果文件不存在则回退到 Beep
        # 1. 尝试播放自定义音效
        if name in self.sounds:
            if self.volume > 0.01: # 静音时不播
                # 如果正在播放，停止并重播
                if self.sounds[name].isPlaying():
                    self.sounds[name].stop()
                self.sounds[name].play()
            return

        # 备用方案：如果没有文件，使用 winsound.Beep
        # 和上面类似，只有音量 > 0 时才响
        # 但目前自定义文件运行良好，此部分不会被触发，属于程序改进时期写的防止没有音效的代码
        if self.volume > 0.1:
            try:
                if name == "alarm":
                    winsound.Beep(1000, 800) # 长音
                else:
                    winsound.Beep(800, 150)  # 短音
            except:
                pass

    def stop(self, name):
        # 停止播放
        if name in self.sounds:
            self.sounds[name].stop()

# 创建全局单例，方便其他文件直接 import 使用
SoundMgr = AudioManager()