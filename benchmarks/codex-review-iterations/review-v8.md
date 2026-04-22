1. **Medium - Source tracks for T1 appended comparisons are still ambiguous.**  
Problem: `terse_appended` and `caveman_full_appended` only run in T0, but the Hewn comparison is labeled “T1a/T1b only” and references those appended arms as if they exist there. T1a also has no `hewn_full`.  
Why it matters: implementation can silently mix T0/T1/T1b rows, duplicate one T0 run across three T1b runs, or fail because the required arms are absent.  
Concrete fix: explicitly define the join/aggregation: e.g. “short_en appended comparator values come from T0; `hewn_full` comes from T1b; aggregate `hewn_full` per prompt before subtracting,” or add appended comparator arms to T1b. Also remove T1a from Hewn comparison wording unless it is only used as Caveman parity input.

2. **Medium - Hewn-vs-baseline says “reported in all tracks,” but required arms are not present in all tracks.**  
Problem: T0 lacks both baseline and `hewn_full`; T1a lacks `hewn_full`.  
Why it matters: report generation has an undefined metric for T0/T1a and may either error or make another cross-track comparison without a stated rule.  
Concrete fix: change to “reported in T1b-T5” or explicitly define any intended short_en cross-track pairing.