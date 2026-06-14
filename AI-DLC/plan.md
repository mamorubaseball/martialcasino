# Project Development Life Cycle (AI-DLC) - 全体計画

本プロジェクト（Investment Media Platform）は、米国株分析メディア「TechMoney」と日本株分析メディア「かぶまる」の2つのWebサイトをモノレポ構造で管理し、YouTube動画台本からプレミアムなウェブコンテンツを半自動で生成・配信するプラットフォームです。

開発と運用のロードマップを以下のフェーズに分けて管理します。

---

## 📅 フェーズ概要

### 🟡 フェーズ 0: プラットフォーム基盤構築とTechMoney初期実装（レビュー中）
* **目的**: 2つの独立したAstroサイトの基盤構築、TechMoneyのデザインシステム・基本コンポーネント定義、インフラとスクリプトの基礎作成。
* **ステータス**: ユーザーによるデザイン・UI/UXの確認・レビュー待ち
* **詳細**: [phase0.md](file:///Users/mamoru/AntigravityCompany/投資メディア事業/investment-platform/AI-DLC/phase0.md)

### 🟡 フェーズ 1: TechMoney 台本からのAI直出しHTML生成と移行（現在）
* **目的**: TechMoney（米国株）の動画台本から直接デザイン性の高いAstroページ（.astro）とコレクション用インデックス（.md）を1ステップで自動生成し配置するワークフローの確立、および未移行台本のインポート。
* **ステータス**: 進行中
* **詳細**: [phase1.md](file:///Users/mamoru/AntigravityCompany/投資メディア事業/investment-platform/AI-DLC/phase1.md)

### ⚪ フェーズ 2: TechMoney のSEO・インフラ・実運用最適化
* **目的**: TechMoney の公開に向けたSEO対策（メタタグ、サイトマップ、構造化データ）、レスポンシブ微調整、ホスティング環境（VercelやCloudflare Pagesなど）へのデプロイ準備、ポートフォリオ自動更新ワークフローとの接続。
* **ステータス**: 未着手
* **詳細**: [phase2.md](file:///Users/mamoru/AntigravityCompany/投資メディア事業/investment-platform/AI-DLC/phase2.md)

### ⚪ フェーズ 3: TechMoney のデータ連携・AI対話機能と初回リリース
* **目的**: 各銘柄詳細ページや分析記事へのインタラクティブなチャート追加、Gemini APIを利用した「データと会話する」対話型コンポーネントの埋め込み、およびTechMoneyの初回リリース。
* **ステータス**: 未着手
* **詳細**: [phase3.md](file:///Users/mamoru/AntigravityCompany/投資メディア事業/investment-platform/AI-DLC/phase3.md)

### ⚪ フェーズ 4: かぶまる（日本株メディア）の本格デザイン決定・実装・リリース
* **目的**: 日本株・資産形成メディア「かぶまる」の本格的なデザイン決定、UI/UXの構築、個別銘柄ページのカスタム、台本のインポート移行、およびリリース。
* **ステータス**: 未着手
* **詳細**: [phase4.md](file:///Users/mamoru/AntigravityCompany/投資メディア事業/investment-platform/AI-DLC/phase4.md)

