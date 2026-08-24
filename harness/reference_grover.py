"""reference_grover.py — Python 参照実装(G-04 二実装照合用)。

JS エンジン(web/js/engine.js)とは独立に、リスト演算の素朴な記述で実装する。
意味論は SPEC F-01/F-02, G-01..G-03 と同一:
- オラクル = 目印の符号反転 / 拡散 = 2·mean − a / 1 反復 = オラクル+拡散
- t* は第一ピーク窓 t ∈ [0, ⌈π/(4θ)⌉] の argmax(同値 1e-12 は最小 t)
"""
import math


def _optimal_iterations(N: int, k: int) -> int:
    theta = math.asin(math.sqrt(k / N))
    hi = math.ceil(math.pi / (4 * theta))
    best_t, best_p = 0, -1.0
    for t in range(hi + 1):
        p = math.sin((2 * t + 1) * theta) ** 2
        if p > best_p + 1e-12:
            best_t, best_p = t, p
    return best_t


def run_grover(n: int, marked: list[int], iters: int) -> dict:
    if not isinstance(n, int) or not 2 <= n <= 10:
        raise ValueError(f"n は 2..10 の整数(受領: {n})")
    N = 2 ** n
    mset = set()
    for m in marked:
        if not isinstance(m, int) or not 0 <= m < N:
            raise ValueError(f"目印 {m} が範囲外")
        if m in mset:
            raise ValueError(f"目印 {m} が重複")
        mset.add(m)
    k = len(mset)
    if k == 0:
        raise ValueError("目印集合が空")
    if k >= N:
        raise ValueError("目印が全件")
    marked_sorted = sorted(mset)

    state = [1 / math.sqrt(N)] * N
    states = [state[:]]
    halfsteps = ["init"]

    def prob(s):
        return sum(s[i] * s[i] for i in marked_sorted)

    probs = [prob(state)]
    oracle_calls = 0
    for _ in range(iters):
        for i in marked_sorted:
            state[i] = -state[i]
        oracle_calls += 1
        states.append(state[:])
        halfsteps.append("oracle")
        probs.append(prob(state))

        two_mean = 2 * (sum(state) / N)
        state = [two_mean - a for a in state]
        states.append(state[:])
        halfsteps.append("diffuse")
        probs.append(prob(state))

    return {
        "impl": "py",
        "n": n, "N": N, "k": k, "marked": marked_sorted,
        "theta": math.asin(math.sqrt(k / N)),
        "tstar": _optimal_iterations(N, k),
        "classical": {"expected": N / 2, "worst": N},
        "oracleCalls": oracle_calls,
        "halfsteps": halfsteps, "states": states, "successProbs": probs,
    }
