// Mejorar la hoja de vida (#24) — MejorasCvFront.py.
// Las sugerencias viven solo en el cliente: el perfil cambia únicamente al «Aplicar».
import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Sparkles } from "lucide-react";
import { api, type Respuesta } from "../../api/cliente";
import { AgenteTrabajando, AreaTexto, Aviso, BloqueDudoso, Boton, Campo, Encabezado, Esqueleto, EtiquetaAgente, Mensaje, Tarjeta } from "../../componentes/ui";

type Sug = { campo: "ocupacion" | "funciones" | "habilidades"; id_experiencia: number | null; propuesta: string; actual: string | null; motivo: string; seguro: boolean; vacantes: string[] };
type Datos = { faltantes: string[]; sin_interes: boolean; errores: string[]; sugerencias: Sug[]; experiencias: Record<string, string> };
type Estado = { respuesta: Respuesta<Datos>; sugerencias: (Sug & { numero: number; texto: string })[]; total: number };

function tituloSugerencia(s: Sug, exps: Record<string, string>) {
  if (s.campo === "ocupacion") return "Ocupación (titular de tu perfil)";
  const e = exps[String(s.id_experiencia)] ?? "tu experiencia";
  return s.campo === "funciones" ? `Funciones de «${e}»` : `Habilidades de «${e}»`;
}

export function Mejorar() {
  const cliente = useQueryClient();
  const [estado, setEstado] = useState<Estado | null>(null);
  const [mensaje, setMensaje] = useState<Pick<Respuesta, "ok" | "mensaje"> | null>(null);
  const [trabajando, setTrabajando] = useState(false);
  const [aplicando, setAplicando] = useState<number | null>(null);
  const vacantes = useQuery({
    queryKey: ["vacantes-interes"],
    queryFn: async () => api.get<{ Cargo: string; Empresa: string }[]>("/mejoras/vacantes-interes"),
  });

  const pedir = async () => {
    setTrabajando(true); setMensaje(null);
    const r = await api.post<Datos>("/mejoras/sugerencias");
    setTrabajando(false);
    const lista = r.ok ? r.datos.sugerencias : [];
    setEstado({ respuesta: r, sugerencias: lista.map((s, i) => ({ ...s, numero: i, texto: s.propuesta })), total: lista.length });
  };
  const quitar = (numero: number) =>
    setEstado((e) => (e ? { ...e, sugerencias: e.sugerencias.filter((s) => s.numero !== numero) } : e));
  const editar = (numero: number, texto: string) =>
    setEstado((e) => (e ? { ...e, sugerencias: e.sugerencias.map((s) => (s.numero === numero ? { ...s, texto } : s)) } : e));

  const aplicar = async (s: Estado["sugerencias"][number]) => {
    setAplicando(s.numero);
    const r = await api.post("/mejoras/aplicar", { campo: s.campo, id_experiencia: s.id_experiencia, texto: s.texto });
    setAplicando(null);
    setMensaje(r);
    if (r.ok) { quitar(s.numero); cliente.invalidateQueries({ queryKey: ["perfil"] }); }
  };

  const datos = estado?.respuesta.datos;
  return (
    <>
      <Link to="/perfil" className="mb-4 inline-flex items-center gap-1 text-sm text-texto-sec hover:text-primario">
        <ArrowLeft className="size-4" aria-hidden /> Volver
      </Link>
      <Encabezado
        titulo="Mejora tu hoja de vida"
        descripcion="El agente compara tu perfil con las vacantes que te interesan y te sugiere cambios concretos. Puedes aplicar o descartar cada uno."
      />
      <div className="flex flex-col gap-5">
        <Mensaje resultado={mensaje} />
        <Tarjeta className="flex flex-col gap-4 sm:flex-row sm:items-center">
          <div className="flex-1 text-sm text-texto-sec">
            {vacantes.isLoading ? <Esqueleto className="h-4 w-2/3" /> :
              !vacantes.data?.ok ? <span className="text-error-fuerte">{vacantes.data?.mensaje}</span> :
              vacantes.data.datos.length ? <>Se comparará con: {vacantes.data.datos.map((v) => `${v.Cargo} (${v.Empresa})`).join("; ")}</> :
              "Todavía no tienes vacantes de interés."}
          </div>
          <Boton variante="primario" icono={Sparkles} onClick={pedir} disabled={trabajando}>Pedir sugerencias</Boton>
        </Tarjeta>

        {trabajando && <AgenteTrabajando texto="El agente está comparando tu perfil con tus vacantes de interés..." />}

        {estado && !trabajando && (
          !estado.respuesta.ok ? <Aviso tipo="error">{estado.respuesta.mensaje}</Aviso> :
          datos!.faltantes.length ? (
            <Aviso tipo="aviso">
              {`Para sugerirte mejoras necesito que completes tu perfil. Te falta:\n${datos!.faltantes.map((f) => `- ${f}`).join("\n")}\n\n`}
              Complétalo en <Link to="/perfil/manual" className="font-medium underline">Mi perfil → Llenar mi perfil manualmente</Link>.
            </Aviso>
          ) : datos!.sin_interes ? (
            <Aviso tipo="aviso">
              Para sugerirte mejoras necesito saber qué vacantes te interesan. Guarda al menos una con <strong>Guardar vacante</strong> en
              su detalle (o márcala con <strong>Me interesa</strong> en Recomendaciones) y vuelve a pedir sugerencias.
            </Aviso>
          ) : datos!.errores.length ? (
            <Aviso tipo="error">{datos!.errores.join(" ")}</Aviso>
          ) : !estado.sugerencias.length ? (
            <Aviso tipo="info">
              {estado.total === 0
                ? "Tu perfil ya encaja con tus vacantes de interés: el agente no encontró cambios para sugerirte."
                : "Ya revisaste todas las sugerencias."}
            </Aviso>
          ) : (
            <>
              <p className="text-sm text-texto-sec">Son sugerencias del agente: tu perfil solo cambia cuando aplicas una.</p>
              {estado.sugerencias.map((s) => (
                <Tarjeta key={s.numero} as="article" className="flex flex-col gap-3">
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <h2 className="text-base font-semibold">{tituloSugerencia(s, datos!.experiencias)}</h2>
                    <EtiquetaAgente />
                  </div>
                  {s.seguro ? (
                    <p className="text-sm"><span className="text-xs text-texto-tenue">Cambio sugerido</span><br /><strong>Por qué:</strong> {s.motivo}</p>
                  ) : (
                    <BloqueDudoso>
                      Recomendación: no estoy seguro de este cambio. {s.motivo} Aplícalo solo si es cierto; no se cambia nada por sí solo.
                    </BloqueDudoso>
                  )}
                  {s.vacantes.length > 0 && <p className="text-xs text-texto-sec">Según: {s.vacantes.join(", ")}</p>}
                  {s.campo !== "habilidades" && s.actual && <p className="text-xs text-texto-sec">Ahora dice: {s.actual}</p>}
                  {s.campo === "habilidades" && <p className="text-xs text-texto-sec">Habilidades actuales: {s.actual || "ninguna"}</p>}
                  {s.campo === "habilidades" ? (
                    <Campo etiqueta="Habilidades para agregar" value={s.texto} onChange={(e) => editar(s.numero, e.target.value)} />
                  ) : (
                    <AreaTexto etiqueta="Texto propuesto" rows={3} value={s.texto} onChange={(e) => editar(s.numero, e.target.value)} />
                  )}
                  <div className="flex flex-col gap-2 sm:flex-row">
                    <Boton variante="primario" cargando={aplicando === s.numero} onClick={() => aplicar(s)}>Aplicar a mi perfil</Boton>
                    <Boton onClick={() => { quitar(s.numero); setMensaje({ ok: true, mensaje: "Descartaste la sugerencia; tu perfil no cambió." }); }}>
                      Descartar
                    </Boton>
                  </div>
                </Tarjeta>
              ))}
            </>
          )
        )}
      </div>
    </>
  );
}
