import re


from typing import Any

def sanitize_input(text: Any, max_length: int = 500) -> str:
    if not text:
        return ''
    text_str = str(text).strip()
    return text_str[:max_length]  # type: ignore


def is_valid_url(url):
    pattern = re.compile(
        r'^https?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )
    return bool(pattern.match(url))


def is_valid_keyword(keyword):
    if not keyword or len(keyword) < 2 or len(keyword) > 100:
        return False
    return bool(re.match(r'^[a-zA-Z0-9\s\-_]+$', keyword))


def is_valid_indicator(word):
    if not word or len(word) < 2 or len(word) > 50:
        return False
    return bool(re.match(r'^[a-zA-Z\s\-]+$', word))


def is_valid_headline(headline):
    if not headline:
        return False

    normalized = re.sub(r'\s+', ' ', str(headline).strip())
    if len(normalized) < 15 or len(normalized) > 300:
        return False

    words = re.findall(r"[A-Za-z0-9']+", normalized)
    if len(words) < 4 or len(words) > 35:
        return False

    alpha_words = [word for word in words if re.search(r'[A-Za-z]', word)]
    if len(alpha_words) < 4:
        return False

    unique_ratio = len({word.lower() for word in alpha_words}) / len(alpha_words)
    if unique_ratio < 0.6:
        return False

    return True


def is_valid_search_input(text):
    normalized = sanitize_input(text, max_length=1000)
    if not normalized:
        return False
    return is_valid_url(normalized) or is_valid_headline(normalized)
