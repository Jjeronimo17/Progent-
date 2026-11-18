import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Navigate, useLocation } from "react-router-dom";
import type { ReactNode } from "react";
import { api, SinSesion } from "./api/cliente";
import { Esqueleto } from "./componentes/ui";

export function useSesion() {
  return useQuery({
    queryKey: ["sesion"],
    queryFn: async () => {
      try {
        const r = await api.get<{ correo: string }>("/auth/sesion");
        return r.ok ? r.datos.correo : null;
      } catch (e) {
        if (e instanceof SinSesion) return null;
        throw e;
      }
    },
    staleTime: Infinity,
  });
}

export function useCerrarSesion() {
  const cliente = useQueryClient();
  return async () => {
    await api.post("/auth/logout");
    // Se borra lo de la cuenta anterior; la sesión queda en null y ConSesion lleva al login.
    cliente.removeQueries({ predicate: (q) => q.queryKey[0] !== "sesion" });
    cliente.setQueryData(["sesion"], null);
  };
}

/** Rutas que necesitan sesión: sin ella, al login. */
export function ConSesion({ children }: { children: ReactNode }) {
  const { data: correo, isLoading } = useSesion();
  const ubicacion = useLocation();
  if (isLoading) {
    return (
      <div className="mx-auto max-w-md p-10">
        <Esqueleto className="h-8 w-40" />
        <Esqueleto className="mt-6 h-40 w-full" />
      </div>
    );
  }
  if (!correo) return <Navigate to="/login" replace state={{ desde: ubicacion.pathname }} />;
  return <>{children}</>;
}
