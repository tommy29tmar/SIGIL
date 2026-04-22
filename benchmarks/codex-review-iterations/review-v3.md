1. High - H2 overhead metric is still wrong.  
Problem: plan measures hook overhead via `usage.input_tokens`, but local smoke shows `hewn_full` and `hewn_prompt_only` keep `usage.input_tokens` identical while the hook increases `cache_creation_input_tokens`.  
Why it matters: report will undercount or miss classifier injection cost.  
Concrete fix: compute hook input footprint from `input_tokens + cache_creation_input_tokens + cache_read_input_tokens` for the target model, stratified by warm/cold cache. Update smoke test to assert the delta appears in those fields, not only `usage.input_tokens`.

2. High - Benchmark environment is not isolated.  
Problem: default `claude -p` can load user/project Claude Code instructions, settings, plugins, effort level, and hooks. This workspace has global concise-output instructions, so “baseline” is not clean Verbose Claude and T1a is not true Caveman parity.  
Why it matters: local configuration can dominate token counts and make results non-reproducible.  
Concrete fix: define a clean harness invocation: temp benchmark cwd with no `CLAUDE.md`, disabled plugins/MCP/slash commands/tools where possible, pinned/recorded effort, and repo-local Hewn wrapper/hook. Snapshot the isolation flags. If OAuth prevents clean isolation, relabel as a configured-Claude-Code benchmark and remove Caveman parity/Verbose-Claude claims.

3. Medium - Prompt-file invocation is ambiguous and likely wrong if implemented literally.  
Problem: plan says `--system-prompt <file>` / `--append-system-prompt <file>`, but current `claude --help` shows those flags take prompt text, not file paths.  
Why it matters: passing arm file paths would benchmark filenames as system prompts, invalidating all non-baseline arms.  
Concrete fix: require `run.py` to read arm files and pass their contents as the flag value, or use a real file-specific flag only if verified available. Add a smoke test with a sentinel system prompt proving the contents, not the path, reached Claude.

4. Medium - M5 randomization still does not implement the promised stable mapping.  
Problem: top section says sha256 mod `n!`, but the actual algorithm seeds `random.Random`.  
Why it matters: that does not guarantee Python-version-independent arm order.  
Concrete fix: implement factoradic permutation from `digest_int % factorial(len(arms))`, then persist seed, digest, full arm order, and `arm_order_index`.