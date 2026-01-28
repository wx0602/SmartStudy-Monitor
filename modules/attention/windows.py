import numpy as np

def median_deque(dq):
    return float(np.median(dq)) if len(dq) else None

def std_deque(dq):
    return float(np.std(dq)) if len(dq) else 0.0