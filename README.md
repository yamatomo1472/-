# Daily English Reading Reports

毎朝7時（JST）に英語レポートを自動生成して **Notion に投稿**。
目標：**3,600語 / 30分 / 120 WPM**

---

## セットアップ（5分）

### Step 1 — Notion Integration を作成してトークンを取得

1. [notion.so/my-integrations](https://www.notion.so/my-integrations) を開く
2. **「+ New integration」** をクリック
3. 名前を入力（例：`Daily English Report`）→ **「Submit」**
4. 表示された **Internal Integration Token**（`secret_...`）をコピーして保存

### Step 2 — 受け取るNotionページを用意して共有

1. Notionで新しいページを作成（例：`📖 Daily English Reports`）
2. そのページを開き、右上の **「...」→「Connections」→「Connect to」** から Step 1 で作ったインテグレーションを選んで接続
3. そのページの **URLからページIDを取得**

```
https://www.notion.so/Your-Page-Title-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
                                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                      これがページID（32文字）
```

### Step 3 — GitHub Secretsに追加

GitHubリポジトリの **Settings → Secrets and variables → Actions → New repository secret**

| Name | Value |
|---|---|
| `ANTHROPIC_API_KEY` | `sk-ant-...` |
| `NOTION_TOKEN` | `secret_...`（Step 1のトークン） |
| `NOTION_PAGE_ID` | `xxxxxxxx...`（Step 2の32文字ID） |

### Step 4 — 動作確認

**Actions → Daily English Report → Run workflow** で手動実行。
数分後にNotionページが作成されれば完了です。

---

## Notionに作られるページのイメージ

```
📖 Daily English Report — 2026-03-21 (Saturday)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📖  3,587 words  |  30 min at 120 WPM  |  2026-03-21
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📰 Japan's Startup Scene Breaks Records as...

...
## Main Story: ...
## Second Story: ...
## ⚡ Quick Takes
## 📖 Word of the Day
```

すべてのセクションがNotionブロックとして展開されるので、
スマホのNotionアプリから快適に読めます。

---

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
| 日 | 世界・日本ニュース | AI・Claude Code | 週次まとめ |

---

## 設定（config.json）

```json
{
  "notion": true,   // Notionに投稿する
  "email": false,   // メール送信（Gmail設定が必要）
  "pdf": true       // PDFもreports/に保存する
}
```

メールも併用したい場合は `"email": true` にして、
GitHubSecretsに `GMAIL_ADDRESS` / `GMAIL_APP_PASSWORD` / `RECIPIENT_EMAIL` を追加してください。

---

## ローカルで試す

```bash
pip install anthropic markdown weasyprint notion-client

export ANTHROPIC_API_KEY="sk-ant-..."
export NOTION_TOKEN="secret_..."
export NOTION_PAGE_ID="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

python generate_report.py
```

## ファイル構成

```
├── generate_report.py              # レポート生成・Notion投稿・メール送信
├── config.json                     # 興味分野・出力先設定
├── reports/                        # MarkdownとPDFのバックアップ
└── .github/workflows/
    └── daily_report.yml            # 毎朝7時JST自動実行
```
