#!/usr/bin/env python3
"""Render materials/*.md into site/data/guides.json so the site can show them.

The markdown files stay the source of truth — they are pleasant to edit and they
version well — but nobody should have to read raw markdown on GitHub to use this.
This renders them to HTML that the site displays as ordinary pages.

Deliberately a small, specific renderer rather than a dependency: it handles the
subset these files actually use (headings, paragraphs, emphasis, inline code,
links, bullet and numbered lists, task lists, tables, blockquotes, rules) and
nothing else.
"""

from __future__ import annotations

import html
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
MATERIALS = ROOT / "materials"

# Order and presentation of the guides in the sidebar.
GUIDES = [
    ("timeline",               "guides/timeline.md",                 "📌", "What to do when"),
    ("how-to-get-picked",      "guides/how-to-get-picked.md",        "🎯", "How to get picked"),
    ("reading-a-program-page", "guides/reading-a-program-page.md",   "🔍", "Reading a program page"),
    ("personal-statement",     "templates/personal-statement.md",    "✍️", "Personal statement"),
    ("cv-skeleton",            "templates/cv-skeleton.md",           "📄", "CV skeleton"),
    ("recommendation-request", "templates/recommendation-request.md", "💌", "Asking for letters"),
    ("cold-email-pi",          "templates/cold-email-pi.md",         "📧", "Emailing a lab"),
    ("why-this-program",       "templates/why-this-program.md",      "🏫", "Why this program"),
    ("overview",               "README.md",                          "🗂️", "How to use all this"),
]

# Relative markdown links between the files become in-app page links.
SLUG_BY_PATH = {path: slug for slug, path, _icon, _title in GUIDES}


def inline(text: str) -> str:
    """Emphasis, code, and links inside a line of text."""
    out = []
    i = 0
    # Protect code spans first so their contents are never treated as markup.
    for part in re.split(r"(`[^`]+`)", text):
        if part.startswith("`") and part.endswith("`") and len(part) > 1:
            out.append(f"<code>{html.escape(part[1:-1])}</code>")
            continue

        esc = html.escape(part)
        esc = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", esc)
        esc = re.sub(r"(?<![*\w])\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", esc)

        def link(m):
            label, href = m.group(1), m.group(2)
            if href.endswith(".md") or ".md#" in href:
                target = href.split("#")[0].replace("../", "").lstrip("./")
                slug = SLUG_BY_PATH.get(target)
                if slug:
                    return f'<a href="#guide/{slug}" data-guide="{slug}">{label}</a>'
                return label  # a file we do not publish: drop the link, keep the words
            rel = ' target="_blank" rel="noopener noreferrer"' if href.startswith("http") else ""
            return f'<a href="{html.escape(href, quote=True)}"{rel}>{label}</a>'

        esc = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link, esc)
        out.append(esc)
    return "".join(out)


ITEM_RE = re.compile(r"^(\s*)([-*]|\d+\.)\s+")
BLOCK_START = ("#", ">", "|", "```")


def join_continuations(lines: list[str]) -> list[str]:
    """Fold soft-wrapped list-item continuations back into their item.

    These files wrap long bullets across lines with a hanging indent. Without
    this the indented remainder has no list marker, falls through to the
    paragraph branch, and gets emitted as a sibling <p> outside the list.
    """
    out: list[str] = []
    in_item = False

    for line in lines:
        stripped = line.strip()

        if ITEM_RE.match(line):
            out.append(line)
            in_item = True
            continue

        if in_item and stripped and line[:1] in (" ", "\t") \
                and not stripped.startswith(BLOCK_START) \
                and not re.fullmatch(r"-{3,}", stripped):
            out[-1] = out[-1].rstrip() + " " + stripped
            continue

        if not stripped or not line[:1].isspace():
            in_item = False
        out.append(line)

    return out


def render(md: str) -> str:
    lines = join_continuations(md.split("\n"))
    out: list[str] = []
    i = 0

    def close_lists(stack):
        while stack:
            out.append(f"</{stack.pop()}>")

    list_stack: list[str] = []

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # fenced code block — must come first, since its contents are literal
        # (the CV skeleton is one big pre-formatted block and its column
        # alignment is the whole point)
        if stripped.startswith("```"):
            close_lists(list_stack)
            i += 1
            buf = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1  # closing fence
            out.append(f"<pre><code>{html.escape(chr(10).join(buf))}</code></pre>")
            continue

        if not stripped:
            close_lists(list_stack)
            i += 1
            continue

        # horizontal rule
        if re.fullmatch(r"-{3,}|\*{3,}", stripped):
            close_lists(list_stack)
            out.append('<hr class="divider">')
            i += 1
            continue

        # heading
        m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if m:
            close_lists(list_stack)
            level = len(m.group(1))
            out.append(f"<h{level}>{inline(m.group(2))}</h{level}>")
            i += 1
            continue

        # table
        if stripped.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:|-]+\|$", lines[i + 1].strip()):
            close_lists(list_stack)
            header = [c.strip() for c in stripped.strip("|").split("|")]
            i += 2
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            head = "".join(f"<th>{inline(c)}</th>" for c in header)
            body = "".join(
                "<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in rows)
            out.append(f'<div class="doc-table"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>')
            continue

        # blockquote (consume the whole run)
        if stripped.startswith(">"):
            close_lists(list_stack)
            buf = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                buf.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            inner = "".join(f"<p>{inline(p)}</p>" for p in re.split(r"\n\s*\n", "\n".join(buf)) if p.strip())
            out.append(f"<blockquote>{inner}</blockquote>")
            continue

        # list item
        m = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", line)
        if m:
            indent, marker, body = len(m.group(1)), m.group(2), m.group(3)
            want = "ol" if marker.endswith(".") else "ul"
            depth = indent // 2 + 1

            while len(list_stack) > depth:
                out.append(f"</{list_stack.pop()}>")
            while len(list_stack) < depth:
                out.append(f"<{want}>")
                list_stack.append(want)
            if list_stack and list_stack[-1] != want:
                out.append(f"</{list_stack.pop()}>")
                out.append(f"<{want}>")
                list_stack.append(want)

            task = re.match(r"^\[([ xX])\]\s+(.*)$", body)
            if task:
                checked = task.group(1).lower() == "x"
                out.append(
                    f'<li class="task"><span class="box{" on" if checked else ""}"></span>'
                    f"<span>{inline(task.group(2))}</span></li>")
            else:
                out.append(f"<li>{inline(body)}</li>")
            i += 1
            continue

        # paragraph (join soft-wrapped lines)
        close_lists(list_stack)
        buf = [stripped]
        i += 1
        while i < len(lines):
            nxt = lines[i].strip()
            if (not nxt or nxt.startswith(("#", ">", "|", "- ", "* "))
                    or re.match(r"^\d+\.\s", nxt) or re.fullmatch(r"-{3,}", nxt)):
                break
            buf.append(nxt)
            i += 1
        out.append(f"<p>{inline(' '.join(buf))}</p>")

    close_lists(list_stack)
    return "\n".join(out)


def build() -> dict:
    guides = []
    for slug, rel, icon, title in GUIDES:
        path = (MATERIALS / rel) if rel != "README.md" else (MATERIALS / "README.md")
        if not path.is_file():
            print(f"  ! missing {path.relative_to(ROOT).as_posix()}")
            continue
        md = path.read_text(encoding="utf-8")

        # The file's own H1 becomes the page title, so drop it from the body.
        body_md = re.sub(r"^#\s+.*\n", "", md, count=1)
        guides.append({
            "slug": slug,
            "icon": icon,
            "title": title,
            "html": render(body_md),
            "source": rel,
        })
    return {"guides": guides}


def write() -> int:
    payload = build()
    out = ROOT / "site" / "data" / "guides.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    total = sum(len(g["html"]) for g in payload["guides"])
    print(f"  guides     : {len(payload['guides'])} pages, {total:,} chars -> site/data/guides.json")
    return len(payload["guides"])


if __name__ == "__main__":
    write()
