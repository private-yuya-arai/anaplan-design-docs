#!/usr/bin/env python3
"""設計書 v42（Markdown）の整合チェック。

使い方:
    python tools/check_design.py docs/order-quantity/v42/design.md

確かめること:
    1. 台帳のつながり表：画面の数・モデルの数が中身と一致し、0件がない
    2. つながりのない画面：6.2のカード（テキストとページ移動を除く）が、すべて台帳に出てくる
    3. つながりのないモデル：4.1のリストと4.2の次元表のモジュールが、すべて台帳に出てくる
    4. 概念図の矢印の数が、概念の関係表の行数と一致する
    5. 2.1のすべてのFRが、6.3に出てくる
    6. 4.3のすべての分岐にテストがあり、そのテストが10章にある
    7. 4.2の次元表のライン項目数の合計が、4.4のライン項目の行数と一致する
1件でも NG があれば終了コード 1 を返す。
"""
import re
import sys
from pathlib import Path


def parse(md: str):
    """見出しの位置付きで、表と Mermaid のコードを取り出す。"""
    tables, mermaids = [], []
    heads: list[str] = []
    in_code, lang, buf, cur = False, "", [], None
    for raw in md.splitlines():
        line = raw.rstrip()
        if line.lstrip().startswith("```"):
            if not in_code:
                in_code, lang, buf = True, line.strip()[3:].strip(), []
            else:
                if lang == "mermaid":
                    mermaids.append({"path": " / ".join(h for h in heads if h), "code": "\n".join(buf)})
                in_code = False
            cur = None
            continue
        if in_code:
            buf.append(line)
            continue
        m = re.match(r"^(#{1,6})\s+(.*)", line)
        if m:
            level = len(m.group(1))
            heads = heads[: level - 1]
            heads += [""] * (level - 1 - len(heads))
            heads.append(m.group(2).strip())
            cur = None
            continue
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if cur is None:
                cur = {"path": " / ".join(h for h in heads if h), "header": cells, "rows": []}
                tables.append(cur)
            elif all(re.fullmatch(r":?-{3,}:?", c) for c in cells if c):
                continue
            else:
                cur["rows"].append(dict(zip(cur["header"], cells)))
        else:
            cur = None
    return tables, mermaids


def find(tables, path_kw: str, *cols: str):
    """見出しに path_kw を含み、列名が cols で始まる列をすべて持つ表を返す。
    列名は「表示する画面（6.2）」のような補足付きでも、先頭が一致すればよい。"""
    for t in tables:
        if path_kw in t["path"] and all(any(h.startswith(c) for h in t["header"]) for c in cols):
            t["rows"] = [{_key(t["header"], k): v for k, v in r.items()} for r in t["rows"]]
            return t
    return None


def _key(header, k):
    """補足付きの列名を、補足なしの名前でも引けるようにする（例：表示する画面（6.2）→ 表示する画面）。"""
    return re.sub(r"（[^（）]*）$", "", k) if not k.endswith("（回数）") and not k.endswith("（現在）") else k


def ids(cell: str) -> list[str]:
    parts = re.split(r"[、,]\s*", cell or "")
    return [p.strip() for p in parts if p.strip() and p.strip() not in ("—", "-")]


def main(path: str) -> int:
    md = Path(path).read_text(encoding="utf-8")
    tables, mermaids = parse(md)
    results: list[tuple[str, bool, str]] = []

    def add(name, ok, detail=""):
        results.append((name, ok, detail))

    ledger = find(tables, "つながり表", "概念ID", "表示する画面", "実装するモデル")
    if not ledger:
        add("台帳のつながり表", False, "表が見つからない")
        screens_in_ledger, models_in_ledger = set(), set()
    else:
        bad = []
        screens_in_ledger, models_in_ledger = set(), set()
        for r in ledger["rows"]:
            s, m = ids(r.get("表示する画面", "")), ids(r.get("実装するモデル", ""))
            screens_in_ledger |= set(s)
            models_in_ledger |= set(m)
            try:
                ns, nm = int(r.get("画面の数", "-1")), int(r.get("モデルの数", "-1"))
            except ValueError:
                ns, nm = -1, -1
            if ns != len(s) or nm != len(m):
                bad.append(f"{r.get('概念ID')} の件数が中身と合わない")
            if not s:
                bad.append(f"{r.get('概念ID')} は画面に出ない")
            if not m:
                bad.append(f"{r.get('概念ID')} はモデルがない")
        add("1. 台帳の件数", not bad, "、".join(bad))

    cards_t = find(tables, "6.2", "カード", "表示元")
    if cards_t:
        # テキストとページ移動のカードはデータを表示しないので、台帳の対象外
        cards = [r["カード"] for r in cards_t["rows"]
                 if re.fullmatch(r"P\d+-\d+", r.get("カード", ""))
                 and r.get("種類") != "テキスト" and r.get("表示元") != "ページ移動"]
        missing = [c for c in cards if not any(x.startswith(c + " ") or x == c for x in screens_in_ledger)]
        add("2. つながりのない画面", not missing, "、".join(missing))
    else:
        add("2. つながりのない画面", False, "6.2の表が見つからない")

    dim_t = find(tables, "4.2", "モジュール", "ライン項目数")
    list_t = find(tables, "4.1", "リスト", "種類")
    expected = []
    if dim_t:
        expected += [r["モジュール"].split()[0] for r in dim_t["rows"] if r.get("モジュール")]
    if list_t:
        expected += ["リスト " + r["リスト"] for r in list_t["rows"] if r.get("リスト") and r["リスト"] != "時間"]
    missing = [e for e in expected if e not in models_in_ledger]
    add("3. つながりのないモデル", bool(expected) and not missing, "、".join(missing) or ("" if expected else "4.1か4.2の表が見つからない"))

    rel_t = find(tables, "概念の関係表", "元", "先")
    concept_fig = next((m for m in mermaids if "概念図" in m["path"]), None)
    if rel_t and concept_fig:
        arrows = concept_fig["code"].count("-->")
        add("4. 概念図と関係表", arrows == len(rel_t["rows"]), f"矢印 {arrows} 本、関係表 {len(rel_t['rows'])} 行")
    else:
        add("4. 概念図と関係表", False, "関係表か概念図が見つからない")

    fr_t = find(tables, "2.1", "ID", "要件")
    trace_t = find(tables, "6.3", "要件", "テスト")
    if fr_t and trace_t:
        frs = [r["ID"] for r in fr_t["rows"] if r.get("ID", "").startswith("FR")]
        text = " ".join(r.get("要件", "") for r in trace_t["rows"])
        missing = [f for f in frs if f not in text]
        add("5. FRと6.3", not missing, "、".join(missing))
    else:
        add("5. FRと6.3", False, "2.1か6.3の表が見つからない")

    br_t = find(tables, "4.3", "分岐", "テスト")
    test_t = find(tables, "10.", "ID", "期待結果")
    if br_t and test_t:
        tests = {r["ID"] for r in test_t["rows"]}
        bad = []
        for r in br_t["rows"]:
            refs = ids(r.get("テスト", ""))
            if not refs:
                bad.append(f"{r.get('分岐')} にテストがない")
            bad += [f"{r.get('分岐')} の {t} が10章にない" for t in refs if t not in tests]
        add("6. 分岐とテスト", not bad, "、".join(bad))
    else:
        add("6. 分岐とテスト", False, "4.3の分岐表か10章の表が見つからない")

    spec_rows = sum(len(t["rows"]) for t in tables if "4.4" in t["path"] and "ライン項目" in t["header"])
    if dim_t:
        try:
            dim_sum = sum(int(r["ライン項目数"]) for r in dim_t["rows"])
        except (KeyError, ValueError):
            dim_sum = -1
        add("7. ライン項目数", dim_sum == spec_rows, f"次元表 {dim_sum}、4.4 {spec_rows} 行")
        try:
            cells = sum(int(r["セル数（現在）"].replace(",", "")) for r in dim_t["rows"])
            print(f"参考：モデル全体のセル数（現在） {cells:,}")
        except (KeyError, ValueError):
            pass

    ng = 0
    for name, ok, detail in results:
        mark = "OK" if ok else "NG"
        ng += 0 if ok else 1
        print(f"[{mark}] {name}" + (f"：{detail}" if detail else ""))
    print(f"NG {ng} 件")
    return 1 if ng else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
