1. **Medium**: T0 is still mislabeled as a CLAUDE.md-only calibration.

Problem: `--append-system-prompt` inherits the entire default Claude Code system prompt plus CLAUDE.md, while `--system-prompt` replaces it. So T0 measures aggregate append-vs-replace exposure, not CLAUDE.md alone.

Why it matters: The report would over-attribute the contamination source and any “CLAUDE.md-corrected” Hewn-vs-Caveman range would not be defensible.

Concrete fix: Rename T0 throughout to “append-vs-replace exposure calibration” or “default-system + CLAUDE.md exposure calibration.” Report it as aggregate exposure. If CLAUDE.md-only isolation is required, add a separate calibration with identical prompt mechanism and CLAUDE.md disabled/enabled, or state that this cannot be isolated under the chosen OAuth CLI constraints.

2. **Medium**: The corrected-savings formula has ambiguous or wrong sign.

Problem: T0 defines effect as `appended.output_tokens - replacement.output_tokens`, which will be negative if CLAUDE.md/default exposure compresses output. The plan then says “observational delta minus the effect,” which can increase apparent Hewn savings instead of deflating them.

Why it matters: This can invert the intended correction and produce a misleading “corrected” benchmark number.

Concrete fix: Define correction in output-token space, not as “minus effect.” For each prompt, compare Hewn against the appended comparator directly: `corrected_abs_delta = comparator_appended_tokens - hewn_tokens`; raw is `comparator_replacement_tokens - hewn_tokens`. Report the two as a bracket/range, with explicit sign conventions.