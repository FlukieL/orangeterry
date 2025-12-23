/**
 * Embeds Module
 * 
 * Manages native JavaScript embed APIs (Twitch, Mixcloud) and iframe embeds
 * (Kick, hearthis.at, VK Video) for live streams and archives.
 * 
 * @module embeds
 */

/**
 * Twitch embed instance
 * @type {Object|null}
 */
let twitchEmbed = null;

/**
 * Mixcloud widget instances
 * @type {Map<string, Object>}
 */
const mixcloudWidgets = new Map();

/**
 * Adds the English language parameter to VK embed URLs
 * 
 * @param {string} embedUrl - The VK embed URL
 * @returns {string} The embed URL with lang=en parameter added
 * 
 * @example
 * addVkLanguageParam('https://vk.com/video_ext.php?oid=123&id=456');
 * // Returns: 'https://vk.com/video_ext.php?oid=123&id=456&lang=en'
 */
function addVkLanguageParam(embedUrl) {
    if (!embedUrl || typeof embedUrl !== 'string') {
        return embedUrl;
    }
    
    // Check if it's a VK embed URL
    if (embedUrl.includes('vk.com/video_ext.php') || embedUrl.includes('vkvideo.ru/video_ext.php')) {
        // Check if lang parameter already exists
        if (embedUrl.includes('lang=')) {
            return embedUrl;
        }
        
        // Add lang=en parameter
        const separator = embedUrl.includes('?') ? '&' : '?';
        return `${embedUrl}${separator}lang=en`;
    }
    
    return embedUrl;
}

/**
 * Initialises the Twitch embed using the native Twitch.Embed API
 * 
 * @param {string} channel - The Twitch channel name
 * @param {string} containerId - The ID of the container element
 * @param {Object} [options={}] - Additional options for the embed
 * @param {number} [options.width=1280] - Width of the embed
 * @param {number} [options.height=720] - Height of the embed
 * 
 * @example
 * initTwitchEmbed('flukie', 'twitch-embed', { width: 1280, height: 720 });
 */
export function initTwitchEmbed(channel, containerId, options = {}) {
    const container = document.getElementById(containerId);
    
    if (!container) {
        console.warn(`Twitch Embed: Container "${containerId}" not found`);
        return;
    }

    // Check if Twitch Embed API is loaded
    if (typeof Twitch === 'undefined' || !Twitch.Embed) {
        console.error('Twitch Embed API not loaded. Make sure https://embed.twitch.tv/embed/v1.js is included.');
        return;
    }

    try {
        const embedOptions = {
            width: options.width || 1280,
            height: options.height || 720,
            channel: channel,
            layout: 'video', // Show only video, no chat
            parent: [window.location.hostname],
            ...options
        };

        twitchEmbed = new Twitch.Embed(containerId, embedOptions);

        // Listen for ready event
        twitchEmbed.addEventListener(Twitch.Embed.VIDEO_READY, () => {
            console.log('Twitch embed ready');
        });

        console.log('Twitch embed initialised');
    } catch (error) {
        console.error('Error initialising Twitch embed:', error);
    }
}

/**
 * Initialises a Mixcloud widget using the native Mixcloud.PlayerWidget API
 * 
 * @param {string} feedUrl - The Mixcloud feed URL
 * @param {string} containerId - The ID of the container element
 * @param {string} [widgetId] - Optional unique ID for this widget instance
 * @returns {Object|null} The Mixcloud widget instance, or null if initialisation failed
 * 
 * @example
 * const widget = initMixcloudWidget('https://www.mixcloud.com/FlukieL/', 'mixcloud-container-1', 'widget-1');
 */
export function initMixcloudWidget(feedUrl, containerId, widgetId = null) {
    const container = document.getElementById(containerId);
    
    if (!container) {
        console.warn(`Mixcloud Widget: Container "${containerId}" not found`);
        return null;
    }

    // Check if Mixcloud Widget API is loaded
    if (typeof Mixcloud === 'undefined' || !Mixcloud.PlayerWidget) {
        console.error('Mixcloud Widget API not loaded. Make sure the Mixcloud widget script is included.');
        // Fallback to iframe embed
        createIframeEmbed(`https://www.mixcloud.com/widget/iframe/?feed=${encodeURIComponent(feedUrl)}`, containerId, {
            height: '120',
            title: 'Mixcloud Player'
        });
        return null;
    }

    try {
        const id = widgetId || `mixcloud-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        
        // Create iframe for Mixcloud widget
        const iframe = document.createElement('iframe');
        iframe.width = '100%';
        iframe.height = '120';
        iframe.src = `https://www.mixcloud.com/widget/iframe/?feed=${encodeURIComponent(feedUrl)}`;
        iframe.frameBorder = '0';
        iframe.allow = 'autoplay';
        iframe.id = `mixcloud-iframe-${id}`;
        
        container.appendChild(iframe);
        
        // Initialise PlayerWidget with the iframe
        const widget = Mixcloud.PlayerWidget(iframe);

        mixcloudWidgets.set(id, widget);

        // Listen for ready event
        widget.ready.then(() => {
            console.log(`Mixcloud widget "${id}" ready`);
        }).catch(error => {
            console.error(`Mixcloud widget "${id}" error:`, error);
        });

        console.log(`Mixcloud widget "${id}" initialised`);
        return widget;
    } catch (error) {
        console.error('Error initialising Mixcloud widget:', error);
        // Fallback to iframe embed
        createIframeEmbed(`https://www.mixcloud.com/widget/iframe/?feed=${encodeURIComponent(feedUrl)}`, containerId, {
            height: '120',
            title: 'Mixcloud Player'
        });
        return null;
    }
}

/**
 * Creates an iframe embed for platforms that don't have native JavaScript APIs
 * 
 * @param {string} embedUrl - The URL for the iframe src
 * @param {string} containerId - The ID of the container element
 * @param {Object} [options={}] - Additional options
 * @param {number} [options.width=1280] - Width of the iframe
 * @param {number} [options.height=720] - Height of the iframe
 * @param {string} [options.title=''] - Title attribute for accessibility
 * 
 * @example
 * createIframeEmbed('https://player.kick.com/flukie', 'kick-embed', {
 *   width: 1280,
 *   height: 720,
 *   title: 'Kick.com Live Stream'
 * });
 */
export function createIframeEmbed(embedUrl, containerId, options = {}) {
    const container = document.getElementById(containerId);
    
    if (!container) {
        console.warn(`Iframe Embed: Container "${containerId}" not found`);
        return;
    }

    // Clear existing content
    container.innerHTML = '';

    const iframe = document.createElement('iframe');
    iframe.src = embedUrl;
    iframe.width = options.width || '100%';
    iframe.height = options.height || '100%';
    iframe.frameBorder = '0';
    iframe.scrolling = 'no';
    iframe.allowFullscreen = true;
    iframe.title = options.title || '';
    iframe.style.width = '100%';
    iframe.style.height = '100%';
    iframe.style.border = 'none';
    // Store original src for later restoration
    iframe.setAttribute('data-original-src', embedUrl);

    container.appendChild(iframe);
    console.log(`Iframe embed created in "${containerId}"`);
}

/**
 * Creates an audio archive embed item
 * 
 * @param {Object} archiveItem - The archive item data from config
 * @param {string} archiveItem.platform - The platform name (mixcloud, hearthis)
 * @param {string} archiveItem.title - The title of the archive item
 * @param {string} archiveItem.url - The URL of the archive item
 * @param {string} archiveItem.embedUrl - The embed URL for the archive item
 * @param {string} archiveItem.key - The unique key for the archive item
 * @param {HTMLElement} container - The container element to append the archive item to
 * 
 * @example
 * const item = { platform: 'mixcloud', title: 'My Mix', url: '...', embedUrl: '...', key: '...' };
 * createAudioArchiveItem(item, document.getElementById('audio-archives-container'));
 */
export function createAudioArchiveItem(archiveItem, container) {
    const itemDiv = document.createElement('div');
    itemDiv.className = 'archive-item';
    if (archiveItem.key) {
        itemDiv.dataset.audioKey = archiveItem.key;
    }

    // Create header with title and share button
    const headerDiv = document.createElement('div');
    headerDiv.className = 'archive-item-header';
    
    const titleDiv = document.createElement('div');
    titleDiv.className = 'archive-title';
    titleDiv.textContent = archiveItem.title;
    headerDiv.appendChild(titleDiv);

    // Add share button
    if (archiveItem.key) {
        const shareButton = document.createElement('button');
        shareButton.type = 'button';
        shareButton.className = 'archive-item-share';
        shareButton.setAttribute('aria-label', `Share ${archiveItem.title}`);
        shareButton.innerHTML = '🔗';
        shareButton.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            shareAudioSet(archiveItem);
        });
        headerDiv.appendChild(shareButton);
    }
    
    itemDiv.appendChild(headerDiv);

    // Add date if available
    if (archiveItem.created_time) {
        const dateDiv = document.createElement('div');
        dateDiv.className = 'archive-date';
        const date = new Date(archiveItem.created_time);
        // Format as DD/MM/YYYY (British format)
        const formattedDate = date.toLocaleDateString('en-GB', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
        dateDiv.textContent = formattedDate;
        itemDiv.appendChild(dateDiv);
    }

    const embedDiv = document.createElement('div');
    embedDiv.className = 'archive-embed';
    
    const uniqueId = `audio-${archiveItem.platform}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    embedDiv.id = uniqueId;
    itemDiv.appendChild(embedDiv);

    // Make item clickable to update URL
    if (archiveItem.key) {
        itemDiv.style.cursor = 'pointer';
        itemDiv.addEventListener('click', (e) => {
            // Don't trigger if clicking on share button or embed
            if (e.target.closest('.archive-item-share') || e.target.closest('.archive-embed')) {
                return;
            }
            updateAudioSetUrl(archiveItem);
        });
    }

    container.appendChild(itemDiv);

    // Set up scroll animation observer for this item
    setupArchiveItemAnimation(itemDiv);

    // Initialise the appropriate embed based on platform
    if (archiveItem.platform === 'mixcloud') {
        initMixcloudWidget(archiveItem.url, uniqueId, uniqueId);
    } else if (archiveItem.platform === 'hearthis') {
        createIframeEmbed(archiveItem.embedUrl, uniqueId, {
            height: '150',
            title: archiveItem.title
        });
    } else {
        console.warn(`Unknown audio platform: ${archiveItem.platform}`);
    }
}

/**
 * Sets up Intersection Observer for archive item scroll animations
 * Creates a jukebox-style animation when items enter/exit the viewport
 * 
 * @param {HTMLElement} itemElement - The archive item element to animate
 * @private
 */
function setupArchiveItemAnimation(itemElement) {
    // Add initial hidden state
    itemElement.classList.add('archive-item-animate');
    
    // Create observer for this item
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // Item entering viewport - animate in
                entry.target.classList.add('archive-item-visible');
                entry.target.classList.remove('archive-item-hidden');
            } else {
                // Item leaving viewport - animate out (optional, for scroll up)
                entry.target.classList.add('archive-item-hidden');
                entry.target.classList.remove('archive-item-visible');
            }
        });
    }, {
        root: null,
        rootMargin: '50px', // Start animation slightly before entering viewport
        threshold: 0.1
    });
    
    observer.observe(itemElement);
}

/**
 * Sets up Intersection Observer for video playlist item scroll animations
 * Creates a subtle jukebox-style animation moving leftwards when items enter/exit the viewport
 * 
 * @param {HTMLElement} itemElement - The video playlist item element to animate
 * @private
 */
function setupVideoPlaylistItemAnimation(itemElement) {
    // Add initial hidden state
    itemElement.classList.add('video-playlist-item-animate');
    
    // Create observer for this item
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // Item entering viewport - animate in
                entry.target.classList.add('video-playlist-item-visible');
                entry.target.classList.remove('video-playlist-item-hidden');
            } else {
                // Item leaving viewport - animate out (optional, for scroll up)
                entry.target.classList.add('video-playlist-item-hidden');
                entry.target.classList.remove('video-playlist-item-visible');
            }
        });
    }, {
        root: null,
        rootMargin: '50px', // Start animation slightly before entering viewport
        threshold: 0.1
    });
    
    observer.observe(itemElement);
}

/**
 * Creates a video archive embed item
 * 
 * @param {Object} archiveItem - The archive item data from config
 * @param {string} archiveItem.platform - The platform name (vk)
 * @param {string} archiveItem.title - The title of the archive item
 * @param {string} archiveItem.url - The URL of the archive item
 * @param {string} archiveItem.embedUrl - The embed URL for the archive item
 * @param {HTMLElement} container - The container element to append the archive item to
 * 
 * @example
 * const item = { platform: 'vk', title: 'My Video', url: '...', embedUrl: '...' };
 * createVideoArchiveItem(item, document.getElementById('video-archives-container'));
 */
export function createVideoArchiveItem(archiveItem, container) {
    const itemDiv = document.createElement('div');
    itemDiv.className = 'archive-item';

    const titleDiv = document.createElement('div');
    titleDiv.className = 'archive-title';
    titleDiv.textContent = archiveItem.title;
    itemDiv.appendChild(titleDiv);

    const embedDiv = document.createElement('div');
    embedDiv.className = 'archive-embed';
    
    const uniqueId = `video-${archiveItem.platform}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    embedDiv.id = uniqueId;
    itemDiv.appendChild(embedDiv);

    container.appendChild(itemDiv);

    // Initialise the appropriate embed based on platform
    if (archiveItem.platform === 'vk') {
        const vkEmbedUrl = addVkLanguageParam(archiveItem.embedUrl);
        createIframeEmbed(vkEmbedUrl, uniqueId, {
            height: '360',
            title: archiveItem.title
        });
    } else {
        console.warn(`Unknown video platform: ${archiveItem.platform}`);
    }
}

/**
 * Initialises all live stream embeds
 * 
 * @param {string} kickChannel - The Kick.com channel name
 * @param {string} twitchChannel - The Twitch channel name
 * 
 * @example
 * initLiveStreams('flukie', 'flukie');
 */
export function initLiveStreams(kickChannel, twitchChannel) {
    // Initialise Kick embed (iframe)
    createIframeEmbed(`https://player.kick.com/${kickChannel}`, 'kick-embed', {
        width: '1280',
        height: '720',
        title: 'Kick.com Live Stream'
    });

    // Initialise Twitch embed (native API)
    initTwitchEmbed(twitchChannel, 'twitch-embed', {
        width: 1280,
        height: 720
    });
}

/**
 * Loads and displays audio archives from configuration, grouped by year with lazy loading
 * 
 * @param {Array} audioArchives - Array of audio archive items from config
 * 
 * @example
 * const archives = await getAudioArchives();
 * loadAudioArchives(archives);
 */
export function loadAudioArchives(audioArchives) {
    const container = document.getElementById('audio-archives-container');
    
    if (!container) {
        console.warn('Audio archives container not found');
        return;
    }

    // Clear existing content
    container.innerHTML = '';

    if (audioArchives.length === 0) {
        container.innerHTML = '<div class="loading">No audio archives available</div>';
        return;
    }

    // Sort by date (newest first) - using created_time if available
    const sortedArchives = [...audioArchives].sort((a, b) => {
        const dateA = a.created_time ? new Date(a.created_time) : new Date(0);
        const dateB = b.created_time ? new Date(b.created_time) : new Date(0);
        return dateB - dateA; // Descending order (newest first)
    });

    // Group archives by year
    const archivesByYear = new Map();
    sortedArchives.forEach(item => {
        const year = item.created_time 
            ? new Date(item.created_time).getFullYear() 
            : 'Unknown';
        
        if (!archivesByYear.has(year)) {
            archivesByYear.set(year, []);
        }
        archivesByYear.get(year).push(item);
    });

    // Create year sections
    const years = Array.from(archivesByYear.keys()).sort((a, b) => {
        if (a === 'Unknown') return 1;
        if (b === 'Unknown') return -1;
        return b - a; // Descending order (newest first)
    });

    years.forEach((year, yearIndex) => {
        const yearSection = document.createElement('div');
        yearSection.className = 'audio-year-section';
        yearSection.dataset.year = year;
        yearSection.dataset.yearIndex = yearIndex;

        const yearHeader = document.createElement('h2');
        yearHeader.className = 'audio-year-header';
        yearHeader.textContent = year;
        yearSection.appendChild(yearHeader);

        const yearContent = document.createElement('div');
        yearContent.className = 'audio-year-content';
        yearContent.dataset.loaded = 'false';
        yearSection.appendChild(yearContent);

        container.appendChild(yearSection);
    });

    // Set up Intersection Observer for lazy loading
    const observerOptions = {
        root: null,
        rootMargin: '200px', // Start loading 200px before the section comes into view
        threshold: 0.1
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const yearSection = entry.target;
                const yearContent = yearSection.querySelector('.audio-year-content');
                const year = yearSection.dataset.year;
                const loaded = yearContent.dataset.loaded === 'true';

                if (!loaded && archivesByYear.has(parseInt(year)) || year === 'Unknown') {
                    // Load content for this year
                    const yearArchives = archivesByYear.get(year === 'Unknown' ? 'Unknown' : parseInt(year));
                    
                    yearArchives.forEach((item, index) => {
                        setTimeout(() => {
                            createAudioArchiveItem(item, yearContent);
                        }, index * 50);
                    });

                    yearContent.dataset.loaded = 'true';
                    yearSection.classList.add('loaded');
                }
            }
        });
    }, observerOptions);

    // Observe all year sections
    const yearSections = container.querySelectorAll('.audio-year-section');
    yearSections.forEach(section => observer.observe(section));

    // Load first year immediately
    if (yearSections.length > 0) {
        const firstSection = yearSections[0];
        const firstYearContent = firstSection.querySelector('.audio-year-content');
        const firstYear = firstSection.dataset.year;
        const firstYearArchives = archivesByYear.get(firstYear === 'Unknown' ? 'Unknown' : parseInt(firstYear));
        
        firstYearArchives.forEach((item, index) => {
            setTimeout(() => {
                createAudioArchiveItem(item, firstYearContent);
            }, index * 50);
        });
        
        firstYearContent.dataset.loaded = 'true';
        firstSection.classList.add('loaded');
    }

    // Check URL for audio parameter and scroll to that set
    const urlParams = new URLSearchParams(window.location.search);
    const audioKey = urlParams.get('audio');
    if (audioKey) {
        // Wait for content to load, then scroll to the item
        setTimeout(() => {
            scrollToAudioSet(audioKey);
        }, 500);
    }
}

/**
 * Updates the URL with the audio set key
 * 
 * @param {Object} archiveItem - The archive item to set in the URL
 */
function updateAudioSetUrl(archiveItem) {
    if (!archiveItem.key) return;

    const url = new URL(window.location.href);
    const audioArchivesSection = document.getElementById('audio-archives');
    
    // Only update URL if audio-archives section is active
    if (audioArchivesSection && audioArchivesSection.classList.contains('active')) {
        url.searchParams.set('audio', archiveItem.key);
        window.history.replaceState({}, '', url);
        
        // Highlight the selected item
        highlightAudioSet(archiveItem.key);
    }
}

/**
 * Highlights a specific audio set
 * 
 * @param {string} audioKey - The key of the audio set to highlight
 */
function highlightAudioSet(audioKey) {
    // Remove existing highlights
    const existingHighlighted = document.querySelectorAll('.archive-item.highlighted');
    existingHighlighted.forEach(item => item.classList.remove('highlighted'));

    // Find and highlight the item
    const item = document.querySelector(`[data-audio-key="${audioKey}"]`);
    if (item) {
        item.classList.add('highlighted');
        // Scroll into view with smooth behavior
        item.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

/**
 * Scrolls to a specific audio set based on its key
 * 
 * @param {string} audioKey - The key of the audio set to scroll to
 */
function scrollToAudioSet(audioKey) {
    const item = document.querySelector(`[data-audio-key="${audioKey}"]`);
    if (item) {
        // Ensure the year section is loaded
        const yearSection = item.closest('.audio-year-section');
        if (yearSection) {
            const yearContent = yearSection.querySelector('.audio-year-content');
            if (yearContent && yearContent.dataset.loaded === 'false') {
                // Force load this year section
                const year = yearSection.dataset.year;
                // This will be handled by the observer, but we can trigger it manually
                yearSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        }
        
        // Wait a bit for content to load, then scroll to item
        setTimeout(() => {
            highlightAudioSet(audioKey);
        }, 300);
    }
}

/**
 * Shares an audio set by copying the URL to clipboard or using Web Share API
 * 
 * @param {Object} archiveItem - The archive item to share
 */
function shareAudioSet(archiveItem) {
    if (!archiveItem.key) return;

    const url = new URL(window.location.href);
    url.searchParams.set('audio', archiveItem.key);
    
    const shareUrl = url.toString();
    const shareTitle = archiveItem.title || 'Audio Set';
    const shareText = `Check out ${shareTitle} on Electric Heater Room`;

    // Try Web Share API first (mobile-friendly)
    if (navigator.share) {
        navigator.share({
            title: shareTitle,
            text: shareText,
            url: shareUrl
        }).catch((error) => {
            // User cancelled or error occurred, fall back to clipboard
            if (error.name !== 'AbortError') {
                copyToClipboard(shareUrl);
            }
        });
    } else {
        // Fall back to clipboard
        copyToClipboard(shareUrl);
    }
}

/**
 * Loads and displays video archives from configuration in YouTube-like layout, grouped by year
 * 
 * @param {Array} videoArchives - Array of video archive items from config
 * 
 * @example
 * const archives = await getVideoArchives();
 * loadVideoArchives(archives);
 */
export function loadVideoArchives(videoArchives) {
    const playerLayout = document.getElementById('video-player-layout');
    const mainPlayerContainer = document.getElementById('video-player-container');
    const playlistContainer = document.getElementById('video-playlist');
    
    if (!playerLayout || !mainPlayerContainer || !playlistContainer) {
        console.warn('Video player layout elements not found');
        return;
    }

    // Clear existing content
    playlistContainer.innerHTML = '';
    mainPlayerContainer.innerHTML = '';

    if (videoArchives.length === 0) {
        mainPlayerContainer.innerHTML = '<div class="video-placeholder">No video archives available</div>';
        return;
    }

    // Sort by date (newest first)
    const sortedArchives = [...videoArchives].sort((a, b) => {
        const dateA = a.created_time ? new Date(a.created_time) : new Date(0);
        const dateB = b.created_time ? new Date(b.created_time) : new Date(0);
        return dateB - dateA; // Descending order (newest first)
    });

    // Group archives by year
    const archivesByYear = new Map();
    sortedArchives.forEach(item => {
        const year = item.created_time 
            ? new Date(item.created_time).getFullYear() 
            : 'Unknown';
        
        if (!archivesByYear.has(year)) {
            archivesByYear.set(year, []);
        }
        archivesByYear.get(year).push(item);
    });

    // Create year sections
    const years = Array.from(archivesByYear.keys()).sort((a, b) => {
        if (a === 'Unknown') return 1;
        if (b === 'Unknown') return -1;
        return b - a; // Descending order (newest first)
    });

    // Keep track of global index for video items
    let globalIndex = 0;

    years.forEach((year, yearIndex) => {
        const yearSection = document.createElement('div');
        yearSection.className = 'video-year-section';
        yearSection.dataset.year = year;
        yearSection.dataset.yearIndex = yearIndex;

        const yearHeader = document.createElement('h3');
        yearHeader.className = 'video-year-header';
        yearHeader.textContent = year;
        yearSection.appendChild(yearHeader);

        const yearContent = document.createElement('div');
        yearContent.className = 'video-year-content';
        yearContent.dataset.loaded = 'false';
        yearSection.appendChild(yearContent);

        playlistContainer.appendChild(yearSection);

        // Create playlist items for this year
        const yearArchives = archivesByYear.get(year);
        yearArchives.forEach((item) => {
            const playlistItem = document.createElement('div');
            playlistItem.className = 'video-playlist-item';
            playlistItem.dataset.videoIndex = globalIndex;
            playlistItem.dataset.videoKey = item.key || '';
            
            // Create content wrapper
            const contentWrapper = document.createElement('div');
            contentWrapper.className = 'video-playlist-item-content';
            
            // Add title
            const titleDiv = document.createElement('div');
            titleDiv.className = 'video-playlist-item-title';
            titleDiv.textContent = item.title || 'Untitled';
            contentWrapper.appendChild(titleDiv);
            
            // Add date if available
            if (item.created_time) {
                const dateDiv = document.createElement('div');
                dateDiv.className = 'video-playlist-item-date';
                const date = new Date(item.created_time);
                // Format as DD/MM/YYYY (British format)
                const formattedDate = date.toLocaleDateString('en-GB', {
                    day: '2-digit',
                    month: '2-digit',
                    year: 'numeric'
                });
                dateDiv.textContent = formattedDate;
                contentWrapper.appendChild(dateDiv);
            }
            
            playlistItem.appendChild(contentWrapper);
            
            // Add share button
            const shareButton = document.createElement('button');
            shareButton.type = 'button';
            shareButton.className = 'video-playlist-item-share';
            shareButton.setAttribute('aria-label', `Share ${item.title || 'video'}`);
            shareButton.innerHTML = '🔗';
            shareButton.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation(); // Prevent triggering the playlist item click
                shareVideo(item, globalIndex);
            });
            playlistItem.appendChild(shareButton);
            
            // Add click handler to load video (on playlist item, not share button)
            playlistItem.addEventListener('click', (e) => {
                // Don't trigger if clicking the share button
                if (e.target.closest('.video-playlist-item-share')) {
                    return;
                }
                // Use the index from the dataset to ensure we're using the correct value
                const clickedIndex = parseInt(playlistItem.dataset.videoIndex, 10);
                loadVideoInPlayer(item, clickedIndex, sortedArchives, playlistContainer);
            });
            
            // Set up scroll animation observer for this item
            setupVideoPlaylistItemAnimation(playlistItem);
            
            yearContent.appendChild(playlistItem);
            globalIndex++;
        });

        // Mark year section as loaded
        yearSection.classList.add('loaded');
        yearContent.dataset.loaded = 'true';
    });

    // Check URL for video parameter and load that video, otherwise load first
    const urlParams = new URLSearchParams(window.location.search);
    const videoKey = urlParams.get('video');
    
    if (videoKey && sortedArchives.length > 0) {
        const videoIndex = sortedArchives.findIndex(v => v.key === videoKey);
        if (videoIndex !== -1) {
            loadVideoInPlayer(sortedArchives[videoIndex], videoIndex, sortedArchives, playlistContainer);
        } else {
            // If video key not found, load first video
            loadVideoInPlayer(sortedArchives[0], 0, sortedArchives, playlistContainer);
        }
    } else if (sortedArchives.length > 0) {
        // Load first video by default
        loadVideoInPlayer(sortedArchives[0], 0, sortedArchives, playlistContainer);
    }

    // Initialise playlist toggle button (desktop only)
    initVideoPlaylistToggle();
}

/**
 * Loads a video into the main player
 * 
 * @param {Object} videoItem - The video archive item to load
 * @param {number} index - The index of the video in the sorted array
 * @param {Array} allVideos - All video items for reference
 * @param {HTMLElement} playlistContainer - The playlist container to update active state
 */
function loadVideoInPlayer(videoItem, index, allVideos, playlistContainer) {
    const mainPlayerContainer = document.getElementById('video-player-container');
    
    if (!mainPlayerContainer) {
        console.warn('Video player container not found');
        return;
    }

    // Update active state in playlist - query from document to ensure we get all items
    const playlistItems = document.querySelectorAll('.video-playlist-item');
    
    // First, remove active class from all items
    playlistItems.forEach((item) => {
        item.classList.remove('active');
    });
    
    // Then, add active class to the selected item using the video key for more reliable matching
    const targetKey = videoItem.key;
    playlistItems.forEach((item) => {
        const itemKey = item.dataset.videoKey;
        const itemIndex = parseInt(item.dataset.videoIndex, 10);
        
        // Match by key if available, otherwise by index
        if (targetKey && itemKey === targetKey) {
            item.classList.add('active');
        } else if (!isNaN(itemIndex) && itemIndex === index) {
            item.classList.add('active');
        }
    });

    // Update URL with video key only if video-archives section is active
    const videoArchivesSection = document.getElementById('video-archives');
    if (videoItem.key && videoArchivesSection && videoArchivesSection.classList.contains('active')) {
        const url = new URL(window.location.href);
        url.searchParams.set('video', videoItem.key);
        window.history.replaceState({}, '', url);
    }

    // Clear existing player
    mainPlayerContainer.innerHTML = '';

    // Create iframe for VK video
    if (videoItem.platform === 'vk') {
        const iframe = document.createElement('iframe');
        const embedUrl = videoItem.embedUrl || videoItem.url;
        iframe.src = addVkLanguageParam(embedUrl);
        iframe.width = '100%';
        iframe.height = '100%';
        iframe.frameBorder = '0';
        iframe.allowFullscreen = true;
        iframe.title = videoItem.title || 'Video Player';
        iframe.style.position = 'absolute';
        iframe.style.top = '0';
        iframe.style.left = '0';
        iframe.style.width = '100%';
        iframe.style.height = '100%';
        iframe.style.border = 'none';
        
        mainPlayerContainer.appendChild(iframe);
    } else {
        console.warn(`Unknown video platform: ${videoItem.platform}`);
        mainPlayerContainer.innerHTML = '<div class="video-placeholder">Unsupported video platform</div>';
    }
}

/**
 * Shares a video by copying the URL to clipboard or using Web Share API
 * 
 * @param {Object} videoItem - The video archive item to share
 * @param {number} index - The index of the video in the sorted array
 */
function shareVideo(videoItem, index) {
    const url = new URL(window.location.href);
    url.searchParams.set('video', videoItem.key || '');
    
    const shareUrl = url.toString();
    const shareTitle = videoItem.title || 'Video';
    const shareText = `Check out ${shareTitle} on Electric Heater Room`;

    // Try Web Share API first (mobile-friendly)
    if (navigator.share) {
        navigator.share({
            title: shareTitle,
            text: shareText,
            url: shareUrl
        }).catch((error) => {
            // User cancelled or error occurred, fall back to clipboard
            if (error.name !== 'AbortError') {
                copyToClipboard(shareUrl);
            }
        });
    } else {
        // Fall back to clipboard
        copyToClipboard(shareUrl);
    }
}

/**
 * Copies text to clipboard and shows a brief confirmation
 * 
 * @param {string} text - The text to copy
 */
function copyToClipboard(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(() => {
            showShareConfirmation();
        }).catch(() => {
            // Fallback for older browsers
            fallbackCopyToClipboard(text);
        });
    } else {
        fallbackCopyToClipboard(text);
    }
}

/**
 * Fallback method to copy text to clipboard for older browsers
 * 
 * @param {string} text - The text to copy
 */
function fallbackCopyToClipboard(text) {
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
    
    // Focus and select the text
    textArea.focus();
    textArea.select();
    textArea.setSelectionRange(0, textArea.value.length);
    
    try {
        const successful = document.execCommand('copy');
        if (successful) {
            showShareConfirmation();
        } else {
            throw new Error('execCommand copy returned false');
        }
    } catch (err) {
        console.error('Failed to copy text:', err);
        // Show the URL in a prompt as a last resort
        const userCopied = prompt('Copy this link:', text);
        if (userCopied) {
            showShareConfirmation();
        }
    } finally {
        // Clean up - remove the textarea
        if (document.body.contains(textArea)) {
            document.body.removeChild(textArea);
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
 * Pauses the Twitch embed if it exists
 * 
 * @private
 */
function pauseTwitchEmbed() {
    if (twitchEmbed) {
        try {
            const player = twitchEmbed.getPlayer();
            if (player) {
                player.pause();
            }
        } catch (error) {
            console.warn('Error pausing Twitch embed:', error);
        }
    }
}

/**
 * Unloads all media in a given section by pausing/stopping playback
 * 
 * @param {string} sectionId - The ID of the section to unload
 * 
 * @example
 * unloadSectionMedia('audio-archives');
 */
export function unloadSectionMedia(sectionId) {
    const section = document.getElementById(sectionId);
    if (!section) {
        return;
    }

    // Handle live streams section
    if (sectionId === 'live-streams') {
        // Pause Twitch embed
        pauseTwitchEmbed();
        
        // Unload Kick iframe by removing src (store original src first)
        const kickContainer = document.getElementById('kick-embed');
        const kickIframe = kickContainer ? kickContainer.querySelector('iframe') : null;
        if (kickIframe && kickIframe.src) {
            // Store original src before clearing (only if not already stored)
            if (!kickIframe.getAttribute('data-original-src')) {
                kickIframe.setAttribute('data-original-src', kickIframe.src);
            }
            kickIframe.src = '';
        }
        
        // Unload Twitch iframe by removing src
        const twitchContainer = document.getElementById('twitch-embed');
        if (twitchContainer) {
            const twitchIframe = twitchContainer.querySelector('iframe');
            if (twitchIframe && twitchIframe.src) {
                // Store original src before clearing (only if not already stored)
                if (!twitchIframe.getAttribute('data-original-src')) {
                    twitchIframe.setAttribute('data-original-src', twitchIframe.src);
                }
                twitchIframe.src = '';
            }
        }
        return;
    }

    // Handle audio archives section
    if (sectionId === 'audio-archives') {
        // Pause all Mixcloud widgets
        mixcloudWidgets.forEach((widget, widgetId) => {
            try {
                widget.pause();
            } catch (error) {
                console.warn(`Error pausing Mixcloud widget "${widgetId}":`, error);
            }
        });

        // Unload all iframes in audio archives - store original src before clearing
        const iframes = section.querySelectorAll('iframe');
        iframes.forEach(iframe => {
            const currentSrc = iframe.src;
            if (currentSrc && currentSrc !== 'about:blank' && currentSrc !== window.location.href) {
                // Store original src in data attribute (only if not already stored)
                if (!iframe.getAttribute('data-original-src')) {
                    iframe.setAttribute('data-original-src', currentSrc);
                }
                // Clear the src to stop playback
                iframe.src = 'about:blank';
            }
        });
        return;
    }

    // Handle video archives section
    if (sectionId === 'video-archives') {
        // Unload the main video player iframe
        const mainPlayerContainer = document.getElementById('video-player-container');
        if (mainPlayerContainer) {
            const iframe = mainPlayerContainer.querySelector('iframe');
            if (iframe) {
                const currentSrc = iframe.src;
                if (currentSrc && currentSrc !== 'about:blank' && currentSrc !== window.location.href) {
                    // Store original src in data attribute (only if not already stored)
                    if (!iframe.getAttribute('data-original-src')) {
                        iframe.setAttribute('data-original-src', currentSrc);
                    }
                    // Clear the src to stop playback
                    iframe.src = 'about:blank';
                }
            }
        }
        return;
    }
}

/**
 * Reloads all media in a given section by restoring iframe sources
 * 
 * @param {string} sectionId - The ID of the section to reload
 * 
 * @example
 * reloadSectionMedia('audio-archives');
 */
export function reloadSectionMedia(sectionId) {
    const section = document.getElementById(sectionId);
    if (!section) {
        return;
    }

    // Handle live streams section
    if (sectionId === 'live-streams') {
        // Small delay to ensure section is visible before reloading streams
        setTimeout(() => {
            // Dynamically import getActiveStream to avoid circular dependency
            import('./stream-controls.js').then(({ getActiveStream }) => {
                const activeStream = getActiveStream();
                
                // Reload the currently active stream - always force a refresh
                if (activeStream === 'kick') {
                    const kickContainer = document.getElementById('kick-embed');
                    if (kickContainer) {
                        const kickIframe = kickContainer.querySelector('iframe');
                        let originalSrc = null;
                        
                        // Get original src from iframe or use default
                        if (kickIframe) {
                            originalSrc = kickIframe.getAttribute('data-original-src');
                            if (!originalSrc && kickIframe.src && kickIframe.src !== '' && kickIframe.src !== 'about:blank' && kickIframe.src.includes('kick.com')) {
                                originalSrc = kickIframe.src;
                            }
                        }
                        
                        // If no original src found, use default
                        if (!originalSrc) {
                            const kickChannel = 'flukie';
                            originalSrc = `https://player.kick.com/${kickChannel}`;
                        }
                        
                        // Remove existing iframe and recreate to force refresh
                        kickContainer.innerHTML = '';
                        
                        // Create new iframe with fresh src
                        const newIframe = document.createElement('iframe');
                        newIframe.src = originalSrc;
                        newIframe.width = '1280';
                        newIframe.height = '720';
                        newIframe.frameBorder = '0';
                        newIframe.scrolling = 'no';
                        newIframe.allowFullscreen = true;
                        newIframe.title = 'Kick.com Live Stream';
                        newIframe.style.width = '100%';
                        newIframe.style.height = '100%';
                        newIframe.style.border = 'none';
                        newIframe.setAttribute('data-original-src', originalSrc);
                        
                        kickContainer.appendChild(newIframe);
                    }
                } else if (activeStream === 'twitch') {
                    const twitchContainer = document.getElementById('twitch-embed');
                    if (twitchContainer) {
                        // Always reinitialise Twitch embed to ensure fresh connection
                        // Clear the container first
                        twitchContainer.innerHTML = '';
                        // Reset the twitchEmbed reference
                        twitchEmbed = null;
                        
                        // Reinitialise Twitch embed
                        const twitchChannel = 'flukie';
                        initTwitchEmbed(twitchChannel, 'twitch-embed', {
                            width: 1280,
                            height: 720
                        });
                    }
                }
            }).catch(error => {
                console.error('Error reloading live streams:', error);
            });
        }, 100);
        return;
    }

    // Handle audio archives section
    if (sectionId === 'audio-archives') {
        // Reload all iframes in audio archives from stored src
        const iframes = Array.from(section.querySelectorAll('iframe'));
        iframes.forEach((iframe) => {
            const originalSrc = iframe.getAttribute('data-original-src');
            const currentSrc = iframe.src;
            
            // If we have a stored original src, use it
            if (originalSrc) {
                const needsReload = !currentSrc || 
                                   currentSrc === '' || 
                                   currentSrc === 'about:blank' ||
                                   currentSrc === window.location.href;
                
                if (needsReload) {
                    // Store iframe attributes
                    const width = iframe.width || iframe.getAttribute('width') || '100%';
                    const height = iframe.height || iframe.getAttribute('height') || '120';
                    const frameBorder = iframe.frameBorder || iframe.getAttribute('frameborder') || '0';
                    const allow = iframe.allow || iframe.getAttribute('allow') || '';
                    const title = iframe.title || iframe.getAttribute('title') || '';
                    const id = iframe.id || '';
                    const style = iframe.getAttribute('style') || '';
                    
                    // Create new iframe with same attributes
                    const newIframe = document.createElement('iframe');
                    newIframe.width = width;
                    newIframe.height = height;
                    newIframe.frameBorder = frameBorder;
                    if (allow) newIframe.allow = allow;
                    if (title) newIframe.title = title;
                    if (id) newIframe.id = id;
                    if (style) newIframe.setAttribute('style', style);
                    newIframe.setAttribute('data-original-src', originalSrc);
                    
                    // Replace old iframe with new one
                    const parent = iframe.parentNode;
                    if (parent) {
                        parent.replaceChild(newIframe, iframe);
                        
                        // Set src after a small delay to ensure DOM is ready
                        setTimeout(() => {
                            newIframe.src = originalSrc;
                        }, 10);
                    }
                } else if (currentSrc !== originalSrc) {
                    // If src exists but is different, restore it
                    iframe.src = originalSrc;
                }
            } else if (!currentSrc || currentSrc === '' || currentSrc === 'about:blank') {
                // If no stored src but iframe is empty, this shouldn't happen
                // but we'll log it for debugging
                console.warn('Audio archive iframe has no src and no stored original src');
            }
        });
        return;
    }

    // Handle video archives section
    if (sectionId === 'video-archives') {
        // Reload the main video player iframe from stored src
        const mainPlayerContainer = document.getElementById('video-player-container');
        if (mainPlayerContainer) {
            const iframe = mainPlayerContainer.querySelector('iframe');
            if (iframe) {
                const originalSrc = iframe.getAttribute('data-original-src');
                const currentSrc = iframe.src;
                
                // If we have a stored original src, use it
                if (originalSrc) {
                    const needsReload = !currentSrc || 
                                       currentSrc === '' || 
                                       currentSrc === 'about:blank' ||
                                       currentSrc === window.location.href;
                    
                    if (needsReload) {
                        // Store iframe attributes
                        const width = iframe.width || iframe.getAttribute('width') || '100%';
                        const height = iframe.height || iframe.getAttribute('height') || '100%';
                        const frameBorder = iframe.frameBorder || iframe.getAttribute('frameborder') || '0';
                        const allow = iframe.allow || iframe.getAttribute('allow') || '';
                        const title = iframe.title || iframe.getAttribute('title') || '';
                        const id = iframe.id || '';
                        const style = iframe.getAttribute('style') || '';
                        
                        // Create new iframe with same attributes
                        const newIframe = document.createElement('iframe');
                        newIframe.width = width;
                        newIframe.height = height;
                        newIframe.frameBorder = frameBorder;
                        if (allow) newIframe.allow = allow;
                        if (title) newIframe.title = title;
                        if (id) newIframe.id = id;
                        if (style) newIframe.setAttribute('style', style);
                        newIframe.setAttribute('data-original-src', originalSrc);
                        
                        // Replace old iframe with new one
                        const parent = iframe.parentNode;
                        if (parent) {
                            parent.replaceChild(newIframe, iframe);
                            
                            // Set src after a small delay to ensure DOM is ready
                            setTimeout(() => {
                                newIframe.src = originalSrc;
                            }, 10);
                        }
                    } else if (currentSrc !== originalSrc) {
                        // If src exists but is different, restore it
                        iframe.src = originalSrc;
                    }
                } else if (!currentSrc || currentSrc === '' || currentSrc === 'about:blank') {
                    // If no stored src but iframe is empty, this shouldn't happen
                    // but we'll log it for debugging
                    console.warn('Video archive iframe has no src and no stored original src');
                }
            }
        }
        return;
    }
}

/**
 * Unloads a specific stream (Kick or Twitch) by clearing its iframe src
 * 
 * @param {string} stream - The stream to unload ('kick' or 'twitch')
 * 
 * @example
 * unloadStream('twitch');
 */
export function unloadStream(stream) {
    if (stream === 'twitch') {
        pauseTwitchEmbed();
        const twitchContainer = document.getElementById('twitch-embed');
        if (twitchContainer) {
            // Clear the container to fully unload the embed
            twitchContainer.innerHTML = '';
            // Reset the twitchEmbed reference
            twitchEmbed = null;
        }
    } else if (stream === 'kick') {
        const kickIframe = document.querySelector('#kick-embed iframe');
        if (kickIframe && kickIframe.src) {
            // Store original src before clearing
            kickIframe.setAttribute('data-original-src', kickIframe.src);
            kickIframe.src = '';
        }
    }
}

/**
 * Checks if the current device is a mobile device
 * 
 * @returns {boolean} True if mobile device, false otherwise
 * @private
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

/**
 * Checks if the device is in landscape orientation
 * 
 * @returns {boolean} True if landscape, false if portrait
 * @private
 */
function isLandscape() {
    return window.innerWidth > window.innerHeight;
}

/**
 * Initialises the video playlist toggle button
 * Similar to how chat toggle works in live streams
 * 
 * @private
 */
function initVideoPlaylistToggle() {
    const playlistToggle = document.getElementById('video-playlist-toggle');
    const playlistWrapper = document.getElementById('video-playlist-wrapper');
    const videoArchivesSection = document.getElementById('video-archives');
    
    if (!playlistToggle || !playlistWrapper || !videoArchivesSection) {
        return;
    }

    // Toggle playlist wrapper collapsed state
    playlistToggle.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        toggleVideoPlaylistWrapper();
    });
    
    // Initialise playlist wrapper as collapsed by default on landscape mobile devices only
    // Keep expanded by default on portrait (vertical) mobile
    if (isMobileDevice() && isLandscape()) {
        playlistWrapper.classList.add('collapsed');
    }
}

/**
 * Toggles the video playlist wrapper expand/collapse state
 * Similar to toggleChatWrapper for live streams
 * 
 * @private
 */
function toggleVideoPlaylistWrapper() {
    const playlistWrapper = document.getElementById('video-playlist-wrapper');
    
    if (!playlistWrapper) {
        return;
    }

    const isCollapsed = playlistWrapper.classList.contains('collapsed');
    
    if (isCollapsed) {
        playlistWrapper.classList.remove('collapsed');
    } else {
        playlistWrapper.classList.add('collapsed');
    }
}

