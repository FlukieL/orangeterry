/**
 * Chat Initialisation Module
 * 
 * Handles dynamic initialisation of chat iframes with correct parent parameters.
 * 
 * @module chat-init
 */

/**
 * Initialises chat iframes with correct parent parameters
 * 
 * Updates the src attributes of chat iframes to include the parent parameter
 * for proper embedding (required by Twitch).
 * 
 * @example
 * initChatEmbeds();
 */
export function initChatEmbeds() {
    const twitchChat = document.getElementById('twitch-chat');
    
    if (twitchChat) {
        // Get current hostname for parent parameter
        const hostname = window.location.hostname;
        const protocol = window.location.protocol;
        
        // Build parent parameter - include both current hostname and common localhost variants
        const parentParams = [];
        if (hostname === 'localhost' || hostname === '127.0.0.1') {
            parentParams.push('localhost', '127.0.0.1');
        } else {
            parentParams.push(hostname);
        }
        
        // Update Twitch chat iframe src with parent parameter and dark mode
        const twitchChatUrl = `https://www.twitch.tv/embed/flukie/chat?parent=${parentParams.join('&parent=')}&darkpopout`;
        twitchChat.src = twitchChatUrl;
        
        console.log('Twitch chat embed initialised with URL:', twitchChatUrl);
    }
}


