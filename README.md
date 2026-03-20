# Daily English Reading Reports

毎朝7時（JST）に自動生成される英語多読用レポート。
目標：**3,600語 / 30分 / 120 WPM**

## 仕組み

GitHub Actionsが毎朝22:00 UTC（= 7:00 JST）に起動し、`config.json`の興味分野を元にClaude APIがレポートを生成。`reports/YYYY-MM-DD.md` として保存されます。

## セットアップ

### 1. ANTHROPIC_API_KEY をシークレットに追加

GitHub リポジトリの **Settings → Secrets and variables → Actions** で：

```
Name:  ANTHROPIC_API_KEY
Value: sk-ant-...
```

### 2. 興味分野を設定

`config.json` を編集：

```json
{
  "interests": ["technology", "AI", "business", "science"],
  "exclude_topics": ["politics", "sports"],
  "level": "intermediate",
  "style": "magazine article"
}
```

| フィールド | 説明 | 例 |
|---|---|---|
| `interests` | 読みたいトピック（複数OK） | `["AI", "travel", "food", "history"]` |
| `exclude_topics` | 除外したいトピック | `["politics", "war"]` |
| `level` | 英語レベル | `"intermediate"` / `"advanced"` |
| `style` | 文体 | `"magazine article"` / `"news"` / `"essay"` |

### 3. ローカルで試す

```bash
pip install anthropic
export ANTHROPIC_API_KEY="sk-ant-..."
python generate_report.py
```

## レポートの読み方

各レポートは以下の構成：

| セクション | 語数 | 内容 |
|---|---|---|
| Today's Report | ~80語 | 見出し＋導入 |
| Main Story | ~1,800語 | メインの深掘り記事 |
| Second Story | ~1,200語 | サブトピック |
| Quick Takes | ~300語 | ショートニュース3本 |
| Word of the Day | ~120語 | 今日の単語 |
| **合計** | **~3,600語** | **30分 @ 120 WPM** |

## ファイル構成

```
├── generate_report.py       # レポート生成スクリプト
├── config.json              # 興味分野の設定
├── reports/
│   ├── 2026-03-20.md
│   ├── 2026-03-21.md
│   └── ...
└── .github/workflows/
    └── daily_report.yml     # 自動実行スケジュール
```
