"""Fetch public homepage data at build time; the token never enters Hugo's data."""
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

QUERY = """
query($after: String) {
  user(login: "Dysta") {
    login name bio avatarUrl url location company websiteUrl createdAt
    followers { totalCount }
    repositories(first: 100, after: $after, privacy: PUBLIC, ownerAffiliations: OWNER) {
      totalCount
      nodes { stargazerCount isFork primaryLanguage { name color } }
      pageInfo { hasNextPage endCursor }
    }
    organizations(first: 8) { nodes { login name avatarUrl url } }
    pinnedItems(first: 6, types: REPOSITORY) {
      nodes { ... on Repository {
        name description url isPrivate stargazerCount forkCount
        primaryLanguage { name color }
      } }
    }
    contributionsCollection {
      commitContributionsByRepository(maxRepositories: 100) {
        repository { nameWithOwner url isPrivate owner { login } }
        contributions { totalCount }
      }
      pullRequestContributionsByRepository(maxRepositories: 100) {
        repository { nameWithOwner url isPrivate owner { login } }
        contributions { totalCount }
      }
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date weekday contributionCount contributionLevel } }
      }
    }
  }
}
"""


def validate_response(payload):
    if payload.get("errors"):
        details = []
        for error in payload["errors"]:
            path = ".".join(map(str, error.get("path", [])))
            details.append(f"{path}: {error['message']}" if path else error["message"])
        raise ValueError("GitHub GraphQL: " + "; ".join(details))
    if not (payload.get("data") or {}).get("user"):
        raise ValueError("GitHub did not return user Dysta; deployment stopped.")


def save_response(payload, destination):
    validate_response(payload)
    user = payload["data"]["user"]
    user["pinnedItems"]["nodes"] = [
        repo for repo in user["pinnedItems"]["nodes"] if repo and not repo["isPrivate"]
    ]
    if "nodes" in user["repositories"]:
        repositories = user["repositories"].pop("nodes")
        user["totalStars"] = sum(repo["stargazerCount"] for repo in repositories)
        languages = {}
        for repo in repositories:
            language = repo["primaryLanguage"]
            if language and not repo.get("isFork", False):
                entry = languages.setdefault(language["name"], {**language, "count": 0})
                entry["count"] += 1
        user["languages"] = sorted(languages.values(), key=lambda language: (-language["count"], language["name"]))[:8]
    external = {}
    collection = user["contributionsCollection"]
    for field, kind in (("commitContributionsByRepository", "commits"),
                        ("pullRequestContributionsByRepository", "pullRequests")):
        for contribution in collection.pop(field, []):
            repo = contribution["repository"]
            if repo["isPrivate"] or repo["owner"]["login"].lower() == user["login"].lower():
                continue
            entry = external.setdefault(repo["url"], {"name": repo["nameWithOwner"],
                "url": repo["url"], "commits": 0, "pullRequests": 0})
            entry[kind] += contribution["contributions"]["totalCount"]
    user["externalContributions"] = sorted(external.values(),
        key=lambda repo: (-(repo["commits"] + repo["pullRequests"]), repo["name"]))
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(user, ensure_ascii=False), encoding="utf-8")


def fetch_page(after=None):
    request = Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"after": after}}).encode(),
        headers={"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
                 "Content-Type": "application/json", "User-Agent": "dysta-homepage"},
    )
    with urlopen(request, timeout=30) as response:
        payload = json.load(response)
    validate_response(payload)
    return payload


if __name__ == "__main__":
    payload = fetch_page()
    repositories = payload["data"]["user"]["repositories"]
    while repositories["pageInfo"]["hasNextPage"]:
        page = fetch_page(repositories["pageInfo"]["endCursor"])["data"]["user"]["repositories"]
        repositories["nodes"].extend(page["nodes"])
        repositories["pageInfo"] = page["pageInfo"]
    save_response(payload, Path(__file__).resolve().parents[1] / "data/github.json")
