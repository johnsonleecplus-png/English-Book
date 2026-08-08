"""提取词表中无 emoji 的词条 (word + pos + cn), 输出 JSON 供配 emoji"""
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = r"D:\10-English-Book"


def load_words():
    words = []
    path = os.path.join(ROOT, "src", "lib", "mockWords.ts")
    with open(path, encoding="utf-8") as f:
        words += re.findall(r"word:\s*'([^']+)'", f.read())
    path = os.path.join(ROOT, "src", "data", "vocabSeed.ts")
    with open(path, encoding="utf-8") as f:
        content = f.read().replace("\\'", "'")
    words += re.findall(r"word['\"]?\s*:\s*['\"]([^'\"]+)['\"]", content)
    seen = set()
    unique = []
    for w in words:
        if w not in seen:
            seen.add(w)
            unique.append(w)
    return unique


def load_meta():
    """word -> {pos, cn}"""
    meta = {}
    path = os.path.join(ROOT, "src", "data", "vocabSeed.ts")
    with open(path, encoding="utf-8") as f:
        content = f.read().replace("\\'", "'")
    for m in re.finditer(
        r"word['\"]?\s*:\s*['\"]([^'\"]+)['\"]\s*,\s*pos['\"]?\s*:\s*['\"]([^'\"]*)['\"]\s*,\s*cn['\"]?\s*:\s*['\"]([^'\"]*)['\"]",
        content,
    ):
        meta[m.group(1)] = {"pos": m.group(2), "cn": m.group(3)}
    return meta


def main():
    words = load_words()
    meta = load_meta()
    emojis = json.load(open(os.path.join(ROOT, "src", "data", "wordEmojis.json"), encoding="utf-8"))
    missing = [w for w in words if w not in emojis]
    out = []
    for w in missing:
        m = meta.get(w, {"pos": "", "cn": ""})
        out.append({"word": w, "pos": m["pos"], "cn": m["cn"]})
    # 排序: 词组按字母, 专有名词按字母
    out.sort(key=lambda x: x["word"].lower())
    dest = os.path.join(ROOT, "tools", "_missing_emoji_271.json")
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"缺失 {len(out)} 词 → {dest}")
    for item in out:
        print(f"{item['word']}  [{item['pos']}]  {item['cn']}")


if __name__ == "__main__":
    main()
