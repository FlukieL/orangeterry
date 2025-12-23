#!/usr/bin/env python3
"""
Audio Archive Scraper
Fetches uploads from both Mixcloud and hearthis.at profiles and generates a JSON file.

Usage:
    python scripts/fetch_mixcloud.py [mixcloud_username] [hearthis_username]
    
Example:
    python scripts/fetch_mixcloud.py FlukieL flukie
"""

import json
import sys
import urllib.request
import urllib.parse
import re
from pathlib import Path
from html.parser import HTMLParser
from datetime import datetime


def fetch_mixcloud_user(username):
    """
    Fetches user profile data from Mixcloud API.
    
    Args:
        username: The Mixcloud username (e.g., 'FlukieL')
        
    Returns:
        dict: User profile data including uploads
    """
    base_url = f"https://api.mixcloud.com/{username}/"
    
    try:
        with urllib.request.urlopen(base_url) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data
    except urllib.error.HTTPError as e:
        print(f"Error fetching user data: HTTP {e.code}")
        if e.code == 404:
            print(f"User '{username}' not found on Mixcloud.")
        return None
    except Exception as e:
        print(f"Error fetching user data: {e}")
        return None


def fetch_all_uploads(username):
    """
    Fetches all uploads from a Mixcloud user profile.
    Mixcloud API uses pagination, so we need to follow 'next' links.
    
    Args:
        username: The Mixcloud username
        
    Returns:
        list: List of all upload items
    """
    uploads = []
    next_url = f"https://api.mixcloud.com/{username}/cloudcasts/"
    
    print(f"Fetching uploads for {username}...")
    
    while next_url:
        try:
            with urllib.request.urlopen(next_url) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                # Add uploads from this page
                if 'data' in data:
                    uploads.extend(data['data'])
                    print(f"  Fetched {len(data['data'])} uploads (total: {len(uploads)})")
                
                # Check for next page
                next_url = data.get('paging', {}).get('next')
                
        except Exception as e:
            print(f"Error fetching uploads: {e}")
            break
    
    print(f"Total uploads fetched: {len(uploads)}")
    return uploads


def format_archive_item(upload):
    """
    Formats a Mixcloud upload into the archive item format.
    
    Args:
        upload: Raw upload data from Mixcloud API
        
    Returns:
        dict: Formatted archive item
    """
    # Extract the key from the URL (e.g., 'FlukieL/mix-name' from 'https://www.mixcloud.com/FlukieL/mix-name/')
    url = upload.get('url', '')
    key = upload.get('key', '')
    
    # Build embed URL
    embed_url = f"https://www.mixcloud.com/widget/iframe/?feed={urllib.parse.quote(url)}"
    
    return {
        "platform": "mixcloud",
        "title": upload.get('name', 'Untitled'),
        "url": url,
        "embedUrl": embed_url,
        "key": key,
        "created_time": upload.get('created_time', ''),
        "play_count": upload.get('play_count', 0),
        "listener_count": upload.get('listener_count', 0),
        "favorite_count": upload.get('favorite_count', 0),
        "repost_count": upload.get('repost_count', 0)
    }


def fetch_hearthis_tracks(username):
    """
    Fetches all tracks from a hearthis.at user profile by parsing HTML, RSS feed, and track pages.
    
    Args:
        username: The hearthis.at username (e.g., 'flukie')
        
    Returns:
        list: List of track items
    """
    tracks = []
    
    print(f"Fetching hearthis.at profile: {username}")
    
    try:
        # Look for iframe embed codes in the HTML that contain track IDs
        # Pattern: src="https://app.hearthis.at/embed/TRACK_ID/..."
        embed_iframe_pattern = re.compile(r'src="https://app\.hearthis\.at/embed/(\d+)/')
        
        # Also look for track URLs in iframe embed codes
        # Pattern: href="https://hearthis.at/USERNAME/TRACK-SLUG/"
        track_link_pattern = re.compile(r'href="https://hearthis\.at/([^/]+)/([^/"]+)/"')
        
        # Also get the main page to extract additional track data
        url = f"https://hearthis.at/{username}/"
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8')
            
            # Look for iframe embed codes that contain track IDs
            # These are often in the page even if tracks are loaded via JS
            embed_matches = embed_iframe_pattern.findall(html)
            embed_ids = set()
            for match in embed_matches:
                # match is a tuple, get the first non-empty group
                track_id = match[0] if match[0] else match[1]
                if track_id:
                    embed_ids.add(track_id)
            
            # Look for track links in iframe embed code descriptions
            # Pattern in iframe: <p>Listen to <a href="https://hearthis.at/flukie/track-name/"...
            track_links = track_link_pattern.findall(html)
            
            # Exclude common non-track paths
            skip_slugs = {'podcast', 'rss', 'live', 'following', 'followers', 'sets', 'groups'}
            
            print(f"  Found {len(embed_ids)} embed IDs and {len(track_links)} track links in HTML")
            
            # Create a mapping of track IDs to track URLs by fetching track pages
            track_id_to_url = {}
            for track_link_match in track_links:
                # track_link_match is a tuple: (user, slug, title)
                if len(track_link_match) >= 2:
                    track_user = track_link_match[0]
                    track_slug = track_link_match[1]
                    track_title = track_link_match[2] if len(track_link_match) > 2 else None
                    
                    # Skip non-track slugs
                    if track_slug.lower() in skip_slugs:
                        continue
                    
                    if track_user.lower() == username.lower() and track_slug:
                        track_url = f"https://hearthis.at/{track_user}/{track_slug}/"
                        # Fetch the track page to find its ID
                        try:
                            track_req = urllib.request.Request(track_url)
                            track_req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
                            with urllib.request.urlopen(track_req, timeout=5) as track_response:
                                track_html = track_response.read().decode('utf-8')
                                # Look for track ID in the page
                                track_id_match = embed_iframe_pattern.search(track_html)
                                if track_id_match:
                                    # Get first non-empty group
                                    track_id = track_id_match.group(1) if track_id_match.group(1) else track_id_match.group(2)
                                    track_id_to_url[track_id] = (track_user, track_slug, track_url, track_title)
                                else:
                                    # If no ID found, use URL as key
                                    track_id_to_url[track_url] = (track_user, track_slug, track_url, track_title)
                        except Exception as e:
                            # If we can't fetch, still add it with URL as key
                            track_id_to_url[track_url] = (track_user, track_slug, track_url, track_title)
            
            # Also check embed IDs we found in the main page
            for track_id in embed_ids:
                if track_id not in track_id_to_url:
                    # Try to find the track URL near this embed ID
                    embed_pos = html.find(f'app.hearthis.at/embed/{track_id}/')
                    if embed_pos != -1:
                        context = html[max(0, embed_pos-1000):embed_pos+500]
                        # Look for track link near the embed
                        link_match = track_link_pattern.search(context)
                        if link_match:
                            track_user, track_slug = link_match.groups()
                            if track_user.lower() == username.lower():
                                track_url = f"https://hearthis.at/{track_user}/{track_slug}/"
                                track_id_to_url[track_id] = (track_user, track_slug, track_url)
            
            # Now create track items from what we found
            for track_key, track_data in track_id_to_url.items():
                if len(track_data) >= 3:
                    track_user = track_data[0]
                    track_slug = track_data[1]
                    track_url = track_data[2]
                    track_title = track_data[3] if len(track_data) > 3 else None
                    
                    href = f"/{track_user}/{track_slug}"
                    embed_url = f"https://hearthis.at{href}/embed/"
                    
                    # Use title from link if available, otherwise fetch from page
                    title = track_title if track_title else track_slug.replace('-', ' ').title()
                    created_time = ""
                    
                    # Fetch track page to get full title and date
                    try:
                        track_req = urllib.request.Request(track_url)
                        track_req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
                        with urllib.request.urlopen(track_req, timeout=5) as track_response:
                            track_html = track_response.read().decode('utf-8')
                            
                            # Extract title from page title or meta tags
                            title_match = re.search(r'<title>([^<]+)</title>', track_html)
                            if title_match:
                                title = title_match.group(1).strip()
                                # Remove " | hearthis.at" suffix if present
                                title = title.replace(' | hearthis.at', '').strip()
                            
                            # Look for date in meta tags or page content
                            date_match = re.search(r'<meta[^>]*property="article:published_time"[^>]*content="([^"]+)"', track_html)
                            if date_match:
                                created_time = date_match.group(1)
                            else:
                                # Try to find date in other formats
                                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', track_html)
                                if date_match:
                                    created_time = date_match.group(1) + "T00:00:00Z"
                    except Exception as e:
                        pass  # Use defaults if we can't fetch
                    
                    tracks.append({
                        "platform": "hearthis",
                        "title": title,
                        "url": track_url,
                        "embedUrl": embed_url,
                        "key": href,
                        "created_time": created_time,
                        "play_count": 0,
                        "listener_count": 0,
                        "favorite_count": 0,
                        "repost_count": 0
                    })
            
            if tracks:
                print(f"  Found {len(tracks)} tracks from profile page")
            
            # Also look for track URLs directly in the HTML (e.g., href="/flukie/track-name/")
            # Also look for embed codes with track IDs
            track_url_pattern = re.compile(r'href="/([^/]+)/([^/"]+)/"')
            embed_id_pattern = re.compile(r'app\.hearthis\.at/embed/(\d+)/')
            
            # Create a set of existing track URLs from RSS to avoid duplicates
            existing_urls = {track['url'] for track in tracks}
            found_tracks = {}
            
            # Find all track URLs that belong to this user
            for match in track_url_pattern.finditer(html):
                track_user = match.group(1)
                track_slug = match.group(2)
                
                # Only get tracks from the specified user (skip categories, etc.)
                if track_user.lower() == username.lower() and track_slug and track_slug not in ['', 'podcast', 'rss']:
                    href = f"/{track_user}/{track_slug}"
                    track_url = f"https://hearthis.at{href}/"
                    
                    # Skip if we already have this from RSS
                    if track_url in existing_urls:
                        continue
                    
                    embed_url = f"https://hearthis.at{href}/embed/"
                    
                    # Try to find title near the URL
                    url_pos = html.find(href)
                    if url_pos != -1:
                        context = html[max(0, url_pos-200):url_pos+500]
                        # Look for title in various formats
                        title_match = re.search(r'<a[^>]*href="[^"]*' + re.escape(href) + r'[^"]*"[^>]*>([^<]+)</a>', context)
                        title = title_match.group(1).strip() if title_match else track_slug.replace('-', ' ').title()
                        
                        # Look for track ID in embed code near this URL
                        embed_context = html[max(0, url_pos-500):url_pos+1000]
                        embed_match = embed_id_pattern.search(embed_context)
                        track_id = embed_match.group(1) if embed_match else None
                        
                        # Look for timestamp
                        timestamp_match = re.search(r'data-time="(\d+)"', context)
                        timestamp = int(timestamp_match.group(1)) if timestamp_match else 0
                        
                        # Use track_id as key if available, otherwise use URL
                        key = track_id if track_id else href
                        
                        if key not in found_tracks:
                            created_time = ""
                            if timestamp > 0:
                                created_time = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%dT%H:%M:%SZ')
                            
                            found_tracks[key] = {
                                "platform": "hearthis",
                                "title": title,
                                "url": track_url,
                                "embedUrl": embed_url,
                                "key": href,
                                "created_time": created_time,
                                "play_count": 0,
                                "listener_count": 0,
                                "favorite_count": 0,
                                "repost_count": 0
                            }
            
            # Add tracks found in HTML that weren't in RSS
            for track in found_tracks.values():
                if track['url'] not in existing_urls:
                    tracks.append(track)
            
            # Also look for track data in data attributes (hearthis.at uses data-trackid, data-playlist-title, etc.)
            track_pattern = re.compile(
                r'<li[^>]*data-trackid="(\d+)"[^>]*data-playlist-title="([^"]*)"[^>]*data-playlist-author="([^"]*)"[^>]*data-time="(\d+)"[^>]*>.*?href="([^"]*)"',
                re.DOTALL
            )
            
            for match in track_pattern.finditer(html):
                track_id = match.group(1)
                title = match.group(2).strip()
                author = match.group(3).strip()
                timestamp = int(match.group(4))
                href = match.group(5)
                
                # Extract track slug from href
                if href.startswith('/'):
                    href = href.rstrip('/')
                    parts = href.split('/')
                    if len(parts) >= 3:
                        track_user = parts[1]
                        track_slug = parts[2]
                        
                        # Only get tracks from the specified user
                        if track_user.lower() == username.lower():
                            track_url = f"https://hearthis.at{href}/"
                            embed_url = f"https://hearthis.at{href}/embed/"
                            
                            # Convert timestamp to ISO format
                            created_time = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%dT%H:%M:%SZ')
                            
                            # Update or add track
                            found_tracks[track_id] = {
                                "platform": "hearthis",
                                "title": title if title else track_slug.replace('-', ' ').title(),
                                "url": track_url,
                                "embedUrl": embed_url,
                                "key": href,
                                "created_time": created_time,
                                "play_count": 0,
                                "listener_count": 0,
                                "favorite_count": 0,
                                "repost_count": 0
                            }
            
            # Also try to fetch more tracks via AJAX endpoint
            try:
                ajax_data = urllib.parse.urlencode({'user': username}).encode()
                ajax_req = urllib.request.Request('https://hearthis.at/user_ajax_more.php', data=ajax_data)
                ajax_req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
                ajax_req.add_header('Content-Type', 'application/x-www-form-urlencoded')
                ajax_req.add_header('X-Requested-With', 'XMLHttpRequest')
                
                with urllib.request.urlopen(ajax_req) as ajax_response:
                    ajax_html = ajax_response.read().decode('utf-8')
                    
                    # Parse AJAX response for additional tracks using same patterns
                    # Look for track URLs
                    for match in track_url_pattern.finditer(ajax_html):
                        track_user = match.group(1)
                        track_slug = match.group(2)
                        
                        if track_user.lower() == username.lower() and track_slug and track_slug not in ['', 'podcast', 'rss']:
                            href = f"/{track_user}/{track_slug}"
                            track_url = f"https://hearthis.at{href}/"
                            embed_url = f"https://hearthis.at{href}/embed/"
                            
                            url_pos = ajax_html.find(href)
                            if url_pos != -1:
                                context = ajax_html[max(0, url_pos-200):url_pos+500]
                                title_match = re.search(r'<a[^>]*href="[^"]*' + re.escape(href) + r'[^"]*"[^>]*>([^<]+)</a>', context)
                                title = title_match.group(1).strip() if title_match else track_slug.replace('-', ' ').title()
                                
                                embed_context = ajax_html[max(0, url_pos-500):url_pos+1000]
                                embed_match = embed_id_pattern.search(embed_context)
                                track_id = embed_match.group(1) if embed_match else None
                                
                                timestamp_match = re.search(r'data-time="(\d+)"', context)
                                timestamp = int(timestamp_match.group(1)) if timestamp_match else 0
                                
                                key = track_id if track_id else href
                                
                                if key not in found_tracks:
                                    created_time = ""
                                    if timestamp > 0:
                                        created_time = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%dT%H:%M:%SZ')
                                    
                                    found_tracks[key] = {
                                        "platform": "hearthis",
                                        "title": title,
                                        "url": track_url,
                                        "embedUrl": embed_url,
                                        "key": href,
                                        "created_time": created_time,
                                        "play_count": 0,
                                        "listener_count": 0,
                                        "favorite_count": 0,
                                        "repost_count": 0
                                    }
                    
                    # Also parse data attributes from AJAX response
                    for match in track_pattern.finditer(ajax_html):
                        track_id = match.group(1)
                        title = match.group(2).strip()
                        author = match.group(3).strip()
                        timestamp = int(match.group(4))
                        href = match.group(5)
                        
                        if href.startswith('/'):
                            href = href.rstrip('/')
                            parts = href.split('/')
                            if len(parts) >= 3:
                                track_user = parts[1]
                                track_slug = parts[2]
                                
                                if track_user.lower() == username.lower():
                                    track_url = f"https://hearthis.at{href}/"
                                    embed_url = f"https://hearthis.at{href}/embed/"
                                    created_time = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%dT%H:%M:%SZ')
                                    
                                    found_tracks[track_id] = {
                                        "platform": "hearthis",
                                        "title": title if title else track_slug.replace('-', ' ').title(),
                                        "url": track_url,
                                        "embedUrl": embed_url,
                                        "key": href,
                                        "created_time": created_time,
                                        "play_count": 0,
                                        "listener_count": 0,
                                        "favorite_count": 0,
                                        "repost_count": 0
                                    }
            except Exception as ajax_error:
                print(f"  Note: Could not fetch additional tracks via AJAX: {ajax_error}")
            
            # Merge found_tracks with existing tracks (avoid duplicates)
            existing_urls = {track['url'] for track in tracks}
            for track in found_tracks.values():
                if track['url'] not in existing_urls:
                    tracks.append(track)
            
            print(f"Found {len(tracks)} tracks from hearthis.at")
            
    except Exception as e:
        print(f"Error fetching hearthis.at data: {e}")
        import traceback
        traceback.print_exc()
    
    return tracks


def main():
    """Main function to fetch data from both platforms and generate JSON."""
    # Get usernames from command line or use defaults
    mixcloud_username = sys.argv[1] if len(sys.argv) > 1 else "FlukieL"
    hearthis_username = sys.argv[2] if len(sys.argv) > 2 else "flukie"
    
    all_archive_items = []
    
    # Fetch Mixcloud data
    print(f"\n=== Fetching Mixcloud profile: {mixcloud_username} ===")
    user_data = fetch_mixcloud_user(mixcloud_username)
    if user_data:
        print(f"User found: {user_data.get('name', mixcloud_username)}")
        uploads = fetch_all_uploads(mixcloud_username)
        if uploads:
            mixcloud_items = [format_archive_item(upload) for upload in uploads]
            all_archive_items.extend(mixcloud_items)
            print(f"Added {len(mixcloud_items)} Mixcloud items")
        else:
            print("No Mixcloud uploads found.")
    else:
        print("Failed to fetch Mixcloud user data.")
    
    # Fetch hearthis.at data
    print(f"\n=== Fetching hearthis.at profile: {hearthis_username} ===")
    hearthis_tracks = fetch_hearthis_tracks(hearthis_username)
    if hearthis_tracks:
        all_archive_items.extend(hearthis_tracks)
        print(f"Added {len(hearthis_tracks)} hearthis.at items")
    else:
        print("No hearthis.at tracks found.")
    
    if not all_archive_items:
        print("\nNo audio items found from either platform.")
        return 1
    
    # Read existing JSON to preserve video entries and manually added tracks
    output_path = Path(__file__).parent.parent / "data" / "archives.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    existing_data = {}
    existing_hearthis_tracks = []
    if output_path.exists():
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                # Preserve existing hearthis tracks (they may be manually added since they load dynamically)
                if "audio" in existing_data:
                    existing_hearthis_tracks = [item for item in existing_data["audio"] if item.get("platform") == "hearthis"]
        except Exception as e:
            print(f"Warning: Could not read existing JSON file: {e}")
    
    # Ensure video is always an array (required by config.js validation)
    existing_video = existing_data.get("video", [])
    if not isinstance(existing_video, list):
        existing_video = []
    
    # Merge hearthis tracks: keep manually added ones, add newly scraped ones
    existing_hearthis_urls = {track['url'] for track in existing_hearthis_tracks}
    new_hearthis_tracks = [item for item in all_archive_items if item.get("platform") == "hearthis"]
    other_audio_items = [item for item in all_archive_items if item.get("platform") != "hearthis"]
    
    # Add new hearthis tracks that aren't already in the list
    for track in new_hearthis_tracks:
        if track['url'] not in existing_hearthis_urls:
            existing_hearthis_tracks.append(track)
    
    # Combine all audio items
    all_audio_items = other_audio_items + existing_hearthis_tracks
    
    # Create output structure, preserving existing video entries and manually added hearthis tracks
    output = {
        "audio": all_audio_items,
        "video": existing_video
    }
    
    # Write to JSON file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n=== Successfully generated {output_path} ===")
    print(f"Total audio items: {len(all_audio_items)}")
    print(f"  - Mixcloud: {len([i for i in all_audio_items if i['platform'] == 'mixcloud'])}")
    print(f"  - hearthis.at: {len([i for i in all_audio_items if i['platform'] == 'hearthis'])}")
    if existing_hearthis_tracks and not new_hearthis_tracks:
        print(f"  Note: Preserved {len(existing_hearthis_tracks)} existing hearthis.at track(s)")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

