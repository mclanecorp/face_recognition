// État de l'application
let recognitionActive = false;

// Éléments DOM
const toggleBtn = document.getElementById('toggle-recognition');
const reloadBtn = document.getElementById('reload-faces');
const statusIndicator = document.getElementById('status-indicator');
const statusText = document.getElementById('status-text');
const lastRecognitionDiv = document.getElementById('last-recognition');
const knownFacesSpan = document.getElementById('known-faces');
const recognitionStatusSpan = document.getElementById('recognition-status');
const logsDiv = document.getElementById('logs');
const testHaBtn = document.getElementById('test-ha-btn');

// Toggle reconnaissance
toggleBtn.addEventListener('click', async () => {
    try {
        const response = await fetch('/api/toggle_recognition', {
            method: 'POST'
        });
        const data = await response.json();
        
        recognitionActive = data.active;
        updateUI();
        
        showNotification(data.message, 'success');
    } catch (error) {
        showNotification('Erreur lors du toggle', 'error');
        console.error(error);
    }
});

// Recharger les visages
reloadBtn.addEventListener('click', async () => {
    try {
        const response = await fetch('/api/reload_faces', {
            method: 'POST'
        });
        const data = await response.json();
        
        showNotification(data.message, 'success');
        updateStatus();
    } catch (error) {
        showNotification('Erreur lors du rechargement', 'error');
        console.error(error);
    }
});

// Mise à jour de l'interface
function updateUI() {
    if (recognitionActive) {
        toggleBtn.textContent = 'Désactiver la reconnaissance';
        toggleBtn.classList.remove('btn-primary');
        toggleBtn.classList.add('btn-secondary');
        statusIndicator.classList.remove('inactive');
        statusIndicator.classList.add('active');
        statusText.textContent = 'Reconnaissance activée';
        recognitionStatusSpan.textContent = 'Active';
        recognitionStatusSpan.style.color = '#10b981';
    } else {
        toggleBtn.textContent = 'Activer la reconnaissance';
        toggleBtn.classList.remove('btn-secondary');
        toggleBtn.classList.add('btn-primary');
        statusIndicator.classList.remove('active');
        statusIndicator.classList.add('inactive');
        statusText.textContent = 'Reconnaissance désactivée';
        recognitionStatusSpan.textContent = 'Inactive';
        recognitionStatusSpan.style.color = '#ef4444';
    }
}

// Mise à jour du statut
async function updateStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        
        recognitionActive = data.recognition_active;
        knownFacesSpan.textContent = data.known_faces_count;
        
        if (data.last_recognition && data.last_recognition.name) {
            const nameP = lastRecognitionDiv.querySelector('.name');
            const confidenceP = lastRecognitionDiv.querySelector('.confidence');
            const timestampP = lastRecognitionDiv.querySelector('.timestamp');
            
            nameP.textContent = data.last_recognition.name;
            confidenceP.textContent = `Confiance: ${(data.last_recognition.confidence * 100).toFixed(1)}%`;
            
            const date = new Date(data.last_recognition.timestamp);
            timestampP.textContent = date.toLocaleString('fr-FR');
        }
        
        updateUI();
    } catch (error) {
        console.error('Erreur mise à jour statut:', error);
    }
}

// Mise à jour des logs
async function updateLogs() {
    try {
        const response = await fetch('/api/logs');
        const data = await response.json();
        
        if (data.logs && data.logs.length > 0) {
            logsDiv.innerHTML = data.logs.reverse().join('<br>');
        }
    } catch (error) {
        console.error('Erreur mise à jour logs:', error);
    }
}

// Notification toast
function showNotification(message, type = 'info') {
    // Créer un élément de notification
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background: ${type === 'success' ? '#10b981' : '#ef4444'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        z-index: 1000;
        animation: slideIn 0.3s ease;
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Style pour les animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(400px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(400px); opacity: 0; }
    }
`;
document.head.appendChild(style);

// homeAssistant
testHaBtn.addEventListener('click', async () => {
    try {
        const response = await fetch('/api/test_homeassistant', {
            method: 'POST'
        });
        const data = await response.json();
        showNotification(data.message, data.success ? 'success' : 'error');
    } catch (error) {
        showNotification('Erreur de test', 'error');
    }
});

// Mise à jour automatique toutes les 2 secondes
setInterval(updateStatus, 2000);
setInterval(updateLogs, 5000);

// Initialisation
updateStatus();
updateLogs();