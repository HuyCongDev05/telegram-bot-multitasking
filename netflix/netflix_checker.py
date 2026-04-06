import json
import logging
import re
from http.client import RemoteDisconnected

import requests
from bs4 import BeautifulSoup
from requests.exceptions import ConnectionError, RequestException

from netflix.cookie_utils import (
    extract_cookie_dict,
    is_probable_netscape_cookie_line,
    normalize_cookie_domain,
    sanitize_cookie_text,
)

logger = logging.getLogger(__name__)

# Internal module sign ID
_MOD_SIG = "687579636f6e676465763035"


class NetscapeConverter:
    """Convert Netscape cookies into JSON-style cookie dicts."""

    @staticmethod
    def is_json(content):
        try:
            json.loads(sanitize_cookie_text(content))
            return True
        except Exception:
            return False

    @staticmethod
    def convert_to_json(content):
        """Convert Netscape cookie content into a list of cookie dicts."""
        content = sanitize_cookie_text(content)
        if NetscapeConverter.is_json(content):
            return json.loads(content)

        cookies = []
        for line in content.splitlines():
            line = line.strip()
            if not is_probable_netscape_cookie_line(line):
                continue

            fields = re.split(r"\s+", line, maxsplit=6)
            cookies.append(
                {
                    "domain": normalize_cookie_domain(fields[0]),
                    "flag": fields[1],
                    "path": fields[2],
                    "secure": fields[3].upper() == "TRUE",
                    "expiration": fields[4],
                    "name": fields[5],
                    "value": fields[6],
                }
            )
        if cookies:
            return cookies

        cookie_dict = extract_cookie_dict(content)
        if not cookie_dict:
            return cookies

        for name, value in cookie_dict.items():
            cookies.append(
                {
                    "domain": ".netflix.com",
                    "flag": "TRUE",
                    "path": "/",
                    "secure": True,
                    "expiration": "0",
                    "name": name,
                    "value": value,
                }
            )
        return cookies


class NetflixChecker:
    """Check Netflix cookies and only accept accounts that are watchable."""

    ERROR_MESSAGES = {
        "cookie_expired_or_invalid": "Cookie expired or invalid",
        "no_active_plan": "No active Netflix plan detected. This cookie cannot watch right now",
        "membership_setup_required": "Membership setup is incomplete. This cookie cannot watch right now",
        "membership_restart_required": "Membership must be restarted before watching",
        "membership_on_hold": "Membership is on hold and cannot watch right now",
        "payment_issue": "Account has a payment issue and cannot watch right now",
    }
    NON_WATCHABLE_PATTERNS = (
        (re.compile(r"choose (a|your) plan", re.I), "no_active_plan"),
        (re.compile(r"finish (setting up|signup|sign up)", re.I), "membership_setup_required"),
        (re.compile(r"complete (your )?sign[\s-]?up", re.I), "membership_setup_required"),
        (re.compile(r"restart (your )?membership", re.I), "membership_restart_required"),
        (re.compile(r"(membership|account).{0,40}on hold", re.I), "membership_on_hold"),
        (re.compile(r"resolve (your )?payment (issue|problem)", re.I), "payment_issue"),
        (re.compile(r"problem with (the )?payment method", re.I), "payment_issue"),
    )
    PLAN_CANDIDATES = ("Premium", "Standard with ads", "Standard", "Basic", "Mobile")

    def __init__(self, proxy_url=None):
        self.session = requests.Session()
        self.proxy_url = proxy_url
        if proxy_url:
            self.session.proxies = {
                "http": proxy_url,
                "https": proxy_url,
            }
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept-Encoding": "identity",
            }
        )

    def decode_hex_escapes(self, value):
        if not value:
            return value
        value = re.sub(r"\\x([0-9A-Fa-f]{2})", lambda match: chr(int(match.group(1), 16)), value)
        value = re.sub(r"\\u([0-9A-Fa-f]{4})", lambda match: chr(int(match.group(1), 16)), value)
        return value

    def extract_info(self, text):
        patterns = {
            "localizedPlanName": r'"localizedPlanName"\s*:\s*\{\s*"fieldType"\s*:\s*"String"\s*,\s*"value"\s*:\s*"([^"]+)"',
            "emailAddress": r'"emailAddress"\s*:\s*"([^"]+)"',
            "countryOfSignup": r'"countryOfSignup"\s*:\s*"([^"]+)"',
        }
        result = {}
        for key, pattern in patterns.items():
            match = re.search(pattern, text)
            result[key] = self.decode_hex_escapes(match.group(1)) if match else None
        return result

    def build_error(self, error_code, **extra):
        payload = {
            "error_code": error_code,
            "error": self.ERROR_MESSAGES.get(error_code, "Unknown error"),
        }
        payload.update({key: value for key, value in extra.items() if value is not None})
        return payload

    def detect_watchability_issue(self, response_url, page_text, plan):
        normalized_url = (response_url or "").lower()
        if any(marker in normalized_url for marker in ("signup", "setupaccount", "confirmmembershipstarted")):
            return "membership_setup_required"

        for pattern, error_code in self.NON_WATCHABLE_PATTERNS:
            if pattern.search(page_text):
                return error_code

        if not plan or plan == "Unknown":
            return "no_active_plan"

        return None

    def check(self, cookies_list):
        """
        Validate a Netflix cookie list.
        Returns: (True/False, info_dict)
        """
        self.session.cookies.clear()
        for cookie in cookies_list:
            self.session.cookies.set(
                cookie["name"],
                cookie["value"],
                domain=cookie.get("domain", ".netflix.com"),
            )

        try:
            response = self.session.get("https://www.netflix.com/YourAccount", timeout=20, allow_redirects=True)
            if response.status_code != 200:
                return False, {"error": f"HTTP {response.status_code}"}

            content = response.text
            soup = BeautifulSoup(content, "lxml")
            page_text = " ".join(soup.get_text(" ", strip=True).split())

            if soup.find(string=re.compile("Sign In", re.I)) or "netflix.com/login" in response.url:
                return False, self.build_error("cookie_expired_or_invalid")

            info = self.extract_info(content)

            try:
                extra_member_response = self.session.get(
                    "https://www.netflix.com/accountowner/addextramember",
                    allow_redirects=False,
                    timeout=15,
                )
                extra_member = extra_member_response.status_code == 200
            except Exception:
                extra_member = False

            plan = info.get("localizedPlanName")
            if plan:
                plan = plan.replace("miembro\xa0extra", "(Shared Extra Member)")
            else:
                page_text_lower = page_text.lower()
                for candidate in self.PLAN_CANDIDATES:
                    if candidate.lower() in page_text_lower:
                        plan = candidate
                        break
                else:
                    plan = "Unknown"

            email = info.get("emailAddress")
            if not email:
                email_element = soup.select_one(".account-section-email")
                email = email_element.text.strip() if email_element else "Unknown"

            country = info.get("countryOfSignup") or "Unknown"

            result = {
                "plan": plan,
                "email": email,
                "country": country,
                "extra_member": extra_member,
                "watchable": True,
            }

            issue_code = self.detect_watchability_issue(response.url, page_text, plan)
            if issue_code:
                result.update(self.build_error(issue_code))
                result["watchable"] = False
                return False, result

            return True, result

        except (RequestException, ConnectionError, RemoteDisconnected) as exc:
            return False, {"error": str(exc)}
        except Exception as exc:
            logger.error("Unknown error while checking Netflix cookie: %s", exc)
            return False, {"error": "Internal Error"}
