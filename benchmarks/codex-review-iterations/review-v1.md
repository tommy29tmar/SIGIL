1. **High** — The model pin is not executable as written: `claude-opus-4-7[1m]` looks like a leaked ANSI escape fragment.

   Why it matters: the benchmark could fail outright or accidentally run the CLI default model, invalidating all arm comparisons.

   Concrete fix: replace it with the exact CLI-accepted model ID, pass `--model <id>` on every `claude -p` and `hewn -p` invocation, and assert the returned snapshot model matches.

2. **High** — T1 claims exact Caveman parity, but uses 3 runs and all 6 arms. Caveman’s described method is single run per prompt/arm with only baseline, terse, and skill-style arms.

   Why it matters: the headline “Caveman-parity” numbers would not actually be Caveman-parity, and medians/stdevs change the methodology being replicated.

   Concrete fix: split T1 into an exact replication track: 10 prompts × 1 run × `baseline`, `terse`, `caveman_full`; then run a separate repeated extension track with all 6 arms.

3. **High** — `hewn_full` uses `hewn -p`, but the metrics section assumes every call is raw `claude -p --output-format json`.

   Why it matters: the wrapper may add classifier calls, alter system prompts, change output format, or include extra latency/token cost. That makes `hewn_full` incomparable unless explicitly instrumented.

   Concrete fix: define `hewn -p` pass-through behavior for `--model` and `--output-format json`; capture final Claude usage separately from wrapper/classifier usage; report wrapper overhead as its own metric.

4. **Medium** — `caveman_ultra` is defined as Caveman Full plus a hand-appended sentence, but the plan presents it as Caveman Ultra.

   Why it matters: if that sentence is not Caveman’s official Ultra prompt/method, the benchmark misrepresents the competing arm.

   Concrete fix: source Caveman Ultra from a pinned Caveman commit or official artifact. If none exists, rename the arm to something like `caveman_full_plus_ultra_directive` and avoid claiming it is Caveman Ultra.

5. **Medium** — The judge methodology calls binary LLM judgments “deterministic” without validation or failure handling.

   Why it matters: invalid JSON, inconsistent judgments, or prompt-sensitive misses can corrupt `concepts_covered`, info density, and readability metrics.

   Concrete fix: add schema validation, raw judge-output snapshots, retry-on-invalid JSON, fixed temperature/settings where the CLI supports it, and explicit judge failure states excluded from aggregate scores.

6. **Medium** — Cache and execution order can bias latency/cost results, especially T3 long-context and T4 multi-turn runs.

   Why it matters: later arms may benefit from warmed prompt cache, making duration/cost comparisons depend on run order rather than arm behavior.

   Concrete fix: randomize or counterbalance arm order per prompt/run, record cold vs warm cache status, and keep token-savings claims separate from latency/cost claims unless cache effects are normalized.