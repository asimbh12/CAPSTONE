import type {
  AssetInput,
  BackupRecord,
  CareerAsset,
  DocumentRecord,
  Evidence,
  Goal,
  ImportReport,
  IngestionProposal,
  IngestionRun,
  ApplyIngestionResult,
  Organisation,
  Profile,
  ProfileInput,
  Theme,
  TimelineItem,
} from '../types/career'

export const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000/api'

interface ErrorEnvelope {
  detail?: string
  error?: { message?: string }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const headers = new Headers(options?.headers)
  if (options?.body && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json')
  }
  const response = await fetch(`${apiBaseUrl}${path}`, { ...options, headers })
  if (!response.ok) {
    let message = `Request failed with status ${response.status}`
    try {
      const payload = (await response.json()) as ErrorEnvelope
      message = payload.detail ?? payload.error?.message ?? message
    } catch {
      // The status remains the safest fallback for non-JSON errors.
    }
    throw new Error(message)
  }
  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}

export const careerApi = {
  getProfile: () => request<Profile | null>('/profile'),
  saveProfile: (payload: ProfileInput) =>
    request<Profile>('/profile', { method: 'PUT', body: JSON.stringify(payload) }),
  listThemes: () => request<Theme[]>('/themes'),
  createTheme: (payload: Pick<Theme, 'name' | 'description'>) =>
    request<Theme>('/themes', { method: 'POST', body: JSON.stringify(payload) }),
  listGoals: () => request<Goal[]>('/goals'),
  createGoal: (payload: Pick<Goal, 'title' | 'description' | 'horizon' | 'target_date'>) =>
    request<Goal>('/goals', { method: 'POST', body: JSON.stringify(payload) }),
  listOrganisations: () => request<Organisation[]>('/organisations'),
  createOrganisation: (
    payload: Pick<Organisation, 'name' | 'organisation_type' | 'website' | 'notes'>,
  ) => request<Organisation>('/organisations', { method: 'POST', body: JSON.stringify(payload) }),
  listAssets: (params: URLSearchParams) =>
    request<{ items: CareerAsset[]; total: number }>(`/assets?${params.toString()}`),
  getAsset: (id: string) => request<CareerAsset>(`/assets/${id}`),
  createAsset: (payload: AssetInput) =>
    request<CareerAsset>('/assets', { method: 'POST', body: JSON.stringify(payload) }),
  updateAsset: (id: string, payload: AssetInput) =>
    request<CareerAsset>(`/assets/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
  archiveAsset: (id: string) => request<CareerAsset>(`/assets/${id}/archive`, { method: 'POST' }),
  createEvidence: (
    assetId: string,
    payload: Pick<Evidence, 'title' | 'description' | 'source_url' | 'document_id'>,
  ) =>
    request<Evidence>(`/assets/${assetId}/evidence`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  uploadDocument: (formData: FormData) =>
    request<DocumentRecord>('/documents', { method: 'POST', body: formData }),
  timeline: () => request<TimelineItem[]>('/timeline'),
  importData: (payload: object, mode: 'dry_run' | 'apply') =>
    request<ImportReport>('/data/import', {
      method: 'POST',
      body: JSON.stringify({ confirmed_public_information: true, mode, payload }),
    }),
  createBackup: () => request<BackupRecord>('/data/backups', { method: 'POST' }),
  ingestDocument: (formData: FormData) =>
    request<IngestionRun>('/ingestions/documents', { method: 'POST', body: formData }),
  ingestUrl: (url: string, aiHandlingPolicy: DocumentRecord['ai_handling_policy']) =>
    request<IngestionRun>('/ingestions/urls', {
      method: 'POST',
      body: JSON.stringify({ url, ai_handling_policy: aiHandlingPolicy, confirmed_public_information: true }),
    }),
  applyIngestion: (id: string, proposal: IngestionProposal) =>
    request<ApplyIngestionResult>(`/ingestions/${id}/apply`, {
      method: 'POST', body: JSON.stringify({ proposal }),
    }),
}

export const downloadUrl = (path: string) => `${apiBaseUrl}${path.replace(/^\/api/, '')}`
