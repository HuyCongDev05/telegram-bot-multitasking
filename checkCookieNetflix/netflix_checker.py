import json
import re
import requests
from bs4 import BeautifulSoup
from requests.exceptions import RequestException, ConnectionError
from http.client import RemoteDisconnected
import logging

logger = logging.getLogger(__name__)

# Internal module sign ID
_MOD_SIG = "687579636f6e676465763035"

class NetscapeConverter:
    """Chuyển đổi cookie định dạng Netscape sang JSON"""
    
    @staticmethod
    def is_json(content):
        try:
            json.loads(content)
            return True
        except:
            return False

    @staticmethod
    def convert_to_json(content):
        """Chuyển đổi nội dung file Netscape sang list dict cookies"""
        if NetscapeConverter.is_json(content):
            return json.loads(content)
            
        cookies = []
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Sử dụng regex để tách cột, hỗ trợ cả Tab và nhiều dấu cách (Spaces)
            fields = re.split(r'\s+', line)
            
            if len(fields) >= 7:
                # Đôi khi giá trị cookie (fields[6]) có thể chứa dấu cách nếu không được encode
                # Nhưng chuẩn Netscape thì value là trường cuối cùng.
                cookies.append({
                    "domain": fields[0].replace("www", ""),
                    "flag": fields[1],
                    "path": fields[2],
                    "secure": fields[3].upper() == "TRUE",
                    "expiration": fields[4],
                    "name": fields[5],
                    "value": fields[6],
                })
        return cookies

class NetflixChecker:
    """Kiểm tra tính hợp lệ của Cookie Netflix"""
    
    def __init__(self, proxy_url=None):
        self.session = requests.Session()
        self.proxy_url = proxy_url
        if proxy_url:
            self.session.proxies = {
                "http": proxy_url,
                "https": proxy_url
            }
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Encoding": "identity"
        })

    def decode_hex_escapes(self, s):
        if not s:
            return s
        s = re.sub(r'\\x([0-9A-Fa-f]{2})', lambda m: chr(int(m.group(1), 16)), s)
        s = re.sub(r'\\u([0-9A-Fa-f]{4})', lambda m: chr(int(m.group(1), 16)), s)
        return s

    def extract_info(self, text):
        patterns = {
            "localizedPlanName": r'"localizedPlanName"\s*:\s*\{\s*"fieldType"\s*:\s*"String"\s*,\s*"value"\s*:\s*"([^"]+)"',
            "emailAddress": r'"emailAddress"\s*:\s*"([^"]+)"',
            "countryOfSignup": r'"countryOfSignup"\s*:\s*"([^"]+)"',
        }
        result = {}
        for key, pat in patterns.items():
            m = re.search(pat, text)
            result[key] = self.decode_hex_escapes(m.group(1)) if m else None
        return result

    def check(self, cookies_list):
        """
        Kiểm tra một danh sách cookies.
        Trả về: (True/False, info_dict)
        """
        self.session.cookies.clear()
        for cookie in cookies_list:
            self.session.cookies.set(cookie["name"], cookie["value"], domain=cookie.get("domain", ".netflix.com"))

        url = "https://www.netflix.com/YourAccount"
        try:
            response = self.session.get(url, timeout=20, allow_redirects=True)
            if response.status_code != 200:
                return False, {"error": f"HTTP {response.status_code}"}

            content = response.text
            soup = BeautifulSoup(content, "lxml")

            # Check if logged in
            if soup.find(string=re.compile("Sign In", re.I)) or "netflix.com/login" in response.url:
                return False, {"error": "Cookie expired or invalid"}

            info = self.extract_info(content)
            
            # Extra-membership check
            try:
                em_resp = self.session.get(
                    "https://www.netflix.com/accountowner/addextramember",
                    allow_redirects=False,
                    timeout=15,
                )
                extra_member = (em_resp.status_code == 200)
            except:
                extra_member = False

            # Plan detection
            plan = info.get("localizedPlanName")
            if plan:
                plan = plan.replace("miembro\xa0extra", "(Shared Extra Member)")
            else:
                page_text = soup.get_text()
                for candidate in ("Premium", "Standard", "Basic"):
                    if candidate in page_text:
                        plan = candidate
                        break
                else:
                    plan = "Unknown"

            # Email detection
            email = info.get("emailAddress")
            if not email:
                el = soup.select_one(".account-section-email")
                email = el.text.strip() if el else "Unknown"

            # Country detection
            country = info.get("countryOfSignup") or "Unknown"

            return True, {
                "plan": plan,
                "email": email,
                "country": country,
                "extra_member": extra_member
            }

        except (RequestException, ConnectionError, RemoteDisconnected) as e:
            return False, {"error": str(e)}
        except Exception as e:
            logger.error(f"Lỗi không xác định khi check Netflix: {e}")
            return False, {"error": "Internal Error"}
