#!/usr/bin/env python3
import os
import re
import sys
import shutil
from datetime import datetime

# 設定
TARGET_BLOG_DIR = "/Users/mamoru/AntigravityCompany/投資メディア事業/investment-platform"

SOURCES = [
    "/Users/mamoru/techmoney",
    "/Users/mamoru/kabu_maru"
]

def clean_filename(name):
    # ファイル名として安全な文字のみ残す（日本語はそのまま許可するが特殊記号は除去）
    name = re.sub(r'[\\/*?:"<>|#\s]', '_', name)
    return name

def parse_date(date_str):
    # YYYYMMDD を YYYY-MM-DD に変換
    try:
        dt = datetime.strptime(date_str, "%Y%m%d")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        # フォールバックとして現在日付
        return datetime.now().strftime("%Y-%m-%d")

def extract_metadata_from_gaiyou(gaiyou_path):
    title = None
    description = ""
    
    if not os.path.exists(gaiyou_path):
        return title, description
        
    try:
        with open(gaiyou_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # 1. タイトル候補の抽出（推奨マークが付いているもの、または1番目のもの）
        # 例: 1. **【SpaceXのIPOは申し込む？】...** (推奨)
        title_match = re.search(r'1\.\s+\*\*([^*]+)\*\*(?:\s*\(推奨\))?', content)
        if title_match:
            title = title_match.group(1).strip()
        else:
            # 推奨マークを探す
            recommend_match = re.search(r'\d+\.\s+\*\*([^*]+)\*\*\s*\(推奨\)', content)
            if recommend_match:
                title = recommend_match.group(1).strip()
            else:
                # 単に最初の太字
                bold_match = re.search(r'\*\*([^*]+)\*\*', content)
                if bold_match:
                    title = bold_match.group(1).strip()

        # 2. 概要の抽出
        # 例: ### ■ 動画概要
        # (次のセクションか区切り線まで)
        summary_section = re.search(r'###\s*■\s*動画概要\s*\n(.*?)(?=\n---|###|\n\n\n)', content, re.DOTALL)
        if summary_section:
            description = summary_section.group(1).strip()
            # Markdownの改行や余分な空白をトリム
            description = re.sub(r'\s+', ' ', description)
            if len(description) > 150:
                description = description[:147] + "..."
    except Exception as e:
        print(f"Warning: Failed to parse gaiyou.md at {gaiyou_path}: {e}")
        
    return title, description

def find_main_markdown(parent_dir, folder_name, base_name):
    folder_path = os.path.join(parent_dir, folder_name)
    
    # 候補1: 親ディレクトリ直下の {base_name}.md (大文字小文字無視)
    for f in os.listdir(parent_dir):
        if f.lower() == f"{base_name.lower()}.md" and os.path.isfile(os.path.join(parent_dir, f)):
            return os.path.join(parent_dir, f)
            
    # 候補2: サブディレクトリ内の {base_name}.md
    for f in os.listdir(folder_path):
        if f.lower() == f"{base_name.lower()}.md" and os.path.isfile(os.path.join(folder_path, f)):
            return os.path.join(folder_path, f)
            
    # 候補3: サブディレクトリ内の最もファイルサイズの大きいMarkdownファイル (gaiyou, chap等を除外)
    md_files = []
    for f in os.listdir(folder_path):
        f_path = os.path.join(folder_path, f)
        if os.path.isfile(f_path) and f.endswith(".md"):
            f_lower = f.lower()
            if "gaiyou" not in f_lower and "chap" not in f_lower and "template" not in f_lower:
                md_files.append((f_path, os.path.getsize(f_path)))
                
    if md_files:
        # サイズ順にソートして最大のものを返す
        md_files.sort(key=lambda x: x[1], reverse=True)
        return md_files[0][0]
        
    # 候補4: chap1.md 〜 chapN.md の結合が必要な場合（後述で処理するため、ディレクトリパス自体を返すか一番目のchapを返す）
    chaps = sorted([os.path.join(folder_path, f) for f in os.listdir(folder_path) if re.match(r'chap\d+\.md', f, re.IGNORECASE)])
    if chaps:
        return "COMBINE_CHAPS"
        
    return None

def combine_chapters(folder_path):
    chaps = []
    for f in os.listdir(folder_path):
        if re.match(r'chap\d+\.md', f, re.IGNORECASE):
            # 数値順にソートするために番号を抽出
            num = int(re.search(r'\d+', f).group())
            chaps.append((os.path.join(folder_path, f), num))
    
    chaps.sort(key=lambda x: x[1])
    
    combined_content = ""
    for path, _ in chaps:
        try:
            with open(path, "r", encoding="utf-8") as f:
                combined_content += f.read() + "\n\n"
        except Exception as e:
            print(f"Error reading chapter {path}: {e}")
            
    return combined_content

def import_all():
    print("Starting YouTube to Blog import process...")
    
    import_count = 0
    
    for source in SOURCES:
        if not os.path.exists(source):
            print(f"Source directory not found: {source}")
            continue
            
        print(f"Scanning source directory: {source}")
        
        # 配信先ディレクトリの決定
        if "techmoney" in source:
            blog_content_dir = os.path.join(TARGET_BLOG_DIR, "techmoney-web/src/content/blog")
        else:
            blog_content_dir = os.path.join(TARGET_BLOG_DIR, "kabumaru-web/src/content/blog")
            
        os.makedirs(blog_content_dir, exist_ok=True)
        
        # ソースディレクトリ配下の「+」を含むフォルダを再帰的に走査
        for root, dirs, files in os.walk(source):
            for item in dirs:
                if "+" not in item:
                    continue
                item_path = os.path.join(root, item)
                parts = item.split("+")
                if len(parts) < 2:
                    continue
                    
                base_name = parts[0]
                date_part = parts[1]
                
                # 日付パース
                pub_date = parse_date(date_part)
                
                # HTML要約ファイルの探索
                html_summary_path = None
                for f in os.listdir(item_path):
                    if f.lower() == "video_summary.html" and os.path.isfile(os.path.join(item_path, f)):
                        html_summary_path = os.path.join(item_path, f)
                        break
                
                if html_summary_path:
                    print(f"Found HTML summary for {item}: {html_summary_path}")
                    try:
                        with open(html_summary_path, "r", encoding="utf-8") as f:
                            html_content = f.read()
                        
                        # タイトルの抽出
                        title = base_name
                        title_match = re.search(r'<title>(.*?)</title>', html_content, re.IGNORECASE | re.DOTALL)
                        if title_match:
                            title = title_match.group(1).strip()
                            # 末尾の「 - TechMoney」や「 - かぶまる」を除去
                            title = re.sub(r'\s*-\s*(TechMoney|かぶまる|KabuMaru).*$', '', title, flags=re.IGNORECASE)
                        
                        # descriptionの抽出
                        description = ""
                        desc_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', html_content, re.IGNORECASE | re.DOTALL)
                        if not desc_match:
                            desc_match = re.search(r'<meta\s+content=["\'](.*?)["\']\s+name=["\']description["\']', html_content, re.IGNORECASE | re.DOTALL)
                        if desc_match:
                            description = desc_match.group(1).strip()
                        
                        # 記事本文の作成 (HTMLの全内容をそのまま出力)
                        content_body = html_content
                        
                        # ファイル名の決定（安全な英語/日本語名）
                        out_filename = f"{clean_filename(base_name)}.md"
                        out_path = os.path.join(blog_content_dir, out_filename)
                        
                        blog_post = f"""---
title: "{title}"
description: "{description}"
pubDate: {pub_date}
customLayout: true
---

{content_body}
"""
                        with open(out_path, "w", encoding="utf-8") as f:
                            f.write(blog_post)
                        print(f"Successfully imported HTML summary: {item} -> {out_filename}")
                        import_count += 1
                        continue
                    except Exception as e:
                        print(f"Failed to process HTML summary for {item}: {e}. Falling back to markdown.")
                
                # メインMarkdownファイルの探索
                main_md_path = find_main_markdown(root, item, base_name)
                
                if not main_md_path:
                    print(f"No main markdown found for {item}. Skipping.")
                    continue
                    
                # コンテンツの読み込み
                content_body = ""
                if main_md_path == "COMBINE_CHAPS":
                    content_body = combine_chapters(item_path)
                else:
                    try:
                        with open(main_md_path, "r", encoding="utf-8") as f:
                            content_body = f.read()
                    except Exception as e:
                        print(f"Failed to read {main_md_path}: {e}")
                        continue
                
                if not content_body.strip():
                    print(f"Content is empty for {item}. Skipping.")
                    continue
                    
                # 概要とタイトル候補の抽出
                gaiyou_path = os.path.join(item_path, "gaiyou.md")
                gaiyou_title, description = extract_metadata_from_gaiyou(gaiyou_path)
                
                # タイトルの決定
                title = gaiyou_title
                if not title:
                    title_match = re.search(r'^#\s+(.+)$', content_body, re.MULTILINE)
                    if title_match:
                        title = title_match.group(1).strip()
                    else:
                        first_line = content_body.split('\n')[0].strip()
                        if first_line.startswith('■'):
                            title = first_line.replace('■', '').strip()
                        else:
                            title = base_name
                            
                if not description:
                    clean_body = re.sub(r'Speaker\s+\d+:\s*', '', content_body)
                    clean_body = re.sub(r'[#■━\-\s]', '', clean_body)
                    description = clean_body[:140] + "..." if len(clean_body) > 140 else clean_body
                    
                out_filename = f"{clean_filename(base_name)}.md"
                out_path = os.path.join(blog_content_dir, out_filename)
                
                blog_post = f"""---
title: "{title}"
description: "{description}"
pubDate: {pub_date}
---

{content_body}
"""
                try:
                    with open(out_path, "w", encoding="utf-8") as f:
                        f.write(blog_post)
                    print(f"Successfully imported: {item} -> {out_filename}")
                    import_count += 1
                except Exception as e:
                    print(f"Failed to write blog post {out_filename}: {e}")
                    
    print(f"\nImport process completed. Total imported: {import_count} articles.")

if __name__ == "__main__":
    import_all()
