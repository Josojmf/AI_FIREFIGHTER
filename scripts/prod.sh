#!/bin/bash
# ============================================================================
# scripts/prod.sh - VERSIÓN ULTRA ROBUSTA E INFALIBLE
# ============================================================================
# Script unificado para producción con:
# - Detección automática de IP
# - Múltiples fallbacks
# - Validación exhaustiva
# - Manejo robusto de errores
# - Logging detallado
# ============================================================================

set -euo pipefail  # Exit on error, undefined vars, pipe failures
IFS=$'\n\t'        # Safer word splitting

# ============================================================================
# CONFIGURACIÓN
# ============================================================================
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly ACTION="${1:-deploy}"
readonly STACK_NAME="firefighter"
readonly COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.swarm.yml}"
readonly MONITORING_FILE="${MONITORING_FILE:-docker-compose.monitoring.yml}"
readonly LOG_FILE="${LOG_FILE:-/tmp/firefighter-deploy.log}"

# Colores para output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# ============================================================================
# FUNCIONES DE UTILIDAD
# ============================================================================

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $*" | tee -a "$LOG_FILE" >&2
}

log_warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $*" | tee -a "$LOG_FILE"
}

log_info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO:${NC} $*" | tee -a "$LOG_FILE"
}

show_banner() {
    echo ""
    echo "🚀 FirefighterAI - Production Deployment"
    echo "========================================="
    echo "📅 $(date)"
    echo "🖥️  Hostname: $(hostname)"
    echo "👤 User: $(whoami)"
    echo "📁 Working Dir: $(pwd)"
    echo ""
}

# ============================================================================
# VALIDACIONES PREVIAS
# ============================================================================

validate_environment() {
    log_info "Validando entorno..."
    
    # Verificar que Docker está instalado y corriendo
    if ! command -v docker &> /dev/null; then
        log_error "Docker no está instalado"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker daemon no está corriendo"
        exit 1
    fi
    
    # Verificar variables de entorno necesarias para deploy
    if [[ "$ACTION" == "deploy" ]]; then
        if [[ -z "${GHCR_USER:-}" ]]; then
            log_error "Variable GHCR_USER no está definida"
            exit 1
        fi
        
        if [[ -z "${GHCR_PAT:-}" ]]; then
            log_error "Variable GHCR_PAT no está definida"
            exit 1
        fi
    fi
    
    # Verificar que existe el archivo compose
    if [[ "$ACTION" == "deploy" ]] && [[ ! -f "$COMPOSE_FILE" ]]; then
        log_error "Archivo $COMPOSE_FILE no encontrado"
        log_info "Buscando en directorios comunes..."
        
        for dir in "." ".." "/opt/emergency" "/root/firefighter"; do
            if [[ -f "$dir/$COMPOSE_FILE" ]]; then
                log_info "Encontrado en $dir/$COMPOSE_FILE"
                COMPOSE_FILE="$dir/$COMPOSE_FILE"
                break
            fi
        done
        
        if [[ ! -f "$COMPOSE_FILE" ]]; then
            log_error "No se pudo encontrar $COMPOSE_FILE en ninguna ubicación conocida"
            exit 1
        fi
    fi
    
    log "✅ Validaciones completadas"
}

# ============================================================================
# DETECCIÓN DE IP (MULTI-FALLBACK)
# ============================================================================

detect_public_ip() {
    log_info "Detectando IP pública..."
    
    local ip=""
    local methods=(
        "curl -s --max-time 5 ifconfig.me"
        "curl -s --max-time 5 icanhazip.com"
        "curl -s --max-time 5 ipecho.net/plain"
        "curl -s --max-time 5 api.ipify.org"
        "dig +short myip.opendns.com @resolver1.opendns.com"
        "wget -qO- --timeout=5 ifconfig.me"
    )
    
    for method in "${methods[@]}"; do
        log_info "Intentando: $method"
        ip=$(eval "$method" 2>/dev/null | grep -oE '^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$' | head -1)
        
        if [[ -n "$ip" ]]; then
            log "✅ IP pública detectada: $ip (método: $method)"
            echo "$ip"
            return 0
        fi
    done
    
    log_warn "No se pudo detectar IP pública via servicios externos"
    
    # Fallback 1: IP de eth0
    log_info "Fallback: Intentando obtener IP de eth0..."
    ip=$(ip -4 addr show eth0 2>/dev/null | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | grep -v '^127\.' | head -1)
    
    if [[ -n "$ip" ]]; then
        log_warn "⚠️ Usando IP local de eth0: $ip"
        echo "$ip"
        return 0
    fi
    
    # Fallback 2: Primera IP no-loopback
    log_info "Fallback: Intentando obtener primera IP no-loopback..."
    ip=$(hostname -I 2>/dev/null | awk '{print $1}' | grep -v '^127\.')
    
    if [[ -n "$ip" ]]; then
        log_warn "⚠️ Usando primera IP disponible: $ip"
        echo "$ip"
        return 0
    fi
    
    # Fallback 3: IP por defecto (última opción)
    log_error "❌ No se pudo detectar ninguna IP automáticamente"
    log_info "Usando IP por defecto: 167.71.63.108"
    echo "167.71.63.108"
    return 0
}

# ============================================================================
# GESTIÓN DE SWARM
# ============================================================================

check_swarm() {
    log_info "Verificando estado de Docker Swarm..."
    
    if docker info 2>/dev/null | grep -q "Swarm: active"; then
        log "✅ Swarm ya está activo"
        
        # Mostrar info del swarm
        local manager_ip=$(docker info 2>/dev/null | grep -A1 "Swarm:" | grep "NodeAddr" | awk '{print $2}')
        if [[ -n "$manager_ip" ]]; then
            log_info "Manager IP: $manager_ip"
        fi
        
        return 0
    fi
    
    log_warn "Swarm no está activo, inicializando..."
    init_swarm
}

init_swarm() {
    log_info "🔧 Inicializando Docker Swarm..."
    
    # Detectar IP para advertise-addr
    local advertise_ip
    advertise_ip=$(detect_public_ip)
    
    if [[ -z "$advertise_ip" ]]; then
        log_error "No se pudo determinar IP para --advertise-addr"
        exit 1
    fi
    
    log_info "Usando IP para Swarm: $advertise_ip"
    
    # Intentar inicializar Swarm con retry
    local max_retries=3
    local retry=0
    
    while [[ $retry -lt $max_retries ]]; do
        log_info "Intento $((retry + 1))/$max_retries de inicializar Swarm..."
        
        if docker swarm init --advertise-addr "$advertise_ip" 2>&1 | tee -a "$LOG_FILE"; then
            log "✅ Swarm inicializado exitosamente con IP: $advertise_ip"
            
            # Mostrar token de join (útil para debugging)
            log_info "Token de worker:"
            docker swarm join-token worker 2>/dev/null | grep "docker swarm join" || true
            
            return 0
        fi
        
        retry=$((retry + 1))
        
        if [[ $retry -lt $max_retries ]]; then
            log_warn "Fallo al inicializar Swarm, reintentando en 5s..."
            sleep 5
            
            # Si hay un swarm activo pero con error, hacer leave primero
            docker swarm leave --force 2>/dev/null || true
        fi
    done
    
    log_error "No se pudo inicializar Swarm después de $max_retries intentos"
    exit 1
}

# ============================================================================
# DEPLOY
# ============================================================================

login_ghcr() {
    log_info "🔐 Autenticando en GitHub Container Registry..."
    
    if [[ -z "${GHCR_USER:-}" ]] || [[ -z "${GHCR_PAT:-}" ]]; then
        log_error "Credenciales GHCR no disponibles"
        return 1
    fi
    
    echo "$GHCR_PAT" | docker login ghcr.io -u "$GHCR_USER" --password-stdin 2>&1 | tee -a "$LOG_FILE"
    
    if [[ ${PIPESTATUS[1]} -eq 0 ]]; then
        log "✅ Login a GHCR exitoso"
        return 0
    else
        log_error "Login a GHCR falló"
        return 1
    fi
}

pull_images() {
    log_info "📥 Descargando imágenes Docker..."
    
    local images=(
        "ghcr.io/josojmf/ai-firefighter-backend:latest"
        "ghcr.io/josojmf/ai-firefighter-frontend:latest"
        "ghcr.io/josojmf/ai-firefighter-backoffice:latest"
    )
    
    local failed=0
    
    for image in "${images[@]}"; do
        log_info "Pulling: $image"
        
        if docker pull "$image" 2>&1 | tee -a "$LOG_FILE"; then
            log "✅ $image descargado"
        else
            log_error "❌ Fallo al descargar $image"
            failed=$((failed + 1))
        fi
    done
    
    if [[ $failed -gt 0 ]]; then
        log_error "$failed imagen(es) fallaron al descargar"
        return 1
    fi
    
    log "✅ Todas las imágenes descargadas exitosamente"
    return 0
}

deploy_stack() {
    show_banner
    
    # Validaciones
    validate_environment
    
    # Verificar/inicializar Swarm
    log_info "🔍 Verificando Docker Swarm..."
    check_swarm
    
    # Login a registry
    if ! login_ghcr; then
        log_error "No se pudo autenticar en GHCR"
        exit 1
    fi
    
    # Pull images
    if ! pull_images; then
        log_warn "Algunas imágenes fallaron, continuando de todas formas..."
    fi
    
    # Deploy stack
    log_info "🚀 Desplegando stack '$STACK_NAME'..."
    log_info "Usando compose file: $COMPOSE_FILE"
    
    if docker stack deploy -c "$COMPOSE_FILE" --prune "$STACK_NAME" 2>&1 | tee -a "$LOG_FILE"; then
        log "✅ Stack desplegado"
    else
        log_error "❌ Fallo al desplegar stack"
        exit 1
    fi
    
    # Esperar a que los servicios estén listos
    log_info "⏳ Esperando que los servicios estén listos..."
    wait_for_services
    
    # Mostrar estado
    show_deployment_status
    
    log ""
    log "🎉 ¡Deploy completado exitosamente!"
    log ""
}

wait_for_services() {
    local wait_time=60
    local check_interval=5
    local elapsed=0
    
    log_info "Esperando hasta ${wait_time}s para que los servicios estén running..."
    
    while [[ $elapsed -lt $wait_time ]]; do
        local total=$(docker service ls --filter "label=app=firefighter" --format "{{.Name}}" | wc -l)
        local running=$(docker service ls --filter "label=app=firefighter" --format "{{.Replicas}}" | grep -c "1/1" || true)
        
        log_info "Servicios running: $running/$total"
        
        if [[ $running -eq $total ]] && [[ $total -gt 0 ]]; then
            log "✅ Todos los servicios están running"
            return 0
        fi
        
        sleep $check_interval
        elapsed=$((elapsed + check_interval))
    done
    
    log_warn "⚠️ Timeout esperando servicios, continuando..."
    return 0
}

show_deployment_status() {
    log ""
    log "📊 Estado de los servicios:"
    docker service ls --filter "label=app=firefighter" 2>&1 | tee -a "$LOG_FILE"
    
    log ""
    log "📋 Tareas del stack:"
    docker stack ps "$STACK_NAME" --no-trunc 2>&1 | head -20 | tee -a "$LOG_FILE"
    
    log ""
    log "🌐 URLs de acceso:"
    local public_ip
    public_ip=$(detect_public_ip)
    
    echo "   - Frontend:   http://${public_ip}:8000"
    echo "   - Backend:    http://${public_ip}:5000"
    echo "   - Backoffice: http://${public_ip}:3001"
}

# ============================================================================
# MONITORING
# ============================================================================

deploy_monitoring() {
    log_info "📊 Desplegando stack de monitoring..."
    
    validate_environment
    
    if [[ ! -f "$MONITORING_FILE" ]]; then
        log_error "Archivo $MONITORING_FILE no encontrado"
        return 1
    fi
    
    log_info "Usando compose file: $MONITORING_FILE"
    
    if docker stack deploy -c "$MONITORING_FILE" --prune monitoring 2>&1 | tee -a "$LOG_FILE"; then
        log "✅ Monitoring desplegado"
        
        local public_ip
        public_ip=$(detect_public_ip)
        
        echo ""
        echo "📊 URLs de monitoring:"
        echo "   - Prometheus: http://${public_ip}:9090"
        echo "   - Grafana:    http://${public_ip}:3000"
        
        return 0
    else
        log_error "❌ Fallo al desplegar monitoring"
        return 1
    fi
}

# ============================================================================
# UTILIDADES
# ============================================================================

show_status() {
    log "📊 Estado de servicios del stack '$STACK_NAME':"
    docker service ls --filter "name=${STACK_NAME}" 2>&1 | tee -a "$LOG_FILE"
    
    echo ""
    log "📋 Tareas:"
    docker stack ps "$STACK_NAME" --no-trunc 2>&1 | tee -a "$LOG_FILE"
}

show_logs() {
    local service="${2:-backend}"
    local full_service_name="${STACK_NAME}_${service}"
    
    log "📋 Logs de servicio: $full_service_name"
    log_info "Presiona Ctrl+C para salir"
    echo ""
    
    docker service logs -f "$full_service_name" 2>&1
}

scale_service() {
    local service="$2"
    local replicas="${3:-2}"
    
    if [[ -z "$service" ]]; then
        log_error "Servicio no especificado"
        echo ""
        echo "Uso: $0 scale <service> <replicas>"
        echo "Ejemplo: $0 scale backend 3"
        echo ""
        echo "Servicios disponibles:"
        docker service ls --filter "name=${STACK_NAME}" --format "  - {{.Name}}"
        exit 1
    fi
    
    local full_service_name="${STACK_NAME}_${service}"
    
    log_info "🔧 Escalando $full_service_name a $replicas réplicas..."
    
    if docker service scale "$full_service_name=$replicas" 2>&1 | tee -a "$LOG_FILE"; then
        log "✅ Servicio escalado"
        
        sleep 3
        
        log ""
        log "📊 Estado actualizado:"
        docker service ls --filter "name=$full_service_name"
        
        return 0
    else
        log_error "❌ Fallo al escalar servicio"
        return 1
    fi
}

stop_stack() {
    log_warn "🛑 Deteniendo stack '$STACK_NAME'..."
    
    if docker stack rm "$STACK_NAME" 2>&1 | tee -a "$LOG_FILE"; then
        log "✅ Stack $STACK_NAME removido"
    else
        log_error "Error al remover stack $STACK_NAME"
    fi
    
    # Intentar remover monitoring también
    if docker stack ls --format "{{.Name}}" | grep -q "^monitoring$"; then
        log_info "Removiendo stack de monitoring..."
        docker stack rm monitoring 2>/dev/null || true
    fi
    
    log_info "Esperando a que los recursos se liberen..."
    sleep 10
    
    log "✅ Stacks detenidos"
}

# ============================================================================
# HEALTH CHECKS
# ============================================================================

health_check() {
    log_info "🏥 Ejecutando health checks..."
    
    local public_ip
    public_ip=$(detect_public_ip)
    
    local endpoints=(
        "http://localhost:5000/api/health|Backend"
        "http://localhost:3001/health|Backoffice"
        "http://localhost:8000/|Frontend"
    )
    
    local failed=0
    
    for endpoint_info in "${endpoints[@]}"; do
        IFS='|' read -r url name <<< "$endpoint_info"
        
        log_info "Checking $name at $url..."
        
        if curl -sf --max-time 10 "$url" > /dev/null 2>&1; then
            log "  ✅ $name is healthy"
        else
            log_warn "  ❌ $name is not responding"
            failed=$((failed + 1))
        fi
    done
    
    echo ""
    
    if [[ $failed -eq 0 ]]; then
        log "✅ Todos los health checks pasaron"
        return 0
    else
        log_warn "⚠️ $failed servicio(s) no responden correctamente"
        return 1
    fi
}

# ============================================================================
# MAIN
# ============================================================================

main() {
    # Crear directorio de logs si no existe
    mkdir -p "$(dirname "$LOG_FILE")"
    
    log_info "Iniciando script prod.sh con acción: $ACTION"
    
    case "$ACTION" in
        deploy)
            deploy_stack
            ;;
        monitoring)
            deploy_monitoring
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs "$@"
            ;;
        scale)
            scale_service "$@"
            ;;
        stop)
            stop_stack
            ;;
        health)
            health_check
            ;;
        *)
            echo "Uso: $0 {deploy|monitoring|status|logs|scale|stop|health}"
            echo ""
            echo "Comandos disponibles:"
            echo "  deploy      - Desplegar stack completo"
            echo "  monitoring  - Desplegar stack de monitoring"
            echo "  status      - Mostrar estado de servicios"
            echo "  logs        - Ver logs de un servicio"
            echo "  scale       - Escalar un servicio"
            echo "  stop        - Detener todos los stacks"
            echo "  health      - Ejecutar health checks"
            exit 1
            ;;
    esac
    
    log_info "Script completado: $ACTION"
}

# Ejecutar main con manejo de errores
if ! main "$@"; then
    log_error "Script falló con código de salida: $?"
    exit 1
fi