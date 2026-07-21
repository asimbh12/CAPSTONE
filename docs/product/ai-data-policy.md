# AI and Data Handling Policy

## Scope

The MVP accepts only information that is already publicly available at an official professional level. It is not intended to store sensitive personal information or confidential material.

## Prohibited information

Users must not add:

- Health, medical, biometric, or disability information.
- Classified, export-controlled, security-cleared, or operational defence information.
- Confidential employer, client, grant-review, or commercially sensitive information.
- Government identifiers, financial account information, passwords, or API keys.
- Private referee reports or non-public personal details about contacts.
- Information the user lacks the right to store or process.

The interface must warn users at manual-entry, upload, paste, and import boundaries. Automated detection may warn about likely sensitive content but cannot guarantee detection; the user remains responsible for confirming eligibility.

## Document handling classes

### `ai_allowed`

Selected, minimised content may be sent to the configured external AI provider for the requested operation.

### `local_only`

Content remains local and must never be placed in an external AI request. Local deterministic extraction may be used. Features requiring external inference must explain that they are unavailable for this content.

### `redacted`

Only a reviewed redacted derivative may be sent externally. The unchanged original remains local. Until the redacted derivative exists and is approved, the effective policy is `local_only`.

The default for a newly uploaded document is `local_only`; the user must explicitly choose or confirm `ai_allowed` when external processing is needed.

## AI authority boundaries

AI may automatically create or maintain:

- Derived tags, themes, summaries, match suggestions, confidence estimates, and next-action recommendations.
- Draft target requirements and trajectories.
- Draft job requirements and application text.

AI may not overwrite:

- User-entered career facts.
- Original source files or extracted source snapshots.
- User-adopted goals, targets, requirements, or trajectory decisions.
- User corrections or explicit suppressions.

AI output is untrusted structured input. It must pass schema validation, length limits, identifier checks, and application-level authorisation rules before storage or display.

## External request rules

Before an AI request, the server must:

1. Identify the exact operation and required fields.
2. Exclude records not needed for that operation.
3. Enforce each source's AI handling policy.
4. Apply configured redaction where required.
5. Avoid secrets, local absolute paths, and unrelated contact details.
6. Record input record identifiers and hashes, not unrestricted content, in the audit trail.

The UI must disclose that eligible content leaves the computer when Gemini is used and provide a final operation-level summary of the information categories being sent.

## Grounded generation

- Generated factual claims must reference one or more eligible evidence identifiers internally.
- Unsupported suggestions must be labelled as suggestions or confirmation-required placeholders.
- The generation pipeline must not infer dates, metrics, titles, credentials, responsibilities, or outcomes without evidence.
- Job requirements extracted by AI require user confirmation before final scoring or generation.
- Generated documents remain drafts until reviewed by the user.

## Provider portability

Application services depend on a provider-neutral AI interface, not the Gemini SDK directly. Operations use versioned structured contracts such as:

- `enrich_asset`
- `suggest_trajectory`
- `extract_job_requirements`
- `map_evidence`
- `analyse_job_fit`
- `generate_application_document`

Provider-specific model names, credentials, rate limits, safety settings, and request translation belong in the provider adapter. Switching to OpenAI later must not require changes to domain entities or workflow rules.

## Logging and retention

- Never log API keys or authorisation headers.
- Avoid logging raw prompts, document bodies, or complete AI responses in routine application logs.
- Store the minimum metadata needed for reproducibility and troubleshooting.
- Derived results retain provider, model, operation contract version, timestamp, status, and source record references.
- Users can delete derived AI outputs without deleting authoritative source material.

