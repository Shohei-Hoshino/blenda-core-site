"""Blenda Core ブログ: その日の記事を1本生成して _posts/ に保存する。

GitHub Actions（.github/workflows/daily-post.yml）から毎日呼ばれます。
ローカルで試す場合:
    pip install -r scripts/requirements.txt
    ANTHROPIC_API_KEY=... python scripts/generate_post.py
"""

from __future__ import annotations

import datetime as dt
import os
import re
import subprocess
import sys
from pathlib import Path

import anthropic
import yaml

ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = ROOT / "_posts"
TOPICS_FILE = ROOT / "_data" / "topics.yml"
JST = dt.timezone(dt.timedelta(hours=9))
MODEL = os.environ.get("BLOG_MODEL") or "claude-sonnet-5"
MIN_BODY_CHARS = 2500

SYSTEM_PROMPT = """\
あなたは、Blender専門の3DCG制作スタジオ「Blenda Core（ブレンダ コア）」の公式ブログ記事を書くライターです。

## スタジオについて
- 株式会社Blenda Core。2026年設立、埼玉県越谷市。代表は星野昇平（Blender歴20年、ゲーム業界の背景モデラー歴10年、ゼネラリスト歴10年）。
- 対応領域: キャラクター制作、背景モデリング、リギング、VRM/VRMA、映像制作、Unity/UEコンテンツ、Web3D（glTF）、3D広告（裸眼3D）、エフェクト、アドオン/パイプライン構築、Blender講座・研修、AI生成モデルの最適化、デジタルツイン。
- Blenderを主軸にしつつ、必要に応じてPhotoshopやSubstanceなども使う。

## 書き方のルール
- 日本語。です・ます調。読者に語りかける、実務者らしい落ち着いたトーン。
- 本文は3000〜5000字程度。見出しは「## 」（h2）と「### 」（h3）を使う。h1は書かない（タイトルは別に指定する）。
- 冒頭に、読者の悩みと「この記事でわかること」を短く示す導入を置く。最後に「まとめ」の見出しで要点を整理する。
- 手順や設定は具体的に。Blenderのメニュー名・項目名は日本語UIと英語UIを併記すると親切（例: 「適用（Apply）」）。
- コードを載せるときは ```python のようにフェンス付きコードブロックにする。
- 表（Markdownテーブル）や箇条書きは、読みやすさが上がる場合だけ使う。

## 正確さのルール（最重要）
- 確信がない数値・バージョン番号・リリース日・価格・統計は書かない。バージョン依存の話は「バージョンによってUIの位置が異なる場合があります」のように書く。
- 架空の制作事例、架空のお客様の声、スタジオや代表の架空のエピソード（「以前担当した案件で〜」など）は絶対に書かない。
- 他社・他製品を貶めない。誇大表現（「絶対」「必ず売れる」など）を避ける。
- 外部サイトへのリンクは、公式サイトのトップ（https://www.blender.org/ など）のように確実に存在するものだけにする。

## 記事の締め
- 本文の最後（まとめの後）に、押し付けにならない一文で「Blenda Coreでは〇〇のご相談も承っています」のように自然に触れてよい（1〜2文まで）。

## 出力形式
次のタグだけを、この順番で出力してください。タグの外には何も書かないこと。
<title>記事タイトル（32文字前後、検索されやすい具体的な言葉を入れる）</title>
<slug>URL用の英小文字スラッグ（例: blender-bevel-modifier-guide）。英数字とハイフンのみ、5語程度</slug>
<description>検索結果に表示される説明文（80〜120文字）</description>
<tags>タグをカンマ区切りで3〜5個（例: Blender,モデリング,ハードサーフェス）</tags>
<body>
Markdown本文
</body>
"""


def log(msg: str) -> None:
    print(msg, file=sys.stderr)


def set_output(**kwargs: str) -> None:
    """GitHub Actions の step output に値を渡す（ローカル実行時は何もしない）。"""
    path = os.environ.get("GITHUB_OUTPUT")
    if not path:
        return
    with open(path, "a", encoding="utf-8") as f:
        for k, v in kwargs.items():
            f.write(f"{k}={v}\n")


def read_front_matter(text: str) -> dict:
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not m:
        return {}
    try:
        return yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return {}


def existing_posts() -> list[dict]:
    """公開済みの記事と、まだマージされていない下書きブランチ（blog/*）の記事を集める。"""
    posts: list[dict] = []
    for p in sorted(POSTS_DIR.glob("*.md")):
        fm = read_front_matter(p.read_text(encoding="utf-8"))
        fm["_file"] = p.name
        posts.append(fm)

    # レビュー待ちのプルリクエストに入っている記事も「使用済み」として扱い、テーマの重複を防ぐ
    try:
        branches = subprocess.run(
            ["git", "for-each-ref", "--format=%(refname)", "refs/remotes/origin/blog/"],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout.split()
        for ref in branches:
            files = subprocess.run(
                ["git", "ls-tree", "-r", "--name-only", ref, "_posts/"],
                cwd=ROOT, capture_output=True, text=True, check=True,
            ).stdout.split()
            known = {p["_file"] for p in posts}
            for f in files:
                name = Path(f).name
                if name in known:
                    continue
                text = subprocess.run(
                    ["git", "show", f"{ref}:{f}"], cwd=ROOT, capture_output=True, text=True, check=True
                ).stdout
                fm = read_front_matter(text)
                fm["_file"] = name
                posts.append(fm)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return posts


def pick_topic(posts: list[dict]) -> dict:
    topics = yaml.safe_load(TOPICS_FILE.read_text(encoding="utf-8")) or []
    used = {str(p.get("topic_id")) for p in posts if p.get("topic_id")}
    for t in topics:
        if str(t["id"]) not in used:
            return t
    # 候補を使い切ったら、既存記事と重ならないテーマをAIに考えてもらう
    return {"id": None, "category": None, "audience": None, "hint": None}


def build_user_prompt(topic: dict, posts: list[dict], today: dt.date) -> str:
    titles = [str(p.get("title")) for p in posts if p.get("title")]
    recent = "\n".join(f"- {t}" for t in titles[-80:]) or "（まだありません）"

    if topic["id"]:
        audience = "3DCG制作者・学習者" if topic.get("audience") == "creator" else "3DCG制作の発注や導入を検討している企業の担当者（3DCGの専門家ではない）"
        return (
            f"今日（{today:%Y年%-m月%-d日}）の記事を書いてください。\n\n"
            f"- テーマ: {topic['hint']}\n"
            f"- カテゴリ: {topic['category']}\n"
            f"- 想定読者: {audience}\n\n"
            f"既存の記事タイトル（内容が重複しないようにしてください）:\n{recent}"
        )
    return (
        f"今日（{today:%Y年%-m月%-d日}）の記事を書いてください。\n\n"
        "テーマは自由に選んでください。Blender・3DCG制作の技術記事か、3DCGを活用したい企業向けの記事のどちらか。"
        "既存記事と重複しないこと。\n"
        "追加で <category> タグに、次のいずれかのカテゴリ名を出力してください: "
        "Blender Tips / 3DCG活用ガイド / Web3D / ゲームエンジン連携 / パイプライン / VRM・アバター / 映像制作\n\n"
        f"既存の記事タイトル:\n{recent}"
    )


def extract(tag: str, text: str) -> str:
    m = re.search(rf"<{tag}>\s*(.*?)\s*</{tag}>", text, re.S)
    return m.group(1).strip() if m else ""


def yaml_str(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def main() -> int:
    now = dt.datetime.now(JST)
    today = now.date()
    POSTS_DIR.mkdir(exist_ok=True)

    posts = existing_posts()
    if any(str(p.get("_file", "")).startswith(today.isoformat()) for p in posts):
        log(f"{today} の記事はすでにあるため、スキップします。")
        return 0

    topic = pick_topic(posts)
    log(f"テーマ: {topic.get('id') or '（AIにおまかせ）'}")

    client = anthropic.Anthropic()
    text = ""
    for attempt in range(2):
        resp = client.messages.create(
            model=MODEL,
            max_tokens=12000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": build_user_prompt(topic, posts, today)}],
        )
        text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
        body = extract("body", text)
        if extract("title", text) and len(body) >= MIN_BODY_CHARS:
            break
        log(f"出力が短すぎるか形式が不正なため再生成します（{attempt + 1}回目, 本文{len(body)}字）")
    else:
        log("記事の生成に失敗しました。出力の先頭:\n" + text[:1500])
        return 1

    title = extract("title", text)
    description = extract("description", text)
    tags = [t.strip() for t in extract("tags", text).split(",") if t.strip()][:5]
    category = topic.get("category") or extract("category", text) or "Blender Tips"
    slug = re.sub(r"[^a-z0-9-]+", "-", extract("slug", text).lower()).strip("-")
    slug = slug or (topic.get("id") or f"post-{today:%Y%m%d}")
    slug = slug[:60].strip("-")

    path = POSTS_DIR / f"{today.isoformat()}-{slug}.md"
    front = [
        "---",
        f"title: {yaml_str(title)}",
        f"date: {now:%Y-%m-%d %H:%M:%S} +0900",
        f"description: {yaml_str(description)}",
        f"category_label: {yaml_str(category)}",
        "tags: [" + ", ".join(yaml_str(t) for t in tags) + "]",
    ]
    if topic.get("id"):
        front.append(f"topic_id: {topic['id']}")
    front.append(f"generated_by: {MODEL}")
    front.append("---")
    # {% raw %} で囲み、本文中の {{ }} などがJekyllのテンプレートとして解釈されないようにする
    content = "\n".join(front) + "\n\n{% raw %}\n" + body.strip() + "\n{% endraw %}\n"
    path.write_text(content, encoding="utf-8")

    log(f"作成しました: {path.relative_to(ROOT)}（{len(body)}字）")
    set_output(post_path=str(path.relative_to(ROOT)), title=title, date=today.isoformat())
    return 0


if __name__ == "__main__":
    sys.exit(main())
