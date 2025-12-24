from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from urllib.parse import urlparse
import re


class YouTubeURLValidator:
    """
    Validator for checking if URL is from YouTube.
    """
    message = _('Only YouTube URLs are allowed.')
    code = 'invalid_youtube_url'

    def __init__(self, allowed_domains=None):
        if allowed_domains is None:
            self.allowed_domains = ['youtube.com', 'youtu.be', 'www.youtube.com']
        else:
            self.allowed_domains = allowed_domains

    def __call__(self, value):
        if not value:
            return

        try:
            parsed_url = urlparse(value)
            domain = parsed_url.netloc.lower()

            # Check if domain is in allowed domains
            is_allowed = any(allowed_domain in domain for allowed_domain in self.allowed_domains)

            if not is_allowed:
                raise serializers.ValidationError(
                    self.message,
                    code=self.code
                )

            # Additional YouTube-specific validation
            if 'youtube.com' in domain or 'youtu.be' in domain:
                self._validate_youtube_url(value)

        except ValidationError:
            raise
        except Exception as e:
            raise serializers.ValidationError(
                _('Invalid URL format.'),
                code='invalid_url_format'
            )

    def _validate_youtube_url(self, url):
        """Additional validation for YouTube URLs."""
        # Check for video ID pattern
        youtube_regex = r'(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
        match = re.search(youtube_regex, url)

        if not match:
            raise serializers.ValidationError(
                _('Invalid YouTube URL format.'),
                code='invalid_youtube_format'
            )

    def __eq__(self, other):
        return (
                isinstance(other, self.__class__) and
                self.allowed_domains == other.allowed_domains
        )


class NoExternalLinksValidator:
    """
    Validator for checking if text contains external links (except YouTube).
    """
    message = _('Text contains external links to non-YouTube resources.')
    code = 'external_links_found'

    def __init__(self, fields=None):
        if fields is None:
            self.fields = ['description']
        else:
            self.fields = fields

    def __call__(self, data):
        youtube_validator = YouTubeURLValidator()

        for field in self.fields:
            if field in data:
                text = data[field]
                if text:
                    # Find all URLs in text
                    url_pattern = r'(https?://[^\s]+)'
                    urls = re.findall(url_pattern, text)

                    for url in urls:
                        try:
                            # Check if URL is YouTube
                            youtube_validator(url)
                        except serializers.ValidationError:
                            # If not YouTube, raise validation error
                            raise serializers.ValidationError(
                                {field: self.message},
                                code=self.code
                            )

    def __eq__(self, other):
        return (
                isinstance(other, self.__class__) and
                self.fields == other.fields
        )


# Function-based validators
def validate_youtube_url(value):
    """
    Function-based validator for YouTube URLs.
    """
    validator = YouTubeURLValidator()
    return validator(value)


def validate_no_external_links(text):
    """
    Function-based validator to check for external links.
    """
    if not text:
        return

    # Pattern to find URLs
    url_pattern = r'(https?://[^\s]+)'
    urls = re.findall(url_pattern, text)

    for url in urls:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()

        # Check if domain is not YouTube
        if 'youtube.com' not in domain and 'youtu.be' not in domain:
            raise ValidationError(
                _('Text contains external links to non-YouTube resources.'),
                code='external_links_found'
            )