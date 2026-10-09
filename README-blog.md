# Blenda Core ブログのしくみ

記事は `_posts/` にMarkdownで置きます。GitHub Pages（Jekyll）が自動でページ化し、https://blendacore.com/blog/ に公開されます。

## ファイル構成

| ファイル | 役割 |
| --- | --- |
| `_config.yml` | ブログ全体の設定（URL、記事のURL形式、サイトマップ・RSSなど） |
| `_layouts/base.html` | ブログ共通の枠（ヘッダー・フッター） |
| `_layouts/post.html` | 記事ページのデザイン |
| `blog/index.html` | 記事一覧ページ（/blog/） |
| `assets/blog.css` | ブログのデザイン（トップページと同じ配色） |
| `assets/logo.png` | ヘッダー用ロゴ |
| `_posts/` | 記事ファイル（Markdown） |
| `scripts/post-template.md` | 記事のひな形 |
| `frontmatter.json` | VS Code の Front Matter CMS 用の設定 |

`index.html`（トップページ）はこれまでどおりそのまま表示されます。

## 記事を書く

- `scripts/post-template.md` をコピーして `_posts/` に置き、`2026-10-01-英語のスラッグ.md` のような「日付-スラッグ.md」の名前にします
- VS Code の Front Matter CMS からも作成・編集できます
- コミットしてpushすると、数分で公開されます

## ローカルで表示を確認する（Windows）

### 最初に1回だけ
1. https://rubyinstaller.org/downloads/ から **Ruby+Devkit**（「WITH DEVKIT」の一番上、x64）をダウンロードしてインストール
2. インストールの最後に出る黒い画面で `ridk install` が始まったら、`1,3` と入力（または何も入れずに）Enter。終わったらEnterで閉じる
3. PowerShellを開き直して、このフォルダで次を実行
   ```
   gem install bundler
   bundle install
   ```

### 毎回
- `preview.bat` をダブルクリック → ブラウザで http://localhost:4000/blog/ が開きます
- 記事ファイルを保存すると、ブラウザが自動で更新されます
- 終わるときは黒い画面で `Ctrl + C`

うまく動かないときは、`bundle exec jekyll serve` をPowerShellで直接実行して、表示されたエラーを見てください。
