// Mi perfil: las 5 opciones (CargarCV.mostrar_eleccion_perfil).
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ChevronRight, FileText, FileUp, Contact, PenLine, Wand2, type LucideIcon } from "lucide-react";
import { api } from "../../api/cliente";
import { Encabezado, Esqueleto } from "../../componentes/ui";

const OPCIONES: { ruta: string; titulo: string; descripcion: string; icono: LucideIcon }[] = [
  {
    ruta: "/perfil/linkedin",
    titulo: "Importar desde LinkedIn",
    descripcion: "Sube el PDF de tu perfil (en LinkedIn: Más → Guardar en PDF) y el agente lo lee.",
    icono: Contact,
  },
  {
    ruta: "/perfil/hoja-de-vida",
    titulo: "Subir mi hoja de vida (PDF o Word)",
    descripcion: "Guárdala en tu perfil y, si quieres, el agente extrae tus datos.",
    icono: FileUp,
  },
  { ruta: "/perfil/manual", titulo: "Llenar mi perfil manualmente", descripcion: "Escribe tus datos paso a paso.", icono: PenLine },
  {
    ruta: "/perfil/mejorar",
    titulo: "Mejorar mi hoja de vida",
    descripcion: "El agente compara tu perfil con las vacantes que te interesan y te sugiere mejoras.",
    icono: Wand2,
  },
  {
    ruta: "/perfil/generar-cv",
    titulo: "Generar mi CV",
    descripcion: "El agente redacta tu CV a partir de tu perfil, listo para descargar o para postularte.",
    icono: FileText,
  },
];

export function Eleccion() {
  const hoja = useQuery({
    queryKey: ["hoja-de-vida"],
    queryFn: async () => (await api.get<{ nombre: string; tipo: string } | null>("/perfil/hoja-de-vida")).datos,
  });

  return (
    <>
      <Encabezado
        titulo="¿Cómo quieres empezar tu perfil?"
        descripcion="El agente construirá tu perfil a partir de lo que elijas. Podrás editarlo todo después."
      />
      <ul className="grid gap-3 sm:grid-cols-2">
        {OPCIONES.map(({ ruta, titulo, descripcion, icono: Icono }) => (
          <li key={ruta}>
            <Link
              to={ruta}
              className="group flex h-full items-start gap-4 rounded-[var(--radius-tarjeta)] border border-borde bg-superficie p-5 shadow-suave transition-colors hover:border-primario/40 hover:bg-primario-suave/40"
            >
              <span className="grid size-10 shrink-0 place-items-center rounded-[var(--radius-control)] bg-primario-suave text-primario">
                <Icono className="size-5" aria-hidden />
              </span>
              <span className="flex min-w-0 flex-1 flex-col gap-1">
                <span className="text-base font-medium text-texto">{titulo}</span>
                <span className="text-sm text-texto-sec">{descripcion}</span>
                {ruta === "/perfil/hoja-de-vida" &&
                  (hoja.isLoading ? (
                    <Esqueleto className="mt-1 h-3 w-40" />
                  ) : (
                    hoja.data && <span className="mt-1 text-xs font-medium text-acento-fuerte">Hoja de vida guardada: {hoja.data.nombre}</span>
                  ))}
              </span>
              <ChevronRight className="mt-2 size-5 shrink-0 text-texto-tenue transition-transform group-hover:translate-x-0.5 group-hover:text-primario" aria-hidden />
            </Link>
          </li>
        ))}
      </ul>
    </>
  );
}
