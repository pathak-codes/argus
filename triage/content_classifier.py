import re

from .http_analyzer import HttpResult, KNOWN_DEFAULT_PAGES, KNOWN_ERROR_PATTERNS

LOGIN_KEYWORDS = re.compile(
    r"\b(login|signin|sign-in|sign_in|log-in|log_in|authenticate|auth)\b",
    re.IGNORECASE,
)
ADMIN_KEYWORDS = re.compile(
    r"\b(admin|dashboard|control\s*panel|manager|console|administrator|admin-panel|management)\b",
    re.IGNORECASE,
)
CREDENTIAL_PATTERNS = re.compile(
    r"(password|passwd|pwd|secret|token|api[_-]?key)", re.IGNORECASE
)

SAFE_SCREENSHOT_STATUSES = {200, 401, 403, 405, 500, 502, 503, 301, 302, 307, 308}


class ContentClassifier:
    def __init__(self, min_score=3, min_content_length=1024):
        self.min_score = min_score
        self.min_content_length = min_content_length

    def should_analyze(self, result):
        if result.status == 0:
            return False
        if result.status in {301, 302, 307, 308} and not result.redirect_location:
            return False
        return True

    def is_error_or_default(self, result):
        title_lower = result.title.lower().strip()

        if title_lower in KNOWN_DEFAULT_PAGES:
            return True

        for pat in KNOWN_ERROR_PATTERNS:
            if pat.search(title_lower):
                return True

        body_lower = result.body.lower() if result.body else b""
        error_signals = [
            b"<title>404 not found",
            b"<title>403 forbidden",
            b"<title>500 internal server",
            b"<title>502 bad gateway",
            b"<title>503 service unavailable",
            b"welcome to nginx",
            b"apache2 ubuntu default page",
            b"it works",
            b"under construction",
        ]
        for sig in error_signals:
            if sig in body_lower:
                return True

        if result.content_length < self.min_content_length:
            return not (result.has_form or result.has_js or result.title)

        if result.visible_text_length < 20 and not result.title:
            return True

        return False

    def should_screenshot(self, result):
        if result.status == 0:
            return False

        if result.status not in SAFE_SCREENSHOT_STATUSES:
            return False

        if result.status in {301, 302, 307, 308}:
            return bool(result.redirect_location)

        if result.content_length < self.min_content_length and not result.title:
            return False

        score = self.score(result)
        return score >= self.min_score

    def score(self, result):
        score = 0

        if result.title:
            score += 3

        if result.content_length > 5120:
            score += 2

        if result.has_form:
            score += 1

        if result.has_js:
            score += 1

        body_text = result.body.lower() if result.body else b""
        if isinstance(body_text, bytes):
            body_text = body_text.decode("utf-8", errors="replace")

        if LOGIN_KEYWORDS.search(body_text) or LOGIN_KEYWORDS.search(result.title.lower()):
            score += 2

        if ADMIN_KEYWORDS.search(body_text) or ADMIN_KEYWORDS.search(result.title.lower()):
            score += 2

        if CREDENTIAL_PATTERNS.search(body_text):
            score += 1

        if result.content_length > 50000:
            score += 1

        return score
