# 🎭 Système de Reconnaissance Faciale

Un système complet de reconnaissance faciale en temps réel avec interface web moderne et notifications Discord intelligentes.

![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)
![OpenCV](https://img.shields.io/badge/OpenCV-4.x-green.svg)
![Flask](https://img.shields.io/badge/Flask-3.x-lightgrey.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ Fonctionnalités

### Core Features
- 🎥 **Détection de visages en temps réel** avec OpenCV et face_recognition
- 👤 **Enregistrement de nouveaux visages** via interface web ou CLI
- 🎯 **Reconnaissance faciale** avec score de confiance
- 🌐 **Interface web moderne** avec streaming vidéo MJPEG
- 📊 **Tableau de bord** avec statistiques en temps réel

### Notifications Intelligentes
- 👋 **Notification d'arrivée** : Alerte Discord quand une personne est détectée (avec photo)
- 🚪 **Notification de départ** : Alerte quand la personne quitte (avec durée de présence)
- 🚫 **Anti-spam** : Système intelligent sans notifications répétitives
- ✅ **Notifications d'enregistrement** : Confirmation lors de l'ajout d'un nouveau visage

### Robustesse
- 📝 **Logs automatiques** : Fichiers journaliers et CSV pour l'historique
- ⚙️ **Configuration externalisée** : Fichier JSON pour tous les paramètres
- 🛡️ **Gestion d'erreurs** complète
- 🔧 **Mode debug** pour le développement

## 📸 Screenshots

### Interface principale
![Interface principale](docs/screenshots/interface-main.png)

### Page d'enregistrement
![Page d'enregistrement](docs/screenshots/interface-register.png)

### Notifications Discord
![Notification arrivée](docs/screenshots/notification-arrival.png)
![Notification départ](docs/screenshots/notification-departure.png)

## 🚀 Installation

### Prérequis

- Python 3.12 ou supérieur
- Webcam USB ou intégrée
- Serveur Debian/Ubuntu (ou Windows/macOS pour développement)

### Dépendances système
```bash
# Sur Debian/Ubuntu
sudo apt update
sudo apt install cmake build-essential libopenblas-dev liblapack-dev python3-dev
```

### Installation du projet
```bash
# Cloner le repository
git clone https://github.com/votre-username/face_recognition.git
cd face_recognition

# Créer l'environnement virtuel
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Installer les dépendances Python
pip install --upgrade pip setuptools
pip install opencv-python numpy pillow click face-recognition flask requests
```

### Configuration
```bash
# Copier le fichier de configuration exemple
cp config/settings.example.json config/settings.json

# Éditer la configuration
nano config/settings.json
```

**Configuration Discord** (optionnel) :

1. Créer un webhook Discord :
   - Serveur Discord → Paramètres → Intégrations → Webhooks → Nouveau Webhook
   - Copier l'URL du webhook

2. Dans `config/settings.json`, remplacer :
```json
   "webhook_url": "YOUR_DISCORD_WEBHOOK_URL_HERE"
```

## 📖 Utilisation

### Interface Web (Recommandé)
```bash
# Démarrer le serveur web
cd src/web
python3 app.py
```

Accéder à l'interface : `http://localhost:5000` (ou `http://IP_DU_SERVEUR:5000`)

**Fonctionnalités de l'interface :**
- ▶️ Activer/désactiver la reconnaissance
- ➕ Enregistrer un nouveau visage
- 🔄 Recharger les visages enregistrés
- 📊 Voir les statistiques en temps réel
- 📜 Consulter l'historique des reconnaissances

### Scripts CLI

#### Enregistrer un nouveau visage
```bash
python3 src/register_face.py
```

Instructions :
1. Entrer le nom de la personne
2. Se positionner face à la webcam
3. Appuyer sur **ESPACE** pour capturer (5 photos nécessaires)
4. Le visage est automatiquement enregistré

#### Reconnaissance faciale (CLI)
```bash
python3 src/recognize_faces.py
```

Touches :
- **Q** : Quitter
- **D** : Activer/désactiver le mode debug

#### Détection simple
```bash
python3 src/detect_faces.py
```

## 🏗️ Architecture du projet
```
face_recognition/
├── src/
│   ├── detect_faces.py           # Détection simple de visages
│   ├── register_face.py          # Enregistrement CLI
│   ├── recognize_faces.py        # Reconnaissance CLI complète
│   ├── notifications.py          # Système de notifications
│   └── web/
│       ├── app.py                # Application Flask
│       ├── templates/            # Templates HTML
│       └── static/               # CSS, JS, assets
├── data/
│   ├── faces/                    # Visages enregistrés (.pkl)
│   └── detections/               # Captures (mode headless)
├── config/
│   ├── settings.json             # Configuration (git-ignoré)
│   └── settings.example.json    # Template de configuration
├── logs/
│   ├── recognition_*.log         # Logs quotidiens
│   ├── recognitions.csv          # Historique CSV
│   └── temp_notifications/       # Images temporaires
├── docs/
│   └── screenshots/              # Screenshots du README
├── .gitignore
├── README.md
└── venv/
```

## ⚙️ Configuration

### Paramètres disponibles

**Caméra** :
```json
"camera": {
    "device_id": 0,           // ID de la webcam (0 = défaut)
    "width": 640,             // Largeur de la vidéo
    "height": 480             // Hauteur de la vidéo
}
```

**Reconnaissance** :
```json
"recognition": {
    "tolerance": 0.6,         // Seuil de reconnaissance (0.4-0.7)
    "process_every_n_frames": 2,  // Traiter 1 frame sur N
    "model": "hog"            // "hog" (rapide) ou "cnn" (précis)
}
```

**Affichage** :
```json
"display": {
    "show_confidence": true,  // Afficher le score de confiance
    "show_timestamp": true,   // Afficher l'heure
    "show_fps": true,         // Afficher les FPS
    "debug_mode": false       // Mode debug
}
```

**Notifications Discord** :
```json
"notifications": {
    "discord": {
        "enabled": true,      // Activer/désactiver
        "webhook_url": "...", // URL du webhook
        "send_image": true    // Envoyer une photo
    }
}
```

## 🔒 Sécurité et confidentialité

### Données personnelles

⚠️ **IMPORTANT** : Ce projet traite des données biométriques sensibles.

**Bonnes pratiques** :
- ✅ Les fichiers `.pkl` ne sont **jamais** versionnés dans Git
- ✅ Données stockées **localement uniquement**
- ✅ Pas de connexion cloud ou API externe (sauf Discord si activé)
- ✅ Webhook Discord dans fichier de config git-ignoré

**RGPD** :
- Obtenir le **consentement explicite** avant d'enregistrer un visage
- Informer de l'usage des données
- Permettre la **suppression** des données (supprimer le fichier .pkl)

### Supprimer un visage enregistré
```bash
# Lister les visages
ls data/faces/

# Supprimer un visage
rm data/faces/NOM_PRENOM_*.pkl

# Recharger dans l'interface web
# Bouton "Recharger les visages"
```

## 🐛 Dépannage

### La webcam ne fonctionne pas
```bash
# Vérifier les périphériques vidéo
ls -l /dev/video*

# Tester avec OpenCV
python3 -c "import cv2; print(cv2.VideoCapture(0).isOpened())"
```

### Erreur "No module named 'face_recognition'"
```bash
# Vérifier l'environnement virtuel
which python3
# Doit afficher : .../venv/bin/python3

# Réinstaller
pip install face-recognition
```

### Erreur de compilation dlib
```bash
# Installer CMake et les dépendances
sudo apt install cmake build-essential libopenblas-dev liblapack-dev
pip install dlib
```

### Port 5000 déjà utilisé
```bash
# Modifier le port dans src/web/app.py
# Ligne : app.run(host='0.0.0.0', port=5000, ...)
# Changer en : port=5001
```

### Les notifications Discord ne fonctionnent pas

- Vérifier l'URL du webhook dans `config/settings.json`
- Vérifier que `enabled: true`
- Consulter les logs : `logs/recognition_*.log`

## 🛠️ Technologies utilisées

- **Python 3.12+** : Langage principal
- **OpenCV 4.x** : Traitement d'image et vidéo
- **face_recognition** : Reconnaissance faciale (basé sur dlib)
- **Flask** : Framework web
- **Discord Webhooks** : Notifications
- **NumPy** : Calculs matriciels

## 📊 Performance

**Benchmarks** (sur Debian 12, Raspberry Pi 4) :
- Détection : ~15-20 FPS (mode hog)
- Reconnaissance : ~10-15 FPS
- Via X11 forwarding : ~3-5 FPS
- Via interface web : ~8-12 FPS

**Optimisations** :
- Réduire la résolution : `"width": 320, "height": 240`
- Augmenter `process_every_n_frames`
- Utiliser `"model": "hog"` au lieu de `"cnn"`

## 🤝 Contribution

Les contributions sont les bienvenues !

1. Fork le projet
2. Créer une branche (`git checkout -b feature/AmazingFeature`)
3. Commit les changements (`git commit -m 'Add AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## 📝 Roadmap

### Futures fonctionnalités
- [ ] Notifications Telegram
- [ ] Notifications Email (SMTP)
- [ ] Interface web avec authentification
- [ ] Tableau de bord avec graphiques
- [ ] Export des données en PDF
- [ ] Support multi-caméras
- [ ] API REST pour intégrations
- [ ] Application mobile (React Native)
- [ ] Conteneurisation Docker
- [ ] Mode nuit (détection infrarouge)

## 📄 License

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 👨‍💻 Auteur

**mclanecorp**

## 🙏 Remerciements

- [face_recognition](https://github.com/ageitgey/face_recognition) par Adam Geitgey
- [OpenCV](https://opencv.org/)
- [Flask](https://flask.palletsprojects.com/)
- La communauté Python

## ⚠️ Avertissement

Ce projet est à des fins **éducatives et de démonstration**. 

**Attention** :
- ⚠️ Ne pas utiliser pour la surveillance non consentie
- ⚠️ Respecter la vie privée et les lois locales (RGPD en Europe)
- ⚠️ Les données biométriques sont sensibles
- ⚠️ Ce n'est pas un système de sécurité professionnel

L'auteur décline toute responsabilité pour une utilisation inappropriée de ce logiciel.

---

**Fait avec ❤️ par mclanecorp**
