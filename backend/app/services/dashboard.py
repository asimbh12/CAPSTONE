from datetime import UTC, date, datetime, timedelta
from typing import Literal

from sqlmodel import Session, col, select

from app.core.config import get_settings
from app.models.career import (
    ApplicationAssessment,
    ApplicationDraft,
    CareerAsset,
    CareerProfile,
    EvidenceItem,
    IngestionRun,
    JobApplication,
    Opportunity,
    ReadinessAssessment,
    StrategicGoal,
    StrategicGoalAssessment,
    Target,
)
from app.schemas.dashboard import DashboardAction, DashboardMetrics, DashboardRead
from app.services.career import build_asset_read


def _action(
    key: str,
    title: str,
    description: str,
    page: str,
    priority: int,
    count: int,
    urgency: Literal["critical", "high", "medium", "low"],
) -> DashboardAction:
    return DashboardAction(
        key=key,
        title=title,
        description=description,
        page=page,
        priority=priority,
        count=count,
        urgency=urgency,
    )


def build_dashboard(session: Session) -> DashboardRead:
    today = date.today()
    profile = session.exec(select(CareerProfile).limit(1)).first()
    assets = list(
        session.exec(
            select(CareerAsset)
            .where(CareerAsset.status == "active")
            .order_by(col(CareerAsset.updated_at).desc())
        ).all()
    )
    goals = list(
        session.exec(select(StrategicGoal).where(StrategicGoal.status == "active")).all()
    )
    targets = list(session.exec(select(Target).where(Target.status != "archived")).all())
    opportunities = list(
        session.exec(select(Opportunity).where(Opportunity.status != "archived")).all()
    )
    applications = list(session.exec(select(JobApplication)).all())
    evidence_asset_ids = set(session.exec(select(EvidenceItem.asset_id)).all())
    assessed_goal_ids = set(session.exec(select(StrategicGoalAssessment.goal_id)).all())
    assessed_target_ids = set(session.exec(select(ReadinessAssessment.target_id)).all())
    assessed_application_ids = set(session.exec(select(ApplicationAssessment.application_id)).all())
    drafted_application_ids = set(session.exec(select(ApplicationDraft.application_id)).all())

    active_opportunities = [
        item
        for item in opportunities
        if item.status not in {"won", "lost", "withdrawn", "archived"}
    ]
    closing_soon = [
        item
        for item in active_opportunities
        if item.closing_date is not None
        and today <= item.closing_date <= today + timedelta(days=14)
    ]
    actions: list[DashboardAction] = []

    if profile is None or not profile.name.strip():
        actions.append(
            _action(
                "complete-profile",
                "Complete the career profile",
                "Add the user-authoritative career narrative and mission before relying on AI.",
                "profile",
                100,
                1,
                "critical",
            )
        )
    if not assets:
        actions.append(
            _action(
                "import-career",
                "Import the first career evidence",
                "Upload a CV or public profile to establish reusable career assets.",
                "onboarding",
                95,
                1,
                "critical",
            )
        )
    missing_experience_impact = [
        item
        for item in assets
        if "experience" in item.category.casefold() and not item.impact_summary.strip()
    ]
    if missing_experience_impact:
        actions.append(
            _action(
                "review-impact-summaries",
                "Strengthen experience impact summaries",
                "Use the guided AI review queue and explicitly save the best grounded summary.",
                "assets",
                82,
                len(missing_experience_impact),
                "high",
            )
        )
    assets_without_evidence = [item for item in assets if item.id not in evidence_asset_ids]
    if assets_without_evidence:
        actions.append(
            _action(
                "add-evidence",
                "Add evidence to unsupported assets",
                "Link public sources or local documents so future claims remain traceable.",
                "assets",
                72,
                len(assets_without_evidence),
                "medium",
            )
        )
    unassessed_goals = [goal for goal in goals if goal.id not in assessed_goal_ids]
    if unassessed_goals:
        actions.append(
            _action(
                "assess-goals",
                "Assess strategic-goal readiness",
                "Map existing achievements to active goals and establish a progress baseline.",
                "targets",
                86,
                len(unassessed_goals),
                "high",
            )
        )
    unassessed_targets = [target for target in targets if target.id not in assessed_target_ids]
    if unassessed_targets:
        actions.append(
            _action(
                "assess-targets",
                "Complete target readiness assessments",
                "Review criteria mappings and save a versioned readiness assessment.",
                "targets",
                78,
                len(unassessed_targets),
                "high",
            )
        )
    if closing_soon:
        actions.append(
            _action(
                "closing-opportunities",
                "Review opportunities closing soon",
                "Confirm the next action for deadlines within the next 14 days.",
                "opportunities",
                98,
                len(closing_soon),
                "critical",
            )
        )
    opportunities_without_action = [
        item for item in active_opportunities if not item.next_action.strip()
    ]
    if opportunities_without_action:
        actions.append(
            _action(
                "opportunity-actions",
                "Define opportunity next actions",
                "Turn prioritised opportunities into concrete, trackable actions.",
                "opportunities",
                68,
                len(opportunities_without_action),
                "medium",
            )
        )
    incomplete_applications = [
        item for item in applications if not item.requirements_confirmed
    ]
    if incomplete_applications:
        actions.append(
            _action(
                "confirm-job-requirements",
                "Review extracted job requirements",
                "Correct and confirm position requirements before evidence mapping.",
                "applications",
                88,
                len(incomplete_applications),
                "high",
            )
        )
    unmapped_applications = [
        item
        for item in applications
        if item.requirements_confirmed and item.id not in assessed_application_ids
    ]
    if unmapped_applications:
        actions.append(
            _action(
                "map-job-evidence",
                "Map evidence to active applications",
                "Assess fit and reveal evidence gaps before drafting application materials.",
                "applications",
                84,
                len(unmapped_applications),
                "high",
            )
        )
    undrafted_applications = [
        item
        for item in applications
        if item.id in assessed_application_ids and item.id not in drafted_application_ids
    ]
    if undrafted_applications:
        actions.append(
            _action(
                "generate-application-drafts",
                "Generate reviewed application drafts",
                "Create grounded application materials from the completed evidence assessment.",
                "applications",
                76,
                len(undrafted_applications),
                "medium",
            )
        )
    failed_imports = list(
        session.exec(select(IngestionRun).where(IngestionRun.status == "failed")).all()
    )
    if failed_imports:
        actions.append(
            _action(
                "recover-imports",
                "Review failed career imports",
                "Inspect diagnostic details, correct the source and reprocess safely.",
                "onboarding",
                74,
                len(failed_imports),
                "medium",
            )
        )

    backup_dir = get_settings().data_root / "backups"
    backup_files = list(backup_dir.glob("capstone-backup-*.zip")) if backup_dir.exists() else []
    latest_backup = max((item.stat().st_mtime for item in backup_files), default=0)
    backup_age = (
        datetime.now(UTC) - datetime.fromtimestamp(latest_backup, tz=UTC)
        if latest_backup
        else None
    )
    if backup_age is None or backup_age > timedelta(days=7):
        actions.append(
            _action(
                "create-backup",
                "Create a current local backup",
                "Protect the SQLite database and local documents with a checksum manifest.",
                "data",
                80 if backup_age is None else 64,
                1,
                "high" if backup_age is None else "medium",
            )
        )

    actions.sort(key=lambda item: (-item.priority, item.key))
    return DashboardRead(
        profile_name=profile.name if profile else "",
        metrics=DashboardMetrics(
            active_assets=len(assets),
            asset_categories=len({item.category for item in assets}),
            strategic_goals=len(goals),
            timeline_events=len(assets),
            open_opportunities=len(active_opportunities),
            closing_soon=len(closing_soon),
        ),
        actions=actions[:8],
        recent_assets=[build_asset_read(session, item) for item in assets[:4]],
    )
