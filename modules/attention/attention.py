import cv2
import json
import time

from .monitor import AttentionMonitor
from .config import SLEEPY_TIME, POSE_HOLD_TIME, ATTN_BAD_THRESHOLD

def draw_button(frame, rect, text, enabled=True):
    x1, y1, x2, y2 = rect
    bg = (60, 180, 60) if enabled else (120, 120, 120)
    cv2.rectangle(frame, (x1, y1), (x2, y2), bg, -1)
    cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 255), 2)
    (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
    tx = x1 + (x2 - x1 - tw) // 2
    ty = y1 + (y2 - y1 + th) // 2
    cv2.putText(frame, text, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

def point_in_rect(x, y, rect):
    x1, y1, x2, y2 = rect
    return (x1 <= x <= x2) and (y1 <= y <= y2)

def run_webcam_demo():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("无法打开摄像头，请检查权限/摄像头占用。")

    fps = 30
    baseline_frames = 100

    WAIT_START = "WAIT_START"
    CALIBRATING = "CALIBRATING"
    RUNNING = "RUNNING"

    state = WAIT_START
    monitor = None

    # JSONL 保存
    output_file = "attention_output.jsonl"
    save_interval = 0.5  
    last_save_time = 0.0

    # 帧编号
    frame_id = 0

    # START按钮
    start_btn = (20, 20, 160, 70)

    # 镜像
    mirror = False

    # 强制显示 yaw/pitch=0
    force_zero_frames = 0

    def on_mouse(event, x, y, flags, param):
        nonlocal state, monitor, force_zero_frames
        if event != cv2.EVENT_LBUTTONDOWN:
            return
        if state == WAIT_START and point_in_rect(x, y, start_btn):
            monitor = AttentionMonitor(fps=fps, baseline_frames=baseline_frames)
            state = CALIBRATING
            force_zero_frames = 0

    win_name = "Attention Monitor (B)"
    cv2.namedWindow(win_name)
    cv2.setMouseCallback(win_name, on_mouse)

    print("已进入界面：点击 START 按钮开始校准。ESC 退出。按 m 切换镜像。运行中按 r 重新校准。")

    while True:
        ret, raw_frame = cap.read()
        if not ret:
            continue

        frame_id += 1  

        disp_frame = cv2.flip(raw_frame, 1) if mirror else raw_frame

        key = cv2.waitKey(1) & 0xFF
        if key == 27:  
            break
        if key == ord('m'):
            mirror = not mirror
        if key == ord('r'):
            monitor = AttentionMonitor(fps=fps, baseline_frames=baseline_frames)
            state = CALIBRATING
            force_zero_frames = 0

        # 等待开始状态
        if state == WAIT_START:
            draw_button(disp_frame, start_btn, "START", enabled=True)
            cv2.putText(disp_frame, "Click START to calibrate",
                        (20, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(disp_frame, "ESC: quit   m: mirror toggle",
                        (20, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)
            cv2.putText(disp_frame, f"Mirror: {'ON' if mirror else 'OFF'}",
                        (20, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)
            cv2.imshow(win_name, disp_frame)
            continue

        # 校准状态
        if state == CALIBRATING:
            assert monitor is not None
            ok = monitor.calibrate(raw_frame)

            ear_n = len(monitor.calibrator.baseline_ears)
            pose_n = len(monitor.calibrator.pose_yaws)
            need = int(monitor.calibrator.baseline_frames)

            cv2.putText(disp_frame, "Calibrating... Keep face/eyes forward",
                        (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(disp_frame, f"EAR baseline frames: {ear_n}/{need}",
                        (20, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2)
            cv2.putText(disp_frame, f"Pose baseline frames: {pose_n}/{need}",
                        (20, 105), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2)

            cv2.putText(disp_frame, f"Mirror: {'ON' if mirror else 'OFF'}   (press m)",
                        (20, 135), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (220, 220, 220), 2)

            cv2.imshow(win_name, disp_frame)

            if ok:
                print(f"EAR 基线 = {monitor.EAR_BASELINE:.3f}")
                print(f"Pose 基线 yaw0={monitor.yaw0:.2f}, pitch0={monitor.pitch0:.2f}")

                monitor.reset_runtime_state(seed_zero=False)

                for _ in range(max(1, monitor.win_len)):
                    monitor.yaw_window.append(0.0)
                    monitor.pitch_window.append(0.0)

                force_zero_frames = max(8, monitor.win_len)

                print("校准完成，进入检测：显示的 yaw/pitch 会从 0 开始。按 r 可重新校准，ESC 退出。")
                state = RUNNING

            continue

        # 运行状态
        if state == RUNNING:
            assert monitor is not None
            json_data = monitor.process(raw_frame)
            data = json.loads(json_data)

            # 每 0.5 秒保存一次
            now = time.time()
            if now - last_save_time >= save_interval:
                data["ts"] = now
                data["frame_id"] = frame_id
                data["has_person"] = (data.get("blink_state") != "no_face")

                json_line = json.dumps(data, ensure_ascii=False)

                with open(output_file, "a", encoding="utf-8") as f:
                    f.write(json_line + "\n")

                last_save_time = now

            x, y0, dy = 10, 30, 25

            # EAR值显示
            ear_ratio = data.get("ear")
            ear_state = data.get("blink_state", "no_face")
            ear_bad = (ear_state == "closed" or ear_state == "no_face")
            ear_color = (0, 0, 255) if ear_bad else (0, 255, 0)
            cv2.putText(disp_frame, f"EAR(ratio): {ear_ratio}", (x, y0 + 0 * dy),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, ear_color, 2)

            # 眨眼状态显示
            blink = data.get("blink_state", "no_face")
            blink_bad = (blink == "closed" or blink == "no_face")
            blink_color = (0, 0, 255) if blink_bad else (0, 255, 0)
            cv2.putText(disp_frame, f"Blink: {blink}", (x, y0 + 1 * dy),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, blink_color, 2)

            # 疲劳状态显示
            drowsy = (monitor.eye_closed_time >= SLEEPY_TIME)
            drowsy_color = (0, 0, 255) if drowsy else (0, 255, 0)
            cv2.putText(disp_frame, f"Drowsy: {drowsy} ({monitor.eye_closed_time:.2f}s)", (x, y0 + 2 * dy),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, drowsy_color, 2)

            # Yaw/Pitch 显示
            if force_zero_frames > 0:
                yaw_show = 0.0
                pitch_show = 0.0
                force_zero_frames -= 1
                look_away = False
                look_down = False
                look_up = False
            else:
                yaw_show = data.get("yaw_angle")
                pitch_show = data.get("pitch_angle")
                look_away = (monitor.yaw_off_time >= POSE_HOLD_TIME)
                look_down = (monitor.pitch_down_time >= POSE_HOLD_TIME)
                look_up = (monitor.pitch_up_time >= POSE_HOLD_TIME)

            yaw_color = (0, 0, 255) if look_away else (0, 255, 0)
            cv2.putText(disp_frame, f"Yaw: {yaw_show}  away:{look_away}", (x, y0 + 3 * dy),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, yaw_color, 2)

            pitch_bad = look_down or look_up
            pitch_color = (0, 0, 255) if pitch_bad else (0, 255, 0)
            cv2.putText(disp_frame, f"Pitch: {pitch_show}  down:{look_down} up:{look_up}", (x, y0 + 4 * dy),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, pitch_color, 2)

            # 视线显示
            gx = data.get("gaze_x")
            gy = data.get("gaze_y")
            gaze_off = data.get("gaze_off", False)
            gaze_color = (0, 0, 255) if gaze_off else (0, 255, 0)
            cv2.putText(disp_frame, f"Gaze: off:{gaze_off}  x:{gx} y:{gy}", (x, y0 + 5 * dy),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, gaze_color, 2)

            # 注意力分数显示
            attn = data.get("attention_score", 0)
            attn_bad = (float(attn) < ATTN_BAD_THRESHOLD)
            attn_color = (0, 0, 255) if attn_bad else (0, 255, 0)
            cv2.putText(disp_frame, f"Attention: {attn} (thr {ATTN_BAD_THRESHOLD})", (x, y0 + 6 * dy),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, attn_color, 2)

            # 提示
            cv2.putText(disp_frame, f"r: recalibrate   m: mirror toggle({ 'ON' if mirror else 'OFF' })   ESC: quit",
                        (10, disp_frame.shape[0] - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (220, 220, 220), 2)

            cv2.imshow(win_name, disp_frame)
            continue

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run_webcam_demo()