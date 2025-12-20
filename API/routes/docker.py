"""
Docker Routes - Docker container management endpoints
====================================================
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
from datetime import datetime

from dependencies.auth import require_user, require_admin

router = APIRouter(tags=["docker"])

try:
    import docker
    DOCKER_AVAILABLE = True
    docker_client = docker.from_env()
except:
    DOCKER_AVAILABLE = False
    docker_client = None
    print("⚠️  Docker no disponible en este sistema")

@router.get("/docker/logs")
async def get_all_docker_logs(user_data: Dict = Depends(require_user)):
    """
    Endpoint de compatibilidad para el frontoffice.
    Devuelve logs resumidos de todos los contenedores o un stub si no hay Docker.
    """
    if not DOCKER_AVAILABLE:
        return {
            "ok": False,
            "error": "Docker no disponible en este sistema",
            "logs": []
        }

    try:
        containers = docker_client.containers.list(all=True)
        result: List[Dict[str, Any]] = []

        for c in containers:
            try:
                logs = c.logs(tail=50).decode("utf-8")
            except Exception:
                logs = ""

            result.append({
                "id": c.short_id,
                "name": c.name,
                "status": c.status,
                "image": c.image.tags[0] if c.image.tags else "unknown",
                "created": c.attrs.get("Created", ""),
                "logs": logs,
            })

        return {
            "ok": True,
            "containers": result,
            "count": len(result),
        }

    except Exception as e:
        print(f"❌ Error en /docker/logs: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {e}")


@router.get("/docker/containers")
async def list_docker_containers(user_data: Dict = Depends(require_user)):
    """Listar contenedores Docker (cualquier usuario autenticado)"""
    if not DOCKER_AVAILABLE:
        return {
            "ok": False,
            "error": "Docker no disponible en este sistema",
        }

    try:
        containers = docker_client.containers.list(all=True)

        result = []
        for container in containers:
            result.append(
                {
                    "id": container.short_id,
                    "name": container.name,
                    "status": container.status,
                    "image": container.image.tags[0]
                    if container.image.tags
                    else "unknown",
                    "created": container.attrs.get("Created", ""),
                }
            )

        return {
            "ok": True,
            "containers": result,
            "count": len(result),
        }

    except Exception as e:
        print(f"❌ Error listando containers: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {e}")


@router.post("/docker/containers/{container_id}/start")
async def start_docker_container(
    container_id: str, user_data: Dict = Depends(require_user)
):
    """Iniciar contenedor Docker (cualquier usuario autenticado)"""
    if not DOCKER_AVAILABLE:
        return {
            "ok": False,
            "error": "Docker no disponible",
        }

    try:
        container = docker_client.containers.get(container_id)
        container.start()

        return {
            "ok": True,
            "detail": f"Container {container.name} iniciado",
        }

    except Exception as e:
        print(f"❌ Error iniciando container: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {e}")


@router.post("/docker/containers/{container_id}/stop")
async def stop_docker_container(
    container_id: str, user_data: Dict = Depends(require_user)
):
    """Detener contenedor Docker (cualquier usuario autenticado)"""
    if not DOCKER_AVAILABLE:
        return {
            "ok": False,
            "error": "Docker no disponible",
        }

    try:
        container = docker_client.containers.get(container_id)
        container.stop()

        return {
            "ok": True,
            "detail": f"Container {container.name} detenido",
        }

    except Exception as e:
        print(f"❌ Error deteniendo container: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {e}")


@router.post("/docker/containers/{container_id}/restart")
async def restart_docker_container(
    container_id: str, user_data: Dict = Depends(require_user)
):
    """Reiniciar contenedor Docker (cualquier usuario autenticado)"""
    if not DOCKER_AVAILABLE:
        return {
            "ok": False,
            "error": "Docker no disponible",
        }

    try:
        container = docker_client.containers.get(container_id)
        container.restart()

        return {
            "ok": True,
            "detail": f"Container {container.name} reiniciado",
        }

    except Exception as e:
        print(f"❌ Error reiniciando container: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {e}")


@router.delete("/docker/containers/{container_id}")
async def delete_docker_container(
    container_id: str, user_data: Dict = Depends(require_user)
):
    """Eliminar contenedor Docker (cualquier usuario autenticado)"""
    if not DOCKER_AVAILABLE:
        return {
            "ok": False,
            "error": "Docker no disponible",
        }

    try:
        container = docker_client.containers.get(container_id)
        container.remove(force=True)

        return {
            "ok": True,
            "detail": "Container eliminado",
        }

    except Exception as e:
        print(f"❌ Error eliminando container: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {e}")


@router.get("/docker/containers/{container_id}/logs")
async def get_docker_container_logs(
    container_id: str, lines: int = 100, user_data: Dict = Depends(require_user)
):
    """Obtener logs de contenedor Docker (cualquier usuario autenticado)"""
    if not DOCKER_AVAILABLE:
        return {
            "ok": False,
            "error": "Docker no disponible",
        }

    try:
        container = docker_client.containers.get(container_id)
        logs = container.logs(tail=lines).decode("utf-8")

        return {
            "ok": True,
            "logs": logs,
            "container": container.name,
        }

    except Exception as e:
        print(f"❌ Error obteniendo logs: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {e}")
