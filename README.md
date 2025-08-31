# CAS Document Management System

Ein hochmodernes, skalierbares Dokumentenmanagement-System mit automatischer Dateisortierung, OCR und intelligenter Indexierung.

## 🏗️ Architektur

Das System basiert auf einer Microservices-Architektur mit folgenden Kernkomponenten:

- **Ingest Service**: Automatische Dateisortierung und Metadatenextraktion
- **Indexing Service**: Volltext-Indexierung mit Elasticsearch
- **DMS (Paperless-ngx)**: Dokumentenmanagement mit OCR
- **Admin Dashboard**: React-basierte Verwaltungsoberfläche
- **Message Queue**: RabbitMQ für Service-Kommunikation
- **Object Storage**: MinIO für skalierbare Dateispeicherung

## 🚀 Quick Start

### Voraussetzungen

- Docker & Docker Compose
- Node.js 18+ (für Admin Dashboard)
- Python 3.11+ (für Ingest Service)

### Lokale Entwicklung

```bash
# Repository klonen
git clone <repository-url>
cd cas_stm

# Services starten
docker-compose up -d

# Admin Dashboard starten
cd admin-dashboard
npm install
npm run dev

# Ingest Service starten
cd ingest-service
pip install -r requirements.txt
python main.py
```

### Produktions-Deployment

```bash
# Kubernetes Deployment
kubectl apply -f k8s/

# Helm Chart (optional)
helm install cas-dms ./helm-charts/cas-dms
```

## 📁 Projektstruktur

```
cas_stm/
├── ingest-service/          # Python-basierter Ingest Service
├── admin-dashboard/         # React Admin Dashboard
├── indexing-service/        # Diskover + Elasticsearch
├── dms/                     # Paperless-ngx Konfiguration
├── k8s/                     # Kubernetes Manifests
├── helm-charts/            # Helm Charts für Production
├── docker-compose.yml      # Lokale Entwicklung
└── docs/                   # Dokumentation
```

## 🔧 Konfiguration

### Ingest Service Konfiguration

```yaml
# config/sorting-rules.yaml
rules:
  - name: "Rechnungen"
    keywords: ["rechnung", "invoice", "bill"]
    target_path: "documents/invoices/{year}/{month}"
    
  - name: "Verträge"
    keywords: ["vertrag", "contract", "agreement"]
    target_path: "documents/contracts/{client}"
```

### Umgebungsvariablen

```bash
# .env
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
POSTGRES_URL=postgresql://user:pass@localhost:5432/cas_dms
ELASTICSEARCH_URL=http://localhost:9200
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
```

## 📊 Monitoring

- **Grafana**: http://localhost:3000
- **Kibana**: http://localhost:5601
- **Admin Dashboard**: http://localhost:3001
- **Paperless-ngx**: http://localhost:8010

## 🧪 Tests

```bash
# Unit Tests
cd ingest-service && python -m pytest

# Integration Tests
docker-compose -f docker-compose.test.yml up --abort-on-container-exit

# E2E Tests
cd admin-dashboard && npm run test:e2e
```

## 📈 Skalierung

Das System ist horizontal skalierbar:

- **Ingest Service**: Kann bei hoher Dateianzahl skaliert werden
- **Elasticsearch**: Cluster-Modus für große Datenmengen
- **MinIO**: Distributed Mode für hohe Verfügbarkeit

## 🔒 Sicherheit

- TLS/SSL für alle Services
- JWT-basierte Authentifizierung
- RBAC (Role-Based Access Control)
- Audit-Logging für alle Operationen

## 📘 Zusätzliche Dokumentation & Quicklinks

- Admin Guide: `docs/README-ADMIN.md`
- Gateway Services: `config/gateway-services.yml`
- RBAC: `config/gateway-rbac.yml`
- Ingest Config (multi-NAS): `config/ingest-config.yaml` (API: /api/ingest/config/ingest)
- Email Config (multi-accounts): `config/email-config.yaml` (API: /api/email/config/email)
- Health (Gateway): `/health/all`

## 🤝 Beitragen

1. Fork das Repository
2. Erstelle einen Feature Branch
3. Committe deine Änderungen
4. Push zum Branch
5. Erstelle einen Pull Request

## 📄 Lizenz

MIT License - siehe [LICENSE](LICENSE) für Details.