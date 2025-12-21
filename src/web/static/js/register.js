let currentStep = 1;
let captureCount = 0;
const totalCaptures = 5;
let registrationActive = false;

// Éléments DOM
const nameInput = document.getElementById('name-input');
const startBtn = document.getElementById('start-btn');
const captureBtn = document.getElementById('capture-btn');
const cancelBtn = document.getElementById('cancel-btn');
const saveBtn = document.getElementById('save-btn');
const newRegBtn = document.getElementById('new-registration-btn');

const nameSection = document.getElementById('name-section');
const captureSection = document.getElementById('capture-section');
const saveSection = document.getElementById('save-section');
const successSection = document.getElementById('success-section');

const registrationFeed = document.getElementById('registration-feed');
const progressFill = document.getElementById('progress-fill');

// Démarrer l'enregistrement
startBtn.addEventListener('click', async () => {
    const name = nameInput.value.trim();
    
    if (!name) {
        showNotification('Veuillez entrer un nom', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/start_registration', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({name})
        });
        
        const data = await response.json();
        
        if (data.success) {
            registrationActive = true;
            goToStep(2);
            registrationFeed.src = '/registration_feed?' + new Date().getTime();
            showNotification(data.message, 'success');
        } else {
            showNotification(data.message, 'error');
        }
    } catch (error) {
        showNotification('Erreur de connexion', 'error');
        console.error(error);
    }
});

// Capturer une photo
captureBtn.addEventListener('click', capturePhoto);

// Raccourci clavier (Espace)
document.addEventListener('keydown', (e) => {
    if (e.code === 'Space' && currentStep === 2 && captureCount < totalCaptures) {
        e.preventDefault();
        capturePhoto();
    }
});

async function capturePhoto() {
    if (captureCount >= totalCaptures) return;
    
    try {
        const response = await fetch('/api/auto_capture', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            captureCount = data.count;
            updateProgress();
            
            // Marquer le slot comme capturé
            document.getElementById(`slot-${captureCount}`).classList.add('captured');
            document.getElementById(`slot-${captureCount}`).textContent = '✓';
            
            showNotification(`Photo ${captureCount}/${totalCaptures} capturée !`, 'success');
            
            if (data.complete) {
                setTimeout(() => goToStep(3), 500);
            }
        } else {
            showNotification(data.message, 'error');
        }
    } catch (error) {
        showNotification('Erreur lors de la capture', 'error');
        console.error(error);
    }
}

// Annuler
cancelBtn.addEventListener('click', async () => {
    if (!confirm('Voulez-vous vraiment annuler l\'enregistrement ?')) return;
    
    try {
        await fetch('/api/cancel_registration', {method: 'POST'});
        registrationActive = false;
        resetRegistration();
        goToStep(1);
        showNotification('Enregistrement annulé', 'info');
    } catch (error) {
        console.error(error);
    }
});

// Sauvegarder
saveBtn.addEventListener('click', async () => {
    try {
        const response = await fetch('/api/save_registration', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('success-message').textContent = data.message;
            goToStep(4);
            showNotification(data.message, 'success');
        } else {
            showNotification(data.message, 'error');
        }
    } catch (error) {
        showNotification('Erreur lors de la sauvegarde', 'error');
        console.error(error);
    }
});

// Nouvel enregistrement
newRegBtn.addEventListener('click', () => {
    resetRegistration();
    goToStep(1);
    nameInput.value = '';
    nameInput.focus();
});

// Navigation entre étapes
function goToStep(step) {
    currentStep = step;
    
    // Masquer toutes les sections
    nameSection.style.display = 'none';
    captureSection.style.display = 'none';
    saveSection.style.display = 'none';
    successSection.style.display = 'none';
    
    // Afficher la bonne section
    if (step === 1) nameSection.style.display = 'block';
    else if (step === 2) captureSection.style.display = 'block';
    else if (step === 3) saveSection.style.display = 'block';
    else if (step === 4) successSection.style.display = 'block';
    
    // Mettre à jour les indicateurs d'étapes
    for (let i = 1; i <= 3; i++) {
        const stepEl = document.getElementById(`step-${i}`);
        stepEl.classList.remove('active', 'completed');
        
        if (i < step) stepEl.classList.add('completed');
        else if (i === step) stepEl.classList.add('active');
    }
}

// Mise à jour de la barre de progression
function updateProgress() {
    const percent = (captureCount / totalCaptures) * 100;
    progressFill.style.width = `${percent}%`;
    progressFill.textContent = `${captureCount}/${totalCaptures}`;
}

// Réinitialisation
function resetRegistration() {
    captureCount = 0;
    registrationActive = false;
    updateProgress();
    
    // Réinitialiser les slots
    for (let i = 1; i <= totalCaptures; i++) {
        const slot = document.getElementById(`slot-${i}`);
        slot.classList.remove('captured');
        slot.textContent = i;
    }
}

// Notification
function showNotification(message, type = 'info') {
    const colors = {
        success: '#10b981',
        error: '#ef4444',
        info: '#3b82f6'
    };
    
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background: ${colors[type]};
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