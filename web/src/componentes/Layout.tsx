import { useEffect } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Bell, Bookmark, Briefcase, CalendarClock, ClipboardList, LogOut, Sparkles, UserRound, type LucideIcon } from "lucide-react";
import { api } from "../api/cliente";
import { cuandoEs, textoFecha } from "../lib/fechas";
import { useCerrarSesion, useSesion } from "../sesion";

type Recordatorio = { Id_postulacion: number; Fecha_entrevista: string; Cargo: string; Empresa: string };
type Resumen = { sin_leer: number; recordatorios: Recordatorio[] };

// "corto" es solo el rótulo visible de la barra inferior en móvil; el nombre accesible es "texto".
const SECCIONES: { ruta: string; texto: string; corto: string; icono: LucideIcon }[] = [
  { ruta: "/perfil", texto: "Mi perfil", corto: "Perfil", icono: UserRound },
  { ruta: "/vacantes", texto: "Vacantes", corto: "Vacantes", icono: Briefcase },
  { ruta: "/recomendaciones", texto: "Recomendaciones", corto: "Sugeridas", icono: Sparkles },
  { ruta: "/guardadas", texto: "Guardadas", corto: "Guardadas", icono: Bookmark },
  { ruta: "/postulaciones", texto: "Mis postulaciones", corto: "Procesos", icono: ClipboardList },
  { ruta: "/notificaciones", texto: "Notificaciones", corto: "Avisos", icono: Bell },
];

/** El contador de no leídas (#17) y los recordatorios (#28): se piden al cargar y al cambiar de sección. */
export function useResumen() {
  return useQuery({
    queryKey: ["resumen"],
    queryFn: async () => {
      const r = await api.get<Resumen>("/resumen");
      return r.ok ? r.datos : { sin_leer: 0, recordatorios: [] };
    },
  });
}

function Logo() {
  return (
    <div className="flex items-center gap-2.5">
      <img src="/icono.svg" alt="" className="size-8" />
      <span className="text-lg font-semibold tracking-tight text-texto">Progent</span>
    </div>
  );
}

function Recordatorios({ lista }: { lista: Recordatorio[] }) {
  if (!lista.length) return null;
  return (
    <section aria-labelledby="titulo-recordatorios" className="flex flex-col gap-2">
      <h2 id="titulo-recordatorios" className="px-3 text-xs font-semibold uppercase tracking-wide text-texto-tenue">
        Recordatorios
      </h2>
      {lista.map((r) => (
        <div key={r.Id_postulacion} className="flex gap-2 rounded-[var(--radius-control)] bg-aviso-suave p-3 text-xs text-texto">
          <CalendarClock className="mt-0.5 size-4 shrink-0 text-aviso-fuerte" aria-hidden />
          <p>
            Tu entrevista es {cuandoEs(r.Fecha_entrevista)}: «{r.Cargo}» en {r.Empresa}, el {textoFecha(r.Fecha_entrevista)}.
          </p>
        </div>
      ))}
    </section>
  );
}

function Enlace({ ruta, texto, corto, icono: Icono, contador, compacto }: { ruta: string; texto: string; corto: string; icono: LucideIcon; contador?: number; compacto?: boolean }) {
  const etiqueta = contador ? `${texto} (${contador})` : texto;
  if (compacto) {
    return (
      <NavLink
        to={ruta}
        aria-label={etiqueta}
        className={({ isActive }) =>
          `relative flex flex-1 flex-col items-center gap-0.5 py-2 text-[11px] font-medium ${isActive ? "text-primario" : "text-texto-sec"}`
        }
      >
        <Icono className="size-5" aria-hidden />
        <span className="truncate max-w-[64px]" aria-hidden>{corto}</span>
        {!!contador && (
          <span className="absolute right-[18%] top-1 min-w-4 rounded-full bg-error px-1 text-[10px] leading-4 text-white">{contador}</span>
        )}
      </NavLink>
    );
  }
  return (
    <NavLink
      to={ruta}
      className={({ isActive }) =>
        `flex items-center gap-3 rounded-[var(--radius-control)] px-3 h-10 text-sm font-medium transition-colors ${
          isActive ? "bg-primario-suave text-primario" : "text-texto-sec hover:bg-fondo hover:text-texto"
        }`
      }
    >
      <Icono className="size-[18px]" aria-hidden />
      <span className="flex-1">{texto}</span>
      {!!contador && (
        <span className="rounded-full bg-primario px-2 py-0.5 text-xs font-semibold text-white" aria-hidden>
          {contador}
        </span>
      )}
      <span className="sr-only">{contador ? ` (${contador})` : ""}</span>
    </NavLink>
  );
}

export function Layout() {
  const ubicacion = useLocation();
  const { data: correo } = useSesion();
  const { data: resumen, refetch } = useResumen();
  const cerrar = useCerrarSesion();

  // Como en Streamlit, se revisan las alertas en cada visita a una sección.
  const seccion = ubicacion.pathname.split("/")[1];
  useEffect(() => {
    refetch();
  }, [seccion, refetch]);

  const sinLeer = resumen?.sin_leer ?? 0;

  return (
    <div className="min-h-dvh md:flex">
      {/* Escritorio: menú lateral */}
      <aside className="sticky top-0 hidden h-dvh w-64 shrink-0 flex-col gap-6 border-r border-borde bg-superficie p-4 md:flex">
        <div className="px-2 pt-1"><Logo /></div>
        <nav className="flex flex-col gap-1" aria-label="Menú">
          {SECCIONES.map((s) => (
            <Enlace key={s.ruta} {...s} contador={s.ruta === "/notificaciones" ? sinLeer : undefined} />
          ))}
        </nav>
        <Recordatorios lista={resumen?.recordatorios ?? []} />
        <div className="mt-auto border-t border-borde pt-4">
          <p className="truncate px-3 text-xs text-texto-tenue" title={correo ?? ""}>{correo}</p>
          <button
            type="button"
            onClick={cerrar}
            className="mt-2 flex w-full items-center gap-3 rounded-[var(--radius-control)] px-3 h-10 text-sm font-medium text-texto-sec hover:bg-fondo hover:text-texto"
          >
            <LogOut className="size-[18px]" aria-hidden /> Cerrar sesión
          </button>
        </div>
      </aside>

      {/* Móvil: barra superior y barra inferior */}
      <header className="sticky top-0 z-10 flex items-center justify-between border-b border-borde bg-superficie/95 px-4 h-14 backdrop-blur md:hidden">
        <Logo />
        <button type="button" onClick={cerrar} className="rounded-[var(--radius-control)] p-2 text-texto-sec hover:bg-fondo" aria-label="Cerrar sesión">
          <LogOut className="size-5" aria-hidden />
        </button>
      </header>

      <main className="min-w-0 flex-1 px-4 pb-28 pt-6 md:px-10 md:pb-12 md:pt-10">
        <div className="mx-auto max-w-[1100px]">
          {!!resumen?.recordatorios.length && (
            <div className="mb-6 md:hidden"><Recordatorios lista={resumen.recordatorios} /></div>
          )}
          <Outlet />
        </div>
      </main>

      <nav className="fixed inset-x-0 bottom-0 z-10 flex border-t border-borde bg-superficie md:hidden" aria-label="Menú">
        {SECCIONES.map((s) => (
          <Enlace key={s.ruta} {...s} compacto contador={s.ruta === "/notificaciones" ? sinLeer : undefined} />
        ))}
      </nav>
    </div>
  );
}
