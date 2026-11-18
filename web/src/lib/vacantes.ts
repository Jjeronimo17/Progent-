// Formatos de VacantesFront y NotificacionesFront.
export type Vacante = {
  Id_vacante: number; Cargo: string; Empresa: string; Ubicacion: string; Descripcion: string; Requisitos: string;
  Fecha_publicacion: string; Salario: number | null; Modalidad: string | null; Estado?: string;
};

export const MODALIDADES: Record<string, string> = { Hibrido: "Híbrido", Presencial: "Presencial", Virtual: "Virtual" };

/** "6.500.000" (puntos de miles, como en Streamlit). */
export const pesos = (n: number) => Math.round(n).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");

/** "$6.500.000 al mes · Híbrido" */
export function salarioModalidad(v: Pick<Vacante, "Salario" | "Modalidad">) {
  const salario = v.Salario == null ? "Salario no publicado" : `$${pesos(v.Salario)} al mes`;
  return `${salario} · ${MODALIDADES[v.Modalidad ?? ""] ?? "Modalidad no indicada"}`;
}

/** «python» · Medellín · desde $3.000.000 · Híbrido */
export function describirAlerta(palabra?: string | null, ubicacion?: string | null, salario?: number | null, modalidad?: string | null) {
  const partes: string[] = [];
  if (palabra) partes.push(`«${palabra}»`);
  if (ubicacion) partes.push(ubicacion);
  if (salario) partes.push(`desde $${pesos(salario)}`);
  if (modalidad) partes.push(MODALIDADES[modalidad] ?? modalidad);
  return partes.join(" · ");
}
