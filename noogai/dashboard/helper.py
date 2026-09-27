from urllib.parse import urlparse, parse_qs
import requests
import streamlit as st

@st.cache_data
def get_video_id(youtube_url):
    parsed_url = urlparse(youtube_url)
    if parsed_url.hostname == "youtu.be":
        return parsed_url.path[1:]
    if parsed_url.hostname in ("www.youtube.com", "youtube.com"):
        if parsed_url.path == "/watch":
            return parse_qs(parsed_url.query)["v"][0]
    return None

@st.cache_data
def get_all_comments(video_id, api_key, limit=None):
    """Fetch top-level comments for a video.

    Args:
        video_id (str): YouTube video id.
        api_key (str): Google API key with YouTube Data API access.
        limit (int|None): Optional maximum number of comments to return. If None, fetches all available comments.

    Returns:
        list[dict]: List of comment dicts with keys: 'author', 'text', 'likes'.
    """

    BASE_URL = "https://www.googleapis.com/youtube/v3/commentThreads"
    comments = []
    next_page_token = None

    # validate limit
    if limit is not None:
        try:
            limit = int(limit)
            if limit <= 0:
                raise ValueError
        except Exception:
            raise ValueError("limit must be a positive integer or None")

    while True:
        # determine how many results to request this page
        if limit is None:
            page_size = 100
        else:
            remaining = limit - len(comments)
            if remaining <= 0:
                break
            page_size = min(100, remaining)

        params = {
            "part": "snippet",
            "videoId": video_id,
            "maxResults": page_size,
            "textFormat": "plainText",
            "key": api_key,
        }
        if next_page_token:
            params["pageToken"] = next_page_token

        resp = requests.get(BASE_URL, params=params)
        if resp.status_code != 200:
            break

        response = resp.json()

        for item in response.get("items", []):
            top_comment = item["snippet"]["topLevelComment"]["snippet"]
            text = top_comment.get("textDisplay", "")
            author = top_comment.get("authorDisplayName", "")
            like_count = top_comment.get("likeCount", 0)
            comments.append({
                "author": author,
                "text": text,
                "likes": like_count
            })

            # stop early if we've reached the requested limit
            if limit is not None and len(comments) >= limit:
                break

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

    return comments