from __future__ import annotations

from datetime import datetime, timezone
from html import escape
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "assets" / "generated"
CONFIG_FILE = ROOT / "config.yml"


def load_config() -> dict:
    """Load JSON-formatted YAML (valid in YAML 1.2) from config.yml."""
    return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))


def github_get(url: str, params: dict | None = None) -> dict | list:
    """Generic helper for GitHub API requests."""
    query = f"?{urlencode(params)}" if params else ""
    req = Request(f"{url}{query}")
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    
    # Standard header for most endpoints
    req.add_header("Accept", "application/vnd.github+json")
    
    with urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_stats(username: str, config: dict) -> dict:
    defaults = config.get(
        "stats_defaults", {"commits": 0, "stars": 0, "prs": 0, "issues": 0, "repos": 0}
    )

    try:
        # 1. User Data (for total public repos)
        user_data = github_get(f"https://api.github.com/users/{username}")
        total_repos = user_data.get("public_repos", 0)

        # 2. Repository Data (for stars and open issues calculation)
        # Note: This grabs the first 100 repos. If you have >100, you might need pagination,
        # but this covers most use cases.
        repos_data = github_get(
            f"https://api.github.com/users/{username}/repos",
            {"per_page": 100, "sort": "updated"},
        )
        total_stars = sum(repo.get("stargazers_count", 0) for repo in repos_data)
        open_issues_count = sum(repo.get("open_issues_count", 0) for repo in repos_data)

        # 3. Search API for PRs and Issues
        # We use the search API to get accurate historical totals
        total_prs = github_get(
            "https://api.github.com/search/issues",
            {"q": f"author:{username} type:pr", "per_page": 1},
        ).get("total_count", 0)

        total_issues = github_get(
            "https://api.github.com/search/issues",
            {"q": f"author:{username} type:issue", "per_page": 1},
        ).get("total_count", 0)

        # 4. Search API for Commits (THE FIX)
        # The previous 'events' method only looked at the last 90 days.
        # This searches your entire history.
        commit_search_url = "https://api.github.com/search/commits"
        commit_params = {"q": f"author:{username}", "per_page": 1}
        
        # We construct this request manually because commit search 
        # historically required a specific preview header.
        query = f"?{urlencode(commit_params)}"
        req = Request(f"{commit_search_url}{query}")
        token = os.getenv("GITHUB_TOKEN", "").strip()
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        
        # This header is often required for the Commit Search API
        req.add_header("Accept", "application/vnd.github.cloak-preview")
        
        with urlopen(req, timeout=20) as resp:
            commits_data = json.loads(resp.read().decode("utf-8"))
            total_commits = commits_data.get("total_count", 0)

        print(f"DEBUG: Stats fetched -> Commits: {total_commits}, Stars: {total_stars}, PRs: {total_prs}")

        return {
            "commits": total_commits,
            "stars": total_stars,
            "prs": total_prs,
            "issues": max(open_issues_count, total_issues),
            "repos": total_repos,
        }
    except Exception as e:
        # Print the specific error so it appears in GitHub Actions logs
        print(f"::error::Failed to fetch GitHub stats: {e}")
        return defaults


def write_svg(name: str, body: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / name).write_text(body, encoding="utf-8")


def svg_header(profile: dict) -> str:
    name = escape(profile.get("name", "Developer"))
    tagline = escape(profile.get("tagline", "Building in public"))

    return f"""<svg width=\"850\" height=\"280\" viewBox=\"0 0 850 280\" xmlns=\"http://www.w3.org/2000/svg\" role=\"img\" aria-label=\"Galaxy Header\">
  <defs>
    <linearGradient id=\"bg\" x1=\"0\" y1=\"0\" x2=\"1\" y2=\"1\">
      <stop offset=\"0%\" stop-color=\"#080c14\"/>
      <stop offset=\"100%\" stop-color=\"#111b2e\"/>
    </linearGradient>
    <radialGradient id=\"core\" cx=\"50%\" cy=\"50%\" r=\"55%\">
      <stop offset=\"0%\" stop-color=\"#a78bfa\" stop-opacity=\"1\"/>
      <stop offset=\"40%\" stop-color=\"#00d4ff\" stop-opacity=\"0.7\"/>
      <stop offset=\"100%\" stop-color=\"#00d4ff\" stop-opacity=\"0\"/>
    </radialGradient>
  </defs>
  <rect width=\"850\" height=\"280\" fill=\"url(#bg)\"/>
  <g opacity=\"0.65\"> 
    <circle cx=\"110\" cy=\"40\" r=\"1.2\" fill=\"#f1f5f9\"/>
    <circle cx=\"760\" cy=\"70\" r=\"1.4\" fill=\"#f1f5f9\"/>
    <circle cx=\"690\" cy=\"220\" r=\"1.1\" fill=\"#f1f5f9\"/>
    <circle cx=\"200\" cy=\"230\" r=\"1.3\" fill=\"#f1f5f9\"/>
  </g>
  <g transform=\"translate(425 140)\">
    <ellipse rx=\"210\" ry=\"70\" fill=\"none\" stroke=\"#a78bfa\" stroke-opacity=\"0.35\" stroke-width=\"1.8\"/>
    <ellipse rx=\"160\" ry=\"52\" fill=\"none\" stroke=\"#00d4ff\" stroke-opacity=\"0.4\" stroke-width=\"1.6\">
      <animateTransform attributeName=\"transform\" type=\"rotate\" from=\"0\" to=\"360\" dur=\"40s\" repeatCount=\"indefinite\"/>
    </ellipse>
    <ellipse rx=\"112\" ry=\"34\" fill=\"none\" stroke=\"#ffb020\" stroke-opacity=\"0.35\" stroke-width=\"1.4\">
      <animateTransform attributeName=\"transform\" type=\"rotate\" from=\"360\" to=\"0\" dur=\"28s\" repeatCount=\"indefinite\"/>
    </ellipse>
    <circle r=\"44\" fill=\"url(#core)\">
      <animate attributeName=\"r\" values=\"42;46;42\" dur=\"4s\" repeatCount=\"indefinite\"/>
    </circle>
  </g>
  <text x=\"425\" y=\"145\" text-anchor=\"middle\" fill=\"#f1f5f9\" font-family=\"Segoe UI, Arial\" font-size=\"30\" font-weight=\"700\">{name}</text>
  <text x=\"425\" y=\"172\" text-anchor=\"middle\" fill=\"#94a3b8\" font-family=\"Segoe UI, Arial\" font-size=\"16\">{tagline}</text>
</svg>
"""


def svg_stats_card(stats: dict, config: dict) -> str:
    allowed_metrics = config.get("stats", {}).get(
        "metrics", ["commits", "stars", "prs", "issues", "repos"]
    )
    all_cards = {
        "commits": ("Commits", stats["commits"], "#00d4ff"),
        "stars": ("Stars", stats["stars"], "#a78bfa"),
        "prs": ("PRs", stats["prs"], "#ffb020"),
        "issues": ("Issues", stats["issues"], "#00d4ff"),
        "repos": ("Repos", stats["repos"], "#a78bfa"),
    }
    cards = [all_cards[key] for key in allowed_metrics if key in all_cards][:5]
    if not cards:
        cards = list(all_cards.values())

    parts = []
    x = 30
    for idx, (label, value, color) in enumerate(cards):
        width = 150 if idx < 4 else 130
        parts.append(
            f'<rect x="{x}" y="58" width="{width}" height="90" rx="10" fill="#1a2332"/>'
        )
        parts.append(
            f'<text x="{x+14}" y="88" fill="#94a3b8" font-size="13">{escape(label)}</text>'
        )
        parts.append(
            f'<text x="{x+14}" y="126" fill="{color}" font-size="30" font-weight="700">{value}</text>'
        )
        x += width + 15

    return "\n".join(
        [
            '<svg width="850" height="180" viewBox="0 0 850 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Mission Telemetry">',
            '  <rect width="850" height="180" rx="16" fill="#0f1623"/>',
            '  <text x="30" y="40" fill="#f1f5f9" font-family="Segoe UI, Arial" font-size="24" font-weight="700">Mission Telemetry</text>',
            '  <g font-family="Segoe UI, Arial">',
            *[f"    {item}" for item in parts],
            "  </g>",
            "</svg>",
            "",
        ]
    )


def svg_tech_stack(config: dict) -> str:
    lines = []
    y = 78
    for arm in config.get("galaxy_arms", []):
        color = arm.get("color", "#00d4ff")
        for item in arm.get("items", [])[:2]:
            lines.append((escape(str(item)), color, y))
            y += 30
    lines = lines[:6]

    bar_width = 380
    bars = []
    for label, color, y_pos in lines:
        bars.append(
            f'<text x="30" y="{y_pos}" fill="#94a3b8" font-size="13">{label}</text>'
        )
        bars.append(
            f'<rect x="130" y="{y_pos - 13}" width="600" height="12" rx="6" fill="#1a2332"/>'
        )
        bars.append(
            f'<rect x="130" y="{y_pos - 13}" width="{bar_width}" height="12" rx="6" fill="{color}"/>'
        )
        bar_width = max(180, bar_width - 35)

    return "\n".join(
        [
            '<svg width="850" height="250" viewBox="0 0 850 250" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Tech Stack">',
            '  <rect width="850" height="250" rx="16" fill="#0f1623"/>',
            '  <text x="30" y="40" fill="#f1f5f9" font-family="Segoe UI, Arial" font-size="24" font-weight="700">Language Telemetry + Focus Sectors</text>',
            '  <g font-family="Segoe UI, Arial">',
            *[f"    {item}" for item in bars],
            "  </g>",
            '  <g transform="translate(730 150)">',
            '    <polygon points="0,-55 50,-16 31,44 -31,44 -50,-16" fill="none" stroke="#a78bfa" stroke-opacity="0.7"/>',
            '    <polygon points="0,-38 34,-11 21,30 -21,30 -34,-11" fill="none" stroke="#00d4ff" stroke-opacity="0.8">',
            '      <animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="16s" repeatCount="indefinite"/>',
            "    </polygon>",
            '    <text x="0" y="4" text-anchor="middle" fill="#f1f5f9" font-family="Segoe UI, Arial" font-size="10">Focus</text>',
            "  </g>",
            "</svg>",
            "",
        ]
    )


def svg_projects(config: dict) -> str:
    projects = config.get("projects", [])[:4]
    points = [(95, 130), (280, 90), (470, 140), (665, 100)]

    nodes = []
    labels = []
    for idx, project in enumerate(projects):
        x_pos, y_pos = points[idx]
        repo = escape(project.get("repo", "project"))
        short_name = escape(repo.split("/")[-1])
        desc = escape(project.get("description", ""))[:48]
        color = ["#00d4ff", "#a78bfa", "#ffb020", "#00d4ff"][idx]
        nodes.append(f'<circle cx="{x_pos}" cy="{y_pos}" r="8" fill="{color}"/>')
        labels.append(
            f'<text x="{x_pos}" y="{y_pos + 26}" text-anchor="middle" fill="#cbd5e1" font-size="12">{short_name}</text>'
        )
        labels.append(
            f'<text x="{x_pos}" y="{y_pos + 42}" text-anchor="middle" fill="#64748b" font-size="10">{desc}</text>'
        )

    return "\n".join(
        [
            '<svg width="850" height="220" viewBox="0 0 850 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Projects Constellation">',
            '  <rect width="850" height="220" rx="16" fill="#0f1623"/>',
            '  <text x="30" y="40" fill="#f1f5f9" font-family="Segoe UI, Arial" font-size="24" font-weight="700">Featured Systems</text>',
            '  <g stroke="#334155" stroke-width="1.2" fill="none" opacity="0.8">',
            '    <path d="M95 130 L280 90 L470 140 L665 100"/>',
            "  </g>",
            '  <g font-family="Segoe UI, Arial">',
            *[f"    {item}" for item in nodes + labels],
            "  </g>",
            "</svg>",
            "",
        ]
    )


def main() -> None:
    # Ensure stdout/stderr are flushed immediately so logs appear in real-time
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)

    config = load_config()
    username = config["username"]
    profile = config.get("profile", {})

    stats = fetch_stats(username, config)

    write_svg("galaxy-header.svg", svg_header(profile))
    write_svg("stats-card.svg", svg_stats_card(stats, config))
    write_svg("tech-stack.svg", svg_tech_stack(config))
    write_svg("projects-constellation.svg", svg_projects(config))


if __name__ == "__main__":
    main()
