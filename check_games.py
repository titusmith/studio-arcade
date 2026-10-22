#!/usr/bin/env python3
"""
Studio Arcade checker
=====================

Checks every game folder inside games/ for the problems that break games in
the arcade, and (with --write) adds the games to the arcade's index.html.

Run it from the arcade folder (the one that contains index.html and games/):

    Mac:      python3 check_games.py            just check
              python3 check_games.py --write    check, then update the arcade
    Windows:  py check_games.py
              py check_games.py --write

Results:
    FAIL  the game will not work in the arcade until this is fixed
    WARN  probably a problem; read it and decide
    OK    passed

GitHub runs  python3 check_games.py --pr <base commit>  on every pull request.
That mode checks only the game folders the pull request adds or changes, and
fails if the pull request changes anything outside games/.

Only uses Python's standard library. Python 3.8 or newer.
"""

import json
import os
import re
import struct
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
GAMES_DIR = os.path.join(ROOT, "games")
LAUNCHER = os.path.join(ROOT, "index.html")

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
VALID_INPUT = {"keyboard", "mouse", "touch", "gamepad"}
VALID_DEVICES = {"desktop", "tablet", "phone"}
TEXT_EXT = {".html", ".htm", ".js", ".mjs", ".css", ".jsx", ".json"}
RETIRED = "sample-star-catcher"   # removed from the arcade; pull requests may not add it back
MAX_TOTAL_MB = 100          # per game folder
MAX_FILE_MB = 100           # GitHub rejects any single file over 100 MB
WARN_FILE_MB = 50           # GitHub warns about files over 50 MB
MAX_THUMB_KB = 1024

# Patterns that mean "this game loads something from the internet".
EXTERNAL_PATTERNS = [
    (re.compile(r"""<(?:script|link|img|audio|video|source|iframe)\b[^>]*?\b(?:src|href)\s*=\s*["'](?:https?:)?//""", re.I), "loads a file from the internet"),
    (re.compile(r"""url\(\s*["']?(?:https?:)?//""", re.I), "CSS url() points to the internet"),
    (re.compile(r"""@import\s+(?:url\()?\s*["']https?://""", re.I), "CSS @import from the internet"),
    (re.compile(r"""\bimport\s[^;'"]*?from\s*["']https?://"""), "JavaScript import from the internet"),
    (re.compile(r"""\bimport\(\s*["']https?://"""), "JavaScript import from the internet"),
    (re.compile(r"""\bfetch\(\s*[`"']https?://"""), "fetch() call to the internet"),
    (re.compile(r"""new\s+(?:WebSocket|EventSource)\(\s*[`"']"""), "live network connection"),
]
CLAUDE_ONLY = [
    (re.compile(r"\bwindow\.claude\b"), "window.claude only works on claude.ai (live AI calls can't run offline)"),
    (re.compile(r"\bwindow\.storage\b"), "window.storage only works on claude.ai; use localStorage for saves"),
]
ROOT_PATH = re.compile(r"""<(?:script|link|img|audio|video|source)\b[^>]*?\b(?:src|href)\s*=\s*["']/(?!/)([^"']*)["']""", re.I)
LOCAL_REF = re.compile(r"""<(?:script|link|img|audio|video|source)\b[^>]*?\b(?:src|href)\s*=\s*["']([^"'#?]+)""", re.I)
CSS_LOCAL_REF = re.compile(r"""url\(\s*["']?([^"')#?]+)""", re.I)
ESCAPE_KEY = re.compile(r"""(?:key\s*===?\s*["']Esc(?:ape)?["']|code\s*===?\s*["']Escape["']|keyCode\s*===?\s*27\b|which\s*===?\s*27\b|ESCAPE\b)""")
POPUPS = re.compile(r"""(?<![\w.])(?:window\.)?(?:alert|confirm|prompt)\s*\(|window\.open\s*\(""")
LIBRARY_NAME = re.compile(r"(\.min\.js$|^lib/|/lib/|three|phaser|p5|react|tone|howler|pixi|matter|gsap|babel|tailwind|UnityLoader|\.loader\.js$|\.framework\.js$)", re.I)

COLOR = sys.stdout.isatty() and os.name != "nt"
def paint(text, code):
    return f"\033[{code}m{text}\033[0m" if COLOR else text


class Report:
    def __init__(self, slug):
        self.slug = slug
        self.fails, self.warns, self.oks = [], [], []
        self.meta = None
        self.has_thumb = False

    def fail(self, msg): self.fails.append(msg)
    def warn(self, msg): self.warns.append(msg)
    def ok(self, msg): self.oks.append(msg)


def exact_exists(base, rel):
    """True only if every part of rel exists with exactly this capitalization
    (Mac and Windows ignore case, the iPad does not)."""
    cur = base
    for part in [p for p in rel.replace("\\", "/").split("/") if p not in ("", ".")]:
        if part == "..":
            cur = os.path.dirname(cur)
            continue
        try:
            names = os.listdir(cur)
        except OSError:
            return False
        if part not in names:
            return False
        cur = os.path.join(cur, part)
    return True


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    if len(head) < 24 or head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", head[16:24])


def walk_files(folder):
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and d not in ("node_modules", "__MACOSX")]
        for name in filenames:
            if not name.startswith("."):
                yield os.path.join(dirpath, name)


def line_of(text, index):
    return text.count("\n", 0, index) + 1


def snippet(text, index, width=70):
    start = text.rfind("\n", 0, index) + 1
    end = text.find("\n", index)
    end = len(text) if end == -1 else end
    line = text[start:end].strip()
    if len(line) > width:
        offset = max(0, index - start - 20)
        line = ("..." if offset else "") + line[offset:offset + width] + "..."
    return line


def check_game(folder, slug):
    r = Report(slug)
    names = set(os.listdir(folder))

    # Folder name
    if SLUG_RE.match(slug):
        r.ok("folder name")
    else:
        suggestion = re.sub(r"[^a-z0-9]+", "-", slug.lower()).strip("-")
        r.fail(f'folder name "{slug}" must be lowercase letters, numbers and hyphens only (try "{suggestion}")')

    # index.html
    if "index.html" in names:
        r.ok("index.html at the top")
    else:
        wrong_case = [n for n in names if n.lower() == "index.html"]
        nested = []
        for dirpath, _, filenames in os.walk(folder):
            if dirpath != folder and "index.html" in filenames:
                nested.append(os.path.relpath(os.path.join(dirpath, "index.html"), folder))
        jsx = [n for n in names if n.lower().endswith((".jsx", ".tsx"))]
        if wrong_case:
            r.fail(f'start page is named "{wrong_case[0]}"; rename it to "index.html" (all lowercase)')
        elif nested:
            r.fail(f'index.html is inside a subfolder ({nested[0].replace(os.sep, "/")}); move that folder\'s contents up to the top')
        elif jsx:
            r.fail(f'found {jsx[0]} but no index.html. A React artifact can\'t run by itself: use the "Built with Claude" prompt in the guide')
        else:
            others = [n for n in names if n.lower().endswith((".html", ".htm"))]
            hint = f' (found {others[0]}; rename it to index.html)' if others else ""
            r.fail("no index.html" + hint)

    # thumbnail.png
    if "thumbnail.png" in names:
        path = os.path.join(folder, "thumbnail.png")
        size = png_size(path)
        kb = os.path.getsize(path) / 1024
        if size is None:
            r.fail("thumbnail.png is not a real PNG file (was it renamed from .jpg?); export it again as PNG")
        else:
            w, h = size
            r.has_thumb = True
            if (w, h) == (1280, 720):
                r.ok("thumbnail.png is 1280x720")
            elif abs(w / h - 16 / 9) < 0.02:
                r.warn(f"thumbnail.png is {w}x{h}; it's 16:9, but 1280x720 is the standard size")
            else:
                r.warn(f"thumbnail.png is {w}x{h}, not 16:9; it will be cropped on the card. Use 1280x720")
        if kb > MAX_THUMB_KB:
            r.warn(f"thumbnail.png is {kb:.0f} KB; keep it under 1 MB")
    else:
        wrong = [n for n in names if n.lower().startswith("thumbnail")]
        if wrong:
            r.fail(f'thumbnail is named "{wrong[0]}"; it must be exactly "thumbnail.png" (a PNG, all lowercase)')
        else:
            r.warn("no thumbnail.png; the arcade will show a placeholder")

    # meta.json
    if "meta.json" in names:
        try:
            with open(os.path.join(folder, "meta.json"), encoding="utf-8-sig") as f:
                meta = json.load(f)
        except json.JSONDecodeError as e:
            r.fail(f"meta.json has a typo on line {e.lineno}: {e.msg} (check quotes and commas)")
            meta = None
        except UnicodeDecodeError:
            r.fail("meta.json isn't plain text; save it from a plain-text editor")
            meta = None
        if isinstance(meta, dict):
            problems = 0
            for key in ("title", "student", "instructions"):
                if not isinstance(meta.get(key), str) or not meta.get(key).strip():
                    r.fail(f'meta.json is missing "{key}"')
                    problems += 1
            for key, valid in (("input", VALID_INPUT), ("devices", VALID_DEVICES)):
                val = meta.get(key)
                if val is None:
                    r.warn(f'meta.json has no "{key}" list')
                    problems += 1
                elif not isinstance(val, list) or not val or any(v not in valid for v in val):
                    r.fail(f'meta.json "{key}" must be a list using only: ' + ", ".join(f'"{v}"' for v in sorted(valid)))
                    problems += 1
            designed = meta.get("designedFor")
            if designed is not None:
                if designed not in VALID_DEVICES:
                    r.fail('meta.json "designedFor" must be one of: "desktop", "tablet", "phone" (just one, in quotes)')
                    problems += 1
                elif isinstance(meta.get("devices"), list) and designed not in meta["devices"]:
                    r.warn(f'"designedFor" is "{designed}" but "devices" doesn\'t include it, so the game won\'t show there')
            orient = meta.get("orientation")
            if orient is not None and orient not in ("landscape", "portrait"):
                r.fail('meta.json "orientation" must be "landscape" or "portrait"')
                problems += 1
            if isinstance(meta.get("title"), str) and len(meta["title"]) > 30:
                r.warn(f'title is {len(meta["title"])} characters; it may be cut off (30 max)')
            if not problems:
                r.ok("meta.json")
            r.meta = meta
        elif meta is not None:
            r.fail("meta.json must be one { ... } block like the template")
    else:
        wrong = [n for n in names if n.lower().startswith("meta")]
        r.fail(f'meta.json is named "{wrong[0]}"; rename it to "meta.json"' if wrong else "no meta.json")

    # Scan code
    total_bytes = 0
    external, claude_only, rootpaths, missing, escape, popups = [], [], [], [], [], []
    unity_compressed = False
    godot_threads = False
    for path in walk_files(folder):
        size_bytes = os.path.getsize(path)
        total_bytes += size_bytes
        rel = os.path.relpath(path, folder).replace(os.sep, "/")
        file_mb = size_bytes / (1024 * 1024)
        if file_mb > MAX_FILE_MB:
            r.fail(f"{rel} is {file_mb:.0f} MB; GitHub rejects files over {MAX_FILE_MB} MB. Compress it or split it up")
        elif file_mb > WARN_FILE_MB:
            r.warn(f"{rel} is {file_mb:.0f} MB; try to keep files under {WARN_FILE_MB} MB")
        ext = os.path.splitext(path)[1].lower()
        if rel.startswith("Build/") and ext in (".gz", ".br"):
            unity_compressed = True
        if ext not in TEXT_EXT or os.path.getsize(path) > 15 * 1024 * 1024:
            continue
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                text = f.read()
        except OSError:
            continue
        is_library = bool(LIBRARY_NAME.search(rel))
        if ext in (".html", ".htm") and re.search(r"GODOT_THREADS_ENABLED\s*=\s*true", text):
            godot_threads = True
        if not is_library:
            for rx, why in EXTERNAL_PATTERNS:
                for m in rx.finditer(text):
                    external.append(f"{rel} line {line_of(text, m.start())}: {why}\n           {snippet(text, m.start())}")
            for rx, why in CLAUDE_ONLY:
                m = rx.search(text)
                if m:
                    claude_only.append(f"{rel} line {line_of(text, m.start())}: {why}")
            m = ESCAPE_KEY.search(text)
            if m:
                escape.append(f"{rel} line {line_of(text, m.start())}")
            m = POPUPS.search(text)
            if m:
                popups.append(f"{rel} line {line_of(text, m.start())}: {snippet(text, m.start(), 50)}")
        if ext in (".html", ".htm"):
            for m in ROOT_PATH.finditer(text):
                rootpaths.append(f"{rel} line {line_of(text, m.start())}: \"/{m.group(1)}\" should be \"{m.group(1)}\"")
            base = os.path.dirname(path)
            for m in LOCAL_REF.finditer(text):
                ref = m.group(1).strip()
                if re.match(r"^(?:[a-z]+:|//|/|\$|\{)", ref, re.I) or "${" in ref or "{{" in ref:
                    continue
                if not exact_exists(base, ref):
                    missing.append(f"{rel} line {line_of(text, m.start())}: \"{ref}\"")
        if ext == ".css":
            base = os.path.dirname(path)
            for m in CSS_LOCAL_REF.finditer(text):
                ref = m.group(1).strip()
                if re.match(r"^(?:[a-z]+:|//|/)", ref, re.I):
                    continue
                if not exact_exists(base, ref):
                    missing.append(f"{rel} line {line_of(text, m.start())}: \"{ref}\"")

    def listed(items, limit=5):
        shown = "\n         - ".join(items[:limit])
        more = f"\n         ...and {len(items) - limit} more" if len(items) > limit else ""
        return "\n         - " + shown + more

    if external:
        r.fail("loads files from the internet, which fails offline:" + listed(external))
    else:
        r.ok("no internet links")
    if claude_only:
        r.fail("uses claude.ai-only features:" + listed(claude_only))
    if rootpaths:
        r.fail("paths start with / and will break inside the arcade:" + listed(rootpaths))
    if missing:
        r.fail("links to files that don't exist (check spelling and capitalization; the iPad is case-sensitive):" + listed(missing))
    elif not rootpaths:
        r.ok("all linked files found")
    if unity_compressed:
        r.fail("Unity build is compressed (.gz/.br files in Build/). Set Compression Format to Disabled and build again")
    if godot_threads:
        r.fail("Godot export has Thread Support on. Untick Thread Support and export again")
    if escape:
        r.warn("the game seems to use the Escape key, which the arcade uses to exit:" + listed(escape, 3))
    if popups:
        r.warn("pop-ups (alert/confirm/prompt/window.open) can interrupt the kiosk:" + listed(popups, 3))
    mb = total_bytes / (1024 * 1024)
    if mb > MAX_TOTAL_MB:
        r.warn(f"folder is {mb:.0f} MB; keep it under {MAX_TOTAL_MB} MB")
    for junk in ("node_modules", "src", "Assets", "ProjectSettings", ".godot"):
        if junk in names and os.path.isdir(os.path.join(folder, junk)):
            r.warn(f'"{junk}/" looks like project source; submit only the exported game')
    return r


def js_string(s):
    return json.dumps(s, ensure_ascii=False)


def build_games_block(reports):
    lines = ["const GAMES = ["]
    entries = []
    for r in reports:
        m = r.meta
        parts = [
            f"    id: {js_string(r.slug)}",
            f"    title: {js_string(m['title'])}",
            f"    student: {js_string(m['student'])}",
            f"    instructions: {js_string(m['instructions'])}",
            f"    path: {js_string('games/' + r.slug + '/index.html')}",
        ]
        if r.has_thumb:
            parts.append(f"    thumbnail: {js_string('games/' + r.slug + '/thumbnail.png')}")
        if isinstance(m.get("tag"), str) and m["tag"].strip():
            parts.append(f"    tag: {js_string(m['tag'].strip())}")
        for key in ("input", "devices"):
            if isinstance(m.get(key), list) and m[key]:
                parts.append(f"    {key}: {json.dumps(m[key])}")
        if m.get("designedFor") in VALID_DEVICES:
            parts.append(f"    designedFor: {js_string(m['designedFor'])}")
        if m.get("orientation") in ("landscape", "portrait"):
            parts.append(f"    orientation: {js_string(m['orientation'])}")
        entries.append("  {\n" + ",\n".join(parts) + "\n  }")
    lines.append(",\n".join(entries))
    lines.append("];")
    return "\n".join(lines)


def write_launcher(reports):
    with open(LAUNCHER, encoding="utf-8") as f:
        html = f.read()
    start, end = "// GAMES:START", "// GAMES:END"
    if start not in html or end not in html:
        print(paint("Can't update index.html: the // GAMES:START and // GAMES:END lines are missing.", "31"))
        return False
    a = html.index(start) + len(start)
    b = html.index(end)
    new_html = html[:a] + "\n// Written by check_games.py. Run it again after adding or changing games.\n" + build_games_block(reports) + "\n" + html[b:]
    with open(os.path.join(ROOT, "index.backup.html"), "w", encoding="utf-8") as f:
        f.write(html)
    with open(LAUNCHER, "w", encoding="utf-8", newline="\n") as f:
        f.write(new_html)
    return True


def changed_in_pr(base):
    """Files a pull request changes, relative to its base commit."""
    out = subprocess.run(["git", "diff", "--name-only", "--no-renames", f"{base}...HEAD"],
                         cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return [line for line in out.splitlines() if line.strip()]


def main():
    write = "--write" in sys.argv
    pr_base = None
    if "--pr" in sys.argv:
        i = sys.argv.index("--pr")
        pr_base = sys.argv[i + 1] if i + 1 < len(sys.argv) else None
        if not pr_base:
            print("--pr needs the base commit")
            return 2
    if not os.path.isdir(GAMES_DIR):
        print("No games/ folder next to this script. Run it from the arcade folder.")
        return 2

    outside = []
    if pr_base:
        changed = changed_in_pr(pr_base)
        outside = [p for p in changed if not p.startswith("games/") or p.count("/") < 2]
        slugs = sorted({p.split("/")[1] for p in changed if p.startswith("games/") and p.count("/") >= 2
                        and os.path.isdir(os.path.join(GAMES_DIR, p.split("/")[1]))})
        if outside:
            print(paint("FAIL  this pull request changes files outside games/", "31;1"))
            print("   x  A submission should only add your own folder inside games/. Undo changes to:")
            for p in outside[:10]:
                print(f"         - {p}")
            print("      To undo one, run:  git checkout main -- <file>   then commit and push again.")
            print("      (If you ran check_games.py --write, index.html changed: undo it the same way.)\n")
        if RETIRED in slugs:
            print(paint(f"FAIL  this pull request adds back games/{RETIRED}/", "31;1"))
            print("   x  The sample game was removed from the arcade on purpose. Delete it from your branch:")
            print(f"         git rm -r games/{RETIRED}   then commit and push again.\n")
            outside.append(f"games/{RETIRED}/")
            slugs = [s for s in slugs if s != RETIRED]
        if len(slugs) > 1:
            print(paint(f"FAIL  this pull request changes {len(slugs)} game folders: " + ", ".join(slugs), "31;1"))
            print("   x  A pull request may only add or change ONE game folder: your own.")
            print("      Undo changes to the other folders:  git checkout main -- games/<folder>")
            print("      (for a folder that isn't on main at all:  git rm -r games/<folder>)  then commit and push.\n")
            outside.append("more than one game folder")
        if not slugs:
            print("This pull request doesn't add or change a game folder inside games/.")
            return 1 if outside else 0
    else:
        slugs = sorted(d for d in os.listdir(GAMES_DIR)
                       if os.path.isdir(os.path.join(GAMES_DIR, d)) and not d.startswith((".", "_")) and d != "__MACOSX")
        if RETIRED in slugs:
            print(paint(f"SKIP  games/{RETIRED}/ is the retired sample game; it is never added to the arcade.", "33;1"))
            print(f"      Delete the folder to clear this message:  git rm -r games/{RETIRED}\n")
            slugs.remove(RETIRED)
    if not slugs:
        print("games/ is empty. Put your game folder inside games/ and run this again.")
        return 2

    print(f"\nChecking {len(slugs)} game folder(s) in games/\n")
    reports = [check_game(os.path.join(GAMES_DIR, s), s) for s in slugs]

    for r in reports:
        status = paint("FAIL", "31;1") if r.fails else (paint("WARN", "33;1") if r.warns else paint("OK  ", "32;1"))
        title = f' ({r.meta["title"]})' if isinstance(r.meta, dict) and isinstance(r.meta.get("title"), str) else ""
        print(f"{status}  {r.slug}{title}")
        for msg in r.fails:
            print(f"   {paint('x', '31')}  {msg}")
        for msg in r.warns:
            print(f"   {paint('!', '33')}  {msg}")
        if not r.fails and not r.warns:
            print(f"   {paint('+', '32')}  " + ", ".join(r.oks))
        print()

    failing = [r for r in reports if r.fails]
    passing = [r for r in reports if not r.fails]
    print(f"Summary: {len(passing)} ready, {len(failing)} need fixes.")

    if write:
        ready = [r for r in passing if isinstance(r.meta, dict)]
        if not ready:
            print("Nothing added to the arcade: no game passed all checks.")
            return 1
        if write_launcher(ready):
            print(paint(f"\nUpdated index.html with {len(ready)} game(s)", "32;1") + " (old version saved as index.backup.html).")
            if failing:
                print("Left out until fixed: " + ", ".join(r.slug for r in failing))
            print("\nNext: start the server and open the arcade:")
            cmd = "py" if os.name == "nt" else "python3"
            print(f"   {cmd} -m http.server 8080")
            print("   then go to http://localhost:8080 in Chrome")
    elif pr_base:
        if failing or outside:
            print("\nFix the FAIL items above, then commit and push again. This check reruns automatically.")
        else:
            print("\nAll checks passed. Your instructor will review and merge your pull request.")
    elif passing:
        cmd = "py" if os.name == "nt" else "python3"
        print(f"Run  {cmd} check_games.py --write  to add the ready games to the arcade.")
    return 1 if (failing or outside) else 0


if __name__ == "__main__":
    sys.exit(main())
