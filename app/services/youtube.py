import re
from dataclasses import dataclass

from googleapiclient.discovery import build

from app.core.config import get_settings
from app.core.exceptions import AppException, VideoNotFoundException

settings = get_settings()

_VIDEO_ID_PATTERN = re.compile(
    r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/shorts/)([a-zA-Z0-9_-]{11})"
)


@dataclass(frozen=True)
class VideoMetadata:
    video_id: str
    title: str
    channel_name: str
    thumbnail_url: str


def extract_video_id(url: str) -> str:
    """유튜브 URL에서 video_id(11자)를 추출한다."""
    match = _VIDEO_ID_PATTERN.search(url)
    if match is None:
        raise AppException("유효하지 않은 유튜브 URL입니다")
    return match.group(1)


def fetch_video_metadata(video_id: str) -> VideoMetadata:
    """YouTube Data API v3로 영상 메타데이터를 조회한다."""
    youtube = build("youtube", "v3", developerKey=settings.youtube_api_key)

    response = youtube.videos().list(part="snippet", id=video_id).execute()

    items = response.get("items", [])
    if not items:
        raise VideoNotFoundException()
    
    snippet = items[0]["snippet"]
    thumbnails = snippet["thumbnails"]
    thumbnail_url = (
        thumbnails.get("maxres", {}).get("url")
        or thumbnails.get("high", {}).get("url")
        or thumbnails.get("medium", {}).get("url", "")
    )

    return VideoMetadata(
        video_id=video_id,
        title=snippet["title"],
        channel_name=snippet["channelTitle"],
        thumbnail_url=thumbnail_url,
    )
