# Stage 6 targets and readiness testing

Stage 6 adds user-adopted career targets, weighted readiness criteria, explicit career asset and
evidence mappings, and immutable versioned readiness assessments. Readiness is the weighted mean
of criterion coverage. Assessment confidence is displayed separately; it is not a success
probability and does not inflate readiness.

Strategic goals can be assessed directly against existing active career achievements and their
evidence using Gemini. The grounded assessment stores mapped asset and evidence identifiers,
readiness, separate confidence, strengths, gaps and actions. Every reassessment creates a dated
version in the goal's progress trajectory.

AI can suggest up to three trajectories with milestones and criteria when Gemini is configured.
Suggestions remain transient and cannot affect goals or readiness until the user reviews, edits
and explicitly adopts one.

## Manual test

1. Open **Targets** and create a target with at least two positively weighted criteria.
2. Map career assets to each criterion. Evidence belonging to selected assets is mapped with it.
3. Select **Assess existing achievements with AI** on a strategic goal and verify mapped
   achievements, readiness, confidence and a new trajectory version are shown.
4. Enter coverage, confidence, an explanation and recommended action for each criterion.
5. Create an assessment and verify readiness, separate confidence, strengths, gaps and actions.
6. Change a mapping or assessment and assess again. Confirm the version increases.
7. Request AI suggestions. Confirm they remain unadopted until reviewed and saved.
8. Select **Map existing evidence with AI** on an adopted target. Confirm relevant active assets
   and their evidence are mapped to each criterion, a new assessment version is created, and any
   mappings previously entered by the user remain present.

Target, mapping, adoption and assessment actions are audited. Each assessment preserves criterion
weights and mapped asset/evidence identifiers as a historical snapshot.
