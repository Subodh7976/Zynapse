from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from urllib.parse import urlparse, parse_qs
from curl_cffi import requests
from pytube import YouTube
import pymupdf4llm
import markdownify


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
            follow_redirects=True,
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


def get_youtube_transcript(youtube_url):
    """
    Extract the transcript and title from a YouTube video.

    Args:
        youtube_url (str): The YouTube video URL

    Returns:
        dict: {
            'success': bool,
            'transcript': str or None,
            'title': str or None,
            'error': str or None,
            'language': str or None,
            'video_id': str,
            'author': str or None,
            'publish_date': str or None,
            'view_count': int or None
        }
    """
    result = {
        'success': False,
        'transcript': None,
        'title': None,
        'error': None,
        'language': None,
        'video_id': None,
        'author': None,
        'publish_date': None,
        'view_count': None
    }

    try:
        # Extract video ID from the URL
        video_id = extract_video_id(youtube_url)
        if not video_id:
            result['error'] = 'Invalid YouTube URL'
            return result

        result['video_id'] = video_id

        # Get video metadata using pytube
        try:
            yt = YouTube(youtube_url)
            result['title'] = yt.title
            result['author'] = yt.author
            result['publish_date'] = yt.publish_date.strftime(
                '%Y-%m-%d') if yt.publish_date else None
            result['view_count'] = yt.views
        except Exception as e:
            result['error'] = f'Error fetching video metadata: {str(e)}'
            # Continue anyway to try getting the transcript

        # Get available transcripts
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        # Try to get English transcript first
        try:
            transcript = transcript_list.find_transcript(['en'])
            result['language'] = 'en'
        except NoTranscriptFound:
            # If no English transcript, get the default one
            transcript = transcript_list.find_generated_transcript()
            result['language'] = transcript.language_code

        # Fetch the transcript
        transcript_data = transcript.fetch()

        # Combine all text entries into a single string
        full_transcript = ' '.join([entry['text']
                                   for entry in transcript_data])

        result['transcript'] = full_transcript
        result['success'] = True

        return result

    except TranscriptsDisabled:
        result['error'] = 'Transcripts are disabled for this video'
        return result
    except NoTranscriptFound:
        result['error'] = 'No transcript found for this video'
        return result
    except Exception as e:
        result['error'] = f'Error extracting transcript: {str(e)}'
        return result


def extract_video_id(youtube_url):
    """
    Extract the video ID from a YouTube URL.

    Args:
        youtube_url (str): The YouTube video URL

    Returns:
        str or None: The video ID if found, None otherwise
    """
    # Handle different YouTube URL formats
    parsed_url = urlparse(youtube_url)

    # Standard youtube.com/watch?v=VIDEO_ID format
    if parsed_url.netloc in ('www.youtube.com', 'youtube.com'):
        if parsed_url.path == '/watch':
            query_params = parse_qs(parsed_url.query)
            return query_params.get('v', [None])[0]

    # Short youtu.be/VIDEO_ID format
    elif parsed_url.netloc == 'youtu.be':
        return parsed_url.path.lstrip('/')

    # Embedded format
    elif '/embed/' in parsed_url.path:
        path_parts = parsed_url.path.split('/')
        if len(path_parts) > 2:
            return path_parts[2]

    return None
