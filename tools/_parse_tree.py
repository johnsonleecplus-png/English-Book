"""Parse GitHub tree JSON, list mp3s + find abandon"""
import json
import sys

with open(r'C:\Users\johns\AppData\Local\Temp\tree.json', 'r', encoding='utf-8-sig') as f:
    data = json.load(f)
truncated = data.get('truncated')
print(f'truncated: {truncated}')
tree = data.get('tree', [])
print(f'tree entries: {len(tree)}')
mp3s = [e for e in tree if e['path'].startswith('public/audio/words/') and e['path'].endswith('.mp3')]
print(f'mp3 count: {len(mp3s)}')
# 前 10
for m in mp3s[:10]:
    print(f'  {m["path"]}  {m["size"]}')
# abandon
ab = [m for m in mp3s if 'abandon' in m['path']]
print(f'abandon: {ab}')
