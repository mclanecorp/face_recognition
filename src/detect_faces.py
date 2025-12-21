#!/usr/bin/env python3
"""
Détection de visages en temps réel
EPIC 3 - US 3.1
"""
import cv2
import face_recognition

def main():
    # Ouvrir la webcam
    video_capture = cv2.VideoCapture(0)
    
    
    if not video_capture.isOpened():
        print("❌ Impossible d'ouvrir la webcam")
        return
    
    print("🎥 Webcam ouverte. Appuyez sur 'q' pour quitter.")
    
    while True:
        # Capturer frame par frame
        ret, frame = video_capture.read()
        
        if not ret:
            print("❌ Erreur de lecture de la frame")
            break
        
        # Convertir BGR (OpenCV) vers RGB (face_recognition)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Détecter les visages
        face_locations = face_recognition.face_locations(rgb_frame)
        
        # Dessiner des rectangles autour des visages
        for (top, right, bottom, left) in face_locations:
            # Rectangle vert autour du visage
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            
            # Texte "Visage détecté"
            cv2.putText(frame, "Visage detecte", (left, top - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Afficher le nombre de visages détectés
        cv2.putText(frame, f"Visages: {len(face_locations)}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Afficher la frame
        cv2.imshow('Detection de visages', frame)
        
        # Quitter avec 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Libérer les ressources
    video_capture.release()
    cv2.destroyAllWindows()
    print("👋 Arrêt propre de l'application")

if __name__ == "__main__":
    main()