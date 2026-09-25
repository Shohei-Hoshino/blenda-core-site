# ローカルで表示を確認するための設定（本番のGitHub Pagesはこのファイルを使いません）
# 公式の github-pages パッケージは古いJekyllを使っていて新しいRubyで動かないため、
# 新しいJekyll＋本番と同じプラグインで表示を再現しています。
source "https://rubygems.org"

gem "jekyll", "~> 4.4"

group :jekyll_plugins do
  gem "jekyll-seo-tag"
  gem "jekyll-sitemap"
  gem "jekyll-feed"
end

# 新しいRubyで標準から外れたライブラリ
gem "webrick"
gem "csv"
gem "base64"
gem "bigdecimal"
gem "logger"

# Windows用
gem "tzinfo-data", platforms: [:windows]
gem "wdm", ">= 0.2", platforms: [:windows]
