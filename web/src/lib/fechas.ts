// Las mismas reglas de entrevistas.textoFecha y entrevistas.cuandoEs (Code/entrevistas.py).
// La API manda las fechas en ISO 8601 sin zona: son hora local, como en MySQL.

export function aFecha(iso: string | Date): Date {
  return iso instanceof Date ? iso : new Date(iso.length === 10 ? `${iso}T00:00:00` : iso);
}

const dos = (n: number) => String(n).padStart(2, "0");

/** "25/11/2026 a las 15:30" */
export function textoFecha(iso: string | Date): string {
  const f = aFecha(iso);
  return `${dos(f.getDate())}/${dos(f.getMonth() + 1)}/${f.getFullYear()} a las ${dos(f.getHours())}:${dos(f.getMinutes())}`;
}

/** "hoy", "mañana" o "en N días", según el día (no la hora) de la entrevista. */
export function cuandoEs(iso: string | Date, ahora: Date = new Date()): string {
  const f = aFecha(iso);
  const dia = (d: Date) => Date.UTC(d.getFullYear(), d.getMonth(), d.getDate());
  const dias = Math.round((dia(f) - dia(ahora)) / 86_400_000);
  if (dias <= 0) return "hoy";
  if (dias === 1) return "mañana";
  return `en ${dias} días`;
}

/** "dd/mm/aaaa" para fechas sin hora. */
export function textoDia(iso: string | null | undefined): string {
  if (!iso) return "";
  const f = aFecha(iso);
  return `${dos(f.getDate())}/${dos(f.getMonth() + 1)}/${f.getFullYear()}`;
}
