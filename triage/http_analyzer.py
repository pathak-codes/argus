import re
import urllib3

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
FORM_RE = re.compile(r"<form[>\s]", re.IGNORECASE)
INPUT_RE = re.compile(r"<input[>\s]", re.IGNORECASE)
SCRIPT_SRC_RE = re.compile(r'<script[^>]*src=["\']', re.IGNORECASE)

KNOWN_DEFAULT_PAGES = {
    "welcome to nginx",
    "welcome to nginx!",
    "apache2 ubuntu default page",
    "it works",
    "it works!",
    "index of /",
    "welcome to iis",
    "iis windows",
    "welcome to centos",
    "default page",
    "under construction",
    "site doesn't have a title",
    "site doesn't have a title (application/json).",
    "403 forbidden",
    "404 not found",
    "400 bad request",
    "500 internal server error",
    "502 bad gateway",
    "503 service unavailable",
}

KNOWN_ERROR_PATTERNS = [
    re.compile(r"404\s*(not\s*found)?", re.IGNORECASE),
    re.compile(r"403\s*forbidden", re.IGNORECASE),
    re.compile(r"500\s*internal\s*server\s*error", re.IGNORECASE),
    re.compile(r"502\s*bad\s*gateway", re.IGNORECASE),
    re.compile(r"503\s*service\s*unavailable", re.IGNORECASE),
    re.compile(r"nginx", re.IGNORECASE),
    re.compile(r"apache.*default", re.IGNORECASE),
    re.compile(r"iis.*welcome", re.IGNORECASE),
]


class HttpResult:
    __slots__ = (
        "host", "port", "url", "method", "status",
        "content_type", "content_length", "body",
        "server", "title", "redirect_location",
        "redirect_count", "redirect_chain",
        "auth_scheme", "has_form", "has_js",
        "visible_text_length", "error",
    )

    def __init__(self, host="", port="", url="", method="GET", status=0,
                 content_type="", content_length=0, body=b"",
                 server="", title="", redirect_location="",
                 redirect_count=0, redirect_chain=None,
                 auth_scheme="", has_form=False, has_js=False,
                 visible_text_length=0, error=""):
        self.host = host
        self.port = port
        self.url = url
        self.method = method
        self.status = status
        self.content_type = content_type
        self.content_length = content_length
        self.body = body
        self.server = server
        self.title = title
        self.redirect_location = redirect_location
        self.redirect_count = redirect_count
        self.redirect_chain = redirect_chain or []
        self.auth_scheme = auth_scheme
        self.has_form = has_form
        self.has_js = has_js
        self.visible_text_length = visible_text_length
        self.error = error

    def dict(self):
        return {
            "host": self.host,
            "port": self.port,
            "url": self.url,
            "method": self.method,
            "status": self.status,
            "content_type": self.content_type,
            "content_length": self.content_length,
            "server": self.server,
            "title": self.title,
            "redirect_location": self.redirect_location,
            "redirect_count": self.redirect_count,
            "auth_scheme": self.auth_scheme,
            "has_form": self.has_form,
            "has_js": self.has_js,
            "visible_text_length": self.visible_text_length,
            "error": self.error,
            "body_preview": (self.body[:500].decode("utf-8", errors="replace")
                             if isinstance(self.body, bytes) else "") if self.body else "",
        }

    def dedup_key(self):
        return f"{self.title}::{self.status}::{self.content_length}"


class HttpAnalyzer:
    def __init__(self, timeout=5, max_retries=2):
        self.timeout = timeout
        self._session = self._build_session(max_retries)

    @staticmethod
    def _build_session(max_retries):
        session = requests.Session()
        session.verify = False
        session.max_redirects = 10

        retry = Retry(
            total=max_retries,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(
            max_retries=retry,
            pool_connections=100,
            pool_maxsize=100,
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    @staticmethod
    def _build_url(host, port_str):
        clean_port = str(port_str).split("/")[0]
        protocol = "https" if "443" in str(port_str) else "http"
        return f"{protocol}://{host}:{clean_port}", clean_port

    @staticmethod
    def _extract_title(body_text):
        m = TITLE_RE.search(body_text)
        if m:
            return m.group(1).strip()
        return ""

    def analyze(self, host, port_str):
        url, clean_port = self._build_url(host, port_str)

        try:
            resp = self._session.get(url, timeout=self.timeout, allow_redirects=True)

            body = resp.content
            body_text = resp.text

            content_type = (resp.headers.get("Content-Type", "") or "").split(";")[0].strip()

            title = self._extract_title(body_text)

            redirect_chain = []
            for h in resp.history:
                redirect_chain.append({
                    "status": h.status_code,
                    "location": h.headers.get("Location", ""),
                    "url": h.url,
                })

            visible_text = re.sub(r"<[^>]+>", " ", body_text)
            visible_text = re.sub(r"\s+", " ", visible_text).strip()

            result = HttpResult(
                host=host,
                port=clean_port,
                url=url,
                method="GET",
                status=resp.status_code,
                content_type=content_type,
                content_length=len(body),
                body=body,
                server=resp.headers.get("Server", ""),
                title=title,
                redirect_location=redirect_chain[-1]["location"] if redirect_chain else "",
                redirect_count=len(redirect_chain),
                redirect_chain=redirect_chain,
                auth_scheme=resp.headers.get("WWW-Authenticate", ""),
                has_form=bool(FORM_RE.search(body_text) or INPUT_RE.search(body_text)),
                has_js=bool(SCRIPT_SRC_RE.search(body_text) or "javascript" in content_type),
                visible_text_length=len(visible_text),
            )
            return result

        except requests.exceptions.Timeout:
            return HttpResult(host=host, port=clean_port, url=url, status=0, error="Timeout")
        except requests.exceptions.ConnectionError:
            return HttpResult(host=host, port=clean_port, url=url, status=0, error="Connection Refused")
        except requests.exceptions.TooManyRedirects:
            return HttpResult(host=host, port=clean_port, url=url, status=0, error="Too Many Redirects")
        except Exception as e:
            return HttpResult(host=host, port=clean_port, url=url, status=0, error=str(e)[:80])

    def close(self):
        self._session.close()
