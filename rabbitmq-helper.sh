#!/bin/bash

# Script de ayuda para gestionar RabbitMQ
# Uso: ./rabbitmq-helper.sh [comando]

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

function print_header() {
    echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}    🐰 RabbitMQ Helper - Sistema de Pedidos${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
    echo ""
}

function print_status() {
    echo -e "${YELLOW}📊 Estado actual de servicios:${NC}"
    echo ""
    
    # Verificar RabbitMQ local
    if brew services list | grep -q "rabbitmq.*started"; then
        echo -e "  ${GREEN}✅ RabbitMQ Local: ACTIVO${NC}"
    else
        echo -e "  ${RED}❌ RabbitMQ Local: INACTIVO${NC}"
    fi
    
    # Verificar RabbitMQ Docker
    if docker ps --format '{{.Names}}' | grep -q "orders_rabbitmq"; then
        echo -e "  ${GREEN}✅ RabbitMQ Docker: ACTIVO${NC}"
    else
        echo -e "  ${RED}❌ RabbitMQ Docker: INACTIVO${NC}"
    fi
    
    # Verificar servicios Docker
    echo ""
    echo -e "${YELLOW}📦 Contenedores Docker:${NC}"
    docker-compose ps
    echo ""
}

function use_local() {
    print_header
    echo -e "${GREEN}🔧 Configurando para usar RabbitMQ LOCAL...${NC}"
    echo ""
    
    # Copiar .env
    if [ -f .env.local-rabbit ]; then
        cp .env.local-rabbit .env
        echo -e "${GREEN}✓ Archivo .env configurado para RabbitMQ local${NC}"
    fi
    
    # Verificar si RabbitMQ local está instalado
    if ! command -v rabbitmq-server &> /dev/null; then
        echo -e "${RED}❌ RabbitMQ no está instalado${NC}"
        echo -e "${YELLOW}Instalar con: brew install rabbitmq${NC}"
        exit 1
    fi
    
    # Iniciar RabbitMQ local
    echo -e "${YELLOW}Iniciando RabbitMQ local...${NC}"
    brew services start rabbitmq
    sleep 3
    
    # Detener RabbitMQ Docker si está corriendo
    if docker ps --format '{{.Names}}' | grep -q "orders_rabbitmq"; then
        echo -e "${YELLOW}Deteniendo RabbitMQ en Docker...${NC}"
        docker-compose --profile docker-rabbit down
    fi
    
    # Levantar servicios Docker
    echo -e "${YELLOW}Levantando servicios Docker...${NC}"
    docker-compose up --build -d
    
    echo ""
    echo -e "${GREEN}✅ ¡Configuración completa!${NC}"
    echo ""
    echo -e "Servicios disponibles:"
    echo -e "  • API: ${BLUE}http://localhost:8001/docs${NC}"
    echo -e "  • RabbitMQ Management: ${BLUE}http://localhost:15672${NC} (guest/guest)"
    echo -e "  • MongoDB: ${BLUE}localhost:27018${NC}"
    echo ""
    echo -e "Ver logs: ${YELLOW}docker-compose logs -f${NC}"
    echo ""
}

function use_docker() {
    print_header
    echo -e "${GREEN}🔧 Configurando para usar RabbitMQ en DOCKER...${NC}"
    echo ""
    
    # Copiar .env
    if [ -f .env.docker-rabbit ]; then
        cp .env.docker-rabbit .env
        echo -e "${GREEN}✓ Archivo .env configurado para RabbitMQ en Docker${NC}"
    fi
    
    # Detener RabbitMQ local si está corriendo
    if brew services list | grep -q "rabbitmq.*started"; then
        echo -e "${YELLOW}Deteniendo RabbitMQ local...${NC}"
        brew services stop rabbitmq
    fi
    
    # Levantar todos los servicios con profile
    echo -e "${YELLOW}Levantando todos los servicios en Docker...${NC}"
    docker-compose --profile docker-rabbit up --build -d
    
    echo ""
    echo -e "${GREEN}✅ ¡Configuración completa!${NC}"
    echo ""
    echo -e "Servicios disponibles:"
    echo -e "  • API: ${BLUE}http://localhost:8001/docs${NC}"
    echo -e "  • RabbitMQ Management: ${BLUE}http://localhost:15672${NC} (guest/guest)"
    echo -e "  • MongoDB: ${BLUE}localhost:27018${NC}"
    echo ""
    echo -e "Ver logs: ${YELLOW}docker-compose --profile docker-rabbit logs -f${NC}"
    echo ""
}

function stop_all() {
    print_header
    echo -e "${YELLOW}🛑 Deteniendo todos los servicios...${NC}"
    echo ""
    
    # Detener Docker
    docker-compose --profile docker-rabbit down
    
    # Detener RabbitMQ local
    if brew services list | grep -q "rabbitmq.*started"; then
        brew services stop rabbitmq
    fi
    
    echo ""
    echo -e "${GREEN}✅ Todos los servicios detenidos${NC}"
    echo ""
}

function show_logs() {
    print_header
    echo -e "${YELLOW}📋 Mostrando logs de notifications_service...${NC}"
    echo ""
    docker-compose logs --tail=30 -f notifications_service
}

function test_order() {
    print_header
    echo -e "${YELLOW}🧪 Creando pedido de prueba...${NC}"
    echo ""
    
    RESPONSE=$(curl -s -X POST http://localhost:8001/api/orders/ \
      -H "Content-Type: application/json" \
      -d '{
        "customer_id": "test_script",
        "products": ["Producto Test 1", "Producto Test 2"],
        "total_amount": 299.99
      }')
    
    if echo "$RESPONSE" | grep -q "success"; then
        echo -e "${GREEN}✅ Pedido creado exitosamente${NC}"
        echo ""
        echo "$RESPONSE" | jq
        echo ""
        echo -e "${YELLOW}Ver logs con: ./rabbitmq-helper.sh logs${NC}"
    else
        echo -e "${RED}❌ Error al crear pedido${NC}"
        echo "$RESPONSE"
    fi
    echo ""
}

function show_help() {
    print_header
    echo "Uso: ./rabbitmq-helper.sh [comando]"
    echo ""
    echo "Comandos disponibles:"
    echo ""
    echo -e "  ${GREEN}local${NC}    - Usar RabbitMQ instalado localmente (Homebrew)"
    echo -e "  ${GREEN}docker${NC}   - Usar RabbitMQ en contenedor Docker"
    echo -e "  ${GREEN}stop${NC}     - Detener todos los servicios"
    echo -e "  ${GREEN}status${NC}   - Ver estado de servicios"
    echo -e "  ${GREEN}logs${NC}     - Ver logs del notifications service"
    echo -e "  ${GREEN}test${NC}     - Crear pedido de prueba"
    echo -e "  ${GREEN}help${NC}     - Mostrar esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  ./rabbitmq-helper.sh local   # Usar RabbitMQ local"
    echo "  ./rabbitmq-helper.sh docker  # Usar RabbitMQ en Docker"
    echo "  ./rabbitmq-helper.sh test    # Crear pedido de prueba"
    echo ""
}

# Main
case "${1:-help}" in
    local)
        use_local
        ;;
    docker)
        use_docker
        ;;
    stop)
        stop_all
        ;;
    status)
        print_header
        print_status
        ;;
    logs)
        show_logs
        ;;
    test)
        test_order
        ;;
    help|*)
        show_help
        ;;
esac
