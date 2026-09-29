"""Sync blog posts from dobiapps.com (MDX) into blog/*.md. Run: python3 scripts/sync-blog.py"""
import json, re, sys, pathlib, yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
# Source: the dobiapps website monorepo, checked out next to this repo.
SRC = ROOT.parent / "dobiapps/apps/www/content/blog"
OUT = ROOT / "blog"
SITE = "https://dobiapps.com"
ATTR = re.compile(r'(\w+)="([^"]*)"')


def attrs(s):
    return dict(ATTR.findall(s))


def stat(m):
    a = attrs(m.group(1))
    src = f"[{a['source']}]({a['href']})" if a.get("href") else a.get("source", "")
    return f"> **{a.get('value','')}** — {a.get('label','')}\n>\n> *Source: {src}*"


def quote(m):
    a = attrs(m.group(1))
    body = " ".join(m.group(2).split())
    who = a.get("source", "")
    if a.get("cite"):
        who = f"[{who}]({a['cite']})"
    if a.get("context"):
        who += f", {a['context']}"
    return f"> “{body}”\n>\n> — {who}"


def convert(path):
    text = path.read_text()
    _, fm, body = text.split("---", 2)
    meta = yaml.safe_load(fm)
    slug = meta["slug"]
    url = f"{SITE}/blog/{slug}"

    body = re.sub(r"<Stat\b(.*?)/>", stat, body, flags=re.S)
    body = re.sub(r"<Quote\b(.*?)>(.*?)</Quote>", quote, body, flags=re.S)
    body = re.sub(r"<Faq\b.*?/>", "", body, flags=re.S)
    # Root-relative site links -> absolute dobiapps.com links
    body = re.sub(r"\]\((/[^)]*)\)", lambda m: f"]({SITE}{m.group(1)})", body)
    body = body.strip()

    date = str(meta.get("datePublished", ""))[:10]
    modified = str(meta.get("dateModified", ""))[:10]
    out = [
        "---",
        f"title: {json.dumps(meta['title'])}",
        f"description: {json.dumps(meta['description'])}",
        f"canonical_url: \"{url}\"",
        "---",
        "",
        f"# {meta['title']}",
        "",
        f"*By [The Dobi Apps Team]({SITE}/authors/editorial) · Published {date}"
        + (f" · Updated {modified}" if modified and modified != date else "")
        + f" · Originally published at [dobiapps.com]({url})*",
        "",
        f"> **{meta['description']}**",
        "",
    ]
    if meta.get("answerCapsule"):
        out += ["**In short:** " + " ".join(meta["answerCapsule"].split()), ""]
    if meta.get("heroImage"):
        out += [f"![{meta.get('heroAlt', meta['title'])}]({meta['heroImage']})", ""]
    out += [body, ""]

    if meta.get("faq"):
        out += ["## Frequently Asked Questions", ""]
        for q in meta["faq"]:
            out += [f"### {q['question']}", "", q["answer"], ""]

    if meta.get("citations"):
        out += ["## Sources", ""]
        out += [f"- [{c['name']}]({c['url']})" for c in meta["citations"]]
        out += [""]

    if meta.get("relatedPosts"):
        out += ["## Related articles", ""]
        for r in meta["relatedPosts"]:
            rp = SRC / f"{r}.mdx"
            title = yaml.safe_load(rp.read_text().split("---", 2)[1])["title"] if rp.exists() else r
            out += [f"- [{title}]({SITE}/blog/{r})"]
        out += [""]

    out += [
        "---",
        "",
        f"📖 Read the original article on the Dobi Apps blog: **[{meta['title']}]({url})**",
        "",
        f"Learn English with the Dobi Apps: [Audiobook]({SITE}/audiobook) · [Storybook]({SITE}/storybook) · [All articles](README.md) · [← Dobi Apps](../README.md)",
        "",
    ]
    (OUT / f"{slug}.md").write_text("\n".join(out))
    return slug, meta["title"]


for p in sorted(SRC.glob("*.mdx")):
    print(*convert(p), sep="\t")
