# Drowsyness-detection

This is a Python based project to build to monitor driver drowsiness using real-time eye blink detection. It uses a webcam feed and analyzes facial landmarks to detect eye closure and blink patterns. When signs of drowsiness are detected, it raises an alarm to alert the driver.

# Overview

The system uses `cvzone` and `opencv` to detect facial landmarks and calculate the eye aspect ratio. It tracks blink frequency, eye openness percentage, and provides visual feedback along with an audio alert if the driver shows signs of fatigue.

It includes  visual dashboard that shows the blink count, eye openness, current status (alert, sleepy, drowsy), and a live graph for better real-time monitoring.

# Features

- Real-time face and eye detection using FaceMesh
- Dynamic blink detection and eye openness tracking
- Visual dashboard showing:
  - Eye openness percentage
  - Blink count
  - Driver status
  - Session time left
- Sound alarm that triggers on drowsy or critical blink count
- Auto-reset functionality when alertness improves
- Graphical representation of eye activity with zone indicators

# Configuration

You can modify the detection behavior using the `CONFIG` dictionary at the top of the script:
CONFIG = {
    'DROWSY_BLINK_THRESHOLD': 15,
    'CRITICAL_BLINK_THRESHOLD': 30,
    'EYE_CLOSED_RATIO': 30,
    'MONITORING_TIME': 60,
    'ALARM_COOLDOWN': 10,
    'GRAPH_HISTORY_SIZE': 150,
}
