"""Task map: KFall task IDs -> project labels.

KFall: 36 tasks. IDs 1-19 and 35-36 are ADLs (no fall), IDs 20-34 are the
15 scripted falls F01-F15 (label xlsx: "F01 (20)" = fall F01 is task 20).

Project mapping (RQ1 = IMU-only baseline):
  positive (1)  -> pre-impact fall segment, onset..impact frames (from label xlsx)
  negative (0)  -> everything in ADL trials, + pre-onset part of fall trials
  ignore  (-1)  -> post-impact part of fall trials (person already on the floor)

KFall is waist-worn IMU, NOT a cane. It is a stand-in for the IMU half of the
pipeline until cane data exists. Falls here are real falls, not recovered near-misses.
"""

FALL_TASKS = tuple(range(20, 35))          # F01..F15
ADL_TASKS = tuple(range(1, 20)) + (35, 36)

# Closest KFall analogue of a near-miss. F11/F13/F14 = trip/slip while walking.
# Use these for the "trip/slip only" sub-analysis.
TRIP_SLIP_TASKS = (30, 31, 32, 33, 34)

# ADLs that look like a fall to an IMU-only detector (hard negatives).
# Task 35/36 are the high-impact ADLs in KFall (peak accel > 2 g in the sample file).
HARD_NEGATIVE_TASKS = (35, 36)


def task_kind(task_id: int) -> str:
    if task_id in FALL_TASKS:
        return "fall"
    if task_id in ADL_TASKS:
        return "adl"
    raise ValueError(f"unknown KFall task id {task_id}")


def fall_code(task_id: int) -> str:
    """20 -> 'F01'."""
    return f"F{task_id - 19:02d}"
