"""T-012 — 深リンク #n=&m=&t= の往復恒等(F-09)。

期待値の出所: encode→decode の恒等は定義そのもの(合成フィクスチャ)。
不正ハッシュの拒否は SPEC F-09+エンジンの構成検証に従う。
"""
import json
import pathlib
import random
import subprocess

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def link_cli(args: list[str]) -> dict:
    proc = subprocess.run(["node", str(ROOT / "harness" / "link_grover.mjs")] + args,
                          capture_output=True, text=True, encoding="utf-8",
                          timeout=30, cwd=ROOT)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


@pytest.mark.unit
def test_t012_roundtrip_identity():
    """T-012: encode → decode が恒等(ランダム 100 構成+境界)。"""
    rng = random.Random(20260824)
    cases = [(2, [0], 0), (10, [1023], 25), (2, [1, 2, 3], 1)]
    for _ in range(100):
        n = rng.randint(2, 10)
        N = 2 ** n
        k = rng.randint(1, min(N - 1, 12))
        marked = sorted(rng.sample(range(N), k))
        cases.append((n, marked, rng.randint(0, 40)))
    for n, marked, t in cases:
        r = link_cli(["--n", str(n), "--marked", ",".join(map(str, marked)), "--t", str(t)])
        assert r["ok"], (n, marked, t)
        assert r["decoded"] == {"n": n, "marked": marked, "t": t}, r


@pytest.mark.unit
def test_t012_invalid_hash_rejected():
    """T-012: 不正ハッシュは ok=false(例外や誤解釈でなく明示拒否)。"""
    bad = ["#n=1&m=0&t=0",        # n 範囲外
           "#n=3&m=&t=0",         # 目印空
           "#n=3&m=8&t=0",        # 範囲外目印
           "#n=3&m=1,1&t=0",      # 重複
           "#n=3&m=0,1,2,3,4,5,6,7&t=0",  # 全件
           "#n=3&m=2&t=-1",       # 負反復
           "#n=x&m=2&t=0",        # 非数
           ""]
    for h in bad:
        r = link_cli(["--hash", h])
        assert r["ok"] is False, f"拒否されるべきハッシュが通った: {h!r}"
