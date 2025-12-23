/**
 * Main Application Module
 * 
 * Initialises all modules and coordinates their interactions.
 * This is the entry point for the Electric Heater Room website application.
 * 
 * @module main
 */

import { loadConfig, getAudioArchives, getVideoArchives } from './config.js';
import { initNavigation, initHashNavigation, switchSection } from './navigation.js';
import { 
    initLiveStreams, 
    loadAudioArchives, 
    loadVideoArchives 
} from './embeds.js';
import { initStreamControls } from './stream-controls.js';
import { initChatEmbeds } from './chat-init.js';
import { initLogoAnimations } from './logo-animations.js';
import { loadAndDisplayEvents } from './events.js';

/**
 * Initialises the entire application
 * 
 * Loads configuration, sets up navigation, initialises embeds, and loads archive content.
 * Should be called once when the DOM is ready.
 * 
 * @example
 * // Called automatically when DOM is ready
 * init();
 */
async function init() {
    try {
        console.log('Electric Heater Room: Initialising...');

        // Wait for DOM to be fully ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                startInitialisation();
            });
        } else {
            startInitialisation();
        }
    } catch (error) {
        console.error('Error initialising application:', error);
    }
}

/**
 * Performs the actual initialisation steps
 * 
 * @private
 */
async function startInitialisation() {
    try {
        // Initialise navigation first
        initNavigation();
        initHashNavigation();

        // Initialise logo animations (plays on load, every 69s, and on click)
        initLogoAnimations();

        // Initialise live streams
        initLiveStreams('flukie', 'flukie');

        // Initialise chat embeds with correct parent parameters
        initChatEmbeds();

        // Initialise stream controls (expand/collapse and chat)
        initStreamControls();

        // Load and display archives
        await loadArchives();

        console.log('Electric Heater Room: Initialisation complete');
    } catch (error) {
        console.error('Error during initialisation:', error);
        showError('Failed to load content. Please refresh the page.');
    }
}

/**
 * Loads and displays audio and video archives
 * 
 * @private
 */
async function loadArchives() {
    try {
        // Load configuration
        await loadConfig();

        // Load audio archives
        const audioArchives = await getAudioArchives();
        loadAudioArchives(audioArchives);

        // Load video archives
        const videoArchives = await getVideoArchives();
        loadVideoArchives(videoArchives);

        // Load and display events
        loadAndDisplayEvents();
    } catch (error) {
        console.error('Error loading archives:', error);
        // Show error messages in the containers
        const audioContainer = document.getElementById('audio-archives-container');
        const videoContainer = document.getElementById('video-archives-container');
        
        if (audioContainer) {
            audioContainer.innerHTML = '<div class="loading">Error loading audio archives</div>';
        }
        if (videoContainer) {
            videoContainer.innerHTML = '<div class="loading">Error loading video archives</div>';
        }
    }
}

/**
 * Displays an error message to the user
 * 
 * @param {string} message - The error message to display
 * @private
 */
function showError(message) {
    const mainContent = document.querySelector('.main-content');
    if (mainContent) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.style.cssText = `
            padding: 2rem;
            text-align: center;
            color: var(--accent-orange);
            font-size: 1.2rem;
        `;
        errorDiv.textContent = message;
        mainContent.insertBefore(errorDiv, mainContent.firstChild);
    }
}

// Start the application when this module loads
init();

// Export functions that might be useful for debugging or external use
export { init, loadArchives };

