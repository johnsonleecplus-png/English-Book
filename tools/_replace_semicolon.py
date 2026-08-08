"""
批量替换 vocabSeed.ts 里的分号为斜杠
- 全角 ； → /
- 半角 ; → /
- 保留 , (半角逗号) 跟 . (句号) 不动
- 保留 <  > 等其它符号不动
"""
import re
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

SRC = r'D:\10-English-Book\src\data\vocabSeed.ts'

with open(SRC, 'r', encoding='utf-8') as f:
    content = f.read()

# 统计
before_full = content.count('；')
before_half = content.count(';')

# 替换
new_content = content.replace('；', '/').replace(';', '/')

# 统计
after_full = new_content.count('；')
after_half = new_content.count(';')
slash = new_content.count('/')

# 写回
with open(SRC, 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"  全角 ；: {before_full} → {after_full}")
print(f"  半角 ;: {before_half} → {after_half}")
print(f"  / 总数: {slash}")

# 抽样 10 个看效果
import re
matches = re.findall(r"cn: '[^']+'", new_content)
print(f"\n  抽样 10 个 cn 字段:")
for m in matches[:10]:
    print(f"    {m}")
