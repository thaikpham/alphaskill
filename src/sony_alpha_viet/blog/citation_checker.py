
import os
import re
import socket
import ipaddress
import urllib.request
import urllib.error
from typing import Dict
from urllib.parse import urlparse

from ._doc import as_article, band, fold, links


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # surfaces 3xx as HTTPError instead of following it


_NO_REDIRECT = urllib.request.build_opener(_NoRedirect)

TIER_1_DOMAINS = ["sony.com", "sony.com.vn", "sony.co.jp", "alphauniverse.com", "imaging-edge.sony.net"]
TIER_2_DOMAINS = ["dpreview.com", "petapixel.com", "sonyalpharumors.com", "thephoblographer.com", "digitalcameraworld.com"]
TIER_3_DOMAINS = ["facebook.com", "youtube.com", "instagram.com"]

def classify_domain(url: str) -> str:
    try:
        host = urlparse(url).netloc.lower().split(":")[0]  # strip port
        for d in TIER_1_DOMAINS:
            if host == d or host.endswith("." + d):
                return "Tier 1 - Chính thống Sony (tốt nhất cho AIO)"
        for d in TIER_2_DOMAINS:
            if host == d or host.endswith("." + d):
                return "Tier 2 - Uy tín ngành ảnh"
        for d in TIER_3_DOMAINS:
            if host == d or host.endswith("." + d):
                return "Tier 3 - Mạng xã hội"
        return "Tier 3 - Blog/shop khác"
    except (ValueError, AttributeError, TypeError):
        return "Không xác định"

def check_link_alive(url: str, timeout=5) -> Dict:
    """HEAD tới url. alive: True (sống), False (chết 4xx), None (không kiểm được, không tính là chết)."""
    if os.environ.get("SONY_VN_NO_NET"):  # public server: never fetch URLs taken from a caller's text
        return {"alive": None, "status": None, "evidence": "Không kiểm link trên server công khai"}
    try:
        parsed = urlparse(url)
        scheme = parsed.scheme.lower()
        if scheme not in ("http", "https"):
            return {"alive": None, "status": None, "evidence": f"Lược đồ không hỗ trợ: {scheme}"}

        host = parsed.hostname or ""
        try:
            addrs = socket.getaddrinfo(host, None)
            for family, socktype, proto, canonname, sockaddr in addrs:
                ip_str = sockaddr[0]
                ip = ipaddress.ip_address(ip_str)
                if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                    return {"alive": None, "status": None, "evidence": f"Không cho phép địa chỉ {ip_str}"}
        except (socket.gaierror, ValueError):
            return {"alive": None, "status": None, "evidence": f"Không kiểm được: không phân giải hostname {host}"}

        req = urllib.request.Request(url, method='HEAD', headers={'User-Agent': 'SonyAlphaVietBot/1.1'})
        with _NO_REDIRECT.open(req, timeout=timeout) as resp:
            return {"alive": True, "status": resp.status, "evidence": f"Status {resp.status}"}
    except urllib.error.HTTPError as e:
        if 300 <= e.code < 400:
            location = e.headers.get('Location', '?')[:80]
            return {"alive": True, "status": e.code, "evidence": f"Chuyển hướng {e.code} -> {location}"}
        if e.code in (403, 429):
            return {"alive": True, "status": e.code, "evidence": f"Bị chặn {e.code} nhưng link tồn tại"}
        if e.code in (405, 501) or e.code >= 500:  # server không nhận HEAD hoặc đang lỗi: chưa biết
            return {"alive": None, "status": e.code, "evidence": f"Không kiểm được: máy chủ trả {e.code}"}
        return {"alive": False, "status": e.code, "evidence": f"Chết {e.code}"}
    except Exception as e:
        return {"alive": None, "status": None, "evidence": f"Không kiểm được (lỗi mạng): {str(e)[:60]}"}

def _verdict(score: int, tier1: int) -> str:
    if tier1 == 0:
        note = "Thiếu nguồn Sony official (Tier 1)"
    elif score >= 80:
        note = "Có nguồn Tier 1"
    else:
        note = "Cần bổ sung nguồn"
    return f"{band(score)} - {note}"

def citation_checker(text: str, check_links: bool = True) -> Dict:
    """
    Tool MCP: citation_checker
    check_links=True: HEAD từng link (timeout 5s). False: chỉ chấm domain và câu nguồn, quy về thang 100 trên 70 điểm.
    Link không kiểm được (offline, lỗi mạng, 5xx, 405) không bị coi là chết và không được cộng điểm.
    """
    # Nguồn ngoài only: link nội bộ (alphacolorlab.com, đường dẫn tương đối, placeholder) không phải nguồn trích dẫn
    found = [x for x in links(as_article(text)) if not x["internal"]]
    line_of = {x["url"]: x["line"] for x in found}
    all_links = [x["url"] for x in found]

    if not all_links:
        return {
            "total_links": 0,
            "tier1_count": 0,
            "alive": 0,
            "dead": 0,
            "unverified": 0,
            "link_check": "không có link",
            "score": 0,
            "verdict": f"{band(0)} - Không có link nguồn nào, AIO sẽ không trích dẫn",
            "fix": "Thêm ít nhất 1 link Sony official + 1 link DPReview",
            "details": []
        }

    details = []
    tier1_count = 0
    for url in all_links[:15]:
        tier = classify_domain(url)
        if "Tier 1" in tier:
            tier1_count += 1
        if check_links:
            alive_info = check_link_alive(url, timeout=5)
        else:
            alive_info = {"alive": None, "status": None, "evidence": "Bỏ qua (check_links=False)"}
        details.append({
            "url": url[:80],
            "line": line_of[url],
            "tier": tier,
            "alive": alive_info["alive"],
            "evidence": alive_info["evidence"]
        })

    checked = [d for d in details if d["alive"] is not None]
    alive_count = sum(1 for d in checked if d["alive"] is True)
    dead_count = sum(1 for d in details if d["alive"] is False)
    unverified = len(details) - len(checked)

    folded = fold(text)
    has_specs = bool(re.search(r'\d+\s?mp|\d+\s*trieu', folded))
    has_source_sentence = bool(re.search(r'nguon:|source:|theo sony|theo dpreview', folded))

    # Điểm nguồn: Tier 1 40, câu nguồn 20, từ 2 link 10; link sống 30 chỉ khi có link kiểm được
    raw = 0
    if tier1_count >= 1: raw += 40
    if has_source_sentence: raw += 20
    if len(all_links) >= 2: raw += 10
    link_known = bool(checked)
    if link_known:
        if alive_count >= len(checked) * 0.8: raw += 30
        max_score = 100
        link_check = "đã kiểm" if not unverified else f"không kiểm được {unverified}/{len(details)} link"
    else:
        max_score = 70
        link_check = ("bỏ qua link (check_links=False)" if not check_links else "không kiểm được link") + ", chấm trên 70 điểm nguồn"
    score = round(raw * 100 / max_score)

    fixes = []
    if tier1_count == 0:
        fixes.append("Thêm link Sony official (sony.com.vn, sony.com)")
    if not has_source_sentence:
        fixes.append("ghi '(nguồn: Sony official, [năm])' sau thông số")

    return {
        "total_links": len(all_links),
        "tier1_count": tier1_count,
        "alive": alive_count,
        "dead": dead_count,
        "unverified": unverified,
        "link_check": link_check,
        "has_specs_needs_source": has_specs,
        "has_source_sentence": has_source_sentence,
        "score": score,
        "verdict": _verdict(score, tier1_count),
        "details": details,
        "fix": "; ".join(fixes),
    }
