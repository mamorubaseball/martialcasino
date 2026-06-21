#!/usr/bin/env python3
import os
import sys
import json
import re
import urllib.request
import urllib.parse
from datetime import datetime

def get_channel_uploads_playlist_id(api_key, handle):
    if not handle.startswith('@'):
        handle = '@' + handle
    
    url = f"https://www.googleapis.com/youtube/v3/channels?key={api_key}&forHandle={urllib.parse.quote(handle)}&part=contentDetails"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            if not data.get("items"):
                print(f"Error: Channel with handle {handle} not found.")
                return None
            uploads_id = data["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
            return uploads_id
    except Exception as e:
        print(f"Failed to get channel details for {handle}: {e}")
        return None

def fetch_videos_from_playlist(api_key, playlist_id, start_date, end_date):
    videos = []
    page_token = ""
    
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    
    while True:
        url = f"https://www.googleapis.com/youtube/v3/playlistItems?key={api_key}&playlistId={playlist_id}&part=snippet&maxResults=50"
        if page_token:
            url += f"&pageToken={page_token}"
            
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                items = data.get("items", [])
                
                if not items:
                    break
                
                for item in items:
                    snippet = item["snippet"]
                    pub_date_str = snippet["publishedAt"][:10]  # YYYY-MM-DD
                    pub_dt = datetime.strptime(pub_date_str, "%Y-%m-%d")
                    
                    if start_dt <= pub_dt <= end_dt:
                        video_id = snippet["resourceId"]["videoId"]
                        videos.append({
                            "title": snippet["title"],
                            "url": f"https://youtu.be/{video_id}",
                            "publishedAt": pub_date_str
                        })
                    elif pub_dt < start_dt:
                        pass
                
                page_token = data.get("nextPageToken")
                if not page_token or (items and datetime.strptime(items[-1]["snippet"]["publishedAt"][:10], "%Y-%m-%d") < start_dt):
                    break
        except Exception as e:
            print(f"Error fetching playlist items: {e}")
            break
            
    return videos

def fetch_videos_via_scraping(handle):
    if not handle.startswith('@'):
        handle = '@' + handle
    url = f"https://www.youtube.com/{handle}/videos"
    
    print(f"Attempting to scrape videos directly from {url}...")
    req = urllib.request.Request(
        url, 
        headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8'
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode('utf-8')
            
        match = re.search(r'var ytInitialData\s*=\s*({.*?});</script>', html)
        if not match:
            match = re.search(r'window\["ytInitialData"\]\s*=\s*({.*?});', html)
            
        if not match:
            print("  Warning: Could not extract ytInitialData. Scraping failed.")
            return []
            
        data = json.loads(match.group(1))
        
        tabs = data.get("contents", {}).get("twoColumnBrowseResultsRenderer", {}).get("tabs", [])
        videos_tab = None
        for tab in tabs:
            tab_renderer = tab.get("tabRenderer", {})
            title = tab_renderer.get("title", "")
            if title in ["動画", "Videos"] or "videos" in tab_renderer.get("endpoint", {}).get("browseEndpoint", {}).get("params", "").lower():
                videos_tab = tab_renderer
                break
                
        if not videos_tab:
            if len(tabs) > 0:
                videos_tab = tabs[0].get("tabRenderer", {})
            else:
                return []
                
        contents = videos_tab.get("content", {}).get("richGridRenderer", {}).get("contents", [])
        
        videos = []
        for item in contents:
            rich_item = item.get("richItemRenderer", {}).get("content", {})
            
            # YouTube の新しい ViewModel 構造を処理
            if "lockupViewModel" in rich_item:
                lvm = rich_item["lockupViewModel"]
                video_id = lvm.get("contentId")
                
                lmvm = lvm.get("metadata", {}).get("lockupMetadataViewModel", {})
                title_text = lmvm.get("title", {}).get("content", "")
                
                # 投稿日時の相対テキスト抽出
                published_text = ""
                rows = lmvm.get("metadata", {}).get("contentMetadataViewModel", {}).get("metadataRows", [])
                for row in rows:
                    parts = row.get("metadataParts", [])
                    for part in parts:
                        text = part.get("text", {}).get("content", "")
                        if any(x in text for x in ["前", "日", "週", "月", "年", "時間"]):
                            published_text = text
                            break
                    if published_text:
                        break
                
                if video_id and title_text:
                    videos.append({
                        "title": title_text,
                        "url": f"https://youtu.be/{video_id}",
                        "publishedAt": published_text
                    })
            
            # 旧 videoRenderer 構造のフォールバック
            elif "videoRenderer" in rich_item:
                video_renderer = rich_item["videoRenderer"]
                video_id = video_renderer.get("videoId")
                
                title_text = ""
                runs = video_renderer.get("title", {}).get("runs", [])
                if runs:
                    title_text = runs[0].get("text", "")
                    
                published_text = ""
                pub_runs = video_renderer.get("publishedTimeText", {}).get("runs", [])
                if pub_runs:
                    published_text = pub_runs[0].get("text", "")
                    
                if video_id and title_text:
                    videos.append({
                        "title": title_text,
                        "url": f"https://youtu.be/{video_id}",
                        "publishedAt": published_text
                    })
                
        return videos
    except Exception as e:
        print(f"  Scraping failed: {e}")
        return []

def main():
    api_key = os.environ.get("YOUTUBE_API_KEY")
    
    channels = {
        "techmoney": "TechMoney-1billion",
        "kabumaru": "kabumaru-mmm"
    }
    
    start_date = "2026-04-01"
    end_date = "2026-06-30"
    
    for name, handle in channels.items():
        videos = []
        if api_key:
            print(f"Fetching uploads for {name} ({handle}) via YouTube API...")
            playlist_id = get_channel_uploads_playlist_id(api_key, handle)
            if playlist_id:
                videos = fetch_videos_from_playlist(api_key, playlist_id, start_date, end_date)
        
        if not videos:
            if not api_key:
                print(f"No YOUTUBE_API_KEY found. Falling back to scraping for {name} ({handle})...")
            else:
                print(f"API fetch failed. Falling back to scraping for {name} ({handle})...")
            videos = fetch_videos_via_scraping(handle)
            
        print(f"Found {len(videos)} videos for {name}.")
        
        # JSONファイルとして保存
        out_path = f"scripts/youtube_videos_{name}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(videos, f, ensure_ascii=False, indent=2)
        print(f"Saved to {out_path}")

if __name__ == "__main__":
    main()
