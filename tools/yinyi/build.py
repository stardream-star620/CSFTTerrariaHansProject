# -*- coding: utf-8 -*-
"""Build the 音译 (transliteration) variant of the 亚共版 Chinese localization.

Sources
-------
* sources/yinyi/*.json  : the human-made transliteration corpus
                           (extracted from the Steam Workshop mod
                           "TerrariaTransliteratedEdition" by HoCha113)
* backup_en/en-US*.json : the English original, used as the key universe and
                           as the input for machine transliteration
* zh-Hans*.json         : the current 亚共版 translation, used as the key
                           universe (it also carries a few keys the English
                           files no longer have)

Every key covered by the corpus is copied verbatim. Keys the corpus does not
cover are transliterated with tools/yinyi/translit.py, reusing the corpus as a
word/phrase memory so that the machine output stays consistent with the human
output (e.g. "Adamantite" always becomes 阿戴慢泰特).
"""

from __future__ import annotations

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOURCES = os.path.join(ROOT, "sources", "yinyi")
sys.path.insert(0, HERE)

from translit import Transliterator, TOKEN_RE, HAS_LATIN  # noqa: E402

PAIRS = [
    ("zh-Hans.json", "Main.json", "en-US.json"),
    ("zh-Hans.Items.json", "Items.json", "en-US.Items.json"),
    ("zh-Hans.Game.json", "Game.json", "en-US.Game.json"),
    ("zh-Hans.NPCs.json", "NPCs.json", "en-US.NPCs.json"),
    ("zh-Hans.Projectiles.json", "Projectiles.json", "en-US.Projectiles.json"),
    ("zh-Hans.Town.json", "Town.json", "en-US.Town.json"),
    ("zh-Hans.Legacy.json", "Legacy.json", "en-US.Legacy.json"),
    ("zh-Hans.Mobile.json", None, "en-US.Mobile.json"),
    ("zh-Hans.PS4.json", None, "en-US.PS4.json"),
    ("zh-Hans.Switch.json", None, "en-US.Switch.json"),
    ("zh-Hans.XBO.json", None, "en-US.XBO.json"),
]

TRAILING_COMMA = re.compile(r",\s*([}\]])")
HANZI = re.compile(r"[\u4e00-\u9fff]")
WORD_ONLY = re.compile(r"^[A-Za-z][A-Za-z'\-]*$")


def load_json(path: str):
    raw = open(path, "rb").read().decode("utf-8-sig")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return json.loads(TRAILING_COMMA.sub(r"\1", raw))


def walk(node, path=()):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from walk(v, path + (k,))
    else:
        yield path, node


def set_path(tree, path, value):
    node = tree
    for key in path[:-1]:
        node = node.setdefault(key, {})
    node[path[-1]] = value


def build_memory(corpus_pairs):
    """Learn word-level and phrase-level transliterations from the corpus."""
    word_counts = {}
    phrase = {}
    total = 0
    for en_tree, zy_tree in corpus_pairs:
        for path, zh in walk(zy_tree):
            if not isinstance(zh, str) or not zh:
                continue
            en = en_tree
            for key in path:
                if not isinstance(en, dict) or key not in en:
                    en = None
                    break
                en = en[key]
            if not isinstance(en, str) or not en:
                continue
            total += 1
            if HAS_LATIN.search(zh):
                continue
            key = en.strip().lower()
            if WORD_ONLY.match(key) and len(zh) <= 12:
                word_counts.setdefault(key, {}).setdefault(zh, 0)
                word_counts[key][zh] += 1
            elif len(key) <= 120 and "{" not in key and "[" not in key:
                phrase.setdefault(key, {}).setdefault(zh, 0)
                phrase[key][zh] += 1
    word_memory = {k: max(v.items(), key=lambda kv: kv[1])[0] for k, v in word_counts.items()}
    phrase_memory = {k: max(v.items(), key=lambda kv: kv[1])[0] for k, v in phrase.items()}
    return word_memory, phrase_memory, total


SPACE_FIX = [
    (re.compile(r"[ \t]{2,}"), " "),
    (re.compile(r"\s+([,.;:!?，。；：！？、])"), r"\1"),
    (re.compile(r"([（(])\s+"), r"\1"),
]


def polish(text: str) -> str:
    for pattern, repl in SPACE_FIX:
        text = pattern.sub(repl, text)
    return text.strip() if text.strip() else text


def tokens(text: str):
    return sorted(m.group(0) for m in TOKEN_RE.finditer(text))


def main():
    corpus_pairs = []
    for _, mod_name, _ in PAIRS:
        if not mod_name:
            continue
        path = os.path.join(SOURCES, mod_name)
        if os.path.exists(path):
            corpus_pairs.append(load_json(path))

    source_pairs = []
    for repo_name, mod_name, en_name in PAIRS:
        en_path = os.path.join(ROOT, "backup_en", en_name)
        en_tree = load_json(en_path) if os.path.exists(en_path) else {}
        mod_tree = {}
        if mod_name and os.path.exists(os.path.join(SOURCES, mod_name)):
            mod_tree = load_json(os.path.join(SOURCES, mod_name))
        source_pairs.append((repo_name, en_tree, mod_tree))

    word_memory, phrase_memory, learned = build_memory(
        [(en, mod) for _, en, mod in source_pairs if mod]
    )
    overrides_path = os.path.join(HERE, "overrides.json")
    overrides = load_json(overrides_path) if os.path.exists(overrides_path) else {}
    tr = Transliterator(
        phrase_memory=phrase_memory, word_memory=word_memory, overrides=overrides
    )

    stats = {
        "learned": learned,
        "words": len(word_memory),
        "phrases": len(phrase_memory),
        "overrides": len(overrides),
    }
    total_corpus = total_generated = total_kept = token_issues = 0
    samples = []

    for repo_name, en_tree, mod_tree in source_pairs:
        target_path = os.path.join(ROOT, repo_name)
        zh_tree = load_json(target_path)
        out = {}
        for path, zh in walk(zh_tree):
            en = en_tree
            for key in path:
                en = en[key] if isinstance(en, dict) and key in en else None
                if en is None:
                    break

            mod_value = mod_tree
            for key in path:
                mod_value = mod_value[key] if isinstance(mod_value, dict) and key in mod_value else None
                if mod_value is None:
                    break

            if isinstance(mod_value, str) and mod_value:
                value = mod_value
                total_corpus += 1
            elif isinstance(en, str) and en and HAS_LATIN.search(en):
                value = polish(tr(en))
                total_generated += 1
                if len(samples) < 400:
                    samples.append([repo_name, ".".join(path), en, value])
            elif isinstance(zh, str) and HAS_LATIN.search(zh) and not HANZI.search(zh):
                # no English source (credits, custom keys): transliterate what is there
                value = polish(tr(zh))
                total_generated += 1
                if len(samples) < 400:
                    samples.append([repo_name, ".".join(path), zh, value])
            else:
                value = zh
                total_kept += 1

            if isinstance(en, str) and isinstance(value, str) and value != zh:
                if tokens(en) != tokens(value) and tokens(value):
                    token_issues += 1
            set_path(out, path, value)

        text = json.dumps(out, ensure_ascii=False, indent="\t")
        text = text.replace("\n", "\r\n") + "\r\n"
        with open(target_path, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)

    stats.update(
        corpus=total_corpus,
        generated=total_generated,
        kept=total_kept,
        token_issues=token_issues,
        samples=len(samples),
    )
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    with open(os.path.join(HERE, "last-build-report.json"), "w", encoding="utf-8") as fh:
        json.dump({"stats": stats, "samples": samples}, fh, ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
