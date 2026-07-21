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

