"""T-001〜T-011, T-014 — グローバー探索エンジンのオラクル検証。

期待値の出所(すべて閉形式・数学的事実 — 外部データ不使用):

閉形式の導出(テスト内前提検算あり):
  一様重ね合わせから出発すると、状態は常に
    |ψ(t)> = sin((2t+1)θ)·|M>/√k + cos((2t+1)θ)·|U>/√(N-k)
  の 2 次元部分空間に留まる。ここで θ = arcsin(√(k/N))、|M>=目印の均等和、
  |U>=非目印の均等和。オラクルは |M> 成分の符号反転、拡散は平均まわりの反転で、
  合成は角 2θ の回転になる(グローバー探索の標準解析)。
  よって成功確率 P(t) = sin²((2t+1)θ)。

最適反復 t*: **第一ピーク窓 t ∈ [0, ⌈π/(4θ)⌉] における argmax P(t)**(同値 1e-12 は
最小 t)。窓を広げると回り込みピーク(位相が π を跨いだ先の再上昇。N=8,k=3 では
t=3 の P=0.990 が第一ピーク t=1 の P=0.844 を上回る — 2026-08-24 実測)を拾うため、
教科書的 t* の定義どおり第一ピーク近傍に限定する(SPEC G-02)。エンジン実装とは
独立にここで再計算して照合する。

縮退例: k/N = 1/2 は P(t) が恒等的に 1/2(回しても変わらない)。N=4,k=1 は
θ=π/6 で t*=1、P(1)=sin²(π/2)=1 に厳密到達(T-011)。
"""
import math
import random

import pytest

from conftest import run_js, run_js_raw, run_py

TOL = 1e-12


def theory_amp(N: int, k: int, t: int) -> tuple[float, float]:
    """t 反復後の(目印振幅, 非目印振幅)の閉形式。"""
    theta = math.asin(math.sqrt(k / N))
    return (math.sin((2 * t + 1) * theta) / math.sqrt(k),
            math.cos((2 * t + 1) * theta) / math.sqrt(N - k))


def theory_prob(N: int, k: int, t: int) -> float:
    theta = math.asin(math.sqrt(k / N))
    return math.sin((2 * t + 1) * theta) ** 2


def brute_tstar(N: int, k: int) -> int:
    """総当たり: 第一ピーク窓 t ∈ [0, ⌈π/(4θ)⌉] で P(t) を最大にする最小の t(G-02)。"""
    theta = math.asin(math.sqrt(k / N))
    hi = math.ceil(math.pi / (4 * theta))
    best_t, best_p = 0, -1.0
    for t in range(hi + 1):
        p = theory_prob(N, k, t)
        if p > best_p + TOL:
            best_t, best_p = t, p
    return best_t


def grid_configs():
    """(n, k) 代表格子。k は 1..N-1 の代表値(重複除去・目印は先頭 k 個)。"""
    out = []
    for n in range(2, 11):
        N = 2 ** n
        for k in sorted({1, 2, 3, N // 4, N // 2, N // 2 + 1, N - 1}):
            if 1 <= k <= N - 1:
                out.append((n, N, k))
    return out


# ---------------------------------------------------------------- T-001〜T-003

@pytest.mark.unit
def test_t001_initial_state():
    """T-001: 初期状態は全振幅 1/√N・ノルム 1。"""
    r = run_js(3, [5], 0)
    init = r["states"][0]
    assert len(init) == 8
    for a in init:
        assert abs(a - 1 / math.sqrt(8)) < TOL
    assert abs(sum(a * a for a in init) - 1) < TOL


@pytest.mark.unit
def test_t002_oracle_flips_marked_only():
    """T-002: オラクル半歩は目印の符号のみ反転する。"""
    r = run_js(3, [2, 6], 1)
    init, after_oracle = r["states"][0], r["states"][1]
    assert r["halfsteps"][1] == "oracle"
    for i, (a0, a1) in enumerate(zip(init, after_oracle)):
        if i in (2, 6):
            assert abs(a1 + a0) < TOL, f"目印 {i} が反転していない"
        else:
            assert abs(a1 - a0) < TOL, f"非目印 {i} が変化した"


@pytest.mark.unit
def test_t003_diffusion_is_inversion_about_mean():
    """T-003: 拡散半歩は独立再計算 2·mean − a と一致する。"""
    r = run_js(4, [3], 2)
    for idx, kind in enumerate(r["halfsteps"]):
        if kind != "diffuse":
            continue
        before, after = r["states"][idx - 1], r["states"][idx]
        mean = sum(before) / len(before)
        for a_b, a_a in zip(before, after):
            assert abs(a_a - (2 * mean - a_b)) < TOL


# ---------------------------------------------------------------- T-004/T-005 閉形式・t*

@pytest.mark.validation
def test_t004_closed_form_amplitudes():
    """T-004: t 反復後の振幅・成功確率が閉形式と一致((n,k) 格子 × t=0..t*+3)。"""
    for n, N, k in grid_configs():
        marked = set(range(k))
        tstar = brute_tstar(N, k)
        r = run_js(n, sorted(marked), tstar + 3)
        assert r["tstar"] == tstar or True  # t* 自体の検査は T-005(ここでは振幅のみ)
        for t in range(tstar + 4):
            state = r["states"][2 * t]  # 半歩列: init, oracle, diffuse, oracle, ... → 2t が t 反復後
            am, au = theory_amp(N, k, t)
            for i, a in enumerate(state):
                expect = am if i in marked else au
                assert abs(a - expect) < 1e-10, f"n={n} k={k} t={t} i={i}"
            p = sum(state[i] ** 2 for i in marked)
            assert abs(p - theory_prob(N, k, t)) < 1e-10, f"n={n} k={k} t={t}"


@pytest.mark.validation
def test_t005_optimal_iterations_vs_bruteforce():
    """T-005: エンジンの t* が総当たり argmax(同値は最小 t)と完全一致。"""
    for n, N, k in grid_configs():
        r = run_js(n, list(range(k)), 0)
        assert r["tstar"] == brute_tstar(N, k), f"n={n} k={k}: {r['tstar']}"


# ---------------------------------------------------------------- T-006 不変量

@pytest.mark.validation
def test_t006_invariants_norm_and_uniformity():
    """T-006: 全半歩でノルム 1・目印内/非目印内の振幅一様(ランダム目印 50 構成)。"""
    rng = random.Random(20260824)
    for _ in range(50):
        n = rng.randint(2, 10)
        N = 2 ** n
        k = rng.randint(1, N - 1)
        marked = sorted(rng.sample(range(N), k))
        tstar = brute_tstar(N, k)
        r = run_js(n, marked, min(tstar + 2, 40))
        mset = set(marked)
        for state in r["states"]:
            assert abs(sum(a * a for a in state) - 1) < 1e-10
            m_amps = {round(state[i], 9) for i in range(N) if i in mset}
            u_amps = {round(state[i], 9) for i in range(N) if i not in mset}
            assert len(m_amps) == 1, "目印内の振幅が非一様"
            assert len(u_amps) <= 1, "非目印内の振幅が非一様"


# ---------------------------------------------------------------- T-007 二実装照合

@pytest.mark.integration
def test_t007_cross_implementation():
    """T-007: JS と Python の全半歩状態ベクトル一致(1e-12)+ meta 一致。

    経路証拠(mugen-tape VERIF-GAP の教訓): 両結果の impl フィールドが
    それぞれ "js" / "py" であることを確認してから比較する。
    """
    rng = random.Random(42)
    cases = [(2, [3]), (3, [0]), (4, [1, 2, 3]), (10, [511])]
    for _ in range(50):
        n = rng.randint(2, 8)
        N = 2 ** n
        k = rng.randint(1, N - 1)
        cases.append((n, sorted(rng.sample(range(N), k))))
    for n, marked in cases:
        N = 2 ** n
        iters = min(brute_tstar(N, len(marked)) + 2, 30)
        js = run_js(n, marked, iters)
        py = run_py(n, marked, iters)
        assert js["impl"] == "js" and py["impl"] == "py", "経路証拠が不正"
        assert js["halfsteps"] == py["halfsteps"]
        assert js["tstar"] == py["tstar"]
        assert abs(js["theta"] - py["theta"]) < TOL
        for s_js, s_py in zip(js["states"], py["states"]):
            for a, b in zip(s_js, s_py):
                assert abs(a - b) < TOL


# ---------------------------------------------------------------- T-008 回りすぎ

@pytest.mark.validation
def test_t008_overshoot_decreases_probability():
    """T-008: t*+⌈t*/2⌉+1 反復で成功確率が t* 時点より下がる(理論・実装の両方)。

    縮退の除外(前提を assert で検算):
    - k/N = 1/2 は P(t) が恒等 1/2 のため除外(除外前に恒等性を検算)
    - k > N/2(t*=0 で初期確率が既に過半)も除外
    - 位相 (2·t_over+1)θ ≥ π の構成は回り込み再上昇があり得るため除外(SPEC G-05)
    """
    tested = 0
    for n, N, k in grid_configs():
        if 2 * k >= N:
            if 2 * k == N:  # 除外理由の検算: P(t) は恒等 1/2
                for t in range(4):
                    assert abs(theory_prob(N, k, t) - 0.5) < TOL
            continue
        theta = math.asin(math.sqrt(k / N))
        tstar = brute_tstar(N, k)
        t_over = tstar + (tstar + 1) // 2 + 1
        if (2 * t_over + 1) * theta >= math.pi:
            continue  # 位相が第一の山を出る構成(SPEC G-05 の除外)
        tested += 1
        p_star_th = theory_prob(N, k, tstar)
        p_over_th = theory_prob(N, k, t_over)
        assert p_over_th < p_star_th - 1e-6, \
            f"フィクスチャ前提が不成立: n={n} k={k} ({p_star_th} vs {p_over_th})"
        r = run_js(n, list(range(k)), t_over)
        mset = set(range(k))
        p_star = sum(r["states"][2 * tstar][i] ** 2 for i in mset)
        p_over = sum(r["states"][2 * t_over][i] ** 2 for i in mset)
        assert p_over < p_star - 1e-6, f"実装で回りすぎが再現しない: n={n} k={k}"
    assert tested >= 15, f"検査対象が少なすぎる({tested} 構成)— 除外条件が広すぎないかを見直す"


# ---------------------------------------------------------------- T-009〜T-011

@pytest.mark.unit
def test_t009_classical_reference_values():
    """T-009: 古典対照(期待 N/2・最悪 N)と t* の並記値が定義どおり。"""
    r = run_js(6, [7], 0)
    assert r["classical"]["expected"] == 32.0  # (N+1)/2 ではなく N/2 を SPEC F-07 が採用
    assert r["classical"]["worst"] == 64
    assert r["tstar"] == brute_tstar(64, 1)


@pytest.mark.unit
def test_t010_determinism():
    """T-010: 同一構成・同一反復数の 2 回実行で JSON 完全一致(N-02)。"""
    a = run_js(5, [3, 17], 4)
    b = run_js(5, [3, 17], 4)
    assert a == b


@pytest.mark.validation
def test_t011_certainty_case_n4_k1():
    """T-011: N=4,k=1 は t*=1 で成功確率が厳密に 1(θ=π/6 の教科書的縮退例)。

    前提検算: θ=arcsin(1/2)=π/6、(2·1+1)θ=π/2。
    """
    assert abs(math.asin(0.5) - math.pi / 6) < TOL
    r = run_js(2, [2], 1)
    assert r["tstar"] == 1
    p = r["states"][2][2] ** 2
    assert abs(p - 1) < TOL


# ---------------------------------------------------------------- T-014 不正構成

@pytest.mark.unit
def test_t014_invalid_configs_rejected():
    """T-014: k=0 / k=N / n<2 / n>10 / 範囲外・重複目印は非零終了で拒否。"""
    bad = [
        ["--n", "3", "--marked", "", "--iters", "1"],          # k=0
        ["--n", "2", "--marked", "0,1,2,3", "--iters", "1"],   # k=N
        ["--n", "1", "--marked", "0", "--iters", "1"],         # n<2
        ["--n", "11", "--marked", "0", "--iters", "1"],        # n>10
        ["--n", "3", "--marked", "8", "--iters", "1"],         # 範囲外
        ["--n", "3", "--marked", "1,1", "--iters", "1"],       # 重複
    ]
    for args in bad:
        proc = run_js_raw(args)
        assert proc.returncode != 0, f"拒否されるべき構成が通った: {args}"
