# Orange Terry

A modern website for showcasing DJ sets and managing an events calendar. Features audio archives from Mixcloud and an interactive events calendar.

## Features

### Audio Sets
- **Audio Archives**: Browse and play audio sets from Mixcloud
- **JSON-Based Configuration**: Easy content management via JSON files
- **Dynamic Loading**: Content loaded dynamically from configuration files
- **Embedded Players**: Play sets directly in the browser using Mixcloud's widget API

### Events Calendar
- **Calendar View**: Visual calendar displaying upcoming events
- **Event Types**: Support for streams, releases, and special events
- **JSON Storage**: Events stored in `data/events.json` for easy updates

### Interactive Logo
- **Random Animations**: Multiple different animations
- **Auto-Play**: Animation on page load and at regular intervals
- **Click to Animate**: Click the logo to trigger a random animation

### Design
- **Dark Theme**: Black background with orange accent colours matching the logo
- **Fluid Animations**: Smooth transitions between sections
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Modern UI**: Clean, minimalist interface with hover effects

### External Links
- **WeekendRadio.co.uk**: Link to Weekend Radio website
- **Instagram**: Link to Instagram profile

## Project Structure

```
orangeterry/
├── assets/
│   ├── EHRLogo.png          # Legacy logo image
│   └── logos/                # Optimised logo variants
├── data/
│   ├── archives.json         # Audio sets configuration
│   └── events.json           # Events calendar data
├── scripts/
│   ├── config.js             # Configuration loader
│   ├── embeds.js             # Archive embed management
│   ├── events.js             # Events calendar functionality
│   ├── fetch_mixcloud.py     # Python script to fetch Mixcloud content
│   ├── fetch_vk_videos.py    # Python script to fetch VK Video content
│   ├── generate_favicon.py   # Python script to generate favicon files
│   ├── generate_logo_optimized.py  # Logo optimisation script
│   ├── logo-animations.js    # Logo animation system
│   ├── main.js               # Main application initialisation
│   ├── navigation.js         # Section navigation and animations
│   ├── stream-controls.js    # Legacy stream controls (if needed)
│   └── update_vk_titles.py   # Python script to update VK video titles
├── styles/
│   └── main.css              # Main stylesheet
├── server.py                 # Python Waitress server (recommended)
├── server_waitress.py        # Alternative Waitress server implementation
├── requirements.txt          # Python dependencies
├── manifest.json             # Web app manifest
├── index.html                # Main HTML file
├── OrangeTerryLogo.jpg       # Main logo image
└── favicon files             # Various favicon sizes and formats
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
Upload all files to your GitHub Pages repository or use GitHub Actions for automatic deployment.

**Manual Deployment:**
1. Upload all files to your web server
2. Ensure the server supports serving static files
3. Configure appropriate MIME types for JSON files

## Utility Scripts

### Fetching Content

**Mixcloud:**
```bash
python scripts/fetch_mixcloud.py [mixcloud_username] [hearthis_username]
```
Example:
```bash
python scripts/fetch_mixcloud.py Orangeterry
```
This script fetches uploads from Mixcloud and updates `data/archives.json`.

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

**Generate Optimised Logos:**
```bash
python scripts/generate_logo_optimized.py
```
Generates optimised logo variants in multiple sizes and formats.

## Configuration

### Audio Sets

Edit `data/archives.json` to manage audio sets:

```json
{
  "audio": [
    {
      "platform": "mixcloud",
      "title": "Your Mix Title",
      "url": "https://www.mixcloud.com/YourUsername/",
      "embedUrl": "https://www.mixcloud.com/widget/iframe/?feed=...",
      "key": "/YourUsername/your-mix/",
      "created_time": "2023-01-01T12:00:00Z",
      "play_count": 100,
      "listener_count": 50,
      "favorite_count": 10,
      "repost_count": 5
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
      "type": "event"
    }
  ]
}
```

**Event Types:**
- `stream`: Live streaming events (orange border)
- `release`: Music releases (green border)
- `event`: Special events (blue border)

**Date Format:** Use `YYYY-MM-DD` format for dates

## Usage

### Navigation
- Click navigation buttons in the header to switch between sections
- Smooth animations transition between sections
- Direct links to WeekendRadio.co.uk and Instagram

### Audio Sets
- Browse sets in grid format
- Click on sets to play them in embedded Mixcloud players
- Sets are sorted by creation date (newest first)

### Events
- View upcoming events in calendar format
- Events are sorted chronologically
- Each event shows date, time, location, and description

### Logo Animations
- Logo animates automatically on page load
- New animation at regular intervals
- Click the logo to trigger a random animation

## Technical Details

### Technologies
- **HTML5**: Semantic markup
- **CSS3**: Modern styling with CSS Grid, Flexbox, and animations
- **Vanilla JavaScript**: No external dependencies (except platform SDKs)
- **ES6 Modules**: Modular JavaScript architecture

### External Dependencies
- **Mixcloud Widget API**: `https://widget.mixcloud.com/media/js/widgetApi.js`
- **Google Fonts**: Montserrat font family

### Python Dependencies
- **waitress**: Production-ready WSGI server (for `server.py`)
- **Pillow**: Image processing for utility scripts
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
- Grid layouts: Update `grid-template-columns` in relevant sections
- Responsive breakpoints: Adjust media queries in `styles/main.css`

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

- Logo: Orange Terry
- Design: Custom dark theme with orange accents
- Audio Platform: Mixcloud
- Font: Montserrat (Google Fonts)

## Support

For issues or questions, please check:
- Browser console for JavaScript errors
- Network tab for failed resource loads
- JSON file syntax for configuration errors

---

**Orange Terry** - Your destination for DJ sets and music archives.
