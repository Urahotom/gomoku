# 五目並べ - Gomoku

人間 vs AI(キャラクター)の五目並べゲーム。**画像とテキストを差し替えるだけで対戦キャラを換装できる**、pygame 製のデスクトップゲームです。

Version: **1.0**

## 特徴

- 15x15 盤、フリーチュールール(禁じ手なし、長連勝ち)
- negamax + alpha-beta 探索の AI(レベル・深さを設定で調整可能)
- ホバープレビュー、打石アニメ、勝利ライン演出などの UI/UX
- キャラは `assets/characters/<キャラID>/` の差し替えだけで追加可能(立ち絵 3 種 + `dialog.json`)
- 音声ファイルが無い場合は numpy でプレースホルダを自動生成(差し替え対応)
- 依存は `pygame` のみ

## 動作環境

| 項目 | 条件 |
|---|---|
| OS | Windows 10/11(Linux / macOS でも動作目安) |
| Python | 3.10 以上 |
| pygame | 2.6 以上 |

## セットアップと起動

```
pip install -r requirements.txt
python main.py
```

## 操作方法

| 入力 | 動作 |
|---|---|
| マウス移動 | ホバープレビュー |
| 左クリック | 石を置く / 決定 |
| Enter / Space | 決定(タイトル開始、リザルト継続) |
| R | 対局再戦 |
| ESC | 対局を破棄してタイトルへ |
| M / V | SE / BGM のミュート切替 |

## 設定(`config.json`)

`character`(キャラID)、`bgm_volume` / `se_volume`(音量)、`player_is_black`(先手)、
`ai_level`(1: 簡易ヒューリスティック / 2: 探索 AI)、`ai_depth`(探索深さ)、`ai_noise` など。
音量・ミュート設定は終了時に自動保存されます。

## キャラ・音声の差し替え

- キャラ追加: `assets/characters/` 内のフォルダをコピーし、`config.json` の `character` を変更するだけ。
- 音声差し替え: `assets/audio/` に `bgm_title.ogg` など同名ファイルを置くだけで自動切替。
  詳細は [SPEC.md](SPEC.md) の §5・§6 を参照。

## テスト

```
python main.py --selftest
```

AI の勝敗判定・受け手の自己検証と、レベル 2 > レベル 1 の強さ検証を行います。

## ドキュメント

設計・仕様的详细は [SPEC.md](SPEC.md) を参照。

## ライセンス

[MIT](LICENSE) © 2026 Urahotom
