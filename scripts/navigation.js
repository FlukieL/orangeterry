/**
 * Navigation Module
 * 
 * Handles section switching with smooth animations and active state management.
 * Provides a clean interface for navigating between different sections of the website.
 * 
 * @module navigation
 */

import { unloadSectionMedia, reloadSectionMedia } from './embeds.js';

/**
 * Currently active section ID
 * @type {string|null}
 */
let activeSection = null;

/**
 * All section elements
 * @type {NodeListOf<HTMLElement>}
 */
let sections = null;

/**
 * All navigation buttons
 * @type {NodeListOf<HTMLElement>}
 */
let navButtons = null;

/**
 * Initialises the navigation system
 * 
 * Sets up event listeners for navigation buttons and identifies the initial active section.
 * Should be called once when the page loads.
 * 
 * @example
 * initNavigation();
 */
export function initNavigation() {
    sections = document.querySelectorAll('.section');
    navButtons = document.querySelectorAll('.nav-button');

    if (sections.length === 0 || navButtons.length === 0) {
        console.warn('Navigation: No sections or buttons found');
        return;
    }

    // Set initial active section
    const initialSection = document.querySelector('.section.active');
    if (initialSection) {
        activeSection = initialSection.id;
        updateActiveButton(activeSection);
    }

    // Add click event listeners to navigation buttons
    navButtons.forEach(button => {
        button.addEventListener('click', handleNavClick);
    });

    // Optional: Handle browser back/forward buttons
    window.addEventListener('popstate', handlePopState);
}

/**
 * Handles navigation button clicks
 * 
 * @param {Event} event - The click event
 * @private
 */
function handleNavClick(event) {
    const button = event.currentTarget;
    const sectionId = button.getAttribute('data-section');

    if (sectionId) {
        switchSection(sectionId);
        
        // Update browser history
        const state = { section: sectionId };
        const url = `#${sectionId}`;
        window.history.pushState(state, '', url);
    }
}

/**
 * Handles browser back/forward navigation
 * 
 * @param {PopStateEvent} event - The popstate event
 * @private
 */
function handlePopState(event) {
    if (event.state && event.state.section) {
        switchSection(event.state.section, false);
    } else {
        // Handle hash-based navigation
        const hash = window.location.hash.slice(1);
        if (hash) {
            switchSection(hash, false);
        }
    }
}

/**
 * Switches to a different section with smooth animation
 * 
 * @param {string} sectionId - The ID of the section to switch to
 * @param {boolean} [animate=true] - Whether to animate the transition
 * 
 * @example
 * switchSection('audio-archives');
 */
export function switchSection(sectionId, animate = true) {
    const targetSection = document.getElementById(sectionId);

    if (!targetSection) {
        console.warn(`Navigation: Section "${sectionId}" not found`);
        return;
    }

    // Special handling for audio-archives: even if already on this section, 
    // clicking the tab should clear URL params and scroll to top
    const isAudioArchivesClick = sectionId === 'audio-archives' && animate && activeSection === sectionId;
    
    if (isAudioArchivesClick) {
        // Already on audio-archives, just clear URL and scroll to top
        const url = new URL(window.location.href);
        url.searchParams.delete('audio');
        window.history.replaceState({}, '', url);
        
        // Remove any highlighted items
        const highlightedItems = document.querySelectorAll('.archive-item.highlighted');
        highlightedItems.forEach(item => item.classList.remove('highlighted'));
        
        // Scroll to top
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
        return;
    }
    
    if (activeSection === sectionId) {
        return; // Already on this section
    }

    // Unload media in the current section before switching
    if (activeSection) {
        unloadSectionMedia(activeSection);
        
        // Remove video URL parameter if leaving video-archives section
        if (activeSection === 'video-archives') {
            const url = new URL(window.location.href);
            url.searchParams.delete('video');
            window.history.replaceState({}, '', url);
        }
        
        const currentSection = document.getElementById(activeSection);
        if (currentSection && animate) {
            currentSection.classList.add('fade-out');
            setTimeout(() => {
                currentSection.classList.remove('active', 'fade-out');
            }, 300);
        } else if (currentSection) {
            currentSection.classList.remove('active');
        }
    }

    // Fade in new section
    if (animate) {
        targetSection.style.opacity = '0';
        targetSection.classList.add('active');
        
        // Trigger reflow to ensure the fade-in animation works
        void targetSection.offsetHeight;
        
        requestAnimationFrame(() => {
            targetSection.style.transition = `opacity ${getComputedStyle(document.documentElement).getPropertyValue('--transition-speed')} ${getComputedStyle(document.documentElement).getPropertyValue('--transition-easing')}`;
            targetSection.style.opacity = '1';
        });
    } else {
        targetSection.classList.add('active');
    }

    // Reload media in the new section (restore iframe sources)
    reloadSectionMedia(sectionId);

    // Update active section and button
    activeSection = sectionId;
    updateActiveButton(sectionId);

    // Show/hide chat wrapper based on active section
    const chatWrapper = document.getElementById('chat-wrapper');
    if (chatWrapper) {
        if (sectionId === 'live-streams') {
            chatWrapper.style.display = 'flex';
        } else {
            chatWrapper.style.display = 'none';
        }
    }

    // Add/remove class to body and html to prevent scrolling on mobile when live streams is active
    if (sectionId === 'live-streams') {
        document.body.classList.add('live-streams-active');
        document.documentElement.classList.add('live-streams-active');
    } else {
        document.body.classList.remove('live-streams-active');
        document.documentElement.classList.remove('live-streams-active');
    }

    // Handle audio parameter when switching to audio-archives
    if (sectionId === 'audio-archives') {
        // Clear audio parameter from URL when clicking the tab (user-initiated navigation)
        if (animate) {
            const url = new URL(window.location.href);
            url.searchParams.delete('audio');
            window.history.replaceState({}, '', url);
            
            // Remove any highlighted items
            const highlightedItems = document.querySelectorAll('.archive-item.highlighted');
            highlightedItems.forEach(item => item.classList.remove('highlighted'));
        } else {
            // On page load (no animation), check if there's an audio parameter to scroll to
            const urlParams = new URLSearchParams(window.location.search);
            const audioKey = urlParams.get('audio');
            if (audioKey) {
                // Wait a bit for content to load, then scroll to the item
                setTimeout(() => {
                    const item = document.querySelector(`[data-audio-key="${audioKey}"]`);
                    if (item) {
                        // Ensure the year section is loaded
                        const yearSection = item.closest('.audio-year-section');
                        if (yearSection) {
                            const yearContent = yearSection.querySelector('.audio-year-content');
                            if (yearContent && yearContent.dataset.loaded === 'false') {
                                // Trigger loading by scrolling into view
                                yearSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
                            }
                        }
                        
                        // Scroll to item after a delay
                        setTimeout(() => {
                            item.scrollIntoView({ behavior: 'smooth', block: 'center' });
                            item.classList.add('highlighted');
                        }, 500);
                    }
                }, 300);
                return; // Don't scroll to top if we're scrolling to a specific item on page load
            }
        }
    }

    // Scroll to top of the page
    window.scrollTo({
        top: 0,
        behavior: animate ? 'smooth' : 'auto'
    });
}

/**
 * Updates the active state of navigation buttons
 * 
 * @param {string} sectionId - The ID of the active section
 * @private
 */
function updateActiveButton(sectionId) {
    if (!navButtons) return;

    navButtons.forEach(button => {
        const buttonSection = button.getAttribute('data-section');
        if (buttonSection === sectionId) {
            button.classList.add('active');
        } else {
            button.classList.remove('active');
        }
    });
}

/**
 * Gets the currently active section ID
 * 
 * @returns {string|null} The active section ID, or null if no section is active
 * 
 * @example
 * const currentSection = getActiveSection();
 * console.log(`Currently viewing: ${currentSection}`);
 */
export function getActiveSection() {
    return activeSection;
}

/**
 * Initialises navigation based on URL hash (for direct links)
 * 
 * Checks if there's a hash in the URL and switches to that section on page load.
 * Should be called after initNavigation().
 * 
 * @example
 * initNavigation();
 * initHashNavigation();
 */
export function initHashNavigation() {
    const hash = window.location.hash.slice(1);
    if (hash) {
        // Small delay to ensure DOM is ready
        setTimeout(() => {
            switchSection(hash, false);
        }, 100);
    }
}

