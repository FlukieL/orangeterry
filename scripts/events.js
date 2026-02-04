/**
 * Events Module
 * 
 * Handles loading and displaying events in a calendar format.
 * 
 * @module events
 */

/**
 * Loads events from the JSON configuration file
 * 
 * @returns {Promise<Array>} Promise that resolves with an array of event items
 * 
 * @example
 * const events = await loadEvents();
 */
export async function loadEvents() {
    try {
        const response = await fetch('data/events.json');

        if (!response.ok) {
            throw new Error(`Failed to load events: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();

        if (!data || !Array.isArray(data.events)) {
            throw new Error('Invalid events format: expected an array');
        }

        return data.events;
    } catch (error) {
        console.error('Error loading events:', error);
        return [];
    }
}

/**
 * Formats a date string for display
 * 
 * @param {string} dateString - Date string in YYYY-MM-DD format
 * @returns {Object} Object with formatted date parts
 * @private
 */
function formatDate(dateString) {
    const date = new Date(dateString + 'T00:00:00');
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];

    return {
        day: date.getDate(),
        dayName: days[date.getDay()],
        month: months[date.getMonth()],
        monthIndex: date.getMonth(),
        year: date.getFullYear(),
        date: date
    };
}

/**
 * Generates a Google Calendar URL for an event
 * 
 * @param {Object} event - Event object with date, time, title, description, and location
 * @returns {string} Google Calendar URL
 * @private
 */
function generateGoogleCalendarUrl(event) {
    // Parse date and time
    const dateStr = event.date; // YYYY-MM-DD format
    const timeStr = event.time || '00:00'; // HH:MM format or default to midnight

    // Create start date/time
    const [hours, minutes] = timeStr.split(':').map(Number);
    const startDate = new Date(dateStr + 'T' + String(hours).padStart(2, '0') + ':' + String(minutes).padStart(2, '0') + ':00');

    // Default to 1 hour duration if no end time specified
    const endDate = new Date(startDate);
    endDate.setHours(endDate.getHours() + 1);

    // Format dates for Google Calendar (YYYYMMDDTHHMMSSZ in UTC)
    const formatGoogleDate = (date) => {
        const year = date.getUTCFullYear();
        const month = String(date.getUTCMonth() + 1).padStart(2, '0');
        const day = String(date.getUTCDate()).padStart(2, '0');
        const hour = String(date.getUTCHours()).padStart(2, '0');
        const minute = String(date.getUTCMinutes()).padStart(2, '0');
        const second = String(date.getUTCSeconds()).padStart(2, '0');
        return `${year}${month}${day}T${hour}${minute}${second}Z`;
    };

    const start = formatGoogleDate(startDate);
    const end = formatGoogleDate(endDate);

    // Build event details with website link
    const websiteUrl = 'https://flukiel.github.io/orangeterry';
    let details = event.description || '';
    if (details) {
        details += '\n\n';
    }
    details += websiteUrl;

    // Build Google Calendar URL
    const params = new URLSearchParams({
        action: 'TEMPLATE',
        text: event.title || '',
        dates: `${start}/${end}`,
        details: details,
        location: event.location || ''
    });

    return `https://calendar.google.com/calendar/render?${params.toString()}`;
}

/**
 * Groups events by date
 * 
 * @param {Array} events - Array of event objects
 * @returns {Object} Object with dates as keys and arrays of events as values
 * @private
 */
function groupEventsByDate(events) {
    const grouped = {};

    events.forEach(event => {
        if (!grouped[event.date]) {
            grouped[event.date] = [];
        }
        grouped[event.date].push(event);
    });

    return grouped;
}

/**
 * Renders the calendar with events
 * 
 * @param {Array} events - Array of event objects
 * @param {HTMLElement} container - Container element to render the calendar into
 * 
 * @example
 * renderCalendar(events, document.getElementById('calendar-container'));
 */
export function renderCalendar(events, container, sortOrder = 'asc') {
    if (!container) {
        console.warn('Calendar container not found');
        return;
    }

    // Clear existing content
    container.innerHTML = '';

    if (events.length === 0) {
        container.innerHTML = '<div class="no-events">No events scheduled</div>';
        return;
    }

    // Group events by date
    const eventsByDate = groupEventsByDate(events);

    // Sort events by date
    let sortedDates = Object.keys(eventsByDate).sort();
    if (sortOrder === 'desc') {
        sortedDates.reverse();
    }

    // Create calendar grid
    const calendarGrid = document.createElement('div');
    calendarGrid.className = 'calendar-grid';

    sortedDates.forEach(dateString => {
        const dateInfo = formatDate(dateString);
        const dateEvents = eventsByDate[dateString];

        // Create calendar day card
        const dayCard = document.createElement('div');
        dayCard.className = 'calendar-day';

        // Add date header
        const dateHeader = document.createElement('div');
        dateHeader.className = 'calendar-day-header';
        dateHeader.innerHTML = `
            <div class="calendar-day-number">${dateInfo.day}</div>
            <div class="calendar-day-info">
                <div class="calendar-day-name">${dateInfo.dayName}</div>
                <div class="calendar-day-month">${dateInfo.month}</div>
                <div class="calendar-day-year">${dateInfo.year}</div>
            </div>
        `;
        dayCard.appendChild(dateHeader);

        // Add events for this day
        const eventsList = document.createElement('div');
        eventsList.className = 'calendar-events';

        dateEvents.forEach(event => {
            const eventCard = document.createElement('div');
            eventCard.className = `calendar-event calendar-event-${event.type || 'default'}`;

            const googleCalendarUrl = generateGoogleCalendarUrl(event);

            // Make the event card clickable
            // Make the event card clickable
            eventCard.addEventListener('click', (e) => {
                // Don't navigate if clicking any link or button inside
                if (!e.target.closest('a') && !e.target.closest('button')) {
                    const targetUrl = event.setLink || 'https://weekendradio.co.uk/';
                    window.open(targetUrl, '_blank', 'noopener,noreferrer');
                }
            });
            eventCard.style.cursor = 'pointer';

            const setLinkHtml = event.setLink ? `
                <a href="${event.setLink}" target="_blank" rel="noopener noreferrer" class="event-calendar-button event-set-button" aria-label="Listen">
                    <span class="event-calendar-icon">🎧</span>
                    <span class="event-calendar-text">Listen</span>
                </a>
            ` : '';

            eventCard.innerHTML = `
                <div class="event-time">${event.time || 'All Day'}</div>
                <div class="event-title">${event.title}</div>
                ${event.location ? `<div class="event-location">${event.location}</div>` : ''}
                ${event.description ? `<div class="event-description">${event.description}</div>` : ''}
                <div class="event-actions">
                    ${setLinkHtml}
                    <a href="${googleCalendarUrl}" target="_blank" rel="noopener noreferrer" class="event-calendar-button" aria-label="Add to Google Calendar">
                        <span class="event-calendar-icon">📅</span>
                        <span class="event-calendar-text">Add to Google Calendar</span>
                    </a>
                </div>
            `;

            eventsList.appendChild(eventCard);
        });

        dayCard.appendChild(eventsList);
        calendarGrid.appendChild(dayCard);
    });

    container.appendChild(calendarGrid);
}

/**
 * Loads and displays events in the calendar
 * 
 * @example
 * loadAndDisplayEvents();
 */
export async function loadAndDisplayEvents() {
    const calendarContainer = document.getElementById('calendar-container');
    const pastContainer = document.getElementById('past-events-container');
    const pastToggle = document.getElementById('past-events-toggle');

    if (!calendarContainer) {
        console.warn('Calendar container not found');
        return;
    }

    // Show loading state
    calendarContainer.innerHTML = '<div class="loading">Loading events...</div>';

    try {
        const events = await loadEvents();

        // Filter events
        const now = new Date();
        // Create a date for "start of today" to properly categorize today's events as upcoming
        const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());

        const upcomingEvents = [];
        const pastEvents = [];

        events.forEach(event => {
            const eventDate = new Date(event.date + 'T00:00:00');
            if (eventDate < today) {
                pastEvents.push(event);
            } else {
                upcomingEvents.push(event);
            }
        });

        // Render upcoming events (ascending order - default behaviour of renderCalendar sort)
        renderCalendar(upcomingEvents, calendarContainer, 'asc');

        // Render past events if container exists
        if (pastContainer) {
            // Sort past events descending (newest first)
            renderCalendar(pastEvents, pastContainer, 'desc');

            // Allow user to reverse content of pastContainer? 
            // No, the grouping is by date.

            // Setup toggle
            if (pastToggle) {
                pastToggle.addEventListener('click', () => {
                    pastContainer.classList.toggle('hidden');
                    pastToggle.classList.toggle('active');
                });
            }
        }

    } catch (error) {
        console.error('Error loading events:', error);
        calendarContainer.innerHTML = '<div class="error-message">Error loading events. Please try again later.</div>';
    }
}

