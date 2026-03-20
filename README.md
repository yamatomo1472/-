# Daily English Reading Reports

毎朝7時（JST）に英語レポートを自動生成してメール送信。
目標：**3,600語 / 30分 / 120 WPM** — PDF添付メールで届く。

---

## セットアップ（5分）

### Step 1 — Gmail App Passwordを取得

通常のGmailパスワードではなく「アプリパスワード」が必要です。

1. Googleアカウントにログイン → [myaccount.google.com/security](https://myaccount.google.com/security)
2. **「2段階認証プロセス」** をオンにする（まだの場合）
3. 同じページで **「アプリパスワード」** をクリック
4. アプリ名を適当に入力（例：`Daily English Report`）→ **「作成」**
5. 表示された **16文字のパスワード**（スペースなし）をコピーして保存

### Step 2 — GitHub Secretsに4つ追加

GitHubリポジトリの **Settings → Secrets and variables → Actions → New repository secret**

| Name | Value | 説明 |
|---|---|---|
| `ANTHROPIC_API_KEY` | `sk-ant-...` | Claude APIキー |
| `GMAIL_ADDRESS` | `you@gmail.com` | 送信元Gmailアドレス |
| `GMAIL_APP_PASSWORD` | `xxxx xxxx xxxx xxxx` | Step 1で取得した16文字 |
| `RECIPIENT_EMAIL` | `you@gmail.com` | 受信先（送信元と同じでOK） |

> `RECIPIENT_EMAIL` は省略可。省略すると `GMAIL_ADDRESS` に送信されます。

### Step 3 — 動作確認

**Actions → Daily English Report → Run workflow** で手動実行。
数分後にメールが届けば完了です。

---

## 毎日届くメールのイメージ

```
件名: 📖 Daily English Report — 2026-03-21 (Saturday)

Good morning!

Today's English reading report is attached.

📊 Stats
  Date       : 2026-03-21 (Saturday)
  Word count : 3,587 words
  Reading time: 30 minutes at 120 WPM

Open the PDF and enjoy your commute reading!
```

PDFが添付されているのでそのまま開いて読めます。

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

## ファイル構成

```
├── generate_report.py              # レポート生成・メール送信
├── config.json                     # 興味分野・設定
├── reports/
│   ├── 2026-03-20.md
│   ├── 2026-03-20.pdf
│   └── ...
└── .github/workflows/
    └── daily_report.yml            # 毎朝7時JST自動実行
```

## ローカルで試す

```bash
pip install anthropic markdown weasyprint

export ANTHROPIC_API_KEY="sk-ant-..."
export GMAIL_ADDRESS="you@gmail.com"
export GMAIL_APP_PASSWORD="xxxxxxxxxxxx"
export RECIPIENT_EMAIL="you@gmail.com"

python generate_report.py
```
