// StoryMimi Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    console.log('StoryMimi application loaded');
    
    // Initialize any UI components
    initializeUI();
    
    // Add event listeners
    addEventListeners();
});

/**
 * Initialize UI components
 */
function initializeUI() {
    // Toggle mobile navigation menu if it exists
    const menuToggle = document.querySelector('.menu-toggle');
    if (menuToggle) {
        const navMenu = document.querySelector('nav ul');
        menuToggle.addEventListener('click', function() {
            navMenu.classList.toggle('show');
        });
    }
    
    // Initialize audio players if they exist
    const audioPlayers = document.querySelectorAll('.audio-player');
    audioPlayers.forEach(player => {
        // Add custom controls or functionality if needed
        player.addEventListener('play', function() {
            console.log('Audio playback started');
        });
    });
}

/**
 * Add event listeners to interactive elements
 */
function addEventListeners() {
    // Story creation form submission
    const storyForm = document.getElementById('story-form');
    if (storyForm) {
        storyForm.addEventListener('submit', function(e) {
            e.preventDefault();
            submitStoryForm(this);
        });
    }
    
    // User creation form submission
    const userForm = document.getElementById('user-form');
    if (userForm) {
        userForm.addEventListener('submit', function(e) {
            e.preventDefault();
            submitUserForm(this);
        });
    }
}

/**
 * Submit the story creation form via API
 * @param {HTMLFormElement} form - The story creation form
 */
async function submitStoryForm(form) {
    try {
        const formData = new FormData(form);
        const data = {
            title: formData.get('title'),
            prompt: formData.get('prompt'),
            style: formData.get('style'),
            num_scenes: parseInt(formData.get('num_scenes')),
            user_id: formData.get('user_id')
        };
        
        // Show loading state
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.textContent = 'Creating Story...';
        
        // Make API request
        const response = await fetch('/stories/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            throw new Error('Failed to create story');
        }
        
        const result = await response.json();
        
        // Show success message
        showAlert('Story creation started! Story ID: ' + result.story_id, 'success');
        
        // Redirect to story status page
        setTimeout(() => {
            window.location.href = `/story-status.html?id=${result.story_id}`;
        }, 2000);
        
    } catch (error) {
        console.error('Error creating story:', error);
        showAlert('Error creating story: ' + error.message, 'danger');
        
        // Reset button
        const submitBtn = form.querySelector('button[type="submit"]');
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
    }
}

/**
 * Submit the user creation form via API
 * @param {HTMLFormElement} form - The user creation form
 */
async function submitUserForm(form) {
    try {
        const formData = new FormData(form);
        const data = {
            email: formData.get('email'),
            username: formData.get('username')
        };
        
        // Show loading state
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.textContent = 'Creating User...';
        
        // Make API request
        const response = await fetch('/users/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            throw new Error('Failed to create user');
        }
        
        const result = await response.json();
        
        // Show success message
        showAlert('User created successfully! User ID: ' + result.user_id, 'success');
        
        // Store user ID in local storage for future use
        localStorage.setItem('currentUserId', result.user_id);
        
        // Redirect to create story page
        setTimeout(() => {
            window.location.href = '/create-story.html';
        }, 2000);
        
    } catch (error) {
        console.error('Error creating user:', error);
        showAlert('Error creating user: ' + error.message, 'danger');
        
        // Reset button
        const submitBtn = form.querySelector('button[type="submit"]');
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
    }
}

/**
 * Display an alert message to the user
 * @param {string} message - The message to display
 * @param {string} type - The type of alert (success, warning, danger)
 */
function showAlert(message, type = 'info') {
    const alertContainer = document.getElementById('alert-container');
    if (!alertContainer) {
        // Create alert container if it doesn't exist
        const container = document.createElement('div');
        container.id = 'alert-container';
        container.style.position = 'fixed';
        container.style.top = '20px';
        container.style.right = '20px';
        container.style.zIndex = '1000';
        document.body.appendChild(container);
    }
    
    // Create alert element
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="close" aria-label="Close">
            <span aria-hidden="true">&times;</span>
        </button>
    `;
    
    // Add close button functionality
    const closeBtn = alert.querySelector('.close');
    closeBtn.addEventListener('click', function() {
        alert.remove();
    });
    
    // Add to container
    const container = document.getElementById('alert-container');
    container.appendChild(alert);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alert.parentNode) {
            alert.remove();
        }
    }, 5000);
}

/**
 * Check the status of a story periodically
 * @param {string} storyId - The ID of the story to check
 */
function pollStoryStatus(storyId) {
    const statusElement = document.getElementById('story-status');
    if (!statusElement) return;
    
    const interval = setInterval(async () => {
        try {
            const response = await fetch(`/stories/${storyId}/status`);
            if (!response.ok) {
                throw new Error('Failed to fetch story status');
            }
            
            const data = await response.json();
            statusElement.textContent = data.status;
            statusElement.className = `badge badge-${data.status.toLowerCase()}`;
            
            // If story is complete or failed, stop polling
            if (data.status === 'COMPLETE' || data.status === 'FAILED') {
                clearInterval(interval);
                
                if (data.status === 'COMPLETE') {
                    // Show view story button
                    const viewBtn = document.getElementById('view-story-btn');
                    if (viewBtn) {
                        viewBtn.style.display = 'inline-block';
                        viewBtn.href = `/story.html?id=${storyId}`;
                    }
                }
            }
            
        } catch (error) {
            console.error('Error checking story status:', error);
            clearInterval(interval);
        }
    }, 5000); // Check every 5 seconds
    
    // Store interval ID to clear it when navigating away
    window.storyStatusInterval = interval;
}

// Clean up intervals when navigating away
window.addEventListener('beforeunload', function() {
    if (window.storyStatusInterval) {
        clearInterval(window.storyStatusInterval);
    }
});