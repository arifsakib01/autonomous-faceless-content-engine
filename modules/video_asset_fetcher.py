"""
MODULE 3: Visual Asset Fetcher
Fetches short vertical video clips from Pexels API.
"""
import json
import logging
import time
from pathlib import Path
from typing import List, Optional
import requests

from models import VideoClip
from exceptions import VideoAssetError
from config import (
    PEXELS_API_KEY, PEXELS_VIDEO_COUNT, PEXELS_MIN_DURATION,
    PEXELS_VIDEO_QUALITY, PEXELS_SEARCH_LIMIT, TEMP_DIR,
    MAX_RETRIES, RETRY_DELAY
)


logger = logging.getLogger(__name__)


class PexelsVideoFetcher:
    """Fetches vertical HD video clips from Pexels API."""
    
    BASE_URL = "https://api.pexels.com/videos/search"
    
    def __init__(self, api_key: str = PEXELS_API_KEY):
        """
        Initialize Pexels fetcher.
        
        Args:
            api_key: Pexels API key
        
        Raises:
            VideoAssetError: If API key is missing
        """
        if not api_key:
            raise VideoAssetError("Pexels API key not provided in environment or config")
        
        self.api_key = api_key
        logger.info("PexelsVideoFetcher initialized")
    
    def fetch_videos(
        self,
        keywords: List[str],
        video_count: int = PEXELS_VIDEO_COUNT,
        quality: str = PEXELS_VIDEO_QUALITY
    ) -> List[VideoClip]:
        """
        Fetch vertical video clips matching keywords.
        
        Args:
            keywords: Search keywords/phrases
            video_count: Number of videos to fetch (3-4 recommended)
            quality: Video quality ('sd' or 'hd')
        
        Returns:
            List of VideoClip objects with metadata
        
        Raises:
            VideoAssetError: If fetching fails
        """
        try:
            logger.info(f"Fetching {video_count} videos for keywords: {keywords}")
            
            all_videos = []
            
            # Search with each keyword (rotate through keywords for variety)
            for keyword in keywords[:3]:  # Use first 3 keywords
                videos = self._search_videos(keyword, quality)
                all_videos.extend(videos)
                
                if len(all_videos) >= video_count:
                    break
            
            if not all_videos:
                raise VideoAssetError(f"No videos found for keywords: {keywords}")
            
            # Select and download the most suitable videos
            selected_videos = all_videos[:video_count]
            downloaded_videos = []
            
            for video in selected_videos:
                try:
                    downloaded = self._download_video(video, quality)
                    downloaded_videos.append(downloaded)
                except Exception as e:
                    logger.warning(f"Failed to download video {video.id}: {str(e)}")
                    continue
            
            if not downloaded_videos:
                raise VideoAssetError("Failed to download any videos")
            
            logger.info(f"Successfully fetched {len(downloaded_videos)} videos")
            return downloaded_videos
            
        except requests.exceptions.RequestException as e:
            raise VideoAssetError(f"Network error fetching videos: {str(e)}")
        except Exception as e:
            raise VideoAssetError(f"Failed to fetch videos: {str(e)}")
    
    def _search_videos(self, query: str, quality: str = PEXELS_VIDEO_QUALITY) -> List[VideoClip]:
        """
        Search Pexels for videos matching query.
        
        Args:
            query: Search query
            quality: Video quality
        
        Returns:
            List of VideoClip objects from search results
        """
        try:
            logger.debug(f"Searching Pexels for: {query}")
            
            headers = {
                "Authorization": self.api_key
            }
            
            params = {
                "query": query,
                "per_page": PEXELS_SEARCH_LIMIT,
                "page": 1,
                "orientation": "portrait"  # Vertical videos
            }
            
            response = requests.get(
                self.BASE_URL,
                headers=headers,
                params=params,
                timeout=15
            )
            
            if response.status_code == 401:
                raise VideoAssetError("Invalid Pexels API key")
            elif response.status_code == 429:
                logger.warning("Pexels API rate limited, waiting before retry")
                time.sleep(RETRY_DELAY)
                return self._search_videos(query, quality)
            elif response.status_code != 200:
                raise VideoAssetError(f"Pexels API error {response.status_code}: {response.text}")
            
            data = response.json()
            videos = []
            
            for video_obj in data.get("videos", []):
                # Filter for vertical videos with adequate duration
                if video_obj.get("duration", 0) >= PEXELS_MIN_DURATION:
                    video = self._parse_video_object(video_obj, quality)
                    if video:
                        videos.append(video)
            
            logger.debug(f"Found {len(videos)} suitable videos for: {query}")
            return videos
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Search request failed: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error searching videos: {str(e)}")
            return []
    
    def _parse_video_object(self, video_obj: dict, quality: str) -> Optional[VideoClip]:
        """
        Parse Pexels video object to VideoClip.
        
        Args:
            video_obj: Raw video object from Pexels API
            quality: Requested quality
        
        Returns:
            VideoClip object or None if parsing fails
        """
        try:
            video_id = video_obj.get("id")
            duration = video_obj.get("duration", 0)
            width = video_obj.get("width", 0)
            height = video_obj.get("height", 0)
            
            # Get video file URL for requested quality
            video_files = video_obj.get("video_files", [])
            
            selected_file = None
            for vf in video_files:
                if vf.get("quality") == quality:
                    selected_file = vf
                    break
            
            # Fallback to hd if quality not available
            if not selected_file:
                for vf in video_files:
                    if vf.get("quality") == "hd":
                        selected_file = vf
                        break
            
            # Last resort: any available file
            if not selected_file and video_files:
                selected_file = video_files[0]
            
            if not selected_file:
                logger.warning(f"No video file found for video {video_id}")
                return None
            
            url = selected_file.get("link")
            
            if not url:
                logger.warning(f"No download URL for video {video_id}")
                return None
            
            return VideoClip(
                id=video_id,
                url=url,
                duration=duration,
                width=width,
                height=height
            )
            
        except Exception as e:
            logger.error(f"Error parsing video object: {str(e)}")
            return None
    
    def _download_video(self, video: VideoClip, quality: str) -> VideoClip:
        """
        Download video file from URL.
        
        Args:
            video: VideoClip object with URL
            quality: Video quality (for logging)
        
        Returns:
            VideoClip with file_path populated
        
        Raises:
            VideoAssetError: If download fails
        """
        try:
            output_path = TEMP_DIR / f"video_{video.id}_{int(time.time())}.mp4"
            
            logger.info(f"Downloading video {video.id} to {output_path}")
            
            # Download with timeout and streaming
            response = requests.get(
                video.url,
                timeout=60,
                stream=True
            )
            
            if response.status_code != 200:
                raise VideoAssetError(f"Failed to download video: HTTP {response.status_code}")
            
            # Write in chunks to handle large files
            total_size = 0
            chunk_size = 8192
            max_size = 500 * 1024 * 1024  # 500MB limit
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        total_size += len(chunk)
                        
                        if total_size > max_size:
                            output_path.unlink()
                            raise VideoAssetError(f"Video exceeded size limit ({max_size} bytes)")
            
            if not output_path.exists():
                raise VideoAssetError(f"Download failed: file not created")
            
            file_size = output_path.stat().st_size
            
            if file_size == 0:
                output_path.unlink()
                raise VideoAssetError("Downloaded file is empty")
            
            logger.info(f"Video downloaded: {file_size} bytes")
            
            # Update VideoClip with local path
            video.file_path = str(output_path)
            return video
            
        except requests.exceptions.RequestException as e:
            if output_path.exists():
                try:
                    output_path.unlink()
                except:
                    pass
            raise VideoAssetError(f"Download request failed: {str(e)}")
        except Exception as e:
            if output_path.exists():
                try:
                    output_path.unlink()
                except:
                    pass
            raise VideoAssetError(f"Video download failed: {str(e)}")


# Convenience function
def fetch_video_assets(keywords: List[str], count: int = PEXELS_VIDEO_COUNT) -> List[VideoClip]:
    """
    Convenience function to fetch video assets.
    
    Args:
        keywords: Search keywords
        count: Number of videos to fetch
    
    Returns:
        List of downloaded VideoClip objects
    """
    fetcher = PexelsVideoFetcher()
    return fetcher.fetch_videos(keywords, count)
