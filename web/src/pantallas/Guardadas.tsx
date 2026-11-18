// Vacantes guardadas (#16) — GuardadasFront.py.
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Bookmark } from "lucide-react";
import { api, type Respuesta } from "../api/cliente";
import { Aviso, Boton, Encabezado, EstadoVacio, EsqueletoTarjetas, Mensaje, Tarjeta } from "../componentes/ui";
import { textoDia } from "../lib/fechas";

type Guardada = { Id_vacante: number; Cargo: string; Empresa: string; Ubicacion: string; Estado: string; Fecha_guardada: string };

export function Guardadas() {
  const navegar = useNavigate();
  const [mensaje, setMensaje] = useState<Pick<Respuesta, "ok" | "mensaje"> | null>(null);
  const guardadas = useQuery({ queryKey: ["guardadas"], queryFn: () => api.get<Guardada[]>("/guardadas") });

  const quitar = async (id: number) => {
    setMensaje(await api.delete(`/vacantes/${id}/guardada`));
    guardadas.refetch();
  };

  return (
    <>
      <Encabezado titulo="Vacantes guardadas" />
      <div className="flex flex-col gap-3">
        <Mensaje resultado={mensaje} />
        {guardadas.isLoading ? <EsqueletoTarjetas /> :
          !guardadas.data?.ok ? <Aviso tipo="error">{guardadas.data?.mensaje}</Aviso> :
          !guardadas.data.datos.length ? (
            <EstadoVacio
              icono={Bookmark}
              titulo="Todavía no has guardado vacantes."
              texto={<>Usa <strong>Guardar vacante</strong> en el detalle de cualquier vacante para revisarla después.</>}
              accion={<Boton variante="primario" onClick={() => navegar("/vacantes")}>Ver vacantes</Boton>}
            />
          ) : guardadas.data.datos.map((v) => (
            <Tarjeta key={v.Id_vacante} as="article" className="flex flex-col gap-3 sm:flex-row sm:items-center">
              <div className="flex-1">
                <h3 className="text-base font-semibold">{v.Cargo}</h3>
                <p className="text-sm"><strong className="font-medium">{v.Empresa}</strong> · {v.Ubicacion}</p>
                <p className="text-xs text-texto-sec">La guardaste el {textoDia(v.Fecha_guardada)}</p>
                {v.Estado === "Cerrada" && <Aviso tipo="aviso" className="mt-2">Esta vacante ya fue cerrada y no recibe postulaciones.</Aviso>}
              </div>
              <div className="flex gap-2">
                <Boton disabled={v.Estado === "Cerrada"} onClick={() => navegar(`/vacantes/${v.Id_vacante}`)}>Ver detalle</Boton>
                <Boton variante="texto" onClick={() => quitar(v.Id_vacante)}>Quitar</Boton>
              </div>
            </Tarjeta>
          ))}
      </div>
    </>
  );
}
