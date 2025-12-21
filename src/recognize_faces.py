#!/usr/bin/env python3
"""
Reconnaissance faciale en temps réel
EPIC 5, 6, 7 - Version complète avec feedback, logs et robustesse
"""
import cv2
import face_recognition
import pickle
import os
import glob
import json
import logging
from datetime import datetime
from pathlib import Path

# Configuration du logging
def setup_logging():
    """Configure le système de logs"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f"recognition_{datetime.now().strftime('%Y%m%d')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)


class Config:
    """Configuration externalisée"""
    
    def __init__(self):
        self.config_file = Path("config/settings.json")
        self.default_config = {
            "camera": {
                "device_id": 0,
                "width": 640,
                "height": 480
            },
            "recognition": {
                "tolerance": 0.6,
                "process_every_n_frames": 2,
                "model": "hog"  # ou "cnn" pour plus de précision (mais plus lent)
            },
            "display": {
                "show_confidence": True,
                "show_timestamp": True,
                "show_fps": True,
                "debug_mode": False
            },
            "colors": {
                "known": [0, 255, 0],
                "unknown": [0, 0, 255],
                "text": [255, 255, 255]
            }
        }
        
        self.config = self.load_config()
    
    def load_config(self):
        """Charge la configuration depuis le fichier JSON"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    logging.info(f"✅ Configuration chargée depuis {self.config_file}")
                    return config
            except Exception as e:
                logging.warning(f"⚠️  Erreur de lecture config: {e}, utilisation config par défaut")
                return self.default_config
        else:
            # Créer le fichier de config par défaut
            self.save_config(self.default_config)
            return self.default_config
    
    def save_config(self, config):
        """Sauvegarde la configuration"""
        self.config_file.parent.mkdir(exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=4)
        logging.info(f"✅ Configuration sauvegardée dans {self.config_file}")
    
    def get(self, *keys):
        """Récupère une valeur de config"""
        value = self.config
        for key in keys:
            value = value.get(key)
            if value is None:
                return None
        return value


def load_known_faces(logger):
    """Charge tous les visages enregistrés"""
    
    known_faces = []
    known_names = []
    
    face_files = glob.glob("data/faces/*.pkl")
    
    if not face_files:
        logger.warning("⚠️  Aucun visage enregistré trouvé dans data/faces/")
        return [], []
    
    logger.info(f"📂 Chargement de {len(face_files)} fichier(s) de visages...")
    
    for file_path in face_files:
        try:
            with open(file_path, 'rb') as f:
                data = pickle.load(f)
                
                for encoding in data['encodings']:
                    known_faces.append(encoding)
                    known_names.append(data['name'])
                
                logger.info(f"✅ Chargé: {data['name']} ({len(data['encodings'])} encodings)")
        
        except Exception as e:
            logger.error(f"❌ Erreur lors du chargement de {file_path}: {e}")
    
    logger.info(f"📊 Total: {len(known_faces)} encodings pour {len(set(known_names))} personne(s)")
    
    return known_faces, known_names


def log_recognition(logger, name, confidence, timestamp):
    """Log une reconnaissance dans un fichier CSV"""
    log_file = Path("logs/recognitions.csv")
    
    # Créer le fichier avec en-tête si nécessaire
    if not log_file.exists():
        log_file.parent.mkdir(exist_ok=True)
        with open(log_file, 'w') as f:
            f.write("timestamp,name,confidence\n")
    
    # Ajouter l'entrée
    with open(log_file, 'a') as f:
        f.write(f"{timestamp},{name},{confidence:.4f}\n")


class FPSCounter:
    """Compteur de FPS"""
    
    def __init__(self):
        self.fps = 0
        self.frame_count = 0
        self.start_time = datetime.now()
    
    def update(self):
        """Met à jour le compteur FPS"""
        self.frame_count += 1
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        if elapsed > 1.0:
            self.fps = self.frame_count / elapsed
            self.frame_count = 0
            self.start_time = datetime.now()
        
        return self.fps


def recognize_faces():
    """Reconnaissance faciale en temps réel avec feedback avancé"""
    
    # Setup
    logger = setup_logging()
    config = Config()
    fps_counter = FPSCounter()
    
    logger.info("=" * 50)
    logger.info("🎭 DÉMARRAGE DU SYSTÈME DE RECONNAISSANCE FACIALE")
    logger.info("=" * 50)
    
    # Charger les visages connus
    known_face_encodings, known_face_names = load_known_faces(logger)
    
    if not known_face_encodings:
        logger.error("❌ Impossible de démarrer sans visages enregistrés")
        logger.info("💡 Utilisez 'python3 src/register_face.py' pour enregistrer un visage")
        return
    
    # Ouvrir la webcam
    camera_id = config.get("camera", "device_id")
    video_capture = cv2.VideoCapture(camera_id)
    
    if not video_capture.isOpened():
        logger.error(f"❌ Impossible d'ouvrir la webcam {camera_id}")
        return
    
    # Configuration de la webcam
    video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, config.get("camera", "width"))
    video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, config.get("camera", "height"))
    
    logger.info("✅ Webcam ouverte avec succès")
    logger.info("📹 Appuyez sur 'q' pour quitter, 'd' pour toggle debug mode")
    
    # Paramètres
    tolerance = config.get("recognition", "tolerance")
    process_every_n_frames = config.get("recognition", "process_every_n_frames")
    model = config.get("recognition", "model")
    
    # Display settings
    show_confidence = config.get("display", "show_confidence")
    show_timestamp = config.get("display", "show_timestamp")
    show_fps = config.get("display", "show_fps")
    debug_mode = config.get("display", "debug_mode")
    
    # Couleurs
    color_known = tuple(config.get("colors", "known"))
    color_unknown = tuple(config.get("colors", "unknown"))
    color_text = tuple(config.get("colors", "text"))
    
    # Variables pour mémoriser les derniers résultats
    last_face_locations = []
    last_face_data = []  # Liste de dictionnaires avec name, confidence, etc.
    frame_count = 0
    
    try:
        while True:
            ret, frame = video_capture.read()
            
            if not ret:
                logger.error("❌ Erreur de lecture de la frame")
                break
            
            frame_count += 1
            current_fps = fps_counter.update()
            
            # Traiter seulement certaines frames
            if frame_count % process_every_n_frames == 0:
                # Convertir en RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Détecter les visages
                try:
                    face_locations = face_recognition.face_locations(rgb_frame, model=model)
                    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                except Exception as e:
                    logger.error(f"❌ Erreur lors de la détection: {e}")
                    continue
                
                # Réinitialiser les données pour cette frame
                face_data = []
                
                # Pour chaque visage détecté
                for face_encoding in face_encodings:
                    # Comparer avec les visages connus
                    matches = face_recognition.compare_faces(
                        known_face_encodings, 
                        face_encoding, 
                        tolerance=tolerance
                    )
                    name = "Inconnu"
                    confidence = 0.0
                    
                    # Calculer les distances
                    face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                    
                    if True in matches:
                        # Trouver le meilleur match
                        best_match_index = face_distances.argmin()
                        
                        if matches[best_match_index]:
                            name = known_face_names[best_match_index]
                            # Convertir distance en score de confiance (0-1)
                            confidence = 1 - face_distances[best_match_index]
                            
                            timestamp = datetime.now().isoformat()
                            logger.info(f"✅ Reconnu: {name} (confiance: {confidence:.2%})")
                            
                            # Logger la reconnaissance
                            log_recognition(logger, name, confidence, timestamp)
                    
                    face_data.append({
                        'name': name,
                        'confidence': confidence,
                        'distances': face_distances.tolist() if debug_mode else None
                    })
                
                # Mémoriser les résultats
                last_face_locations = face_locations
                last_face_data = face_data
            
            # Dessiner avec les derniers résultats mémorisés
            for (top, right, bottom, left), data in zip(last_face_locations, last_face_data):
                name = data['name']
                confidence = data['confidence']
                
                # Couleur selon reconnaissance
                color = color_known if name != "Inconnu" else color_unknown
                
                # Rectangle autour du visage
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                
                # Préparer le texte
                labels = [name]
                
                if show_confidence and confidence > 0:
                    labels.append(f"{confidence:.1%}")
                
                # Hauteur du rectangle pour le texte
                label_height = 25 * len(labels) + 10
                
                # Fond pour le texte
                cv2.rectangle(frame, (left, bottom - label_height), (right, bottom), color, cv2.FILLED)
                
                # Afficher les labels
                y_offset = bottom - label_height + 20
                for label in labels:
                    cv2.putText(frame, label, (left + 6, y_offset),
                               cv2.FONT_HERSHEY_DUPLEX, 0.5, color_text, 1)
                    y_offset += 20
                
                # Mode debug : afficher toutes les distances
                if debug_mode and data['distances']:
                    y_debug = top - 10
                    for i, dist in enumerate(data['distances'][:3]):  # Top 3
                        debug_text = f"{known_face_names[i]}: {dist:.3f}"
                        cv2.putText(frame, debug_text, (left, y_debug),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)
                        y_debug -= 15
            
            # Overlay d'informations
            info_y = 30
            
            # Nombre de visages
            cv2.putText(frame, f"Visages: {len(last_face_locations)}", 
                       (10, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color_text, 2)
            info_y += 30
            
            # FPS
            if show_fps:
                cv2.putText(frame, f"FPS: {current_fps:.1f}", 
                           (10, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color_text, 2)
                info_y += 30
            
            # Timestamp
            if show_timestamp:
                timestamp_str = datetime.now().strftime("%H:%M:%S")
                cv2.putText(frame, timestamp_str, 
                           (10, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color_text, 2)
            
            # Mode debug indicator
            if debug_mode:
                cv2.putText(frame, "DEBUG MODE", 
                           (frame.shape[1] - 150, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            
            # Afficher la frame
            cv2.imshow('Reconnaissance Faciale', frame)
            
            # Gestion des touches
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                logger.info("👋 Arrêt demandé par l'utilisateur")
                break
            elif key == ord('d'):
                debug_mode = not debug_mode
                logger.info(f"🔧 Mode debug: {'ON' if debug_mode else 'OFF'}")
    
    except KeyboardInterrupt:
        logger.info("👋 Interruption clavier (Ctrl+C)")
    
    except Exception as e:
        logger.error(f"❌ Erreur critique: {e}", exc_info=True)
    
    finally:
        # Libérer les ressources
        video_capture.release()
        cv2.destroyAllWindows()
        logger.info("=" * 50)
        logger.info("🛑 Arrêt du système de reconnaissance")
        logger.info("=" * 50)


if __name__ == "__main__":
    recognize_faces()