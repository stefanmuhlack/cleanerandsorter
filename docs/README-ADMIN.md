CAS Platform - Administrator Guide

This guide documents the current architecture, deployed services, configuration, and operational workflows. It is focused on Day 1 (setup) and Day 2 (operate) tasks for admins.

Architecture Overview

Microservices behind an API Gateway:
- API Gateway (FastAPI): auth, RBAC, routing, metrics.
- Ingest Service (FastAPI): crawler, duplicates, snapshots, classification review, config API.
- LLM Manager (FastAPI): classification endpoint.
- Footage Service (FastAPI): media mgmt (upload, list, pagination, search, thumbnails).
- Email Processor (FastAPI): multiple accounts, filters, processing tasks.
- Storage Manager (FastAPI): heterogeneous storage autodetection; health and listing stub.
- Backup, OTRS Integration, Paperless-ngx, Elasticsearch/Kibana, Prometheus/Grafana.

Admin Dashboard (React/Material-UI) provides:
- Dashboard with live health and ingest stats.
- Monitoring: service health with per-service details (from /health), system metrics from Prometheus (placeholder), alerts.
- Footage Management: uploads, batch ops, import from share.
- Control Panel: ingest config editor, email config editor (YAML), crawler controls, reports.
- Review: classification review queue with confirm/download.

URLs (default, via docker-compose)
- Admin Dashboard: http://localhost:3001
- API Gateway: http://localhost:8000
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)
- MinIO Console: http://localhost:9001 (minioadmin/minioadmin)
- Paperless: http://localhost:8010

Authentication
- Temporary: POST /auth/login with username=admin, password=admin123 → returns JWT for protected routes.
- Dashboard stores the token in localStorage and attaches it to API calls.

RBAC
- Roles defined in config/gateway-rbac.yml.
- Gateway enforces RBAC for /api/{service}/… and generic routes.
- Degraded health responses are shown as “warning”.

Health and Monitoring
- Gateway aggregates /health/all with per-service status, response_time, error.
- Monitoring page: click on a service card → shows raw JSON of /api/{service}/health.
- Prometheus scrapes gateway, ingest, llm, storage, footage; Grafana dashboards provisioned under config/grafana/provisioning.

Configuration Management

Ingest Configuration (multi-NAS)
- File: config/ingest-config.yaml
- API: GET/PUT /api/ingest/config/ingest
- Validation enforces shares list (multiple paths) and central_base.
- In Dashboard → Control Panel → “Ingest YAML bearbeiten” to edit.
- Confidence threshold: PUT /api/ingest/config/ingest/confidence-threshold or use the numeric field in editor.

Example:
central_base: "/data/sorted"
shares:
  - "/data/source"
  - "/mnt/share/customers"
  - "/mnt/share/internal"
internal_roots:
  - "ORGA"
  - "INFRA"
  - "SALES"
  - "HR"
sorting:
  enable_year_subfolders: true

Email Configuration (multi-account)
- File: config/email-config.yaml
- API: GET /api/email/config/email, PUT /api/email/config/email
- Dashboard → Control Panel → “Email Config bearbeiten” opens YAML editor.
- Email Processor reloads accounts on save; supports multiple accounts and filters.

Crawler Operations
- Control Panel → Crawler tab.
- Start/Stop: /api/ingest/crawler/start|stop.
- Status polled every 15s; shows stats (processed, moved, duplicates, errors) and per-customer breakdown.

Footage Operations
- Upload single or batch with progress.
- Server-side list pagination/sorting/filtering; thumbnails fetched per item.
- Import from Share dialog uses Storage Manager for detect/test/list.

Classification Review
- LLM Manager returns category + confidence.
- Ingest applies threshold: auto-move or queue for review.
- Review UI lists pending, allows confirm/override and file download.

Backup
- Backup service exposes endpoints for listing/creating/restoring backups. Configure under config/backup-config.yaml.

Troubleshooting
- Dashboard service tiles show error/warning; click to view raw service health JSON.
- Use Gateway /health/all to cross-check; cache TTL from config/gateway-services.yml.
- Logs: docker-compose logs -f <service>.
- Ensure MinIO/Postgres/RabbitMQ healthy for Ingest critical checks.

Deploy/Run
- Build and start: docker-compose up -d --build
- Admin Dashboard rebuild only: docker-compose up -d --build admin-dashboard
- Storage Manager is currently a minimal stub; replace with adapter implementations as needed.

Security Notes
- Replace default JWT secret in config/gateway-services.yml.
- Do not store production secrets in YAML; use environment variables and secrets managers.

Roadmap
- Wire Monitoring charts to Prometheus queries.
- Expand Storage Manager adapters (SMB/WebDAV/SharePoint) and listing/download.
- Add E2E tests for classification threshold and RBAC.
