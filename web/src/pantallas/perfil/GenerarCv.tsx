// Generar el CV con el agente (#7) — GenerarCvFront.py.
// El borrador vive en el cliente; «Confirmar CV» lo guarda como hoja de vida, «Rechazar» lo descarta.
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Download, Sparkles } from "lucide-react";
import { api, descargar, type Respuesta } from "../../api/cliente";
import { AgenteTrabajando, AreaTexto, Aviso, BloqueDudoso, Boton, Campo, Encabezado, EtiquetaAgente, Mensaje, Tarjeta } from "../../componentes/ui";

type Exp = { cargo: string; empresa: string; periodo: string; logros: string[] };
type Edu = { titulo: string; institucion: string; periodo: string };
type CV = {
  nombre: string; titular: string; resumen: string; contacto: Record<string, string | null>;
  experiencia: Exp[]; educacion: Edu[]; habilidades: string[]; secciones_dudosas: string[];
};
type Edicion = { titular: string; resumen: string; logros: string[]; habilidades: string };

function editado(b: CV, e: Edicion): CV {
  return {
    ...b,
    titular: e.titular.trim(),
    resumen: e.resumen.trim(),
    experiencia: b.experiencia.map((x, i) => ({
      ...x,
      logros: e.logros[i].split("\n").map((l) => l.trim().replace(/^[•\-\s]+|[•\-\s]+$/g, "").trim()).filter(Boolean),
    })),
    habilidades: e.habilidades.split(",").map((h) => h.trim()).filter(Boolean),
  };
}

function Dudosa({ dudosas, seccion, texto }: { dudosas: string[]; seccion: string; texto: string }) {
  if (!dudosas.includes(seccion)) return null;
  return <BloqueDudoso>Revisa {texto}: el agente no quedó seguro de cómo redactarla.</BloqueDudoso>;
}

function VistaPrevia({ cv }: { cv: CV }) {
  const contacto = Object.values(cv.contacto).filter(Boolean).join(" · ");
  return (
    <div className="flex flex-col gap-4 rounded-[var(--radius-control)] border border-borde bg-superficie p-6 text-sm">
      <div>
        <p className="text-lg font-semibold text-primario">{cv.nombre}</p>
        <p>{cv.titular}</p>
        <p className="text-xs italic text-texto-sec">{contacto}</p>
      </div>
      <div><p className="font-semibold">Perfil profesional</p><p className="mt-1 whitespace-pre-line text-texto-sec">{cv.resumen}</p></div>
      <div>
        <p className="font-semibold">Experiencia</p>
        <ul className="mt-1 list-disc pl-5">
          {cv.experiencia.map((e, i) => (
            <li key={i}><strong>{e.cargo}</strong> — {e.empresa} ({e.periodo})
              <ul className="list-[circle] pl-5 text-texto-sec">{e.logros.map((l, j) => <li key={j}>{l}</li>)}</ul>
            </li>
          ))}
        </ul>
      </div>
      <div>
        <p className="font-semibold">Educación</p>
        <ul className="mt-1 list-disc pl-5">{cv.educacion.map((e, i) => <li key={i}><strong>{e.titulo}</strong> — {e.institucion} ({e.periodo})</li>)}</ul>
      </div>
      <div><p className="font-semibold">Habilidades</p><p className="mt-1 text-texto-sec">{cv.habilidades.join(", ")}</p></div>
    </div>
  );
}

function Borrador({ borrador, onFin }: { borrador: CV; onFin: (r: Pick<Respuesta, "ok" | "mensaje">) => void }) {
  const cliente = useQueryClient();
  const [ed, setEd] = useState<Edicion>({
    titular: borrador.titular, resumen: borrador.resumen,
    logros: borrador.experiencia.map((e) => e.logros.join("\n")), habilidades: borrador.habilidades.join(", "),
  });
  const [vista, setVista] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirmando, setConfirmando] = useState(false);
  const cv = useMemo(() => editado(borrador, ed), [borrador, ed]);
  const dudosas = borrador.secciones_dudosas;

  return (
    <div className="flex flex-col gap-5">
      {dudosas.length > 0 && (
        <BloqueDudoso>Revisa estas secciones: el agente no quedó seguro de cómo redactarlas: {dudosas.join(", ")}.</BloqueDudoso>
      )}
      <p className="text-sm text-texto-sec">Es un borrador: nada se guarda hasta que lo confirmes. Puedes editar lo que redactó el agente.</p>
      <Tarjeta className="flex flex-col gap-4">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div>
            <p className="text-base font-semibold">{borrador.nombre}</p>
            <p className="text-xs text-texto-sec">{Object.values(borrador.contacto).filter(Boolean).join(" · ")} (se cambia en Mi perfil)</p>
          </div>
          <EtiquetaAgente />
        </div>
        <Campo etiqueta="Titular" value={ed.titular} onChange={(e) => setEd({ ...ed, titular: e.target.value })} />
        <Dudosa dudosas={dudosas} seccion="resumen" texto="el perfil profesional" />
        <AreaTexto etiqueta="Perfil profesional" value={ed.resumen} onChange={(e) => setEd({ ...ed, resumen: e.target.value })} />
        <h3 className="text-base font-semibold">Experiencia</h3>
        {borrador.experiencia.map((e, i) => (
          <div key={i} className="flex flex-col gap-2 border-l-2 border-borde pl-4">
            <p className="text-sm font-medium">{e.cargo} — {e.empresa}</p>
            <p className="text-xs text-texto-sec">{e.periodo}</p>
            <Dudosa dudosas={dudosas} seccion={`experiencia ${i + 1}`} texto="esta experiencia" />
            <AreaTexto
              etiqueta="Logros (uno por línea)" value={ed.logros[i]}
              onChange={(ev) => setEd({ ...ed, logros: ed.logros.map((l, j) => (j === i ? ev.target.value : l)) })}
            />
          </div>
        ))}
        <h3 className="text-base font-semibold">Educación</h3>
        {borrador.educacion.map((e, i) => <p key={i} className="text-sm text-texto-sec">{e.titulo} — {e.institucion} · {e.periodo}</p>)}
        <Dudosa dudosas={dudosas} seccion="habilidades" texto="las habilidades" />
        <AreaTexto etiqueta="Habilidades (separadas por comas)" rows={2} value={ed.habilidades} onChange={(e) => setEd({ ...ed, habilidades: e.target.value })} />
      </Tarjeta>

      <div className="rounded-[var(--radius-tarjeta)] border border-borde bg-superficie">
        <button type="button" aria-expanded={vista} onClick={() => setVista(!vista)} className="w-full px-5 h-12 text-left text-sm font-medium text-primario cursor-pointer">
          Vista previa del CV
        </button>
        {vista && <div className="border-t border-borde p-5"><VistaPrevia cv={cv} /></div>}
      </div>

      {error && <Aviso tipo="error">{error}</Aviso>}
      <div className="flex flex-col gap-3">
        <div><Boton icono={Download} onClick={async () => setError(await descargar("/cv/documento", { cv }))}>Descargar CV (.docx)</Boton></div>
        <p className="text-xs text-texto-sec">Al confirmarlo, reemplaza la hoja de vida de tu perfil y es la que se usará al postularte.</p>
        <div className="flex flex-col gap-2 sm:flex-row">
          <Boton
            variante="primario" cargando={confirmando}
            onClick={async () => {
              setConfirmando(true);
              const r = await api.post("/cv/confirmar", { cv });
              setConfirmando(false);
              if (r.ok) cliente.invalidateQueries({ queryKey: ["hoja-de-vida"] });
              onFin(r);
            }}
          >
            Confirmar CV
          </Boton>
          <Boton onClick={() => onFin({ ok: true, mensaje: "Rechazaste el CV generado: no se guardó nada." })}>Rechazar</Boton>
        </div>
      </div>
    </div>
  );
}

export function GenerarCv() {
  const [mensaje, setMensaje] = useState<Pick<Respuesta, "ok" | "mensaje"> | null>(null);
  const [generado, setGenerado] = useState<{ cv: CV; ronda: number } | null>(null);
  const [resultado, setResultado] = useState<Respuesta<{ cv: CV | null; faltantes: string[] }> | null>(null);
  const [trabajando, setTrabajando] = useState(false);

  const generar = async () => {
    setTrabajando(true); setMensaje(null); setResultado(null);
    const r = await api.post<{ cv: CV | null; faltantes: string[] }>("/cv/borrador");
    setTrabajando(false);
    if (r.ok && r.datos.cv) setGenerado({ cv: r.datos.cv, ronda: Date.now() });
    else { setGenerado(null); setResultado(r); }
  };

  return (
    <>
      <Link to="/perfil" className="mb-4 inline-flex items-center gap-1 text-sm text-texto-sec hover:text-primario">
        <ArrowLeft className="size-4" aria-hidden /> Volver
      </Link>
      <Encabezado
        titulo="Genera tu CV"
        descripcion="El agente redacta tu CV a partir de tu perfil. Revísalo y edítalo; cuando lo confirmes, queda como tu hoja de vida para postularte."
        accion={<Boton variante="primario" icono={Sparkles} onClick={generar} disabled={trabajando}>Generar mi CV</Boton>}
      />
      <div className="flex flex-col gap-5">
        <Mensaje resultado={mensaje} />
        {trabajando && <AgenteTrabajando texto="El agente está redactando tu CV..." />}
        {generado && (
          <Borrador
            key={generado.ronda} borrador={generado.cv}
            onFin={(r) => { setMensaje(r); if (r.ok) setGenerado(null); window.scrollTo({ top: 0, behavior: "smooth" }); }}
          />
        )}
        {!generado && resultado && (
          !resultado.ok ? <Aviso tipo="error">{resultado.mensaje}</Aviso> : (
            <Aviso tipo="aviso">
              {`Antes de generar tu CV completa estas secciones de tu perfil:\n${resultado.datos.faltantes.map((f) => `- ${f}`).join("\n")}\n\n`}
              Hazlo en <Link to="/perfil/manual" className="font-medium underline">Mi perfil → Llenar mi perfil manualmente</Link>.
            </Aviso>
          )
        )}
      </div>
    </>
  );
}
