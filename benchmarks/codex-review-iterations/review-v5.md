1. **High**: The CLAUDE.md asymmetry is documented, but the bias direction is misstated.

Problem: `hewn_prompt_only` and `hewn_full` inherit the user’s terseness instructions via `--append-system-prompt`; `terse` and Caveman arms do not because `--system-prompt` replaces the Claude Code/user prompt stack. That can bias Hewn-vs-terse/Caveman output-token savings in Hewn’s favor, not just make baseline comparisons conservative.

Why it matters: This is central to the benchmark claim. With option B, contamination is acceptable only if the report states the causal limitation correctly.

Concrete fix: Update the implications/report language to say Hewn-vs-`terse`/Caveman comparisons are observed under asymmetric CLAUDE.md exposure and may be inflated for Hewn. Either add append-mode comparator arms for extended tracks, or explicitly demote those comparisons from causal “Hewn saved X%” claims to contaminated observational results.