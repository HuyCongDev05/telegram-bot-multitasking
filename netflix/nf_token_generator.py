"""Create Netflix app-login links from stored Netflix cookies."""

from __future__ import annotations

import json
import urllib.parse
import uuid

import requests
from urllib3.exceptions import InsecureRequestWarning

from .cookie_utils import REQUIRED_COOKIES, build_cookie_header, extract_cookie_dict, validate_netflix_cookie

_MOD_SIG = "687579636f6e676465763035"


IOS_API_URL = "https://ios.prod.ftl.netflix.com/iosui/user/15.48"
IOS_QUERY_PARAMS = {
    "appVersion": "15.48.1",
    "config": '{"gamesInTrailersEnabled":"false","isTrailersEvidenceEnabled":"false","cdsMyListSortEnabled":"true","kidsBillboardEnabled":"true","addHorizontalBoxArtToVideoSummariesEnabled":"false","skOverlayTestEnabled":"false","homeFeedTestTVMovieListsEnabled":"false","baselineOnIpadEnabled":"true","trailersVideoIdLoggingFixEnabled":"true","postPlayPreviewsEnabled":"false","bypassContextualAssetsEnabled":"false","roarEnabled":"false","useSeason1AltLabelEnabled":"false","disableCDSSearchPaginationSectionKinds":["searchVideoCarousel"],"cdsSearchHorizontalPaginationEnabled":"true","searchPreQueryGamesEnabled":"true","kidsMyListEnabled":"true","billboardEnabled":"true","useCDSGalleryEnabled":"true","contentWarningEnabled":"true","videosInPopularGamesEnabled":"true","avifFormatEnabled":"false","sharksEnabled":"true"}',
    "device_type": "NFAPPL-02-",
    "esn": "NFAPPL-02-IPHONE8%3D1-PXA-02026U9VV5O8AUKEAEO8PUJETCGDD4PQRI9DEB3MDLEMD0EACM4CS78LMD334MN3MQ3NMJ8SU9O9MVGS6BJCURM1PH1MUTGDPF4S4200",
    "idiom": "phone",
    "iosVersion": "15.8.5",
    "isTablet": "false",
    "languages": "en-US",
    "locale": "en-US",
    "maxDeviceWidth": "375",
    "model": "saget",
    "modelType": "IPHONE8-1",
    "odpAware": "true",
    "path": '["account","token","default"]',
    "pathFormat": "graph",
    "pixelDensity": "2.0",
    "progressive": "false",
    "responseFormat": "json",
}
IOS_HEADERS = {
    "User-Agent": "Argo/15.48.1 (iPhone; iOS 15.8.5; Scale/2.00)",
    "x-netflix.request.attempt": "1",
    "x-netflix.request.client.user.guid": "A4CS633D7VCBPE2GPK2HL4EKOE",
    "x-netflix.context.profile-guid": "A4CS633D7VCBPE2GPK2HL4EKOE",
    "x-netflix.request.routing": '{"path":"/nq/mobile/nqios/~15.48.0/user","control_tag":"iosui_argo"}',
    "x-netflix.context.app-version": "15.48.1",
    "x-netflix.argo.translated": "true",
    "x-netflix.context.form-factor": "phone",
    "x-netflix.context.sdk-version": "2012.4",
    "x-netflix.client.appversion": "15.48.1",
    "x-netflix.context.max-device-width": "375",
    "x-netflix.context.ab-tests": "",
    "x-netflix.tracing.cl.useractionid": "4DC655F2-9C3C-4343-8229-CA1B003C3053",
    "x-netflix.client.type": "argo",
    "x-netflix.client.ftl.esn": "NFAPPL-02-IPHONE8=1-PXA-02026U9VV5O8AUKEAEO8PUJETCGDD4PQRI9DEB3MDLEMD0EACM4CS78LMD334MN3MQ3NMJ8SU9O9MVGS6BJCURM1PH1MUTGDPF4S4200",
    "x-netflix.context.locales": "en-US",
    "x-netflix.context.top-level-uuid": "90AFE39F-ADF1-4D8A-B33E-528730990FE3",
    "x-netflix.client.iosversion": "15.8.5",
    "accept-language": "en-US;q=1",
    "x-netflix.argo.abtests": "",
    "x-netflix.context.os-version": "15.8.5",
    "x-netflix.request.client.context": '{"appState":"foreground"}',
    "x-netflix.context.ui-flavor": "argo",
    "x-netflix.argo.nfnsm": "9",
    "x-netflix.context.pixel-density": "2.0",
    "x-netflix.request.toplevel.uuid": "90AFE39F-ADF1-4D8A-B33E-528730990FE3",
    "x-netflix.request.client.timezoneid": "Asia/Dhaka",
}

ANDROID_API_URL = "https://android13.prod.ftl.netflix.com/graphql?netka=true"
ANDROID_HEADERS = {
    "User-Agent": "com.netflix.mediaclient/63884 (Linux; U; Android 13; ro; M2007J3SG; Build/TQ1A.230205.001.A2; Cronet/143.0.7445.0)",
    "Accept": "multipart/mixed;deferSpec=20220824, application/graphql-response+json, application/json",
    "Content-Type": "application/json",
    "X-Netflix.client.type": "ANDROID",
}
ANDROID_PAYLOAD = {
    "operationName": "CreateAutoLoginToken",
    "variables": {"scope": "WEBVIEW_MOBILE_STREAMING"},
    "extensions": {
        "persistedQuery": {
            "version": 102,
            "id": "76e97129-f4b5-41a0-a73c-12e674896849",
        }
    },
}

requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)


def _build_proxies(proxy_url: str | None) -> dict | None:
    if not proxy_url:
        return None
    return {"http": proxy_url, "https": proxy_url}


def _normalize_expiry(expires):
    if isinstance(expires, int) and len(str(expires)) == 13:
        return expires // 1000
    return expires


def _summarize_ios_response(data: dict) -> str:
    value = data.get("value")
    if isinstance(value, dict):
        value_keys = ",".join(sorted(value.keys()))
        return f"response value keys: {value_keys or 'none'}"
    if data:
        top_keys = ",".join(sorted(data.keys()))
        return f"response keys: {top_keys or 'none'}"
    return "empty JSON response"


def _fetch_ios_nftoken(cookie_header: str, proxies: dict | None):
    headers = dict(IOS_HEADERS)
    headers["Cookie"] = cookie_header

    response = requests.get(
        IOS_API_URL,
        params=IOS_QUERY_PARAMS,
        headers=headers,
        proxies=proxies,
        timeout=30,
        verify=False,
    )
    response.raise_for_status()

    data = response.json()
    token_data = (
        (((data.get("value") or {}).get("account") or {}).get("token") or {}).get("default")
        or {}
    )
    token = token_data.get("token")
    expires = _normalize_expiry(token_data.get("expires"))
    if token:
        return token, expires

    raise ValueError(_summarize_ios_response(data))


def _fetch_android_nftoken(cookie_header: str, proxies: dict | None):
    headers = dict(ANDROID_HEADERS)
    headers["X-Netflix.client.request.id"] = str(uuid.uuid4())
    headers["X-Netflix.request.client.user.agent"] = ANDROID_HEADERS["User-Agent"]
    headers["Cookie"] = cookie_header

    response = requests.post(
        ANDROID_API_URL,
        headers=headers,
        json=ANDROID_PAYLOAD,
        proxies=proxies,
        timeout=30,
    )
    response.raise_for_status()

    data = response.json()
    token = (data.get("data") or {}).get("createAutoLoginToken")
    if token:
        return token, None

    errors = data.get("errors")
    if errors:
        raise ValueError(json.dumps(errors, ensure_ascii=True))

    top_keys = ",".join(sorted(data.keys())) if isinstance(data, dict) else "non-dict"
    raise ValueError(f"response keys: {top_keys}")


def fetch_nftoken(
    cookie_dict: dict[str, str],
    proxy_url: str | None = None,
    include_expiry: bool = False,
):
    missing = [name for name in REQUIRED_COOKIES if not cookie_dict.get(name)]
    if missing:
        raise ValueError("Missing required cookies: " + ", ".join(missing))

    cookie_header = build_cookie_header(cookie_dict)
    proxies = _build_proxies(proxy_url)

    ios_error = None
    try:
        token, expires = _fetch_ios_nftoken(cookie_header, proxies)
        return (token, expires) if include_expiry else token
    except (requests.RequestException, ValueError) as exc:
        ios_error = str(exc)

    try:
        token, expires = _fetch_android_nftoken(cookie_header, proxies)
        return (token, expires) if include_expiry else token
    except requests.RequestException:
        raise
    except ValueError as exc:
        raise ValueError(f"No token found. iOS: {ios_error}. Android: {exc}") from exc


def build_nftoken_link(token: str) -> str:
    encoded_token = urllib.parse.quote(token, safe="")
    return "https://netflix.com/?nftoken=" + encoded_token


def generate_nftoken(cookie_text: str, proxy_url: str = None) -> str:
    is_valid, error_msg = validate_netflix_cookie(cookie_text)
    if not is_valid:
        raise ValueError(error_msg)

    cookie_dict = extract_cookie_dict((cookie_text or "").strip())
    token = fetch_nftoken(cookie_dict, proxy_url=proxy_url)
    return build_nftoken_link(token)
