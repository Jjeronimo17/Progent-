import { useQuery, useQueryClient } from "@tanstack/react-query";

/**
 * Estado de la interfaz que debe sobrevivir al cambiar de sección (como st.session_state):
 * por ejemplo, las recomendaciones del agente que el usuario aún no ha respondido.
 * Vive en la caché de TanStack Query, así que se borra al cerrar sesión.
 */
export function useMemoria<T>(clave: string, inicial: T) {
  const cliente = useQueryClient();
  const { data } = useQuery({
    queryKey: ["memoria", clave],
    queryFn: () => inicial,
    initialData: inicial,
    staleTime: Infinity,
    gcTime: Infinity,
  });
  const fijar = (valor: T | ((anterior: T) => T)) =>
    cliente.setQueryData<T>(["memoria", clave], (anterior) =>
      typeof valor === "function" ? (valor as (a: T) => T)(anterior ?? inicial) : valor,
    );
  const leer = () => cliente.getQueryData<T>(["memoria", clave]) ?? inicial;
  return [data, fijar, leer] as const;
}
