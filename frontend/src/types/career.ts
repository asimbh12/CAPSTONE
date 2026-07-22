export interface Profile {
  id: string
  name: string
  current_title: string
  current_organisation: string
  career_mission: string
  career_narrative: string
  created_at: string
  updated_at: string
}

export type ProfileInput = Omit<Profile, 'id' | 'created_at' | 'updated_at'>

export interface Theme {
  id: string
  name: string
  description: string
  provenance: string
  created_at: string
}

export interface Goal {
  id: string
  title: string
  description: string
  horizon: 'short_term' | 'medium_term' | 'long_term'
  target_date: string | null
  status: string
  provenance: string
  created_at: string
  updated_at: string
}

export interface Organisation {
  id: string
  name: string
  organisation_type: string
  website: string
  notes: string
  provenance: string
  created_at: string
}

export interface DocumentRecord {
  id: string
  original_filename: string
  mime_type: string
  byte_size: number
  sha256: string
  ai_handling_policy: 'ai_allowed' | 'local_only' | 'redacted'
  extraction_status: string
  extraction_error: string
  created_at: string
}

export interface Evidence {
  id: string
  asset_id: string
  title: string
  description: string
  source_url: string
  document_id: string | null
  source_kind: string
  created_at: string
  document: DocumentRecord | null
}

export interface CareerAsset {
  id: string
  title: string
  description: string
  category: string
  subcategory: string
  start_date: string | null
  end_date: string | null
  date_precision: string
  status: 'draft' | 'active' | 'archived'
  impact_summary: string
  organisation_id: string | null
  role: string
  visibility: 'public' | 'professional'
  tags: string[]
  keywords: string[]
  theme_ids: string[]
  source_kind: string
  created_at: string
  updated_at: string
  archived_at: string | null
  themes: Theme[]
  evidence: Evidence[]
  organisation: Organisation | null
}

export type AssetInput = Omit<
  CareerAsset,
  | 'id'
  | 'source_kind'
  | 'created_at'
  | 'updated_at'
  | 'archived_at'
  | 'themes'
  | 'evidence'
  | 'organisation'
>

export interface TimelineItem {
  id: string
  title: string
  category: string
  start_date: string | null
  end_date: string | null
  role: string
  organisation: string | null
}

export interface TimelineDuplicateCandidate extends TimelineItem {
  description: string
  source_kind: string
  evidence_count: number
}

export interface TimelineDuplicateGroup {
  confidence: number
  reasons: string[]
  items: TimelineDuplicateCandidate[]
}

export interface TimelineDuplicateResolutionResult {
  kept_id: string
  archived_ids: string[]
}

export interface ImportReport {
  mode: string
  schema_version: string
  valid: boolean
  counts: Record<string, number>
  errors: string[]
  warnings: string[]
  duplicate_titles: string[]
  applied: boolean
}

export interface BackupRecord {
  filename: string
  byte_size: number
  created_at: string
  download_url: string
}

export interface ProposedAsset {
  title: string
  description: string
  category: string
  role: string
  organisation: string
  start_date: string | null
  end_date: string | null
  impact_summary: string
  tags: string[]
  themes: string[]
  include: boolean
  source_labels: string[]
  source_urls: string[]
}

export interface IngestionProposal {
  profile: Pick<ProfileInput, 'name' | 'current_title' | 'current_organisation' | 'career_narrative'> & { field_sources: Record<string, string[]> }
  assets: ProposedAsset[]
  themes: string[]
  warnings: string[]
  conflicts: string[]
  coverage: Record<string, number>
  source_diagnostics: Record<string, string | number | boolean>
}

export interface PublicProfileSource {
  url: string
  source_type: string
}

export interface IngestionRun {
  id: string
  source_type: string
  source_label: string
  source_url: string
  source_manifest: PublicProfileSource[]
  document_id: string | null
  ai_handling_policy: DocumentRecord['ai_handling_policy']
  provider: string
  status: string
  proposal: IngestionProposal
  error_message: string
  created_at: string
  applied_at: string | null
}

export interface ApplyIngestionResult {
  profile_created: boolean
  profile_fields_filled: string[]
  assets_created: number
  assets_skipped: number
  organisations_created: number
  themes_created: number
}

export interface AiProviderStatus {
  configured_provider: string
  active_provider: string
  model: string
  gemini_key_configured: boolean
}

export interface AssetEnrichmentResult {
  asset_id: string
  provider: string
  tags_added: string[]
  themes_added: string[]
  summary: string
  association_suggestions: string[]
}

export interface OpportunityAssessment {
  id: string; algorithm_version: string; strategic_value: number; probability: number; effort: number
  raw_score: number; normalized_score: number; input_source: 'user' | 'ai'; explanation: string; created_at: string
}
export interface OpportunityUrgency { level: string; days_remaining: number | null; label: string }
export interface Opportunity {
  id: string; title: string; description: string; opportunity_type: string; organisation_id: string | null
  organisation_name: string | null; url: string; opening_date: string | null; closing_date: string | null
  status: string; owner: string; next_action: string; notes: string; source: string
  created_at: string; updated_at: string; archived_at: string | null
  assessment: OpportunityAssessment; urgency: OpportunityUrgency
}
export interface OpportunityInput {
  title: string; description: string; opportunity_type: string; organisation_id: string | null; url: string
  opening_date: string | null; closing_date: string | null; status: string; owner: string; next_action: string
  notes: string; source: string; strategic_value: number; probability: number; effort: number; score_input_source: 'user' | 'ai'
}
export interface OpportunitySummary { active: number; pursuing: number; closing_soon: number; top_opportunity: Opportunity | null }

export interface TargetCriterion {
  id: string; title: string; description: string; weight: number; sort_order: number; provenance: string
  asset_ids: string[]; evidence_ids: string[]
}
export interface CriterionInput { title: string; description: string; weight: number; sort_order: number; provenance: 'user' | 'ai' }
export interface CriterionAssessmentInput { criterion_id: string; coverage: number; confidence: number; explanation: string; recommended_action: string }
export interface CriterionAssessment extends CriterionAssessmentInput {
  criterion_title: string; weight: number; normalized_weight: number; asset_ids: string[]; evidence_ids: string[]
}
export interface ReadinessAssessment {
  id: string; version: number; algorithm_version: string; readiness_score: number; overall_confidence: number
  strengths: string[]; gaps: string[]; recommendations: string[]; criteria: CriterionAssessment[]; created_at: string
}
export interface Target {
  id: string; title: string; description: string; target_type: string; status: string; target_date: string | null
  provenance: string; criteria: TargetCriterion[]; latest_assessment: ReadinessAssessment | null
  created_at: string; updated_at: string
}
export interface TargetInput {
  title: string; description: string; target_type: string; status: string; target_date: string | null
  provenance: 'user' | 'ai'; criteria: CriterionInput[]
}
export interface TargetSuggestion {
  title: string; description: string; target_type: string; rationale: string; milestones: string[]; criteria: CriterionInput[]
}
export interface TargetSuggestionResponse { provider: string; suggestions: TargetSuggestion[] }
