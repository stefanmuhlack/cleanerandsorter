# CAS Document Management System - Deployment Guide

## Übersicht

Das CAS Document Management System ist eine hochmoderne, skalierbare Lösung für die automatische Sortierung, Indexierung und Verwaltung von Dokumenten. Diese Anleitung beschreibt die vollständige Installation und Konfiguration des Systems.

## Systemarchitektur

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Admin Panel   │    │  Ingest Service │    │  Paperless-ngx  │
│   (React)       │    │   (FastAPI)     │    │   (DMS)         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │     MinIO       │    │  Elasticsearch  │
│   (Database)    │    │ (Object Store)  │    │   (Search)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │    RabbitMQ     │
                    │ (Message Queue) │
                    └─────────────────┘
```

## Voraussetzungen

### Hardware-Anforderungen

**Minimale Konfiguration:**
- CPU: 4 Cores
- RAM: 8 GB
- Storage: 100 GB SSD
- Netzwerk: 1 Gbps

**Empfohlene Konfiguration:**
- CPU: 8+ Cores
- RAM: 16+ GB
- Storage: 500+ GB SSD
- Netzwerk: 10 Gbps

### Software-Anforderungen

- Docker 20.10+
- Docker Compose 2.0+
- Kubernetes 1.24+ (für Production)
- Git

## Lokale Entwicklung

### 1. Repository klonen

```bash
git clone <repository-url>
cd cas_stm
```

### 2. Umgebungsvariablen konfigurieren

```bash
# .env Datei erstellen
cp .env.example .env

# Werte anpassen
nano .env
```

### 3. Services starten

```bash
# Alle Services starten
docker-compose up -d

# Status prüfen
docker-compose ps

# Logs anzeigen
docker-compose logs -f
```

### 4. Services verifizieren

| Service | URL | Beschreibung |
|---------|-----|--------------|
| Admin Dashboard | http://localhost:3001 | React Admin Panel |
| Ingest Service | http://localhost:8000 | FastAPI Backend |
| Paperless-ngx | http://localhost:8010 | Dokumentenmanagement |
| MinIO Console | http://localhost:9001 | Object Storage |
| Kibana | http://localhost:5601 | Elasticsearch UI |
| Grafana | http://localhost:3000 | Monitoring |
| RabbitMQ | http://localhost:15672 | Message Queue |

### 5. Admin Dashboard starten

```bash
cd admin-dashboard
npm install
npm start
```

## Production Deployment

### Kubernetes Deployment

#### 1. Namespace erstellen

```bash
kubectl apply -f k8s/namespace.yaml
```

#### 2. Secrets konfigurieren

```bash
# Secrets anpassen
nano k8s/secrets.yaml

# Secrets anwenden
kubectl apply -f k8s/secrets.yaml
```

#### 3. ConfigMap anwenden

```bash
kubectl apply -f k8s/configmap.yaml
```

#### 4. Services deployen

```bash
# PostgreSQL
kubectl apply -f k8s/postgres-statefulset.yaml

# Ingest Service
kubectl apply -f k8s/ingest-service-deployment.yaml

# Weitere Services...
```

#### 5. Ingress konfigurieren

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: cas-dms-ingress
  namespace: cas-dms
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: cas-dms.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: cas-admin-dashboard
            port:
              number: 3000
```

### Helm Chart Deployment

#### 1. Helm Chart installieren

```bash
# Repository hinzufügen
helm repo add cas-dms https://charts.example.com/cas-dms

# Chart installieren
helm install cas-dms cas-dms/cas-dms \
  --namespace cas-dms \
  --create-namespace \
  --values values.yaml
```

#### 2. Values anpassen

```yaml
# values.yaml
ingestService:
  replicas: 3
  resources:
    requests:
      memory: "1Gi"
      cpu: "500m"
    limits:
      memory: "2Gi"
      cpu: "1000m"

storage:
  minio:
    persistence:
      size: 500Gi
  postgres:
    persistence:
      size: 100Gi
```

## Konfiguration

### Sortierregeln

Die Sortierregeln werden in `config/sorting-rules.yaml` definiert:

```yaml
rules:
  - name: "Rechnungen"
    keywords: ["rechnung", "invoice", "bill"]
    target_path: "documents/invoices/{year}/{month}"
    priority: 10
    enabled: true
    file_types: ["pdf", "document", "spreadsheet"]
```

### Umgebungsvariablen

| Variable | Beschreibung | Standard |
|----------|--------------|----------|
| `MINIO_ENDPOINT` | MinIO Server URL | `localhost:9000` |
| `MINIO_ACCESS_KEY` | MinIO Access Key | `minioadmin` |
| `MINIO_SECRET_KEY` | MinIO Secret Key | `minioadmin` |
| `POSTGRES_URL` | PostgreSQL Connection String | `postgresql://user:pass@localhost:5432/cas_dms` |
| `RABBITMQ_URL` | RabbitMQ Connection String | `amqp://guest:guest@localhost:5672/` |
| `ELASTICSEARCH_URL` | Elasticsearch URL | `http://localhost:9200` |

## Monitoring & Logging

### Prometheus Metrics

Das System exportiert Prometheus-Metriken unter `/metrics`:

- `http_requests_total`: HTTP Request Counter
- `http_request_duration_seconds`: Request Latency
- `file_processing_total`: File Processing Counter
- `file_processing_duration_seconds`: Processing Time

### Grafana Dashboards

Vordefinierte Dashboards für:
- System Performance
- File Processing Statistics
- Error Rates
- Storage Usage

### Logging

Strukturiertes Logging mit JSON-Format:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "service": "ingest-service",
  "message": "File processed successfully",
  "file_id": "123e4567-e89b-12d3-a456-426614174000",
  "processing_time": 1.234
}
```

## Skalierung

### Horizontale Skalierung

```bash
# Ingest Service skalieren
kubectl scale deployment cas-ingest-service --replicas=5

# Elasticsearch Cluster erweitern
kubectl scale statefulset cas-elasticsearch --replicas=3
```

### Vertikale Skalierung

```yaml
resources:
  requests:
    memory: "2Gi"
    cpu: "1000m"
  limits:
    memory: "4Gi"
    cpu: "2000m"
```

## Backup & Recovery

### Datenbank Backup

```bash
# PostgreSQL Backup
pg_dump -h localhost -U cas_user -d cas_dms > backup.sql

# Automatisiertes Backup
kubectl create -f k8s/backup-cronjob.yaml
```

### Object Storage Backup

```bash
# MinIO Backup
mc mirror minio/documents backup-bucket/

# S3 kompatibles Backup
aws s3 sync s3://cas-documents s3://backup-bucket/
```

## Sicherheit

### TLS/SSL Konfiguration

```yaml
# Ingress mit TLS
spec:
  tls:
  - hosts:
    - cas-dms.example.com
    secretName: cas-dms-tls
```

### Authentifizierung

- JWT-basierte Authentifizierung
- OAuth2 Integration möglich
- LDAP/Active Directory Support

### Netzwerk-Sicherheit

- Service Mesh (Istio) Integration
- Network Policies
- Pod Security Policies

## Troubleshooting

### Häufige Probleme

#### 1. Services starten nicht

```bash
# Logs prüfen
docker-compose logs <service-name>

# Health Checks
curl http://localhost:8000/health
```

#### 2. Datenbankverbindung fehlschlägt

```bash
# PostgreSQL Status
docker-compose exec postgres pg_isready -U cas_user -d cas_dms

# Connection Test
docker-compose exec ingest-service python -c "
import asyncpg
import asyncio
async def test():
    conn = await asyncpg.connect('postgresql://cas_user:cas_password@postgres:5432/cas_dms')
    await conn.close()
asyncio.run(test())
"
```

#### 3. MinIO Verbindungsprobleme

```bash
# MinIO Status
docker-compose exec minio mc admin info local

# Bucket erstellen
docker-compose exec minio mc mb local/documents
```

### Debug-Modus

```bash
# Debug-Logging aktivieren
export LOG_LEVEL=DEBUG
docker-compose up
```

## Support

### Dokumentation

- [API Dokumentation](http://localhost:8000/docs)
- [Admin Dashboard Guide](docs/admin-dashboard.md)
- [Developer Guide](docs/developer.md)

### Community

- GitHub Issues: [Repository Issues](https://github.com/example/cas-dms/issues)
- Discord: [Community Server](https://discord.gg/cas-dms)
- Email: support@cas-dms.com

### Enterprise Support

Für Enterprise-Kunden steht professioneller Support zur Verfügung:
- 24/7 Support
- SLA Garantien
- Custom Development
- On-Site Installation

## Lizenz

Dieses Projekt steht unter der MIT Lizenz. Siehe [LICENSE](LICENSE) für Details. 