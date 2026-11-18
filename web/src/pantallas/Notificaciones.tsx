// Notificaciones y alerta de vacantes (#17) — NotificacionesFront.py.
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { BellOff, Inbox } from "lucide-react";
import { api, type Respuesta } from "../api/cliente";
import { Aviso, Boton, Encabezado, EstadoVacio, EsqueletoTarjetas, Mensaje, Tarjeta } from "../componentes/ui";
import { textoDia } from "../lib/fechas";
import { describirAlerta } from "../lib/vacantes";

type Notificacion = {
  Id_notificacion: number; Id_vacante: number; Cargo: string; Empresa: string; Ubicacion: string; Estado: string;
  Leida: number | boolean; Fecha_publicacion: string; Fecha_notificacion: string;
};
type Alerta = { Palabra_clave: string | null; Ubicacion: string | null; Salario_minimo: number | null; Modalidad: string | null; Fecha_creacion: string } | null;

export function Notificaciones() {
  const navegar = useNavigate();
  const cliente = useQueryClient();
  const [mensaje, setMensaje] = useState<Pick<Respuesta, "ok" | "mensaje"> | null>(null);
  const notis = useQuery({ queryKey: ["notificaciones"], queryFn: () => api.get<Notificacion[]>("/notificaciones") });
  const alerta = useQuery({ queryKey: ["alerta"], queryFn: () => api.get<Alerta>("/alerta") });
  const refrescar = () => { notis.refetch(); cliente.invalidateQueries({ queryKey: ["resumen"] }); };

  const lista = notis.data?.ok ? notis.data.datos : [];
  return (
    <>
      <Encabezado
        titulo="Notificaciones"
        accion={lista.some((n) => !n.Leida) && (
          <Boton onClick={async () => { setMensaje(await api.post("/notificaciones/leidas", {})); refrescar(); }}>Marcar todas como leídas</Boton>
        )}
      />
      <div className="flex flex-col gap-3">
        <Mensaje resultado={mensaje} />
        {notis.isLoading ? <EsqueletoTarjetas /> :
          !notis.data?.ok ? <Aviso tipo="error">{notis.data?.mensaje}</Aviso> :
          !lista.length ? (
            <EstadoVacio icono={Inbox} titulo="No tienes notificaciones."
              texto="Cuando se publique una vacante que cumpla tu alerta, aparecerá aquí." />
          ) : lista.map((n) => {
            const cerrada = n.Estado === "Cerrada";
            return (
              <Tarjeta key={n.Id_notificacion} as="article" className={`flex flex-col gap-3 sm:flex-row sm:items-center ${n.Leida ? "" : "border-primario/40"}`}>
                <div className="flex-1">
                  <h3 className="text-base font-semibold">{n.Cargo}</h3>
                  <p className="text-sm">
                    {!n.Leida && <span className="mr-2 rounded-full bg-primario px-2 py-0.5 text-xs font-semibold text-white">Nueva</span>}
                    <strong className="font-medium">{n.Empresa}</strong> · {n.Ubicacion}
                  </p>
                  <p className="text-xs text-texto-sec">Publicada el {textoDia(n.Fecha_publicacion)} · te avisamos el {textoDia(n.Fecha_notificacion)}</p>
                  {cerrada && <Aviso tipo="aviso" className="mt-2">Esta vacante ya fue cerrada y no recibe postulaciones.</Aviso>}
                </div>
                <Boton disabled={cerrada} onClick={async () => {
                  await api.post("/notificaciones/leidas", { id_notificacion: n.Id_notificacion });
                  cliente.invalidateQueries({ queryKey: ["notificaciones"] });
                  navegar(`/vacantes/${n.Id_vacante}`);
                }}>Ver detalle</Boton>
              </Tarjeta>
            );
          })}

        <section className="mt-6 flex flex-col gap-3 border-t border-borde pt-6">
          <h2 className="text-lg font-semibold">Tu alerta</h2>
          {alerta.isLoading ? null : !alerta.data?.ok ? <Aviso tipo="error">{alerta.data?.mensaje}</Aviso> :
            !alerta.data.datos ? (
              <p className="text-sm text-texto-sec">
                No tienes una alerta activa. Créala en <Link to="/vacantes" className="font-medium text-primario">Vacantes</Link> con los filtros que quieras y el botón «Crear alerta con estos filtros».
              </p>
            ) : (
              <Tarjeta className="flex flex-col gap-3 sm:flex-row sm:items-center">
                <div className="flex-1">
                  <p className="text-sm">Te avisamos de vacantes nuevas: <strong className="font-semibold">
                    {describirAlerta(alerta.data.datos.Palabra_clave, alerta.data.datos.Ubicacion, alerta.data.datos.Salario_minimo, alerta.data.datos.Modalidad)}
                  </strong></p>
                  <p className="text-xs text-texto-sec">Activa desde el {textoDia(alerta.data.datos.Fecha_creacion)}</p>
                </div>
                <Boton icono={BellOff} onClick={async () => { setMensaje(await api.delete("/alerta")); alerta.refetch(); }}>Desactivar alerta</Boton>
              </Tarjeta>
            )}
        </section>
      </div>
    </>
  );
}
