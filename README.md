# Daily English Reading Reports

毎朝7時（JST）に自動生成される英語多読用レポート。
目標：**3,600語 / 30分 / 120 WPM** — Markdown + **PDF** の2形式で保存。

## 仕組み

GitHub Actionsが毎朝22:00 UTC（= 07:00 JST）に起動し、`config.json`の興味分野を元にClaude claude-opus-4-6がレポートを生成。`reports/YYYY-MM-DD.md` と `reports/YYYY-MM-DD.pdf` として保存されます。

## セットアップ（1分）

### 1. ANTHROPIC_API_KEY をシークレットに追加

GitHub リポジトリの **Settings → Secrets and variables → Actions** で：

```
Name:  ANTHROPIC_API_KEY
Value: sk-ant-...
```

### 2. 動作確認（任意）

**Actions → Daily English Report → Run workflow** から手動実行できます。

### 3. ローカルで試す

```bash
pip install anthropic markdown weasyprint
export ANTHROPIC_API_KEY="sk-ant-..."
python generate_report.py
```

## レポート構成（毎日固定）

| セクション | 語数 | 内容 |
|---|---|---|
| Today's Report | ~80語 | 見出し・フック |
| Main Story | ~1,800語 | メインの深掘り記事 |
| Second Story | ~1,200語 | サブトピック |
| Quick Takes | ~300語 | ショートニュース3本 |
| Word of the Day | ~120語 | 今日の単語（語源・例文付き） |
| **合計** | **~3,600語** | **30分 @ 120 WPM** |

## 曜日別トピックローテーション

| 曜日 | メイン | サブ | クイック |
|---|---|---|---|
| 月 | 世界・日本ニュース | ビジネス機会 | AI最新動向 |
| 火 | 世界・日本ニュース | スタートアップ | ファイナンス動向 |
| 水 | 世界・日本ニュース | コモディティ | 地政学リスク |
| 木 | 世界・日本ニュース | ファイナンス動向 | ファイナンス基礎 |
| 金 | 世界・日本ニュース | 副業ビジネス | リスクマネジメント |
| 土 | 世界・日本ニュース | 日本不動産 | ファイナンス |
| 日 | 世界・日本ニュース | AI・Claude Code | 週次ファイナンスまとめ |

## ファイル構成

```
├── generate_report.py              # レポート生成スクリプト
├── config.json                     # 興味分野の設定
├── reports/
│   ├── 2026-03-20.md
│   ├── 2026-03-20.pdf              ← これを電車で読む
│   └── ...
└── .github/workflows/
    └── daily_report.yml            # 毎朝7時JST自動実行
```

## PDFの配布方法（任意）

生成されたPDFはGitHubリポジトリの `reports/` フォルダに保存されます。
スマホで読むには以下のいずれかが便利です：

- **GitHub Mobile アプリ**でリポジトリを開く
- **GitHub Releases** にPDFを添付するよう改造する（別途設定）
- **Slack/Discord Bot** でPDFを自動送信する（別途設定）
