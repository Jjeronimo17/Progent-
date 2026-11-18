// Detalle de la vacante (#10): guardar (#16), compatibilidad (#26) y postularse (#12, #13, #20).
import { useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Bookmark, BookmarkCheck, CheckCircle2, CircleDashed, Sparkles, XCircle } from "lucide-react";
import { api, type Respuesta } from "../../api/cliente";
import { Carta } from "../../componentes/Carta";
import {
  AgenteTrabajando, Aviso, BarraNivel, BloqueDudoso, Boton, Encabezado, EsqueletoTarjetas, EtiquetaAgente, Mensaje, Tarjeta,
} from "../../componentes/ui";
import { textoDia } from "../../lib/fechas";
import { salarioModalidad, type Vacante } from "../../lib/vacantes";

type Postulacion = { Id_postulacion: number; Fecha_postulacion: string; Cv: string | null } | null;
type Detalle = { vacante: Vacante; guardada: boolean | null; postulacion: Postulacion; avisos: string[] };
type Criterio = { requisito: string; cumple: "si" | "parcial" | "no"; dato_perfil: string | null; seguro: boolean };
type Compat = {
  perfil_vacio: boolean; errores: string[]; insuficiente: boolean; falta: string[];
  nivel: "Alta" | "Media" | "Baja"; porcentaje: number; aproximado: boolean; criterios: Criterio[];
};
type Resultado = Pick<Respuesta, "ok" | "mensaje"> | null;

const CUMPLE = {
  si: { texto: "Cumple", Icono: CheckCircle2, clase: "text-exito-fuerte" },
  parcial: { texto: "Cumple en parte", Icono: CircleDashed, clase: "text-aviso-fuerte" },
  no: { texto: "No cumple", Icono: XCircle, clase: "text-error-fuerte" },
};

function Volver() {
  return (
    <Link to="/vacantes" className="mb-4 inline-flex items-center gap-1 text-sm text-texto-sec hover:text-primario">
      <ArrowLeft className="size-4" aria-hidden /> Volver
    </Link>
  );
}

function Compatibilidad({ id }: { id: number }) {
  const [abierta, setAbierta] = useState(false);
  const [trabajando, setTrabajando] = useState(false);
  const [resp, setResp] = useState<Respuesta<Compat> | null>(null);
  const calcular = async () => {
    setTrabajando(true);
    setResp(await api.post<Compat>(`/vacantes/${id}/compatibilidad`));
    setTrabajando(false);
  };
  const d = resp?.datos;
  return (
    <Tarjeta className="p-0">
      <button type="button" aria-expanded={abierta} onClick={() => setAbierta(!abierta)}
        className="flex w-full items-center gap-2 px-5 h-12 text-sm font-medium text-texto cursor-pointer">
        <Sparkles className="size-4 text-primario" aria-hidden /> Mi compatibilidad con esta vacante
      </button>
      {abierta && (
        <div className="flex flex-col gap-4 border-t border-borde p-5">
          <p className="text-sm text-texto-sec">El agente compara cada requisito de la vacante con tu perfil.</p>
          <div><Boton onClick={calcular} disabled={trabajando}>Calcular mi compatibilidad</Boton></div>
          {trabajando && <AgenteTrabajando texto="El agente está comparando tu perfil con la vacante..." />}
          {resp && !trabajando && (
            !resp.ok ? <Aviso tipo="error">{resp.mensaje}</Aviso> :
            d!.perfil_vacio ? (
              <Aviso tipo="aviso">
                Tu perfil no tiene información para compararlo con esta vacante. Agrega tu ocupación, experiencia o educación en{" "}
                <Link to="/perfil/manual" className="font-medium underline">Mi perfil → Llenar mi perfil manualmente</Link>.
              </Aviso>
            ) : d!.errores.length ? <Aviso tipo="error">{d!.errores.join(" ")}</Aviso> : (
              <div className="flex flex-col gap-4">
                {d!.insuficiente && (
                  <Aviso tipo="aviso">
                    Tu perfil no tiene suficiente información{d!.falta.length ? ` (te falta: ${d!.falta.join(", ")})` : ""}: el resultado
                    puede no ser preciso. Complétalo en Mi perfil para una comparación mejor.
                  </Aviso>
                )}
                <div className="flex items-center justify-between">
                  <p className="text-sm font-semibold">
                    Compatibilidad: {d!.nivel} ({d!.porcentaje} %){d!.aproximado ? " · aproximada" : ""}
                  </p>
                  <EtiquetaAgente />
                </div>
                <BarraNivel nivel={d!.nivel} porcentaje={d!.porcentaje} />
                <p className="text-xs text-texto-sec">
                  Calculada con {d!.criterios.length} requisitos de la vacante: cumple = 1, en parte = ½ y no cumple = 0. Alta desde 70 %, media desde 40 %.
                </p>
                <ul className="flex flex-col gap-3">
                  {d!.criterios.map((c, i) => {
                    const { texto, Icono, clase } = CUMPLE[c.cumple];
                    return (
                      <li key={i} className="flex gap-3 text-sm">
                        <Icono className={`mt-0.5 size-4 shrink-0 ${clase}`} aria-label={texto} />
                        <div className="flex flex-col gap-1">
                          <p><span className={clase}>{texto}</span> — <strong className="font-medium">{c.requisito}</strong></p>
                          {!c.seguro && <BloqueDudoso>aproximado: el agente no quedó seguro</BloqueDudoso>}
                          <p className="text-xs text-texto-sec">{c.dato_perfil ? `Me basé en: ${c.dato_perfil}` : "Tu perfil no lo menciona."}</p>
                        </div>
                      </li>
                    );
                  })}
                </ul>
                <p className="text-xs text-texto-tenue">Es una estimación del agente para ayudarte a decidir; no se guarda ni se envía a la empresa.</p>
              </div>
            )
          )}
        </div>
      )}
    </Tarjeta>
  );
}

function HojaParaPostular({ id, alPostular }: { id: number; alPostular: (r: Resultado) => void }) {
  const cliente = useQueryClient();
  const entrada = useRef<HTMLInputElement>(null);
  const [archivo, setArchivo] = useState<File | null>(null);
  const [mensaje, setMensaje] = useState<Resultado>(null);
  const [enviando, setEnviando] = useState(false);
  const hoja = useQuery({ queryKey: ["hoja-de-vida"], queryFn: () => api.get<{ nombre: string } | null>("/perfil/hoja-de-vida") });

  if (hoja.isLoading) return null;
  if (!hoja.data?.ok) return <Aviso tipo="error">{hoja.data?.mensaje}</Aviso>;
  const cv = hoja.data.datos;
  return (
    <div className="flex flex-col gap-4">
      <Mensaje resultado={mensaje} />
      {!cv ? (
        <>
          <Aviso tipo="info">Para postularte necesitas tu hoja de vida. Cárgala aquí: quedará guardada en tu perfil para tus próximas postulaciones.</Aviso>
          <div className="flex flex-col gap-1.5">
            <label htmlFor="cv-postular" className="text-sm font-medium">Tu hoja de vida (PDF o Word, máx. 5 MB)</label>
            <input ref={entrada} id="cv-postular" type="file" accept=".pdf,.docx" onChange={(e) => setArchivo(e.target.files?.[0] ?? null)}
              className="text-sm file:mr-3 file:rounded-[var(--radius-control)] file:border file:border-borde file:bg-superficie file:px-3 file:py-2 file:text-sm file:font-medium" />
          </div>
          <div>
            <Boton disabled={!archivo} onClick={async () => {
              const r = await api.subir("POST", "/perfil/hoja-de-vida", archivo!);
              setMensaje(r);
              if (r.ok) { setArchivo(null); cliente.invalidateQueries({ queryKey: ["hoja-de-vida"] }); }
            }}>Guardar hoja de vida</Boton>
          </div>
        </>
      ) : (
        <fieldset className="flex flex-col gap-2">
          <legend className="mb-1 text-sm font-medium">Hoja de vida para esta postulación</legend>
          <label className="flex items-center gap-2 text-sm">
            <input type="radio" name={`cv-${id}`} defaultChecked className="accent-[var(--color-primario)]" />
            {cv.nombre} (guardada en tu perfil)
          </label>
        </fieldset>
      )}
      <Boton variante="primario" ancho cargando={enviando} onClick={async () => {
        setEnviando(true);
        alPostular(await api.post(`/vacantes/${id}/postular`));
        setEnviando(false);
      }}>
        Postularme
      </Boton>
    </div>
  );
}

export function DetalleVacante() {
  const id = Number(useParams().id);
  const navegar = useNavigate();
  const cliente = useQueryClient();
  const [resGuardar, setResGuardar] = useState<Resultado>(null);
  const [resPostular, setResPostular] = useState<Resultado>(null);
  const detalle = useQuery({ queryKey: ["vacante", id], queryFn: () => api.get<Detalle>(`/vacantes/${id}`) });

  if (detalle.isLoading) return <><Volver /><EsqueletoTarjetas n={2} /></>;
  if (!detalle.data?.ok) return <><Volver /><Aviso tipo="error">{detalle.data?.mensaje}</Aviso></>;
  const { vacante: v, guardada, postulacion, avisos } = detalle.data.datos;
  if (v.Estado === "Cerrada") {
    return <><Volver /><Aviso tipo="aviso">La vacante «{v.Cargo}» fue cerrada y ya no recibe postulaciones.</Aviso></>;
  }

  const cambiarGuardada = async () => {
    const r = guardada ? await api.delete(`/vacantes/${id}/guardada`) : await api.put(`/vacantes/${id}/guardada`);
    setResGuardar(r);
    detalle.refetch();
    cliente.invalidateQueries({ queryKey: ["guardadas"] });
  };

  return (
    <>
      <Volver />
      <Encabezado
        titulo={v.Cargo}
        descripcion={<>Publicada por <strong className="text-texto">{v.Empresa}</strong> · {v.Ubicacion} · Publicada el {textoDia(v.Fecha_publicacion)}<br />{salarioModalidad(v)}</>}
        accion={guardada !== null && (
          <Boton icono={guardada ? BookmarkCheck : Bookmark} onClick={cambiarGuardada}>
            {guardada ? "Quitar de guardadas" : "Guardar vacante"}
          </Boton>
        )}
      />
      <div className="flex flex-col gap-6">
        {avisos.map((a) => <Aviso key={a} tipo="error">{a}</Aviso>)}
        {resGuardar?.mensaje && <Aviso tipo={resGuardar.ok ? "exito" : "error"}>{resGuardar.mensaje.replace(/\*\*/g, "")}</Aviso>}
        <Tarjeta className="flex flex-col gap-4 text-sm">
          <div><h2 className="text-base font-semibold">Descripción</h2><p className="mt-1 text-texto-sec">{v.Descripcion}</p></div>
          <div><h2 className="text-base font-semibold">Requisitos</h2><p className="mt-1 text-texto-sec">{v.Requisitos}</p></div>
        </Tarjeta>
        <Compatibilidad id={id} />
        <Tarjeta className="flex flex-col gap-4">
          <h2 className="text-base font-semibold">Postulación</h2>
          {resPostular?.mensaje && (
            resPostular.ok ? (
              <div className="flex flex-col gap-1">
                <Aviso tipo="exito">{resPostular.mensaje.replace(/\*\*/g, "")}</Aviso>
                <p className="text-xs text-texto-sec">Progent guarda tu postulación para que le hagas seguimiento, pero no la envía al portal de la empresa.</p>
              </div>
            ) : <Aviso tipo="aviso">{resPostular.mensaje.replace(/\*\*/g, "")}</Aviso>
          )}
          {postulacion ? (
            <div className="flex flex-col gap-4">
              <Aviso tipo="info">Ya te postulaste a esta vacante el {textoDia(postulacion.Fecha_postulacion)}.</Aviso>
              <p className="text-sm">
                {postulacion.Cv ? <>Hoja de vida asociada a esta postulación: <strong>{postulacion.Cv}</strong></> : "Esta postulación no tiene hoja de vida asociada."}
              </p>
              <div><Boton onClick={() => navegar("/postulaciones")}>Ver en mis postulaciones</Boton></div>
              <div className="border-t border-borde pt-4">
                <p className="mb-3 text-sm font-semibold">Carta de presentación <span className="font-normal text-texto-sec">(opcional)</span></p>
                <Carta idPostulacion={postulacion.Id_postulacion} />
              </div>
            </div>
          ) : (
            <HojaParaPostular id={id} alPostular={(r) => { setResPostular(r); detalle.refetch(); cliente.invalidateQueries({ queryKey: ["postulaciones"] }); }} />
          )}
        </Tarjeta>
      </div>
    </>
  );
}
