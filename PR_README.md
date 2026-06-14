# Investment Media Platform

## プロジェクト概要

YouTubeで発信している投資コンテンツを資産化し、

* YouTube
* Webメディア
* AIランキング
* 将来的な投資エージェント

へ発展させる投資プラットフォームを構築する。

運営メディアは以下の2つ。

### TechMoney

米国株・AI・テクノロジー投資専門メディア

* 米国株分析
* AI銘柄分析
* 半導体
* 宇宙銘柄
* ETF
* AIランキング

YouTubeチャンネル「TechMoney」と連携

---

### Kabumaru

日本株・資産形成専門メディア

* 日本株分析
* NISA
* 高配当株
* 資産形成
* ETF
* AIランキング

YouTubeチャンネル「かぶまる」と連携

---

# なぜこのサイトを作るのか？

## 現状

YouTube動画の台本がHTML形式で大量に蓄積されている。

しかし現在は

YouTube
↓
動画視聴
↓
離脱

となっており、

コンテンツが検索資産として活用されていない。

---

## 解決したい課題

### ① コンテンツ資産化

動画で発信した情報を永続的な資産として蓄積する。

---

### ② SEO流入獲得

Google検索から新規ユーザーを獲得する。

---

### ③ 銘柄情報の集約

動画単位ではなく

銘柄単位

で情報を整理する。

例

NVIDIA

* 動画一覧
* 記事一覧
* 決算分析
* AIスコア
* 関連銘柄

---

### ④ YouTube依存リスクの軽減

プラットフォームを自社資産として保有する。

---

# プロダクト思想

## 動画メディアではなく投資データプラットフォーム

一般的な投資ブログ

記事
↓
カテゴリ
↓
記事

---

本プロジェクト

銘柄
↓
動画
↓
記事
↓
ランキング

---

Entity First設計を採用する。

---

# ドメイン戦略

## Phase1（検証フェーズ）

既存ドメインを利用

techmoney.martialcasino.net

kabumaru.martialcasino.net

目的

* 開発速度向上
* コスト削減
* ブランド検証

---

## Phase2（成長フェーズ）

条件

* 月間10万PV達成
  または
* 月間収益10万円達成

移行先

techmoney.jp

kabumaru.jp

目的

* ブランド独立
* SEO強化
* 将来的な事業価値向上

---

# サイト構成

## TechMoney

### カテゴリ

* AI
* 半導体
* クラウド
* ソフトウェア
* サイバーセキュリティ
* 宇宙
* ETF
* 決算分析

### URL設計

/stock/nvda

/stock/pltr

/stock/amd

/theme/ai

/theme/semiconductor

/ranking/ai

/ranking/growth

/video/nvidia-q1-2026

---

## Kabumaru

### カテゴリ

* 日本株分析
* 高配当株
* NISA
* ETF
* 資産形成
* 投資初心者

### URL設計

/stock/8058

/stock/9432

/ranking/ai

/ranking/dividend

/asset-management

/nisa

---

# 銘柄ページ設計

本サービスの中心機能。

例

NVIDIA

表示内容

* 企業概要
* 業績推移
* 決算情報
* AIスコア
* 関連動画
* 関連記事
* 関連テーマ
* ランキング順位

---

# AIランキング

## コンセプト

AIが企業分析を行いスコアリングする。

例

NVIDIA

AI Score: 95

評価理由

* 売上成長率
* EPS成長率
* ROE
* 利益率
* 市場成長性
* モメンタム

---

## ランキング例

### TechMoney

* AI注目銘柄ランキング
* 成長株ランキング
* 半導体ランキング
* 宇宙銘柄ランキング

### Kabumaru

* AI注目銘柄ランキング
* 高配当ランキング
* 増配ランキング
* 成長株ランキング

---

# 重要な価値

ランキング自体が価値ではない。

ランキング
↓
銘柄ページ
↓
動画
↓
記事

という導線が価値になる。

---

例

AIランキング

↓
NVIDIA

↓
動画10本

↓
記事10本

↓
関連銘柄

という回遊体験を実現する。

---

# レポジトリ構成

investment-platform

├ techmoney-web
│
├ kabumaru-web
│
├ ranking-engine
│
├ stock-data-batch
│
├ llm-analysis
│
├ shared-ui
│
└ infra

---

# システム構成

## techmoney-web

役割

* TechMoneyフロントエンド

---

## kabumaru-web

役割

* Kabumaruフロントエンド

---

## ranking-engine

役割

* AIランキング生成
* スコアリング
* ランキング更新

---

## stock-data-batch

役割

* 株価取得
* 財務情報取得
* 定期バッチ処理

---

## llm-analysis

役割

* AI分析
* レポート生成
* 要約生成

---

# 開発ロードマップ

## Step1 MVP

目的

HTML台本公開

機能

* 記事一覧
* 記事詳細
* 動画埋め込み
* カテゴリ
* 銘柄タグ
* 検索

---

## Step2

銘柄ページ

機能

* 銘柄DB
* 関連記事
* 関連動画

---

## Step3

検索強化

機能

* 銘柄検索
* カテゴリ検索
* タグ検索

---

## Step4

ランキング機能

機能

* AIランキング
* 成長株ランキング
* 高配当ランキング

---

## Step5

会員機能

機能

* ウォッチリスト
* お気に入り
* 通知

---

## Step6

AI投資エージェント

機能

* 銘柄診断
* ポートフォリオ分析
* AI投資アドバイス

---

# マネタイズ

## Phase1

広告収益

* Google AdSense

---

## Phase2

アフィリエイト

* SBI証券
* 楽天証券
* moomoo証券

---

## Phase3

有料会員

月額980円〜

機能

* AI分析レポート
* 全銘柄AIスコア
* ランキング詳細
* ウォッチリスト
* AIポートフォリオ分析

---

## Phase4

自社サービス

AI投資エージェント

---

# サイトデザイン

## TechMoney

コンセプト

Bloomberg × NVIDIA × Apple

世界観

* AI
* テクノロジー
* データ
* 未来感

カラー

* Black
* Navy
* Electric Blue

UI

* Glassmorphism
* 3Dカード
* 発光エフェクト
* 高級感

---

## Kabumaru

コンセプト

Yahoo!ファイナンス × 楽天証券 × 日本の個人投資家

世界観

* 親しみやすさ
* 資産形成
* 日本らしさ
* 安心感

カラー

* White
* Orange
* Red

UI

* 和モダン
* 情報整理型
* 初心者向け
* シンプルな導線

---

# 最終ゴール

YouTubeチャンネルの補助サイトではなく、

「日本最大級の個人投資家向けAI投資プラットフォーム」

を構築する。

動画 → 記事 → 銘柄 → ランキング → AIエージェント

へ進化させる。
