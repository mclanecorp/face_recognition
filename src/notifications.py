#!/usr/bin/env python3
"""
Module de notifications avec détection arrivée/départ
Support Discord, Telegram, Email, Webhook
"""
import requests
import json
import logging
from datetime import datetime, timedelta
import cv2
from pathlib import Path

logger = logging.getLogger(__name__)


class NotificationManager:
    """Gestionnaire de notifications avec détection présence"""
    
    def __init__(self, config):
        self.config = config
        
        # État de présence des personnes
        self.presence_state = {}  # {name: {"present": bool, "last_seen": datetime, "arrival_time": datetime}}
        
        # Configuration
        self.absence_threshold = 10  # Secondes sans détection = parti
        self.min_presence_duration = 3  # Secondes minimum de présence avant notification départ
    
    def update_presence(self, detected_people):
        """
        Met à jour l'état de présence et retourne les événements (arrivée/départ)
        
        Args:
            detected_people: Liste de tuples (name, confidence, frame)
        
        Returns:
            Liste d'événements: [{"type": "arrival/departure", "name": str, "data": dict}]
        """
        current_time = datetime.now()
        events = []
        
        # Marquer qui est présent maintenant
        currently_present = set()
        
        for name, confidence, frame in detected_people:
            if name == "Inconnu":
                continue
            
            currently_present.add(name)
            
            # Vérifier si c'est une nouvelle arrivée
            if name not in self.presence_state or not self.presence_state[name]["present"]:
                # Arrivée détectée
                self.presence_state[name] = {
                    "present": True,
                    "last_seen": current_time,
                    "arrival_time": current_time
                }
                
                events.append({
                    "type": "arrival",
                    "name": name,
                    "data": {
                        "confidence": confidence,
                        "frame": frame,
                        "timestamp": current_time
                    }
                })
                
                logger.info(f"👋 Arrivée détectée: {name}")
            
            else:
                # Mise à jour du last_seen
                self.presence_state[name]["last_seen"] = current_time
        
        # Vérifier les départs (personnes qui étaient présentes mais plus détectées)
        for name in list(self.presence_state.keys()):
            if name not in currently_present and self.presence_state[name]["present"]:
                # Vérifier si assez de temps écoulé sans détection
                time_since_last_seen = (current_time - self.presence_state[name]["last_seen"]).total_seconds()
                
                if time_since_last_seen >= self.absence_threshold:
                    # Vérifier durée minimale de présence
                    presence_duration = (self.presence_state[name]["last_seen"] - self.presence_state[name]["arrival_time"]).total_seconds()
                    
                    if presence_duration >= self.min_presence_duration:
                        # Départ confirmé
                        events.append({
                            "type": "departure",
                            "name": name,
                            "data": {
                                "arrival_time": self.presence_state[name]["arrival_time"],
                                "departure_time": self.presence_state[name]["last_seen"],
                                "duration": presence_duration,
                                "timestamp": current_time
                            }
                        })
                        
                        logger.info(f"👋 Départ détecté: {name} (présence: {self._format_duration(presence_duration)})")
                    
                    # Marquer comme absent
                    self.presence_state[name]["present"] = False
        
        return events
    
    def process_events(self, events):
        """Traite les événements et envoie les notifications appropriées"""
        for event in events:
            if event["type"] == "arrival":
                self._notify_arrival(event["name"], event["data"])
            elif event["type"] == "departure":
                self._notify_departure(event["name"], event["data"])
    
    def _notify_arrival(self, name, data):
        """Notification d'arrivée"""
        if self.config.get("notifications", "discord", "enabled"):
            self._send_discord_arrival(name, data)
    
    def _notify_departure(self, name, data):
        """Notification de départ"""
        if self.config.get("notifications", "discord", "enabled"):
            self._send_discord_departure(name, data)
    
    def _send_discord_arrival(self, name, data):
        """Envoie une notification Discord d'arrivée"""
        webhook_url = self.config.get("notifications", "discord", "webhook_url")
        send_image = self.config.get("notifications", "discord", "send_image")
        
        if not webhook_url or webhook_url == "TON_URL_WEBHOOK_ICI":
            logger.warning("⚠️  URL webhook Discord non configurée")
            return
        
        try:
            timestamp = data["timestamp"].strftime("%d/%m/%Y à %H:%M:%S")
            confidence_percent = data["confidence"] * 100
            
            # Couleur verte pour arrivée
            color = 0x10b981
            
            # Créer l'embed
            embed = {
                "title": f"👋 {name} est arrivé(e)",
                "description": f"Détection d'une personne connue.",
                "color": color,
                "fields": [
                    {
                        "name": "👤 Personne",
                        "value": name,
                        "inline": True
                    },
                    {
                        "name": "📊 Confiance",
                        "value": f"{confidence_percent:.1f}%",
                        "inline": True
                    },
                    {
                        "name": "🕐 Heure d'arrivée",
                        "value": timestamp,
                        "inline": False
                    }
                ],
                "footer": {
                    "text": "Système de reconnaissance faciale"
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            payload = {"embeds": [embed]}
            
            # Envoyer avec image si demandé
            if send_image and data["frame"] is not None:
                self._send_with_image(webhook_url, payload, data["frame"], f"arrival_{name}")
            else:
                response = requests.post(
                    webhook_url,
                    json=payload,
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code in [200, 204]:
                    logger.info(f"✅ Notification Discord (arrivée) envoyée pour {name}")
        
        except Exception as e:
            logger.error(f"❌ Erreur envoi Discord: {e}")
    
    def _send_discord_departure(self, name, data):
        """Envoie une notification Discord de départ"""
        webhook_url = self.config.get("notifications", "discord", "webhook_url")
        
        if not webhook_url or webhook_url == "TON_URL_WEBHOOK_ICI":
            return
        
        try:
            departure_time = data["departure_time"].strftime("%d/%m/%Y à %H:%M:%S")
            duration_str = self._format_duration(data["duration"])
            
            # Couleur orange pour départ
            color = 0xf59e0b
            
            embed = {
                "title": f"🚪 {name} est parti(e)",
                "description": f"La personne a quitté le champ de vision.",
                "color": color,
                "fields": [
                    {
                        "name": "👤 Personne",
                        "value": name,
                        "inline": True
                    },
                    {
                        "name": "⏱️ Durée de présence",
                        "value": duration_str,
                        "inline": True
                    },
                    {
                        "name": "🕐 Heure de départ",
                        "value": departure_time,
                        "inline": False
                    }
                ],
                "footer": {
                    "text": "Système de reconnaissance faciale"
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            payload = {"embeds": [embed]}
            
            response = requests.post(
                webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code in [200, 204]:
                logger.info(f"✅ Notification Discord (départ) envoyée pour {name}")
        
        except Exception as e:
            logger.error(f"❌ Erreur envoi Discord: {e}")
    
    def _send_with_image(self, webhook_url, payload, frame, prefix):
        """Envoie un message Discord avec image"""
        try:
            # Sauvegarder temporairement l'image
            temp_dir = Path("../../logs/temp_notifications")
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            temp_file = temp_dir / f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            cv2.imwrite(str(temp_file), frame)
            
            # Envoyer avec fichier
            with open(temp_file, 'rb') as f:
                files = {
                    'file': (temp_file.name, f, 'image/jpeg')
                }
                response = requests.post(
                    webhook_url,
                    data={'payload_json': json.dumps(payload)},
                    files=files
                )
            
            # Nettoyer le fichier temporaire
            temp_file.unlink()
            
            return response.status_code in [200, 204]
        
        except Exception as e:
            logger.error(f"❌ Erreur envoi image: {e}")
            return False
    
    def _format_duration(self, seconds):
        """Formate une durée en secondes en format lisible"""
        if seconds < 60:
            return f"{int(seconds)} secondes"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            secs = int(seconds % 60)
            return f"{minutes} min {secs} sec"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours}h {minutes} min"
    
    def send_new_registration(self, name):
        """Notification pour un nouveau visage enregistré"""
        webhook_url = self.config.get("notifications", "discord", "webhook_url")
        
        if not webhook_url or webhook_url == "TON_URL_WEBHOOK_ICI":
            return
        
        try:
            embed = {
                "title": "✅ Nouveau visage enregistré",
                "description": f"Un nouveau visage a été ajouté au système.",
                "color": 0x8b5cf6,  # Violet
                "fields": [
                    {
                        "name": "👤 Nom",
                        "value": name,
                        "inline": True
                    },
                    {
                        "name": "🕐 Heure",
                        "value": datetime.now().strftime("%d/%m/%Y à %H:%M:%S"),
                        "inline": True
                    }
                ],
                "footer": {
                    "text": "Système de reconnaissance faciale"
                }
            }
            
            payload = {"embeds": [embed]}
            
            response = requests.post(
                webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code in [200, 204]:
                logger.info(f"✅ Notification enregistrement envoyée pour {name}")
        
        except Exception as e:
            logger.error(f"❌ Erreur notification enregistrement: {e}")