// Subir la hoja de vida (#5, #6) e importar desde LinkedIn (#4) — ImportarPerfilFront.py.
// Lo que extrae el agente vive SOLO aquí (en el cliente) hasta que el usuario confirma (decisión 7).
import { useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Download, FileText, Sparkles, Upload } from "lucide-react";
import { api, descargar, type Respuesta } from "../../api/cliente";
import {
  AgenteTrabajando, AreaTexto, Aviso, BloqueDudoso, Boton, Campo, Casilla, Encabezado, Esqueleto, EtiquetaAgente, Mensaje, Tarjeta,
} from "../../componentes/ui";

type ExpB = { cargo: string; empresa: string; fecha_inicio: string; fecha_fin: string; actual: boolean; descripcion: string; incluir: boolean };
type EduB = { titulo: string; institucion: string; fecha_inicio: string; fecha_fin: string; en_curso: boolean; incluir: boolean };
type Borrador = {
  nombre: string; titular: string; correo: string; telefono: string; ciudad: string;
  experiencia: ExpB[]; educacion: EduB[]; habilidades: string[]; idiomas: { idioma: string; nivel?: string | null }[]; dudosos: string[];
};
type Origen = "cv" | "linkedin";
type Resultado = Pick<Respuesta, "ok" | "mensaje"> | null;

function HojaGuardada() {
  const hoja = useQuery({
    queryKey: ["hoja-de-vida"],
    queryFn: async () => {
      const r = await api.get<{ nombre: string; tipo: string } | null>("/perfil/hoja-de-vida");
      if (!r.ok) throw new Error(r.mensaje ?? "");
      return r.datos;
    },
  });
  const [error, setError] = useState<string | null>(null);
  if (hoja.isLoading) return <Esqueleto className="h-16 w-full" />;
  if (hoja.error) return <Aviso tipo="error">{(hoja.error as Error).message}</Aviso>;
  if (!hoja.data) return <p className="text-sm text-texto-sec">Todavía no tienes una hoja de vida guardada en tu perfil.</p>;
  return (
    <Tarjeta className="flex flex-col gap-3 sm:flex-row sm:items-center">
      <span className="grid size-10 place-items-center rounded-[var(--radius-control)] bg-acento-suave text-acento-fuerte">
        <FileText className="size-5" aria-hidden />
      </span>
      <div className="flex-1">
        <p className="text-sm">Hoja de vida guardada en tu perfil: <strong className="font-semibold">{hoja.data.nombre}</strong></p>
        <p className="text-xs text-texto-sec">Para reemplazarla, sube otra abajo y pulsa «Guardar en mi perfil».</p>
        {error && <p className="mt-1 text-xs text-error-fuerte">{error}</p>}
      </div>
      <Boton icono={Download} onClick={async () => setError(await descargar("/perfil/hoja-de-vida/archivo"))}>
        Descargar mi hoja de vida
      </Boton>
    </Tarjeta>
  );
}

function aBorrador(b: Omit<Borrador, "experiencia" | "educacion"> & { experiencia: Omit<ExpB, "incluir">[]; educacion: Omit<EduB, "incluir">[] }): Borrador {
  return {
    ...b,
    experiencia: b.experiencia.map((e) => ({ ...e, incluir: true })),
    educacion: b.educacion.map((e) => ({ ...e, incluir: true })),
  };
}

/** Lo que se envía al confirmar: sin lo desmarcado y con todo recortado (leer_borrador). */
function paraGuardar(b: Borrador, habilidades: string) {
  const t = (v: string) => (v ?? "").trim();
  return {
    nombre: t(b.nombre), titular: t(b.titular), correo: t(b.correo), telefono: t(b.telefono), ciudad: t(b.ciudad),
    experiencia: b.experiencia.filter((e) => e.incluir).map(({ incluir: _i, ...e }) => ({
      ...e, cargo: t(e.cargo), empresa: t(e.empresa), fecha_inicio: t(e.fecha_inicio), fecha_fin: t(e.fecha_fin), descripcion: t(e.descripcion),
    })),
    educacion: b.educacion.filter((e) => e.incluir).map(({ incluir: _i, ...e }) => ({
      ...e, titulo: t(e.titulo), institucion: t(e.institucion), fecha_inicio: t(e.fecha_inicio), fecha_fin: t(e.fecha_fin),
    })),
    habilidades: habilidades.split(",").map((h) => h.trim()).filter(Boolean),
    idiomas: b.idiomas,
    dudosos: b.dudosos,
  };
}

function Revision({ inicial, onConfirmar, onRechazar }: {
  inicial: Borrador;
  onConfirmar: (borrador: ReturnType<typeof paraGuardar>, revise: boolean) => Promise<void>;
  onRechazar: () => void;
}) {
  const [b, setB] = useState(inicial);
  const [habilidades, setHabilidades] = useState(inicial.habilidades.join(", "));
  const [revise, setRevise] = useState(false);
  const [guardando, setGuardando] = useState(false);
  const campo = (k: "nombre" | "titular" | "correo" | "telefono" | "ciudad") => ({
    value: b[k] ?? "", onChange: (e: React.ChangeEvent<HTMLInputElement>) => setB({ ...b, [k]: e.target.value }),
  });
  const exp = (i: number, cambio: Partial<ExpB>) => setB({ ...b, experiencia: b.experiencia.map((e, j) => (j === i ? { ...e, ...cambio } : e)) });
  const edu = (i: number, cambio: Partial<EduB>) => setB({ ...b, educacion: b.educacion.map((e, j) => (j === i ? { ...e, ...cambio } : e)) });

  return (
    <section className="flex flex-col gap-5" aria-labelledby="titulo-revision">
      <div className="flex flex-wrap items-center gap-3">
        <h2 id="titulo-revision" className="text-lg font-semibold">Revisa lo que encontró el agente</h2>
        <EtiquetaAgente />
      </div>
      <p className="-mt-3 text-sm text-texto-sec">Nada se guarda hasta que confirmes. Corrige lo que esté mal o desmarca lo que no quieras guardar.</p>
      {b.dudosos.length > 0 && (
        <BloqueDudoso>El agente no quedó seguro de: {b.dudosos.join(", ")}. Quedan pendientes de tu confirmación.</BloqueDudoso>
      )}

      <Tarjeta className="grid gap-4 sm:grid-cols-2">
        <h3 className="text-base font-semibold sm:col-span-2">Datos básicos</h3>
        <Campo etiqueta="Nombre completo *" {...campo("nombre")} />
        <Campo etiqueta="Titular u ocupación" {...campo("titular")} />
        <Campo etiqueta="Correo de contacto *" {...campo("correo")} />
        <Campo etiqueta="Teléfono" {...campo("telefono")} />
        <Campo etiqueta="Ciudad *" {...campo("ciudad")} />
      </Tarjeta>

      <h3 className="text-base font-semibold">Experiencia</h3>
      {!b.experiencia.length && <p className="text-sm text-texto-sec">El agente no encontró experiencia laboral.</p>}
      {b.experiencia.map((e, i) => (
        <Tarjeta key={i} className={`grid gap-4 sm:grid-cols-2 ${e.incluir ? "" : "opacity-60"}`}>
          <div className="sm:col-span-2">
            <Casilla
              etiqueta={`Incluir: ${inicial.experiencia[i].cargo || "sin cargo"} — ${inicial.experiencia[i].empresa || "sin empresa"}`}
              checked={e.incluir} onChange={(ev) => exp(i, { incluir: ev.target.checked })}
            />
          </div>
          <Campo etiqueta="Cargo *" value={e.cargo} onChange={(ev) => exp(i, { cargo: ev.target.value })} />
          <Campo etiqueta="Empresa *" value={e.empresa} onChange={(ev) => exp(i, { empresa: ev.target.value })} />
          <Campo etiqueta="Fecha de inicio * (AAAA-MM-DD)" value={e.fecha_inicio} onChange={(ev) => exp(i, { fecha_inicio: ev.target.value })} />
          <Campo etiqueta="Fecha de fin (AAAA-MM-DD)" value={e.fecha_fin} onChange={(ev) => exp(i, { fecha_fin: ev.target.value })} />
          <div className="sm:col-span-2"><Casilla etiqueta="Trabajo aquí actualmente" checked={e.actual} onChange={(ev) => exp(i, { actual: ev.target.checked })} /></div>
          <div className="sm:col-span-2"><AreaTexto etiqueta="Descripción de funciones" rows={3} value={e.descripcion} onChange={(ev) => exp(i, { descripcion: ev.target.value })} /></div>
        </Tarjeta>
      ))}

      <h3 className="text-base font-semibold">Educación</h3>
      {!b.educacion.length && <p className="text-sm text-texto-sec">El agente no encontró estudios.</p>}
      {b.educacion.map((e, i) => (
        <Tarjeta key={i} className={`grid gap-4 sm:grid-cols-2 ${e.incluir ? "" : "opacity-60"}`}>
          <div className="sm:col-span-2">
            <Casilla
              etiqueta={`Incluir: ${inicial.educacion[i].titulo || "sin título"} — ${inicial.educacion[i].institucion || "sin institución"}`}
              checked={e.incluir} onChange={(ev) => edu(i, { incluir: ev.target.checked })}
            />
          </div>
          <Campo etiqueta="Título *" value={e.titulo} onChange={(ev) => edu(i, { titulo: ev.target.value })} />
          <Campo etiqueta="Institución *" value={e.institucion} onChange={(ev) => edu(i, { institucion: ev.target.value })} />
          <Campo etiqueta="Fecha de inicio * (AAAA-MM-DD)" value={e.fecha_inicio} onChange={(ev) => edu(i, { fecha_inicio: ev.target.value })} />
          <Campo etiqueta="Fecha de fin (AAAA-MM-DD)" value={e.fecha_fin} onChange={(ev) => edu(i, { fecha_fin: ev.target.value })} />
          <div className="sm:col-span-2"><Casilla etiqueta="Lo estoy cursando" checked={e.en_curso} onChange={(ev) => edu(i, { en_curso: ev.target.checked })} /></div>
        </Tarjeta>
      ))}

      <AreaTexto etiqueta="Habilidades (separadas por comas)" rows={2} value={habilidades} onChange={(e) => setHabilidades(e.target.value)} />
      {b.idiomas.length > 0 && (
        <p className="text-sm text-texto-sec">Idiomas: {b.idiomas.map((i) => i.idioma + (i.nivel ? ` (${i.nivel})` : "")).join(", ")}</p>
      )}
      {b.dudosos.length > 0 && (
        <Casilla etiqueta="Revisé los datos que el agente marcó como dudosos" checked={revise} onChange={(e) => setRevise(e.target.checked)} />
      )}
      <div className="flex flex-col gap-2 sm:flex-row">
        <Boton
          variante="primario" cargando={guardando}
          onClick={async () => { setGuardando(true); await onConfirmar(paraGuardar(b, habilidades), revise); setGuardando(false); }}
        >
          Confirmar y guardar en mi perfil
        </Boton>
        <Boton onClick={onRechazar}>Rechazar</Boton>
      </div>
    </section>
  );
}

export function Importar({ origen }: { origen: Origen }) {
  const navegar = useNavigate();
  const cliente = useQueryClient();
  const entrada = useRef<HTMLInputElement>(null);
  const [archivo, setArchivo] = useState<File | null>(null);
  const [mensaje, setMensaje] = useState<Resultado>(null);
  const [fallo, setFallo] = useState<{ error?: string; sinTexto?: boolean } | null>(null);
  const [borrador, setBorrador] = useState<{ datos: Borrador; ronda: number } | null>(null);
  const [trabajando, setTrabajando] = useState(false);
  const [guardandoHoja, setGuardandoHoja] = useState(false);

  const extraer = async () => {
    if (!archivo) return;
    setTrabajando(true); setMensaje(null); setFallo(null); setBorrador(null);
    const r = await api.subir<{ sin_texto: boolean; borrador: Borrador | null }>("POST", "/importacion/extraer", archivo, { origen });
    setTrabajando(false);
    if (r.ok && r.datos.borrador) setBorrador({ datos: aBorrador(r.datos.borrador as never), ronda: Date.now() });
    else if (!r.ok) setFallo({ error: r.mensaje ?? "" });
    else setFallo({ sinTexto: true });
  };

  const guardarHoja = async () => {
    if (!archivo) return;
    setGuardandoHoja(true);
    const r = await api.subir("PUT", "/perfil/hoja-de-vida", archivo);
    setGuardandoHoja(false);
    setMensaje(r);
    if (r.ok) cliente.invalidateQueries({ queryKey: ["hoja-de-vida"] });
  };

  const confirmar = async (b: ReturnType<typeof paraGuardar>, revise: boolean) => {
    const r = await api.post("/importacion/confirmar", { borrador: b, revise });
    setMensaje(r);
    if (r.ok) {
      setBorrador(null);
      cliente.invalidateQueries({ queryKey: ["perfil"] });
    }
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const esCv = origen === "cv";
  return (
    <>
      <Link to="/perfil" className="mb-4 inline-flex items-center gap-1 text-sm text-texto-sec hover:text-primario">
        <ArrowLeft className="size-4" aria-hidden /> Volver
      </Link>
      {esCv ? (
        <Encabezado titulo="Sube tu hoja de vida" descripcion="PDF o Word (.docx), máximo 5 MB." />
      ) : (
        <Encabezado
          titulo="Importar desde LinkedIn"
          descripcion={
            <>1. En LinkedIn abre tu perfil, elige <strong>Más</strong> y luego <strong>Guardar en PDF</strong>.<br />
              2. Sube aquí ese PDF. El agente leerá tu experiencia, educación y aptitudes.</>
          }
        />
      )}

      <div className="flex flex-col gap-6">
        {mensaje?.mensaje && (
          <div className="flex flex-col gap-2">
            <Mensaje resultado={mensaje} />
            {mensaje.ok && mensaje.mensaje.startsWith("Guardaste tu perfil") && (
              <div><Boton variante="texto" onClick={() => navegar("/perfil/manual")}>Ver mi perfil</Boton></div>
            )}
          </div>
        )}

        {esCv && <HojaGuardada />}

        <Tarjeta className="flex flex-col gap-4">
          <label htmlFor={`archivo-${origen}`} className="text-sm font-medium">
            {esCv ? "Arrastra tu hoja de vida aquí" : "Arrastra el PDF de tu perfil de LinkedIn aquí"}
          </label>
          <div
            className="flex flex-col items-center gap-2 rounded-[var(--radius-control)] border border-dashed border-borde bg-fondo px-4 py-8 text-center"
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => { e.preventDefault(); const f = e.dataTransfer.files[0]; if (f) setArchivo(f); }}
          >
            <Upload className="size-6 text-texto-tenue" aria-hidden />
            <p className="text-sm text-texto-sec">{archivo ? archivo.name : "Arrastra el archivo o elígelo de tu equipo"}</p>
            <input
              ref={entrada} id={`archivo-${origen}`} type="file" className="sr-only"
              accept={esCv ? ".pdf,.docx" : ".pdf"}
              onChange={(e) => setArchivo(e.target.files?.[0] ?? null)}
            />
            <Boton variante="texto" onClick={() => entrada.current?.click()}>Elegir archivo</Boton>
          </div>
          {archivo && (
            <div className="flex flex-col gap-2 sm:flex-row">
              {esCv && <Boton onClick={guardarHoja} cargando={guardandoHoja}>Guardar en mi perfil</Boton>}
              <Boton variante="primario" icono={Sparkles} onClick={extraer} disabled={trabajando}>Extraer mis datos con el agente</Boton>
            </div>
          )}
        </Tarjeta>

        {trabajando && <AgenteTrabajando texto="El agente está leyendo tu archivo..." />}
        {fallo?.error && <Aviso tipo="error">{fallo.error}</Aviso>}
        {fallo?.sinTexto && (
          <div className="flex flex-col gap-2">
            <Aviso tipo="aviso">
              No pude extraer información: el PDF no tiene texto seleccionable (puede ser un escaneo). Completa tu perfil manualmente o sube otra versión del archivo.
            </Aviso>
            <div><Boton onClick={() => navegar("/perfil/manual")}>Llenar mi perfil manualmente</Boton></div>
          </div>
        )}

        {borrador && (
          <Revision
            key={borrador.ronda}
            inicial={borrador.datos}
            onConfirmar={async (b, revise) => {
              if (b.dudosos.length && !revise) {
                setMensaje({ ok: false, mensaje: "Confirma que revisaste los datos que el agente marcó como dudosos." });
                window.scrollTo({ top: 0, behavior: "smooth" });
                return;
              }
              await confirmar(b, revise);
            }}
            onRechazar={() => {
              setBorrador(null);
              setMensaje({ ok: true, mensaje: "Rechazaste la propuesta del agente: tu perfil no cambió." });
              window.scrollTo({ top: 0, behavior: "smooth" });
            }}
          />
        )}
      </div>
    </>
  );
}
