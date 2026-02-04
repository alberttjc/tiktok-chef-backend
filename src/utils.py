"""
Utility functions for TiktokChef
"""
import re
from typing import Optional
from urllib.parse import urlparse


def extract_tiktok_username(url: str) -> Optional[str]:
    """
    Extract TikTok username from various TikTok URL formats.

    Supported formats:
    - https://www.tiktok.com/@username/video/123456789
    - https://tiktok.com/@username/video/123456789
    - https://vm.tiktok.com/ZMxxx/ (short URL - cannot extract username)
    - https://www.tiktok.com/@username

    Args:
        url: TikTok URL string

    Returns:
        Username without @ prefix, or None if not found

    Examples:
        >>> extract_tiktok_username("https://www.tiktok.com/@chef_marco/video/7123456789")
        'chef_marco'
        >>> extract_tiktok_username("https://tiktok.com/@cooking.with.jane/video/123")
        'cooking.with.jane'
        >>> extract_tiktok_username("https://vm.tiktok.com/ZMxxx/")
        None
    """
    if not url:
        return None

    try:
        # Pattern to match @username in TikTok URLs
        # Matches: @username followed by either / or end of string
        pattern = r'/@([a-zA-Z0-9._]+)'

        match = re.search(pattern, url)
        if match:
            username = match.group(1)
            return username

        return None

    except Exception:
        return None


def format_tiktok_username(username: Optional[str]) -> Optional[str]:
    """
    Format username to ensure it has @ prefix for display.

    Args:
        username: Username with or without @ prefix

    Returns:
        Username with @ prefix, or None if input is None

    Examples:
        >>> format_tiktok_username("chef_marco")
        '@chef_marco'
        >>> format_tiktok_username("@chef_marco")
        '@chef_marco'
        >>> format_tiktok_username(None)
        None
    """
    if not username:
        return None

    if username.startswith('@'):
        return username

    return f'@{username}'
