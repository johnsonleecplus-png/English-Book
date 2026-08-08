"""
Openclipart 批量下载 + 按单词归类 脚本模板
下载公共域 (CC0) 矢量图, 为中考词汇表做本地图片库

用法:
  python openclipart_dl.py --csv "../public/词源/上海中考英文词汇表_完整版.csv" --output ../public/images --max-per-word 5
  python openclipart_dl.py --csv ... --first 5          # 只跑前 5 词
  python openclipart_dl.py --csv ... --dry-run          # 只搜不下

依赖: 仅标准库 (urllib/re/json)
输出:
  images/
    {word}/
      01.svg
      02.svg
      ...
    index.json     # {word: [{idx, title, url, local_path, size}, ...]}

Openclipart API (经验, 端点可能变):
  搜索: https://openclipart.org/api/search?q={word}&page={page}
       (旧 JSON API, 部分历史快照稳定)
  备选 (HTML 解析): https://openclipart.org/search/?query={word}
"""
import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

# --- 限速: Openclipart 不要太狠, 间隔 1.5s 比较稳 ---
RATE_LIMIT_SEC = 1.5
USER_AGENT = 'EnglishBook-PWA-Builder/1.0 (CC0 image harvest; contact: dev@example.com)'
TIMEOUT = 20

# --- Openclipart API 端点 ---
OC_SEARCH_API = 'https://openclipart.org/api/search?q={q}&page={page}'
OC_SEARCH_HTML = 'https://openclipart.org/search/?query={q}'


def fetch(url: str) -> tuple[bytes, str]:
    """GET url, 限速 + UA, 返回 (body, content_type)"""
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read(), r.headers.get('Content-Type', '')


def search_api(word: str) -> list[dict]:
    """用老 JSON API 搜. 返回 [{title, url, svg_url, png_url, id, license}, ...]"""
    url = OC_SEARCH_API.format(q=urllib.parse.quote(word), page=1)
    try:
        body, ct = fetch(url)
    except Exception as e:
        print(f'  [api fail] {word}: {e}', file=sys.stderr)
        return []
    if 'json' not in ct.lower():
        return []  # 端点可能已弃用, 跳到 HTML 解析
    try:
        data = json.loads(body.decode('utf-8', errors='replace'))
    except json.JSONDecodeError:
        return []
    # API 返回结构: {'info': {...}, 'payload': [...]}
    payload = data.get('payload') or []
    results = []
    for item in payload:
        title = item.get('title', '').strip()
        # 不同 API 版本字段可能不同, 多拿几个候选
        svg = item.get('svg') or item.get('svg_url') or item.get('svg_files', [None])[0]
        png = item.get('png') or item.get('png_url') or item.get('png_preview') or item.get('png_400')
        link = item.get('detail_link') or item.get('link') or item.get('url') or ''
        # 构造 detail page URL (兜底)
        if not link and item.get('id'):
            link = f"https://openclipart.org/detail/{item['id']}"
        if not title:
            continue
        # 优先 svg
        file_url = svg or png
        if not file_url:
            continue
        if file_url.startswith('/'):
            file_url = 'https://openclipart.org' + file_url
        results.append({
            'id': item.get('id'),
            'title': title,
            'detail_url': link if link.startswith('http') else ('https://openclipart.org' + link if link else ''),
            'file_url': file_url,
            'format': 'svg' if svg else 'png',
            'license': item.get('license') or 'CC0',
        })
    return results


def search_html(word: str) -> list[dict]:
    """HTML 解析兜底. 拿搜索页, 抓 detail 链接 + 缩略图."""
    url = OC_SEARCH_HTML.format(q=urllib.parse.quote(word))
    try:
        body, _ = fetch(url)
    except Exception as e:
        print(f'  [html fail] {word}: {e}', file=sys.stderr)
        return []
    html = body.decode('utf-8', errors='replace')
    # 找 detail 链接: /detail/{id}/{slug}
    pattern = re.compile(r'href="(/detail/(\d+)/([^"]+))"')
    results = []
    seen_ids = set()
    for m in pattern.finditer(html):
        href, did, slug = m.group(1), m.group(2), m.group(3)
        if did in seen_ids:
            continue
        seen_ids.add(did)
        # 缩略图: <img ... src="..."> (在同 anchor 内或附近)
        # 这里用 detail page URL 进去再抓 SVG 链接 — 简化: 拿 detail page
        results.append({
            'id': did,
            'title': slug.replace('-', ' '),
            'detail_url': 'https://openclipart.org' + href,
            'file_url': None,  # 留给 detail page 抓
            'format': 'svg',
            'license': 'CC0',
        })
        if len(results) >= 10:
            break
    return results


def get_svg_from_detail(detail_url: str) -> str | None:
    """进 detail page 抓 svg 下载链接"""
    try:
        body, _ = fetch(detail_url)
    except Exception:
        return None
    html = body.decode('utf-8', errors='replace')
    # 找 .svg 直链 (Openclipart 通常: /image/...svg)
    m = re.search(r'href="([^"]+\.svg)"', html)
    if m:
        url = m.group(1)
        if url.startswith('/'):
            url = 'https://openclipart.org' + url
        return url
    # 备选 png
    m = re.search(r'href="([^"]+\.png)"', html)
    if m:
        url = m.group(1)
        if url.startswith('/'):
            url = 'https://openclipart.org' + url
        return url
    return None


def download(url: str, dest: Path) -> int:
    """下载文件, 返回字节数; 失败抛异常"""
    body, ct = fetch(url)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(body)
    return len(body)


def harvest_word(word: str, outdir: Path, max_per_word: int) -> list[dict]:
    """单个词: 搜 + 下 N 个候选. 返回 saved 列表 (供 index.json)"""
    saved: list[dict] = []
    word_dir = outdir / word
    word_dir.mkdir(parents=True, exist_ok=True)

    # 1) 搜 (优先 API)
    candidates = search_api(word)
    if not candidates:
        candidates = search_html(word)

    if not candidates:
        print(f'  [no result] {word}')
        return saved

    # 2) 限速下 (每个候选一个 detail page 也算一次请求)
    for i, c in enumerate(candidates[:max_per_word]):
        file_url = c.get('file_url')
        if not file_url and c.get('detail_url'):
            file_url = get_svg_from_detail(c.get('detail_url'))
        if not file_url:
            continue
        ext = c.get('format') or ('svg' if file_url.endswith('.svg') else 'png')
        dest = word_dir / f'{i+1:02d}.{ext}'
        try:
            size = download(file_url, dest)
            saved.append({
                **c,
                'file_url': file_url,
                'local_path': str(dest.relative_to(outdir.parent)),
                'size': size,
            })
            print(f'  [{i+1}/{max_per_word}] {word}: {c["title"][:40]} ({size} bytes)')
        except Exception as e:
            print(f'  [dl fail] {word} #{i+1}: {e}')
        time.sleep(RATE_LIMIT_SEC)

    return saved


def load_words(csv_path: Path, limit: int | None = None) -> list[str]:
    """从 CSV 读 "单词" 列 (跳过 # 注释和表头)"""
    words = []
    with open(csv_path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('序号'):
                continue
            parts = line.split(',')
            if len(parts) >= 2:
                w = parts[1].strip()
                if w and w.replace('-', '').isalpha():
                    words.append(w)
            if limit and len(words) >= limit:
                break
    return words


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--csv', required=True, help='词表 CSV 路径')
    ap.add_argument('--output', required=True, help='输出根目录 (e.g. ../public/images)')
    ap.add_argument('--max-per-word', type=int, default=5, help='每词最多下几个候选')
    ap.add_argument('--first', type=int, default=None, help='只跑前 N 词 (POC)')
    ap.add_argument('--dry-run', action='store_true', help='只搜不下')
    args = ap.parse_args()

    csv_path = Path(args.csv).resolve()
    outdir = Path(args.output).resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    words = load_words(csv_path, limit=args.first)
    print(f'Loaded {len(words)} words from {csv_path.name}')

    if args.dry_run:
        for w in words[:5]:
            res = search_api(w) or search_html(w)
            print(f'  {w}: {len(res)} candidates')
            for r in res[:3]:
                print(f'    - [{r["format"]}] {r["title"][:50]}')
            time.sleep(0.5)
        return

    index: dict[str, list[dict]] = {}
    for n, w in enumerate(words, 1):
        print(f'[{n}/{len(words)}] {w}')
        index[w] = harvest_word(w, outdir, args.max_per_word)

    # 写 index
    idx_path = outdir / 'index.json'
    idx_path.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'\nDone. Index: {idx_path} ({len(index)} words)')


if __name__ == '__main__':
    main()
