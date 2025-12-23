#!/usr/bin/env python3
"""
Interface Web Flask pour la reconnaissance faciale
EPIC 10 - Interface web avec notifications Discord, downscale intelligent et FPS
"""
from flask import Flask, render_template, Response, jsonify, request
import cv2
import face_recognition
import pickle
import glob
import json
from datetime import datetime
from pathlib import Path
import threading
import logging
import sys

# Importer le module de notifications
sys.path.append('../..')
from src.notifications import NotificationManager


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


app = Flask(__name__)

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Variables globales
camera = None
camera_lock = threading.Lock()
known_face_encodings = []
known_face_names = []
recognition_active = False
last_recognition = {"name": None, "confidence": 0, "timestamp": None}
notification_manager = None


class Config:
    """Configuration externalisée"""
    
    def __init__(self):
        self.config_file = Path("../../config/settings.json")
        self.config = self.load_config()
    
    def load_config(self):
        """Charge la configuration depuis le fichier JSON"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    logger.info(f"✅ Configuration chargée depuis {self.config_file}")
                    return config
            except Exception as e:
                logger.warning(f"⚠️  Erreur de lecture config: {e}")
                return {}
        return {}
    
    def get(self, *keys):
        """Récupère une valeur de config"""
        value = self.config
        for key in keys:
            value = value.get(key)
            if value is None:
                return None
        return value


def init_notifications():
    """Initialise le gestionnaire de notifications"""
    global notification_manager
    config_obj = Config()
    notification_manager = NotificationManager(config_obj)
    logger.info("📢 Gestionnaire de notifications initialisé")


def load_known_faces():
    """Charge tous les visages enregistrés"""
    global known_face_encodings, known_face_names
    
    known_face_encodings = []
    known_face_names = []
    
    face_files = glob.glob("../../data/faces/*.pkl")
    
    if not face_files:
        logger.warning("⚠️  Aucun visage enregistré trouvé")
        return
    
    logger.info(f"📂 Chargement de {len(face_files)} fichier(s)...")
    
    for file_path in face_files:
        try:
            with open(file_path, 'rb') as f:
                data = pickle.load(f)
                for encoding in data['encodings']:
                    known_face_encodings.append(encoding)
                    known_face_names.append(data['name'])
                logger.info(f"✅ Chargé: {data['name']}")
        except Exception as e:
            logger.error(f"❌ Erreur: {e}")
    
    logger.info(f"📊 Total: {len(known_face_encodings)} encodings")


def get_camera():
    """Récupère ou initialise la caméra"""
    global camera
    
    with camera_lock:
        if camera is None or not camera.isOpened():
            camera = cv2.VideoCapture(0)
            camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            logger.info("📹 Webcam initialisée")
    
    return camera


def detect_faces_optimized(frame):
    """
    Détection optimisée avec downscaling intelligent
    - Détecte sur une image réduite (2x plus rapide)
    - Encode sur l'image originale (précision maximale)
    """
    # Réduire la taille pour la détection (gain de performance ~60%)
    small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
    rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
    
    # Détecter sur la petite image
    face_locations_small = face_recognition.face_locations(rgb_small, model="hog")
    
    # Si aucun visage détecté, retourner vide
    if not face_locations_small:
        return [], []
    
    # Scale up les coordonnées pour l'image originale (x2)
    face_locations = [
        (top * 2, right * 2, bottom * 2, left * 2)
        for (top, right, bottom, left) in face_locations_small
    ]
    
    # Encoder sur l'image ORIGINALE pour garder la précision
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
    
    return face_locations, face_encodings


def generate_frames():
    """Génère les frames pour le streaming vidéo"""
    global recognition_active, last_recognition
    
    frame_count = 0
    process_every_n_frames = 3
    
    # Variables pour mémoriser les derniers résultats
    last_face_locations = []
    last_face_data = []
    
    # Compteur FPS
    fps_counter = FPSCounter()
    
    while True:
        camera = get_camera()
        
        success, frame = camera.read()
        if not success:
            logger.error("❌ Erreur de lecture frame")
            break
        
        frame_count += 1
        
        # Mettre à jour FPS
        current_fps = fps_counter.update()
        
        # Liste des personnes détectées dans cette frame
        detected_people = []
        
        # Reconnaissance uniquement si activée
        if recognition_active and frame_count % process_every_n_frames == 0:
            try:
                # UTILISER LA DÉTECTION OPTIMISÉE
                face_locations, face_encodings = detect_faces_optimized(frame)
                
                # Réinitialiser les données
                face_data = []
                
                for face_encoding in face_encodings:
                    matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.6)
                    name = "Inconnu"
                    confidence = 0.0
                    
                    if True in matches:
                        face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                        best_match_index = face_distances.argmin()
                        
                        if matches[best_match_index]:
                            name = known_face_names[best_match_index]
                            confidence = 1 - face_distances[best_match_index]
                            
                            # Mettre à jour la dernière reconnaissance
                            last_recognition = {
                                "name": name,
                                "confidence": float(confidence),
                                "timestamp": datetime.now().isoformat()
                            }
                            
                            logger.info(f"✅ Reconnu: {name} ({confidence:.2%})")
                            
                            # Ajouter à la liste des personnes détectées
                            detected_people.append((name, confidence, frame.copy()))
                    
                    face_data.append({
                        'name': name,
                        'confidence': confidence
                    })
                
                # Mémoriser les résultats
                last_face_locations = face_locations
                last_face_data = face_data
                
                # Traiter les événements de présence (arrivée/départ)
                if notification_manager:
                    events = notification_manager.update_presence(detected_people)
                    notification_manager.process_events(events)
            
            except Exception as e:
                logger.error(f"❌ Erreur reconnaissance: {e}")
        
        # Si reconnaissance inactive, mettre à jour avec liste vide (pour détecter les départs)
        elif recognition_active and notification_manager:
            events = notification_manager.update_presence([])
            notification_manager.process_events(events)
        
        # Dessiner avec les derniers résultats mémorisés
        for (top, right, bottom, left), data in zip(last_face_locations, last_face_data):
            name = data['name']
            confidence = data['confidence']
            color = (0, 255, 0) if name != "Inconnu" else (0, 0, 255)
            
            # Rectangle
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
            
            # Label
            label = f"{name} ({confidence:.1%})" if confidence > 0 else name
            cv2.putText(frame, label, (left + 6, bottom - 6),
                       cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)
        
        # Overlay d'informations
        info_y = 30
        
        # Timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        cv2.putText(frame, timestamp, (10, info_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        info_y += 30
        
        # Nombre de visages
        cv2.putText(frame, f"Visages: {len(last_face_locations)}", (10, info_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        info_y += 30
        
        # FPS
        cv2.putText(frame, f"FPS: {current_fps:.1f}", (10, info_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Indicateur de reconnaissance active (coin supérieur droit)
        if recognition_active:
            cv2.circle(frame, (frame.shape[1] - 30, 30), 10, (0, 255, 0), -1)
        
        # Encoder la frame en JPEG
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/')
def index():
    """Page d'accueil"""
    return render_template('index.html')


@app.route('/video_feed')
def video_feed():
    """Route pour le streaming vidéo"""
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/api/toggle_recognition', methods=['POST'])
def toggle_recognition():
    """Active/désactive la reconnaissance"""
    global recognition_active
    
    recognition_active = not recognition_active
    status = "activée" if recognition_active else "désactivée"
    logger.info(f"🔄 Reconnaissance {status}")
    
    return jsonify({
        "active": recognition_active,
        "message": f"Reconnaissance {status}"
    })


@app.route('/api/status')
def status():
    """Retourne le statut actuel"""
    return jsonify({
        "recognition_active": recognition_active,
        "known_faces_count": len(set(known_face_names)),
        "last_recognition": last_recognition
    })


@app.route('/api/reload_faces', methods=['POST'])
def reload_faces():
    """Recharge les visages enregistrés"""
    load_known_faces()
    return jsonify({
        "success": True,
        "count": len(set(known_face_names)),
        "message": f"{len(set(known_face_names))} personne(s) chargée(s)"
    })


@app.route('/api/logs')
def get_logs():
    """Récupère les derniers logs de reconnaissance"""
    try:
        log_file = Path("../../logs/recognitions.csv")
        if log_file.exists():
            with open(log_file, 'r') as f:
                lines = f.readlines()[-20:]  # 20 dernières lignes
            return jsonify({"logs": lines})
        return jsonify({"logs": []})
    except Exception as e:
        return jsonify({"error": str(e)})


# Variables globales pour l'enregistrement
registration_mode = False
registration_name = ""
registration_encodings = []
registration_count = 0
registration_total = 5


@app.route('/register')
def register_page():
    """Page d'enregistrement de nouveau visage"""
    return render_template('register.html')


@app.route('/api/start_registration', methods=['POST'])
def start_registration():
    """Démarre le processus d'enregistrement"""
    global registration_mode, registration_name, registration_encodings, registration_count
    
    data = request.json
    name = data.get('name', '').strip()
    
    if not name:
        return jsonify({"success": False, "message": "Nom invalide"}), 400
    
    registration_mode = True
    registration_name = name
    registration_encodings = []
    registration_count = 0
    
    logger.info(f"📸 Démarrage enregistrement pour: {name}")
    
    return jsonify({
        "success": True,
        "message": f"Enregistrement de {name} démarré",
        "total_needed": registration_total
    })


@app.route('/api/capture_photo', methods=['POST'])
def capture_photo():
    """Capture une photo pour l'enregistrement"""
    global registration_count, registration_encodings
    
    if not registration_mode:
        return jsonify({"success": False, "message": "Mode enregistrement non actif"}), 400
    
    return jsonify({
        "success": True,
        "count": registration_count,
        "total": registration_total,
        "remaining": registration_total - registration_count
    })


@app.route('/api/cancel_registration', methods=['POST'])
def cancel_registration():
    """Annule l'enregistrement en cours"""
    global registration_mode, registration_name, registration_encodings, registration_count
    
    registration_mode = False
    registration_name = ""
    registration_encodings = []
    registration_count = 0
    
    logger.info("❌ Enregistrement annulé")
    
    return jsonify({"success": True, "message": "Enregistrement annulé"})


@app.route('/api/save_registration', methods=['POST'])
def save_registration():
    """Sauvegarde le visage enregistré"""
    global registration_mode, registration_name, registration_encodings, registration_count
    
    if not registration_mode or registration_count < registration_total:
        return jsonify({
            "success": False, 
            "message": f"Enregistrement incomplet ({registration_count}/{registration_total})"
        }), 400
    
    try:
        # Créer le dossier si nécessaire
        data_dir = Path("../../data/faces")
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Nom du fichier
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = data_dir / f"{registration_name}_{timestamp}.pkl"
        
        # Sauvegarder
        data = {
            'name': registration_name,
            'encodings': registration_encodings,
            'timestamp': timestamp
        }
        
        with open(filename, 'wb') as f:
            pickle.dump(data, f)
        
        logger.info(f"✅ Visage sauvegardé: {filename}")
        
        # Notification d'enregistrement
        if notification_manager:
            notification_manager.send_new_registration(registration_name)
        
        # Recharger les visages connus
        load_known_faces()
        
        # Réinitialiser
        registration_mode = False
        temp_name = registration_name
        registration_name = ""
        registration_encodings = []
        registration_count = 0
        
        return jsonify({
            "success": True,
            "message": f"Visage de {temp_name} enregistré avec succès !",
            "filename": str(filename)
        })
    
    except Exception as e:
        logger.error(f"❌ Erreur sauvegarde: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/registration_feed')
def registration_feed():
    """Flux vidéo pour l'enregistrement"""
    return Response(generate_frames_registration(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


def generate_frames_registration():
    """Génère les frames pour l'enregistrement"""
    global registration_count, registration_encodings
    
    # Compteur FPS
    fps_counter = FPSCounter()
    
    while True:
        camera = get_camera()
        
        success, frame = camera.read()
        if not success:
            break
        
        # Mettre à jour FPS
        current_fps = fps_counter.update()
        
        if registration_mode:
            try:
                # UTILISER LA DÉTECTION OPTIMISÉE
                face_locations, _ = detect_faces_optimized(frame)
                
                if len(face_locations) == 1:
                    # Un seul visage - OK
                    top, right, bottom, left = face_locations[0]
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                    cv2.putText(frame, "Visage OK - Capture auto en cours", (left, top - 10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
                elif len(face_locations) == 0:
                    # Aucun visage
                    cv2.putText(frame, "Aucun visage detecte", (10, 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                else:
                    # Plusieurs visages
                    cv2.putText(frame, "Plusieurs visages - Un seul requis", (10, 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                
            except Exception as e:
                logger.error(f"Erreur détection: {e}")
        
        # Overlay d'informations
        info_y = 60
        
        # Compteur
        cv2.putText(frame, f"Photos: {registration_count}/{registration_total}", (10, info_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        info_y += 30
        
        # FPS
        cv2.putText(frame, f"FPS: {current_fps:.1f}", (10, info_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Encoder
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/api/auto_capture', methods=['POST'])
def auto_capture():
    """Capture automatique d'une photo"""
    global registration_count, registration_encodings
    
    if not registration_mode:
        return jsonify({"success": False, "message": "Mode non actif"}), 400
    
    if registration_count >= registration_total:
        return jsonify({"success": False, "message": "Toutes les photos capturées"}), 400
    
    camera = get_camera()
    success, frame = camera.read()
    
    if not success:
        return jsonify({"success": False, "message": "Erreur lecture caméra"}), 500
    
    # UTILISER LA DÉTECTION OPTIMISÉE
    face_locations, face_encodings = detect_faces_optimized(frame)
    
    if len(face_locations) != 1:
        return jsonify({
            "success": False, 
            "message": "Un seul visage requis"
        }), 400
    
    # Utiliser l'encodage déjà calculé
    registration_encodings.append(face_encodings[0])
    registration_count += 1
    
    logger.info(f"✅ Photo {registration_count}/{registration_total} capturée")
    
    return jsonify({
        "success": True,
        "count": registration_count,
        "total": registration_total,
        "complete": registration_count >= registration_total
    })


if __name__ == '__main__':
    logger.info("=" * 50)
    logger.info("🌐 Démarrage de l'interface web")
    logger.info("=" * 50)
    
    # Charger les visages au démarrage
    load_known_faces()
    
    # Initialiser les notifications
    init_notifications()
    
    # Lancer l'application
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
