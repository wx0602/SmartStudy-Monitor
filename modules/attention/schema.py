def make_base_output(score_ema: float) -> dict:
    return{
        "ear": None,
        "blink_state": "no_face",
        "yaw_angle": None,
        "pitch_angle": None,

        "gaze_x": None,
        "gaze_y": None,
        "gaze_off": False,

        "attention_score": int(round(score_ema)),

        "perclos": None,
        "away_ratio": None,
        "down_ratio": None,
        "up_ratio": None,
        "noface_ratio": None,
        "gaze_ratio": None,
        "unstable": None,
    }

