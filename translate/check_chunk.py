"""Check a translation chunk before it goes into translate/manual/texts/.

    python translate/check_chunk.py <chunk_in.json> <chunk_out.json> [<reference.json>]

chunk_in  = {"texts": {zh: {...}}}  (from translate/todo.json)
chunk_out = {"texts": {zh: en | null}}

Errors (exit 1): a key of chunk_in missing in chunk_out, an extra key, or a number mismatch
(the multisets of Arabic numbers of zh and en must be equal; gamedict.numbers).
Warnings: Chinese characters left in en; a glossary/name term present in zh whose English is
not found in en (case-insensitive).
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gamedict import numbers  # noqa: E402

HAN = re.compile(r"[㐀-鿿]")


def main(cin, cout, ref=None):
    src = json.load(open(cin, encoding="utf-8"))["texts"]
    out = json.load(open(cout, encoding="utf-8"))["texts"]
    terms = {}
    if ref:
        r = json.load(open(ref, encoding="utf-8"))
        terms = {**r.get("terms", {}), **r.get("names", {})}
    errors, warnings = [], []
    for zh in src:
        if zh not in out:
            errors.append(("missing key", zh))
            continue
        en = out[zh]
        if en is None:
            continue
        if Counter(numbers(zh)) != Counter(numbers(en)):
            errors.append(("numbers %s vs %s" % (sorted(numbers(zh)), sorted(numbers(en))), zh))
        if HAN.search(en):
            warnings.append(("Chinese left in English", zh))
        # longest terms first, each zh position used once
        used = [False] * len(zh)
        for t in sorted(terms, key=len, reverse=True):
            if len(t) < 2 or not terms[t]:
                continue
            for m in re.finditer(re.escape(t), zh):
                if any(used[m.start():m.end()]):
                    continue
                for i in range(m.start(), m.end()):
                    used[i] = True
                if terms[t].lower() not in en.lower():
                    warnings.append(("term %s -> %s not in English" % (t, terms[t]), zh))
                break
    for zh in out:
        if zh not in src:
            errors.append(("extra key", zh))
    for kind, zh in errors:
        print("ERROR", kind, "|", zh)
    for kind, zh in warnings:
        print("warn ", kind, "|", zh[:80])
    print("%d texts, %d errors, %d warnings" % (len(src), len(errors), len(warnings)))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:4]))
