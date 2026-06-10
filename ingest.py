"""Ingestion: parse raw collected JSON (data_raw/) into cleaned per-document
text files in documents/.

Two source types:
  - r/Colby threads: data_raw/threads/<id>_post.json + <id>_comments.json (PullPush API shape)
  - RMP professors:  data_raw/rmp/<name>_<id>.json (RMP GraphQL response)

Output format (one .txt per document) keeps one unit per paragraph, with a
UNIT-TYPE prefix the chunker uses as a hard boundary:

  TITLE: ...
  SOURCE: <url>
  TYPE: reddit_thread | rmp_reviews
  DATE: YYYY-MM

  POST: ...
  COMMENT: ...
  REVIEW (CS231, 2021-05): ...
"""

import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path

RAW_DIR = Path("data_raw")
OUT_DIR = Path("documents")

# Comments shorter than this add nothing retrievable ("Same!", "thank you").
MIN_COMMENT_CHARS = 40

# Signatures of Reddit bots seen in the raw data (book bot, grammar bot, botrank).
BOT_BODY_PATTERNS = [
    r"\bi'?\s?a?m a (ro)?bot\b",
    r"beep\.? boop",
    r"botrank|botcrime|botsrights",
    r"^(bad|good) bot\b",
    r"this bot wants to find",
]
BOT_AUTHOR_PATTERN = re.compile(r"bot", re.IGNORECASE)


def clean_text(text: str) -> str:
    """Strip Reddit/RMP markup down to plain readable sentences."""
    if not text:
        return ""
    # PullPush bodies are HTML-escaped, sometimes twice (&amp;gt;).
    text = html.unescape(html.unescape(text))
    # Quoted parent comments duplicate content from elsewhere in the thread.
    text = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith(">"))
    # Markdown links -> keep the visible text, drop the URL.
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"https?://\S+", "", text)
    # Markdown emphasis/superscript/strikethrough markers and table/rule junk.
    text = re.sub(r"[*_~`#^]+", "", text)
    text = re.sub(r"-{3,}", " ", text)
    # Bullets and invisible characters (word joiner, zero-width space, etc.).
    text = re.sub(r"[•‣◦⁃⁠​‌‍﻿]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def is_bot_or_junk(author: str, body: str) -> bool:
    if body in ("[deleted]", "[removed]") or not body.strip():
        return True
    if author and BOT_AUTHOR_PATTERN.search(author) and author.lower() != "[deleted]":
        return True
    lowered = body.lower()
    return any(re.search(p, lowered) for p in BOT_BODY_PATTERNS)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def ingest_thread(post_path: Path) -> str:
    thread_id = post_path.name.replace("_post.json", "")
    post = load_json(post_path)["data"][0]
    comments = load_json(post_path.with_name(f"{thread_id}_comments.json"))["data"]

    created = datetime.fromtimestamp(post["created_utc"], tz=timezone.utc)
    lines = [
        f"TITLE: {clean_text(post['title'])}",
        f"SOURCE: https://www.reddit.com/r/Colby/comments/{thread_id}/",
        "TYPE: reddit_thread",
        f"DATE: {created:%Y-%m}",
        "",
    ]

    selftext = clean_text(post.get("selftext", ""))
    if selftext and selftext not in ("[deleted]", "[removed]"):
        lines.append(f"POST: {selftext}")
        lines.append("")

    kept = 0
    # Oldest first so the document reads like the thread did.
    for c in sorted(comments, key=lambda c: c.get("created_utc", 0)):
        raw_body = c.get("body", "")
        body = clean_text(raw_body)
        if is_bot_or_junk(c.get("author", ""), raw_body) or len(body) < MIN_COMMENT_CHARS:
            continue
        lines.append(f"COMMENT: {body}")
        lines.append("")
        kept += 1

    print(f"  {thread_id}: kept {kept}/{len(comments)} comments")
    return "\n".join(lines)


def ingest_professor(json_path: Path) -> str:
    node = load_json(json_path)["data"]["node"]
    name = f"{node['firstName']} {node['lastName']}".strip()
    rmp_id = json_path.stem.rsplit("_", 1)[-1]

    lines = [
        f"TITLE: Rate My Professors reviews of {name} ({node['department']}, Colby College)",
        f"SOURCE: https://www.ratemyprofessors.com/professor/{rmp_id}",
        "TYPE: rmp_reviews",
        f"DATE: {datetime.now():%Y-%m}",
        "",
        (
            f"SUMMARY: Professor {name} ({node['department']}) has an average rating of "
            f"{node['avgRating']}/5 across {node['numRatings']} Rate My Professors reviews, "
            f"with an average difficulty of {node['avgDifficulty']}/5."
        ),
        "",
    ]

    kept = 0
    for edge in node["ratings"]["edges"]:
        r = edge["node"]
        comment = clean_text(r.get("comment", ""))
        if len(comment) < MIN_COMMENT_CHARS:
            continue
        date = (r.get("date") or "")[:7]  # "2021-05-04 ..." -> "2021-05"
        course = r.get("class") or "unspecified course"
        extras = f" [Quality: {r['helpfulRating']}/5, Difficulty: {r['difficultyRating']}/5]"
        tags = clean_text((r.get("ratingTags") or "").replace("--", ", "))
        if tags:
            extras += f" [Tags: {tags}]"
        lines.append(f"REVIEW ({course}, {date}): {comment}{extras}")
        lines.append("")
        kept += 1

    print(f"  {name}: kept {kept}/{len(node['ratings']['edges'])} reviews")
    return "\n".join(lines)


def main():
    OUT_DIR.mkdir(exist_ok=True)
    for old in OUT_DIR.glob("*.txt"):
        old.unlink()

    print("Ingesting r/Colby threads:")
    for post_path in sorted((RAW_DIR / "threads").glob("*_post.json")):
        doc = ingest_thread(post_path)
        thread_id = post_path.name.replace("_post.json", "")
        (OUT_DIR / f"reddit_{thread_id}.txt").write_text(doc, encoding="utf-8")

    print("Ingesting RMP professor reviews:")
    for json_path in sorted((RAW_DIR / "rmp").glob("*.json")):
        doc = ingest_professor(json_path)
        (OUT_DIR / f"rmp_{json_path.stem}.txt").write_text(doc, encoding="utf-8")

    docs = list(OUT_DIR.glob("*.txt"))
    print(f"\nWrote {len(docs)} documents to {OUT_DIR}/")


if __name__ == "__main__":
    main()
