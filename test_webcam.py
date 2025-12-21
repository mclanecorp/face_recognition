# test_webcam.py
import cv2
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
if ret:
    cv2.imwrite('test_capture.jpg', frame)
    print("✅ Webcam OK, image sauvegardée")
else:
    print("❌ Webcam non accessible")
cap.release()