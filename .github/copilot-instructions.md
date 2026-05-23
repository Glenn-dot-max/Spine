# Spine CRM - AI Agent Instructions

## Architecture Overview

Spine is a full-stack **email automation CRM** for trade show lead management with:

- **Backend**: FastAPI (Python 3.9+) + PostgreSQL + Alembic migrations + APScheduler
- **Frontend**: React 19 + TypeScript + Vite + TailwindCSS + React Router
- **Infrastructure**: Docker Compose (Postgres + Redis)

The core workflow: sales reps connect OAuth (Microsoft/Gmail) → create campaigns (trade shows) → import prospects → send personalized email sequences via Microsoft Graph API → manually track responses (Oven/Fridge/Trash pipeline).

## Critical Ownership Pattern (IDOR Protection)

**ALL resources are owner-scoped** - users can only access their own data. This is enforced at the query level:

```python
# ALWAYS filter by user_id from get_current_user()
campaigns = db.query(Campaign).filter(Campaign.user_id == current_user.id).all()

# Check ownership before updates/deletes
if entity.user_id != current_user.id:
    raise HTTPException(status_code=403, detail="Not authorized")
```

**Exception**: Email templates can be global (`user_id=None`) or user-specific. Global templates are read-only for all users.

See: [backend/app/routes/campaigns.py](../backend/app/routes/campaigns.py#L31), [backend/app/routes/email_templates.py](../backend/app/routes/email_templates.py#L45-L47)

## Authentication Flow

1. **OAuth First-Party**: Microsoft (multi-tenant) or Gmail OAuth via [backend/app/api/oauth.py](../backend/app/api/oauth.py)
2. **Internal JWT**: After OAuth, app issues JWT tokens (access + refresh) via [backend/app/services/auth.py](../backend/app/services/auth.py)
3. **Protected Routes**: All API routes use `Depends(get_current_user)` from [backend/app/api/deps.py](../backend/app/api/deps.py) - validates JWT via HTTPBearer

Frontend stores `access_token` in localStorage, auto-attaches via axios interceptor in [frontend/src/services/api.ts](../frontend/src/services/api.ts).

## Email Sending Architecture

**Critical**: Email is sent via **Microsoft Graph API** (not SMTP). The `EmailService` orchestrator in [backend/app/services/email/email_service.py](../backend/app/services/email/email_service.py):

1. Loads template (priority: campaign-specific → user-global → system default)
2. Renders with `AdvancedTemplateRenderer` (supports `{{prospect.first_name}}`, `{{campaign.name|upper}}`, filters)
3. Routes to `outlook_sender.py` or `gmail_sender.py` based on user's connected provider
4. Updates `CampaignContact.email_sequence_step`, `last_email_sent_at`, and schedules next follow-up

See: [backend/app/services/email/](../backend/app/services/email/)

## Background Scheduler

APScheduler runs in-process (started in FastAPI lifespan). Key job:

```python
# backend/app/scheduler.py - runs every 5 minutes
send_due_followups_task()  # Queries CampaignContact where next_follow_up_scheduled_at <= now
```

**Follow-up delays**: Configurable per-campaign (`followup_delay_1/2/3` in days) with optional per-contact overrides (`custom_followup_delay_1/2/3`).

## Database Patterns

- **Alembic migrations**: Run `alembic upgrade head` in backend/ before starting
- **Models**: All inherit from `Base` (SQLAlchemy 2.0 style) in [backend/app/models/base.py](../backend/app/models/base.py)
- **Enums**: Used extensively (e.g., `ProspectStatus`, `TradeShowStatus`) - always import from models
- **Relationships**: Configured with `back_populates` - see [backend/app/models/campaign.py](../backend/app/models/campaign.py) for cascade patterns

## Template Rendering System

Custom variable syntax in email templates:

```html
Hi {{prospect.first_name}},
<!-- Nested access -->
Company: {{prospect.company_name|default:"your company"}}
<!-- Default filter -->
Event: {{campaign.name|upper}}
<!-- Transform filter -->
```

Available context: `user`, `prospect`, `campaign`, `products` (list). Renderer in [backend/app/services/email/advanced_template_renderer.py](../backend/app/services/email/advanced_template_renderer.py) handles undefined vars safely.

## Development Workflow

**Backend**:

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head  # Run migrations
python -m uvicorn app.main:app --reload  # Port 8000
```

**Frontend**:

```bash
cd frontend
npm install
npm run dev  # Port 5173
```

**Docker** (full stack):

```bash
docker-compose up  # Postgres (5433) + Redis (6379)
```

**Seed default templates** (run once):

```bash
cd backend
python scripts/seed_default_templates.py
```

## Key Files Reference

- **Main App**: [backend/app/main.py](../backend/app/main.py) - FastAPI app with CORS, includes all routers
- **Config**: [backend/app/core/config.py](../backend/app/core/config.py) - Environment vars (OAuth credentials, DATABASE_URL, JWT secrets)
- **Campaign Logic**: [backend/app/routes/campaigns.py](../backend/app/routes/campaigns.py) - 760 lines covering campaign CRUD, contact/product management, email sending
- **Auth Dependency**: [backend/app/api/deps.py](../backend/app/api/deps.py) - JWT validation for all protected routes
- **Frontend API**: [frontend/src/services/api.ts](../frontend/src/services/api.ts) - Axios instance with auth interceptor

## Common Gotchas

- **API calls**: Backend runs on port 8000, frontend on 5173 - CORS is configured for `localhost:5173` only
- **Migrations**: Always create with `alembic revision -m "description"` and review auto-generated code
- **OAuth tokens**: Stored in `User.gmail_access_token` / `outlook_access_token` - must handle refresh (see [backend/app/services/email/outlook_sender.py](../backend/app/services/email/outlook_sender.py#L50-L80))
- **Scheduler**: Runs in same process as API - for production, consider separating to dedicated worker
- **Template IDs**: Campaign can reference specific templates via `template_initial_id`, `template_followup_1_id`, etc. (see [backend/app/models/campaign.py](../backend/app/models/campaign.py#L39-L42))

## Testing

Limited test coverage currently in [backend/tests/](../backend/tests/). When adding tests:

- Use `pytest` for backend
- Create fixtures for authenticated users with `User.id` for ownership checks
- Mock Microsoft Graph API calls in email service tests
