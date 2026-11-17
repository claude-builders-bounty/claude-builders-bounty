---
name: cross-platform-text-processing
description: "Handle large Chinese text files with encoding detection, conversion, and chunked processing across WSL/Windows."
version: 0.1.0
author: User (Hermes Agent)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [text-processing, encoding, gbk, utf8, large-files, wsl, cross-platform]
    related_skills: [novel-to-sillytavern-pipeline, manage-python-venv-wsl, edit-config-files-wsl]
---

# Cross-Platform Text Processing

Robust handling of large Chinese text files (novels, logs, exports) with automatic encoding detection, GBK/UTF-8 conversion, and memory-efficient chunked processing across WSL2 and Windows.

## When to Use

- Process multi-MB/GB Chinese text files (novels, subtitles, logs)
- Convert legacy GBK/GB18030 files to UTF-8 for modern toolchains
- Chunk large files for LLM context windows or streaming processing
- Extract structure (chapters, sections) from unstructured Chinese text
- Bridge WSL2 (Linux tools) and Windows (file storage) paths

## Prerequisites

- WSL2 (Ubuntu 24.04+) with Windows file mounts at `/mnt/c/`, `/mnt/d/`
- Python 3.10+ with `chardet`, `iconv` (system), `tqdm`
- Read-only Windows mounts enforced via `/etc/wsl.conf` (`options = "ro,..."`)
- Python scripts in `/home/user01/.hermes/python/` (WSL-native, deployed via `deploy_to_prod.sh`)

## How to Run

```bash
# From WSL2 (native environment)
cd /home/user01/.hermes/python
python3 scripts/text_processing.py --input /mnt/c/Users/Administrator/Desktop/novel.txt --output ./novel_utf8.txt

# Or use the deployed Windows version
python3 /mnt/d/Ai/python/text_processing.py --input "C:\\Users\\Administrator\\Desktop\\novel.txt" --output "D:\\Ai\\novel_utf8.txt"
```

## Quick Reference

| Operation | Tool/Command |
|-----------|--------------|
| Detect encoding | `chardet.detect()` or `file -i` |
| Convert GBK→UTF-8 | `iconv -f GBK -t UTF-8` or `GB18030` fallback |
| Safe read large file | Python chunked generator (yield lines) |
| Chapter extraction | Regex: `第\\d+章[.·\\s]` + variants |
| WSL→Windows path | `/mnt/c/Users/...` ↔ `\\\\wsl.localhost\\Ubuntu-24.04\\home\\user01\\...` |
| Deploy script | `./deploy_to_prod.sh script.py` (temp remounts RW, then RO) |

## Procedure

### 1. Encoding Detection & Conversion

**Completion criterion**: UTF-8 file verified, no data loss

```python
def detect_and_convert(input_path: Path, output_path: Path) -> dict:
    """
    Returns: {'encoding': str, 'confidence': float, 'converted': bool, 'bytes_read': int, 'chars_written': int}
    """
    # 1. Sample first 100KB for detection
    with open(input_path, 'rb') as f:
        sample = f.read(100_000)
    
    detected = chardet.detect(sample)
    encoding = detected['encoding'] or 'GB18030'
    confidence = detected['confidence']
    
    # 2. Normalize encoding name
    encoding_map = {'GB2312': 'GB18030', 'GBK': 'GB18030', 'CP936': 'GB18030'}
    encoding = encoding_map.get(encoding.upper(), encoding)
    
    # 3. Convert with fallback chain
    fallback_chain = [encoding, 'GB18030', 'GBK', 'UTF-8']
    for enc in fallback_chain:
        try:
            with open(input_path, 'r', encoding=enc) as f_in:
                content = f_in.read()
            with open(output_path, 'w', encoding='utf-8') as f_out:
                f_out.write(content)
            return {'encoding': enc, 'confidence': confidence, 'converted': True, ...}
        except UnicodeDecodeError:
            continue
    
    raise ValueError(f"All encoding attempts failed for {input_path}")
```

### 2. Memory-Efficient Chunked Processing

**Completion criterion**: Process files > RAM without OOM

```python
def chunked_reader(file_path: Path, chunk_size: int = 1_000_000) -> Generator[str, None, None]:
    """Yield text chunks of ~chunk_size chars, respecting line boundaries."""
    with open(file_path, 'r', encoding='utf-8') as f:
        buffer = ''
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                if buffer:
                    yield buffer
                break
            buffer += chunk
            # Split at last newline
            lines = buffer.split('\n')
            buffer = lines.pop()  # incomplete line
            for line in lines:
                yield line + '\n'

# Usage: for chunk in chunked_reader(huge_file): process(chunk)
```

### 3. Chapter/Structure Extraction

**Completion criterion**: Chapter index with byte offsets, titles, char counts

```python
CHAPTER_PATTERNS = [
    r'第[一二三四五六七八九十百千万\d]+章[.·\s]',  # 第1章. / 第第一章·
    r'Chapter\s+\d+[.:\s]',                        # Chapter 1.
    r'第\s*\d+\s*章[.·\s]',                        # 第 1 章.
    r'卷[一二三四五六七八九十\d]+[.·\s]',           # 卷一.
]

def extract_chapters(file_path: Path) -> List[dict]:
    """Returns: [{'title': str, 'byte_offset': int, 'char_offset': int, 'char_count': int, 'chapter_num': int}, ...]"""
    chapters = []
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all matches with positions
    for pattern in CHAPTER_PATTERNS:
        for match in re.finditer(pattern, content):
            chapters.append({
                'title': match.group().strip(),
                'byte_offset': match.start(),
                'char_offset': match.start(),  # UTF-8: byte != char for CJK
                'match_pattern': pattern,
            })
    
    # Deduplicate, sort, calculate char_count between chapters
    chapters.sort(key=lambda x: x['byte_offset'])
    for i, ch in enumerate(chapters):
        end = chapters[i+1]['byte_offset'] if i+1 < len(chapters) else len(content)
        ch['char_count'] = len(content[ch['byte_offset']:end])
        ch['chapter_num'] = i + 1
    
    return chapters
```

### 4. Cross-Platform Path Handling

**Completion criterion**: Paths work identically in WSL2 and Windows Python

```python
from pathlib import Path
import platform

def normalize_path(path_str: str) -> Path:
    """Convert any path format to current platform's Path object."""
    p = Path(path_str)
    if platform.system() == 'Linux' and p.is_absolute() and p.drive in ('C:', 'D:'):
        # Windows path in WSL: C:\Users -> /mnt/c/Users
        drive = p.drive.lower().rstrip(':')
        return Path('/mnt') / drive / p.relative_to(p.drive)
    elif platform.system() == 'Windows' and str(p).startswith('/mnt/'):
        # WSL path in Windows: /mnt/c/Users -> C:\Users
        parts = p.parts
        if len(parts) >= 3 and parts[1] in ('c', 'd', 'e'):
            drive = parts[1].upper() + ':'
            return Path(drive) / Path(*parts[3:])
    return p

# Windows mount points (read-only in this environment)
WSL_MOUNTS = {'/mnt/c': 'C:', '/mnt/d': 'D:'}
```

### 5. Safe Deployment to Windows (Read-Only Mounts)

**Completion criterion**: Script deployed to Windows, mounts remain RO

```bash
#!/bin/bash
# deploy_to_prod.sh — deploy script from WSL-native to Windows
# Requires: sudo for temporary remount

SCRIPT=$1
SRC="/home/user01/.hermes/python/$SCRIPT"
DST="/mnt/d/Ai/python/$SCRIPT"

# 1. Verify source exists
[[ -f "$SRC" ]] || { echo "Source not found: $SRC"; exit 1; }

# 2. Temporarily remount Windows drive RW
sudo mount -o remount,rw /mnt/d

# 3. Copy with verification
cp "$SRC" "$DST"
diff "$SRC" "$DST" || { echo "Copy verification failed"; exit 1; }

# 4. Immediately restore RO
sudo mount -o remount,ro /mnt/d

# 5. Log deployment
echo "$(date -Iseconds) DEPLOY $SCRIPT" >> /home/user01/.hermes/python/deploy.log
```

## Pitfalls

| Issue | Solution |
|-------|----------|
| `iconv` drops unrepresentable chars | Use `GB18030` (superset of GBK); Python `errors='replace'` as last resort |
| WSL `read_file` tool can't read Windows files >100KB | Use `terminal` with `iconv`/`python` for large files; or copy to WSL first |
| Windows Python sees `/mnt/` paths as literal | Use `normalize_path()` function; deploy scripts to Windows-native paths |
| Mount remount requires sudo | `deploy_to_prod.sh` handles this; scripts MUST NOT remount themselves |
| Chapter regex misses variants | Test on sample; add patterns for `第X回`, `第X节`, `第X卷` |
| Memory spike on huge file read | Always use `chunked_reader()`; never `f.read()` on >500MB files |
| `subprocess.run(..., text=True)` without `encoding=` | Windows default codec is cp936/GBK: the reader thread raises `UnicodeDecodeError` (`0xbb`/`0xb4` bytes), `result.stdout` becomes `None`, and the call looks like it "returned nothing" instead of failing. Always pass `encoding="utf-8", errors="replace"` |

### Rule: every text-mode subprocess needs an explicit encoding

```python
# WRONG on Windows — silent None / mojibake when output contains non-ASCII
subprocess.run(cmd, capture_output=True, text=True)

# RIGHT — decode as UTF-8 regardless of console code page
subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")

# If you must keep bytes control, decode yourself:
out = subprocess.run(cmd, capture_output=True).stdout.decode("utf-8", errors="replace")
```

Same rule for your own stdout when printing Chinese from a scheduled task
(`.bat` under schtasks): set `PYTHONUTF8=1` or reconfigure
`sys.stdout.reconfigure(encoding="utf-8", errors="replace")`, else
`UnicodeEncodeError: 'charmap' codec can't encode ...` kills the run at the first
log line.

## Verification

```bash
# Test suite (run in WSL2):
python3 -m pytest tests/test_text_processing.py -v

# Key tests:
# 1. detect_and_convert() handles GBK, GB18030, UTF-8, mixed
# 2. chunked_reader() yields complete lines, no data loss
# 3. extract_chapters() finds all chapters in sample novel
# 4. normalize_path() round-trips WSL↔Windows paths
# 5. deploy_to_prod.sh leaves /mnt/d read-only after deploy
```

## Pattern Source

Derived from 7-day session analysis (Sep 1-7, 2026):
- 4+ sessions processing 8MB GBK novel (`整座大山都是我的猎场`)
- Repeated: `iconv -f GBK -t UTF-8`, `file` detection, chapter regex iteration
- WSL read_file tool failed on binary/large files → used terminal + python
- Windows mount read-only enforcement caused deployment friction
- Need for reusable, tested text processing utilities in `/home/user01/.hermes/python/`
- Cross-platform path confusion between WSL `/mnt/c/` and Windows `C:\`