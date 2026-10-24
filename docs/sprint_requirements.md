# Sprint judging criteria and submission requirements (from the sprint page, read 2026-10-24)

Source: https://apartresearch.com/sprints/ai-collusion-research-sprint-2026-10-23-to-2026-10-25#guidelines

## Rubric (each scored 1–5)
1. **Impact potential & innovation.** How much would this matter if it worked, and how new is
   it? 4–5 need real novelty, not replication: an original approach or a neglected problem; "a
   valuable contribution others could build on"; 5 = opens a direction, clear theory of change.
2. **Execution quality.** 3 = technically solid for the duration, interpretable results,
   limitations acknowledged. 4 = thorough methodology with convincing validation; results
   clearly support conclusions. 5 = ambitious scope done rigorously, unusually robust validation.
3. **Presentation & clarity.** 3 = problem, method, findings and limitations are clearly
   present. 4 = easy to follow, well structured. 5 = a pleasure to read; could serve as a model.

## Required
- Research report PDF using the official template:
  https://docs.google.com/document/d/1Y5wd3VRbXU5N08BvAGiJUQTaWbMCSPjhzXsR-ozuehg/copy?usp=sharing
- At most 8 pages, excluding references and appendices (most strong projects: 4–8).
- Title and an abstract of 150–250 words. Author names and affiliations.
- Appendix "Limitations and Dual-Use / Ethical Considerations": what the result does and does
  not establish, and any way the setup or findings could make real-world collusion easier to
  carry out or harder to detect.
- Optional: public GitHub repo, 3–5 min video, slides.

## Recommended structure
Introduction; Related Work; Methodology (enough to replicate: models, prompts, environments,
seeds, metrics); Results (quantitative; report variance, seeds and baselines, and **always
include the positive control**); Discussion; Limitations/Ethics appendix; References.

## Rules that affect us
- **Prior work must be disclosed**: "clearly identify what is new work done during the
  sprint… Mark any code you wrote before the sprint as preexisting in the README and the
  report." Undisclosed prior work can lead to disqualification. (See PRE_SPRINT_LOG.md.)
- Made-up results or references can disqualify a project.
- Deadline: **Sunday Oct 25, 11:59 PM AoE**. Submitted through the form on the sprint page;
  pick Track 2 (Detection and Audit of Collusion).

## Track 2, question 2.2 (sprint page)
"Does combining what agents say with what they do improve detection?" Starter code:
llm-trust-breaking (Shi et al.) and TraceGuard (its action-trace consistency rubric is
reusable). Weekend project: a small balanced set from one game; the same monitor gets four views
(messages only; actions only; raw messages plus actions; a structured report comparing claims
with outcomes). **Freeze the monitor model, prompt and threshold before evaluation**, and
report both accuracy and false-positive rate. Budget guide: $5–30.
