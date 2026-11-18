// Mis postulaciones — PostulacionesFront.py: panel por etapa (#23), estado (#21, #22), entrevista (#28),
// carta (#18), formulario (#19), hoja de vida asociada (#20) y prioridades (#29).
import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { CalendarClock, ChevronDown, ClipboardList, Copy, ListOrdered, Sparkles } from "lucide-react";
import { api, type Respuesta } from "../api/cliente";
import { Carta } from "../componentes/Carta";
import {
  AgenteTrabajando, AreaTexto, Aviso, BloqueDudoso, Boton, Campo, Casilla, Encabezado, EstadoVacio, EsqueletoTarjetas,
  EtiquetaAgente, EtiquetaEtapa, colorDeEtapa, etiquetaEstado, Mensaje, Selector, Tarjeta,
} from "../componentes/ui";
import { textoDia, textoFecha } from "../lib/fechas";
import { useMemoria } from "../lib/memoria";

const ESTADOS = ["Postulado", "En revision", "Entrevista", "Oferta", "Rechazado", "Retirado"];

type Postulacion = {
  Id_postulacion: number; Fecha_postulacion: string; Estado: string; Fecha_actualizacion: string; Cv: string | null;
  Fecha_entrevista: string | null; Estado_para_deshacer: string | null; Cargo: string; Empresa: string; Ubicacion: string;
  Descripcion: string; Requisitos: string; Fecha_publicacion: string; Estado_vacante: string;
};
type Resultado = Pick<Respuesta, "ok" | "mensaje"> | null;

function Desplegable({ titulo, children, abierto: inicial = false }: { titulo: string; children: ReactNode; abierto?: boolean }) {
  const [abierto, setAbierto] = useState(inicial);
  return (
    <div className="border-t border-borde">
      <button type="button" aria-expanded={abierto} onClick={() => setAbierto(!abierto)}
        className="flex w-full items-center gap-2 py-3 text-sm font-medium text-texto cursor-pointer">
        <span className="flex-1 text-left">{titulo}</span>
        <ChevronDown className={`size-4 text-texto-tenue transition-transform ${abierto ? "rotate-180" : ""}`} aria-hidden />
      </button>
      {abierto && <div className="pb-4">{children}</div>}
    </div>
  );
}

// ---------------------------------------------------------------- Estado (#22)
function SeccionEstado({ p, alCambiar }: { p: Postulacion; alCambiar: (texto: string) => void }) {
  const [nuevo, setNuevo] = useState(p.Estado);
  const [mensaje, setMensaje] = useState<Resultado>(null);
  useEffect(() => setNuevo(p.Estado), [p.Estado]); // se reinicia solo cuando cambia el estado guardado
  return (
    <div className="flex flex-col gap-3">
      {mensaje?.mensaje && <Aviso tipo={mensaje.ok ? "exito" : "aviso"}>{mensaje.mensaje}</Aviso>}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end">
        <div className="flex-1">
          <Selector etiqueta="Nueva etapa" value={nuevo} onChange={(e) => setNuevo(e.target.value)}
            opciones={ESTADOS.map((e) => ({ valor: e, texto: etiquetaEstado(e) }))} />
        </div>
        <Boton onClick={async () => {
          const r = await api.put(`/postulaciones/${p.Id_postulacion}/estado`, { estado: nuevo });
          if (r.ok) alCambiar(`Estado actualizado a «${etiquetaEstado(nuevo)}». «${p.Cargo}» ahora aparece en esa etapa.`);
          else setMensaje(r);
        }}>Guardar estado</Boton>
      </div>
      {p.Estado_para_deshacer && (
        <div>
          <Boton variante="texto" onClick={async () => {
            const r = await api.post(`/postulaciones/${p.Id_postulacion}/deshacer`);
            if (r.ok) alCambiar(`${r.mensaje} «${p.Cargo}» volvió a «${etiquetaEstado(p.Estado_para_deshacer!)}».`);
            else setMensaje(r);
          }}>
            Deshacer último cambio (volver a «{etiquetaEstado(p.Estado_para_deshacer)}»)
          </Boton>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------- Entrevista (#28)
function SeccionEntrevista({ p, alGuardar }: { p: Postulacion; alGuardar: () => void }) {
  const [dia, setDia] = useState("");
  const [hora, setHora] = useState("");
  const [mensaje, setMensaje] = useState<Resultado>(null);
  const hoy = new Date().toISOString().slice(0, 10);
  return (
    <div className="flex flex-col gap-3">
      <Mensaje resultado={mensaje} />
      {p.Fecha_entrevista && <p className="text-sm">Entrevista informada: <strong>{textoFecha(p.Fecha_entrevista)}</strong></p>}
      <form className="flex flex-col gap-3 sm:flex-row sm:items-end" onSubmit={async (e) => {
        e.preventDefault();
        if (!dia || !hora) return setMensaje({ ok: false, mensaje: "Elige la fecha y la hora de la entrevista." });
        const r = await api.put(`/postulaciones/${p.Id_postulacion}/entrevista`, { fecha: `${dia}T${hora}` });
        setMensaje(r);
        if (r.ok) { setDia(""); setHora(""); alGuardar(); }
      }}>
        <Campo etiqueta="Fecha de la entrevista" type="date" min={hoy} value={dia} onChange={(e) => setDia(e.target.value)} />
        <Campo etiqueta="Hora" type="time" step={900} value={hora} onChange={(e) => setHora(e.target.value)} />
        <Boton type="submit">Guardar entrevista</Boton>
      </form>
      {p.Fecha_entrevista && (
        <div><Boton variante="texto" onClick={async () => { setMensaje(await api.delete(`/postulaciones/${p.Id_postulacion}/entrevista`)); alGuardar(); }}>
          Quitar entrevista
        </Boton></div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------- Formulario (#19)
type CampoForm = { pregunta: string; respuesta: string; estado: "seguro" | "dudoso" | "manual" | "personal"; nota: string | null };

function SeccionFormulario({ id }: { id: number }) {
  const [propuesta, setPropuesta] = useMemoria<{ campos: (CampoForm & { texto: string; rechazada: boolean })[] } | null>(`formulario-${id}`, null);
  const [texto, setTexto] = useState("");
  const [archivo, setArchivo] = useState<File | null>(null);
  const [mensaje, setMensaje] = useState<Resultado>(null);
  const [trabajando, setTrabajando] = useState(false);
  const entrada = useRef<HTMLInputElement>(null);
  const guardadas = useQuery({
    queryKey: ["respuestas", id],
    queryFn: () => api.get<{ Pregunta: string; Respuesta: string }[]>(`/postulaciones/${id}/formulario`),
  });

  const procesar = async () => {
    setMensaje(null);
    let contenido = texto;
    if (archivo && !texto.trim()) {
      const leido = await api.subir<string>("POST", `/postulaciones/${id}/formulario/leer`, archivo);
      if (!leido.ok) return setMensaje(leido);
      contenido = leido.datos;
    }
    setTrabajando(true);
    const r = await api.post<{ campos: CampoForm[]; errores: string[] }>(`/postulaciones/${id}/formulario/generar`, { texto: contenido });
    setTrabajando(false);
    if (!r.ok) setMensaje(r);
    else if (r.datos.errores.length) setMensaje({ ok: false, mensaje: r.datos.errores.join(" ") });
    else setPropuesta({ campos: r.datos.campos.map((c) => ({ ...c, texto: c.respuesta, rechazada: false })) });
  };

  const confirmar = async () => {
    const aceptadas = propuesta!.campos.filter((c) => !c.rechazada).map((c) => [c.pregunta, c.texto.trim()] as [string, string]);
    const vacias = aceptadas.filter(([, t]) => !t).map(([p]) => p);
    if (vacias.length) return setMensaje({ ok: false, mensaje: `Completa o rechaza estas preguntas antes de confirmar: ${vacias.join("; ")}` });
    if (!aceptadas.length) return setMensaje({ ok: false, mensaje: "Rechazaste todas las respuestas; no hay nada que guardar." });
    const r = await api.put(`/postulaciones/${id}/formulario`, { respuestas: aceptadas });
    setMensaje(r);
    if (r.ok) { setPropuesta(null); guardadas.refetch(); }
  };

  const editar = (i: number, cambio: Partial<{ texto: string; rechazada: boolean }>) =>
    setPropuesta((pr) => (pr ? { campos: pr.campos.map((c, j) => (j === i ? { ...c, ...cambio } : c)) } : pr));

  return (
    <div className="flex flex-col gap-4">
      <Mensaje resultado={mensaje} />
      {guardadas.data && !guardadas.data.ok && <Aviso tipo="error">{guardadas.data.mensaje}</Aviso>}
      {guardadas.data?.ok && guardadas.data.datos.length > 0 && (
        <div className="flex flex-col gap-2">
          <p className="text-sm"><strong>Respuestas confirmadas</strong> — cópialas en el portal de la empresa. Progent no envía el formulario.</p>
          {guardadas.data.datos.map((r, i) => (
            <div key={i} className="rounded-[var(--radius-control)] bg-fondo p-3 text-sm">
              <p className="italic text-texto-sec">{r.Pregunta}</p>
              <div className="mt-1 flex items-start gap-2">
                <p className="flex-1 whitespace-pre-line">{r.Respuesta}</p>
                <button type="button" className="text-texto-tenue hover:text-primario cursor-pointer" aria-label="Copiar respuesta"
                  onClick={() => navigator.clipboard?.writeText(r.Respuesta)}><Copy className="size-4" aria-hidden /></button>
              </div>
            </div>
          ))}
        </div>
      )}
      {!propuesta ? (
        <div className="flex flex-col gap-3">
          <AreaTexto etiqueta="Pega aquí el formulario de la vacante" value={texto} onChange={(e) => setTexto(e.target.value)} />
          <div className="flex flex-col gap-1.5">
            <label htmlFor={`form-archivo-${id}`} className="text-sm font-medium">…o súbelo (PDF o Word)</label>
            <input ref={entrada} id={`form-archivo-${id}`} type="file" accept=".pdf,.docx" onChange={(e) => setArchivo(e.target.files?.[0] ?? null)}
              className="text-sm file:mr-3 file:rounded-[var(--radius-control)] file:border file:border-borde file:bg-superficie file:px-3 file:py-2 file:text-sm file:font-medium" />
          </div>
          <div><Boton icono={Sparkles} onClick={procesar} disabled={trabajando}>Llenar con el agente</Boton></div>
          {trabajando && <AgenteTrabajando texto="El agente está leyendo el formulario..." />}
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between gap-2">
            <p className="text-sm text-texto-sec">Respuestas propuestas por el agente. Edítalas, rechaza las que no sirvan y confirma.</p>
            <EtiquetaAgente />
          </div>
          {propuesta.campos.map((c, i) => (
            <div key={i} className={`flex flex-col gap-2 ${c.rechazada ? "opacity-60" : ""}`}>
              <p className="text-sm font-semibold">{i + 1}. {c.pregunta}</p>
              {c.estado === "personal" && <p className="text-xs text-texto-sec">Dato tomado de tu perfil. No se envió al agente.</p>}
              {c.estado === "dudoso" && <BloqueDudoso>No estoy seguro de esta respuesta: {c.nota || "revísala"}. Revísala antes de confirmar.</BloqueDudoso>}
              {c.estado === "manual" && <Aviso tipo="error">No sé cómo llenar este campo: {c.nota} Complétalo tú.</Aviso>}
              <AreaTexto etiqueta={`Respuesta ${i + 1}`} rows={2} value={c.texto} onChange={(e) => editar(i, { texto: e.target.value })} />
              <Casilla etiqueta="Rechazar esta respuesta" checked={c.rechazada} onChange={(e) => editar(i, { rechazada: e.target.checked })} />
            </div>
          ))}
          <div className="flex flex-col gap-2 sm:flex-row">
            <Boton variante="primario" onClick={confirmar}>Confirmar respuestas</Boton>
            <Boton onClick={() => setPropuesta(null)}>Descartar propuesta</Boton>
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------- Prioridades (#29)
type Proceso = { Id_postulacion: number; Cargo: string; Empresa: string; Estado: string };
type Prioridades = { procesos: Proceso[]; orden: { id_proceso: number; motivo: string; seguro: boolean }[]; resumen: string; errores: string[] };

function SeccionPrioridades({ postulaciones }: { postulaciones: Postulacion[] }) {
  // Si cambian las postulaciones (etapa o entrevista), el orden anterior ya no vale.
  const firma = useMemo(() => JSON.stringify(postulaciones.map((p) => [p.Id_postulacion, p.Estado, p.Fecha_entrevista])), [postulaciones]);
  const [guardado, setGuardado] = useMemoria<{ firma: string; respuesta: Respuesta<Prioridades> } | null>("prioridades", null);
  const [trabajando, setTrabajando] = useState(false);
  const vigente = guardado && guardado.firma === firma ? guardado : null;
  useEffect(() => { if (guardado && guardado.firma !== firma) setGuardado(null); }, [firma]); // eslint-disable-line react-hooks/exhaustive-deps
  const d = vigente?.respuesta.datos;

  return (
    <Tarjeta className="p-0">
      <Desplegable titulo="¿Qué proceso atiendo primero?" abierto={!!vigente}>
        <div className="flex flex-col gap-4 px-5">
          <p className="text-sm text-texto-sec">El agente revisa tus procesos activos y te sugiere un orden para atenderlos.</p>
          <div><Boton icono={ListOrdered} disabled={trabajando} onClick={async () => {
            setTrabajando(true);
            const r = await api.post<Prioridades>("/prioridades");
            setTrabajando(false);
            setGuardado({ firma, respuesta: r });
          }}>Sugerir prioridades</Boton></div>
          {trabajando && <AgenteTrabajando texto="El agente está revisando tus procesos..." />}
          {vigente && !trabajando && (
            !vigente.respuesta.ok ? <Aviso tipo="error">{vigente.respuesta.mensaje}</Aviso> :
            !d!.procesos.length ? (
              <Aviso tipo="info">No tienes procesos activos: tus postulaciones están rechazadas o retiradas, así que no hay nada que priorizar.</Aviso>
            ) : d!.procesos.length === 1 ? (
              <Aviso tipo="info">Solo tienes un proceso activo: «{d!.procesos[0].Cargo}». No hay nada que ordenar; atiéndelo a él.</Aviso>
            ) : d!.errores.length ? <Aviso tipo="error">{d!.errores.join(" ")}</Aviso> : (
              <div className="flex flex-col gap-3">
                <div className="flex items-start justify-between gap-2">
                  {d!.resumen ? <p className="text-sm"><strong>Por qué este orden:</strong> {d!.resumen}</p> : <span />}
                  <EtiquetaAgente />
                </div>
                <ol className="flex flex-col gap-3">
                  {d!.orden.map((item, i) => {
                    const p = d!.procesos.find((x) => x.Id_postulacion === item.id_proceso);
                    if (!p) return null;
                    return (
                      <li key={item.id_proceso} className="flex gap-3">
                        <span className="grid size-7 shrink-0 place-items-center rounded-full bg-primario-suave text-sm font-semibold text-primario">{i + 1}</span>
                        <div className="flex flex-1 flex-col gap-1">
                          <p className="text-sm"><strong>{p.Cargo}</strong> — {p.Empresa} · {etiquetaEstado(p.Estado)}</p>
                          {item.seguro ? <p className="text-xs text-texto-sec">{item.motivo}</p>
                            : <BloqueDudoso>Sugerencia (no estoy seguro de este lugar): {item.motivo}</BloqueDudoso>}
                        </div>
                      </li>
                    );
                  })}
                </ol>
                <p className="text-xs text-texto-tenue">Es solo una sugerencia del agente: no cambia nada en tus postulaciones.</p>
              </div>
            )
          )}
        </div>
      </Desplegable>
    </Tarjeta>
  );
}

// ---------------------------------------------------------------- Tarjeta y panel
function TarjetaPostulacion({ p, alCambiarEstado, refrescar }: { p: Postulacion; alCambiarEstado: (t: string) => void; refrescar: () => void }) {
  const ahora = new Date();
  const entrevista = p.Fecha_entrevista ? new Date(p.Fecha_entrevista) : null;
  return (
    <Tarjeta as="article" className="flex flex-col gap-2 pb-1">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h4 className="text-base font-semibold">{p.Cargo}</h4>
          <p className="text-sm"><strong className="font-medium">{p.Empresa}</strong> · {p.Ubicacion}</p>
        </div>
        <EtiquetaEtapa etapa={p.Estado} />
      </div>
      <p className="text-sm">Estado: <strong>{etiquetaEstado(p.Estado)}</strong></p>
      <p className="text-xs text-texto-sec">Te postulaste el {textoDia(p.Fecha_postulacion)}</p>
      <p className="text-xs text-texto-sec">{p.Cv ? `Hoja de vida: ${p.Cv}` : "Sin hoja de vida asociada"}</p>
      {entrevista && (entrevista >= ahora ? (
        <p className="flex items-center gap-1.5 text-xs font-medium text-aviso-fuerte"><CalendarClock className="size-3.5" aria-hidden />Próxima entrevista: {textoFecha(p.Fecha_entrevista!)}</p>
      ) : (
        <Aviso tipo="aviso">La entrevista del {textoFecha(p.Fecha_entrevista!)} ya pasó. Actualiza el estado o informa una nueva fecha.</Aviso>
      ))}
      <div className="mt-2">
        <Desplegable titulo="Ver información de la vacante">
          <div className="flex flex-col gap-2 text-sm">
            <p>Estado actual: <strong>{etiquetaEstado(p.Estado)}</strong> · última actualización el {textoFecha(p.Fecha_actualizacion)}</p>
            {p.Estado_vacante === "Cerrada" && <Aviso tipo="aviso">Esta vacante ya fue cerrada y no recibe más postulaciones.</Aviso>}
            <p className="font-medium">Descripción</p><p className="text-texto-sec">{p.Descripcion}</p>
            <p className="font-medium">Requisitos</p><p className="text-texto-sec">{p.Requisitos}</p>
            <p className="text-xs text-texto-tenue">Publicada el {textoDia(p.Fecha_publicacion)}</p>
          </div>
        </Desplegable>
        <Desplegable titulo="Actualizar estado"><SeccionEstado p={p} alCambiar={alCambiarEstado} /></Desplegable>
        <Desplegable titulo="Informar entrevista"><SeccionEntrevista p={p} alGuardar={refrescar} /></Desplegable>
        <Desplegable titulo="Carta de presentación"><Carta idPostulacion={p.Id_postulacion} /></Desplegable>
        <Desplegable titulo="Formulario de la vacante"><SeccionFormulario id={p.Id_postulacion} /></Desplegable>
      </div>
    </Tarjeta>
  );
}

export function Postulaciones() {
  const navegar = useNavigate();
  const cliente = useQueryClient();
  const [aviso, setAviso] = useState<string | null>(null);
  const datos = useQuery({ queryKey: ["postulaciones"], queryFn: () => api.get<Postulacion[]>("/postulaciones") });
  const refrescar = () => { datos.refetch(); cliente.invalidateQueries({ queryKey: ["resumen"] }); };

  if (datos.isLoading) return <><Encabezado titulo="Mis postulaciones" /><EsqueletoTarjetas /></>;
  if (!datos.data?.ok) return <><Encabezado titulo="Mis postulaciones" /><Aviso tipo="error">{datos.data?.mensaje}</Aviso></>;
  const lista = datos.data.datos;

  return (
    <>
      <Encabezado titulo="Mis postulaciones" />
      {!lista.length ? (
        <EstadoVacio icono={ClipboardList} titulo="Todavía no te has postulado a ninguna vacante."
          accion={<Boton variante="primario" onClick={() => navegar("/vacantes")}>Ver vacantes</Boton>} />
      ) : (
        <div className="flex flex-col gap-8">
          {/* El aviso va arriba del panel: la tarjeta cambia de grupo al cambiar el estado. */}
          {aviso && <Aviso tipo="exito">{aviso}</Aviso>}
          <SeccionPrioridades postulaciones={lista} />
          {ESTADOS.map((etapa) => {
            const grupo = lista.filter((p) => p.Estado === etapa);
            return (
              <section key={etapa} className="flex flex-col gap-3" aria-labelledby={`etapa-${etapa}`}>
                <h3 id={`etapa-${etapa}`} className="flex items-center gap-2 text-base font-semibold text-texto">
                  <span className="size-2.5 rounded-full" style={{ background: colorDeEtapa(etapa) }} aria-hidden />
                  {etiquetaEstado(etapa)} ({grupo.length})
                </h3>
                {!grupo.length ? <p className="text-sm text-texto-tenue">Sin postulaciones en esta etapa.</p> :
                  grupo.map((p) => (
                    <TarjetaPostulacion key={p.Id_postulacion} p={p} refrescar={refrescar}
                      alCambiarEstado={(t) => { setAviso(t); refrescar(); window.scrollTo({ top: 0, behavior: "smooth" }); }} />
                  ))}
              </section>
            );
          })}
        </div>
      )}
    </>
  );
}
