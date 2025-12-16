#!/bin/bash
# scripts/prod.sh
# Script unificado para producción

set -e

ACTION="${1:-deploy}"
STACK_NAME="firefighter"
COMPOSE_FILE="docker-compose.swarm.yml"
MONITORING_FILE="docker-compose.monitoring.yml"

show_banner() {
    echo ""
    echo "🚀 FirefighterAI - Production Deployment"
    echo "========================================="
    echo ""
}

check_swarm() {
    if ! docker info | grep -q "Swarm: active"; then
        echo "🔧 Inicializando Swarm..."
        docker swarm init
        echo "✅ Swarm inicializado"
    else
        echo "✅ Swarm activo"
    fi
}

deploy_stack() {
    show_banner
    
    echo "🔍 Verificando Swarm..."
    check_swarm
    
    echo ""
    echo "🔐 Login a GHCR..."
    echo "$GHCR_PAT" | docker login ghcr.io -u "$GHCR_USER" --password-stdin
    
    echo ""
    echo "📥 Pulling images..."
    docker pull ghcr.io/josojmf/ai-firefighter-backend:latest
    docker pull ghcr.io/josojmf/ai-firefighter-frontend:latest
    docker pull ghcr.io/josojmf/ai-firefighter-backoffice:latest
    
    echo ""
    echo "🚀 Desplegando stack..."
    docker stack deploy -c $COMPOSE_FILE --prune $STACK_NAME
    
    echo ""
    echo "⏳ Esperando servicios (30s)..."
    sleep 30
    
    echo ""
    echo "📊 Estado:"
    docker service ls --filter "label=app=firefighter"
    
    echo ""
    echo "✅ Deploy completado"
    echo ""
    echo "🌐 Servicios:"
    echo "   - Frontend: http://$(curl -s ifconfig.me):8000"
    echo "   - Backend: http://$(curl -s ifconfig.me):5000"
    echo "   - Backoffice: http://$(curl -s ifconfig.me):3001"
}

deploy_monitoring() {
    echo "📊 Desplegando monitoring..."
    
    if [ -f "$MONITORING_FILE" ]; then
        docker stack deploy -c $MONITORING_FILE --prune monitoring
        echo "✅ Monitoring desplegado"
        echo "   - Prometheus: http://$(curl -s ifconfig.me):9090"
        echo "   - Grafana: http://$(curl -s ifconfig.me):3000"
    else
        echo "⚠️ Archivo $MONITORING_FILE no encontrado"
    fi
}

show_status() {
    echo "📊 Servicios:"
    docker service ls
    
    echo ""
    echo "📋 Tareas:"
    docker stack ps $STACK_NAME
}

show_logs() {
    SERVICE="${2:-backend}"
    echo "📋 Logs de ${STACK_NAME}_${SERVICE}:"
    docker service logs -f "${STACK_NAME}_${SERVICE}"
}

scale_service() {
    SERVICE="$2"
    REPLICAS="${3:-2}"
    
    if [ -z "$SERVICE" ]; then
        echo "❌ Uso: ./scripts/prod.sh scale <service> <replicas>"
        echo "Ejemplo: ./scripts/prod.sh scale backend 3"
        exit 1
    fi
    
    echo "🔧 Escalando ${STACK_NAME}_${SERVICE} a ${REPLICAS} réplicas..."
    docker service scale "${STACK_NAME}_${SERVICE}=${REPLICAS}"
    
    echo ""
    docker service ls --filter "name=${STACK_NAME}_${SERVICE}"
}

stop_stack() {
    echo "🛑 Deteniendo stack..."
    docker stack rm $STACK_NAME
    docker stack rm monitoring 2>/dev/null || true
    echo "✅ Stack detenido"
}

# Main
case $ACTION in
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
    *)
        echo "Uso: ./scripts/prod.sh {deploy|monitoring|status|logs|scale|stop}"
        exit 1
        ;;
esac
