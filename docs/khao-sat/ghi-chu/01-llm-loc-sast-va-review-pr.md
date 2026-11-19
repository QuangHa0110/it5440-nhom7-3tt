# LLM-assisted SAST alert triage and LLM/agent security review of PRs (2023–2026): state of the art and gaps

Scope notes for the report writer:
- Research done 2026-11-07. Many 2026 items are arXiv preprints that are not peer reviewed. Several report model names past my training cutoff (e.g., "GPT-6 sol", "Grok 4.6", "Sonnet 5", "GPT-5.5"). They are copied exactly as the arXiv abstracts give them; I could not check them independently.
- Most numbers come from arXiv abstract pages or vendor blogs that I fetched or saw in search results. I did not read full PDFs, so per-table details such as how many TPs were dropped are often missing and are listed under Gaps.
- I did not check the seed papers (QLCoder 2511.08462, 2609.15425, GONDAR 2604.01645, P2Patch 2610.20245). They were out of scope.

---

## Q1. LLMs for SAST alert triage / false-positive (FP) reduction: what has been done, what precision/recall changes, what failure modes?

### Takeaway
This area is crowded and moving fast. Benchmark papers (ZeroFalse, LLM4FPM, IRIS), an agent comparison at ISSTA 2026 ("Sifting the Noise", which uses CodeQL on real Java projects), and a Tencent industrial study (ICSE 2026 SEIP) all report that 72–98% of FPs can be removed, and hybrid static analysis + LLM methods beat plain prompting. Every source names the same main failure mode: aggressive filtering suppresses true positives (TPs). Vendors (Semgrep, Datadog, CyberArk Vulnhalla) say the same and deliberately tune toward keeping TPs. "Tools + LLM FP filter" (method B in the team draft) is therefore well covered and not novel by itself.

### Cited Findings

**Academic: benchmarks and techniques**
- **IRIS: LLM-Assisted Static Analysis for Detecting Security Vulnerabilities**. Ziyang Li, Saikat Dutta, Mayur Naik. ICLR 2025, arXiv:2405.17238.
  - IRIS uses an LLM to infer taint sources and sinks and to triage paths, combined with CodeQL. It introduces **CWE-Bench-Java** (120 manually validated vulnerabilities in real Java projects).
  - IRIS + GPT-4 detects 55 of 120 vulnerabilities, against 27 for CodeQL (+28, +103.7%). Average false discovery rate is 84.82%, which is 5.21 points lower than CodeQL's. It found 4 previously unknown vulnerabilities in 30 Java projects.
  - Discrepancy: arXiv v1 said 69 detected; the ICLR version says 55.
  - Even IRIS has a very high false discovery rate (about 85%), so precision is still the bottleneck.
  - Sources: [ICLR proceedings](https://proceedings.iclr.cc/paper_files/paper/2025/hash/582d4e27fa24168f3af1f4582655034b-Abstract-Conference.html); [arXiv](https://arxiv.org/abs/2405.17238); [project site](https://iris-sast.github.io/iris/print.html)
- **ZeroFalse: Improving Precision in Static Analysis with LLMs**. Mohsen Iranmanesh et al. arXiv:2510.02534, Oct 2025, cs.SE.
  - Analyzer findings become structured input, enriched with flow-sensitive traces, code context and CWE-specific knowledge. Ten LLMs were evaluated.
  - Best F1 is 0.912 on the OWASP Java Benchmark and 0.955 on OpenVuln, with precision and recall both above 90%.
  - CWE-specialized prompts beat generic prompts, and reasoning-oriented LLMs give the best precision/recall balance.
  - Source: [arXiv](https://arxiv.org/abs/2510.02534)
- **Utilizing Precise and Complete Code Context to Guide LLM in Automatic False Positive Mitigation (LLM4FPM)**. Chen et al. (USTC). arXiv:2411.03079.
  - Uses eCPG/Joern-based code slicing as context for the LLM.
  - On Juliet: F1 above 99% across CWEs, $0.384 per warning, 4.7 s per warning.
  - On 8 real-world OSS projects (v2): over 85% of FPs eliminated. In v1 it identified 37 of 43 confirmed FPs (86.05%).
  - Failure causes: Joern parsing failures, after which the slicer falls back to the whole function, and LLM difficulty with complex context.
  - D2A label accuracy improves from 53% to 86% (v2); v1 said 82%.
  - Peer-review status: not verified.
  - Source: [arXiv](https://arxiv.org/abs/2411.03079)
- **Minimizing False Positives in Static Bug Detection via LLM-Enhanced Path Feasibility Analysis (LLM4PFA)**. arXiv:2506.10322.
  - Filters 72–96% of false alarms across bug types with GPT-4o-mini as the backbone. This figure comes from a search summary; I did not fetch the page.
  - Source: [arXiv PDF](https://arxiv.org/pdf/2506.10322)
- **LLM-Driven Adaptive Source-Sink Identification and False Positive Mitigation for Static Analysis**. arXiv:2511.04023. I saw only the title in search results, no numbers.
  - Source: [arXiv PDF](https://arxiv.org/pdf/2511.04023)
- **Sifting the Noise: A Comparative Study of LLM Agents in Vulnerability False Positive Filtering**. Yunpeng Xiong, Ting Zhang. arXiv:2601.22952, v3 Jul 2026, "to appear in ISSTA 2026".
  - Compares the agent frameworks Aider, OpenHands and SWE-agent with Claude Sonnet 4, GPT-5 and weaker backbones.
  - Datasets: OWASP Benchmark, real-world Java projects with CodeQL alerts, and a post-cutoff OSS-Fuzz C/C++ set.
  - OWASP: the FP rate falls from over 92% to as low as 6.3%.
  - Real-world Java (CodeQL): FP identification up to 93.3%.
  - OSS-Fuzz: SWE-agent + Claude Sonnet 4 identifies 95.5% of FPs at 95.5% precision, against 36.4% for vanilla prompting.
  - Agents help with strong models, but gains are limited or inconsistent with weak backbones. Results vary by CWE, and cost differs widely between frameworks. The authors warn that aggressive FP reduction can suppress true vulnerabilities.
  - One search summary said the real-world Java set is 50 Vul4J cases. The abstract page does not mention Vul4J, so check the full paper.
  - This is the closest published work to method B, and arguably to D, on Java.
  - Source: [arXiv](https://arxiv.org/abs/2601.22952)
- **QASecClaw: A Multi-Agent LLM Approach for False Positive Reduction in Static Application Security Testing**. arXiv:2605.01885. Title only; no numbers retrieved.
  - Source: [arXiv PDF](https://arxiv.org/pdf/2605.01885)
- **Assisting Static Analysis with Large Language Models: A ChatGPT Experiment**. ESEC/FSE 2023 Ideas, Visions and Reflections track. An early, small-scale work; title only.
  - Source: [FSE 2023 page](https://2023.esec-fse.org/details/fse-2023-ideas--visions-and-reflections/4/Assisting-Static-Analysis-with-Large-Language-Models-A-ChatGPT-Experiment)

**Industrial studies**
- **Reducing False Positives in Static Bug Detection with LLMs: An Empirical Study in Industry**. Xueying Du, Jiayi Feng, Yi Zou, Wei Xu, Jie Ma, Wei Zhang, Sisi Liu, Xin Peng, Yiling Lou (Fudan + Tencent). arXiv:2601.18844.
  - Listed in ICSE 2026 SEIP; ACM DOI 10.1145/3786583.3786910. The arXiv page itself lists no venue.
  - Setting: Tencent's enterprise-customized static analysis tool (BPcheck), Advertising and Marketing Services code.
  - Dataset: 433 alarms (NPD, out-of-bounds, divide-by-zero), of which 328 are FPs (about 76%) and 105 are TPs. Manual inspection takes about 10–20 minutes per alarm.
  - Hybrid LLM + static analysis techniques (LLM4PFA, LLM4SA) remove 94–98% of FPs "while maintaining high recall". The abstract gives no exact TP-loss figure.
  - Cost per alarm: 2.1–109.5 s and $0.0011–$0.12. The paper includes a case analysis of the limitations of LLM-based reduction in industry.
  - Note: this is C/C++ bug types (NPD/OOB/DBZ), not Java security taint.
  - Sources: [arXiv](https://arxiv.org/abs/2601.18844); [ICSE 2026 SEIP listing](https://conf.researchr.org/details/icse-2026/icse-2026-software-engineering-in-practice/72/Reducing-False-Positives-in-Static-Bug-Detection-with-LLMs-An-Empirical-Study-in-Ind); [artifact repo](https://github.com/LLM4SFPR/static-bug-false-positives-reduction-in-practice)

**Vendors and practitioners (self-reported; not independently validated)**
- **Semgrep Assistant (GPT-4-based auto-triage)**
  - Claims 95% user agreement and 96% security-researcher agreement. A later post cites 96% agreement across more than 6M findings.
  - Out of the box it cuts findings to review by about 20%, and handles about 60% of incoming triage once "memories" (org-specific triage history) are enabled.
  - Semgrep's own engineering post tells a different story under the headline. Version 1 agreed with a 2,000-finding researcher dataset only about 55% of the time. After tuning, agreement was 96% on TPs but only **41% on FPs**: Semgrep deliberately favors keeping TPs over filtering noise.
  - Sources: [Announcing AI noise filtering](https://semgrep.dev/blog/2025/announcing-ai-noise-filtering-and-triage-memories); [60% of triage](https://semgrep.dev/blog/2025/semgrep-is-confidently-handling-60-of-all-triage-for-users-without-reducing-coverage); [How we built it, 96%](https://semgrep.dev/blog/2025/building-an-appsec-ai-that-security-researchers-agree-with-96-of-the-time/); [docs](https://semgrep.dev/docs/semgrep-assistant/overview)
- **Datadog, "Using LLMs to filter out false positives from static code analysis"** (Cole Maring, Kassen Qian)
  - Bits AI labels SAST findings as likely TP or FP. On the OWASP Benchmark, prompts tuned to catch TPs let more FPs through, and prompts tuned to filter FPs risked dropping real issues, so they chose a balance.
  - The product docs describe three tiers:
    - baseline filtering: a toggle that applies to Datadog-hosted scans only;
    - "agentic filtering" with cross-file context and symbol search, limited to injection rules (SQLi, command injection);
    - custom context, where teams describe their own sanitizers.
  - Sources: [Datadog blog](https://www.datadoghq.com/blog/using-llms-to-filter-out-false-positives); [Datadog docs: AI-enhanced SAST](https://docs.datadoghq.com/security/code_security/static_analysis/ai_enhanced_sast/)
- **CyberArk Vulnhalla** (open source; CodeQL + GPT-4/GPT-4o post-processing)
  - Claims "up to 96%" FP reduction for specific issue types; the Black Hat Europe 2025 talk said up to 97%.
  - Strict mode returns only TPs but mislabels some TPs as FPs. The output verdicts are TP, FP, or "Needs More Data".
  - CyberArk itself notes that little academic work targets CodeQL triage specifically.
  - Source: [CyberArk blog](https://www.cyberark.com/resources/threat-research-blog/vulnhalla-picking-the-true-vulnerabilities-from-the-codeql-haystack)
- **GitHub Security Lab "Taskflow Agent"** for AI-supported vulnerability triage. Title only; not read.
  - Source: [GitHub blog](https://github.blog/security/ai-supported-vulnerability-triage-with-the-github-security-lab-taskflow-agent/)

**Failure modes reported across sources**
- **TP suppression.** Aggressive FP filtering suppresses real vulnerabilities ([Sifting the Noise](https://arxiv.org/abs/2601.22952)). Datadog reports the same trade-off ([Datadog](https://www.datadoghq.com/blog/using-llms-to-filter-out-false-positives)). Vulnhalla's strict mode mislabels some TPs ([CyberArk](https://www.cyberark.com/resources/threat-research-blog/vulnhalla-picking-the-true-vulnerabilities-from-the-codeql-haystack)). Semgrep keeps FP agreement low (41%) to protect TPs ([Semgrep](https://semgrep.dev/blog/2025/building-an-appsec-ai-that-security-researchers-agree-with-96-of-the-time/)).
- **Context-extraction failures** (parser or slicer) degrade LLM verdicts ([LLM4FPM](https://arxiv.org/abs/2411.03079)).
- **Dependence on model strength.** Weak backbones gain little or inconsistently from agents ([Sifting the Noise](https://arxiv.org/abs/2601.22952)).
- **CWE dependence.** Generic prompts underperform; CWE-specific prompts help ([ZeroFalse](https://arxiv.org/abs/2510.02534); [Sifting the Noise](https://arxiv.org/abs/2601.22952)).

### Inferences
- High numbers like 93–98% FP removal mostly come from OWASP Benchmark, Juliet, or curated alarm sets with about 76–92% FP base rates. On real company code, with the seed paper's 22.2% FP rate, a filter that drops even 5–10% of TPs may cost more than it saves. That base-rate effect has barely been studied and is a usable angle.
- To be publishable today, method B needs either (a) a new setting (real company, new language or framework mix, Vietnamese SME), (b) an explicit TP-loss / cost-of-miss analysis, or (c) an open-weight local model. B alone on OWASP or Vul4J is already done.

### Gaps
- Exact TP-loss (recall drop) numbers for the Tencent study and Sifting the Noise; I read the abstracts only.
- Whether Sifting the Noise uses Vul4J. A search snippet said "50 Vul4J cases", but the abstract does not say so.
- Candidate citations I know of but did not re-verify this session (check before citing):
  - Kang, Le, Lo, "Detecting False Alarms from Automatic Static Analysis Tools: How Far are We?" (ICSE 2022), the "golden features" data-leakage critique of actionable-warning ML.
  - LLift, "The Hitchhiker's Guide to Program Analysis: A Journey with Large Language Models" (arXiv 2308.00245, OOPSLA 2024).
  - BugLens (arXiv 2504.11711, Linux kernel taint FP reduction).
  - Microsoft CORE (FSE 2024).
  - Google, Ericsson and Microsoft industrial LLM SAST-triage papers. Searches surfaced none besides Tencent, so I found no reliable sources for those companies specifically.

---

## Q2. LLM/agent security review of PRs and commits: papers, benchmarks, industrial bots. Has the A/B/C/D comparison on reverted-CVE PRs been done?

### Takeaway
"Agent reviews a PR for security" (method C) is now a hot benchmark topic in 2026, and **reverting CVE-fix commits to synthesize vulnerable PRs is already published**:
- SEVRA-BENCH builds about 1,000+ PRs by reversing CVE fixes.
- AFCRA-Bench (159 vulnerability/fix pairs with exploits) follows the Vul4J PoC rule.
- SecPRBench (Oct 2026) argues that fix-derived PRs are unrealistic and uses validated real bug-introducing commits instead.

I found no single paper that runs the exact four-way A/B/C/D comparison on Java reverted-CVE PRs. Every component has been studied, though, so the four-way comparison would be incremental and exposed to contamination critiques.

### Cited Findings

**PR / commit security-review benchmarks (2025–2026)**
- **Can Agentic Code Review Catch Vulnerabilities Before They Are Merged? (SecPRBench)**. Yihan Yang, Chenyuan Yang, Zijie Zhao, Anh Nguyen Hoang, Ziqi Zhang, Weidong Wang, Zhiheng Lyu, Lingming Zhang. arXiv:2610.33509, v1 24 Oct 2026, v2 30 Oct 2026, cs.SE.
  - Dataset: 265 tasks from 9 systems (Firefox, V8, OpenSSL, among others), built by an agentic pipeline that harvests, builds and validates **real bug-introducing commits**. The authors explicitly criticize benchmarks that derive reviewed changes from later fixes. Matching to ground truth uses LLM-as-judge.
  - Recall across 8 frontier models: 32.5%–78.1%. The page names Grok 4.6 and GPT-6 sol at the top; I could not verify these model names.
  - 68% of misses flag the right file but argue for a different mechanism.
  - Harnesses: OpenAI's "Codex Security" lowers recall by 8.3 points, mostly by abstaining. Anthropic's "Defending Code" raises recall by 7.7 points at higher cost.
  - No SAST baseline appears in the abstract.
  - Languages are probably mostly C/C++. That is my inference from the projects named.
  - Source: [arXiv](https://arxiv.org/abs/2610.33509)
- **SEVRA-BENCH: Social Engineering of Vulnerabilities in Review Agents**. Rui Melo, Riccardo Fogliato, Sean Zhou, Pratiksha Thaker, Zhiwei Steven Wu. arXiv:2606.13757, Jun 2026, cs.CR.
  - Each PR **automatically reverses a historical vulnerability-fixing commit**, covering the top 10 of the 2025 CWE Top 25. The PR is wrapped in one of 15 social-engineering framings (urgency, prior approval, authority).
  - Size: a challenge split of about 1,000 adversarial PRs; a search summary said 1,062. 8 review agents are evaluated.
  - Finding: agents are "susceptible to narrative manipulation".
  - **This directly overlaps the team's "revert CVE fix → PR" construction.**
  - Sources: [arXiv](https://arxiv.org/abs/2606.13757); [HTML](https://arxiv.org/html/2606.13757v1)
- **Adaptive Code Revision Attacks on AI Pull Request Reviewers (AFCRA-Bench)**. Jingzhi Gong, Jie M. Zhang, Gunel Jahangirova, Meng Wang. arXiv:2610.05399, Oct 2026.
  - 159 disclosed vulnerabilities with executable exploits.
  - PoC acceptance follows the Vul4J rule: the exploit must trigger on the pre-fix code and be blocked by the historical fix. This is the same oracle as QLCoder's "fires on vulnerable, silent on patched".
  - Five-round attacks against "Sonnet 5" and "GPT-5.5" reviewers achieve 2.5x and 12.5x the success rate of the strongest text or comment attack.
  - Source: [arXiv](https://arxiv.org/abs/2610.05399)
- **PRWeaver: Evaluating LLM-Based Code Auditors against Long-Horizon Malicious Pull Requests**. arXiv:2608.02693.
  - 208 execution-validated attacks across 10 repositories, each under 4 review formats.
  - Detection is 16–22% when the auditor reviews the whole window of changes, against 50–60% when reviewing each PR separately.
  - This comes from a search snippet; I did not fetch it.
  - Source: [arXiv PDF](https://arxiv.org/pdf/2608.02693)
- **Benchmarking LLMs and LLM-based Agents in Practical Vulnerability Detection for Code Repositories (JITVul)**. ACL 2025 (long).
  - 1,758 commit pairs across 91 vulnerability types, linking each function to its introducing and fixing commits.
  - ReAct-style agents separate vulnerable from benign code better than plain LLMs.
  - Numbers come from a snippet.
  - Source: [ACL Anthology](https://aclanthology.org/2025.acl-long.1490/)
- **SecureVibeBench: Benchmarking Secure Vibe Coding of AI Agents via Reconstructing Vulnerability-Introducing Scenarios**. arXiv:2509.22097. Title only.
  - Source: [arXiv PDF](https://arxiv.org/pdf/2509.22097)

**LLM security code review (comment generation and evaluation)**
- **An Insight into Security Code Review with LLMs: Capabilities, Obstacles, and Influential Factors**. Jiaxin Yu, Peng Liang et al. arXiv:2401.16310 (v5 Dec 2025; v2 was titled "Security Code Review by Large Language Models").
  - Dataset: 534 code-review files from OpenStack Nova/Neutron and Qt Base/Creator.
  - LLMs outperform state-of-the-art SAST tools in security code review. DeepSeek-R1 is best, then GPT-4 (v5).
  - v4 framed LLM capability as "limited" but still better than SAST, so cite a specific version.
  - Source: [arXiv](https://arxiv.org/abs/2401.16310)
- **SecureReviewer: Enhancing Large Language Models for Secure Code Review through Secure-aware Fine-tuning**. Fang Liu, Simiao Liu, Yinghao Zhu, Xiaoli Lian, Li Zhang. arXiv:2510.26457, ICSE 2026 research track.
  - Secure-aware fine-tuning plus RAG over 261 comment templates; the templates detail comes from a third-party summary. Introduces the SecureBLEU metric and beats SOTA baselines.
  - Code: github.com/SIMIAO515/SecureReviewer.
  - Sources: [arXiv](https://arxiv.org/abs/2510.26457); [ICSE 2026](https://conf.researchr.org/details/icse-2026/icse-2026-research-track/149/SecureReviewer-Enhancing-Large-Language-Models-for-Secure-Code-Review-through-Secure)
- **AutoReview: An LLM-based Multi-Agent System for Security Issue-Oriented Code Review**. FSE 2025 Student Research Competition. Title only.
  - Source: [FSE 2025 SRC](https://conf.researchr.org/details/fse-2025/fse-2025-student-research-competition/5/AutoReview-An-LLM-based-Multi-Agent-System-for-Security-Issue-Oriented-Code-Review)
- **Can Adversarial Code Comments Fool AI Security Reviewers…** Scott Thornton. arXiv:2602.16741, Feb 2026.
  - 100 samples (Python, JavaScript, Java) × 8 comment variants; 8 frontier models (5 commercial, 3 open); 14,012 trials in total.
  - Adversarial comments have non-significant effects (McNemar p > 0.21).
  - Baseline detection: commercial 89–96%, open-source 53–72%.
  - **SAST cross-referencing** (feeding static-analysis findings to the LLM, which is effectively method D) reaches 96.9% detection and recovers 47% of baseline misses.
  - Failures cluster on race conditions, timing side channels, and complex authorization logic.
  - Source: [arXiv](https://arxiv.org/abs/2602.16741)

**SAST vs LLM head-to-head comparisons (relevant to A vs C)**
- **RealVuln: Benchmarking Rule-Based, General-Purpose LLM, and Security-Specialized Scanners on Real-World Code**. John Pellew, Faizan Raza. arXiv:2604.13764, Apr 2026.
  - 26 intentionally vulnerable Python repositories; 796 labels (676 vulnerabilities, 120 FP traps).
  - 15 scanners: 3 rule-based, 10 general LLMs, 2 security-specialized.
  - F3: Kolega.Dev 73.0, Claude Sonnet 4.6 51.7, Semgrep 17.7. F1: Sonnet 4.6 60.9, Kolega.Dev 52.4.
  - Source: [arXiv](https://arxiv.org/abs/2604.13764)
- **Snyk VulnBench JS 1.0: Can LLMs Find the Same Bugs Twice?** arXiv:2606.15762.
  - Concludes that LLM and SAST catch different failure modes. Caveat: its SAST reference set has 100% recall by construction. This comes from a snippet.
  - Source: [arXiv PDF](https://arxiv.org/pdf/2606.15762)
- **LLM vs. SAST: A Technical Analysis on Detecting Coding Bugs of GPT4-Advanced Data Analysis**. arXiv:2506.15212.
  - Small: 32 snippets and 2 SAST tools. Recommends LLMs as a complement to SAST, not a replacement.
  - Source: [arXiv PDF](https://arxiv.org/pdf/2506.15212)

**Industrial AI security / code-review bots**
- **Anthropic Claude Code security review** (Aug 2025)
  - Ships as a `/security-review` command and a GitHub Action that reviews new PRs, filters FPs with customizable rules, and posts inline comments with fixes.
  - Anthropic reports anecdotal internal catches, such as an RCE via DNS rebinding caught before merge. There are no measured precision or recall numbers.
  - Deriv published a third-party write-up of its deployment.
  - Sources: [Anthropic](https://www.anthropic.com/news/automate-security-reviews-with-claude-code); [Deriv write-up](https://derivai.substack.com/p/automated-security-code-reviews-claude-code-github-actions)
- **GitHub Copilot Autofix** (GA Aug 2024)
  - Median time to commit a fix for CodeQL PR alerts: 28 minutes, against 1.5 hours manually (">3x faster"). Beta data covers about May–July 2024.
  - XSS fixes took about 22 minutes against about 3 hours.
  - Since June 2025 the security overview dashboard shows MTTR for CodeQL PR alerts. A deployment study could reuse this metric.
  - Sources: [GitHub blog "Found means fixed"](https://github.blog/news-insights/product-news/secure-code-more-than-three-times-faster-with-copilot-autofix/); [TechTarget](https://www.techtarget.com/cybersecurity/news/366603045/GitHub-Copilot-Autofix-tackles-vulnerabilities-with-AI); [GitHub changelog 2025-06-17](https://github.blog/changelog/2025-06-17-mean-time-to-remediate-metric-for-codeql-pull-request-alerts-now-included-on-the-security-overview-dashboard)
- **Sourcegraph "Sherlock"** (Apr 2025 blog; internal tool)
  - The security team's PR/diff reviewer uses Cody context, targeted prompts and repo metadata. It ingests scanner alerts and correlates them with LLM findings to cut noise. This is essentially method D in production, but no quantitative evaluation was found.
  - Source: [Sourcegraph blog](https://sourcegraph.com/blog/lessons-from-building-sherlock-automating-security-code-reviews-with-sourcegraph)
- **General (non-security) LLM code-review deployments that report developer action rates.** These are useful templates for metrics.
  - **RovoDev Code Reviewer at Atlassian** (arXiv:2601.01129, ICSE-SEIP 2026)
    - Scale: a year-long deployment over more than 1,900 repos and more than 54k comments.
    - Code resolution rate: 38.70%, against 44.45% for human comments.
    - Median PR cycle time: −30.8%. Human comments: −35.6%.
    - Source: [arXiv](https://arxiv.org/abs/2601.01129)
  - **Cihan et al., "Automated Code Review In Practice"** (arXiv:2412.18531, ICSE-SEIP 2025; Qodo PR-Agent in industry)
    - Scale: about 238 practitioners and 4,335 PRs, of which 1,568 received automated review.
    - Comments resolved: 73.8%.
    - PR closure time rose from 5h52m to 8h20m.
    - Source: [arXiv](https://arxiv.org/abs/2412.18531)
  - **Google, "Resolving Code Review Comments with Machine Learning"** (ICSE-SEIP 2024)
    - About 5% (later 7.5%) of reviewer comments are addressed by applying ML-suggested edits.
    - Source: [ICSE 2024 SEIP](https://conf.researchr.org/details/icse-2024/icse-2024-software-engineering-in-practice/35/Resolving-Code-Review-Comments-with-Machine-Learning)

**Status of the A/B/C/D comparison**

| Method | Closest published work |
|---|---|
| A vs C (SAST vs LLM reviewer) | Yu et al. 2401.16310 (OpenStack/Qt); RealVuln (Python); Snyk VulnBench JS |
| B (SAST + LLM filter, Java/CodeQL) | Sifting the Noise (ISSTA 2026); ZeroFalse; IRIS |
| C (agent on PR, reverted-CVE PRs) | SEVRA-BENCH; AFCRA-Bench; SecPRBench (real introducing commits) |
| D (SAST hints + LLM) | Thornton 2602.16741 (SAST cross-reference 96.9%); Sourcegraph Sherlock (industrial, no numbers); Sifting the Noise (agent + CodeQL) |
| All four on Java Vul4J / Project KB reverted-CVE PRs | Not found in any single paper |

- One search summary said it found no benchmark that uses **Project KB** specifically to synthesize revert PRs for LLM review ([search context, reliability study](https://arxiv.org/html/2610.10150v1)). Treat that as "not found", not as proven absent.

### Inferences
- The team's A/B/C/D-on-reverted-CVE-Java-PRs design is **moderately crowded**. Its specific combination may be unpublished, but each arm has close prior work, and SecPRBench explicitly attacks the revert-a-fix construction as unrealistic.
- A reviewer would likely ask: "how does this differ from SEVRA-BENCH, Sifting the Noise and SecPRBench, and how do you rule out memorization of public Vul4J CVEs?" Without a company-specific or post-cutoff component, it reads as a replication.
- A credible differentiator is to run A/B/C/D on **company Z's own historical PRs** (private, so not memorized) or on post-cutoff CVEs. The reverted-CVE set would then serve only as a sanity check.

### Gaps
- I could not see full SEVRA-BENCH details: languages, models, baseline versus manipulated detection rates, and whether Java or Vul4J is included.
- I found no independent numbers for Snyk DeepCode AI / Snyk Code AI triage, and no paper specifically evaluating Datadog's agentic filtering.
- Copilot Autofix's primary blog statistics were relayed via secondary outlets (TechTarget); I did not read the GitHub blog text directly.
- I did not search the vulnerability-contributing-commit JIT literature from before 2023 (VCCFinder, CodeJIT, etc.).

---

## Q3. Known pitfalls: memorization/contamination, weak LLM vulnerability detection (PrimeVul), label noise

### Takeaway
Public CVE-based benchmarks (Vul4J, Project KB, OWASP, Juliet, BigVul) are probably in LLM training data, and vulnerability labels are noisy (20–71% inaccurate in widely used datasets). On realistic, deduplicated data, function-level LLM vulnerability detection is close to random (PrimeVul). Any reverted-CVE evaluation therefore needs contamination controls (post-cutoff CVEs, private company code, filename-only or identity probes) and label auditing.

### Cited Findings
- **Vulnerability Detection with Code Language Models: How Far Are We? (PrimeVul)**. Ding et al. ICSE 2025, arXiv:2403.18624.
  - Prior datasets have poor quality, low label accuracy and high duplication; up to 18.9% of test samples leak from training sets.
  - StarCoder2 F1 is 68.26% on BigVul but 3.09% on PrimeVul. GPT-3.5 and GPT-4 are close to random in the strictest settings.
  - Proposes VD-S (FNR at 0.5% FPR) because accuracy is misleading for rare vulnerabilities.
  - Source: [arXiv](https://arxiv.org/abs/2403.18624)
- **Data Quality for Software Vulnerability Datasets**. Roland Croft, M. Ali Babar, Mehdi Kholoosi. ICSE 2023, arXiv:2301.05456.
  - 20–71% of vulnerability labels are inaccurate and 17–99% of data points are duplicated across four datasets. This can inflate benchmark scores.
  - Source: [arXiv](https://arxiv.org/abs/2301.05456)
- **Contamination checks used in triage work.** Sifting the Noise ran a filename-only probe on OWASP; models stayed near chance, which suggests no label memorization. It also used OSS-Fuzz commits about 10–12 months after the model cutoff, where the agent still achieved high FP-filtering performance.
  - These are reusable methodology templates.
  - Source: [Sifting the Noise](https://arxiv.org/abs/2601.22952), via search summary
- **Calibration Without Comprehension: Diagnosing the Limits of Fine-Tuning LLMs for Vulnerability Detection in Systems Software (CWE-Trace)**. arXiv:2606.20502. All figures below come from a search summary.
  - 84% of nominally contaminated samples carried no usable memorization signal.
  - Fine-tuning shifts thresholds without improving reasoning.
  - Best detection is 52.1%, 2.1 points above chance.
  - Source: [arXiv PDF](https://arxiv.org/pdf/2606.20502)
- **Other contamination-aware frameworks.** RustMizan (mutation-based, contamination-aware, Rust; [arXiv 2607.04729](https://arxiv.org/pdf/2607.04729)) and BenchGuard (two-layer contamination-aware evaluation; [UWF](https://ircommons.uwf.edu/esploro/outputs/conferenceProceeding/BenchGuard-A-Two-Layer-Framework-forContamination-Aware-Evaluation/99381839542806600)). Titles and summaries only.
- **On the Reliability of LLM-Based Vulnerability Patching Benchmarks**. arXiv:2610.10150.
  - Notes that agents can edit or delete Vul4J PoV tests to sway the oracle. If the team uses PoV tests as ground truth, tests must be held out from agent write access.
  - Source: [arXiv](https://arxiv.org/html/2610.10150v1), via search summary
- **SecPRBench's realism critique.** Fix-derived PRs (reverting a fix) do not reflect how vulnerabilities are actually introduced ([arXiv 2610.33509](https://arxiv.org/abs/2610.33509)).
  - A reverted fix is typically a small, focused diff, which is easier than a real feature PR in which the bug is incidental. That is my inference, not a claim the paper makes.
- **Adversarial and social-engineering fragility.** PR narratives can manipulate review agents ([SEVRA-BENCH](https://arxiv.org/abs/2606.13757)). Adaptive code revisions defeat Sonnet- and GPT-based reviewers ([AFCRA](https://arxiv.org/abs/2610.05399)). By contrast, simple adversarial comments have no significant effect ([Thornton 2602.16741](https://arxiv.org/abs/2602.16741)).
- **Vendor benchmark pitfall.** Vendor agreement metrics (Semgrep's 96%) are dominated by the TP class, and FP agreement can be far lower (41%) ([Semgrep](https://semgrep.dev/blog/2025/building-an-appsec-ai-that-security-researchers-agree-with-96-of-the-time/)). Reports should give per-class metrics.

### Inferences
- For the team, reverted Vul4J / Project KB CVEs, which mostly predate 2023, are high-contamination. The LLM may "know" the CVE, and the commit message or tests may leak it. Mitigations:
  - rewrite the PR title and message neutrally;
  - strip CVE IDs and the test diff;
  - include post-cutoff CVEs from 2026;
  - add a "patched version" control so each case is scored as a pair (vulnerable flagged, patched silent), mirroring QLCoder's validation criterion;
  - run an identity probe ("which CVE is this?").
- Report per-class precision/recall, VD-S-style metrics at fixed low FPR, and the TP-drop rate of the filter.

### Gaps
- Not re-verified this session: Ullah et al., "LLMs Cannot Reliably Identify and Reason About Security Vulnerabilities (Yet?)" (IEEE S&P 2024, arXiv 2312.12575, SecLLMHolmes), and CleanVul (arXiv 2411.17274) on label noise in fix-commit datasets. Verify before citing.
- I found no study measuring CVE memorization specifically for Vul4J or Project KB Java samples.

---

## Q4. Concrete gaps a 7-student team could address in about 3 weeks with an industrial deployment

### Takeaway
The best openings are not new detection algorithms. They are **deployment-and-measurement studies in an unstudied context**: a Vietnamese company or SME, private code free of contamination, developer action rates on security findings, cost per PR, and open-weight local LLMs against cloud LLMs under code-privacy constraints. Published industrial evidence covers Tencent (FP triage, C/C++), Atlassian and Beko-like settings (general review, not security), and vendor self-reports. None reports **security-specific developer action rates on LLM-triaged SAST findings in PRs**, and I found no open-weight versus cloud comparison for SAST triage.

### Cited Findings (evidence that these are gaps)
- **No industrial security PR study with developer metrics.** Industrial LLM code-review studies with action and resolution metrics exist only for general review: Atlassian's 38.7% resolution ([arXiv 2601.01129](https://arxiv.org/abs/2601.01129)) and Cihan et al.'s 73.8% ([arXiv 2412.18531](https://arxiv.org/abs/2412.18531)). Industrial LLM FP-triage evidence is the Tencent study, offline and on C/C++ bug types ([arXiv 2601.18844](https://arxiv.org/abs/2601.18844)). I found no academic industrial study of LLM security review on live PRs with developer action rates. That is a search result, not proof of absence.
- **Open-weight versus cloud is unstudied.** Searches found no direct study comparing open-weight models (Qwen, Llama, DeepSeek) with GPT or Claude for on-premise SAST triage.
  - The closest items are Thornton's open versus commercial gap in security review: 53–72% against 89–96% detection ([arXiv 2602.16741](https://arxiv.org/abs/2602.16741)).
  - "Sifting the Noise" finds weak backbones gain little from agents ([arXiv 2601.22952](https://arxiv.org/abs/2601.22952)).
  - A 2025 Hawaii thesis tests GPT-4 against Llama 3 on alert adjudication; I saw the abstract only, with no numbers ([ScholarSpace](https://scholarspace.manoa.hawaii.edu/items/42b220fa-17f8-4cfe-9f2b-ba4553e21bc3)).
  - A 2025 paper argues for on-premise triage of sensitive alerts ([arXiv 2512.08169](https://arxiv.org/pdf/2512.08169)).
- **Cost per alarm or PR is reported only offline.** Figures exist for the Tencent setting ($0.0011–$0.12 and 2.1–109.5 s per alarm; [arXiv 2601.18844](https://arxiv.org/abs/2601.18844)) and LLM4FPM ($0.384 per warning; [arXiv 2411.03079](https://arxiv.org/abs/2411.03079)). SecPRBench notes higher cost for harnesses that raise recall ([arXiv 2610.33509](https://arxiv.org/abs/2610.33509)). I found no per-PR cost and latency data from a live CI deployment.
- **Org-specific context.** Organizational memory and custom sanitizer context sharply increase triage automation: Semgrep went from 20% to 60% ([Semgrep](https://semgrep.dev/blog/2025/semgrep-is-confidently-handling-60-of-all-triage-for-users-without-reducing-coverage)), and Datadog offers custom context ([Datadog docs](https://docs.datadoghq.com/security/code_security/static_analysis/ai_enhanced_sast/)). No academic study measures how much company-specific context (sanitizer lists, framework conventions) helps on a real company codebase.
- **A reusable industrial metric.** MTTR for CodeQL PR alerts is a GitHub-native metric that lets a deployment study measure before and after ([GitHub changelog](https://github.blog/changelog/2025-06-17-mean-time-to-remediate-metric-for-codeql-pull-request-alerts-now-included-on-the-security-overview-dashboard)).

### Inferences: lighter-weight, publishable directions, ranked by feasibility in 3 weeks

1. **Deployment study: SAST + LLM triage in company Z's CI on live or recent PRs.** This is B or D as a bot.
   - Measure:
     - alert volume before and after;
     - developer action rate per finding (fixed, dismissed, ignored), using Atlassian-style "code resolution" (commented lines changed in the next commit);
     - triage time saved;
     - cost per PR (tokens, $, latency);
     - TP-loss, from a manually labeled sample of filtered-out alerts.
   - Novelty: first Vietnamese/SME industrial evidence; security-specific action rates; private code (no contamination).
   - Size: about 100–300 PRs and a few hundred alerts is realistic.
2. **Open-weight local LLM versus cloud LLM for SAST FP triage under code-privacy constraints.**
   - Compare, for example, a Qwen / DeepSeek-Coder-class model on a company GPU against GPT or Claude on the same labeled company alerts.
   - Report accuracy, TP-drop and cost per alert, and whether it runs on a single GPU.
   - This directly fills a gap no source covered.
3. **Base-rate-aware evaluation.**
   - Re-measure FP-filter value at a realistic FP prevalence: the seed paper's 22.2%, against 76–92% in benchmarks.
   - Report the expected cost of TP suppression. Analytically and empirically small, but reviewers value it.
4. **Org-context ablation.**
   - Generic prompt, then CWE-specific prompt (ZeroFalse-style), then prompt + company sanitizer/framework notes, then prompt + past triage decisions (Semgrep-memory-style).
   - Run all of them on company Z alerts.
5. **Shrunken A/B/C/D, used as a contamination-controlled check rather than the main contribution.**
   - Use about 30–50 Vul4J / Project KB reverted fixes, paired with patched controls, neutralized PR text, and some 2026 post-cutoff CVEs.
   - Run an identity probe ("which CVE is this?").
   - Position it against SEVRA-BENCH, SecPRBench and Sifting the Noise as validating the tooling before deployment.
6. **QLCoder-style validation applied to the PR bot.** Accept an LLM finding or generated CodeQL query only if it fires on the vulnerable revision and stays silent on the patched one. The same criterion appears in AFCRA-Bench and Vul4J ([arXiv 2610.05399](https://arxiv.org/abs/2610.05399)). This can serve as an automatic oracle in the deployment.

### Gaps
- I found no published Vietnamese or Southeast Asian industrial study of SAST or LLM security tooling. A search of venues like SoICT, KSE or APSEC was not done, so this is unverified.
- I found no data on developer trust or acceptance of LLM security comments specifically, as opposed to general review comments.
- No source checked whether Snyk, Semgrep or Datadog offer on-prem or open-weight LLM options, which matters for the privacy comparison. Check vendor docs.
