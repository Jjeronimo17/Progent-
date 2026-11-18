// Recomendaciones (#11), automáticas (#25) y confirmar la postulación recomendada (#27) — RecomendacionesFront.py.
// Las recomendaciones viven en el cliente (decisión 7): solo se guarda lo que el usuario responde.
import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ChevronDown, RefreshCw, Sparkles } from "lucide-react";
import { api, type Respuesta } from "../api/cliente";
import {
  AgenteTrabajando, Aviso, BloqueDudoso, Boton, Campo, Encabezado, EsqueletoTarjetas, EtiquetaAgente, Selector, Tarjeta,
} from "../componentes/ui";
import { useMemoria } from "../lib/memoria";
import type { Vacante } from "../lib/vacantes";

type Rec = { vacante: Vacante; motivo: string; seguro: boolean };
type Generado = { faltantes: string[]; sin_candidatas: boolean; recomendaciones: Rec[]; errores: string[]; base: string; candidatas: number[] };
type Estado = { respuesta: Respuesta<Generado | null>; recomendaciones: Rec[]; total: number; base: string | null; candidatas: number[] } | null;
type Resultado = Pick<Respuesta, "ok" | "mensaje"> | null;
const MODALIDADES = ["Cualquiera", "Hibrido", "Presencial", "Virtual"];

function Criterios({ alGuardar }: { alGuardar: (r: Resultado) => void }) {
  const criterios = useQuery({
    queryKey: ["criterios"],
    queryFn: () => api.get<{ Cargo_deseado: string | null; Modalidad: string | null; Ciudad: string | null } | null>("/recomendaciones/criterios"),
  });
  const datos = criterios.data?.ok ? criterios.data.datos : null;
  const [abierto, setAbierto] = useState<boolean | null>(null);
  const [form, setForm] = useState<{ cargo: string; modalidad: string; ciudad: string } | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    if (criterios.data && form === null)
      setForm({ cargo: datos?.Cargo_deseado ?? "", modalidad: datos?.Modalidad ?? "Cualquiera", ciudad: datos?.Ciudad ?? "" });
  }, [criterios.data]); // eslint-disable-line react-hooks/exhaustive-deps
  const visible = abierto ?? !datos;

  return (
    <Tarjeta className="p-0">
      <button type="button" aria-expanded={visible} onClick={() => setAbierto(!visible)}
        className="flex w-full items-center gap-2 px-5 h-12 text-sm font-medium text-texto cursor-pointer">
        <span className="flex-1 text-left">Mis criterios de búsqueda</span>
        <ChevronDown className={`size-4 text-texto-tenue transition-transform ${visible ? "rotate-180" : ""}`} aria-hidden />
      </button>
      {visible && form && (
        <form
          className="grid gap-4 border-t border-borde p-5 sm:grid-cols-3"
          onSubmit={async (e) => {
            e.preventDefault();
            const r = await api.put("/recomendaciones/criterios", {
              cargo_deseado: form.cargo.trim() || null,
              modalidad: form.modalidad === "Cualquiera" ? null : form.modalidad,
              ciudad: form.ciudad.trim() || null,
            });
            if (r.ok) { setError(null); criterios.refetch(); alGuardar(r); } else setError(r.mensaje);
          }}
        >
          {criterios.data && !criterios.data.ok && <div className="sm:col-span-3"><Aviso tipo="error">{criterios.data.mensaje}</Aviso></div>}
          <Campo etiqueta="Cargo que buscas" maxLength={150} placeholder="Ej.: Desarrollador backend" value={form.cargo} onChange={(e) => setForm({ ...form, cargo: e.target.value })} />
          <Selector etiqueta="Modalidad" opciones={MODALIDADES} value={form.modalidad} onChange={(e) => setForm({ ...form, modalidad: e.target.value })} />
          <Campo etiqueta="Ciudad" maxLength={100} value={form.ciudad} onChange={(e) => setForm({ ...form, ciudad: e.target.value })}
            ayuda="Solo se usa para filtrar vacantes (también se incluyen las remotas). No se envía al agente." />
          <div className="flex flex-col gap-2 sm:col-span-3">
            {error && <Aviso tipo="error">{error}</Aviso>}
            <div><Boton type="submit">Guardar criterios</Boton></div>
          </div>
        </form>
      )}
    </Tarjeta>
  );
}

function Confirmacion({ rec, onConfirmar, onRechazar, onCancelar }: { rec: Rec; onConfirmar: () => void; onRechazar: () => void; onCancelar: () => void }) {
  const navegar = useNavigate();
  const hoja = useQuery({ queryKey: ["hoja-de-vida"], queryFn: () => api.get<{ nombre: string } | null>("/perfil/hoja-de-vida") });
  if (hoja.isLoading) return null;
  if (!hoja.data?.ok) return <Aviso tipo="error">{hoja.data?.mensaje}</Aviso>;
  const cv = hoja.data.datos;
  return (
    <div className="flex flex-col gap-3 rounded-[var(--radius-control)] border border-primario/30 bg-primario-suave/50 p-4" role="group" aria-label="Confirmar postulación">
      <p className="text-sm font-semibold">¿Confirmas que quieres postularte a «{rec.vacante.Cargo}» en {rec.vacante.Empresa}?</p>
      {cv ? (
        <p className="text-xs text-texto-sec">
          Se registrará en tu panel de seguimiento con tu hoja de vida <strong>{cv.nombre}</strong>. Progent no envía la postulación al portal de la empresa.
        </p>
      ) : (
        <Aviso tipo="aviso">Para postularte necesitas tu hoja de vida. Cárgala en el detalle de la vacante y postúlate desde ahí.</Aviso>
      )}
      <div className="flex flex-col gap-2 sm:flex-row">
        {cv ? <Boton variante="primario" onClick={onConfirmar}>Confirmar postulación</Boton>
          : <Boton variante="primario" onClick={() => navegar(`/vacantes/${rec.vacante.Id_vacante}`)}>Ver detalle para cargarla</Boton>}
        <Boton onClick={onRechazar}>Rechazar</Boton>
        <Boton variante="texto" onClick={onCancelar}>Cancelar</Boton>
      </div>
    </div>
  );
}

function TarjetaRec({ rec, confirmando, acciones }: {
  rec: Rec; confirmando: boolean;
  acciones: { interesa: () => void; guardar: () => void; postular: () => void; descartar: () => void; confirmar: () => void; rechazar: () => void; cancelar: () => void };
}) {
  const [abierta, setAbierta] = useState(false);
  const v = rec.vacante;
  return (
    <Tarjeta as="article" className="flex flex-col gap-3">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h3 className="text-base font-semibold">{v.Cargo}</h3>
          <p className="text-sm"><strong className="font-medium">{v.Empresa}</strong> · {v.Ubicacion}</p>
        </div>
        <EtiquetaAgente texto={rec.seguro ? "Sugerencia del agente" : "Menor relevancia"} />
      </div>
      {rec.seguro ? (
        <>
          <p className="text-sm"><strong>Por qué te la recomiendo:</strong> {rec.motivo}</p>
          <p className="text-xs text-texto-tenue">Sugerencia del agente: todavía no te has postulado.</p>
        </>
      ) : (
        <BloqueDudoso>
          No estoy seguro de que esta vacante encaje contigo. Te la recomiendo porque: {rec.motivo} Es solo una sugerencia: no he hecho nada en tu nombre ni te he postulado.
        </BloqueDudoso>
      )}
      <button type="button" aria-expanded={abierta} onClick={() => setAbierta(!abierta)} className="flex items-center gap-1 self-start text-sm text-primario cursor-pointer">
        Ver descripción y requisitos <ChevronDown className={`size-4 transition-transform ${abierta ? "rotate-180" : ""}`} aria-hidden />
      </button>
      {abierta && (
        <div className="flex flex-col gap-1 border-t border-borde pt-3 text-sm">
          <p className="font-medium">Descripción</p><p className="text-texto-sec">{v.Descripcion}</p>
          <p className="font-medium">Requisitos</p><p className="text-texto-sec">{v.Requisitos}</p>
        </div>
      )}
      <div className="grid grid-cols-2 gap-2 sm:flex">
        <Boton variante="primario" onClick={acciones.interesa}>Me interesa</Boton>
        <Boton onClick={acciones.guardar}>Guardar</Boton>
        <Boton onClick={acciones.postular}>Postularme</Boton>
        <Boton variante="texto" onClick={acciones.descartar}>Descartar</Boton>
      </div>
      {confirmando && <Confirmacion rec={rec} onConfirmar={acciones.confirmar} onRechazar={acciones.rechazar} onCancelar={acciones.cancelar} />}
    </Tarjeta>
  );
}

export function Recomendaciones() {
  const cliente = useQueryClient();
  const [estado, setEstado, leerEstado] = useMemoria<Estado>("recomendaciones", null);
  const [confirmando, setConfirmando] = useMemoria<number | null>("confirmando-postulacion", null);
  const [mensaje, setMensaje] = useState<Resultado>(null);
  const [trabajando, setTrabajando] = useState(false);
  const enCurso = useRef(false);
  const interes = useQuery({ queryKey: ["de-interes"], queryFn: () => api.get<(Vacante & { Estado: string })[]>("/recomendaciones/interes") });

  /** La regla de RecomendacionesFront.actualizar_recomendaciones (#25). */
  const actualizar = async (forzar: boolean) => {
    if (enCurso.current) return;
    enCurso.current = true;
    try {
      const pre = await api.get<{ base: string; candidatas: number[]; faltantes: string[] }>("/recomendaciones/estado");
      if (!pre.ok) {
        setEstado({ respuesta: { ok: false, mensaje: pre.mensaje, datos: null }, recomendaciones: [], total: 0, base: null, candidatas: [] });
        return;
      }
      const candidatas = new Set(pre.datos.candidatas);
      const anterior = leerEstado();
      if (!forzar && anterior && anterior.base === pre.datos.base && pre.datos.candidatas.every((id) => anterior.candidatas.includes(id))) {
        // Solo salieron candidatas (decididas, guardadas o postuladas): se quitan sin llamar al agente.
        setEstado({ ...anterior, recomendaciones: anterior.recomendaciones.filter((r) => candidatas.has(r.vacante.Id_vacante)) });
        return;
      }
      setTrabajando(true);
      const r = await api.post<Generado>("/recomendaciones/generar");
      setTrabajando(false);
      const recs = r.ok ? r.datos.recomendaciones : [];
      setEstado({
        respuesta: r, recomendaciones: recs, total: recs.length,
        base: r.ok ? r.datos.base : pre.datos.base, candidatas: r.ok ? r.datos.candidatas : pre.datos.candidatas,
      });
    } finally {
      enCurso.current = false;
    }
  };

  useEffect(() => { actualizar(false); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const quitar = (id: number) => setEstado((e) => (e ? { ...e, recomendaciones: e.recomendaciones.filter((r) => r.vacante.Id_vacante !== id) } : e));
  const despues = (r: Resultado, id: number, exito?: string) => {
    setMensaje(r?.ok && exito ? { ok: true, mensaje: exito } : r);
    if (r?.ok) { quitar(id); setConfirmando(null); }
    interes.refetch();
    cliente.invalidateQueries({ queryKey: ["guardadas"] });
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const datos = estado?.respuesta.datos;
  const ordenadas = [...(estado?.recomendaciones ?? [])].sort((a, b) => Number(!a.seguro) - Number(!b.seguro));
  return (
    <>
      <Encabezado
        titulo="Vacantes recomendadas"
        descripcion="El agente revisa tu perfil y tus criterios y te sugiere vacantes sin que tengas que buscarlas. Se actualizan solas cuando cambias tu perfil o se publican vacantes nuevas."
        accion={<Boton icono={RefreshCw} onClick={() => actualizar(true)} disabled={trabajando}>Actualizar recomendaciones</Boton>}
      />
      <div className="flex flex-col gap-5">
        {mensaje?.mensaje && <Aviso tipo={mensaje.ok ? "exito" : "aviso"}>{mensaje.mensaje.replace(/\*\*/g, "")}</Aviso>}
        <Criterios alGuardar={(r) => { setMensaje(r); setEstado(null); actualizar(false); }} />

        {trabajando ? <AgenteTrabajando texto="El agente está actualizando tus recomendaciones..." /> :
          !estado ? <EsqueletoTarjetas n={2} /> :
          !estado.respuesta.ok ? <Aviso tipo="error">{estado.respuesta.mensaje}</Aviso> :
          datos!.faltantes.length ? (
            <Aviso tipo="aviso">
              {`Para recomendarte vacantes necesito que completes tu perfil. Te falta:\n${datos!.faltantes.map((f) => `- ${f}`).join("\n")}\n\n`}
              Complétalo en <Link to="/perfil/manual" className="font-medium underline">Mi perfil → Llenar mi perfil manualmente</Link>.
            </Aviso>
          ) : datos!.sin_candidatas ? (
            <Aviso tipo="info">No hay vacantes nuevas para recomendarte con tus criterios. Prueba cambiando la ciudad o vuelve más tarde.</Aviso>
          ) : datos!.errores.length ? (
            <Aviso tipo="error">{datos!.errores.join(" ")}</Aviso>
          ) : !ordenadas.length ? (
            <Aviso tipo="info">
              {estado.total === 0
                ? "No encontré vacantes que coincidan con tu perfil y tus criterios. Cuando se publiquen vacantes nuevas las revisaré y te las mostraré aquí."
                : "Ya respondiste todas las recomendaciones. Te mostraré otras cuando se publiquen vacantes nuevas, o usa «Actualizar recomendaciones»."}
            </Aviso>
          ) : (
            <>
              <p className="flex items-center gap-2 text-sm text-texto-sec"><Sparkles className="size-4 text-primario" aria-hidden />
                Estas son sugerencias del agente. Nada se guarda hasta que respondas.</p>
              {!ordenadas.some((r) => r.seguro) && (
                <Aviso tipo="info">No encontré coincidencias claras con tu perfil: estas recomendaciones son de menor relevancia.</Aviso>
              )}
              {ordenadas.map((rec) => {
                const id = rec.vacante.Id_vacante;
                return (
                  <TarjetaRec
                    key={id} rec={rec} confirmando={confirmando === id}
                    acciones={{
                      interesa: async () => despues(await api.post(`/recomendaciones/${id}/decision`, { decision: "Interesa", motivo: rec.motivo }), id),
                      descartar: async () => despues(await api.post(`/recomendaciones/${id}/decision`, { decision: "Descartada", motivo: rec.motivo }), id),
                      guardar: async () => despues(await api.put(`/vacantes/${id}/guardada`), id),
                      postular: () => setConfirmando(id),
                      cancelar: () => setConfirmando(null),
                      confirmar: async () => {
                        const r = await api.post(`/vacantes/${id}/postular`);
                        despues(r, id, `Te postulaste a «${rec.vacante.Cargo}». La encuentras en Mis postulaciones.`);
                        cliente.invalidateQueries({ queryKey: ["postulaciones"] });
                      },
                      rechazar: async () => despues(
                        await api.post(`/recomendaciones/${id}/decision`, { decision: "Descartada", motivo: rec.motivo }), id,
                        "Rechazaste la recomendación: no se registró ninguna postulación y no te la volveré a recomendar.",
                      ),
                    }}
                  />
                );
              })}
            </>
          )}

        {interes.data?.ok && interes.data.datos.length > 0 && (
          <section className="mt-4 flex flex-col gap-2 border-t border-borde pt-6">
            <h2 className="text-lg font-semibold">Vacantes que marcaste de interés</h2>
            <ul className="flex flex-col gap-1 text-sm">
              {interes.data.datos.map((v) => (
                <li key={v.Id_vacante}><strong className="font-medium">{v.Cargo}</strong> en {v.Empresa}{v.Estado === "Cerrada" ? " (cerrada)" : ""}</li>
              ))}
            </ul>
          </section>
        )}
        {interes.data && !interes.data.ok && <Aviso tipo="error">{interes.data.mensaje}</Aviso>}
      </div>
    </>
  );
}
