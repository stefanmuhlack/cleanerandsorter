#!/bin/bash

# Business Cases Master Script
# Führt alle Sprints A-F sequenziell aus für vollständige Enterprise-Plattform

set -e

echo "🚀 BUSINESS CASES MASTER SCRIPT"
echo "==============================="
echo "Weltklasse Enterprise-Plattform - Vollständige Implementierung"
echo ""

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging-Funktion
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

highlight() {
    echo -e "${PURPLE}🌟 $1${NC}"
}

# Pre-flight Checks
log "Pre-flight Checks..."
if ! command -v docker &> /dev/null; then
    error "Docker ist nicht installiert"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    error "Docker Compose ist nicht installiert"
    exit 1
fi

if ! command -v curl &> /dev/null; then
    error "curl ist nicht installiert"
    exit 1
fi

if ! command -v jq &> /dev/null; then
    warning "jq ist nicht installiert - JSON-Parsing wird eingeschränkt sein"
fi

success "Pre-flight Checks bestanden"

# Variablen
START_TIME=$(date +%s)
TOTAL_SPRINTS=6
CURRENT_SPRINT=0
SUCCESSFUL_SPRINTS=0
FAILED_SPRINTS=0

# Sprint-Funktionen
run_sprint_a() {
    highlight "SPRINT A: Import-Pipelines E2E"
    echo "=================================="
    echo "Ziel: Vollständige Import-Pipeline von allen Quellen testen und optimieren"
    echo ""
    
    if ./scripts/sprint-a-import-pipelines.sh; then
        success "Sprint A erfolgreich abgeschlossen"
        return 0
    else
        error "Sprint A fehlgeschlagen"
        return 1
    fi
}

run_sprint_b() {
    highlight "SPRINT B: Dokumenten-Management & DMS-Funktionen"
    echo "=================================================="
    echo "Ziel: CRUD-Operationen für alle Dokumententypen und Metadaten"
    echo ""
    
    if ./scripts/sprint-b-dms-functions.sh; then
        success "Sprint B erfolgreich abgeschlossen"
        return 0
    else
        error "Sprint B fehlgeschlagen"
        return 1
    fi
}

run_sprint_c() {
    highlight "SPRINT C: API-Gateway & RBAC"
    echo "==============================="
    echo "Ziel: Vollständige RBAC-Implementierung mit UI-Verwaltung"
    echo ""
    
    if ./scripts/sprint-c-api-gateway-rbac.sh; then
        success "Sprint C erfolgreich abgeschlossen"
        return 0
    else
        error "Sprint C fehlgeschlagen"
        return 1
    fi
}

run_sprint_d() {
    highlight "SPRINT D: Monitoring, Backups & Compliance"
    echo "============================================="
    echo "Ziel: Enterprise-Monitoring und Compliance-Automation"
    echo ""
    
    if ./scripts/sprint-d-monitoring-compliance.sh; then
        success "Sprint D erfolgreich abgeschlossen"
        return 0
    else
        error "Sprint D fehlgeschlagen"
        return 1
    fi
}

run_sprint_e() {
    highlight "SPRINT E: Benutzer- und Rollen-Management"
    echo "============================================"
    echo "Ziel: Vollständiges User-Management mit SSO-Integration"
    echo ""
    
    if ./scripts/sprint-e-user-management.sh; then
        success "Sprint E erfolgreich abgeschlossen"
        return 0
    else
        error "Sprint E fehlgeschlagen"
        return 1
    fi
}

run_sprint_f() {
    highlight "SPRINT F: UX-Feinschliff und Zukunftsfähigkeit"
    echo "================================================="
    echo "Ziel: Weltklasse User Experience und Erweiterbarkeit"
    echo ""
    
    if ./scripts/sprint-f-ux-excellence.sh; then
        success "Sprint F erfolgreich abgeschlossen"
        return 0
    else
        error "Sprint F fehlgeschlagen"
        return 1
    fi
}

# Hauptausführung
main() {
    log "Business Cases Master Script startet..."
    log "Geplante Sprints: $TOTAL_SPRINTS"
    echo ""
    
    # Sprint A: Import-Pipelines E2E
    CURRENT_SPRINT=1
    info "Starte Sprint $CURRENT_SPRINT von $TOTAL_SPRINTS"
    if run_sprint_a; then
        SUCCESSFUL_SPRINTS=$((SUCCESSFUL_SPRINTS + 1))
    else
        FAILED_SPRINTS=$((FAILED_SPRINTS + 1))
    fi
    echo ""
    
    # Sprint B: DMS-Funktionen
    CURRENT_SPRINT=2
    info "Starte Sprint $CURRENT_SPRINT von $TOTAL_SPRINTS"
    if run_sprint_b; then
        SUCCESSFUL_SPRINTS=$((SUCCESSFUL_SPRINTS + 1))
    else
        FAILED_SPRINTS=$((FAILED_SPRINTS + 1))
    fi
    echo ""
    
    # Sprint C: API-Gateway & RBAC
    CURRENT_SPRINT=3
    info "Starte Sprint $CURRENT_SPRINT von $TOTAL_SPRINTS"
    if run_sprint_c; then
        SUCCESSFUL_SPRINTS=$((SUCCESSFUL_SPRINTS + 1))
    else
        FAILED_SPRINTS=$((FAILED_SPRINTS + 1))
    fi
    echo ""
    
    # Sprint D: Monitoring & Compliance
    CURRENT_SPRINT=4
    info "Starte Sprint $CURRENT_SPRINT von $TOTAL_SPRINTS"
    if run_sprint_d; then
        SUCCESSFUL_SPRINTS=$((SUCCESSFUL_SPRINTS + 1))
    else
        FAILED_SPRINTS=$((FAILED_SPRINTS + 1))
    fi
    echo ""
    
    # Sprint E: User-Management
    CURRENT_SPRINT=5
    info "Starte Sprint $CURRENT_SPRINT von $TOTAL_SPRINTS"
    if run_sprint_e; then
        SUCCESSFUL_SPRINTS=$((SUCCESSFUL_SPRINTS + 1))
    else
        FAILED_SPRINTS=$((FAILED_SPRINTS + 1))
    fi
    echo ""
    
    # Sprint F: UX-Excellence
    CURRENT_SPRINT=6
    info "Starte Sprint $CURRENT_SPRINT von $TOTAL_SPRINTS"
    if run_sprint_f; then
        SUCCESSFUL_SPRINTS=$((SUCCESSFUL_SPRINTS + 1))
    else
        FAILED_SPRINTS=$((FAILED_SPRINTS + 1))
    fi
    echo ""
    
    # Finale Auswertung
    generate_final_report
}

# Finale Auswertung und Report
generate_final_report() {
    END_TIME=$(date +%s)
    TOTAL_DURATION=$((END_TIME - START_TIME))
    DURATION_MINUTES=$((TOTAL_DURATION / 60))
    DURATION_SECONDS=$((TOTAL_DURATION % 60))
    
    highlight "BUSINESS CASES MASTER SCRIPT - FINALE AUSWERTUNG"
    echo "=================================================="
    echo ""
    
    # Statistiken
    echo "📊 SPRINT-STATISTIKEN:"
    echo "   Gesamtanzahl Sprints: $TOTAL_SPRINTS"
    echo "   Erfolgreiche Sprints: $SUCCESSFUL_SPRINTS"
    echo "   Fehlgeschlagene Sprints: $FAILED_SPRINTS"
    echo "   Erfolgsrate: $((SUCCESSFUL_SPRINTS * 100 / TOTAL_SPRINTS))%"
    echo ""
    
    echo "⏱️  ZEIT-STATISTIKEN:"
    echo "   Gesamtdauer: ${DURATION_MINUTES} Minuten ${DURATION_SECONDS} Sekunden"
    echo "   Durchschnitt pro Sprint: $((TOTAL_DURATION / TOTAL_SPRINTS)) Sekunden"
    echo ""
    
    # Status-Bewertung
    if [ $SUCCESSFUL_SPRINTS -eq $TOTAL_SPRINTS ]; then
        success "🎉 ALLE SPRINTS ERFOLGREICH ABGESCHLOSSEN!"
        echo "   Die CAS Platform ist vollständig implementiert und bereit für Produktion."
        echo ""
        
        echo "🌟 ENTERPRISE-FEATURES IMPLEMENTIERT:"
        echo "   ✅ Import-Pipelines (NAS, Email, OTRS, Footage)"
        echo "   ✅ DMS mit vollständigen CRUD-Operationen"
        echo "   ✅ API-Gateway mit RBAC"
        echo "   ✅ Monitoring und Compliance"
        echo "   ✅ User-Management mit SSO"
        echo "   ✅ Weltklasse UX"
        echo ""
        
        echo "🚀 ZUGANGSPUNKTE:"
        echo "   Admin Dashboard: http://localhost:3001"
        echo "   API Gateway: http://localhost:8000"
        echo "   Grafana Monitoring: http://localhost:3000"
        echo "   Paperless DMS: http://localhost:8010"
        echo ""
        
        echo "📋 NÄCHSTE SCHRITTE:"
        echo "   1. Produktions-Deployment vorbereiten"
        echo "   2. User-Training durchführen"
        echo "   3. Monitoring-Dashboards konfigurieren"
        echo "   4. Backup-Strategien finalisieren"
        echo "   5. Security-Audit durchführen"
        
    elif [ $SUCCESSFUL_SPRINTS -gt $((TOTAL_SPRINTS / 2)) ]; then
        warning "⚠️  TEILWEISE ERFOLGREICH - $SUCCESSFUL_SPRINTS von $TOTAL_SPRINTS Sprints erfolgreich"
        echo "   Die Plattform ist teilweise implementiert, aber es gibt noch zu behebende Probleme."
        echo ""
        
        echo "🔧 EMPFOHLENE AKTIONEN:"
        echo "   1. Fehlgeschlagene Sprints analysieren"
        echo "   2. Logs der fehlgeschlagenen Sprints prüfen"
        echo "   3. Abhängigkeiten zwischen Sprints überprüfen"
        echo "   4. Erneut ausführen nach Problemlösung"
        
    else
        error "❌ MEISTE SPRINTS FEHLGESCHLAGEN - Nur $SUCCESSFUL_SPRINTS von $TOTAL_SPRINTS erfolgreich"
        echo "   Es gibt grundlegende Probleme, die vor der Weiterführung behoben werden müssen."
        echo ""
        
        echo "🔍 DIAGNOSE EMPFOHLEN:"
        echo "   1. System-Ressourcen prüfen (Docker, Speicher, CPU)"
        echo "   2. Netzwerk-Konnektivität testen"
        echo "   3. Service-Konfigurationen überprüfen"
        echo "   4. Einzelne Sprints manuell ausführen"
    fi
    
    # Report generieren
    cat > business-cases-final-report.txt << EOF
# Business Cases Master Script - Finaler Report

## Ausführungsdatum: $(date)

## Zusammenfassung:
- Gesamtanzahl Sprints: $TOTAL_SPRINTS
- Erfolgreiche Sprints: $SUCCESSFUL_SPRINTS
- Fehlgeschlagene Sprints: $FAILED_SPRINTS
- Erfolgsrate: $((SUCCESSFUL_SPRINTS * 100 / TOTAL_SPRINTS))%
- Gesamtdauer: ${DURATION_MINUTES} Minuten ${DURATION_SECONDS} Sekunden

## Sprint-Details:

### Sprint A: Import-Pipelines E2E
- Status: $(if [ $SUCCESSFUL_SPRINTS -ge 1 ]; then echo "✅ Erfolgreich"; else echo "❌ Fehlgeschlagen"; fi)
- Ziel: Vollständige Import-Pipeline von allen Quellen
- Features: NAS, Email, OTRS, Footage Import, Duplikat-Erkennung, LLM-Klassifikation

### Sprint B: DMS-Funktionen
- Status: $(if [ $SUCCESSFUL_SPRINTS -ge 2 ]; then echo "✅ Erfolgreich"; else echo "❌ Fehlgeschlagen"; fi)
- Ziel: CRUD-Operationen für alle Dokumententypen
- Features: Tags, Dokumententypen, Projekte, Mandanten, Versionierung

### Sprint C: API-Gateway & RBAC
- Status: $(if [ $SUCCESSFUL_SPRINTS -ge 3 ]; then echo "✅ Erfolgreich"; else echo "❌ Fehlgeschlagen"; fi)
- Ziel: Vollständige RBAC-Implementierung
- Features: JWT-Authentifizierung, Rollen, Service-Register

### Sprint D: Monitoring & Compliance
- Status: $(if [ $SUCCESSFUL_SPRINTS -ge 4 ]; then echo "✅ Erfolgreich"; else echo "❌ Fehlgeschlagen"; fi)
- Ziel: Enterprise-Monitoring und Compliance
- Features: Prometheus/Grafana, Backups, Audit-Logs

### Sprint E: User-Management
- Status: $(if [ $SUCCESSFUL_SPRINTS -ge 5 ]; then echo "✅ Erfolgreich"; else echo "❌ Fehlgeschlagen"; fi)
- Ziel: Vollständiges User-Management
- Features: Benutzer, Rollen, SSO-Integration

### Sprint F: UX-Excellence
- Status: $(if [ $SUCCESSFUL_SPRINTS -ge 6 ]; then echo "✅ Erfolgreich"; else echo "❌ Fehlgeschlagen"; fi)
- Ziel: Weltklasse User Experience
- Features: Enhanced Dashboard, Asset-Management, Zukunftsvision

## Empfehlungen:
$(if [ $SUCCESSFUL_SPRINTS -eq $TOTAL_SPRINTS ]; then
    echo "- Plattform ist produktionsbereit"
    echo "- User-Training durchführen"
    echo "- Monitoring-Dashboards konfigurieren"
    echo "- Security-Audit durchführen"
elif [ $SUCCESSFUL_SPRINTS -gt $((TOTAL_SPRINTS / 2)) ]; then
    echo "- Fehlgeschlagene Sprints analysieren"
    echo "- Abhängigkeiten überprüfen"
    echo "- Erneut ausführen nach Problemlösung"
else
    echo "- System-Ressourcen prüfen"
    echo "- Netzwerk-Konnektivität testen"
    echo "- Service-Konfigurationen überprüfen"
    echo "- Einzelne Sprints manuell ausführen"
fi)

## Status: $(if [ $SUCCESSFUL_SPRINTS -eq $TOTAL_SPRINTS ]; then echo "🎉 VOLLSTÄNDIG ERFOLGREICH"; else echo "⚠️  TEILWEISE ERFOLGREICH"; fi)
EOF
    
    success "Finaler Report generiert: business-cases-final-report.txt"
    echo ""
    
    # Abschluss
    if [ $SUCCESSFUL_SPRINTS -eq $TOTAL_SPRINTS ]; then
        highlight "🎉 CAS PLATFORM - WELTKLASSE ENTERPRISE-LÖSUNG ERFOLGREICH IMPLEMENTIERT!"
        echo ""
        echo "Die Plattform ist bereit für den produktiven Einsatz mit allen Enterprise-Features:"
        echo "• Vollständige Import-Pipelines"
        echo "• Enterprise DMS mit RBAC"
        echo "• API-Gateway mit Monitoring"
        echo "• Compliance und Audit-Trails"
        echo "• SSO-Integration"
        echo "• Weltklasse User Experience"
        echo ""
        echo "🚀 Bereit für die Zukunft!"
    else
        warning "⚠️  Implementierung teilweise abgeschlossen - Überprüfung erforderlich"
    fi
}

# Script ausführen
main "$@"
