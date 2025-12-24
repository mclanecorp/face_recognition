#!/usr/bin/env python3
"""
Intégration Home Assistant
Permet de contrôler les appareils HA lors de reconnaissances
"""
import requests
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class HomeAssistantIntegration:
    """Gestion des actions Home Assistant"""
    
    def __init__(self, config):
        self.config = config
        self.enabled = config.get("home_assistant", "enabled") or False
        self.url = config.get("home_assistant", "url")
        self.token = config.get("home_assistant", "token")
        
        if self.enabled and self.url and self.token:
            logger.info("🏠 Intégration Home Assistant activée")
        else:
            logger.info("🏠 Intégration Home Assistant désactivée")
    
    def execute_actions(self, event_type):
        """
        Exécute les actions Home Assistant configurées
        
        Args:
            event_type: "on_arrival" ou "on_departure"
        """
        if not self.enabled:
            return
        
        actions = self.config.get("home_assistant", "actions", event_type)
        
        if not actions:
            return
        
        for action in actions:
            self._call_service(action)
    
    def _call_service(self, action):
        """Appelle un service Home Assistant"""
        entity_id = action.get("entity_id")
        service = action.get("service")
        data = action.get("data", {})
        
        if not entity_id or not service:
            logger.error("❌ Action HA invalide: entity_id ou service manquant")
            return
        
        # Extraire domain et service du format "domain.service"
        if "." not in service:
            logger.error(f"❌ Format service invalide: {service}")
            return
        
        domain, service_name = service.split(".", 1)
        
        # Préparer l'URL
        url = f"{self.url}/api/services/{domain}/{service_name}"
        
        # Headers avec authentification
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        # Payload
        payload = {
            "entity_id": entity_id,
            **data
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=5)
            
            if response.status_code in [200, 201]:
                logger.info(f"✅ Home Assistant: {service} sur {entity_id}")
            else:
                logger.error(f"❌ Home Assistant erreur: {response.status_code} - {response.text}")
        
        except requests.exceptions.Timeout:
            logger.error(f"❌ Home Assistant timeout: {url}")
        except Exception as e:
            logger.error(f"❌ Home Assistant erreur: {e}")
    
    def test_connection(self):
        """Test la connexion à Home Assistant"""
        if not self.enabled:
            return False
        
        url = f"{self.url}/api/"
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                logger.info("✅ Connexion Home Assistant OK")
                return True
            else:
                logger.error(f"❌ Connexion Home Assistant échouée: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Connexion Home Assistant erreur: {e}")
            return False
    
    def trigger_on_arrival(self, name):
        """Actions lors d'une arrivée"""
        logger.info(f"🏠 Déclenchement actions arrivée pour {name}")
        self.execute_actions("on_arrival")
    
    def trigger_on_departure(self, name):
        """Actions lors d'un départ"""
        logger.info(f"🏠 Déclenchement actions départ pour {name}")
        self.execute_actions("on_departure")