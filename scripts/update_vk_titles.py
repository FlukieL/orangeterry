#!/usr/bin/env python3
"""
Update VK video titles and created_time dates in archives.json by fetching each URL.
"""

import json
import urllib.request
import urllib.parse
import urllib.error
import gzip
import re
from pathlib import Path
from http.cookiejar import CookieJar
from datetime import datetime


def parse_date(date_str):
    """
    Parses various date formats and converts to ISO 8601 format.
    
    Args:
        date_str: Date string in various formats
        
    Returns:
        str: ISO 8601 formatted date string (YYYY-MM-DDTHH:MM:SSZ) or None
    """
    if not date_str:
        return None
    
    # Common date formats to try
    date_formats = [
        '%Y-%m-%dT%H:%M:%S%z',  # ISO 8601 with timezone
        '%Y-%m-%dT%H:%M:%SZ',   # ISO 8601 UTC
        '%Y-%m-%dT%H:%M:%S',     # ISO 8601 without timezone
        '%Y-%m-%d %H:%M:%S',    # Standard datetime
        '%Y-%m-%d',              # Date only
        '%d.%m.%Y',              # DD.MM.YYYY
        '%d/%m/%Y',              # DD/MM/YYYY
        '%m/%d/%Y',              # MM/DD/YYYY
    ]
    
    for fmt in date_formats:
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            # Convert to ISO 8601 format with Z suffix
            return dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        except ValueError:
            continue
    
    # Try to extract date from timestamp (Unix timestamp)
    try:
        timestamp = int(date_str)
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime('%Y-%m-%dT%H:%M:%SZ')
    except (ValueError, TypeError):
        pass
    
    return None


def extract_video_id_from_url(url):
    """
    Extracts video ID from VK URL to construct the actual video page URL.
    
    Args:
        url: VK video URL (playlist or direct)
        
    Returns:
        tuple: (owner_id, video_id) or None
    """
    # Pattern 1: vkvideo.ru/playlist/OWNER_PLAYLIST/video-OWNER_VIDEO
    match1 = re.search(r'/playlist/\d+_\d+/video-(\d+)_(\d+)', url)
    if match1:
        return (match1.group(1), match1.group(2))
    
    # Pattern 2: vkvideo.ru/playlist/OWNER_PLAYLIST/videoOWNER_VIDEO
    match2 = re.search(r'/playlist/\d+_\d+/video(\d+)_(\d+)', url)
    if match2:
        return (match2.group(1), match2.group(2))
    
    # Pattern 3: vk.com/video-OWNER_VIDEO or /videoOWNER_VIDEO
    match3 = re.search(r'/video-?(\d+)_(\d+)', url)
    if match3:
        return (match3.group(1), match3.group(2))
    
    return None


def fetch_video_metadata(url):
    """
    Fetches a VK video page and extracts the title and created_time.
    
    Args:
        url: VK video URL
        
    Returns:
        dict: Dictionary with 'title' and 'created_time' keys, or None if extraction fails
    """
    try:
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
        ]
        
        # Try to get the actual VK video page URL if we have a playlist URL
        video_ids = extract_video_id_from_url(url)
        urls_to_try = [url]  # Prefer the original URL (playlist URL works better for titles)
        if video_ids:
            owner_id, video_id = video_ids
            # Try the actual VK video page URL as a fallback (might have better date info)
            vk_video_url = f"https://vk.com/video{owner_id}_{video_id}"
            urls_to_try.append(vk_video_url)
        
        html = None
        htmls = []  # Store HTML from all URLs tried
        final_url = None
        
        for url_to_try in urls_to_try:
            try:
                print(f"  Fetching: {url_to_try}")
                response = opener.open(url_to_try, timeout=15)
                final_url = response.geturl()
                
                # Handle gzip encoding if present
                content = response.read()
                content_encoding = response.headers.get('Content-Encoding', '').lower()
                if content_encoding == 'gzip':
                    content = gzip.decompress(content)
                
                page_html = content.decode('utf-8', errors='ignore')
                response.close()
                htmls.append((url_to_try, page_html))
                if not html:  # Use first successful fetch as primary
                    html = page_html
            except Exception as e:
                if url_to_try == urls_to_try[-1] and not html:  # Last URL and no HTML yet
                    raise
                continue
        
        if not html:
            raise Exception("Failed to fetch any URL")
        
        result = {'title': None, 'created_time': None}
        
        # Extract title from page - prefer the first HTML (usually playlist URL)
        # Try multiple patterns for title extraction
        title_patterns = [
            r'<title>([^<]+)</title>',
            r'<meta[^>]*property=["\']og:title["\'][^>]*content=["\']([^"\']+)["\']',
            r'<meta[^>]*name=["\']title["\'][^>]*content=["\']([^"\']+)["\']',
            r'"title"\s*:\s*"([^"]+)"',
            r'<h1[^>]*>([^<]+)</h1>',
        ]
        
        # Use the first HTML (playlist URL) for title extraction as it works better
        primary_html = htmls[0][1] if htmls else html
        
        for pattern in title_patterns:
            title_match = re.search(pattern, primary_html, re.IGNORECASE)
            if title_match:
                title = title_match.group(1).strip()
                # Remove " | VK" suffix if present
                title = title.replace(' | VK', '').replace(' | ВКонтакте', '').strip()
                # Remove " Video" suffix that sometimes appears
                title = re.sub(r'\s+Video\s*$', '', title, flags=re.IGNORECASE)
                # Skip generic titles like "Katerina Petrovna's Videos"
                if title and len(title) > 3 and 'Videos' not in title and 'Video' not in title:
                    result['title'] = title
                    break
        
        # If no title found with patterns, try to find it in JSON data
        # VK often embeds data in script tags - search primary HTML first
        if not result['title']:
            json_patterns = [
                r'window\.vkData\s*=\s*({.+?});',
                r'var\s+vkData\s*=\s*({.+?});',
                r'window\.__INITIAL_STATE__\s*=\s*({.+?});',
            ]
            
            for pattern in json_patterns:
                json_match = re.search(pattern, primary_html, re.DOTALL)
                if json_match:
                    try:
                        json_str = json_match.group(1)
                        json_data = json.loads(json_str)
                        # Try to find title in JSON structure
                        if isinstance(json_data, dict):
                            # Common locations for title in VK JSON
                            for key in ['title', 'name', 'video_title', 'text']:
                                if key in json_data:
                                    title = str(json_data[key]).strip()
                                    # Remove " Video" suffix
                                    title = re.sub(r'\s+Video\s*$', '', title, flags=re.IGNORECASE)
                                    if title and len(title) > 3 and 'Videos' not in title:
                                        result['title'] = title
                                        break
                    except:
                        pass
        
        # Extract created_time from page - search all HTML sources
        # Try multiple patterns for date extraction
        date_patterns = [
            r'<meta[^>]*property=["\']article:published_time["\'][^>]*content=["\']([^"\']+)["\']',
            r'<meta[^>]*property=["\']video:release_date["\'][^>]*content=["\']([^"\']+)["\']',
            r'<meta[^>]*name=["\']date["\'][^>]*content=["\']([^"\']+)["\']',
            r'<time[^>]*datetime=["\']([^"\']+)["\']',
            r'"date["\']?\s*:\s*["\']([^"\']+)["\']',
            r'"created_time["\']?\s*:\s*["\']([^"\']+)["\']',
            r'"published_time["\']?\s*:\s*["\']([^"\']+)["\']',
            r'"date_published["\']?\s*:\s*["\']([^"\']+)["\']',
            r'"date_added["\']?\s*:\s*["\']([^"\']+)["\']',
            r'"added_date["\']?\s*:\s*["\']([^"\']+)["\']',
            r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z?)',  # ISO 8601 format
            r'(\d{4}-\d{2}-\d{2})',  # Date only
        ]
        
        # Search through all HTML sources for dates
        all_htmls = [html] + [h[1] for h in htmls[1:]] if htmls else [html]
        for html_source in all_htmls:
            for pattern in date_patterns:
                date_match = re.search(pattern, html_source, re.IGNORECASE)
                if date_match:
                    date_str = date_match.group(1).strip()
                    parsed_date = parse_date(date_str)
                    if parsed_date:
                        result['created_time'] = parsed_date
                        break
            if result['created_time']:
                break
        
        # Also try to find Unix timestamps in the HTML (common in JavaScript) - search all HTML sources
        if not result['created_time']:
            # Look for Unix timestamps (10 or 13 digits)
            timestamp_patterns = [
                r'"date["\']?\s*:\s*(\d{10,13})',
                r'"created_time["\']?\s*:\s*(\d{10,13})',
                r'"published_time["\']?\s*:\s*(\d{10,13})',
                r'"date_published["\']?\s*:\s*(\d{10,13})',
                r'"added_date["\']?\s*:\s*(\d{10,13})',
                r'"timestamp["\']?\s*:\s*(\d{10,13})',
            ]
            
            for html_source in all_htmls:
                for pattern in timestamp_patterns:
                    timestamp_match = re.search(pattern, html_source, re.IGNORECASE)
                    if timestamp_match:
                        timestamp_str = timestamp_match.group(1).strip()
                        try:
                            # Handle both seconds (10 digits) and milliseconds (13 digits)
                            timestamp = int(timestamp_str)
                            if len(timestamp_str) == 13:
                                timestamp = timestamp // 1000  # Convert milliseconds to seconds
                            dt = datetime.fromtimestamp(timestamp)
                            result['created_time'] = dt.strftime('%Y-%m-%dT%H:%M:%SZ')
                            break
                        except (ValueError, OSError):
                            continue
                if result['created_time']:
                    break
        
        # Try to extract date from JSON data in script tags - search all HTML sources
        if not result['created_time']:
            json_patterns = [
                r'window\.vkData\s*=\s*({.+?});',
                r'var\s+vkData\s*=\s*({.+?});',
                r'window\.__INITIAL_STATE__\s*=\s*({.+?});',
                r'window\.__DATA__\s*=\s*({.+?});',
            ]
            
            for html_source in all_htmls:
                for pattern in json_patterns:
                    json_match = re.search(pattern, html_source, re.DOTALL)
                    if json_match:
                        try:
                            json_str = json_match.group(1)
                            json_data = json.loads(json_str)
                            # Recursively search for date fields in JSON
                            def find_date_in_json(obj, depth=0):
                                if depth > 5:  # Limit recursion depth
                                    return None
                                if isinstance(obj, dict):
                                    for key, value in obj.items():
                                        if any(term in key.lower() for term in ['date', 'time', 'created', 'published', 'added']):
                                            if isinstance(value, (int, float)) and value > 1000000000:  # Looks like a timestamp
                                                try:
                                                    dt = datetime.fromtimestamp(int(value) if len(str(int(value))) <= 10 else int(value) // 1000)
                                                    return dt.strftime('%Y-%m-%dT%H:%M:%SZ')
                                                except:
                                                    pass
                                            elif isinstance(value, str):
                                                parsed = parse_date(value)
                                                if parsed:
                                                    return parsed
                                        elif isinstance(value, (dict, list)):
                                            result = find_date_in_json(value, depth + 1)
                                            if result:
                                                return result
                                elif isinstance(obj, list):
                                    for item in obj:
                                        result = find_date_in_json(item, depth + 1)
                                        if result:
                                            return result
                                return None
                            
                            found_date = find_date_in_json(json_data)
                            if found_date:
                                result['created_time'] = found_date
                                break
                        except:
                            pass
                if result['created_time']:
                    break
        
        # If we found at least title or date, return the result
        if result['title'] or result['created_time']:
            return result
        
        return None
        
    except urllib.error.HTTPError as e:
        print(f"    HTTP Error {e.code} for {url}")
        return None
    except Exception as e:
        print(f"    Error fetching {url}: {type(e).__name__}: {e}")
        return None


def update_vk_metadata(archives_path):
    """
    Updates titles and created_time for all VK video entries in archives.json.
    
    Args:
        archives_path: Path to archives.json file
    """
    # Read existing JSON
    with open(archives_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    video_entries = data.get('video', [])
    vk_entries = [entry for entry in video_entries if entry.get('platform') == 'vk']
    
    if not vk_entries:
        print("No VK video entries found in archives.json")
        return
    
    print(f"Found {len(vk_entries)} VK video entries to update")
    print()
    
    updated_titles = 0
    updated_dates = 0
    failed_count = 0
    
    for i, entry in enumerate(vk_entries, 1):
        current_title = entry.get('title', '')
        current_date = entry.get('created_time', '')
        url = entry.get('url', '')
        
        if not url:
            print(f"{i}/{len(vk_entries)}: No URL found, skipping")
            failed_count += 1
            continue
        
        print(f"{i}/{len(vk_entries)}: {current_title}")
        
        # Fetch the metadata from the URL
        metadata = fetch_video_metadata(url)
        
        if metadata:
            # Update title if found and different
            if metadata.get('title'):
                if metadata['title'] != current_title:
                    print(f"    Title updated: '{current_title}' -> '{metadata['title']}'")
                    entry['title'] = metadata['title']
                    updated_titles += 1
                else:
                    print(f"    Title already correct: '{metadata['title']}'")
            
            # Update created_time if found and different
            if metadata.get('created_time'):
                if metadata['created_time'] != current_date:
                    print(f"    Date updated: '{current_date}' -> '{metadata['created_time']}'")
                    entry['created_time'] = metadata['created_time']
                    updated_dates += 1
                else:
                    print(f"    Date already correct: '{metadata['created_time']}'")
            elif current_date:
                print(f"    Date not found on page (current: '{current_date}')")
            else:
                print(f"    Date not found on page (currently empty)")
            
            # If we got metadata but neither title nor date was updated, it means they were already correct
            if not metadata.get('title') and not metadata.get('created_time'):
                print(f"    No metadata found on page")
        else:
            print(f"    Failed to extract metadata")
            failed_count += 1
        
        print()
    
    # Write updated JSON back to file
    if updated_titles > 0 or updated_dates > 0:
        with open(archives_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"=== Update Complete ===")
        print(f"Updated titles: {updated_titles}")
        print(f"Updated dates: {updated_dates}")
        print(f"Failed: {failed_count} entries")
        print(f"Total: {len(vk_entries)} entries")
    else:
        print("No metadata was updated")


def main():
    """Main function."""
    # Get the path to archives.json
    script_dir = Path(__file__).parent
    archives_path = script_dir.parent / "data" / "archives.json"
    
    if not archives_path.exists():
        print(f"Error: {archives_path} not found")
        return 1
    
    print(f"Updating VK video titles and dates in {archives_path}")
    print()
    
    update_vk_metadata(archives_path)
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
