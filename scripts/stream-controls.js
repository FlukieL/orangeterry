/**
 * Stream Controls Module
 * 
 * Handles tab switching between Kick and Twitch streams, and chat wrapper toggle.
 * 
 * @module stream-controls
 */

import { unloadStream, initTwitchEmbed, createIframeEmbed } from './embeds.js';

/**
 * Currently active stream tab
 * @type {string}
 */
let activeStream = 'kick';

/**
 * Initialises stream controls (tab switching and chat wrapper)
 * 
 * Sets up event listeners for:
 * - Stream tab buttons to switch between Kick and Twitch
 * - Chat wrapper toggle button
 * 
 * @example
 * initStreamControls();
 */
export function initStreamControls() {
    // Stream tab switching
    const kickTab = document.getElementById('kick-tab');
    const twitchTab = document.getElementById('twitch-tab');
    const kickPlayer = document.getElementById('kick-player');
    const twitchPlayer = document.getElementById('twitch-player');
    
    if (kickTab && twitchTab) {
        kickTab.addEventListener('click', () => {
            switchStream('kick');
        });
        
        twitchTab.addEventListener('click', () => {
            switchStream('twitch');
        });
    }

    // Chat wrapper toggle
    const chatToggle = document.getElementById('chat-toggle');
    const chatWrapper = document.getElementById('chat-wrapper');
    
    if (chatToggle && chatWrapper) {
        chatToggle.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleChatWrapper();
        });
        
        // Initialise chat wrapper as collapsed by default on mobile devices
        if (isMobileDevice()) {
            chatWrapper.classList.add('collapsed');
        }
        // On desktop, chat starts visible alongside the player
    }

    // Stream share button - use multiple binding methods for Edge compatibility
    const streamShareButton = document.getElementById('stream-share-button');
    if (streamShareButton) {
        // Ensure button is clickable
        streamShareButton.style.pointerEvents = 'auto';
        streamShareButton.style.cursor = 'pointer';
        streamShareButton.style.userSelect = 'none';
        
        // Handler function
        const handleShareClick = (e) => {
            try {
                if (e) {
                    e.preventDefault();
                    e.stopPropagation();
                }
                shareStream();
            } catch (error) {
                console.error('Error in share button click handler:', error);
                // Fallback: try to copy URL directly
                try {
                    const currentStream = getActiveStream();
                    const url = new URL(window.location.href);
                    url.searchParams.delete('stream');
                    url.searchParams.set('stream', currentStream);
                    url.hash = '#live-streams';
                    const shareUrl = url.toString();
                    copyToClipboard(shareUrl);
                } catch (fallbackError) {
                    console.error('Fallback share also failed:', fallbackError);
                    alert('Unable to share. Please copy the URL manually: ' + window.location.href);
                }
            }
        };
        
        // Use addEventListener (standard method)
        streamShareButton.addEventListener('click', handleShareClick, false);
        
        // Also set onclick as fallback for Edge compatibility
        // (Edge sometimes has issues with addEventListener on dynamically created elements)
        streamShareButton.onclick = handleShareClick;
    } else {
        console.warn('Stream share button not found');
    }
}

/**
 * Switches between Kick and Twitch streams
 * 
 * @param {string} stream - The stream to switch to ('kick' or 'twitch')
 * 
 * @example
 * switchStream('twitch');
 */
export function switchStream(stream) {
    if (stream !== 'kick' && stream !== 'twitch') {
        console.warn(`Invalid stream: ${stream}. Must be 'kick' or 'twitch'.`);
        return;
    }

    // Don't do anything if already on this stream
    if (activeStream === stream) {
        return;
    }

    const kickTab = document.getElementById('kick-tab');
    const twitchTab = document.getElementById('twitch-tab');
    const kickPlayer = document.getElementById('kick-player');
    const twitchPlayer = document.getElementById('twitch-player');

    if (!kickTab || !twitchTab || !kickPlayer || !twitchPlayer) {
        return;
    }

    // Unload the currently active stream before switching
    if (activeStream) {
        unloadStream(activeStream);
    }

    // Update active tab
    const twitchChat = document.getElementById('twitch-chat');
    
    if (stream === 'kick') {
        kickTab.classList.add('active');
        twitchTab.classList.remove('active');
        kickPlayer.classList.add('active');
        twitchPlayer.classList.remove('active');
        
        // Always use Twitch chat for both streams
        if (twitchChat) {
            twitchChat.classList.add('active');
        }
        
        // Reload Kick stream
        const kickIframe = document.querySelector('#kick-embed iframe');
        if (kickIframe) {
            const originalSrc = kickIframe.getAttribute('data-original-src');
            if (originalSrc && (!kickIframe.src || kickIframe.src === '')) {
                kickIframe.src = originalSrc;
            } else if (!kickIframe.src || kickIframe.src === '' || !kickIframe.src.includes('kick.com')) {
                // Fallback: Get channel name from original src or use default
                const kickChannel = 'flukie'; // Could be made configurable
                kickIframe.src = `https://player.kick.com/${kickChannel}`;
            }
        }
    } else {
        twitchTab.classList.add('active');
        kickTab.classList.remove('active');
        twitchPlayer.classList.add('active');
        kickPlayer.classList.remove('active');
        
        // Switch to Twitch chat
        if (twitchChat) {
            twitchChat.classList.add('active');
            console.log('Switched to Twitch chat');
        } else {
            console.warn('Twitch chat element not found');
        }
        
        // Reload Twitch stream
        const twitchContainer = document.getElementById('twitch-embed');
        if (twitchContainer) {
            const twitchIframe = twitchContainer.querySelector('iframe');
            if (!twitchIframe || !twitchIframe.src) {
                // Reinitialize Twitch embed
                const twitchChannel = 'flukie'; // Could be made configurable
                initTwitchEmbed(twitchChannel, 'twitch-embed', {
                    width: 1280,
                    height: 720
                });
            }
        }
    }

    activeStream = stream;
}

/**
 * Toggles the chat wrapper expand/collapse state
 * 
 * @example
 * toggleChatWrapper();
 */
export function toggleChatWrapper() {
    const chatWrapper = document.getElementById('chat-wrapper');
    
    if (!chatWrapper) {
        return;
    }

    const isCollapsed = chatWrapper.classList.contains('collapsed');
    
    if (isCollapsed) {
        chatWrapper.classList.remove('collapsed');
    } else {
        chatWrapper.classList.add('collapsed');
    }
}

/**
 * Gets the currently active stream
 * 
 * @returns {string} The active stream ('kick' or 'twitch')
 * 
 * @example
 * const currentStream = getActiveStream();
 */
export function getActiveStream() {
    return activeStream;
}

/**
 * Gets the current state of the chat wrapper
 * 
 * @returns {boolean} True if expanded, false if collapsed
 * 
 * @example
 * const isExpanded = isChatWrapperExpanded();
 */
export function isChatWrapperExpanded() {
    const chatWrapper = document.getElementById('chat-wrapper');
    return chatWrapper ? !chatWrapper.classList.contains('collapsed') : false;
}

/**
 * Shares the current stream by copying the URL to clipboard or using Web Share API
 * 
 * @example
 * shareStream();
 */
export function shareStream() {
    try {
        const currentStream = getActiveStream();
        const url = new URL(window.location.href);
        
        // Remove any existing stream parameter and add the current one
        url.searchParams.delete('stream');
        url.searchParams.set('stream', currentStream);
        
        // Ensure we're on the live streams section
        url.hash = '#live-streams';
        
        const shareUrl = url.toString();
        const streamName = currentStream === 'kick' ? 'Kick' : 'Twitch';
        const shareTitle = `Electric Heater Room - ${streamName} Stream`;
        const shareText = `Watch the live stream on Electric Heater Room`;

        // Try Web Share API first (mobile-friendly)
        if (navigator.share) {
            navigator.share({
                title: shareTitle,
                text: shareText,
                url: shareUrl
            }).catch((error) => {
                // User cancelled or error occurred, fall back to clipboard
                if (error.name !== 'AbortError') {
                    console.log('Web Share API failed, falling back to clipboard:', error);
                    copyToClipboard(shareUrl);
                }
            });
        } else {
            // Fall back to clipboard
            copyToClipboard(shareUrl);
        }
    } catch (error) {
        console.error('Error in shareStream function:', error);
        // Last resort: show prompt
        try {
            const currentStream = getActiveStream();
            const url = new URL(window.location.href);
            url.searchParams.delete('stream');
            url.searchParams.set('stream', currentStream);
            url.hash = '#live-streams';
            const shareUrl = url.toString();
            copyToClipboard(shareUrl);
        } catch (fallbackError) {
            console.error('All share methods failed:', fallbackError);
            alert('Unable to share. Please copy the URL manually: ' + window.location.href);
        }
    }
}

/**
 * Copies text to clipboard and shows a brief confirmation
 * 
 * @param {string} text - The text to copy
 */
function copyToClipboard(text) {
    try {
        // Check if Clipboard API is available
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(text).then(() => {
                showShareConfirmation();
            }).catch((err) => {
                console.warn('Clipboard API failed, using fallback:', err);
                // Fallback for when Clipboard API fails
                fallbackCopyToClipboard(text);
            });
        } else {
            // Use fallback for older browsers or when Clipboard API is not available
            fallbackCopyToClipboard(text);
        }
    } catch (error) {
        console.error('Error in copyToClipboard:', error);
        fallbackCopyToClipboard(text);
    }
}

/**
 * Fallback method to copy text to clipboard for older browsers
 * 
 * @param {string} text - The text to copy
 */
function fallbackCopyToClipboard(text) {
    try {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        // Make textarea visible but off-screen for better compatibility
        textArea.style.position = 'fixed';
        textArea.style.left = '-9999px';
        textArea.style.top = '0';
        textArea.style.width = '2em';
        textArea.style.height = '2em';
        textArea.style.padding = '0';
        textArea.style.border = 'none';
        textArea.style.outline = 'none';
        textArea.style.boxShadow = 'none';
        textArea.style.background = 'transparent';
        textArea.style.opacity = '0';
        textArea.style.pointerEvents = 'none';
        textArea.setAttribute('readonly', '');
        textArea.setAttribute('aria-hidden', 'true');
        
        document.body.appendChild(textArea);
        
        // Focus and select the text - use both methods for maximum compatibility
        // For Edge, we need to ensure the element is actually focusable
        textArea.focus();
        textArea.select();
        
        // Use setSelectionRange for better Edge compatibility
        if (textArea.setSelectionRange) {
            textArea.setSelectionRange(0, textArea.value.length);
        }
        
        // Try execCommand
        let successful = false;
        try {
            successful = document.execCommand('copy');
        } catch (execError) {
            console.warn('execCommand failed:', execError);
        }
        
        // Clean up immediately
        if (document.body.contains(textArea)) {
            document.body.removeChild(textArea);
        }
        
        if (successful) {
            showShareConfirmation();
        } else {
            // If execCommand failed, try using the Clipboard API again as a last attempt
            // (sometimes it works on second try in Edge)
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(text).then(() => {
                    showShareConfirmation();
                }).catch(() => {
                    // Final fallback: show prompt
                    const userCopied = prompt('Please copy this link:', text);
                    if (userCopied !== null) {
                        showShareConfirmation();
                    }
                });
            } else {
                // Final fallback: show prompt
                const userCopied = prompt('Please copy this link:', text);
                if (userCopied !== null) {
                    showShareConfirmation();
                }
            }
        }
    } catch (err) {
        console.error('Fallback copy method failed:', err);
        // Last resort: show prompt
        const userCopied = prompt('Please copy this link:', text);
        if (userCopied !== null) {
            showShareConfirmation();
        }
    }
}

/**
 * Shows a brief confirmation message that the link was copied
 */
function showShareConfirmation() {
    // Create or update confirmation message
    let confirmation = document.getElementById('share-confirmation');
    if (!confirmation) {
        confirmation = document.createElement('div');
        confirmation.id = 'share-confirmation';
        confirmation.className = 'share-confirmation';
        confirmation.textContent = 'Link copied to clipboard!';
        document.body.appendChild(confirmation);
    }
    
    confirmation.classList.add('show');
    
    // Hide after 2 seconds
    setTimeout(() => {
        confirmation.classList.remove('show');
    }, 2000);
}

/**
 * Detects if the current device is a mobile device
 * 
 * Checks both window width and user agent to determine if device is mobile
 * 
 * @returns {boolean} True if mobile device, false otherwise
 * 
 * @example
 * if (isMobileDevice()) {
 *     // Mobile-specific code
 * }
 */
function isMobileDevice() {
    // Check window width (matches CSS media query breakpoint)
    const isMobileWidth = window.innerWidth <= 768;
    
    // Check user agent for mobile devices
    const isMobileUserAgent = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    
    // Also check for touch capability
    const hasTouchScreen = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    
    // Consider it mobile if width is small OR (user agent suggests mobile AND has touch)
    return isMobileWidth || (isMobileUserAgent && hasTouchScreen);
}
