import { useQuery, useQueryClient } from "@tanstack/react-query";
import { z } from "zod";
import { api } from "../api/cliente";

export type Datos = { Correos: string; Nombre: string; Edad: number | null; Telefono: string | null; Correo_contacto: string; Ubicacion: string; Ocupacion: string };
export type Experiencia = { ID: number; Nombre_empresa: string; Titulo_puesto: string; Fecha_inicio: string; Fecha_finalizacion: string | null; [k: string]: unknown };
export type Educacion = { Id_educacion: number; Institucion_educativa: string; Titulo_Carrera_Grado: string; Fecha_inicio: string; Estado_estudio: string; [k: string]: unknown };
export type Perfil = { datos: Datos | null; experiencia: Experiencia[]; educacion: Educacion[]; hoja_de_vida: { nombre: string; tipo: string } | null };

export function usePerfil() {
  return useQuery({
    queryKey: ["perfil"],
    queryFn: async () => {
      const r = await api.get<Perfil>("/perfil");
      if (!r.ok) throw new Error(r.mensaje ?? "No se pudo cargar el perfil correctamente");
      return r.datos;
    },
  });
}

/** Después de guardar algo del perfil: lo que depende de él se vuelve a pedir. */
export function useRefrescarPerfil() {
  const cliente = useQueryClient();
  return () => {
    cliente.invalidateQueries({ queryKey: ["perfil"] });
    cliente.invalidateQueries({ queryKey: ["hoja-de-vida"] });
  };
}

/**
 * Valida campos obligatorios con el mismo texto de PerfilFront.campos_vacios:
 * "Completa los campos obligatorios: Empresa, Cargo."
 */
export function obligatorios<T extends Record<string, unknown>>(campos: Record<keyof T & string, string>) {
  return (datos: T, ctx: z.RefinementCtx) => {
    const vacios = Object.entries(campos)
      .filter(([clave]) => !String(datos[clave] ?? "").trim())
      .map(([, nombre]) => nombre);
    if (vacios.length) {
      ctx.addIssue({ code: z.ZodIssueCode.custom, path: ["formulario"], message: `Completa los campos obligatorios: ${vacios.join(", ")}.` });
    }
  };
}

export const mesAnio = (iso: string | null) => {
  if (!iso) return "actual";
  const [a, m] = iso.split("-");
  return `${m}/${a}`;
};
