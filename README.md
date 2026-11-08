# design-docs

Anaplan 発注量検討モデルの設計書（v42）と、設計書を書くためのルール。
図はすべて Mermaid、台帳と画面イメージは表で書いているので、Markdown と Excel だけで作成・更新できる。

## ファイル

```
design-docs/
├─ README.md
├─ CLAUDE.md                     Claude Code 向けの作業ルール
├─ docs/order-quantity/
│  ├─ v42/
│  │  ├─ design.md              設計書 v42（正本）
│  │  ├─ rules.md               設計書ルール v42
│  │  └─ log.md                 検討ログ v41〜v42
│  └─ v41/
│     └─ rules.md               設計書ルール v41（旧版 v40 用）
└─ tools/
   └─ check_design.py           設計書の整合チェック
```

## はじめて読む人へ

- 設計書を読む：`design.md` の「はじめに」で、立場ごとに読む章と、読んだ後にすることを確認する。
- 設計書を書く・直す：`rules.md` の同じ名前の節を開き、作り方と完了条件に従う。
- 直した後：`python tools/check_design.py docs/order-quantity/v42/design.md` を実行し、NG が 0 件であることを確かめる。

## 数値について

件数・時刻・計算例などの数値は、説明用の仮置きである。
