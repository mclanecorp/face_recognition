#!/usr/bin/env python3
"""
Enregistrement d'un nouveau visage
EPIC 4 - US 4.1, 4.2, 4.3
"""
import cv2
import face_recognition
import pickle
import os
from datetime import datetime

def capture_face(name):
    """Capture plusieurs images d'un visage pour l'enregistrement"""
    
    # Ouvrir la webcam
    video_capture = cv2.VideoCapture(0)
    video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    if not video_capture.isOpened():
        print("❌ Impossible d'ouvrir la webcam")
        return None
    
    print(f"\n📸 Enregistrement de: {name}")
    print("=" * 50)
    print("Instructions:")
    print("- Positionnez votre visage face à la caméra")
    print("- Appuyez sur ESPACE pour capturer (5 photos nécessaires)")
    print("- Appuyez sur Q pour annuler")
    print("=" * 50)
    
    captured_encodings = []
    capture_count = 0
    total_needed = 5
    
    while capture_count < total_needed:
        ret, frame = video_capture.read()
        
        if not ret:
            print("❌ Erreur de lecture")
            break
        
        # Convertir en RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Détecter les visages
        face_locations = face_recognition.face_locations(rgb_frame)
        
        # Affichage
        display_frame = frame.copy()
        
        if len(face_locations) == 1:
            # Un seul visage détecté - OK
            top, right, bottom, left = face_locations[0]
            cv2.rectangle(display_frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(display_frame, "Visage OK - Appuyez sur ESPACE", (left, top - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        elif len(face_locations) == 0:
            # Aucun visage
            cv2.putText(display_frame, "Aucun visage detecte", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        else:
            # Plusieurs visages
            cv2.putText(display_frame, "Plusieurs visages detectes - Un seul requis", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        
        # Compteur
        cv2.putText(display_frame, f"Photos: {capture_count}/{total_needed}", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        cv2.imshow('Enregistrement de visage', display_frame)
        
        key = cv2.waitKey(1) & 0xFF
        
        # Capturer avec ESPACE
        if key == ord(' '):
            if len(face_locations) == 1:
                # Encoder le visage
                face_encoding = face_recognition.face_encodings(rgb_frame, face_locations)[0]
                captured_encodings.append(face_encoding)
                capture_count += 1
                print(f"✅ Photo {capture_count}/{total_needed} capturée")
            else:
                print("⚠️  Un seul visage doit être visible pour capturer")
        
        # Quitter avec Q
        elif key == ord('q'):
            print("\n❌ Annulation de l'enregistrement")
            video_capture.release()
            cv2.destroyAllWindows()
            return None
    
    video_capture.release()
    cv2.destroyAllWindows()
    
    return captured_encodings


def save_face_data(name, encodings):
    """Sauvegarde les encodings dans un fichier"""
    
    # Créer le dossier si nécessaire
    data_dir = "data/faces"
    os.makedirs(data_dir, exist_ok=True)
    
    # Nom du fichier
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{data_dir}/{name}_{timestamp}.pkl"
    
    # Sauvegarder
    data = {
        'name': name,
        'encodings': encodings,
        'timestamp': timestamp
    }
    
    with open(filename, 'wb') as f:
        pickle.dump(data, f)
    
    print(f"\n✅ Visage enregistré: {filename}")
    print(f"📊 {len(encodings)} encodings sauvegardés")
    
    return filename


def main():
    print("\n" + "=" * 50)
    print("🎭 SYSTÈME D'ENREGISTREMENT DE VISAGE")
    print("=" * 50)
    
    # Demander le nom
    name = input("\n👤 Entrez votre nom: ").strip()
    
    if not name:
        print("❌ Nom invalide")
        return
    
    # Capturer le visage
    encodings = capture_face(name)
    
    if encodings is None:
        print("\n❌ Enregistrement annulé")
        return
    
    # Sauvegarder
    save_face_data(name, encodings)
    
    print("\n✅ Enregistrement terminé avec succès!")
    print(f"Vous pouvez maintenant être reconnu comme: {name}")


if __name__ == "__main__":
    main()