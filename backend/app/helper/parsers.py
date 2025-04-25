from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from urllib.parse import urlparse, parse_qs
from curl_cffi import requests
from bs4 import BeautifulSoup
from pytube import YouTube
import pymupdf4llm
import markdownify
import re


def parse_pdf(file_path: str):
    md_content = pymupdf4llm.to_markdown(file_path)
    return md_content


def get_web_content(url: str):
    try:
        response = requests.get(
            url,
            impersonate="chrome110",
            timeout=30,
            cookies={},
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/110.0.0.0",
            },
            # follow_redirects=True,
            # For Cloudflare-protected sites
            cf_clearance="",  # Add cf_clearance cookie if available
            proxy=None,  # Optionally use a proxy
            decode_content=True,
        )

        if response.status_code == 200:
            response = response.text
        else:
            print(f"Failed with status code: {response.status_code}")
            return None

        return markdownify.markdownify(response)

    except Exception as e:
        print(f"Error: {str(e)}")
        return None


def get_youtube_info(url):
    """
    Fetches the title and transcript of a YouTube video from its URL.
    
    Args:
        url (str): The URL of the YouTube video
        
    Returns:
        dict: A dictionary containing the video title and transcript
              with keys 'title' and 'transcript'
    """
    # Extract video ID from URL
    video_id = extract_video_id(url)
    if not video_id:
        return {"error": "Invalid YouTube URL"}
    
    result = {"video_id": video_id}
    
    # Get video title using requests and BeautifulSoup
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(f"https://www.youtube.com/watch?v={video_id}", headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            title_element = soup.find("meta", property="og:title")
            if title_element:
                result["title"] = title_element["content"]
            else:
                title_tag = soup.find("title")
                if title_tag:
                    result["title"] = title_tag.text.replace(" - YouTube", "")
                else:
                    result["title"] = f"YouTube Video {video_id}"
        else:
            result["error_title"] = f"Failed to fetch title: HTTP status {response.status_code}"
    except Exception as e:
        result["error_title"] = f"Failed to fetch title: {str(e)}"
    
    # Get transcript using multiple approaches
    transcript_text = get_transcript_multiple_methods(video_id)
    
    if transcript_text:
        result["transcript"] = transcript_text
    else:
        result["error_transcript"] = "Failed to fetch transcript with all available methods"
    
    return result

def get_transcript_multiple_methods(video_id):
    """
    Try multiple methods to get a transcript for a YouTube video.
    
    Args:
        video_id (str): YouTube video ID
        
    Returns:
        str: Transcript text or empty string if all methods fail
    """
    # Method 1: Using youtube_transcript_api directly
    transcript_text = get_transcript_method_1(video_id)
    if transcript_text:
        return transcript_text
    
    # Method 2: Try fetching all available transcripts and languages
    transcript_text = get_transcript_method_2(video_id)
    if transcript_text:
        return transcript_text
    
    # Method 3: Try scraping the transcript from the YouTube page
    transcript_text = get_transcript_method_3(video_id)
    if transcript_text:
        return transcript_text
    
    # All methods failed
    return ""

def get_transcript_method_1(video_id):
    """
    Get transcript using the standard youtube_transcript_api approach.
    
    Args:
        video_id (str): YouTube video ID
        
    Returns:
        str: Transcript text or empty string if failed
    """
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        if transcript_list:
            return format_transcript(transcript_list)
    except Exception:
        pass
    
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
        if transcript_list:
            return format_transcript(transcript_list)
    except Exception:
        pass
    
    # Try other common languages if English fails
    for lang in ['es', 'fr', 'de', 'ru', 'ja', 'ko', 'zh-Hans', 'zh-Hant', 'ar', 'hi']:
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang])
            if transcript_list:
                return format_transcript(transcript_list)
        except Exception:
            continue
    
    return ""

def get_transcript_method_2(video_id):
    """
    Get transcript by trying all available languages and transcript types.
    
    Args:
        video_id (str): YouTube video ID
        
    Returns:
        str: Transcript text or empty string if failed
    """
    try:
        # Get list of available transcripts
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # Try each available transcript
        for transcript in transcript_list:
            try:
                transcript_data = transcript.fetch()
                if transcript_data:
                    formatted = format_transcript(transcript_data)
                    if formatted and not is_empty_transcript(formatted):
                        return formatted
            except Exception:
                continue
        
        # If none of the direct transcripts worked, try translations
        for transcript in transcript_list:
            for lang in ['en', 'es', 'fr', 'de']:
                try:
                    translated = transcript.translate(lang).fetch()
                    if translated:
                        formatted = format_transcript(translated)
                        if formatted and not is_empty_transcript(formatted):
                            return formatted
                except Exception:
                    continue
    except Exception:
        pass
    
    return ""

def get_transcript_method_3(video_id):
    """
    Get transcript by scraping the YouTube page.
    
    Args:
        video_id (str): YouTube video ID
        
    Returns:
        str: Transcript text or empty string if failed
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        # Get the main video page to extract timedtext info
        response = requests.get(f"https://www.youtube.com/watch?v={video_id}", headers=headers)
        if response.status_code != 200:
            return ""
            
        # Basic scraping for transcript text
        soup = BeautifulSoup(response.text, "html.parser")
        transcript_text = ""
        
        # Look for transcript data in page source
        script_tags = soup.find_all("script")
        for script in script_tags:
            if script.string and "captionTracks" in script.string:
                # This is a simplified approach - real implementation would parse the JSON properly
                caption_url_match = re.search(r'"captionTracks":\[{.*?"baseUrl":"(.*?)"', script.string)
                if caption_url_match:
                    caption_url = caption_url_match.group(1).replace('\\u0026', '&')
                    try:
                        caption_response = requests.get(caption_url, headers=headers)
                        if caption_response.status_code == 200:
                            caption_soup = BeautifulSoup(caption_response.text, "xml")
                            text_elements = caption_soup.find_all("text")
                            for i, text in enumerate(text_elements):
                                if text.string and text.string.strip():
                                    start_time = float(text.get("start", 0))
                                    transcript_text += f"[{format_time(start_time)}] {text.string.strip()}\n"
                            if transcript_text:
                                return transcript_text
                    except Exception:
                        pass
    except Exception:
        pass
        
    return ""

def extract_video_id(url):
    """
    Extracts the video ID from a YouTube URL.
    
    Args:
        url (str): YouTube URL
        
    Returns:
        str: YouTube video ID or None if not found
    """
    # Pattern to match YouTube URLs
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/v\/|youtube\.com\/e\/|youtube\.com\/watch\?.*v=)([^&\?#]+)',
        r'(?:youtube\.com\/shorts\/)([^&\?#\/]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None

def format_transcript(transcript_data):
    """
    Formats transcript data into a readable string.
    
    Args:
        transcript_data (list): List of transcript segments
        
    Returns:
        str: Formatted transcript text
    """
    transcript_text = ""
    for entry in transcript_data:
        text = entry.text.strip()
        # Skip empty segments
        if not text:
            continue
        start_time = format_time(entry.start)
        transcript_text += f"[{start_time}] {text}\n"
    
    return transcript_text

def is_empty_transcript(transcript_text):
    """
    Check if a transcript contains actual content or is essentially empty.
    
    Args:
        transcript_text (str): Formatted transcript text
        
    Returns:
        bool: True if the transcript is effectively empty
    """
    # Count lines with actual text (more than just timestamp and whitespace)
    content_lines = 0
    lines = transcript_text.strip().split('\n')
    
    for line in lines:
        # Remove timestamp and check if there's content
        content = re.sub(r'\[\d+:\d+\]', '', line).strip()
        if content:
            content_lines += 1
    
    # If less than 5% of lines have content, consider it empty
    return content_lines < max(3, len(lines) * 0.05)

def format_time(seconds):
    """
    Formats time in seconds to MM:SS format.
    
    Args:
        seconds (float): Time in seconds
        
    Returns:
        str: Time in MM:SS format
    """
    minutes = int(float(seconds) // 60)
    seconds = int(float(seconds) % 60)
    return f"{minutes:02d}:{seconds:02d}"