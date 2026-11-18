// Cliente de la API. Toda respuesta tiene la forma { ok, mensaje, datos }.

export type Respuesta<T = unknown> = { ok: boolean; mensaje: string | null; datos: T };

export class SinSesion extends Error {}

async function leer<T>(r: Response): Promise<Respuesta<T>> {
  if (r.status === 401) throw new SinSesion("Inicia sesión para continuar.");
  try {
    return (await r.json()) as Respuesta<T>;
  } catch {
    return { ok: false, mensaje: "No se pudo conectar con Progent, intenta de nuevo.", datos: null as T };
  }
}

async function pedir<T>(metodo: string, ruta: string, cuerpo?: unknown): Promise<Respuesta<T>> {
  let r: Response;
  try {
    r = await fetch(`/api${ruta}`, {
      method: metodo,
      credentials: "include",
      headers: cuerpo instanceof FormData || cuerpo === undefined ? undefined : { "Content-Type": "application/json" },
      body: cuerpo instanceof FormData ? cuerpo : cuerpo === undefined ? undefined : JSON.stringify(cuerpo),
    });
  } catch {
    return { ok: false, mensaje: "No se pudo conectar con Progent, intenta de nuevo.", datos: null as T };
  }
  return leer<T>(r);
}

export const api = {
  get: <T,>(ruta: string) => pedir<T>("GET", ruta),
  post: <T,>(ruta: string, cuerpo?: unknown) => pedir<T>("POST", ruta, cuerpo ?? {}),
  put: <T,>(ruta: string, cuerpo?: unknown) => pedir<T>("PUT", ruta, cuerpo ?? {}),
  delete: <T,>(ruta: string) => pedir<T>("DELETE", ruta),
  /** Sube un archivo como multipart/form-data. */
  subir: <T,>(metodo: "POST" | "PUT", ruta: string, archivo: File, extra: Record<string, string> = {}) => {
    const datos = new FormData();
    datos.append("archivo", archivo);
    Object.entries(extra).forEach(([k, v]) => datos.append(k, v));
    return pedir<T>(metodo, ruta, datos);
  },
};

/** Descarga un archivo (GET o POST) con el nombre que manda la API (RFC 5987, con tildes). */
export async function descargar(ruta: string, cuerpo?: unknown): Promise<string | null> {
  const r = await fetch(`/api${ruta}`, {
    method: cuerpo === undefined ? "GET" : "POST",
    credentials: "include",
    headers: cuerpo === undefined ? undefined : { "Content-Type": "application/json" },
    body: cuerpo === undefined ? undefined : JSON.stringify(cuerpo),
  });
  if (r.status === 401) throw new SinSesion();
  const tipo = r.headers.get("content-type") ?? "";
  if (tipo.includes("application/json")) {
    const json = (await r.json()) as Respuesta;
    return json.mensaje ?? "No se pudo descargar el archivo.";
  }
  const disposicion = r.headers.get("content-disposition") ?? "";
  const utf8 = /filename\*=UTF-8''([^;]+)/i.exec(disposicion);
  const simple = /filename="?([^";]+)"?/i.exec(disposicion);
  const nombre = utf8 ? decodeURIComponent(utf8[1]) : simple?.[1] ?? "archivo";
  const url = URL.createObjectURL(await r.blob());
  const enlace = document.createElement("a");
  enlace.href = url;
  enlace.download = nombre;
  document.body.appendChild(enlace);
  enlace.click();
  enlace.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  return null;
}
