"""T-013 — UI 静的検査: 導入文・誠実さ注記・フリート標準固定フッタ(F-08/F-10)。

期待値の出所:
- 導入文: SPEC F-08 の要求文言(本プロジェクト向けに author 済み)
- フッタ: フリート慣例(midashi-sanmenkyo R/footer.R の並び・mugen-tape T-019 の先例)。
  リンク先(GitHub リポジトリ・アーティファクト)は実在を確認してから期待値化する
  (mugen-tape HC-001 の規律)。到達性まではここでは検証しない。
"""
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]


@pytest.mark.unit
def test_t013_intro_and_honesty():
    """T-013a: 導入 2 節と誠実さ注記・停止でなく確率の注記が掲出されている。"""
    html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
    assert "グローバー探索とは" in html
    assert "ここでは何を可視化しているか" in html
    assert "厳密シミュレーション" in html, "誠実さ注記(古典での厳密再現)欠落"
    assert "量子加速そのもの" in html
    assert "sin²((2t+1)θ)" in html or "sin&#178;" in html


@pytest.mark.unit
def test_t013_fleet_footer():
    """T-013b: フリート標準フッタ 5 リンク+画面下部固定+本文余白。"""
    html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
    for label in ("MIT License", "GitHub", "振幅劇場の歩き方", "振幅劇場の設計図", "App Menu"):
        assert label in html, f"フッタのリンク『{label}』欠落"
    assert "github.com/twill3c/shinpuku-gekijo" in html
    assert "app-menu-amber.vercel.app" in html
    assert "claude.ai/code/artifact/" in html
    assert "© 2026 坂田哲朗" in html
    css = (ROOT / "web" / "css" / "style.css").read_text(encoding="utf-8")
    footer_rule = css.split(".site-footer {", 1)
    assert len(footer_rule) == 2 and "position: fixed" in footer_rule[1].split("}", 1)[0]
    assert "--footer-clearance" in css
