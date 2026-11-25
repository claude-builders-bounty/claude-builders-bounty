---
name: novel-download-12kanshu
description: "Download complete novels from 12kanshu.com with chapter extraction and text assembly."
version: 0.1.0
author: User (Hermes Agent)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [novel, download, scraping, 12kanshu, chinese-web-novel, text-extraction]
    related_skills: [novel-to-sillytavern-pipeline, cross-platform-text-processing, memory-local]
---

# Novel Download from 12kanshu.com

Download complete Chinese web novels from 12kanshu.com (一二看书网) by extracting chapter list from the index page, then fetching each chapter content via the `read_tz(chapter_id)` JavaScript function pattern. Handles pagination, rate limiting, and assembles full novel text.

## When to Use

- Need to download a complete novel from 12kanshu.com for offline reading or processing
- URL format: `https://www.12kanshu.com/book/{BOOK_ID}/all_1.html`
- Want structured output: chapter list JSON + full text file
- Processing pipeline for SillyTavern conversion (use with `novel-to-sillytavern-pipeline`)

Don't use for:
- Other novel sites (different DOM structure)
- Single chapter extraction (use browser_exec directly)
- Sites with anti-scraping requiring login

## Prerequisites

- Python 3.10+ with `requests`, `tqdm`, `re`, `json`, `time` (stdlib + requests/tqdm)
- Network access to `www.12kanshu.com` (Chinese mainland IP works best)
- Optional: `PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright/` for browser-based fallback

## How to Run

```bash
# 1. Install dependencies
pip install requests tqdm

# 2. Run the download script
cd /home/user01/.hermes/python
python3 scripts/download_12kanshu.py --book-id 199617 --output-dir ./output/jingtao_luori

# 3. Outputs:
#    - output/jingtao_luori/chapters.json (chapter list with IDs, titles, URLs)
#    - output/jingtao_luori/full_novel.txt (complete novel text)
#    - output/jingtao_luori/download.log (progress log)
```

## Quick Reference

| Script | Purpose |
|--------|---------|
| `scripts/download_12kanshu.py` | Main downloader: index pagination → chapter ID extraction → content fetch → assembly |
| `scripts/analyze_chapters.py` | Analyze chapter list: count, title patterns, gaps |

## Procedure

### 1. Extract Book ID from URL

**Completion criterion**: Book ID identified from URL.

```bash
# URL: https://www.12kanshu.com/book/199617/all_1.html
# Book ID: 199617
BOOK_ID=199617
```

### 2. Fetch Index Pages (Pagination)

**Completion criterion**: All index pages fetched, chapter IDs extracted.

```python
# Index URL pattern: https://www.12kanshu.com/book/{BOOK_ID}/all_{page}.html
# Page 1: all_1.html, Page 2: all_2.html, etc.
# Stop when page returns < 50 chapters (last page)

# Chapter links use onclick="read_tz(CHAPTER_ID)" pattern
# Regex: read_tz\((\d+)\)[^>]*>([^<]+)</a>
```

### 3. Extract Chapter IDs and Titles

**Completion criterion**: Complete chapter list with (ID, title, URL) for all chapters.

```python
# Sample chapter structure:
{
  "id": "93750340",
  "title": "第1章 穿越的第一眼就看到了红膏药",
  "url": "https://www.12kanshu.com/chapter/93750340.html"
}

# Total chapters for book 199617: ~119 chapters across multiple index pages
```

### 4. Fetch Chapter Content

**Completion criterion**: Each chapter content fetched and cleaned.

```python
# Chapter URL: https://www.12kanshu.com/chapter/{CHAPTER_ID}.html
# Content selector: .chapter_content, .content, #content, .text
# Clean: remove ads, navigation, extra whitespace
# Rate limit: 0.5-1 second between requests
# Retry: 3 attempts with exponential backoff on failure
```

### 5. Assemble Full Novel

**Completion criterion**: Single text file with all chapters in order.

```python
# Output format:
# 第1章 穿越的第一眼就看到了红膏药
# [chapter content...]
#
# 第2章 我只知道要大开杀戒
# [chapter content...]
# ...

# UTF-8 encoding, LF line endings
# Progress saved incrementally (resume on interruption)
```

### 6. Validate Output

**Completion criterion**: Chapter count matches expected, file size reasonable.

```bash
# Check chapter count
wc -l output/jingtao_luori/chapters.json

# Check text file size (expect ~2-5 MB for 100+ chapters)
ls -lh output/jingtao_luori/full_novel.txt

# Spot check: verify first and last chapters
head -20 output/jingtao_luori/full_novel.txt
tail -20 output/jingtao_luori/full_novel.txt
```

## Implementation Notes

### Chapter ID Extraction Regex

The site uses JavaScript `onclick="read_tz(CHAPTER_ID)"` on chapter links:

```python
import re

# Primary pattern (from page source analysis)
pattern = r'read_tz\((\d+)\)[^>]*>([^<]+)</a>'

# Matches:
# <a onclick="read_tz(93750340);" class="s">第1章 穿越的第一眼就看到了红膏药</a>
# <a onclick="read_tz(104981834);" class="s">第16章 落日</a>
```

### Pagination Handling

```python
def fetch_all_chapters(book_id):
    all_chapters = []
    page = 1
    
    while True:
        url = f"https://www.12kanshu.com/book/{book_id}/all_{page}.html" if page > 1 \
              else f"https://www.12kanshu.com/book/{book_id}/all_1.html"
        
        html = fetch(url)
        chapters = extract_chapters(html)
        
        if len(chapters) < 50:  # Last page has fewer chapters
            all_chapters.extend(chapters)
            break
        
        all_chapters.extend(chapters)
        page += 1
        time.sleep(0.5)  # Be polite
    
    return all_chapters
```

### Chapter Content Fetching

```python
def fetch_chapter(chapter_id):
    url = f"https://www.12kanshu.com/chapter/{chapter_id}.html"
    html = fetch(url)
    
    # Try multiple selectors (site may vary)
    for selector in ['.chapter_content', '.content', '#content', '.text', 'article']:
        content = extract_by_selector(html, selector)
        if content and len(content) > 100:
            return clean_content(content)
    
    # Fallback: extract from body, remove known noise
    return extract_main_text(html)
```

## Pitfalls

| Issue | Solution |
|-------|----------|
| 404 on chapter URLs | Site may use different URL pattern; verify by visiting one chapter in browser |
| Rate limiting / IP block | Add delays (1-2s), use session with headers, rotate User-Agent |
| Encoding issues (GBK/UTF-8) | Force UTF-8: `response.encoding = 'utf-8'` |
| Pagination changes | Check if `all_N.html` pattern holds; some books use different naming |
| Anti-bot (Cloudflare) | Use `browser_exec` with Playwright for initial page loads |
| Incomplete chapters | Verify content length > 200 chars; retry failed chapters |
| Resume after interruption | Save progress to JSON; on restart, skip already-downloaded chapters |

## Verification

```bash
# 1. Chapter count reasonable
python3 -c "
import json
with open('output/jingtao_luori/chapters.json') as f:
    ch = json.load(f)
print(f'Chapters: {len(ch)}')
print(f'First: {ch[0][\"title\"]}')
print(f'Last: {ch[-1][\"title\"]}')
"

# 2. Full text file exists and non-empty
test -s output/jingtao_luori/full_novel.txt && echo "OK" || echo "EMPTY"

# 3. Character count (rough check)
wc -m output/jingtao_luori/full_novel.txt
# Expect: 500k-2M chars for full novel

# 4. UTF-8 valid
file output/jingtao_luori/full_novel.txt
# Should show: UTF-8 Unicode text
```

## Integration with Pipeline

```bash
# After download, feed to SillyTavern pipeline
python3 scripts/novel_to_sillytavern.py \
  --input output/jingtao_luori/full_novel.txt \
  --output-dir ./sillytavern_output/jingtao_luori \
  --reference-card ./references/shixiong_taizhenjian.png
```

---

*Distilled from session 20260926_020816_1453bcf8 (204 messages: complete download of "惊涛落日" - 119 chapters from book ID 199617). Pattern: index pagination → read_tz() chapter ID extraction → chapter content fetch → text assembly. Verified working with domestic mirror (npmmirror) for Playwright if browser fallback needed.*