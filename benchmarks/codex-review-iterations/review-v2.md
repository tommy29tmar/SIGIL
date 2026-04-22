1. **High - Model still is not actually pinned.**  
Problem: `--model opus` is an alias, not a stable pin. Local CLI help says aliases target the latest model, while full model names are accepted. The `modelUsage contains claude-opus-4-7` check is also too weak if `modelUsage` includes internal/helper calls.  
Why it matters: Future reruns, partial reruns, or CLI updates can silently target a different model or reject samples after spending benchmark time.  
Fix: Pass `--model claude-opus-4-7` everywhere. Assert the generated assistant output is from that model, or if only aggregate `modelUsage` exists, require the expected model accounts for the response output tokens.

2. **High - Hewn hook is incorrectly documented as “no token cost.”**  
Problem: The classifier itself is local, but the hook injects `additionalContext` into the model turn. That added directive consumes input tokens on every `hewn_full` call.  
Why it matters: Cost/input-token comparisons for `hewn_full` will be understated or misexplained.  
Fix: State “no extra classifier API call” instead. Measure/report the injected-context input-token overhead as part of `hewn_full`, ideally versus a no-hook append-prompt control.

3. **High - T4 resume flow can contaminate conversations across arms.**  
Problem: Step 8 says test/use `--resume`, but does not require resuming by explicit `session_id`. The CLI supports `--resume [value]`; using bare resume/continue can pick the most recent session in the directory.  
Why it matters: Multi-turn T4 data can accidentally mix arms, runs, or prompt sequences, invalidating drift and cumulative-cost results.  
Fix: Capture `session_id` from turn 1 for each `(sequence, run, arm)` and pass that exact ID on every later turn. Smoke-test this separately for plain `claude` and `hewn`, including `--append-system-prompt` plus hook behavior.

4. **Medium - T4 cannot support the stated “hook value” claim.**  
Problem: T4 excludes `hewn_prompt_only`, and `hewn_full` differs by both hook injection and `--append-system-prompt` behavior.  
Why it matters: Any T4 delta can’t be attributed to the hook.  
Fix: Add a T4 no-hook control using the same append-system-prompt path as `hewn_full`, or remove “hook value” claims and label T4 as only “hewn_full multi-turn behavior.”

5. **Medium - Arm randomization is not reproducible if implemented with Python `hash()`.**  
Problem: `hash(f"{prompt_id}:{run_index}")` is salted per Python process unless `PYTHONHASHSEED` is fixed.  
Why it matters: Resume/reproduction can produce different arm orders, undermining cache-bias controls.  
Fix: Use a stable hash such as `sha256(f"{seed}:{prompt_id}:{run_index}")`, record the seed, and persist the computed arm order in each snapshot.