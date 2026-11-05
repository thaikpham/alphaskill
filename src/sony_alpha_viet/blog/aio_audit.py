
"""
aio_audit.py - Tool chấm điểm AIO-first (35 tiêu chí, tập trung 15 core + 10 schema)
Dùng cho MCP server sony-alpha-viet

Cách dùng:
  aio_audit(text, primary_keyword) -> dict với score, bảng chi tiết, gợi ý sửa

Không cần internet, chỉ phân tích text.
"""

import re
from pathlib import Path
from typing import Dict

def count_words(s: str) -> int:
    return len(s.split())

def has_tldr(text: str) -> Dict:
    """Check TL;DR 40-70 từ ngay dưới H1"""
    # Tìm H1
    h1_match = re.search(r'^#\s+.+', text, re.MULTILINE)
    if not h1_match:
        return {"pass": False, "evidence": "Không tìm thấy H1", "fix": "Thêm H1 với từ khóa chính"}
    # Lấy 500 ký tự sau H1
    after_h1 = text[h1_match.end():h1_match.end()+1000]
    # Tìm đoạn TL;DR hoặc đoạn đầu 40-70 từ
    tldr_match = re.search(r'(TL;DR|Tóm tắt|Tóm lại)[:\s]*(.+?)(\n\n|\n#)', after_h1, re.IGNORECASE | re.DOTALL)
    if tldr_match:
        words = count_words(tldr_match.group(2))
        if 40 <= words <= 70:
            return {"pass": True, "evidence": f"TL;DR {words} từ: {tldr_match.group(2)[:80]}...", "fix": ""}
        else:
            return {"pass": False, "evidence": f"TL;DR có {words} từ, cần 40-70", "fix": "Rút gọn/mở rộng TL;DR về 40-70 từ, trả lời thẳng câu hỏi chính"}
    # Fallback: đoạn đầu sau H1
    first_para = after_h1.strip().split("\n\n")[0]
    words = count_words(first_para)
    if 40 <= words <= 70:
        return {"pass": True, "evidence": f"Đoạn đầu {words} từ, có thể dùng làm TL;DR", "fix": "Thêm nhãn TL;DR: ở đầu"}
    return {"pass": False, "evidence": f"Không có TL;DR, đoạn đầu {words} từ", "fix": "Thêm TL;DR 40-70 từ ngay dưới H1, trả lời thẳng: A7 IV tốt cho... A7R V tốt cho..."}

def check_h2_self_contained(text: str) -> Dict:
    h2s = re.findall(r'^##\s+(.+?)\n+(.+?)(?=\n##|\Z)', text, re.MULTILINE | re.DOTALL)
    if not h2s:
        return {"pass": False, "evidence": "Không có H2", "fix": "Thêm ít nhất 3 H2"}
    fails = []
    for title, content in h2s[:5]:
        first_sent = content.strip().split(".")[0]
        if len(first_sent.split()) < 10:
            fails.append(title)
        # Check mở bằng "Trong phần này", "Hãy cùng"
        if re.search(r'^(Trong phần này|Hãy cùng|Ở phần này|Bài viết này)', content.strip(), re.IGNORECASE):
            fails.append(f"{title} (mở bằng văn AI-sounding)")
    if not fails:
        return {"pass": True, "evidence": f"{len(h2s)} H2 đều mở bằng câu trả lời tự đứng được", "fix": ""}
    return {"pass": False, "evidence": f"H2 lỗi: {', '.join(fails[:3])}", "fix": "Mỗi H2 mở bằng 1-2 câu trả lời thẳng, không dùng 'Trong phần này...'"}

def check_faq(text: str) -> Dict:
    faq_section = re.search(r'(FAQ|Câu hỏi thường gặp)(.+?)(?=\n#|\Z)', text, re.IGNORECASE | re.DOTALL)
    if not faq_section:
        return {"pass": False, "evidence": "Không có FAQ", "fix": "Thêm FAQ 3-6 câu, mỗi đáp 40-70 từ, tự đứng được"}

    faq_text = faq_section.group(0)
    # Parse FAQ: questions are bold lines or headings ending with ?, answers until next question/heading
    questions = []
    # Match bold lines: **...?** or ### ...?
    q_lines = re.findall(r'(?:\*\*(.+?)\*\*|###\s+(.+?))\s*\?', faq_text, re.IGNORECASE | re.MULTILINE)
    if q_lines:
        questions = [(q[0] or q[1]) for q in q_lines]
    else:
        # Fallback: count lines ending with ?
        q_count = faq_text.count('?')
        if q_count < 3:
            return {"pass": False, "evidence": f"FAQ chỉ có {q_count} câu", "fix": "Thêm 3-6 câu hỏi người dùng thật sự gõ"}
        questions = [None] * q_count  # placeholder for count

    if len(questions) < 3:
        return {"pass": False, "evidence": f"FAQ chỉ có {len(questions)} câu", "fix": "Thêm 3-6 câu hỏi người dùng thật sự gõ"}

    # Parse Q/A pairs and check word count + forbidden phrases
    failing = []
    # Match all question/answer pairs: **Q?** or ### Q? followed by answer text
    qa_matches = re.finditer(r'\*\*(.+?\?)\*\*\s*(.*?)(?=\*\*|###|$)', faq_text, re.DOTALL)
    for match in qa_matches:
        q_text = match.group(1).rstrip('?').strip()
        a_text = match.group(2).strip()

        word_count = count_words(a_text)
        has_forbidden = re.search(r'(xem ở trên|như đã nói|đã đề cập|xem o tren|nhu da noi)', a_text, re.IGNORECASE)

        if not (40 <= word_count <= 70):
            failing.append(f"{q_text}? ({word_count} từ)")
        if has_forbidden:
            failing.append(f"{q_text}? (có 'xem ở trên'/'như đã nói')")

    # Also check ### heading format
    heading_qa = re.finditer(r'###\s+(.+?\?)\s*(.*?)(?=###|$)', faq_text, re.DOTALL)
    for match in heading_qa:
        q_text = match.group(1).rstrip('?').strip()
        a_text = match.group(2).strip()

        word_count = count_words(a_text)
        has_forbidden = re.search(r'(xem ở trên|như đã nói|đã đề cập|xem o tren|nhu da noi)', a_text, re.IGNORECASE)

        if not (40 <= word_count <= 70):
            failing.append(f"{q_text}? ({word_count} từ)")
        if has_forbidden:
            failing.append(f"{q_text}? (có 'xem ở trên'/'như đã nói')")

    if failing:
        return {"pass": False, "evidence": f"FAQ lỗi: {failing[0]}", "fix": "Viết lại FAQ để mỗi đáp 40-70 từ, tự đứng được"}

    return {"pass": True, "evidence": f"FAQ có {len(questions)} câu, tự đứng được", "fix": ""}

def check_table(text: str) -> Dict:
    # Check for real markdown table: header row | separator row | data rows
    # Separator row: ^\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)+\|?\s*$
    lines = text.split('\n')
    for i in range(len(lines) - 1):
        header = lines[i].strip()
        separator = lines[i + 1].strip()
        # Check if header is a pipe-delimited row
        if header.startswith('|') and '|' in header:
            # Check if next line is a separator matching pattern
            if re.match(r'^\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)+\|?\s*$', separator):
                header_text = header.strip('|').split('|')[0].strip()
                return {"pass": True, "evidence": f"Có bảng so sánh (header: {header_text})", "fix": ""}
    return {"pass": False, "evidence": "Không có bảng", "fix": "Thêm bảng | Tiêu chí | A7 IV | A7R V | cho bài so sánh"}

def check_ai_sounding(text: str) -> Dict:
    banned = ["Hãy cùng khám phá", "đưa trải nghiệm lên tầm cao mới", "tối ưu hóa trải nghiệm", "không chỉ.*mà còn", "vô cùng quan trọng"]
    found = []
    for phrase in banned:
        if re.search(phrase, text, re.IGNORECASE):
            found.append(phrase)
    if not found:
        return {"pass": True, "evidence": "Không có cụm AI-sounding", "fix": ""}
    return {"pass": False, "evidence": f"Có cụm AI-sounding: {', '.join(found)}", "fix": "Bỏ cụm sáo rỗng, viết trực tiếp"}

def check_placeholder(text: str) -> Dict:
    if "[cần xác minh]" in text or "[can xac minh]" in text.lower():
        return {"pass": False, "evidence": "Còn placeholder [cần xác minh]", "fix": "Thay bằng số liệu thật có nguồn Sony official, hoặc bỏ câu đó"}
    return {"pass": True, "evidence": "Không có placeholder", "fix": ""}

def check_entity(text: str, keyword: str) -> Dict:
    # Kiểm tra keyword có kèm brand/model
    if keyword.lower() not in text.lower():
        return {"pass": False, "evidence": f"Thiếu từ khóa chính {keyword}", "fix": f"Thêm {keyword} vào H1, 100 từ đầu, 1 H2"}
    # Entity: Sony + full-frame + MP
    has_sony = "sony" in text.lower()
    has_specs = bool(re.search(r'\d+MP|full-frame|IBIS|Eye AF', text, re.IGNORECASE))
    if has_sony and has_specs:
        return {"pass": True, "evidence": "Có entity Sony + thông số", "fix": ""}
    return {"pass": False, "evidence": "Thiếu entity", "fix": "Mỗi lần nhắc model, kèm brand + thông số: Sony A7 IV (full-frame 33MP)"}

def aio_audit(text: str, primary_keyword: str = "") -> Dict:
    """
    Tool MCP: aio_audit
    Input: text (markdown bài viết), primary_keyword
    Output: dict với score, bảng chi tiết
    """
    checks = {
        "11 TL;DR 40-70 từ": has_tldr(text),
        "12 H2 mở bằng câu tự đứng": check_h2_self_contained(text),
        "14 FAQ 3-6 câu tự đứng": check_faq(text),
        "15 Có bảng so sánh": check_table(text),
        "17 Không placeholder [cần xác minh]": check_placeholder(text),
        "21 Không AI-sounding": check_ai_sounding(text),
        "22 Entity rõ ràng": check_entity(text, primary_keyword),
        # Thêm các check đơn giản khác
        "13 Định nghĩa 1 câu": {"pass": bool(re.search(r'.* là .*\.', text)), "evidence": "Có câu định nghĩa dạng 'X là...'", "fix": "Thêm định nghĩa 1 câu cho thuật ngữ mới"},
        "19 Ví dụ thực tế VN": {"pass": "Việt Nam" in text or "HCM" in text or "Hà Nội" in text, "evidence": "Có ví dụ VN" if ("Việt Nam" in text or "HCM" in text) else "Thiếu ví dụ VN", "fix": "Thêm ví dụ thợ cưới ở HCM/HN"},
        "23 Freshness 11/2026": {"pass": "2026" in text or "Cập nhật" in text, "evidence": "Có năm/cập nhật", "fix": "Thêm dòng Cập nhật 11/2026: giá hiện tại..."},
    }

    passed = sum(1 for v in checks.values() if v["pass"])
    total = len(checks)
    score = int(passed / total * 100)

    # Dự đoán khả năng được AI Overviews trích
    if score >= 80:
        verdict = "Đạt - có TL;DR, FAQ, bảng để AI trích"
    elif score >= 60:
        verdict = "Trung bình - cần thêm bảng, FAQ tự đứng"
    else:
        verdict = "Thấp - thiếu TL;DR, FAQ, bảng"

    table = []
    for name, res in checks.items():
        table.append({
            "Mục": name,
            "Kết quả": "✅ Đạt" if res["pass"] else "❌ Chưa",
            "Bằng chứng": res["evidence"][:100],
            "Cách sửa": res["fix"]
        })

    return {
        "aio_score": score,
        "passed": f"{passed}/{total}",
        "verdict": verdict,
        "table": table,
        "primary_keyword": primary_keyword
    }

# Để test nhanh
if __name__ == "__main__":
    sample = open("/tmp/test.md").read() if Path("/tmp/test.md").exists() else "# Test\n\nNo TLDR"
    print(aio_audit(sample, "Sony A7 IV"))
