# Electric Heater Room

A modern, animated website for streaming live DJ sets and managing audio/video archives. Features theatre-mode streaming, integrated chat, and an events calendar.

## Features

### Live Streaming
- **Dual Platform Support**: Switch between Kick and Twitch streams with tab navigation
- **Theatre Mode**: Full-screen player layout similar to Twitch.com
- **Integrated Chat**: Platform-specific chat panels that switch automatically
  - Kick chat: `https://kick.com/popout/flukie/chat`
  - Twitch chat: `https://www.twitch.tv/embed/flukie/chat`
- **Retractable Chat**: Collapsible chat sidebar with smooth animations

### Audio & Video Sets
- **Audio Sets**: Browse and play audio archives from Mixcloud and hearthis.at
- **Video Sets**: View video archives from VK Video
- **JSON-Based Configuration**: Easy content management via JSON files
- **Dynamic Loading**: Content loaded dynamically from configuration files

### Events Calendar
- **Calendar View**: Visual calendar displaying upcoming events
- **Event Types**: Support for streams, releases, and special events
- **JSON Storage**: Events stored in `data/events.json` for easy updates

### Interactive Logo
- **Random Animations**: 17 different non-spinning animations
- **Auto-Play**: Animation on page load and every 69 seconds
- **Click to Animate**: Click the logo to trigger a random animation

### Design
- **Dark Theme**: Black background with orange accent colours matching the logo
- **Fluid Animations**: Smooth transitions between sections
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Modern UI**: Clean, minimalist interface with hover effects

## Project Structure

```
ehr/
├── assets/
│   └── EHRLogo.png          # Logo image
├── data/
│   ├── archives.json        # Audio and video sets configuration
│   └── events.json          # Events calendar data
├── scripts/
│   ├── chat-init.js         # Chat embed initialisation
│   ├── config.js            # Configuration loader
│   ├── embeds.js            # Stream and archive embed management
│   ├── events.js            # Events calendar functionality
│   ├── fetch_mixcloud.py    # Python script to fetch Mixcloud/hearthis.at content
│   ├── fetch_vk_videos.py   # Python script to fetch VK Video content
│   ├── generate_favicon.py  # Python script to generate favicon files
│   ├── logo-animations.js   # Logo animation system
│   ├── main.js              # Main application initialisation
│   ├── navigation.js        # Section navigation and animations
│   ├── stream-controls.js   # Stream tab switching and chat controls
│   └── update_vk_titles.py  # Python script to update VK video titles
├── styles/
│   └── main.css             # Main stylesheet
├── .github/
│   └── workflows/
│       └── jekyll-gh-pages.yml  # GitHub Pages deployment workflow
├── server.py                # Python Waitress server (recommended)
├── server_basic.py          # Basic Python HTTP server
├── server_waitress.py        # Alternative Waitress server implementation
├── requirements.txt         # Python dependencies
├── manifest.json            # Web app manifest
├── index.html               # Main HTML file
└── favicon files            # Various favicon sizes and formats
```

## Setup

### Prerequisites
- A web server (for local development)
- Modern web browser with JavaScript enabled
- Python 3 (optional, for Python server and utility scripts)

### Installation

1. Clone or download the repository
2. Ensure all files are in the project directory
3. Start a local web server:

**Option 1: Python Waitress Server (Recommended)**
```bash
# Install dependencies
pip install -r requirements.txt

# Start the server (defaults to port 8000)
python server.py

# Or specify a custom port
python server.py 8080
```

**Option 2: Python HTTP Server**
```bash
# Using Python 3
python -m http.server 8000

# Using Python 2
python -m SimpleHTTPServer 8000
```

**Option 3: Node.js**
```bash
# Using http-server (requires installation)
npx http-server -p 8000
```

4. Open your browser and navigate to `http://localhost:8000`

The Waitress server (Option 1) is recommended as it provides better stability, error handling, and automatically opens your browser.

### Production Deployment

**GitHub Pages:**
The project includes a GitHub Actions workflow for automatic deployment to GitHub Pages. Simply push to the `main` branch and the site will be automatically built and deployed.

**Manual Deployment:**
1. Upload all files to your web server
2. Ensure the server supports serving static files
3. Update the Twitch chat embed `parent` parameter in `scripts/chat-init.js` if needed (it auto-detects the hostname)

## Utility Scripts

### Fetching Content

**Mixcloud and hearthis.at:**
```bash
python scripts/fetch_mixcloud.py [mixcloud_username] [hearthis_username]
```
Example:
```bash
python scripts/fetch_mixcloud.py FlukieL flukie
```
This script fetches uploads from both platforms and updates `data/archives.json`.

**VK Videos:**
```bash
python scripts/fetch_vk_videos.py
```
Fetches video playlists from VK and updates the video section in `data/archives.json`.

**Update VK Titles:**
```bash
python scripts/update_vk_titles.py
```
Updates video titles in the archives configuration.

**Generate Favicons:**
```bash
python scripts/generate_favicon.py
```
Generates favicon files in various sizes from a source image.

## Configuration

### Audio & Video Sets

Edit `data/archives.json` to manage audio and video sets:

```json
{
  "audio": [
    {
      "platform": "mixcloud",
      "title": "Your Mix Title",
      "url": "https://www.mixcloud.com/YourUsername/",
      "embedUrl": "https://www.mixcloud.com/widget/iframe/?feed=..."
    },
    {
      "platform": "hearthis",
      "title": "Your Track Title",
      "url": "https://hearthis.at/yourusername/",
      "embedUrl": "https://hearthis.at/yourusername/embed/"
    }
  ],
  "video": [
    {
      "platform": "vk",
      "title": "Your Video Title",
      "url": "https://vkvideo.ru/playlist/...",
      "embedUrl": "https://vk.com/video_ext.php?..."
    }
  ]
}
```

### Events

Edit `data/events.json` to manage events:

```json
{
  "events": [
    {
      "id": 1,
      "title": "Event Title",
      "date": "2025-12-20",
      "time": "20:00",
      "location": "Online",
      "description": "Event description",
      "type": "stream"
    }
  ]
}
```

**Event Types:**
- `stream`: Live streaming events (orange border)
- `release`: Music releases (green border)
- `event`: Special events (blue border)

**Date Format:** Use `YYYY-MM-DD` format for dates

### Stream Channels

To change the stream channels, edit `scripts/main.js`:

```javascript
initLiveStreams('your-kick-channel', 'your-twitch-channel');
```

### Chat URLs

To update chat URLs, edit `index.html`:
- Kick chat: Update the `src` attribute of `#kick-chat` iframe
- Twitch chat: The URL is dynamically generated in `scripts/chat-init.js`

## Usage

### Navigation
- Click navigation buttons in the header to switch between sections
- Smooth animations transition between sections

### Live Streams
- Use the "Kick" and "Twitch" tabs to switch between streams
- Click the chat toggle button (▶) to expand/collapse the chat panel
- Chat automatically switches to match the active stream

### Audio/Video Sets
- Browse sets in grid format
- Click on sets to play them in embedded players

### Events
- View upcoming events in calendar format
- Events are sorted chronologically
- Each event shows date, time, location, and description

### Logo Animations
- Logo animates automatically on page load
- New animation every 69 seconds
- Click the logo to trigger a random animation

## Technical Details

### Technologies
- **HTML5**: Semantic markup
- **CSS3**: Modern styling with CSS Grid, Flexbox, and animations
- **Vanilla JavaScript**: No external dependencies (except platform SDKs)
- **ES6 Modules**: Modular JavaScript architecture

### External Dependencies
- **Twitch Embed API**: `https://embed.twitch.tv/embed/v1.js`
- **Mixcloud Widget API**: `https://widget.mixcloud.com/media/js/widgetApi.js`

### Python Dependencies
- **waitress**: Production-ready WSGI server (for `server.py`)
  - Install with: `pip install -r requirements.txt`

### Browser Support
- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

### Performance
- Lazy loading of archive content
- Efficient DOM manipulation
- CSS animations for smooth performance
- Minimal external dependencies

## Customisation

### Colours
Edit CSS variables in `styles/main.css`:

```css
:root {
    --bg-primary: #000000;
    --text-primary: #FFFFFF;
    --accent-orange: #FF6B35;
    --accent-orange-light: #FF8C5A;
    --accent-orange-dark: #E55A2B;
}
```

### Animations
- Logo animations: Edit `styles/main.css` keyframes and `scripts/logo-animations.js`
- Section transitions: Modify `--transition-speed` and `--transition-easing` CSS variables

### Layout
- Theatre mode: Adjust `#live-streams` height in `styles/main.css`
- Chat width: Modify `.chat-wrapper` width
- Grid layouts: Update `grid-template-columns` in relevant sections

## Development

### Code Structure
- **Modular Design**: Each feature has its own module
- **JSDoc Comments**: All functions are documented
- **Separation of Concerns**: HTML, CSS, and JavaScript are separated

### Adding New Features
1. Create new module in `scripts/` directory
2. Import and initialise in `scripts/main.js`
3. Add corresponding HTML structure if needed
4. Style with CSS in `styles/main.css`

## License

This project is for personal use. All rights reserved.

## Credits

- Logo: Electric Heater Room
- Design: Custom dark theme with orange accents
- Stream Platforms: Kick.com, Twitch.tv
- Audio Platforms: Mixcloud, hearthis.at
- Video Platform: VK Video

## Support

For issues or questions, please check:
- Browser console for JavaScript errors
- Network tab for failed resource loads
- JSON file syntax for configuration errors

---

**Electric Heater Room** - Your destination for live DJ sets and music archives.

