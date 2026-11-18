// Carta de presentación de una postulación (#18): adjuntar, descargar o reemplazar.
import { useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Download, Paperclip } from "lucide-react";
import { api, descargar, type Respuesta } from "../api/cliente";
import { textoFecha } from "../lib/fechas";
import { Aviso, Boton, Esqueleto, Mensaje } from "./ui";

type CartaDatos = { Nombre_archivo: string; Tipo: string; Fecha_carga: string } | null;

export function Carta({ idPostulacion }: { idPostulacion: number }) {
  const entrada = useRef<HTMLInputElement>(null);
  const [archivo, setArchivo] = useState<File | null>(null);
  const [mensaje, setMensaje] = useState<Pick<Respuesta, "ok" | "mensaje"> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [guardando, setGuardando] = useState(false);
  const carta = useQuery({
    queryKey: ["carta", idPostulacion],
    queryFn: () => api.get<CartaDatos>(`/postulaciones/${idPostulacion}/carta`),
  });

  const guardar = async () => {
    if (!archivo) return;
    setGuardando(true);
    const r = await api.subir("PUT", `/postulaciones/${idPostulacion}/carta`, archivo);
    setGuardando(false);
    setMensaje(r);
    if (r.ok) { setArchivo(null); if (entrada.current) entrada.current.value = ""; carta.refetch(); }
  };

  if (carta.isLoading) return <Esqueleto className="h-10 w-full" />;
  if (!carta.data?.ok) return <Aviso tipo="error">{carta.data?.mensaje}</Aviso>;
  const datos = carta.data.datos;
  const id = `carta-${idPostulacion}`;
  return (
    <div className="flex flex-col gap-3">
      <Mensaje resultado={mensaje} />
      {datos && (
        <div className="flex flex-wrap items-center gap-3 text-sm">
          <Paperclip className="size-4 text-texto-tenue" aria-hidden />
          <span>Carta adjunta: <strong className="font-semibold">{datos.Nombre_archivo}</strong></span>
          <span className="text-xs text-texto-sec">Cargada el {textoFecha(datos.Fecha_carga).replace(" a las", "")}</span>
          <Boton variante="texto" icono={Download} onClick={async () => setError(await descargar(`/postulaciones/${idPostulacion}/carta/archivo`))}>
            Descargar carta
          </Boton>
        </div>
      )}
      {error && <Aviso tipo="error">{error}</Aviso>}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end">
        <div className="flex flex-1 flex-col gap-1.5">
          <label htmlFor={id} className="text-sm font-medium">
            {(datos ? "Reemplazar la carta" : "Adjuntar carta de presentación") + " (PDF o Word, máx. 2 MB)"}
          </label>
          <input
            ref={entrada} id={id} type="file" accept=".pdf,.docx"
            onChange={(e) => setArchivo(e.target.files?.[0] ?? null)}
            className="text-sm file:mr-3 file:rounded-[var(--radius-control)] file:border file:border-borde file:bg-superficie file:px-3 file:py-2 file:text-sm file:font-medium"
          />
        </div>
        <Boton onClick={guardar} disabled={!archivo} cargando={guardando}>Guardar carta</Boton>
      </div>
    </div>
  );
}
