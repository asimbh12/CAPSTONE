# Private Vercel review assessment

CAPSTONE is currently local-first: SQLite, uploaded source documents, generated files and the
Gemini credential stay on the Windows computer. A full deployment to Vercel is therefore not a
safe equivalent of the local application.

## Safe review boundary

A future Vercel review should be a **Preview Deployment** protected with **Vercel
Authentication / Standard Protection** and accessible only to the owner's Vercel account. It
must use synthetic demonstration data and must not include:

- `data/`, the SQLite database, backups or uploaded/generated documents;
- `.env` files or the Gemini API key;
- the owner's real career profile or extracted public-profile dataset;
- shareable links or a production alias.

The protected state must be verified from a signed-out browser before any synthetic review URL
is accepted.

## Why deployment is deferred

The current frontend expects a persistent FastAPI API, while the API expects durable SQLite and
local filesystem storage. Vercel runs FastAPI as a Function; cloud persistence, authentication
and storage require a separate architecture phase. The private preview should therefore be
introduced with an explicit demo-data adapter, not by copying the local data directory.

Production deployment remains deferred until PostgreSQL, authenticated user ownership, object
storage, encryption and backup/restore controls are implemented.
