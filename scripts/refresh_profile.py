import json
from datetime import datetime, timezone
import os
import pathlib
import urllib.request
import urllib.error

ROOT = pathlib.Path(__file__).resolve().parents[1]
OWNER = "indrajithbandara"
PROJECTS = ["Privacy-Lock-App", "indrajithbandara.github.io"]

def api(path):
    request = urllib.request.Request(
        "https://api.github.com/" + path,
        headers={"Authorization": "Bearer " + os.environ["GH_TOKEN"],
                 "Accept": "application/vnd.github+json",
                 "X-GitHub-Api-Version": "2022-11-28",
                 "User-Agent": "profile-terminal-refresh"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)

def main():
    profile = api("users/" + OWNER)
    lines = ["| Repository | Open issues & PRs | Stars | Last push (UTC) |", "| --- | ---: | ---: | --- |"]
    activity = []
    health = ["| Repository | Latest published release | Latest commit check |", "| --- | --- | --- |"]
    for name in PROJECTS:
        try:
            repo = api("repos/" + OWNER + "/" + name)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                print(f"Skipping unavailable repository: {name}")
                continue
            raise
        if repo.get("private") or repo.get("visibility") != "public":
            continue
        lines.append(f"| [{name}](https://github.com/{OWNER}/{name}) | {repo['open_issues_count']} | {repo['stargazers_count']} | {repo['pushed_at'][:10]} |")
        base = "repos/" + OWNER + "/" + name
        commits = api(base + "/commits?per_page=1")
        if commits:
            commit = commits[0]
            sha = commit["sha"]
            activity.append(f"- [{name} / {sha[:7]}]({commit['html_url']}) — {commit['commit']['committer']['date'][:10]}")
            checks = api(base + "/commits/" + sha + "/check-runs?per_page=100")
            runs = checks.get("check_runs", [])
            check = "No checks reported" if not runs else ("Pending" if any(x["status"] != "completed" for x in runs) else ("All reported checks passed" if all(x.get("conclusion") == "success" for x in runs) else "See check results"))
        else:
            check = "No commits reported"
        try:
            release = api(base + "/releases/latest")
            release_label = "Published release available"
        except urllib.error.HTTPError as exc:
            if exc.code != 404:
                raise
            release_label = "No latest stable release reported"
        health.append(f"| [{name}](https://github.com/{OWNER}/{name}) | [{release_label}](https://github.com/{OWNER}/{name}/releases) | {check} |")
    created = profile["created_at"][:10]
    block = "\n".join(["<!-- metrics:start -->", "", f"Public repositories: **{profile['public_repos']}** · Followers: **{profile['followers']}**", "", *lines, "", f"Account created: **{created}**", "", "### Latest public engineering activity", "", *activity, "", "### Project health monitor", "", *health, "", "Check results are not a security or production-readiness guarantee.", "", "Source: GitHub API. Last push is activity, not a release or security certification.", "", "<!-- metrics:end -->"])
    path = ROOT / "README.md"
    original = path.read_text(encoding="utf-8")
    start, end = "<!-- metrics:start -->", "<!-- metrics:end -->"
    if original.count(start) != 1 or original.count(end) != 1 or original.index(start) > original.index(end):
        raise ValueError("Expected exactly one ordered metrics block")
    updated = original[:original.index(start)] + block + original[original.index(end)+len(end):]
    if updated != original:
        path.write_text(updated, encoding="utf-8")

if __name__ == "__main__":
    main()
