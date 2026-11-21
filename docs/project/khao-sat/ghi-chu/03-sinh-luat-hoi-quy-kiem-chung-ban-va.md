# LLM-generated security rules (Semgrep/CodeQL), security regression testing, and security patch validation (2023–2026), seen from an industrial deployment angle

Scope note: compiled 2026-11-07. Wherever a figure changed between arXiv versions, both values are given. "Unverified" marks items I could not confirm in a primary source during this session. Several highly relevant papers (P2Patch, BugStone-E2E, Vul4Py, the multi-patch study) are 2026 arXiv preprints and may still change.

## Q1. LLM-generated Semgrep/CodeQL rules and queries: works besides QLCoder, their precision, success rates, costs, and industrial deployments

### Takeaway
"Patch → LLM → rule, validated vuln-vs-patched" is now a standard pipeline. QLCoder (CodeQL, Java), KNighter (Clang Static Analyzer, Linux), Autogrep (Semgrep, 20 languages), MoCQ (CodeQL/Joern), BugStone-E2E (Tree-sitter + LLM) and AutoChecker (PMD) all use it. Reported per-target success is 9–61%. Precision is measured almost only on the source repository, and when it is measured on other code, false positives run around 35%. I found no peer-reviewed report of these rules being deployed in a company's CI and measured on that company's history or by developer acceptance. That is the clearest gap.

### Cited Findings

**QLCoder (seed paper)**
- Title: "QLCoder: A Query Synthesizer for Static Analysis of Security Vulnerabilities". Authors: Claire Wang, Ziyang Li, Saikat Dutta, Mayur Naik. arXiv:2511.08462; v4 revised 25 Mar 2026. The arXiv v4 page I fetched does not name ICLR 2026, so that venue is **unverified** from this session. — [arXiv v4](https://arxiv.org/html/2511.08462v4)
- Setup: Claude Sonnet 4 inside Claude Code. A custom MCP server exposes a CodeQL Language Server (LSP), a vector DB of CodeQL docs and reference queries, and an AST cache. Up to 10 iterations per CVE and 50 agent turns per iteration. — [arXiv v4](https://arxiv.org/html/2511.08462v4)
- Success definition, which can be reused directly for a company "incident → rule" oracle:
  - the query compiles and runs;
  - it produces at least one path in the vulnerable version that touches the patched code;
  - it produces no such path in the fixed version. — [arXiv v4](https://arxiv.org/html/2511.08462v4)
- Dataset: CWE-Bench-Java, 176 CVEs from 111 projects across 42 CWEs, including 65 CVEs from 2025. — [arXiv v4](https://arxiv.org/html/2511.08462v4)
- Results:
  - Success: 53.4% (94/176) overall; 57.7% on pre-2025 CVEs and 46.2% on 2025 CVEs. The drop on newer CVEs suggests some memorization or contamination effect.
  - On a shared 130-CVE subset:

    | Method | Recall | Avg precision | Avg F1 |
    |---|---|---|---|
    | QLCoder | 80.0% | 0.672 | 0.700 |
    | IRIS | 35.4% | 0.031 | 0.048 |
    | Stock CodeQL | 20.0% | 0.055 | 0.073 |

  — [arXiv v4](https://arxiv.org/html/2511.08462v4)
- Cost: an average of 3,712 s (about 62 min) and $2.90 per CVE. The token figures are internally inconsistent (the text gives 708 input / 43,176 output tokens; Table 7 gives about 4.6M tokens per CVE). Queries that finish in under 3,000 s succeed about 97% of the time, which suggests an early-stop policy. — [arXiv v4](https://arxiv.org/html/2511.08462v4)
- Ablations on 20 CVEs, and baselines:

  | Variant | Success | F1 |
  |---|---|---|
  | Full QLCoder | 55% | 0.69 |
  | Without LSP | 25% | 0.36 |
  | Without docs/reference queries | 20% | 0.36 |
  | Without AST cache | 25% | 0.47 |
  | Plain Claude Code, no tools | 10% | 0.36 |

  Baselines on 2025 CVEs: Codex GPT-5 (medium) 0% → 20% with QLCoder tooling; Gemini CLI 2.5 Pro 0% → 0%. The intro's "best baseline" claim (Gemini CLI) conflicts with Table 5 (Claude Code is better). — [arXiv v4](https://arxiv.org/html/2511.08462v4)
- Stated limitations:
  - The criteria "may admit potentially false positive paths in both versions."
  - There is no false-positive evaluation on other codebases.
  - Variant analysis is anecdotal: one query found 2 unknown bugs in 2 repos, with no FP data.
  - Exploit generation is left as future work. — [arXiv v4](https://arxiv.org/html/2511.08462v4)

**IRIS (taint-spec inference, ICLR 2025)**
- Title: "IRIS: LLM-Assisted Static Analysis for Detecting Security Vulnerabilities". Li, Dutta, Naik. ICLR 2025; arXiv:2405.17238. — [ICLR proceedings](https://proceedings.iclr.cc/paper/2025/hash/582d4e27fa24168f3af1f4582655034b-Abstract-Conference.html), [arXiv](https://arxiv.org/abs/2405.17238)
- Method: an LLM infers CWE-specific source/sink taint specifications, CodeQL runs the taint analysis, and an LLM filters the alerts. It introduced CWE-Bench-Java (120 vulnerabilities in the original version). — [arXiv v3](https://arxiv.org/html/2405.17238v3)
- Results:
  - ICLR version: GPT-4 + IRIS detects 55 vulnerabilities versus 27 for CodeQL (+28, i.e. +103.7%), finds 4 previously unknown vulnerabilities, and uses 7 LLMs.
  - v1 reported 69/120 versus 27, with more than 80% fewer false alarms in the best case.
  - The numbers changed across versions. — [ICLR proceedings](https://proceedings.iclr.cc/paper/2025/hash/582d4e27fa24168f3af1f4582655034b-Abstract-Conference.html), [arXiv v1](https://arxiv.org/html/2405.17238v1)
- In QLCoder's later per-CVE evaluation, IRIS's average precision is only 0.031. This shows how much the precision metric definition matters. — [QLCoder v4](https://arxiv.org/html/2511.08462v4)

**KNighter (LLM-synthesized checkers from patch commits, SOSP 2025)**
- Title: "KNighter: Transforming Static Analysis with LLM-Synthesized Checkers". Chenyuan Yang, Zijie Zhao, Zichen Xie, Haoyu Li, Lingming Zhang (UIUC). SOSP 2025, DOI 10.1145/3731569.3764827; arXiv:2503.09002. Code: [github.com/ise-uiuc/KNighter](https://github.com/ise-uiuc/KNighter). — [arXiv](https://arxiv.org/abs/2503.09002v3)
- Pipeline: commit analysis → checker generation (Clang Static Analyzer checkers) → compile/test refinement → scan the whole kernel → LLM triage agent. A checker is "valid" if it flags the buggy pattern in the pre-patch code and not in the patched code; "plausible" means valid with a low FP rate. This is the closest analogue to the "company fixed bugs → rules" idea, applied to one large codebase. — [arXiv v3](https://arxiv.org/html/2503.09002v3)
- Numbers: from 61 historical patch commits, 37 high-quality checkers (61%), with a false positive rate of about 35% after the triage agent. — [arXiv v2/v3](https://arxiv.org/html/2503.09002v2)
- Impact on the Linux kernel by version:

  | Version | New bugs | Confirmed | Fixed | CVEs |
  |---|---|---|---|---|
  | v1 | 70 | 56 | 41 | — |
  | v2 | — | — | — | 16 |
  | v3 | 92 (latent 4.3 years on average) | 77 | 57 | 30 |

  — [arXiv](https://arxiv.org/abs/2503.09002v3)
- This is effectively within-codebase variant analysis: checkers derived from past fixes find siblings elsewhere in the same codebase. It is strong evidence for the "variant analysis" idea, but it covers C/kernel only.

**Autogrep (Semgrep rules from patches)**
- "Autogrep: Automated Generation and Filtering of Semgrep Rules from Vulnerability Patches" (Lambda Security, Feb 2025). It is a technical report / blog paper, not peer-reviewed. — [project page](https://lambdasec.github.io/AutoGrep-Automated-Generation-and-Filtering-of-Semgrep-Rules-from-Vulnerability-Patches/), [GitHub](https://github.com/lambdasec/autogrep)
- Method: DeepSeek Chat via OpenRouter, with the prompt containing the diff, Semgrep syntax guidance and examples, and 3 retries. A rule is kept only if it fires on the parent (vulnerable) commit and is silent on the fix commit. About 27% of initial rules failed this check. Deduplication uses MiniLM embeddings (cosine > 0.9), and an LLM rejects project-specific, trivial or overly specific rules. — [project page](https://lambdasec.github.io/AutoGrep-Automated-Generation-and-Filtering-of-Semgrep-Rules-from-Vulnerability-Patches/)
- Numbers:
  - Input: 39,931 patches from MoreFixes (26,617 CVEs, 6,945 repos).
  - Yield: 3,591 initial rules (8.99% per patch) → 645 final rules (17.96% of initial).
  - Filter losses: 71.15% removed as overly specific, 10.75% as duplicates.
  - Claimed FP rate of 18–25% versus 15–20% for manual rules, with no methodology described.
  - Cost not reported.
  - Best acceptance was in Go and worst in C. — [project page](https://lambdasec.github.io/AutoGrep-Automated-Generation-and-Filtering-of-Semgrep-Rules-from-Vulnerability-Patches/)
- Lesson for company Z: most raw LLM rules overfit to the exact patched lines. Generalization or filtering is the hard part, and the authors admit that vuln-vs-patched validation misses variants (false negatives).

**MoCQ (holistic neuro-symbolic query generation)**
- "Automated Static Vulnerability Detection via a Holistic Neuro-symbolic Approach", arXiv:2504.16057 (2025). It generates CodeQL and Joern queries. — [arXiv](https://arxiv.org/html/2504.16057v3)
- Method:
  - DSL subsetting so the LLM handles a core subset of CodeQL.
  - A symbolic validator feeds back execution errors.
  - Overfitting and overly broad queries are flagged.
  - The LLM is asked to remove FPs. — [arXiv](https://arxiv.org/html/2504.16057v3)
- Results:
  - From 5–18 examples it builds queries "within hours" that are comparable to expert queries.
  - It found 46 new vulnerability patterns missed by expert queries (v1 said 12 or more), and 5 patterns were integrated upstream.
  - It covers 7 vulnerability types, in PHP and JavaScript according to a secondary summary. — [arXiv v3](https://arxiv.org/html/2504.16057v3), [Moonlight review (secondary)](https://themoonlight.io/review/automated-static-vulnerability-detection-via-a-holistic-neuro-symbolic-approach)

**BugStone-E2E (CVE history → executable rules, IBM Research)**
- "The History Is the Detector: Executing CVE Patch History, End-to-End". Qiushi Wu, Kevin Eykholt, Youngja Park, Xiaokui Shu, Dhilung Kirat, Douglas Lee Schales, Ian Molloy. arXiv:2609.05335, 4 Sep 2026, no venue. — [arXiv](https://arxiv.org/abs/2609.05335)
- Pipeline:
  - Rules are mined from verified fixing commits, organized by CWE and language.
  - Detection is a funnel: Tree-sitter anchor matching → cheap heuristics (no LLM) → LLM agent inspection → runtime verification → scope-checked patches validated by differential tests.
- Numbers:
  - 19,325 high-severity CVEs (2022–2026) → 2,710 fixing commits → 1,033 rules.
  - Coverage: 56 CWE families and 172 packaged "skills".
  - 14 programs tested, with runtime evidence for 644 findings.
  - The abstract reports no precision or cost. — [arXiv](https://arxiv.org/abs/2609.05335)
- This is the closest end-to-end analogue to "past vulns → rules → verified findings → patches", but it starts from public CVEs, not a company's internal incidents.

**AutoChecker (test-driven checker generation, ICSE 2026)**
- "Write Your Own Code Checker: An Automated Test-Driven Checker Development Approach with LLMs", arXiv:2411.06796, ICSE 2026 research track. — [arXiv](https://arxiv.org/abs/2411.06796v3), [ICSE 2026](https://conf.researchr.org/details/icse-2026/icse-2026-research-track/43/Write-Your-Own-Code-Checker-An-Automated-Test-Driven-Checker-Development-Approach-wi)
- Method: checkers are refined one test case at a time, and logic-guided API retrieval reduces hallucinated APIs.
- Results on 20 PMD rules: all checkers compile, the average test pass rate is 82.28% (84.70% easy, 79.86% hard), and that is more than 4.2× the baselines. — [arXiv](https://arxiv.org/html/2411.06796v3)
- Takeaway: use an incident's vulnerable and fixed snippets plus synthetic variants as a test suite for the rule (TDD for rules).

**LLMSA / NESA (neuro-symbolic Datalog analysis)**
- "LLMSA: A Compositional Neuro-Symbolic Approach to Compilation-free and Customizable Static Analysis", arXiv:2412.14399 (Dec 2024). It was later retitled "NESA: Relational Neuro-Symbolic Static Program Analysis" (DOI 10.1145/3808161). — [arXiv](https://arxiv.org/abs/2412.14399), [NESA DOI listing](https://www.citedrive.com/en/discovery/nesa-relational-neuro-symbolic-static-program-analysis/)
- Results:

  | Task / benchmark | Precision | Recall |
  |---|---|---|
  | Alias analysis | 72.37% | 85.94% |
  | Program slicing | 91.50% | 84.61% |
  | Juliet bug detection | 82.77% | 85.00% |
  | TaintBench (55/70 detected) | 66.27% | 78.57% |

  — [arXiv v1](https://arxiv.org/html/2412.14399v1)

**RuleLLM (YARA/Semgrep for malicious packages)**
- "Automatically Generating Rules of Malicious Software Packages via Large Language Model", arXiv:2504.17198. It produced 763 rules (452 YARA, 311 Semgrep). Its precision figure was truncated in my source, so it is **unverified**. — [arXiv](https://arxiv.org/pdf/2504.17198)

**Big Sleep (Google Project Zero + DeepMind), LLM variant analysis without rules**
- Big Sleep is the successor to Naptime and runs on Gemini 1.5 Pro. It was seeded with a previously fixed SQLite bug and asked to find similar bugs. It found a stack buffer underflow in `seriesBestIndex` (sentinel −1 in iColumn) in unreleased dev code, reported and fixed the same day in early October 2024. Fuzzing did not rediscover it. Google cites "the persistent issue of vulnerability variants" as a main motivation. — [Project Zero blog, "From Naptime to Big Sleep"](https://projectzero.google/2024/10/from-naptime-to-big-sleep.html), [The Register](https://www.theregister.com/2024/11/05/google_ai_vulnerability_hunting)
- Claims that Big Sleep pre-empted CVE-2025-6965 (July 2025) appear in secondary press. They are **unverified** here; the ICT Security Magazine article in particular is unreliable.

**GitHub Security Lab Taskflow Agent (industrial open-source tooling)**
- An open-source framework using YAML taskflows, MCP, and CodeQL tools. It includes a demo GHSA variant-analysis taskflow (one repo + one GHSA as input, e.g. `-g repo=github/cmark-gfm -g ghsa=GHSA-c944-cv5f-hpvr`) and is described as "experimental". — [GitHub blog](https://github.blog/security/community-powered-security-with-ai-an-open-source-framework-for-security-research/), [seclab-taskflows fork](https://github.com/mobb-dev/seclab-taskflows)
- It has been used to triage large volumes of CodeQL alerts (GitHub Actions untrusted-checkout and code-injection queries). This comes from a 2026 secondary summary. — [ZenML LLMOps DB (secondary)](https://www.zenml.io/llmops-database/ai-powered-vulnerability-triage-using-github-security-lab-taskflow-agent)

**Industrial deployments that are nearby, but are not LLM-generated rules**
- Tencent industrial study, "Reducing False Positives in Static Bug Detection with LLMs: An Empirical Study in Industry". It includes developer and analyst interviews; the best hybrid techniques removed 94–98% of FPs; LLM-only approaches were judged impractical because of hallucinations. Seen via ResearchGate; the exact venue is **unverified**. — [ResearchGate](https://www.researchgate.net/publication/400117710_Reducing_False_Positives_in_Static_Bug_Detection_with_LLMs_An_Empirical_Study_in_Industry)
- LLM4PFA (arXiv:2506.10322) filters 72–96% of FPs from CodeQL, Infer and CppCheck using LLM path-feasibility analysis. — [arXiv](https://arxiv.org/html/2506.10322v1)
- Semgrep (vendor marketing, not peer-reviewed): "Assistant Memories" took FP filtering from 18 to 588 on one customer example; "experts agree with Assistant 96% of the time"; AI Autofix is in beta. None of this is about generating rules. — [Semgrep blog](https://semgrep.dev/blog/2025/making-zero-false-positive-sast-a-reality-with-ai-powered-memory), [Semgrep blog 2](https://semgrep.dev/blog/2025/announcing-ai-noise-filtering-and-triage-memories), [Semgrep docs](https://semgrep.dev/docs/semgrep-assistant/customize)

### Inferences
- The vuln-fires / patched-silent oracle is necessary but weak. It does not bound FPs elsewhere in the codebase (QLCoder admits this), and it rewards overfitting (Autogrep discarded 71% of rules as overly specific). A company study adds value if it adds:
  - FP rate on the current HEAD of the company codebase;
  - recall on synthetic or real variants;
  - "would it have caught the recurrence" on later history.
- Success rates fall on newer CVEs (QLCoder: 57.7% → 46.2%). A company's private incidents are by definition outside training data, so expect rates at or below the 2025-CVE numbers.
- Semgrep is cheaper and faster to iterate on than CodeQL (no database build), but it is weaker for inter-procedural taint. KNighter and QLCoder show that tool feedback (compile errors, LSP, AST) is what lifts success from about 10% to about 50%. For Semgrep the analogue is `semgrep --test` with annotated `ruleid:` / `ok:` test files.
- A cost budget of about $3 and about 1 hour per incident (QLCoder) makes 30–80 incidents feasible on a student budget, if company Z has that many fix commits.

### Gaps
- I found no peer-reviewed paper reporting LLM-generated Semgrep/CodeQL rules deployed in a company's CI, with measured FP rate on company code, developer acceptance, or prevented recurrences. Autogrep's FP figures lack methodology.
- No head-to-head comparison of Semgrep versus CodeQL for LLM rule synthesis from the same patches was found.
- QLCoder's ICLR 2026 acceptance was not confirmed in sources fetched this session (the user states it).
- I did not find a distinct paper titled "Automated static analysis rule synthesis" matching the user's phrase; it may refer to one of the above.
- Meta and Google internal CodeQL/LLM variant-analysis deployments: no primary publications with numbers were found beyond Big Sleep's anecdote.

## Q2. Security regression testing: generating PoV/exploit tests or unit tests from CVE fixes, and how often it works

### Takeaway
Automatic PoV/exploit test generation works well in narrow, well-instrumented ecosystems (npm on SecBench.js: 77% at about $0.02 per exploit; client-library Java tests: 229/292 confirm exploitation). It is much weaker on general C/C++/Java benchmarks (12–22% on CyberGym/SEC-bench, 16% in FaultLine). CVE-Genie reproduces 51% of recent CVEs end-to-end at $2.77 per CVE. Validity is a major hidden problem: PoC-Gym found that many "successful" PoCs never reach the vulnerable sink. Industrial evidence for developers accepting LLM-generated tests exists (Meta ACH: 73% accepted), but not for security-regression tests.

### Cited Findings

**Exploit tests for vulnerable dependencies (Java)**
- "How well does LLM generate security tests?" (arXiv:2310.00710; Virginia Tech, Na Meng's group, 2023).
  - Setup: ChatGPT-4 is given the vulnerability description, the app context, and a library test that differs between vulnerable and patched versions.
  - Results: tests were generated for all 49 apps, and 24 of 49 demonstrated the vulnerability (25 libraries). It beat the test generators TRANSFER and SIEGE. — [VT Sanghani page](https://sanghani.cs.vt.edu/research-publication/how-well-does-llm-generate-security-tests), [arXiv mirror](https://fugumt.com/fugumt/paper_check/2310.00710v2_enmode)
- VulEUT, "Unit Test Generation for Vulnerability Exploitation in Java Third-Party Libraries" / "Vulnerability-Triggering Test Case Generation from Third-Party Libraries", arXiv:2409.16701.
  - Method: reachability analysis first, then LLM unit-test generation.
  - Results: on 70 client projects, 292 tests were generated and 229 confirmed exploitation, 24% better than baselines.
  - A related Virginia Tech paper (ying-tse-2025) appears to be a TSE 2025 version; the venue is **unverified**. — [arXiv v3](https://arxiv.org/html/2409.16701v3), [VT PDF](https://people.cs.vt.edu/nm8247/publications/ying-tse-2025.pdf)

**PoV generation from CVE reports**
- FaultLine, "FaultLine: Automated Proof-of-Vulnerability Generation using LLM Agents", arXiv:2507.15241 (Jul 2025).
  - Dataset: 100 Java/C/C++ vulnerabilities.
  - Results: 16 working PoV tests versus 9 for CodeAct 2.1 (a 77% relative improvement). — [arXiv](https://arxiv.org/abs/2507.15241)
- PoC-Gym, "PoC-Gym: Towards More Reliable LLM-Assisted Proof-of-Concept Exploit Generation". Gezgin, Das, Kim, Huang, Stojkovic, Claire Wang. arXiv:2602.04165 (v3 Sep 2026).
  - Validity checks: a PoC must execute completely, emit a success signal, and reach the target trace's sink.
  - Results on 20 Java CVEs (338 runs): 116 candidates were runtime-valid and only 65 were post-hoc valid. About 44% of runtime-valid PoCs were invalid (my calculation). Post-hoc valid PoCs covered 12/20 CVEs.
  - Against FaultLine on 14 shared CVEs: 8 versus 5.
  - A search snippet attributed "71.5% of PoCs invalid" to this paper; I could not confirm that figure on the abs page, so it is **unverified**. — [arXiv](https://arxiv.org/abs/2602.04165)
- CVE-Genie, "From CVE Entries to Verifiable Exploits: An Automated Multi-Agent Framework for Reproducing CVEs". Saad Ullah et al. arXiv:2509.01835 (Sep 2025).
  - Pipeline: Processor → Builder → Exploiter → CTF Verifier.
  - Results: reproduced 428/841 (51%) of CVEs published 2024–2025, at an average of $2.77 per CVE. Failures are dominated by broken or complex builds.
  - Secondary details (**unverified** in the primary source): median 18 min per CVE, a $5 / 45 min cap, and 63.3% on a 60-CVE post-cutoff pilot. — [arXiv](https://arxiv.org/abs/2509.01835), [Emergent Mind (secondary)](https://www.emergentmind.com/topics/cve-genie)
- PoCGen, "PoCGen: Generating Proof-of-Concept Exploits for Vulnerabilities in Npm Packages". Simsek, Eghbali, Pradel. arXiv:2506.04962.
  - Results: 77% on SecBench.js, +45 points over Explode.js, at about $0.02 per exploit. v1 also reported 39% on 794 newer vulnerabilities. — [arXiv v3](https://arxiv.org/html/2506.04962v3)
- PoCEvolve, "Generating Proof-of-Concept Exploits from Security Patches with Vulnerability-Aware Prompt Evolution", arXiv:2607.22076 (2026). Found in search only; numbers **unverified**. — [arXiv](https://arxiv.org/pdf/2607.22076)

**Benchmarks with executable oracles**
- SEC-bench, NeurIPS 2025, "SEC-bench: Automated Benchmarking of LLM Agents on Real-World Software Security Tasks". The best agents reach at most 18.0% on PoC generation and 34.0% on patching. — [NeurIPS proceedings](https://proceedings.neurips.cc/paper_files/paper/2025/hash/a9168f1c54e5147027f1e8cf83e1a775-Abstract-Conference.html)
- CyberGym, arXiv:2506.02548: 1,507 instances from 188 OSS-Fuzz projects.
  - v1: best 11.9% (OpenHands + Claude 3.7 Sonnet).
  - v2 (Oct 2025): Claude Sonnet 4 at 17.9%; GPT-5 at 22.0% with thinking; about 20% at best. Agents found 15 (v1) and 35 (v2) zero-days as a by-product. — [arXiv v2](https://arxiv.org/pdf/2506.02548v2)
- SecBench.js, ICSE 2023, "SecBench.js: An Executable Security Benchmark Suite for Server-Side JavaScript" (Bhuiyan, Staicu et al., CISPA). It has 600 npm vulnerabilities across 5 classes, each with an exploit plus an oracle as a Jest test, and found 20 zero-days. The Jest-test format is a ready template for CI security regression tests. — [ICSE 2023 artifact](https://conf.researchr.org/details/icse-2023/icse-2023-artifact-evaluation/51/SecBench-js-An-Executable-Security-Benchmark-Suite-for-Server-Side-JavaScript), [GitHub](https://github.com/cristianstaicu/SecBench.js)
- Vul4J, MSR 2022 Data Showcase, "Vul4J: A Dataset of Reproducible Java Vulnerabilities Geared Towards the Study of Program Repair Techniques" (Bui, Scandariato, Díaz Ferreyra).
  - Contents: 79 reproducible vulnerabilities from 51 projects across 25 CWEs, built from 1,803 fix commits for 912 vulnerabilities (Project KB). Each has a human patch plus PoV JUnit test(s).
  - Reproducibility decay: the maintainers warn that many entries, especially Spring projects, are no longer reproducible because of deprecated dependencies. Later papers use subsets (64 buildable, 35 single-hunk). — [MSR 2022](https://conf.researchr.org/details/msr-2022/msr-2022-data-showcase/10/Vul4J-A-Dataset-of-Reproducible-Java-Vulnerabilities-Geared-Towards-the-Study-of-Pro), [GitHub](https://github.com/tuhh-softsec/vul4j)

**Industrial acceptance of LLM-generated tests (not security-specific, but the closest deployment evidence)**
- Meta ACH, "Mutation-Guided LLM-based Test Generation at Meta", FSE 2025 Industry, arXiv:2501.12862.
  - Setup: an LLM generates mutants (simulated faults, here privacy faults), then tests that kill them.
  - Results: run on 10,795 Android Kotlin classes, producing 9,095 mutants and 571 privacy-hardening tests. Engineers accepted 73% of the tests, and 36% were judged privacy-relevant. Tests were delivered through CI and code review. — [arXiv](https://arxiv.org/abs/2501.12862), [Meta Engineering blog](https://engineering.fb.com/2025/09/30/security/llms-are-the-key-to-mutation-testing-and-better-compliance/)

### Inferences
- For company Z, "fixed incident → regression test" is most tractable for web/API bugs (injection, auth bypass, IDOR, path traversal), where an HTTP-level or unit-level test with a clear oracle (status code, data leak, exception) is possible. That is the SecBench.js/PoCGen regime, not the CyberGym memory-corruption regime.
- The validity lesson from PoC-Gym: require the test to (a) fail on the vulnerable commit, (b) pass on the fixed commit, and (c) actually reach the patched code, checked through coverage. Otherwise tests pass trivially.
- The build environment is the main failure source (CVE-Genie, Vul4J decay). Company Z's CI containers are an advantage over OSS benchmarks, because builds are already reproducible.
- ACH-style mutation framing transfers directly: treat the original vulnerable code as the "mutant" the regression test must kill, then have the LLM create further variant mutants (re-introductions of the bug in sibling forms) and check that the rule and the test still catch them.

### Gaps
- No 2023–2026 paper was found that measures generated security-regression tests catching actual later recurrences in a real company.
- I found no recent "security regression testing" survey of the LLM era; the classical literature (pre-2023) was out of scope.
- The 71.5% invalid-PoC figure is unverified.

## Q3. Patch validation: checking that a security fix is complete, and how often fixes are incomplete

### Takeaway
About 7% of OSS security fixes are incomplete (Li & Paxson, CCS 2017, the canonical estimate), and roughly half of 2022's in-the-wild 0-days that Project Zero had analysed by mid-year were variants of patched bugs. For LLM-generated patches, validating against the same evidence used to construct the patch is overoptimistic. P2Patch finds a distinct bypass exploit in 41% of runs after the original PoV was blocked. Paired exploit + functional oracles (Vul4Py) and exploit-based evaluation (VulnRepairEval) are the current best practice.

### Cited Findings

**P2Patch (seed paper)**
- "P2Patch: Exploit-Guided Vulnerability Repair". Iranmanesh, Moradi Sabet, Marefat, Javidi Ghasr, Nereyabagabo, Amouzesh, Malhi, Velasco, Chung, Tayebi. arXiv:2610.20245 [cs.CR], 14 Oct 2026; no peer-reviewed venue listed; 25 pages, code on GitHub. — [arXiv](https://arxiv.org/abs/2610.20245)
- Method:
  - An exploitation agent builds a PoV from a normalized finding.
  - A patching agent repairs the program.
  - The exploitation agent re-attacks for a distinct exploit; each success becomes a permanent requirement.
  - Construction-time PoVs are kept separate from held-out evaluation oracles (oracle separation). — [arXiv](https://arxiv.org/abs/2610.20245)
- Results on 101 C/C++ and Java CVE subjects:
  - In 41% of runs, a distinct confirmed exploit was found after the patch had blocked its original PoV.
  - Held-out fix-closed coverage: 78.1% (single-pass Claude Code) → 84.7%.
  - Beyond-upstream coverage: 42.1% → 62.5%. — [arXiv](https://arxiv.org/abs/2610.20245)

**Exploit- and functional-oracle evaluation of LLM repair**
- Vul4Py, "Vul4Py: Benchmarking Automated Vulnerability Repair in Python with Paired Exploit and Functional Oracles". Tan Bui, Ting Zhang, Ferdian Thung, Yunpeng Xiong, Penghao Jiang, Xin Zhou, David Lo. arXiv:2608.00692, Aug 2026.
  - Dataset: 100 vulnerabilities from 60 projects across 60 CWEs.
  - Repair: OpenHands repaired 41/100, the best direct LLM 4, and APPATCH 2, all with the same backbone.
  - Oracles: the exploit-only oracle would accept 119 patches; the paired oracle rejects 15 (about 13%) for functional regressions; 98/104 admitted patches were manually confirmed equivalent. — [arXiv](https://arxiv.org/abs/2608.00692)
- VulnRepairEval, "VulnRepairEval: An Exploit-Based Evaluation Framework for Assessing Large Language Model Vulnerability Repair Capabilities". Wang et al. arXiv:2509.03331, Sep 2025.
  - Dataset: 23 Python CVEs with working PoCs, filtered from 400+ CVEs.
  - Results: 12 LLMs tested; the best repaired 5/23 (about 21.7%); enhanced prompting and multi-agent setups helped little. — [arXiv](https://arxiv.org/abs/2509.03331)
- "Red Teaming Program Repair Agents: When Correct Patches can Hide Vulnerabilities", arXiv:2509.25894. It introduces SWExploit: adversarial patches that pass tests but hide vulnerabilities. Only the title and abstract snippet were seen; numbers **unverified**. — [arXiv](https://arxiv.org/pdf/2509.25894)

**How often human security fixes are incomplete**
- Li & Paxson, "A Large-Scale Empirical Study of Security Patches", CCS 2017 (pre-2023 but the canonical baseline). It covers 4,000+ fixes for 3,000+ vulnerabilities in 682 projects: about 7% of fixes failed to fully remedy the hole and about 5% were regressive. — [PDF](https://www.icir.org/vern/papers/patch-study.ccs17.pdf)
- "Why Not Fix It Once and for All? An Empirical Study of Multiple Patches for Vulnerability Fixes in Open-Source Software". Weiliang Qi, Youpeng Li, Xinda Wang. arXiv:2607.13206; accepted at ESORICS 2026 per the arXiv comments.
  - It covers 1,646 manually examined multi-patch fix records, a taxonomy of 3 categories / 6 subcategories of causes, and an evaluation of detectors for confirming complete remediation.
  - The percentages are in the full text, which I did not read. — [arXiv](https://arxiv.org/abs/2607.13206)
- Project Zero (Maddie Stone), "2022 0-day In-the-Wild Exploitation…so far", June 2022.
  - At least 9 of 18 in-the-wild 0-days were variants of previously patched bugs, and 4 of those were variants of 2021 ITW 0-days.
  - Mechanisms: incomplete fixes that patched the PoC path, not the root cause (win32k, Chromium), and regressions (WebKit "Zombie" bug fixed in 2013, regressed in 2016).
  - The full-year 2022 review counts 17 of 41 ITW 0-days as variants of previously reported vulnerabilities. — [Project Zero](https://projectzero.google/2022/06/2022-0-day-in-wild-exploitationso-far.html), [Google Security Blog 2023](https://security.googleblog.com/2023/07/the-ups-and-downs-of-0-days-year-in.html?m=1)
- Industry data (secondary, weaker):
  - Terra Security (2026, reported by Mallory): 2.3% of GitHub-advisory fixes needed another patch within 90 days, and KEV vulnerabilities' fixes broke about 4× more often. — [Mallory](https://mallory.ai/stories/01a1559b-e0e1-7fe6-89a1-3990cfcfac4c)
  - Netlas blog: 15.5% of patches need follow-up fixes (8.05% incomplete, 4.15% incorrect). The underlying study is unnamed, so treat it with caution. — [Netlas](https://netlas.io/blog/when_patches_fail/)

### Inferences
- Patch validation for company Z can reuse the rule and test artifacts from Q1/Q2:
  - A rule that still fires on the fixed HEAD at other locations is a direct "incomplete fix / sibling" signal.
  - A P2Patch-style adversarial agent attacking the fix gives a bypass rate that can be compared with P2Patch's 41% and Li & Paxson's 7%.
- Oracle separation (P2Patch, PoC-Gym, Vul4Py) is the methodological standard a reviewer will expect. The artefacts used to build a rule or test must differ from those used to evaluate it, for example held-out later incidents or manually written variants.

### Gaps
- The exact percentages in arXiv:2607.13206 were not extracted.
- No 2023–2026 study gives a per-company rate of incomplete internal security fixes. Company Z data would be novel.
- "PatchVerif" (USENIX Security 2023) concerns faulty patches in robotic vehicles. Its relevance to security-fix completeness in enterprise code is low; it was not verified in detail.

## Q4. Recurrence: how common are recurring vulnerabilities and variants within the same project?

### Takeaway
Recurrence is common but rarely exact. In ISSTA 2025's study of 4,569 recurring vulnerabilities, only 28% were identical clones and 63% were heavily modified (Type-III). 31% of vulnerabilities have "similar-but-patched" variants, and in mature projects, vulnerability fixes in utility files recur more than 50% of the time. Clone or exact-match rules will therefore miss most recurrences, which favours semantic rules or LLM variant search.

### Cited Findings
- Cao et al., "Recurring Vulnerability Detection: How Far Are We?", ISSTA 2025 (DOI 10.1145/3728901).
  - Of 4,569 recurring vulnerabilities, only 28% are Type-I (identical) clones and 63% are Type-III (heavily modified) because of version evolution and reuse.
  - The scope is mainly cross-repository reuse. — [PDF](https://chenbihuan.github.io/paper/issta25-cao-antman.pdf), [ACM DL](https://dl.acm.org/doi/10.1145/3728901)
- "Similar but Patched Code Considered Harmful — The Impact of Similar but Patched Code on Recurring Vulnerability Detection and How to Remove Them", arXiv:2412.20740.
  - 31% (2,647) of 8,570 vulnerabilities have at least one vulnerable function with similar-but-patched variants, and 18% at function level.
  - This matters because SBP code causes false positives for clone-based recurrence detectors. — [arXiv](https://arxiv.org/pdf/2412.20740)
- "Unsafe and Unused? A History of Utility Code in Mature Open Source Projects", arXiv:2604.28146.
  - Across 7 projects, 717 files were fixed for more than one vulnerability, and 9.6% of them were util files.
  - Util-file vulnerability fixes were recidivistic more than 50% of the time, except in Linux and systemd. — [arXiv](https://arxiv.org/pdf/2604.28146)
- Yue, Meng et al., "A Characterization Study of Repeated Bug Fixes", ICSME 2017 (general bugs, pre-2023). 15–20% of bugs involve repeated fixes, and 73–92% of repeated-fix groups are applied to code clones. — [PDF](https://people.cs.vt.edu/nm8247/publications/ruru-icsme-2017-camera-ready.pdf)
- Project Zero 2022: 17/41 ITW 0-days were variants of previously reported bugs, and one variant reappeared 12 months after the original patch. — [Google Security Blog](https://security.googleblog.com/2023/07/the-ups-and-downs-of-0-days-year-in.html?m=1), [Project Zero](https://projectzero.google/2022/06/2022-0-day-in-wild-exploitationso-far.html)
- KNighter's Linux bugs found from past-fix-derived checkers had been latent for 4.3 years on average. This is indirect evidence that sibling bugs of fixed bugs persist in the same codebase. — [arXiv](https://arxiv.org/abs/2503.09002v3)
- A within-project ICSE 2020 study ("A Large-Scale Empirical Study on Vulnerability Distribution within Projects…", 3,938 vulnerabilities in 5 projects) examines recurrence, but I did not retrieve its headline figure. — [PDF](https://netsec.ccert.edu.cn/files/papers/icse20-vul.pdf)

### Inferences
- For company Z, the measurable research questions are:
  - What fraction of past security fixes had a later sibling fix (same CWE, same component, or same rule match)?
  - Would the LLM rule generated from fix #k have flagged fix #k+j before it happened? This is retrospective replay over git history.
- Since about 63% of recurrences are Type-III, Semgrep rules should be checked for generalization, for example against LLM-generated semantic variants, not just the literal patched lines.

### Gaps
- Within-company (closed-source) recurrence rates: I found no published data. This is a genuine contribution opportunity.
- I did not retrieve exact within-project recurrence percentages (ICSE 2020).

## Q5. Gaps a 7-person team could fill in about 3 weeks on company Z's codebase

### Takeaway
The literature validates rules and tests on public CVEs, using the vuln-vs-patched oracle on the source repository only. The open, publishable gap is an industrial case study that:
1. mines company Z's own security fixes and incidents;
2. synthesizes Semgrep (and optionally CodeQL) rules plus regression tests with an agent;
3. validates them with oracle separation;
4. replays history to measure would-have-prevented recurrence;
5. measures precision on the current HEAD and developer acceptance in CI.

Each element has precedent (QLCoder, KNighter, Autogrep, ACH, P2Patch), but I found no paper that combines them on proprietary code.

### Cited Findings (anchors for each gap)
- Precision only on the source repo: QLCoder reports no FP evaluation on other codebases, and its oracle may admit FP paths in both versions. — [QLCoder v4](https://arxiv.org/html/2511.08462v4)
- Overfitting is the dominant failure: Autogrep removed 71.15% of rules as overly specific, and vuln-vs-patched validation misses variants. — [Autogrep](https://lambdasec.github.io/AutoGrep-Automated-Generation-and-Filtering-of-Semgrep-Rules-from-Vulnerability-Patches/)
- An FP rate of about 35% even after LLM triage (KNighter) shows that a triage layer is needed in CI. — [KNighter](https://arxiv.org/html/2503.09002v3)
- Developer acceptance is measurable in CI: ACH's 73% acceptance is a methodology template. — [Meta ACH](https://arxiv.org/abs/2501.12862)
- Industrial FP studies (Tencent) show developers' sensitivity to FPs and that hybrid filtering works (94–98% FP removal). — [Tencent study](https://www.researchgate.net/publication/400117710_Reducing_False_Positives_in_Static_Bug_Detection_with_LLMs_An_Empirical_Study_in_Industry)
- Single-pass validation overestimates fix completeness (P2Patch: 41% of runs found a bypass); oracle separation is expected. — [P2Patch](https://arxiv.org/abs/2610.20245)
- Test validity: runtime-"successful" PoCs often do not reach the sink (PoC-Gym: 65/116 post-hoc valid). — [PoC-Gym](https://arxiv.org/abs/2602.04165)
- Cost reference points:

  | System | Cost per item |
  |---|---|
  | QLCoder | $2.90 and about 62 min per CVE |
  | CVE-Genie | $2.77 per CVE |
  | PoCGen | $0.02 per npm exploit |

  — [QLCoder](https://arxiv.org/html/2511.08462v4), [CVE-Genie](https://arxiv.org/abs/2509.01835), [PoCGen](https://arxiv.org/html/2506.04962v3)

### Inferences (a concrete, feasible study design; my synthesis, not from a source)
- **RQ1 (rule synthesis yield)**
  - Input: N company security fix commits and incident tickets, with N of about 20–60 realistic in 3 weeks.
  - Measure: the fraction for which an agent (Claude Code / Codex + Semgrep `--test` + optional CodeQL LSP via MCP, following QLCoder) produces a rule that fires on the pre-fix commit and is silent on the post-fix commit.
  - Report cost and time per incident.
  - Baselines: zero-shot LLM, and the Semgrep registry / stock CodeQL suites.
- **RQ2 (generalization / variant recall)**
  - For each rule, have a separate LLM, or team members, write K semantic variants (Type-III-style re-introductions). Measure recall.
  - Compare with stock rules and literal-match rules. This answers the "63% Type-III" concern.
- **RQ3 (precision on company code)**
  - Run all rules on the current HEAD of all company Z repos and manually triage the hits (two raters plus Cohen's kappa).
  - Report TP / FP / "true but won't fix", and the effect of an LLM triage filter (as in KNighter, Tencent).
- **RQ4 (retrospective recurrence prevention)**
  - Replay git history: for each fix at time t, would the rules synthesized from earlier fixes (time < t) have flagged it before it was introduced or fixed?
  - Also: what fraction of company fixes had later siblings? This would be the first closed-source recurrence figure.
- **RQ5 (regression tests and fix completeness)**
  - For web/API-type incidents, generate PoV tests that fail pre-fix and pass post-fix, checking via coverage that the patched lines are executed (PoC-Gym lesson).
  - Optionally run a P2Patch-style bypass agent on the actual company fix. Report the bypass rate against P2Patch's 41% and Li & Paxson's 7%.
- **RQ6 (developer acceptance)**
  - Put the rules and tests into CI as non-blocking PR comments for 1–2 weeks, or show them to company developers in a survey or think-aloud session.
  - Measure accept / dismiss rates, as in ACH.
- **Threats to validity to pre-empt:**
  - LLM memorization (company code is private, which is a strength);
  - small N;
  - selection bias of incidents with clean fix commits;
  - oracle leakage (keep evaluation variants and incidents held out from synthesis).
- **Variant analysis idea:** KNighter (92 Linux bugs) and Big Sleep (SQLite) give strong precedent. On company code, novelty comes from measuring how many sibling bugs per fixed incident exist and how many are confirmed by company developers.

### Gaps
- None of the surveyed works reports results on proprietary enterprise code, rule decay over time (maintenance), or the developer-review burden per rule. All of these are open.
- No sources were found on Semgrep-specific LLM rule-synthesis accuracy in a peer-reviewed venue. Autogrep is a technical report.
- Licensing or deployment constraints (Semgrep vs. Opengrep after Semgrep's license change, which Autogrep cites as motivation) may matter for company Z, but were not researched in depth. — [Autogrep GitHub](https://github.com/lambdasec/autogrep)
