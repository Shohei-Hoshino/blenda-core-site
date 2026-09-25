# Blenda Core ブログ 自動投稿のしくみ

毎朝7時ごろ（日本時間）にGitHub Actionsが起動し、Claude APIで記事を1本書いて `_posts/` に追加します。
GitHub Pages（Jekyll）が自動でページ化し、https://blendacore.com/blog/ に公開されます。

## ファイル構成

| ファイル | 役割 |
| --- | --- |
| `_config.yml` | ブログ全体の設定（URL、記事のURL形式、サイトマップ・RSSなど） |
| `_layouts/base.html` | ブログ共通の枠（ヘッダー・フッター） |
| `_layouts/post.html` | 記事ページのデザイン |
| `blog/index.html` | 記事一覧ページ（/blog/） |
| `assets/blog.css` | ブログのデザイン（トップページと同じ配色） |
| `assets/logo.png` | ヘッダー用ロゴ |
| `_posts/` | 記事ファイル（Markdown）。ここに増えていきます |
| `_data/topics.yml` | 記事テーマの候補リスト（上から順に使われます） |
| `scripts/generate_post.py` | 記事を生成するプログラム |
| `.github/workflows/daily-post.yml` | 毎日の自動実行の設定 |

`index.html`（トップページ）はこれまでどおりそのまま表示されます。ヘッダーとフッターに「ブログ」へのリンクだけ追加しています。

## 初期設定（最初に1回だけ）

1. **ファイルをアップロード**
   リポジトリのページで「Add file」→「Upload files」を開き、このフォルダの中身（`.github` フォルダも含めて）をすべてドラッグ＆ドロップして「Commit changes」。
   `index.html` は上書きされます（動画ファイルは変更していないので再アップロード不要です）。

2. **APIキーを登録**
   - https://console.anthropic.com/ でAPIキーを作成（利用にはクレジットの購入が必要です）
   - リポジトリの「Settings」→「Secrets and variables」→「Actions」→「New repository secret」
   - Name: `ANTHROPIC_API_KEY` / Secret: 作成したキー

3. **Actionsにプルリクエスト作成を許可**
   「Settings」→「Actions」→「General」→ 一番下の「Workflow permissions」で
   - 「Read and write permissions」を選択
   - 「Allow GitHub Actions to create and approve pull requests」にチェック
   - 「Save」

4. **GitHub Pagesの設定を確認**
   「Settings」→「Pages」で、Source が「Deploy from a branch」、Branch が `main` / `(root)` になっていればOK。

5. **動作テスト**
   「Actions」タブ →「Daily blog post」→「Run workflow」。数分後にプルリクエストができていれば成功です。
   ※ 同じ日付の記事がすでにある日は、何もせずに終了します。

## 毎日の流れ（初期設定：レビューモード）

1. 毎朝、記事の下書きがプルリクエストとして届きます（GitHubの通知メールが来ます）
2. 「Files changed」で内容を確認。直したい箇所は鉛筆アイコンから直接編集できます
3. 問題なければ「Merge pull request」→ 数分で公開
4. 公開しない場合は「Close pull request」

## 完全自動に切り替える

品質が安定してきたら、「Settings」→「Secrets and variables」→「Actions」→「Variables」タブで
`AUTO_PUBLISH` という変数を作り、値を `true` にしてください。以降は確認なしで毎日公開されます。
元に戻すときは変数を削除するか `false` にします。

## カスタマイズ

- **テーマを変えたい**：`_data/topics.yml` を編集。上から順に未使用のものが使われます。使い切るとAIが既存記事と重ならないテーマを自分で選びます。
- **文体やルールを変えたい**：`scripts/generate_post.py` の `SYSTEM_PROMPT` を編集。
- **投稿時刻を変えたい**：`.github/workflows/daily-post.yml` の `cron`（UTC表記。日本時間から9時間引く）。
- **使うモデルを変えたい**：Variables に `BLOG_MODEL`（例: `claude-opus-5-5`）を追加。未設定なら `claude-sonnet-5`。
- **自分で記事を書きたい**：`_posts/2026-10-01-my-post.md` のように「日付-英語のスラッグ.md」で置けば、そのまま公開されます（先頭の `---` で囲まれた部分は既存記事をまねてください）。

## 注意

- AIの記事は、数値やバージョン、固有の仕様を誤ることがあります。特にレビューモードのうちは、手順や設定値を一度確認してから公開してください。
- 生成プロンプトでは、架空の制作事例やお客様の声を書かないよう指示しています。実際の制作事例を載せたいときは、手で追記するのがおすすめです。
- API利用料は Anthropic Console の「Usage」画面で確認できます。
