#!/usr/bin/env python3
"""
Update README.md with the latest posts from passo.uno RSS feed and GitHub activity.
"""

import feedparser
import re
import requests
import os
from datetime import datetime, timezone

RSS_FEED_URL = "https://rly0nheart.com/index.xml"
README_PATH = "README.md"
MAX_POSTS = 5
MAX_ACTIVITY = 5
GITHUB_USERNAME = "rly0nheart"
GITHUB_TOKEN = os.getenv("GH_TOKEN")  # Optional, improves rate limits
EXCLUDED_REPOS = ["rly0nheart"]  # Repos to exclude from activity feed

# Markers to identify where to insert content
POSTS_START_MARKER = "<!-- BLOG-POSTS:START -->"
POSTS_END_MARKER = "<!-- BLOG-POSTS:END -->"
ACTIVITY_START_MARKER = "<!-- GITHUB-ACTIVITY:START -->"
ACTIVITY_END_MARKER = "<!-- GITHUB-ACTIVITY:END -->"


def fetch_latest_posts(feed_url, max_posts):
    """Fetch the latest posts from the RSS feed."""
    feed = feedparser.parse(feed_url)

    if feed.bozo:
        print(f"Warning: Feed parsing encountered issues: {feed.bozo_exception}")

    posts = []
    for entry in feed.entries[:max_posts]:
        title = entry.get("title", "Untitled")
        link = entry.get("link", "")
        pub_date = entry.get("published", "")

        # Parse and format the date
        try:
            date_obj = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %z")
            formatted_date = date_obj.strftime("%B %d, %Y")
        except (ValueError, TypeError):
            formatted_date = pub_date

        posts.append({
            "title": title,
            "link": link,
            "date": formatted_date
        })

    return posts


def fetch_github_activity(username, max_items):
    """Fetch recent commits and releases from non-fork repos."""
    try:
        # Prepare headers with token if available
        headers = {}
        if GITHUB_TOKEN:
            headers['Authorization'] = f'token {GITHUB_TOKEN}'
            print("Using authenticated GitHub API requests")

        # Get user's repos (non-fork), sorted by most recently updated
        repos_url = f"https://api.github.com/users/{username}/repos?per_page=100&type=owner&sort=updated"
        repos_response = requests.get(repos_url, headers=headers)
        repos_response.raise_for_status()
        repos = [r for r in repos_response.json()
                if not r.get('fork', False) and r['name'] not in EXCLUDED_REPOS]

        print(f"Found {len(repos)} non-fork repositories (excluding {len(EXCLUDED_REPOS)} repos)")

        activities = []

        # Fetch recent commits from each repo
        for repo in repos[:20]:  # Limit to first 20 repos to avoid rate limits
            repo_name = repo['name']
            repo_url = repo['html_url']

            # Get commits
            commits_url = f"https://api.github.com/repos/{username}/{repo_name}/commits?per_page=3"
            commits_response = requests.get(commits_url, headers=headers)

            if commits_response.status_code == 200:
                commits = commits_response.json()
                for commit in commits:
                    commit_data = commit.get('commit', {})
                    commit_msg = commit_data.get('message', '').split('\n')[0]  # First line only
                    commit_date = commit_data.get('author', {}).get('date', '')
                    commit_sha = commit.get('sha', '')[:7]
                    commit_url = commit.get('html_url', '')

                    if commit_date:
                        try:
                            date_obj = datetime.strptime(commit_date, "%Y-%m-%dT%H:%M:%SZ")
                            date_obj = date_obj.replace(tzinfo=timezone.utc)
                        except ValueError:
                            continue

                        activities.append({
                            'type': 'commit',
                            'repo': repo_name,
                            'repo_url': repo_url,
                            'message': commit_msg,
                            'sha': commit_sha,
                            'url': commit_url,
                            'date': date_obj
                        })

            # Get releases
            releases_url = f"https://api.github.com/repos/{username}/{repo_name}/releases?per_page=3"
            releases_response = requests.get(releases_url, headers=headers)

            if releases_response.status_code == 200:
                releases = releases_response.json()
                for release in releases:
                    release_name = release.get('name') or release.get('tag_name', 'Release')
                    release_date = release.get('published_at', '')
                    release_url = release.get('html_url', '')

                    if release_date:
                        try:
                            date_obj = datetime.strptime(release_date, "%Y-%m-%dT%H:%M:%SZ")
                            date_obj = date_obj.replace(tzinfo=timezone.utc)
                        except ValueError:
                            continue

                        activities.append({
                            'type': 'release',
                            'repo': repo_name,
                            'repo_url': repo_url,
                            'name': release_name,
                            'url': release_url,
                            'date': date_obj
                        })

        # Sort by date and return most recent
        activities.sort(key=lambda x: x['date'], reverse=True)
        return activities[:max_items]

    except Exception as e:
        print(f"Error fetching GitHub activity: {e}")
        return []


def generate_posts_markdown(posts):
    """Generate markdown for the posts section."""
    lines = [POSTS_START_MARKER]

    for post in posts:
        lines.append(f"- [{post['title']}]({post['link']}) - {post['date']}")

    lines.append(POSTS_END_MARKER)
    return "\n".join(lines)


def generate_activity_markdown(activities):
    """Generate markdown for GitHub activity."""
    if not activities:
        return f"{ACTIVITY_START_MARKER}\n*No recent activity*\n{ACTIVITY_END_MARKER}"

    lines = [ACTIVITY_START_MARKER]

    for activity in activities:
        formatted_date = activity['date'].strftime("%B %d, %Y")

        if activity['type'] == 'commit':
            lines.append(f"- **[{activity['repo']}]({activity['repo_url']})**: [{activity['sha']}]({activity['url']}) - {activity['message']} ({formatted_date})")
        elif activity['type'] == 'release':
            lines.append(f"- **[{activity['repo']}]({activity['repo_url']})**: Released [{activity['name']}]({activity['url']}) ({formatted_date})")

    lines.append(ACTIVITY_END_MARKER)
    return "\n".join(lines)


def update_readme_section(content, start_marker, end_marker, new_content_md):
    """Update a specific section in the README between markers."""
    if start_marker in content and end_marker in content:
        pattern = f"{re.escape(start_marker)}.*?{re.escape(end_marker)}"
        return re.sub(pattern, new_content_md, content, flags=re.DOTALL)
    return content


def update_readme(readme_path, posts_markdown, activity_markdown):
    """Update the README file with the latest posts and GitHub activity."""
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Update posts section
    content = update_readme_section(content, POSTS_START_MARKER, POSTS_END_MARKER, posts_markdown)

    # Update activity section
    content = update_readme_section(content, ACTIVITY_START_MARKER, ACTIVITY_END_MARKER, activity_markdown)

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✓ README updated successfully")


def main():
    """Main function to fetch posts, GitHub activity, and update README."""
    # Fetch blog posts
    print(f"Fetching latest {MAX_POSTS} posts from {RSS_FEED_URL}...")
    posts = fetch_latest_posts(RSS_FEED_URL, MAX_POSTS)

    if not posts:
        print("No posts found in feed")
        return

    print(f"✓ Found {len(posts)} posts")

    # Fetch GitHub activity
    print(f"Fetching GitHub activity for {GITHUB_USERNAME}...")
    activities = fetch_github_activity(GITHUB_USERNAME, MAX_ACTIVITY)
    print(f"✓ Found {len(activities)} recent activities")

    # Generate markdown
    posts_markdown = generate_posts_markdown(posts)
    activity_markdown = generate_activity_markdown(activities)

    # Update README
    update_readme(README_PATH, posts_markdown, activity_markdown)

    print("✓ Done!")


if __name__ == "__main__":
    main()
