import glob
import logging
import os
import shutil
import subprocess
import tempfile

from app.core.exceptions import AudioExtractionException

logger = logging.getLogger(__name__)


def extract_audio(video_id: str) -> str:
    """yt-dlp로 유튜브 영상에서 오디오만 추출한다.

    Returns:
        임시 오디오 파일의 절대 경로
    """
    tmp_dir = tempfile.mkdtemp(prefix="ddukddak_")
    output_template = os.path.join(tmp_dir, "audio.%(ext)s")

    url = f"https://www.youtube.com/watch?v={video_id}"
    command = [
        "yt-dlp",
        "-f", "bestaudio",
        "-x",
        "--audio-format", "m4a",
        "-o", output_template,
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

        # tmpdir 안에서 생성된 파일을 찾는다
        files = glob.glob(os.path.join(tmp_dir, "audio.*"))
        if not files or os.path.getsize(files[0]) == 0:
            raise AudioExtractionException()

        return files[0]

    except subprocess.TimeoutExpired:
        logger.error("yt-dlp timeout for video_id: %s", video_id)
        _cleanup_dir(tmp_dir)
        raise AudioExtractionException()
    except AudioExtractionException:
        _cleanup_dir(tmp_dir)
        raise
    except Exception as e:
        logger.error("Audio extraction failed: %s", e)
        _cleanup_dir(tmp_dir)
        raise AudioExtractionException()


def cleanup_audio(file_path: str) -> None:
    """오디오 임시 파일과 디렉토리를 삭제한다."""
    tmp_dir = os.path.dirname(file_path)
    _cleanup_dir(tmp_dir)


def _cleanup_dir(dir_path: str) -> None:
    if dir_path and os.path.exists(dir_path):
        try:
            shutil.rmtree(dir_path)
        except OSError as e:
            logger.warning("Failed to cleanup temp dir %s: %s", dir_path, e)
