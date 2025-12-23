#!/usr/bin/env python3
"""
VK Video Playlist Scraper
Fetches videos from a VK video playlist and generates a JSON file.

Usage:
    python scripts/fetch_vk_videos.py [playlist_url] [--use-vk-scraper] [--vk-username USERNAME] [--vk-password PASSWORD]
    python scripts/fetch_vk_videos.py [video_url1] [video_url2] ...
    
Examples:
    # Fetch from playlist (may not work if JavaScript-rendered)
    python scripts/fetch_vk_videos.py https://vkvideo.ru/playlist/512257790_1
    
    # Extract from specific video URLs
    python scripts/fetch_vk_videos.py https://vkvideo.ru/playlist/512257790_1/video-230027318_456239022 https://vkvideo.ru/playlist/512257790_1/video-230027318_456239021
    
    # Use vk-url-scraper library (requires authentication)
    python scripts/fetch_vk_videos.py https://vkvideo.ru/playlist/512257790_1 --use-vk-scraper --vk-username user --vk-password pass

Note: The --use-vk-scraper option requires the vk-url-scraper library:
    pip install vk-url-scraper
    pip install git+https://github.com/python273/vk_api.git@b99dac0ec2f832a6c4b20bde49869e7229ce4742
"""

import json
import sys
import urllib.request
import urllib.parse
import urllib.error
import gzip
import re
from pathlib import Path
from datetime import datetime
from html.parser import HTMLParser
from http.cookiejar import CookieJar
from io import BytesIO


class VKPlaylistParser(HTMLParser):
    """HTML parser to extract video data from VK playlist page."""
    
    def __init__(self):
        super().__init__()
        self.videos = []
        self.current_video = {}
        self.in_video_item = False
        self.in_title = False
        self.in_date = False
        self.current_tag = None
        
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        
        # Look for video items - VK uses various patterns
        if tag == 'div' and attrs_dict.get('class', ''):
            classes = attrs_dict['class'].split()
            if any('video_item' in c or 'videoItem' in c or 'catalog_item' in c for c in classes):
                self.in_video_item = True
                self.current_video = {}
                # Try to extract video ID from data attributes or class
                if 'data-id' in attrs_dict:
                    self.current_video['video_id'] = attrs_dict['data-id']
                elif 'id' in attrs_dict:
                    video_id_match = re.search(r'video(\d+_\d+)', attrs_dict['id'])
                    if video_id_match:
                        self.current_video['video_id'] = video_id_match.group(1)
        
        # Look for links to videos
        if tag == 'a' and self.in_video_item:
            href = attrs_dict.get('href', '')
            if '/video' in href:
                # Extract video ID from URL
                video_match = re.search(r'/video(-?\d+_\d+)', href)
                if video_match:
                    self.current_video['video_id'] = video_match.group(1)
                    self.current_video['url'] = href if href.startswith('http') else f'https://vk.com{href}'
        
        # Look for iframe embeds
        if tag == 'iframe' and 'src' in attrs_dict:
            src = attrs_dict['src']
            if 'vk.com/video_ext.php' in src or 'vkvideo.ru' in src:
                # Extract video ID from embed URL
                video_match = re.search(r'oid=(-?\d+)&id=(\d+)', src)
                if video_match:
                    oid, vid = video_match.groups()
                    self.current_video['video_id'] = f"{oid}_{vid}"
                    self.current_video['embed_url'] = src
        
        # Look for title elements
        if tag in ['div', 'span', 'a'] and self.in_video_item:
            classes = attrs_dict.get('class', '').split()
            if any('title' in c.lower() or 'name' in c.lower() for c in classes):
                self.in_title = True
                self.current_tag = tag
    
    def handle_endtag(self, tag):
        if tag == self.current_tag and self.in_title:
            self.in_title = False
            self.current_tag = None
        
        if tag == 'div' and self.in_video_item:
            # Check if we should finalize this video
            if self.current_video.get('video_id') and self.current_video.get('title'):
                self.videos.append(self.current_video.copy())
            self.in_video_item = False
            self.current_video = {}
    
    def handle_data(self, data):
        if self.in_title and self.in_video_item:
            title = data.strip()
            if title and len(title) > 3:  # Filter out very short titles
                if 'title' not in self.current_video or len(title) > len(self.current_video.get('title', '')):
                    self.current_video['title'] = title


def fetch_vk_playlist(playlist_url):
    """
    Fetches video data from a VK video playlist.
    
    Args:
        playlist_url: The VK playlist URL (e.g., 'https://vkvideo.ru/playlist/512257790_1')
        
    Returns:
        list: List of video items
    """
    videos = []
    
    print(f"Fetching VK playlist: {playlist_url}")
    
    try:
        # Parse the playlist ID from URL
        playlist_match = re.search(r'playlist/(\d+_\d+)', playlist_url)
        if not playlist_match:
            print(f"Error: Could not parse playlist ID from URL: {playlist_url}")
            return videos
        
        playlist_id = playlist_match.group(1)
        owner_id, playlist_num = playlist_id.split('_')
        
        # Create a cookie jar and opener that handles redirects
        cookie_jar = CookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
        
        # Add headers to make the request look like a real browser
        opener.addheaders = [
            ('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'),
            ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'),
            ('Accept-Language', 'en-GB,en;q=0.9,ru;q=0.8'),
            ('Accept-Encoding', 'gzip, deflate'),
            ('Connection', 'keep-alive'),
            ('Upgrade-Insecure-Requests', '1'),
            ('Sec-Fetch-Dest', 'document'),
            ('Sec-Fetch-Mode', 'navigate'),
            ('Sec-Fetch-Site', 'none'),
            ('Cache-Control', 'max-age=0'),
        ]
        
        # Try alternative URL formats if the main one fails
        # Note: vkvideo.ru playlists may need to be accessed differently
        urls_to_try = [
            playlist_url,
            f"https://vk.com/videos{owner_id}?z=video{owner_id}_{playlist_num}",
            f"https://vk.com/video{owner_id}_{playlist_num}",
            f"https://vk.com/videos{owner_id}?section=playlist_{playlist_num}",
            f"https://vk.com/videos{owner_id}",
        ]
        
        html = None
        final_url = None
        
        for url_to_try in urls_to_try:
            try:
                print(f"  Trying URL: {url_to_try}")
                response = opener.open(url_to_try, timeout=15)
                final_url = response.geturl()  # Get final URL after redirects
                
                # Handle gzip encoding if present
                content = response.read()
                content_encoding = response.headers.get('Content-Encoding', '').lower()
                if content_encoding == 'gzip':
                    content = gzip.decompress(content)
                
                html = content.decode('utf-8', errors='ignore')
                response.close()
                print(f"  Successfully fetched page (final URL: {final_url}, length: {len(html)} chars)")
                break
            except urllib.error.HTTPError as e:
                print(f"  HTTP Error {e.code} for {url_to_try}")
                if e.code == 302 or e.code == 301:
                    # Try to follow the redirect manually
                    redirect_url = e.headers.get('Location') or e.headers.get('location')
                    if redirect_url:
                        if not redirect_url.startswith('http'):
                            redirect_url = urllib.parse.urljoin(url_to_try, redirect_url)
                        print(f"  Got {e.code} redirect to: {redirect_url}")
                        try:
                            response = opener.open(redirect_url, timeout=15)
                            final_url = response.geturl()
                            
                            # Handle gzip encoding if present
                            content = response.read()
                            content_encoding = response.headers.get('Content-Encoding', '').lower()
                            if content_encoding == 'gzip':
                                content = gzip.decompress(content)
                            
                            html = content.decode('utf-8', errors='ignore')
                            response.close()
                            print(f"  Successfully followed redirect (final URL: {final_url}, length: {len(html)} chars)")
                            break
                        except Exception as redirect_error:
                            print(f"  Error following redirect: {redirect_error}")
                            continue
                # For other HTTP errors, try next URL
                continue
            except Exception as e:
                print(f"  Error fetching {url_to_try}: {type(e).__name__}: {e}")
                continue
        
        if not html:
            print("  Failed to fetch playlist from all attempted URLs")
            return videos
        
        # Process the HTML
        try:
            # VK pages are often JavaScript-rendered, so we need to look for JSON data in script tags
            # Look for various JSON patterns that VK might use
            json_patterns = [
                r'window\.vkData\s*=\s*({.+?});',
                r'var\s+vkData\s*=\s*({.+?});',
                r'window\.__INITIAL_STATE__\s*=\s*({.+?});',
                r'window\.__DATA__\s*=\s*({.+?});',
                r'<script[^>]*type=["\']application/json["\'][^>]*>({.+?})</script>',
            ]
            
            for pattern in json_patterns:
                json_data_match = re.search(pattern, html, re.DOTALL)
                if json_data_match:
                    try:
                        json_str = json_data_match.group(1)
                        json_data = json.loads(json_str)
                        print(f"  Found JSON data in page (pattern matched)")
                        # Try to extract video data from JSON
                        # VK JSON structure varies, so we'll try common patterns
                        if isinstance(json_data, dict):
                            # Look for video arrays in common locations
                            for key in ['videos', 'items', 'list', 'data', 'playlist']:
                                if key in json_data and isinstance(json_data[key], list):
                                    print(f"    Found {len(json_data[key])} items in JSON key '{key}'")
                    except Exception as e:
                        # JSON parsing failed, continue
                        pass
            
            # Look for video IDs in various formats in the HTML
            # Pattern 1: /video-123456_78901234 (most common in vkvideo.ru)
            video_id_pattern1 = re.compile(r'/video-(\d+_\d+)')
            # Pattern 2: /playlist/OWNER_PLAYLIST/video-OWNER_VIDEO (specific to vkvideo.ru playlists)
            video_id_pattern1b = re.compile(r'/playlist/\d+_\d+/video-(\d+_\d+)')
            # Pattern 3: video_ext.php?oid=123&id=456
            video_id_pattern2 = re.compile(r'video_ext\.php\?oid=(-?\d+)&id=(\d+)')
            # Pattern 4: data-video-id="123_456"
            video_id_pattern3 = re.compile(r'data-video-id=["\'](\d+_\d+)["\']')
            # Pattern 5: video(\d+_\d+) in class names or IDs
            video_id_pattern4 = re.compile(r'video(\d+_\d+)')
            # Pattern 6: href="/video123456_78901234"
            video_id_pattern5 = re.compile(r'href=["\']/video-?(\d+_\d+)')
            
            found_video_ids = set()
            
            # Search for all patterns
            for match in video_id_pattern1.finditer(html):
                video_id = match.group(1)
                found_video_ids.add(video_id)
            
            for match in video_id_pattern1b.finditer(html):
                video_id = match.group(1)
                found_video_ids.add(video_id)
            
            for match in video_id_pattern2.finditer(html):
                oid, vid = match.groups()
                video_id = f"{oid}_{vid}"
                found_video_ids.add(video_id)
            
            for match in video_id_pattern3.finditer(html):
                video_id = match.group(1)
                found_video_ids.add(video_id)
            
            for match in video_id_pattern4.finditer(html):
                video_id = match.group(1)
                found_video_ids.add(video_id)
            
            for match in video_id_pattern5.finditer(html):
                video_id = match.group(1)
                found_video_ids.add(video_id)
            
            # If we haven't found any video IDs yet, try a more aggressive search
            if len(found_video_ids) == 0:
                print("  No video IDs found with standard patterns, trying broader search...")
                # Look for any number_number patterns that could be video IDs
                all_number_pairs = re.findall(r'(\d{6,})_(\d{6,})', html)
                potential_ids = [f"{pair[0]}_{pair[1]}" for pair in all_number_pairs]
                # Filter to ones that start with the owner ID
                owner_matching = [vid for vid in potential_ids if vid.startswith(f"{owner_id}_")]
                if owner_matching:
                    print(f"    Found {len(set(owner_matching))} potential video IDs matching owner")
                    found_video_ids.update(set(owner_matching))
            
            print(f"  Found {len(found_video_ids)} unique video IDs in HTML")
            
            # Debug: Look for any video-related content
            if len(found_video_ids) == 0:
                print("  Debug: Searching for video-related patterns...")
                # Look for any numbers that might be video IDs
                number_pairs = re.findall(r'(\d+)[_-](\d+)', html)
                print(f"    Found {len(number_pairs)} number pairs (potential video IDs)")
                
                # Look for "video" mentions
                video_mentions = len(re.findall(r'\bvideo\b', html, re.IGNORECASE))
                print(f"    Found {video_mentions} mentions of 'video' in HTML")
                
                # Look for playlist structure
                playlist_mentions = len(re.findall(r'\bplaylist\b', html, re.IGNORECASE))
                print(f"    Found {playlist_mentions} mentions of 'playlist' in HTML")
                
                # Try to find iframe embeds
                iframe_count = len(re.findall(r'<iframe', html, re.IGNORECASE))
                print(f"    Found {iframe_count} iframe tags")
                
                # Look for script tags that might contain video data
                script_tags = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL | re.IGNORECASE)
                print(f"    Found {len(script_tags)} script tags")
                
                # Search script tags for video data
                for i, script_content in enumerate(script_tags):  # Check all scripts
                    # Look for video IDs in various formats
                    # Pattern 1: Standard format 512257790_456239017
                    script_video_ids1 = re.findall(r'\b(\d{6,}_\d{6,})\b', script_content)
                    # Pattern 2: In quotes or strings
                    script_video_ids2 = re.findall(r'["\'](\d{6,}_\d{6,})["\']', script_content)
                    # Pattern 3: In video URLs
                    script_video_ids3 = re.findall(r'/video-?(\d+_\d+)', script_content)
                    # Pattern 4: In data attributes or JSON
                    script_video_ids4 = re.findall(r'["\']?video_id["\']?\s*[:=]\s*["\']?(\d+_\d+)["\']?', script_content, re.IGNORECASE)
                    
                    all_script_ids = script_video_ids1 + script_video_ids2 + script_video_ids3 + script_video_ids4
                    if all_script_ids:
                        unique_ids = set(all_script_ids)
                        # Filter: prefer owner ID matches, but also accept others if reasonable
                        filtered_ids = [vid for vid in unique_ids if vid.startswith(f"{owner_id}_")]
                        other_ids = [vid for vid in unique_ids if not vid.startswith(f"{owner_id}_") and len(vid.split('_')[0]) >= 6]
                        
                        if filtered_ids:
                            print(f"    Script {i} contains {len(filtered_ids)} video IDs matching owner {owner_id}")
                            found_video_ids.update(filtered_ids)
                        if other_ids and len(found_video_ids) < 30:
                            print(f"    Script {i} contains {len(other_ids)} other potential video IDs")
                            found_video_ids.update(other_ids[:20])
                    
                    # Look for JSON data in scripts
                    json_matches = re.findall(r'\{[^{}]*"video"[^{}]*\}', script_content, re.IGNORECASE)
                    if json_matches:
                        print(f"    Script {i} contains {len(json_matches)} JSON objects with 'video'")
                        for json_match in json_matches[:5]:
                            try:
                                data = json.loads(json_match)
                                # Try to extract video info
                                if isinstance(data, dict):
                                    for key in data:
                                        if 'video' in key.lower() or 'id' in key.lower():
                                            print(f"      Found key: {key}")
                            except:
                                pass
                
                # Check if this might be a JavaScript-rendered page
                if 'react' in html.lower() or 'vue' in html.lower() or 'angular' in html.lower():
                    print("    Warning: Page appears to be JavaScript-rendered (React/Vue/Angular detected)")
                    print("    Videos may need to be loaded via JavaScript or API")
                
                # Try to find API endpoints
                api_patterns = [
                    r'["\'](/api[^"\']+)["\']',
                    r'["\'](https?://[^"\']*api[^"\']*)["\']',
                    r'["\'](/method/[^"\']+)["\']',
                ]
                for pattern in api_patterns:
                    api_matches = re.findall(pattern, html, re.IGNORECASE)
                    if api_matches:
                        print(f"    Found {len(set(api_matches))} potential API endpoints")
                        for api_match in list(set(api_matches))[:5]:
                            if 'video' in api_match.lower() or 'playlist' in api_match.lower():
                                print(f"      API endpoint: {api_match}")
            
            # Also try to parse HTML directly
            parser = VKPlaylistParser()
            parser.feed(html)
            videos.extend(parser.videos)
            
            # Process found video IDs
            for video_id in found_video_ids:
                if '_' in video_id:
                    oid, vid = video_id.split('_')
                    video_url = f"https://vk.com/video{video_id}"
                    embed_url = f"https://vk.com/video_ext.php?oid={oid}&id={vid}&lang=en"
                    
                    # Try to find title near the video ID in HTML
                    # Look for title in various patterns
                    title = f"Video {video_id}"
                    
                    # Search for title near video ID
                    video_id_pos = html.find(video_id)
                    if video_id_pos != -1:
                        context = html[max(0, video_id_pos-1000):video_id_pos+1000]
                        # Try various title patterns
                        title_patterns = [
                            r'<a[^>]*href="[^"]*video[^"]*"[^>]*>([^<]+)</a>',
                            r'<div[^>]*class="[^"]*title[^"]*"[^>]*>([^<]+)</div>',
                            r'<span[^>]*class="[^"]*title[^"]*"[^>]*>([^<]+)</span>',
                            r'title["\']?\s*:\s*["\']([^"\']+)["\']',
                            r'"title"\s*:\s*"([^"]+)"',
                        ]
                        
                        for title_pattern in title_patterns:
                            title_match = re.search(title_pattern, context, re.IGNORECASE)
                            if title_match:
                                potential_title = title_match.group(1).strip()
                                if len(potential_title) > 3 and len(potential_title) < 200:
                                    title = potential_title
                                    break
                    
                    # Look for date
                    created_time = ""
                    if video_id_pos != -1:
                        context = html[max(0, video_id_pos-1000):video_id_pos+1000]
                        date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', context)
                        if date_match:
                            created_time = date_match.group(0) + "T00:00:00Z"
                    
                    # Check if we already have this video
                    if not any(v.get('video_id') == video_id for v in videos):
                        videos.append({
                            'video_id': video_id,
                            'title': title,
                            'url': video_url,
                            'embed_url': embed_url,
                            'created_time': created_time
                        })
            
            # Look for video URLs in the HTML (additional pattern matching)
            # Pattern for vkvideo.ru playlist video URLs: /playlist/OWNER_PLAYLIST/video-VIDEO_ID
            playlist_video_pattern = re.compile(r'href=["\'](/playlist/\d+_\d+/video-(\d+_\d+))["\']', re.IGNORECASE)
            for match in playlist_video_pattern.finditer(html):
                video_path = match.group(1)
                video_id = match.group(2)
                video_url = f"https://vkvideo.ru{video_path}"
                
                # Try to find title near this URL
                url_pos = match.start()
                context = html[max(0, url_pos-500):url_pos+500]
                title_match = re.search(r'<a[^>]*href="[^"]*video[^"]*"[^>]*>([^<]+)</a>', context, re.IGNORECASE)
                title = title_match.group(1).strip() if title_match else f"Video {video_id}"
                
                # Build embed URL
                if '_' in video_id:
                    oid, vid = video_id.split('_')
                    embed_url = f"https://vk.com/video_ext.php?oid={oid}&id={vid}&lang=en"
                else:
                    embed_url = f"https://vk.com/video_ext.php?oid={owner_id}&id={video_id}&lang=en"
                
                # Check if we already have this video
                if not any(v.get('video_id') == video_id for v in videos):
                    videos.append({
                        'video_id': video_id,
                        'title': title,
                        'url': video_url,
                        'embed_url': embed_url,
                        'created_time': ""
                    })
            
            # Look for standard video URLs in the HTML
            video_url_pattern = re.compile(r'href=["\'](/video(-?\d+_\d+)[^"]*)["\']', re.IGNORECASE)
            video_title_pattern = re.compile(r'<a[^>]*href="[^"]*video[^"]*"[^>]*>([^<]+)</a>', re.IGNORECASE)
            
            for match in video_url_pattern.finditer(html):
                video_id = match.group(2)
                video_path = match.group(1)
                video_url = f"https://vk.com{video_path}"
                
                # Try to find title near this URL
                url_pos = match.start()
                context = html[max(0, url_pos-500):url_pos+500]
                title_match = video_title_pattern.search(context)
                title = title_match.group(1).strip() if title_match else f"Video {video_id}"
                
                # Look for date information
                date_match = re.search(r'(\d{1,2})[./](\d{1,2})[./](\d{4})', context)
                created_time = ""
                if date_match:
                    day, month, year = date_match.groups()
                    created_time = f"{year}-{month.zfill(2)}-{day.zfill(2)}T00:00:00Z"
                
                # Build embed URL
                # VK embed format: https://vk.com/video_ext.php?oid=OWNER_ID&id=VIDEO_ID
                # Also supports: https://vk.com/video-OWNER_ID_VIDEO_ID format
                if '_' in video_id:
                    oid, vid = video_id.split('_')
                    # Try video_ext.php format first (more reliable for embedding)
                    embed_url = f"https://vk.com/video_ext.php?oid={oid}&id={vid}&lang=en"
                    # Alternative format: https://vk.com/video-{oid}_{vid}
                    video_url_alt = f"https://vk.com/video{oid}_{vid}"
                else:
                    embed_url = f"https://vk.com/video_ext.php?oid={owner_id}&id={video_id}&lang=en"
                    video_url_alt = f"https://vk.com/video{owner_id}_{video_id}"
                
                # Check if we already have this video
                if not any(v.get('video_id') == video_id for v in videos):
                    videos.append({
                        'video_id': video_id,
                        'title': title,
                        'url': video_url,
                        'embed_url': embed_url,
                        'created_time': created_time
                    })
            
            # Also try to find videos in iframe embed codes
            iframe_pattern = re.compile(r'<iframe[^>]*src="([^"]*vk\.com/video_ext\.php[^"]*)"')
            for iframe_match in iframe_pattern.finditer(html):
                embed_src = iframe_match.group(1)
                video_match = re.search(r'oid=(-?\d+)&id=(\d+)', embed_src)
                if video_match:
                    oid, vid = video_match.groups()
                    video_id = f"{oid}_{vid}"
                    video_url = f"https://vk.com/video{oid}_{vid}"
                    
                    # Check if we already have this video
                    if not any(v.get('video_id') == video_id for v in videos):
                        videos.append({
                            'video_id': video_id,
                            'title': f"Video {video_id}",
                            'url': video_url,
                            'embed_url': embed_src,
                            'created_time': ""
                        })
            
            print(f"  Found {len(videos)} videos from HTML parsing")
            
            # Try to fetch individual video pages to get better metadata
            for video in videos[:10]:  # Limit to first 10 to avoid too many requests
                try:
                    video_response = opener.open(video['url'], timeout=10)
                    
                    # Handle gzip encoding if present
                    content = video_response.read()
                    content_encoding = video_response.headers.get('Content-Encoding', '').lower()
                    if content_encoding == 'gzip':
                        content = gzip.decompress(content)
                    
                    video_html = content.decode('utf-8', errors='ignore')
                    video_response.close()
                    
                    # Extract title from page
                    title_match = re.search(r'<title>([^<]+)</title>', video_html)
                    if title_match:
                        title = title_match.group(1).strip()
                        # Remove " | VK" suffix if present
                        title = title.replace(' | VK', '').replace(' | ВКонтакте', '').strip()
                        if title:
                            video['title'] = title
                    
                    # Extract date
                    date_match = re.search(r'<meta[^>]*property="article:published_time"[^>]*content="([^"]+)"', video_html)
                    if date_match:
                        video['created_time'] = date_match.group(1)
                    else:
                        # Try to find date in other formats
                        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', video_html)
                        if date_match:
                            video['created_time'] = date_match.group(1) + "T00:00:00Z"
                except Exception as e:
                    # Skip if we can't fetch individual video page
                    print(f"    Could not fetch metadata for {video.get('url', 'unknown')}: {e}")
                    pass
        except Exception as e:
            print(f"Error processing HTML: {e}")
            import traceback
            traceback.print_exc()
            
    except urllib.error.HTTPError as e:
        print(f"Error fetching playlist: HTTP {e.code}")
        if e.code == 404:
            print(f"Playlist not found: {playlist_url}")
    except Exception as e:
        print(f"Error fetching playlist: {e}")
        import traceback
        traceback.print_exc()
    
    return videos


def extract_video_from_url(video_url):
    """
    Extracts video information from a VK video URL.
    
    Args:
        video_url: VK video URL (e.g., 'https://vkvideo.ru/playlist/512257790_1/video-230027318_456239022')
        
    Returns:
        dict: Video data dictionary or None if extraction fails
    """
    # Pattern 1: vkvideo.ru/playlist/OWNER_PLAYLIST/video-VIDEO_ID
    match1 = re.search(r'/playlist/\d+_\d+/video-(\d+_\d+)', video_url)
    # Pattern 2: vk.com/video-VIDEO_ID or /videoVIDEO_ID
    match2 = re.search(r'/video-?(\d+_\d+)', video_url)
    # Pattern 3: video_ext.php?oid=OWNER&id=VIDEO
    match3 = re.search(r'oid=(-?\d+)&id=(\d+)', video_url)
    
    video_id = None
    if match1:
        video_id = match1.group(1)
    elif match2:
        video_id = match2.group(1)
    elif match3:
        oid, vid = match3.groups()
        video_id = f"{oid}_{vid}"
    
    if not video_id:
        return None
    
    # Build URLs
    if '_' in video_id:
        oid, vid = video_id.split('_')
        embed_url = f"https://vk.com/video_ext.php?oid={oid}&id={vid}&lang=en"
        vk_url = f"https://vk.com/video{video_id}"
    else:
        embed_url = f"https://vk.com/video_ext.php?oid={video_id}&id=0&lang=en"
        vk_url = f"https://vk.com/video{video_id}"
    
    return {
        'video_id': video_id,
        'title': f"Video {video_id}",  # Will be updated when fetching metadata
        'url': vk_url,
        'embed_url': embed_url,
        'created_time': ""
    }


def fetch_video_metadata(video_data, opener):
    """
    Fetches metadata (title, date) for a single video.
    
    Args:
        video_data: Video data dictionary
        opener: urllib opener instance
        
    Returns:
        dict: Updated video data with metadata
    """
    try:
        video_response = opener.open(video_data['url'], timeout=10)
        
        # Handle gzip encoding if present
        content = video_response.read()
        content_encoding = video_response.headers.get('Content-Encoding', '').lower()
        if content_encoding == 'gzip':
            content = gzip.decompress(content)
        
        video_html = content.decode('utf-8', errors='ignore')
        video_response.close()
        
        # Extract title from page
        title_match = re.search(r'<title>([^<]+)</title>', video_html)
        if title_match:
            title = title_match.group(1).strip()
            # Remove " | VK" suffix if present
            title = title.replace(' | VK', '').replace(' | ВКонтакте', '').strip()
            if title:
                video_data['title'] = title
        
        # Extract date
        date_match = re.search(r'<meta[^>]*property="article:published_time"[^>]*content="([^"]+)"', video_html)
        if date_match:
            video_data['created_time'] = date_match.group(1)
        else:
            # Try to find date in other formats
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', video_html)
            if date_match:
                video_data['created_time'] = date_match.group(1) + "T00:00:00Z"
    except Exception as e:
        print(f"    Could not fetch metadata for {video_data.get('url', 'unknown')}: {e}")
    
    return video_data


def format_archive_item(video):
    """
    Formats a VK video into the archive item format.
    
    Args:
        video: Raw video data from VK
        
    Returns:
        dict: Formatted archive item
    """
    video_id = video.get('video_id', '')
    url = video.get('url', '')
    embed_url = video.get('embed_url', '')
    title = video.get('title', 'Untitled')
    created_time = video.get('created_time', '')
    
    # Ensure embed_url is properly formatted
    if not embed_url and video_id:
        if '_' in video_id:
            oid, vid = video_id.split('_')
            embed_url = f"https://vk.com/video_ext.php?oid={oid}&id={vid}&lang=en"
        else:
            embed_url = f"https://vk.com/video_ext.php?oid={video_id}&id=0&lang=en"
    
    # Ensure URL is complete
    if url and not url.startswith('http'):
        url = f"https://vk.com{url}"
    elif not url and video_id:
        if '_' in video_id:
            url = f"https://vk.com/video{video_id}"
        else:
            url = f"https://vk.com/video{video_id}"
    
    return {
        "platform": "vk",
        "title": title,
        "url": url,
        "embedUrl": embed_url,
        "key": video_id,
        "created_time": created_time,
        "play_count": 0,
        "listener_count": 0,
        "favorite_count": 0,
        "repost_count": 0
    }


def fetch_vk_playlist_with_scraper(playlist_url, username=None, password=None):
    """
    Fetches video data using vk-url-scraper library (requires authentication).
    
    Args:
        playlist_url: The VK playlist URL
        username: VK username (optional, will prompt if not provided)
        password: VK password (optional, will prompt if not provided)
        
    Returns:
        list: List of video items
    """
    try:
        from vk_url_scraper import VkScraper
    except ImportError:
        print("Error: vk-url-scraper library not installed.")
        print("Install it with: pip install vk-url-scraper")
        print("Also install: pip install git+https://github.com/python273/vk_api.git@b99dac0ec2f832a6c4b20bde49869e7229ce4742")
        return []
    
    videos = []
    
    # Try to get credentials from environment variables if not provided
    import os
    if not username:
        username = os.environ.get('VK_USERNAME', '').strip()
    if not password:
        password = os.environ.get('VK_PASSWORD', '').strip()
    
    # If still not provided, try to prompt (only if stdin is available)
    if not username:
        try:
            username = input("Enter VK username: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("Error: VK username is required.")
            print("Provide it via --vk-username argument or VK_USERNAME environment variable.")
            return []
    
    if not password:
        try:
            import getpass
            password = getpass.getpass("Enter VK password: ")
        except (EOFError, KeyboardInterrupt):
            print("Error: VK password is required.")
            print("Provide it via --vk-password argument or VK_PASSWORD environment variable.")
            return []
    
    print(f"Using vk-url-scraper to fetch playlist...")
    try:
        # Try to use vk_api directly first to handle 2FA if needed
        try:
            import vk_api
            from vk_api.exceptions import AuthError
            
            # 2FA handler function
            def two_factor_handler():
                """Handle 2FA code input."""
                try:
                    code = input("Enter 2FA code (or press Enter if not needed): ").strip()
                    remember_device = False
                    if code.lower() == 'y' or code.lower() == 'yes':
                        remember_device = True
                        code = input("Enter 2FA code: ").strip()
                    return code, remember_device
                except (EOFError, KeyboardInterrupt):
                    return None, False
            
            # Try to authenticate with vk_api first (supports 2FA)
            session_file = 'vk_config.v2.json'
            token = None
            
            # Check for existing session
            if os.path.exists(session_file):
                try:
                    with open(session_file, 'r') as f:
                        import json
                        session_data = json.load(f)
                        token = session_data.get('token')
                        if token:
                            print("  Found existing token in session file")
                except Exception as e:
                    print(f"  Could not read session file: {e}")
            
            # Authenticate if no valid token
            if not token:
                print("  Authenticating with VK API (2FA supported)...")
                try:
                    vk_session = vk_api.VkApi(
                        login=username,
                        password=password,
                        auth_handler=two_factor_handler,
                        token=token
                    )
                    vk_session.auth()
                    token = vk_session.token.get('access_token')
                    print("  Authentication successful")
                except AuthError as e:
                    print(f"  Authentication failed: {e}")
                    print("  This might be due to:")
                    print("    - Incorrect username/password")
                    print("    - 2FA code not provided")
                    print("    - Account restrictions")
                    raise
            
            # Now use vk-url-scraper with the token
            if token:
                print("  Using authenticated session with vk-url-scraper...")
                vks = VkScraper(username, password, token=token, session_file=session_file)
            else:
                vks = VkScraper(username, password, session_file=session_file)
                
        except ImportError:
            # Fallback to vk-url-scraper without 2FA handling
            print("  vk_api not available, using vk-url-scraper directly...")
            session_file = 'vk_config.v2.json'
            vks = VkScraper(username, password, session_file=session_file)
        
        print("  Scraping playlist...")
        result = vks.scrape(playlist_url)
        
        for item in result:
            # Extract video ID from URL if available
            video_url = item.get('url', '')
            video_id_match = re.search(r'/video-?(\d+_\d+)', video_url)
            if video_id_match:
                video_id = video_id_match.group(1)
            else:
                # Try to extract from other fields
                video_id = item.get('id', '') or item.get('video_id', '')
            
            if video_id:
                oid, vid = video_id.split('_') if '_' in video_id else (video_id, '0')
                embed_url = f"https://vk.com/video_ext.php?oid={oid}&id={vid}&lang=en"
                
                # Parse date if available
                created_time = ""
                if item.get('datetime'):
                    try:
                        # Try to parse various date formats
                        date_str = str(item.get('datetime'))
                        # Common formats: "2024-01-01", "2024-01-01 12:00:00", etc.
                        if 'T' in date_str:
                            created_time = date_str
                        elif ' ' in date_str:
                            created_time = date_str.replace(' ', 'T') + 'Z'
                        else:
                            created_time = date_str + "T00:00:00Z"
                    except:
                        pass
                
                videos.append({
                    'video_id': video_id,
                    'title': item.get('title', item.get('text', f"Video {video_id}")),
                    'url': video_url or f"https://vk.com/video{video_id}",
                    'embed_url': embed_url,
                    'created_time': created_time
                })
        
        print(f"  Found {len(videos)} videos using vk-url-scraper")
    except Exception as e:
        print(f"  Error using vk-url-scraper: {e}")
        import traceback
        traceback.print_exc()
    
    return videos


def main():
    """Main function to fetch VK playlist data and generate JSON."""
    # Parse command line arguments
    playlist_url = "https://vkvideo.ru/playlist/512257790_1"
    use_vk_scraper = False
    vk_username = None
    vk_password = None
    video_urls = []  # For manually specified video URLs
    
    if len(sys.argv) > 1:
        first_arg = sys.argv[1]
        # Check if it's a playlist URL or a video URL
        if '/playlist/' in first_arg and '/video' not in first_arg:
            # It's a playlist URL (not a specific video in playlist)
            playlist_url = first_arg
        elif '/video' in first_arg:
            # Treat as video URL(s) - collect all video URLs
            video_urls.append(first_arg)
            playlist_url = None
    
    # Check for optional flags and additional video URLs
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == '--use-vk-scraper':
            use_vk_scraper = True
        elif sys.argv[i] == '--vk-username' and i + 1 < len(sys.argv):
            vk_username = sys.argv[i + 1]
            i += 1
        elif sys.argv[i] == '--vk-password' and i + 1 < len(sys.argv):
            vk_password = sys.argv[i + 1]
            i += 1
        elif '/video' in sys.argv[i]:
            video_urls.append(sys.argv[i])
        i += 1
    
    print(f"\n=== Fetching VK Video Playlist ===")
    
    videos = []
    
    # If video URLs were provided, extract from them
    if video_urls:
        print(f"Extracting videos from {len(video_urls)} provided URL(s)...")
        cookie_jar = CookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
        opener.addheaders = [
            ('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'),
            ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'),
            ('Accept-Language', 'en-GB,en;q=0.9,ru;q=0.8'),
            ('Accept-Encoding', 'gzip, deflate'),
        ]
        
        for video_url in video_urls:
            video_data = extract_video_from_url(video_url)
            if video_data:
                print(f"  Extracted video ID: {video_data['video_id']} from {video_url}")
                # Fetch metadata
                print(f"    Fetching metadata...")
                video_data = fetch_video_metadata(video_data, opener)
                if video_data.get('title') and video_data['title'] != f"Video {video_data['video_id']}":
                    print(f"    Found title: {video_data['title']}")
                videos.append(video_data)
            else:
                print(f"  Could not extract video ID from: {video_url}")
    
    # Also try to fetch from playlist if URL provided (and no specific videos were given)
    if playlist_url and not video_urls:
        if use_vk_scraper:
            scraper_videos = fetch_vk_playlist_with_scraper(playlist_url, vk_username, vk_password)
            videos.extend(scraper_videos)
            # If scraper didn't find videos, fall back to HTML parsing
            if not scraper_videos:
                print("  Falling back to HTML parsing...")
                playlist_videos = fetch_vk_playlist(playlist_url)
                videos.extend(playlist_videos)
        else:
            playlist_videos = fetch_vk_playlist(playlist_url)
            videos.extend(playlist_videos)
    
        if not videos:
            print("\nNo videos found in playlist.")
            print("\nNote: VK playlists are often JavaScript-rendered, meaning video data")
            print("is loaded dynamically after the page loads. Static HTML parsing may not")
            print("capture all videos. Consider:")
            print("  1. Using a headless browser (Selenium/Playwright) for full rendering")
            print("  2. Manually adding videos to data/archives.json")
            print("  3. Using VK API if available (requires authentication)")
            return 1
    
    # Format videos
    formatted_videos = [format_archive_item(video) for video in videos]
    
    # Read existing JSON to preserve audio entries
    output_path = Path(__file__).parent.parent / "data" / "archives.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    existing_data = {}
    if output_path.exists():
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except Exception as e:
            print(f"Warning: Could not read existing JSON file: {e}")
    
    # Ensure audio is always an array (required by config.js validation)
    existing_audio = existing_data.get("audio", [])
    if not isinstance(existing_audio, list):
        existing_audio = []
    
    # Merge videos: keep existing ones that aren't in the playlist, add new ones
    existing_video = existing_data.get("video", [])
    if not isinstance(existing_video, list):
        existing_video = []
    
    # Create a set of existing video keys to avoid duplicates
    existing_keys = {item.get('key', '') for item in existing_video}
    
    # Add new videos that aren't already in the list
    for video in formatted_videos:
        if video.get('key') and video.get('key') not in existing_keys:
            existing_video.append(video)
            existing_keys.add(video.get('key'))
    
    # Sort videos by date (newest first)
    existing_video.sort(key=lambda x: x.get('created_time', ''), reverse=True)
    
    # Create output structure, preserving existing audio entries
    output = {
        "audio": existing_audio,
        "video": existing_video
    }
    
    # Write to JSON file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n=== Successfully generated {output_path} ===")
    print(f"Total video items: {len(existing_video)}")
    print(f"  - New videos added: {len(formatted_videos)}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

