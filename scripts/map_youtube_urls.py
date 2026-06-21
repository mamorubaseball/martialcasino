#!/usr/bin/env python3
import os
import sys
import re
import json
import unicodedata
from datetime import datetime, timedelta

# 設定
TARGET_BLOG_DIR = "/Users/mamoru/AntigravityCompany/投資メディア事業/martialcasino"
SOURCES = {
    "techmoney": "/Users/mamoru/Library/CloudStorage/GoogleDrive-mamorubasebaii9045@gmail.com/その他のパソコン/マイ Mac/techmoney",
    "kabumaru": "/Users/mamoru/Library/CloudStorage/GoogleDrive-mamorubasebaii9045@gmail.com/その他のパソコン/マイ Mac/kabu_maru"
}

# 基準となる日付（システム日付が2026年6月21日なのでこれを使用）
CURRENT_DATE = datetime(2026, 6, 21)

def parse_relative_time(relative_str):
    # 相対表記を現在（2026-06-21）からの日数差に変換
    # 例: "7 時間前", "1 日前", "2 週間前", "1 か月前"
    relative_str = relative_str.strip()
    
    if "時間前" in relative_str:
        return 0
        
    match_day = re.search(r'(\d+)\s*日前', relative_str)
    if match_day:
        return int(match_day.group(1))
        
    match_week = re.search(r'(\d+)\s*週間前', relative_str)
    if match_week:
        return int(match_week.group(1)) * 7
        
    match_month = re.search(r'(\d+)\s*か月前', relative_str)
    if match_month:
        return int(match_month.group(1)) * 30
        
    return 999  # 不明な場合は大きな差にする

def clean_text(text):
    if not text:
        return ""
    # MacのNFD濁点問題を解決するためNFCに正規化
    text = unicodedata.normalize('NFC', text)
    text = text.lower()
    text = re.sub(r'[\s_\-\[\]【】()（）！？!?/・]', '', text)
    # アルファベット表記揺れやカタカナ表記揺れを一部簡易変換
    replacements = {
        "エヌビディア": "nvidia",
        "スペースx": "spacex",
        "アンソロピック": "anthropic",
        "クアルコム": "qcom",
        "マーベル": "mrvl",
        "ソフィ": "sofi",
        "ふじくら": "fujikura",
        "フジクラ": "fujikura",
        "メタプラ": "metaplanet",
        "メタプラネット": "metaplanet"
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text

def calculate_score(folder_base, folder_date, folder_text, video_title, video_date_approx):
    score = 0
    
    # 1. 日付の近さスコア（最大 40点）
    # フォルダの日付（例: 20260609 -> 2026-06-09）
    try:
        f_dt = datetime.strptime(folder_date, "%Y%m%d")
        days_diff = abs((f_dt - video_date_approx).days)
        if days_diff <= 2:
            score += 40
        elif days_diff <= 5:
            score += 30
        elif days_diff <= 10:
            score += 20
        elif days_diff <= 15:
            score += 10
    except Exception:
        pass
        
    # 2. キーワード（フォルダのベース名）が動画タイトルに含まれているか（最大 50点）
    # 例: folder_base="gsx", video_title="GSX割安サーバー..."
    norm_base = clean_text(folder_base)
    norm_title = clean_text(video_title)
    
    if norm_base in norm_title or norm_title in norm_base:
        score += 50
    else:
        # 部分一致（文字の重なり）
        intersection = set(norm_base) & set(norm_title)
        if len(intersection) >= 2:
            score += len(intersection) * 3
            
    # 3. 台本テキスト内に動画タイトルの言葉が含まれているか（最大 20点）
    # タイトルから特徴的な単語を切り抜いて台本内での出現頻度を見る
    norm_text = clean_text(folder_text)
    keywords = re.findall(r'[a-zA-Z0-9]{3,}|[\u4e00-\u9faf]{2,}', video_title)
    match_count = 0
    for kw in keywords:
        kw_clean = clean_text(kw)
        if len(kw_clean) >= 2 and kw_clean in norm_text:
            match_count += 1
            
    if keywords:
        score += min(20, int((match_count / len(keywords)) * 20))
        
    return score

def find_transcript_content(folder_path):
    # 台本ファイルを探索して一部読み込む
    for f in os.listdir(folder_path):
        f_lower = f.lower()
        if f_lower.endswith(".md") and f_lower != "gaiyou.md" and f_lower != "url.md" and f_lower != "none_url.md":
            try:
                with open(os.path.join(folder_path, f), "r", encoding="utf-8") as file:
                    return file.read()
            except Exception:
                pass
                
    # もしHTML要約があればそれを使う
    for f in os.listdir(folder_path):
        if f.lower() == "video_summary.html":
            try:
                with open(os.path.join(folder_path, f), "r", encoding="utf-8") as file:
                    html = file.read()
                    text = re.sub(r'<[^>]+>', '', html)
                    return text
            except Exception:
                pass
    return ""

def main():
    print(f"Starting local matching process (Base Date: {CURRENT_DATE.strftime('%Y-%m-%d')})...")
    
    for source_name, source_dir in SOURCES.items():
        if not os.path.exists(source_dir):
            print(f"Source directory not found: {source_dir}")
            continue
            
        print(f"\n=== Processing source: {source_name} ===")
        
        # 動画リストの読み込み
        list_path = f"scripts/youtube_videos_{source_name}.json"
        if not os.path.exists(list_path):
            print(f"Video list file {list_path} not found. Skipping {source_name}.")
            continue
            
        with open(list_path, "r", encoding="utf-8") as lf:
            video_list = json.load(lf)
            
        if not video_list:
            print(f"Video list {list_path} is empty. Skipping.")
            continue
            
        # 動画リストの投稿日を概算
        for video in video_list:
            days_ago = parse_relative_time(video["publishedAt"])
            video["approx_date"] = CURRENT_DATE - timedelta(days=days_ago)
            
        # 年月フォルダを走査
        years = ["202604", "202605", "202606"]
        matched_count = 0
        none_count = 0
        
        for year in years:
            year_path = os.path.join(source_dir, year)
            if not os.path.exists(year_path):
                continue
                
            print(f"Scanning directory: {year_path}")
            
            # 各動画フォルダ
            for item in sorted(os.listdir(year_path)):
                if "+" not in item:
                    continue
                item_path = os.path.join(year_path, item)
                if not os.path.isdir(item_path):
                    continue
                    
                url_file = os.path.join(item_path, "url.md")
                none_url_file = os.path.join(item_path, "none_url.md")
                
                # 以前に生成された url.md または none_url.md がある場合は一旦削除して再計算する（強制上書き）
                if os.path.exists(url_file):
                    os.remove(url_file)
                if os.path.exists(none_url_file):
                    os.remove(none_url_file)
                    
                parts = item.split("+")
                base_name = parts[0]
                date_part = parts[1]
                
                # フォルダ内のテキスト取得
                transcript = find_transcript_content(item_path)
                
                # 各動画候補とのマッチスコア計算
                best_video = None
                best_score = 0
                
                for video in video_list:
                    score = calculate_score(base_name, date_part, transcript, video["title"], video["approx_date"])
                    if score > best_score:
                        best_score = score
                        best_video = video
                        
                print(f"  [Folder] {item} -> Best Match: \"{best_video['title'] if best_video else 'NONE'}\" (Score: {best_score})")
                
                # 閾値を設定（一定以上のスコアのみ合格とする。合格ラインを45点に調整）
                if best_video and best_score >= 45:
                    # マッチと判定
                    with open(url_file, "w", encoding="utf-8") as uf:
                        uf.write(best_video["url"] + "\n")
                    print(f"    -> CREATED url.md: {best_video['url']}")
                    matched_count += 1
                else:
                    # 不一致と判定
                    with open(none_url_file, "w", encoding="utf-8") as nuf:
                        nuf.write("")
                    print(f"    -> CREATED none_url.md")
                    none_count += 1
                    
        print(f"\nSource {source_name} complete: {matched_count} matched, {none_count} set to none.")

if __name__ == "__main__":
    main()
