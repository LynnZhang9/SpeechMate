// SpeechMate Admin App

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('configForm');
    const newApiKeyInput = document.getElementById('newApiKey');
    const currentKeyDisplay = document.getElementById('currentKey');
    const saveBtn = document.getElementById('saveBtn');
    const toggleBtn = document.getElementById('toggleVisibility');
    const messageDiv = document.getElementById('message');

    // Load current config on page load
    loadCurrentConfig();

    // Toggle password visibility
    toggleBtn.addEventListener('click', function() {
        if (newApiKeyInput.type === 'password') {
            newApiKeyInput.type = 'text';
            toggleBtn.textContent = 'Hide';
        } else {
            newApiKeyInput.type = 'password';
            toggleBtn.textContent = 'Show';
        }
    });

    // Handle form submission
    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        const apiKey = newApiKeyInput.value.trim();

        if (!apiKey) {
            showMessage('Please enter an API key', 'error');
            return;
        }

        saveBtn.disabled = true;
        saveBtn.innerHTML = '<span class="loading"></span>Saving...';

        try {
            const response = await fetch('/api/config', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ api_key: apiKey })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();

            if (result.success) {
                showMessage('API key saved successfully!', 'success');
                newApiKeyInput.value = '';
                // Reload current config to show updated masked key
                await loadCurrentConfig();
            } else {
                showMessage('Failed to save API key', 'error');
            }
        } catch (error) {
            console.error('Error saving config:', error);
            showMessage('Error saving API key: ' + error.message, 'error');
        } finally {
            saveBtn.disabled = false;
            saveBtn.innerHTML = 'Save';
        }
    });

    // Load current configuration
    async function loadCurrentConfig() {
        try {
            const response = await fetch('/api/config');

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const config = await response.json();
            currentKeyDisplay.textContent = config.api_key || 'Not configured';
        } catch (error) {
            console.error('Error loading config:', error);
            currentKeyDisplay.textContent = 'Error loading configuration';
        }
    }

    // Show message
    function showMessage(text, type) {
        messageDiv.textContent = text;
        messageDiv.className = 'message ' + type;

        // Auto-hide success messages after 3 seconds
        if (type === 'success') {
            setTimeout(function() {
                messageDiv.className = 'message hidden';
            }, 3000);
        }
    }
});
