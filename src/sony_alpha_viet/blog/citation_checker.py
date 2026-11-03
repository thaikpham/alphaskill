
import os
import re
import urllib.request
import urllib.error
from typing import Dict
from urllib.parse import urlparse

TIER_1_DOMAINS = ["sony.com", "sony.co.jp", "alphauniverse.com", "imaging-edge.sony.net"]
TIER_2_DOMAINS = ["dpreview.com", "petapixel.com", "sonyalpharumors.com", "thephoblographer.com", "digitalcameraworld.com"]
TIER_3_DOMAINS = ["facebook.com", "youtube.com", "instagram.com"]

def classify_domain(url: str) -> str:
    try:
        domain = urlparse(url).netloc.lower()
        for d in TIER_1_DOMAINS:
            if d in domain:
                return "Tier 1 - Chinh thong Sony (tot nhat cho AIO)"
        for d in TIER_2_DOMAINS:
            if d in domain:
                return "Tier 2 - Uy tin nganh anh"
        for d in TIER_3_DOMAINS:
            if d in domain:
                return "Tier 3 - Social"
        return "Tier 3 - Blog/shop khac"
    except:
        return "Khong xac dinh"

def check_link_alive(url: str, timeout=3) -> Dict:
    if os.environ.get("SONY_VN_NO_NET"):  # public server: never fetch URLs taken from a caller's text
        return {"alive": None, "status": None, "evidence": "Không kiểm link trên server công khai"}
    try:
        req = urllib.request.Request(url, method='HEAD', headers={'User-Agent': 'SonyAlphaVietBot/1.1'})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return {"alive": True, "status": resp.status, "evidence": f"Status {resp.status}"}
    except urllib.error.HTTPError as e:
        if e.code in (403, 429):
            return {"alive": True, "status": e.code, "evidence": f"Bi chan {e.code} nhung link ton tai"}
        return {"alive": False, "status": e.code, "evidence": f"Chet {e.code}"}
    except Exception as e:
        return {"alive": None, "status": None, "evidence": f"Khong check duoc (offline): {str(e)[:60]}"}

def citation_checker(text: str) -> Dict:
    md_links = re.findall(r'\[.*?\]\(https?://[^)]+\)', text)
    # extract url inside ()
    md_urls = []
    for m in md_links:
        url_match = re.search(r'(https?://[^)]+)', m)
        if url_match:
            md_urls.append(url_match.group(1))
    raw_links = re.findall(r'https?://[^\s\)\]]+', text)
    all_links = list(dict.fromkeys(md_urls + raw_links))
    
    if not all_links:
        return {
            "total_links": 0,
            "score": 0,
            "verdict": "Khong co link nguon nao - AIO se khong trich",
            "fix": "Them it nhat 1 link Sony official + 1 link DPReview",
            "details": []
        }
    
    details = []
    tier1_count = 0
    alive_count = 0
    dead_count = 0
    
    for url in all_links[:15]:
        tier = classify_domain(url)
        alive_info = check_link_alive(url)
        if "Tier 1" in tier:
            tier1_count += 1
        if alive_info["alive"] is True:
            alive_count += 1
        elif alive_info["alive"] is False:
            dead_count += 1
        
        details.append({
            "url": url[:80],
            "tier": tier,
            "alive": alive_info["alive"],
            "evidence": alive_info["evidence"]
        })
    
    has_specs = bool(re.search(r'\d+MP|33MP|61MP|\d+\s*trieu', text))
    has_source_sentence = bool(re.search(r'nguon:|source:|theo Sony|theo DPReview', text, re.IGNORECASE))
    
    score = 0
    if tier1_count >= 1: score += 40
    if len(details) > 0 and alive_count >= len(details)*0.8: score += 30
    if has_source_sentence: score += 20
    if len(all_links) >= 2: score += 10
    
    if score >= 80:
        verdict = "Tot - Co nguon Tier 1, link song"
    elif score >= 50:
        verdict = "Trung binh - Can them 1 link Sony official"
    else:
        verdict = "Kem - Thieu nguon chinh thong"
    
    return {
        "total_links": len(all_links),
        "tier1_count": tier1_count,
        "alive": alive_count,
        "dead": dead_count,
        "has_specs_needs_source": has_specs,
        "has_source_sentence": has_source_sentence,
        "score": score,
        "verdict": verdict,
        "details": details,
        "fix": "Them link Sony official spec, ghi '(nguon: Sony official 2024)' sau thong so" if not has_source_sentence else ""
    }
