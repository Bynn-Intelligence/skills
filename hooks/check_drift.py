#!/usr/bin/env python3
"""Check what the skills claim against the live Bynn surface.

Published integration docs drift silently. Two examples that were already wrong
before these skills existed: public/agents.md documents POST /v1/moderation/image
when the route is /moderation/infer, and the agemin SDK README points at
/v1/agemin/result when the route is /v1/agemin/check/reference/:reference_id.
Nothing failed; customers just hit a 404 before anyone noticed.

This job re-checks every endpoint path and model name the skills cite against the
live spec and catalogue. It is scheduled and non-blocking: upstream moving is real
news, but it is not a reason to fail an unrelated pull request.
"""
import json
import os
import re
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC_URL = "https://api.bynn.com/openapi.json"
MODELS_URL = "https://api.bynn.com/v1/moderation/models/all"
MCP_HEALTH_URL = "https://mcp.bynn.com/health"

# Real routes that are deliberately hidden from the published spec, plus hosts the
# Bynn spec does not describe. Cited on purpose; not drift.
KNOWN_OFF_SPEC = {
    "/moderation/infer_async",   # public, deliberately not in the published spec
    "/health",                   # mcp.bynn.com liveness route, not an API path
}
# Paths under these prefixes belong to another product or host and are not
# described by the Bynn spec.
OFF_SPEC_PREFIXES = ("/agemin/",)
OTHER_HOSTS = ("api.agemin.com", "mcp.bynn.com", "dashboard.bynn.com", "example.com")

problems = []
notes = []


def fetch(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": "bynn-skills-drift"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, resp.read()


def normalize(path):
    """Collapse every path parameter spelling to a single placeholder."""
    path = path.rstrip(".,:;)\"'`")           # prose punctuation, not part of the path
    path = re.sub(r"\{[^}]+\}", "{}", path)
    path = re.sub(r"<[^>]+>", "{}", path)
    path = re.sub(r":[A-Za-z_][A-Za-z0-9_]*", "{}", path)
    return path.rstrip("/") or "/"


def matches_spec(path, spec_paths, spec_patterns):
    """A cited path matches literally, or fills in a templated spec path.

    Skills cite concrete examples such as /moderation/models/ai-generated-image,
    which is the spec's /moderation/models/{api_name}. Comparing strings alone
    would report those as drift every single week.
    """
    if path in spec_paths:
        return True
    return any(pattern.fullmatch(path) for pattern in spec_patterns)


def skill_files():
    for dirpath, _dirs, files in os.walk(os.path.join(ROOT, "plugins")):
        for fn in files:
            if fn.endswith(".md"):
                yield os.path.join(dirpath, fn)


# ---------------------------------------------------------------- endpoints
try:
    status, body = fetch(SPEC_URL)
    spec = json.loads(body)
except Exception as exc:  # noqa: BLE001
    print(f"could not fetch {SPEC_URL}: {exc}", file=sys.stderr)
    sys.exit(1)

spec_paths = {normalize(p) for p in spec.get("paths", {})}
spec_patterns = [
    re.compile("".join("[^/]+" if seg == "{}" else re.escape(seg)
                       for seg in re.split(r"(\{\})", p)))
    for p in spec_paths if "{}" in p
]
print(f"live spec: {len(spec_paths)} paths")

cited = {}
url_re = re.compile(r"https://api\.bynn\.com/v1(/[A-Za-z0-9_{}<>:./-]*)")
verb_re = re.compile(r"\b(?:GET|POST|PATCH|PUT|DELETE)\s+(/v1)?(/[A-Za-z0-9_{}<>:./-]+)")

for path in skill_files():
    text = open(path, encoding="utf-8").read()
    rel = os.path.relpath(path, ROOT)
    for m in url_re.finditer(text):
        cited.setdefault(normalize(m.group(1)), set()).add(rel)
    for line in text.split("\n"):
        if any(h in line for h in OTHER_HOSTS):
            continue
        for m in verb_re.finditer(line):
            cited.setdefault(normalize(m.group(2)), set()).add(rel)

checked = 0
for path, sources in sorted(cited.items()):
    if path in ("/", "") or path in KNOWN_OFF_SPEC:
        continue
    if path.startswith(OFF_SPEC_PREFIXES):
        continue
    checked += 1
    if not matches_spec(path, spec_paths, spec_patterns):
        problems.append(
            f"endpoint no longer in the live spec: {path}  "
            f"(cited in {', '.join(sorted(sources))})"
        )
print(f"endpoints cited by skills: {checked} checked, {len(cited) - checked} skipped as off-spec or other-host")

# ------------------------------------------------------------------ models
try:
    status, body = fetch(MODELS_URL)
    payload = json.loads(body)
    # The catalogue is a list of categories, each holding its own models array.
    live_models = set()
    if isinstance(payload, list):
        for category in payload:
            if not isinstance(category, dict):
                continue
            for model in category.get("models", []) or []:
                if isinstance(model, dict) and model.get("api_name"):
                    live_models.add(model["api_name"])
    if not live_models:
        # Never skip quietly: an unreadable catalogue must look different from
        # a clean run, or the check silently stops covering model names.
        problems.append(
            f"could not read any api_name from {MODELS_URL}; the response shape "
            f"changed and model names are no longer being checked"
        )
except Exception as exc:  # noqa: BLE001
    problems.append(f"model catalogue unreachable at {MODELS_URL}: {exc}")
    live_models = set()

if live_models:
    print(f"live catalogue: {len(live_models)} models")
    # Only the explicit catalogue paragraphs, which are written in one fixed shape.
    cat_re = re.compile(r"\*\*(?:Image|Video|Text|Audio)\.\*\*(.*?)(?:\n\n|\Z)", re.S)
    cited_models = {}
    for path in skill_files():
        text = open(path, encoding="utf-8").read()
        rel = os.path.relpath(path, ROOT)
        for block in cat_re.findall(text):
            for name in re.findall(r"`([a-z0-9]+(?:-[a-z0-9]+)+)`", block):
                cited_models.setdefault(name, set()).add(rel)
    for name, sources in sorted(cited_models.items()):
        if name not in live_models:
            problems.append(
                f"model not in the live catalogue: {name}  "
                f"(listed in {', '.join(sorted(sources))})"
            )
    print(f"models cited by skills: {len(cited_models)} checked")

# --------------------------------------------------------------------- mcp
try:
    status, _ = fetch(MCP_HEALTH_URL, timeout=15)
    if status != 200:
        problems.append(f"MCP health returned {status}, expected 200")
    else:
        print("mcp.bynn.com/health: 200")
except Exception as exc:  # noqa: BLE001
    problems.append(f"MCP server unreachable at {MCP_HEALTH_URL}: {exc}")

# ------------------------------------------------------------------- urls
# Docs move and dashboards get reorganised. A skill that sends someone to a dead
# settings page is wrong in a way no spec check notices.
import glob

SKIP_URL_HOSTS = ("example.com",)
SKIP_URLS = {"https://mcp.bynn.com/mcp"}  # cited as the wrong URL, on purpose
# An MCP endpoint answering 401 to an unauthenticated probe is the server working
# correctly: it returns WWW-Authenticate pointing at its OAuth metadata. Only a
# 5xx or a connection failure means something is actually wrong.
AUTH_EXPECTED = ("https://mcp.bynn.com",)

urls = {}
for path in glob.glob(os.path.join(ROOT, "**", "*.md"), recursive=True):
    if "node_modules" in path:
        continue
    rel = os.path.relpath(path, ROOT)
    for m in re.finditer(r"https?://[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]+", open(path, encoding="utf-8").read()):
        u = m.group(0).rstrip(".,:;)\"'`>\\")
        if u in SKIP_URLS or any(h in u for h in SKIP_URL_HOSTS):
            continue
        # API endpoints are covered by the spec check above and mostly need auth.
        if u.startswith(("https://api.bynn.com/v1", "https://api.agemin.com/v1")):
            continue
        urls.setdefault(u, set()).add(rel)

dead = 0
for url in sorted(urls):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "bynn-skills-drift"}, method="HEAD")
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                code = resp.status
        except urllib.error.HTTPError as exc:
            if exc.code in (403, 405, 501):  # HEAD refused; retry as GET
                with urllib.request.urlopen(
                    urllib.request.Request(url, headers={"User-Agent": "bynn-skills-drift"}), timeout=20
                ) as resp:
                    code = resp.status
            else:
                code = exc.code
        if code in (401, 403) and url.rstrip("/") in [a.rstrip("/") for a in AUTH_EXPECTED]:
            continue
        if code >= 400:
            dead += 1
            problems.append(f"dead link {url} -> HTTP {code}  (in {', '.join(sorted(urls[url]))})")
    except Exception as exc:  # noqa: BLE001
        dead += 1
        problems.append(f"unreachable link {url}: {exc}  (in {', '.join(sorted(urls[url]))})")
print(f"links checked: {len(urls)}, dead: {dead}")

# ---------------------------------------------------------- pinned versions
# The Web SDK is documented with a version-pinned CDN URL. When a new version
# ships, that pin quietly becomes stale advice rather than a broken link.
PINNED = {
    "@bynn-intelligence/websdk": re.compile(r"static\.bynn\.com/sdk/js/([0-9]+\.[0-9]+\.[0-9]+)/"),
}
for package, pattern in PINNED.items():
    pinned = set()
    for path in glob.glob(os.path.join(ROOT, "plugins", "**", "*.md"), recursive=True):
        pinned.update(pattern.findall(open(path, encoding="utf-8").read()))
    if not pinned:
        continue
    try:
        _, body = fetch(f"https://registry.npmjs.org/{package}/latest")
        latest = json.loads(body).get("version")
    except Exception as exc:  # noqa: BLE001
        notes.append(f"could not read the latest {package} version ({exc})")
        continue
    for version in sorted(pinned):
        if version != latest:
            problems.append(
                f"{package} is pinned at {version} in the skills but npm latest is {latest}"
            )
    print(f"{package}: pinned {sorted(pinned)}, npm latest {latest}")

# ------------------------------------------------------------------ report
for n in notes:
    print(f"note: {n}")

if problems:
    print("\nDrift detected:\n", file=sys.stderr)
    for p in problems:
        print(f"  - {p}", file=sys.stderr)
    print(
        "\nThe skills describe a surface that has moved. Update them, "
        "then republish.",
        file=sys.stderr,
    )
    sys.exit(1)

print("\nNo drift: every cited endpoint and model still exists.")
