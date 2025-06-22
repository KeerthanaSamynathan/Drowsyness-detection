import cv2
import cvzone
import time
import pygame
import numpy as np
from cvzone.FaceMeshModule import FaceMeshDetector

# Configuration - Easy to adjust settings
CONFIG = {
    'DROWSY_BLINK_THRESHOLD': 15,      # Number of blinks before drowsy alert
    'CRITICAL_BLINK_THRESHOLD': 30,    # Number of blinks before critical alert
    'EYE_CLOSED_RATIO': 30,            # Ratio below which eye is considered closed
    'MONITORING_TIME': 60,             # Monitoring duration in seconds
    'ALARM_COOLDOWN': 10,              # Seconds between alarm repeats
    'GRAPH_HISTORY_SIZE': 150,         # Number of data points to show in graph
}

# Initialize pygame mixer
pygame.mixer.init()
try:
    pygame.mixer.music.load('mixkit-retro-game-emergency-alarm-1000.wav')
    MUSIC_LOADED = True
except:
    print(" Warning: Audio file not found. Continuing without sound.")
    MUSIC_LOADED = False

class AlarmManager:
    def __init__(self):
        self.last_alarm_time = 0
        self.alarm_active = False
        
    def play_alarm(self):
        current_time = time.time()
        if MUSIC_LOADED and (current_time - self.last_alarm_time) > CONFIG['ALARM_COOLDOWN']:
            pygame.mixer.music.stop()  # Stop any previous music
            pygame.mixer.music.play(-1)  # Loop indefinitely
            self.last_alarm_time = current_time
            self.alarm_active = True
            return True
        return False
    
    def stop_alarm(self):
        if MUSIC_LOADED and self.alarm_active:
            pygame.mixer.music.stop()
            self.alarm_active = False

def create_enhanced_graph(width, height, eye_openness_history, current_openness, blink_count, status):
    """Create an enhanced graph with more information"""
    graph = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Add gradient background
    for i in range(height):
        intensity = int(20 + (i / height) * 15)
        graph[i, :] = [intensity, intensity//2, intensity//3]
    
    # Add grid lines with different colors
    grid_color_major = (60, 60, 60)
    grid_color_minor = (30, 30, 30)
    
    # Horizontal grid lines
    for i in range(0, height, 20):
        color = grid_color_major if i % 40 == 0 else grid_color_minor
        cv2.line(graph, (0, i), (width, i), color, 1)
    
    # Vertical grid lines
    for i in range(0, width, 30):
        color = grid_color_major if i % 60 == 0 else grid_color_minor
        cv2.line(graph, (i, 0), (i, height), color, 1)
    
    # Add zone indicators
    alert_zone = int(height * 0.3)  # Top 30% is alert zone
    drowsy_zone = int(height * 0.7)  # Bottom 30% is drowsy zone
    
    # Color zones
    cv2.rectangle(graph, (0, 0), (width, alert_zone), (0, 40, 0), -1)  # Green zone
    cv2.rectangle(graph, (0, drowsy_zone), (width, height), (0, 0, 40), -1)  # Red zone
    
    # Add labels with better positioning
    cv2.putText(graph, "ALERT ZONE", (width//2-50, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    cv2.putText(graph, "DROWSY ZONE", (width//2-60, height-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    
    # Draw threshold lines
    cv2.line(graph, (0, alert_zone), (width, alert_zone), (0, 255, 0), 2)
    cv2.line(graph, (0, drowsy_zone), (width, drowsy_zone), (0, 0, 255), 2)
    
    # Draw the eye openness line with anti-aliasing effect
    if len(eye_openness_history) > 1:
        points = []
        for i, openness in enumerate(eye_openness_history):
            x = int((i / len(eye_openness_history)) * width)
            y = int(height - (openness / 100) * height)
            points.append((x, y))
        
        # Draw shadow line first
        for i in range(len(points) - 1):
            cv2.line(graph, (points[i][0]+2, points[i][1]+2), 
                    (points[i + 1][0]+2, points[i + 1][1]+2), (20, 20, 20), 4)
        
        # Draw main line with varying thickness based on alertness
        for i in range(len(points) - 1):
            openness = eye_openness_history[i]
            if openness > 70:
                color = (0, 255, 0)
                thickness = 3
            elif openness > 40:
                color = (0, 255, 255)
                thickness = 4
            else:
                color = (0, 0, 255)
                thickness = 5
            
            cv2.line(graph, points[i], points[i + 1], color, thickness)
    
    # Enhanced status indicator
    status_y = int(height - (current_openness / 100) * height)
    
    # Pulsing effect for current position
    pulse_size = int(8 + 4 * abs(np.sin(time.time() * 3)))
    cv2.circle(graph, (width - 30, status_y), pulse_size, (255, 255, 255), -1)
    
    # Status color ring
    ring_color = (0, 255, 0) if current_openness > 70 else (0, 255, 255) if current_openness > 40 else (0, 0, 255)
    cv2.circle(graph, (width - 30, status_y), pulse_size + 3, ring_color, 2)
    
    # Add statistics panel
    stats_bg = np.zeros((100, 200, 3), dtype=np.uint8)
    stats_bg[:] = (40, 40, 40)
    
    cv2.putText(stats_bg, f"Blinks: {blink_count}", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.putText(stats_bg, f"Openness: {int(current_openness)}%", (10, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.putText(stats_bg, f"Status: {status}", (10, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.5, ring_color, 1)
    cv2.putText(stats_bg, f"Threshold: {CONFIG['DROWSY_BLINK_THRESHOLD']}", (10, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
    
    # Overlay stats on graph
    graph[10:110, 10:210] = cv2.addWeighted(graph[10:110, 10:210], 0.3, stats_bg, 0.7, 0)
    
    return graph

def main():
    alarm_manager = AlarmManager()
    
    while True:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print(" Error: Could not open camera")
            break

        # Create enhanced window
        cv2.namedWindow("Advanced Drowsiness Monitor", cv2.WINDOW_NORMAL)
        cv2.setWindowProperty("Advanced Drowsiness Monitor", cv2.WND_PROP_TOPMOST, 1)
        cv2.resizeWindow("Advanced Drowsiness Monitor", 1400, 400)

        start_time = time.time()
        detector = FaceMeshDetector(maxFaces=1)

        # Enhanced tracking variables
        idList = [22, 23, 24, 26, 110, 157, 158, 159, 160, 161, 130, 243]
        ratiolist = []
        eye_openness_history = []
        blink_counter = 0
        counter = 0
        color = (255, 0, 255)
        flag = True
        drowsy_warning_given = False
        last_blink_time = time.time()
        consecutive_closed_frames = 0

        print(f" Monitoring started - Drowsy alert at {CONFIG['DROWSY_BLINK_THRESHOLD']} blinks, Critical at {CONFIG['CRITICAL_BLINK_THRESHOLD']} blinks")

        while True:
            success, img = cap.read()
            if not success:
                print(" Failed to read from camera")
                break

            img, faces = detector.findFaceMesh(img, draw=False)
            current_time = time.time()

            if faces:
                face = faces[0]
                
                # Draw landmark points with different colors
                for i, id in enumerate(idList):
                    point_color = (0, 255, 255) if i < 6 else (255, 0, 255)
                    cv2.circle(img, face[id], 3, point_color, cv2.FILLED)

                # Eye measurements
                leftUp = face[159]
                leftDown = face[23]
                leftLeft = face[130]
                leftRight = face[243]

                lenV, _ = detector.findDistance(leftUp, leftDown)
                lenH, _ = detector.findDistance(leftLeft, leftRight)

                # Enhanced eye lines
                cv2.line(img, leftUp, leftDown, (0, 255, 0), 2)
                cv2.line(img, leftLeft, leftRight, (0, 255, 0), 2)

                # Calculate ratios
                ratio = int((lenV / lenH) * 100)
                ratiolist.append(ratio)
                if len(ratiolist) > 5:  # Increased smoothing
                    ratiolist.pop(0)
                ratioAvg = sum(ratiolist) / len(ratiolist)
                
                # Enhanced eye openness calculation
                if ratioAvg < 18:
                    eye_openness = 0
                    consecutive_closed_frames += 1
                elif ratioAvg > 50:
                    eye_openness = 100
                    consecutive_closed_frames = 0
                else:
                    eye_openness = int(((ratioAvg - 18) / (50 - 18)) * 100)
                    consecutive_closed_frames = 0
                
                # Store history
                eye_openness_history.append(eye_openness)
                if len(eye_openness_history) > CONFIG['GRAPH_HISTORY_SIZE']:
                    eye_openness_history.pop(0)

                # Enhanced blink detection
                if ratioAvg < CONFIG['EYE_CLOSED_RATIO'] and counter == 0:
                    blink_counter += 1
                    last_blink_time = current_time
                    color = (0, 255, 0)
                    counter = 1
                    print(f"Blink detected #{blink_counter} (ratio: {ratioAvg:.1f})")

                if counter != 0:
                    counter += 1
                    if counter > 15:  # Increased debounce time
                        color = (255, 0, 255)
                        counter = 0

                # Enhanced alerting system
                if blink_counter >= CONFIG['DROWSY_BLINK_THRESHOLD'] and not drowsy_warning_given:
                    print(f" DROWSY ALERT! {blink_counter} blinks detected")
                    alarm_manager.play_alarm()
                    drowsy_warning_given = True
                    
                if blink_counter >= CONFIG['CRITICAL_BLINK_THRESHOLD']:
                    print(f" CRITICAL! {blink_counter} blinks - Taking immediate action")
                    alarm_manager.play_alarm()
                    flag = False
                    break

                # Auto-reset if user becomes alert again
                if drowsy_warning_given and eye_openness > 80 and (current_time - last_blink_time) > 5:
                    print(" User appears alert again - Stopping alarm")
                    alarm_manager.stop_alarm()

                # Determine status
                if consecutive_closed_frames > 30:  # Eyes closed for too long
                    status = "SLEEPING"
                    status_color = (0, 0, 255)
                elif blink_counter >= CONFIG['DROWSY_BLINK_THRESHOLD']:
                    status = "DROWSY"
                    status_color = (0, 0, 255)
                elif eye_openness < 40:
                    status = "SLEEPY"
                    status_color = (0, 255, 255)
                else:
                    status = "ALERT"
                    status_color = (0, 255, 0)

                # Enhanced display
                cvzone.putTextRect(img, f'Blinks: {blink_counter}/{CONFIG["DROWSY_BLINK_THRESHOLD"]}', (50, 60), colorR=color, scale=1.2)
                cvzone.putTextRect(img, f'Eye Openness: {int(eye_openness)}%', (50, 100), colorR=status_color, scale=1.0)
                cvzone.putTextRect(img, f'Status: {status}', (50, 140), colorR=status_color, scale=1.2)
                cvzone.putTextRect(img, f'Ratio: {ratioAvg:.1f}', (50, 180), colorR=(255, 255, 255), scale=0.8)
                
                # Time remaining
                time_remaining = int(CONFIG['MONITORING_TIME'] - (current_time - start_time))
                cvzone.putTextRect(img, f'Time: {time_remaining}s', (50, 220), colorR=(200, 200, 200), scale=0.8)

                # Create enhanced graph
                imgPlot = create_enhanced_graph(700, 400, eye_openness_history, eye_openness, blink_counter, status)
                
                # Resize and combine
                img = cv2.resize(img, (700, 400))
                imgStack = cvzone.stackImages([img, imgPlot], cols=2, scale=1)
                
            else:
                # No face detected
                img = cv2.resize(img, (700, 400))
                cvzone.putTextRect(img, 'No Face Detected', (250, 200), colorR=(0, 0, 255), scale=2)
                empty_graph = create_enhanced_graph(700, 400, [], 0, blink_counter, "NO FACE")
                imgStack = cvzone.stackImages([img, empty_graph], cols=2, scale=1)

            # Display
            cv2.imshow("Advanced Drowsiness Monitor", imgStack)

            # Exit conditions
            if (current_time - start_time) > CONFIG['MONITORING_TIME']:
                print(f" Monitoring session completed ({CONFIG['MONITORING_TIME']}s)")
                break
                
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print(" Exiting by user request")
                break
            elif key == ord('r'):  # Reset counter
                blink_counter = 0
                drowsy_warning_given = False
                alarm_manager.stop_alarm()
                print(" Counters reset")
            elif key == ord('s'):  # Stop alarm
                alarm_manager.stop_alarm()
                print("Alarm stopped")

        # Session summary
        session_duration = current_time - start_time
        if blink_counter <= 5:
            print(f' Excellent! Only {blink_counter} blinks in {session_duration:.1f}s - You stayed alert!')
        elif blink_counter <= CONFIG['DROWSY_BLINK_THRESHOLD']:
            print(f'In this session  {blink_counter} blinks detected - Stay hydrated!')
        else:
            print(f' High drowsiness detected: {blink_counter} blinks - Consider taking a break!')

        alarm_manager.stop_alarm()
        cap.release()
        cv2.destroyAllWindows()
        
        print("Press Enter to start new session, or Ctrl+C to exit...")
        try:
            input()
        except KeyboardInterrupt:
            break
if __name__ == "__main__":
    main()