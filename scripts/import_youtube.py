#!/usr/bin/env python3
import os
import re
import sys
import shutil
import json
import urllib.request
import urllib.parse
from datetime import datetime

# 設定
TARGET_BLOG_DIR = "/Users/mamoru/AntigravityCompany/投資メディア事業/martialcasino"

SOURCES = [
    "/Users/mamoru/Library/CloudStorage/GoogleDrive-mamorubasebaii9045@gmail.com/その他のパソコン/マイ Mac/techmoney",
    "/Users/mamoru/Library/CloudStorage/GoogleDrive-mamorubasebaii9045@gmail.com/その他のパソコン/マイ Mac/kabu_maru"
]

# Load Custom Mappings if exist
MAPPINGS_PATH = os.path.join(TARGET_BLOG_DIR, "scripts/title_mappings.json")
title_mappings = {}
if os.path.exists(MAPPINGS_PATH):
    try:
        with open(MAPPINGS_PATH, "r", encoding="utf-8") as fm:
            title_mappings = json.load(fm)
        print(f"Loaded {len(title_mappings)} title overrides from title_mappings.json")
    except Exception as em:
        print(f"Warning: Failed to load title_mappings.json: {em}")

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
        title_match = re.search(r'1\.\s+\*\*([^*]+)\*\*(?:\s*\(推奨\))?', content)
        if title_match:
            title = title_match.group(1).strip()
        else:
            recommend_match = re.search(r'\d+\.\s+\*\*([^*]+)\*\*\s*\(推奨\)', content)
            if recommend_match:
                title = recommend_match.group(1).strip()
            else:
                bold_match = re.search(r'\*\*([^*]+)\*\*', content)
                if bold_match:
                    title = bold_match.group(1).strip()

        # 2. 概要の抽出
        summary_section = re.search(r'###\s*■\s*動画概要\s*\n(.*?)(?=\n---|###|\n\n\n)', content, re.DOTALL)
        if summary_section:
            description = summary_section.group(1).strip()
            description = re.sub(r'\s+', ' ', description)
            if len(description) > 150:
                description = description[:147] + "..."
    except Exception as e:
        print(f"Warning: Failed to parse gaiyou.md at {gaiyou_path}: {e}")
        
    return title, description

def fetch_youtube_info(url_path):
    try:
        with open(url_path, "r", encoding="utf-8") as f:
            url = f.read().strip()
        
        if not url:
            return None, None
            
        # Extract video ID
        video_id = None
        if "youtu.be/" in url:
            video_id = url.split("youtu.be/")[1].split("?")[0]
        elif "youtube.com/watch" in url:
            params = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
            video_id = params.get("v", [None])[0]
        elif "youtube.com/embed/" in url:
            video_id = url.split("youtube.com/embed/")[1].split("?")[0]
            
        if not video_id:
            return None, None
            
        # Fetch title via oEmbed (No API Key Required!)
        oembed_url = f"https://www.youtube.com/oembed?url={urllib.parse.quote(url)}&format=json"
        req = urllib.request.Request(oembed_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            title = data.get("title")
            print(f"Successfully fetched YouTube details: {title} (ID: {video_id})")
            return title, video_id
    except Exception as e:
        print(f"Warning: Failed to fetch YouTube info from oEmbed: {e}")
        return None, None

def generate_title_via_gemini(transcript):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None, None
    
    try:
        print("Calling Gemini Developer API for title generation...")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        prompt = (
            "以下の動画台本から、読者を惹きつける魅力的なブログ用の日本語タイトルと概要（140文字程度）を作成してください。\n"
            "JSONフォーマットのみで出力してください。他の説明やマークダウン記法は含めないでください。フォーマット例:\n"
            "{\n"
            "  \"title\": \"生成されたタイトル\",\n"
            "  \"description\": \"生成された概要\"\n"
            "}\n\n"
            f"台本:\n{transcript[:4000]}"
        )
        req_data = json.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json"
            }
        }).encode('utf-8')
        
        req = urllib.request.Request(url, data=req_data, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=10) as response:
            res_data = json.loads(response.read().decode())
            text_out = res_data['candidates'][0]['content']['parts'][0]['text']
            parsed = json.loads(text_out.strip())
            return parsed.get("title"), parsed.get("description")
    except Exception as e:
        print(f"Warning: Failed to generate title via Gemini API: {e}")
        return None, None

def transform_html_for_astro(html_content, title, description, video_id, category, pub_date):
    # styleブロックの内容抽出
    style_match = re.search(r'<style>(.*?)</style>', html_content, re.DOTALL)
    style_rules = style_match.group(1) if style_match else ""
    
    # 既存のHTML外殻タグを削る
    html_body = re.sub(r'<!DOCTYPE html>.*?(<body[^>]*>)', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    html_body = re.sub(r'</body>.*?</html>', '', html_body, flags=re.DOTALL | re.IGNORECASE)
    html_body = re.sub(r'<head>.*?</head>', '', html_body, flags=re.DOTALL | re.IGNORECASE)
    html_body = re.sub(r'<html>', '', html_body, flags=re.IGNORECASE)
    html_body = re.sub(r'</style>', '', html_body, flags=re.IGNORECASE)
    html_body = re.sub(r'<style>.*', '', html_body, flags=re.DOTALL | re.IGNORECASE)
    
    html_body = html_body.strip()
    
    # h2 や card-title に id を注入しつつ TOC 用データを集める
    toc_items = []
    count = 0
    def repl(match):
        nonlocal count
        count += 1
        t_text = re.sub(r'<[^>]+>', '', match.group(1)).strip()
        toc_items.append((f"chapter-{count}", t_text))
        return f'<div id="chapter-{count}" class="anchor-target"></div>{match.group(0)}'
        
    html_body = re.sub(r'<div class="card-title"[^>]*>(.*?)</div>', repl, html_body, flags=re.DOTALL)
    
    # 目次のリスト要素HTMLを構築
    toc_list_items = ""
    for cid, ctitle in toc_items:
        toc_list_items += f'          <li><a href="#{cid}">{ctitle}</a></li>\n'
        
    # フレックス2カラムのレイアウトコードに置換
    toc_sidebar_html = f"""
  <div class="article-content">
    <aside class="toc-sidebar">
      <div class="glass-card sidebar-toc">
        <h3>目次</h3>
        <ul>
{toc_list_items}        </ul>
      </div>
    </aside>
    <div class="post-body">
      <div class="content-grid">"""
      
    html_body = html_body.replace('<div class="content-grid">', toc_sidebar_html)
    
    # .content-grid 終了時に wraps を閉じる
    if '</div>\n  </div>\n</div>' in html_body:
        html_body = html_body.replace('</div>\n  </div>\n</div>', '</div>\n    </div>\n  </div>\n</div>')
    elif '</div>\n</div>\n</div>' in html_body:
        html_body = html_body.replace('</div>\n</div>\n</div>', '</div>\n</div>\n</div>\n</div>')
    else:
        # Fallback
        html_body += "\n    </div>\n  </div>"
        
    # YouTube動画のプレイヤー埋め込み
    if video_id:
        youtube_html = f"""
  <div class="video-container">
    <iframe src="https://www.youtube.com/embed/{video_id}" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
  </div>
  """
        # <div class="container"> の直後にプレイヤーをインジェクト
        html_body = html_body.replace('<div class="container">', f'<div class="container">\n{youtube_html}', 1)
        
    return style_rules, html_body

def find_main_markdown(parent_dir, folder_name, base_name):
    folder_path = os.path.join(parent_dir, folder_name)
    
    for f in os.listdir(parent_dir):
        if f.lower() == f"{base_name.lower()}.md" and os.path.isfile(os.path.join(parent_dir, f)):
            return os.path.join(parent_dir, f)
            
    for f in os.listdir(folder_path):
        if f.lower() == f"{base_name.lower()}.md" and os.path.isfile(os.path.join(folder_path, f)):
            return os.path.join(folder_path, f)
            
    md_files = []
    for f in os.listdir(folder_path):
        f_path = os.path.join(folder_path, f)
        if os.path.isfile(f_path) and f.endswith(".md"):
            f_lower = f.lower()
            if "gaiyou" not in f_lower and "chap" not in f_lower and "template" not in f_lower and "url" not in f_lower:
                md_files.append((f_path, os.path.getsize(f_path)))
                
    if md_files:
        md_files.sort(key=lambda x: x[1], reverse=True)
        return md_files[0][0]
        
    chaps = sorted([os.path.join(folder_path, f) for f in os.listdir(folder_path) if re.match(r'chap\d+\.md', f, re.IGNORECASE)])
    if chaps:
        return "COMBINE_CHAPS"
        
    return None

def combine_chapters(folder_path):
    chaps = []
    for f in os.listdir(folder_path):
        if re.match(r'chap\d+\.md', f, re.IGNORECASE):
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
        
        if "techmoney" in source:
            blog_content_dir = os.path.join(TARGET_BLOG_DIR, "techmoney-web/src/content/blog")
            default_cat = "ai-semiconductor"
        else:
            blog_content_dir = os.path.join(TARGET_BLOG_DIR, "kabumaru-web/src/content/blog")
            default_cat = "tech"
            
        os.makedirs(blog_content_dir, exist_ok=True)
        
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
                pub_date = parse_date(date_part)
                
                # Check for url.md first
                url_file_path = os.path.join(item_path, "url.md")
                yt_title, video_id = None, None
                if os.path.exists(url_file_path):
                    yt_title, video_id = fetch_youtube_info(url_file_path)
                
                # Check mapping file override
                mapping = title_mappings.get(base_name, {})
                title = mapping.get("title") or yt_title
                description = mapping.get("description")
                category = mapping.get("category") or default_cat
                
                # Find transcripts/texts in case we need AI generation
                main_md_path = find_main_markdown(root, item, base_name)
                content_body = ""
                if main_md_path:
                    if main_md_path == "COMBINE_CHAPS":
                        content_body = combine_chapters(item_path)
                    else:
                        try:
                            with open(main_md_path, "r", encoding="utf-8") as f:
                                content_body = f.read()
                        except Exception as e:
                            print(f"Failed to read {main_md_path}: {e}")

                # AI Generation if url.md is missing and GEMINI_API_KEY exists
                ai_title, ai_desc = None, None
                if not title and not description and content_body:
                    ai_title, ai_desc = generate_title_via_gemini(content_body)
                    
                # Setup Fallback metadata
                if not title:
                    title = ai_title or base_name
                if not description:
                    description = ai_desc or ""

                # Replace double quotes with single quotes to prevent YAML/JSX syntax errors
                title = title.replace('"', "'") if title else ""
                description = description.replace('"', "'") if description else ""

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
                        
                        # Extract description if still missing
                        if not description:
                            desc_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', html_content, re.IGNORECASE)
                            if desc_match:
                                description = desc_match.group(1).strip()
                        
                        # Transform raw HTML with Left TOC, Header, Footer, and Video player
                        style_rules, transformed_body = transform_html_for_astro(html_content, title, description, video_id, category, pub_date)
                        
                        # ページ用ディレクトリの決定
                        blog_pages_dir = blog_content_dir.replace("src/content/blog", "src/pages/blog")
                        os.makedirs(blog_pages_dir, exist_ok=True)
                        
                        out_astro_filename = f"{clean_filename(base_name)}.astro"
                        out_astro_path = os.path.join(blog_pages_dir, out_astro_filename)
                        
                        # Write Astro file
                        astro_page_content = f"""---
import Header from '../../components/Header.astro';
import Footer from '../../components/Footer.astro';
import BaseHead from '../../components/BaseHead.astro';
import {{ SITE_TITLE }} from '../../consts';

// Generated from video_summary.html
---
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <BaseHead title="{title} - {{SITE_TITLE}}" description="{description}" />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&family=Noto+Sans+JP:wght@300;400;500;700;900&display=swap" rel="stylesheet">
  <style is:global>
{style_rules}

    /* Unified Layout Styles */
    .blog-main {{
        max-width: 1200px;
        margin: 0 auto;
        padding: 2rem 1.5rem;
    }}
    .breadcrumb {{
        font-size: 0.85rem;
        color: var(--text-secondary, #cbd5e1);
        margin-bottom: 2rem;
    }}
    .breadcrumb a {{
        color: var(--text-secondary, #cbd5e1);
        text-decoration: none;
    }}
    .breadcrumb a:hover {{
        color: var(--color-accent, #10B981);
    }}
    .breadcrumb .separator {{
        margin: 0 0.5rem;
        color: var(--text-muted, #64748b);
    }}
    .article-content {{
        display: flex;
        gap: 3rem;
        align-items: flex-start;
        margin-top: 2rem;
    }}
    .toc-sidebar {{
        width: 280px;
        position: sticky;
        top: 6rem;
        flex-shrink: 0;
    }}
    .sidebar-toc {{
        background: rgba(28, 37, 65, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        padding: 1.8rem;
        backdrop-filter: blur(10px);
    }}
    .sidebar-toc h3 {{
        font-size: 1.1rem;
        font-weight: 800;
        margin-bottom: 1.2rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        padding-bottom: 0.6rem;
        color: var(--text-primary, #f1f5f9);
    }}
    .sidebar-toc ul {{
        list-style: none;
        display: flex;
        flex-direction: column;
        gap: 0.8rem;
        margin-left: 0;
        padding-left: 0;
    }}
    .sidebar-toc a {{
        font-size: 0.9rem;
        color: var(--text-secondary, #cbd5e1);
        text-decoration: none;
        transition: color 0.2s ease;
    }}
    .sidebar-toc a:hover {{
        color: var(--color-accent, #10B981);
    }}
    .post-body {{
        flex-grow: 1;
        max-width: calc(100% - 310px);
    }}
    .anchor-target {{
        position: relative;
        top: -100px;
        visibility: hidden;
        display: block;
    }}
    .video-container {{
        position: relative;
        width: 100%;
        padding-top: 56.25%;
        margin-bottom: 2rem;
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid var(--border-color, rgba(16, 185, 129, 0.15));
        box-shadow: 0 0 20px rgba(16, 185, 129, 0.1);
    }}
    .video-container iframe {{
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        border: 0;
    }}
    @media (max-width: 992px) {{
        .article-content {{
            flex-direction: column;
        }}
        .toc-sidebar {{
            display: none;
        }}
        .post-body {{
            max-width: 100%;
        }}
    }}
  </style>
</head>
<body>
  <Header />
  
  <main class="blog-main">
    <div class="container">
      <div class="breadcrumb">
        <a href="/">← ホームに戻る</a>
        <span class="separator">|</span>
        <a href="/">トップ</a> &gt; <a href="/blog">ブログ</a> &gt; <span class="current">{title}</span>
      </div>
    </div>
    
    {transformed_body}
  </main>

  <Footer />
</body>
</html>
"""
                        with open(out_astro_path, "w", encoding="utf-8") as f:
                            f.write(astro_page_content)
                        
                        # Markdown Placeholder
                        out_filename = f"{clean_filename(base_name)}.md"
                        out_path = os.path.join(blog_content_dir, out_filename)
                        
                        blog_post_placeholder = f"""---
title: "{title}"
description: "{description}"
pubDate: {pub_date}
category: "{category}"
status: "published"
customLayout: true
---
"""
                        with open(out_path, "w", encoding="utf-8") as f:
                            f.write(blog_post_placeholder)
                        
                        print(f"Successfully imported HTML summary: {item} -> {out_astro_filename} and {out_filename}")
                        import_count += 1
                        continue
                    except Exception as e:
                        print(f"Failed to process HTML summary for {item}: {e}. Falling back to markdown.")
                
                # No HTML summary, standard markdown import
                if content_body.strip():
                    # Parse description if not set
                    if not description:
                        gaiyou_path = os.path.join(item_path, "gaiyou.md")
                        gaiyou_title, gaiyou_desc = extract_metadata_from_gaiyou(gaiyou_path)
                        description = gaiyou_desc or re.sub(r'Speaker\s+\d+:\s*', '', content_body)[:140] + "..."
                    
                    out_filename = f"{clean_filename(base_name)}.md"
                    out_path = os.path.join(blog_content_dir, out_filename)
                    
                    # Standard markdown format (no customLayout)
                    blog_post = f"""---
title: "{title}"
description: "{description}"
pubDate: {pub_date}
category: "{category}"
status: "published"
---

{content_body}
"""
                    try:
                        with open(out_path, "w", encoding="utf-8") as f:
                            f.write(blog_post)
                        print(f"Successfully imported standard post: {item} -> {out_filename}")
                        import_count += 1
                    except Exception as e:
                        print(f"Failed to write blog post {out_filename}: {e}")
                    
    print(f"\nImport process completed. Total imported: {import_count} articles.")

if __name__ == "__main__":
    import_all()
