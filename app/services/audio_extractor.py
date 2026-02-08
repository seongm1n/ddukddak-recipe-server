import logging
import os
import subprocess
import tempfile

from app.core.exceptions import AudioExtractionException

logger = logging.getLogger(__name__)


def extract_audio(video_id: str) -> str:
    """yt-dlp로 유튜브 영상에서 오디오만 추출한다.
    
    Returns:
        임시 오디오 파일의 절대 경로
    """
    with tempfile.NamedTemporaryFile(suffix=".m4a", delete=False) as tmp:
        output_path = tmp.name

    url = f"https://www.youtube.com/watch?v={video_id}"
    command = [
        "yt-dlp",
        "-f", "bestaudio",
        "-x",
        "--audio-format", "m4a",
        "-o", output_path,
        "--no-playlist",
        url,
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode != 0:
            logger.error("yt-dlp failed: %s", result.stderr)
            raise AudioExtractionException()
        
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise AudioExtractionException()
        
        return output_path
    
    except subprocess.TimeoutExpired:
        logger.error("yt-dlp timeout for video_id: %s", video_id)
        _cleanup(output_path)
        raise AudioExtractionException()
    except AudioExtractionException:
        _cleanup(output_path)
        raise
    except Exception as e:
        logger.error("Audio extraction failed: %s", e)
        _cleanup(output_path)
        raise AudioExtractionException()
    

def cleanup_audio(file_path: str) -> None:
    """오디오 임시 파일을 삭제한다."""
    _cleanup(file_path)


def _cleanup(file_path: str) -> None:
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError as e:
            logger.warning("Failed to cleanup audio file %s: %s", file_path, e)
