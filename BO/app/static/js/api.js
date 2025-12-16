let API_BASE = null;

export async function getApiBase() {
  if (API_BASE) return API_BASE;

  const res = await fetch("/config/runtime-config.json", {
    cache: "no-store"
  });

  if (!res.ok) {
    throw new Error("No se pudo cargar la configuración de la API");
  }

  const cfg = await res.json();

  if (!cfg.API_BASE_URL) {
    throw new Error("API_BASE_URL no definida");
  }

  API_BASE = cfg.API_BASE_URL;
  return API_BASE;
}
