"""alphaskill Markdown <-> Alpha ColorLab Article (blog/colorlab.py)."""
import json
from pathlib import Path

from sony_alpha_viet.blog.colorlab import article_to_md, check, md_to_article, slugify, write_pack

ROOT = Path(__file__).resolve().parent.parent
FIX = Path(__file__).parent / "fixtures"
SITE = json.loads((FIX / "colorlab-site-articles.json").read_text(encoding="utf-8"))


def test_slugify_matches_site():
    assert slugify("Lấy nét bằng ngón tay cái") == "lay-net-bang-ngon-tay-cai"
    assert slugify("  Đèn LED: ổn định? ") == "den-led-on-dinh"
    long = slugify("Chế độ ưu tiên khẩu độ " * 5)
    assert len(long) <= 60 and not long.endswith("-")


def test_site_articles_round_trip():
    for a in SITE:
        back = md_to_article(article_to_md(a))["article"]
        want = {**a, "meta": {"section": None, "order": None, **a["meta"]}}
        want.pop("updatedAt", None)
        assert back == want, a["id"]


def test_check_agrees_with_site_gate():
    codes = {a["id"]: check(a) for a in SITE}
    assert codes["back-button-af"] == ["noSource"]           # authored, publishable; packs need a source
    assert codes["white-balance-shift"] == []
    assert "placeholder" in codes["so-sanh-hai-cau-hinh-cung-canh"]


def test_alphaskill_post_converts_clean():
    r = md_to_article((FIX / "colorlab-post.md").read_text(encoding="utf-8"))
    a = r["article"]
    assert r["problems"] == []
    assert [b["t"] for b in a["blocks"]] == ["tldr", "p", "h", "menu", "menu", "callout", "h", "p", "table",
                                              "compare", "h", "p", "checklist"]
    assert a["id"] == "lay-net-bang-ngon-tay-cai" and a["title"].startswith("Lấy nét")
    assert a["blocks"][0]["items"][0] == "Gán AF On cho nút AEL (hoặc C1), rồi tắt AF w/ Shutter."
    assert a["blocks"][3]["old"].startswith("MENU → Camera Settings2")
    assert a["blocks"][-1]["label"] == "Sau khi đổi, kiểm tra lại"
    assert a["meta"]["sources"] == [{"url": "https://helpguide.sony.net/ilc/2110/v1/en/index.html",
                                     "title": "ILCE-7M4 Help Guide", "publisher": "Sony", "checkedAt": "2026-11-02"}]
    assert a["meta"]["authorName"] == "Thai Pham" and "status" not in a


def test_example_post_reports_site_problems():
    r = md_to_article((ROOT / "skills/sony-alpha-viet/examples/example-blog-post.md").read_text(encoding="utf-8"))
    assert {"tableRows", "unverified", "mustCloseWithChecklistOrFigure"} <= set(r["problems"])


def _fake_site(tmp_path, packs="{}"):
    d = tmp_path / "src/lib/lab/packs"
    d.mkdir(parents=True)
    (d / "index.ts").write_text("import type { Article } from '../types'\n\n"
                                f"export const PACKS: Readonly<Record<string, readonly Article[]>> = {packs}\n")
    return d


def test_write_pack_registers(tmp_path):
    d = _fake_site(tmp_path)
    a = md_to_article((FIX / "colorlab-post.md").read_text(encoding="utf-8"))
    r = write_pack([a], str(tmp_path), "trainer-af", check_gate=False)
    assert r["ok"], r
    idx = (d / "index.ts").read_text()
    assert "import { trainerAf } from './trainer-af'" in idx and "{ 'trainer-af': trainerAf }" in idx
    assert '"id": "lay-net-bang-ngon-tay-cai"' in (d / "trainer-af.ts").read_text()
    assert write_pack([a], str(tmp_path), "trainer-af", check_gate=False)["problems"][0].startswith("packExists")
    assert write_pack([a], str(tmp_path), "trainer-af", overwrite=True, check_gate=False)["ok"]
    assert (d / "index.ts").read_text().count("'trainer-af': trainerAf") == 1


def test_write_pack_appends_and_refuses(tmp_path):
    d = _fake_site(tmp_path, "{\n  'old': old,\n}")
    assert write_pack([SITE[0]], str(tmp_path), "new-pack", check_gate=False)["ok"]
    assert "{\n  'new-pack': newPack,\n  'old': old," in (d / "index.ts").read_text()
    assert write_pack([], str(tmp_path), "Bad_Name", check_gate=False)["problems"] == ["packName"]
    assert not write_pack([], str(tmp_path / "nope"), "x", check_gate=False)["ok"]
