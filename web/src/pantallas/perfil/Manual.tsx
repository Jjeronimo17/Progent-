// Llenar el perfil a mano (PerfilFront.py): datos básicos, experiencia y educación.
import { useState, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { ArrowLeft, Briefcase, ChevronDown, GraduationCap, Plus } from "lucide-react";
import { api, type Respuesta } from "../../api/cliente";
import { AreaTexto, Aviso, Boton, Campo, Encabezado, EsqueletoTarjetas, Mensaje, Selector, Tarjeta } from "../../componentes/ui";
import { mesAnio, obligatorios, usePerfil, useRefrescarPerfil } from "../../lib/perfil";
import { useSesion } from "../../sesion";

const MODALIDADES = ["Sin especificar", "Hibrido", "Presencial", "Virtual"];
const ESTADOS_ESTUDIO = ["Cursando", "Graduado", "Aplazado", "Incompleto"];
const hoy = new Date().toISOString().slice(0, 10);

type Resultado = Pick<Respuesta, "ok" | "mensaje"> | null;

function errorDe(errores: object) {
  return (errores as { formulario?: { message?: string } }).formulario?.message;
}

function Seccion({ titulo, icono, children }: { titulo: string; icono: ReactNode; children: ReactNode }) {
  return (
    <section className="flex flex-col gap-4">
      <h2 className="flex items-center gap-2 text-lg font-semibold text-texto">{icono}{titulo}</h2>
      {children}
    </section>
  );
}

// ---------------------------------------------------------------- Datos básicos
const esquemaDatos = z
  .object({ nombre: z.string(), edad: z.string(), telefono: z.string(), correo_contacto: z.string(), ubicacion: z.string(), ocupacion: z.string() })
  .superRefine(obligatorios({ nombre: "Nombre completo", correo_contacto: "Correo de contacto", ubicacion: "Ubicación", ocupacion: "Ocupación" } as never))
  .superRefine((d, ctx) => {
    if (d.correo_contacto.trim() && !d.correo_contacto.includes("@") && d.nombre.trim() && d.ubicacion.trim() && d.ocupacion.trim())
      ctx.addIssue({ code: z.ZodIssueCode.custom, path: ["formulario"], message: "Escribe un correo de contacto válido." });
  });

function DatosBasicos({ correo, alGuardar }: { correo: string; alGuardar: (r: Resultado) => void }) {
  const [resultado, setResultado] = useState<Resultado>(null);
  const { register, handleSubmit, formState } = useForm<z.infer<typeof esquemaDatos>>({
    resolver: zodResolver(esquemaDatos),
    defaultValues: { nombre: "", edad: "", telefono: "", correo_contacto: correo, ubicacion: "", ocupacion: "" },
  });
  const enviar = handleSubmit(async (d) => {
    const r = await api.post("/perfil/datos", { ...d, edad: d.edad ? Number(d.edad) : null });
    r.ok ? alGuardar(r) : setResultado(r);
  });
  const error = errorDe(formState.errors);
  return (
    <Tarjeta>
      <form onSubmit={enviar} noValidate className="grid gap-4 sm:grid-cols-2">
        <Campo etiqueta="Nombre completo *" maxLength={60} {...register("nombre")} />
        <Campo etiqueta="Edad" type="number" min={14} max={100} {...register("edad")} />
        <Campo etiqueta="Teléfono" maxLength={50} {...register("telefono")} />
        <Campo etiqueta="Correo de contacto *" type="email" maxLength={200} {...register("correo_contacto")} />
        <Campo etiqueta="Ubicación *" placeholder="Ciudad, país" maxLength={100} {...register("ubicacion")} />
        <Campo etiqueta="Ocupación *" placeholder="Ej.: Estudiante de Ingeniería de Sistemas" {...register("ocupacion")} />
        <div className="flex flex-col gap-3 sm:col-span-2">
          {error && <Aviso tipo="error">{error}</Aviso>}
          <Mensaje resultado={resultado} />
          <div><Boton type="submit" variante="primario" cargando={formState.isSubmitting}>Guardar datos básicos</Boton></div>
        </div>
      </form>
    </Tarjeta>
  );
}

// ---------------------------------------------------------------- Formularios desplegables
function Desplegable({ titulo, children }: { titulo: string; children: (cerrar: () => void) => ReactNode }) {
  const [abierto, setAbierto] = useState(false);
  return (
    <div className="rounded-[var(--radius-tarjeta)] border border-borde bg-superficie">
      <button
        type="button"
        aria-expanded={abierto}
        onClick={() => setAbierto(!abierto)}
        className="flex w-full items-center gap-2 px-5 h-12 text-sm font-medium text-primario cursor-pointer"
      >
        <Plus className="size-4" aria-hidden /> <span className="flex-1 text-left">{titulo}</span>
        <ChevronDown className={`size-4 transition-transform ${abierto ? "rotate-180" : ""}`} aria-hidden />
      </button>
      {abierto && <div className="border-t border-borde p-5">{children(() => setAbierto(false))}</div>}
    </div>
  );
}

const esquemaExperiencia = z
  .object({
    empresa: z.string(), cargo: z.string(), fecha_inicio: z.string(), fecha_fin: z.string(),
    funciones: z.string(), habilidades: z.string(), logros: z.string(), ubicacion: z.string(), modalidad: z.string(),
  })
  .superRefine(obligatorios({ empresa: "Empresa", cargo: "Cargo", fecha_inicio: "Fecha de inicio", funciones: "Descripción de funciones", habilidades: "Habilidades" } as never));

function FormExperiencia({ alGuardar }: { alGuardar: (r: Resultado) => void }) {
  const [resultado, setResultado] = useState<Resultado>(null);
  const { register, handleSubmit, formState } = useForm<z.infer<typeof esquemaExperiencia>>({
    resolver: zodResolver(esquemaExperiencia),
    defaultValues: { empresa: "", cargo: "", fecha_inicio: "", fecha_fin: "", funciones: "", habilidades: "", logros: "", ubicacion: "", modalidad: MODALIDADES[0] },
  });
  const enviar = handleSubmit(async (d) => {
    const r = await api.post("/perfil/experiencia", { ...d, fecha_fin: d.fecha_fin || null });
    r.ok ? alGuardar(r) : setResultado(r);
  });
  const error = errorDe(formState.errors);
  return (
    <form onSubmit={enviar} noValidate className="grid gap-4 sm:grid-cols-2">
      <Campo etiqueta="Empresa *" maxLength={100} {...register("empresa")} />
      <Campo etiqueta="Cargo *" maxLength={100} {...register("cargo")} />
      <Campo etiqueta="Fecha de inicio *" type="date" min="1950-01-01" max={hoy} {...register("fecha_inicio")} />
      <Campo etiqueta="Fecha de finalización" type="date" min="1950-01-01" max={hoy} ayuda="Déjala vacía si todavía trabajas aquí." {...register("fecha_fin")} />
      <div className="sm:col-span-2"><AreaTexto etiqueta="Descripción de funciones *" {...register("funciones")} /></div>
      <Campo etiqueta="Habilidades *" placeholder="Separadas por comas" {...register("habilidades")} />
      <Campo etiqueta="Ubicación de la empresa" maxLength={100} {...register("ubicacion")} />
      <div className="sm:col-span-2"><AreaTexto etiqueta="Logros" rows={3} {...register("logros")} /></div>
      <Selector etiqueta="Modalidad" opciones={MODALIDADES} {...register("modalidad")} />
      <div className="flex flex-col gap-3 sm:col-span-2">
        {error && <Aviso tipo="error">{error}</Aviso>}
        <Mensaje resultado={resultado} />
        <div><Boton type="submit" variante="primario" cargando={formState.isSubmitting}>Guardar experiencia</Boton></div>
      </div>
    </form>
  );
}

const esquemaEducacion = z
  .object({ institucion: z.string(), titulo: z.string(), nivel: z.string(), campo: z.string(), fecha_inicio: z.string(), fecha_fin: z.string(), estado: z.string(), logros: z.string() })
  .superRefine(obligatorios({ institucion: "Institución", titulo: "Título o carrera", fecha_inicio: "Fecha de inicio" } as never));

function FormEducacion({ alGuardar }: { alGuardar: (r: Resultado) => void }) {
  const [resultado, setResultado] = useState<Resultado>(null);
  const { register, handleSubmit, formState } = useForm<z.infer<typeof esquemaEducacion>>({
    resolver: zodResolver(esquemaEducacion),
    defaultValues: { institucion: "", titulo: "", nivel: "", campo: "", fecha_inicio: "", fecha_fin: "", estado: ESTADOS_ESTUDIO[0], logros: "" },
  });
  const enviar = handleSubmit(async (d) => {
    const r = await api.post("/perfil/educacion", { ...d, fecha_fin: d.fecha_fin || null });
    r.ok ? alGuardar(r) : setResultado(r);
  });
  const error = errorDe(formState.errors);
  return (
    <form onSubmit={enviar} noValidate className="grid gap-4 sm:grid-cols-2">
      <Campo etiqueta="Institución *" maxLength={100} {...register("institucion")} />
      <Campo etiqueta="Título o carrera *" maxLength={200} {...register("titulo")} />
      <Campo etiqueta="Nivel" placeholder="Ej.: Pregrado" maxLength={150} {...register("nivel")} />
      <Campo etiqueta="Campo de estudio" maxLength={200} {...register("campo")} />
      <Campo etiqueta="Fecha de inicio *" type="date" min="1950-01-01" max={hoy} {...register("fecha_inicio")} />
      <Campo etiqueta="Fecha de finalización" type="date" min="1950-01-01" ayuda="Déjala vacía si todavía estudias aquí." {...register("fecha_fin")} />
      <Selector etiqueta="Estado *" opciones={ESTADOS_ESTUDIO} {...register("estado")} />
      <div className="sm:col-span-2"><AreaTexto etiqueta="Logros" rows={3} {...register("logros")} /></div>
      <div className="flex flex-col gap-3 sm:col-span-2">
        {error && <Aviso tipo="error">{error}</Aviso>}
        <Mensaje resultado={resultado} />
        <div><Boton type="submit" variante="primario" cargando={formState.isSubmitting}>Guardar educación</Boton></div>
      </div>
    </form>
  );
}

// ---------------------------------------------------------------- Pantalla
export function Manual() {
  const { data: perfil, isLoading, error } = usePerfil();
  const { data: correoSesion } = useSesion();
  const refrescar = useRefrescarPerfil();
  const [mensaje, setMensaje] = useState<Resultado>(null);
  // Cada vez que se guarda, el formulario vuelve a salir vacío (como el contador de Streamlit).
  const [ronda, setRonda] = useState(0);
  const guardado = (r: Resultado) => {
    setMensaje(r);
    setRonda((n) => n + 1);
    refrescar();
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <>
      <Link to="/perfil" className="mb-4 inline-flex items-center gap-1 text-sm text-texto-sec hover:text-primario">
        <ArrowLeft className="size-4" aria-hidden /> Volver
      </Link>
      <Encabezado titulo="Llena tu perfil" descripcion="Los campos con * son obligatorios." />
      {mensaje?.ok && mensaje.mensaje && <Aviso tipo="exito" className="mb-6">{mensaje.mensaje}</Aviso>}

      {isLoading ? (
        <EsqueletoTarjetas n={3} />
      ) : error || !perfil ? (
        <Aviso tipo="error">{(error as Error)?.message}</Aviso>
      ) : (
        <div className="flex flex-col gap-10">
          <Seccion titulo="Datos básicos" icono={null}>
            {perfil.datos ? (
              <Tarjeta>
                <p className="text-base font-semibold">{perfil.datos.Nombre}</p>
                <p className="text-sm text-texto">{perfil.datos.Ocupacion}</p>
                <p className="mt-1 text-sm text-texto-sec">
                  {perfil.datos.Ubicacion} · {perfil.datos.Correo_contacto}
                  {perfil.datos.Telefono ? ` · ${perfil.datos.Telefono}` : ""}
                </p>
              </Tarjeta>
            ) : (
              <DatosBasicos key={ronda} correo={correoSesion ?? ""} alGuardar={guardado} />
            )}
          </Seccion>

          <Seccion titulo="Experiencia laboral" icono={<Briefcase className="size-5 text-texto-tenue" aria-hidden />}>
            {perfil.experiencia.length ? (
              <ul className="flex flex-col gap-2">
                {perfil.experiencia.map((e) => (
                  <li key={e.ID}>
                    <Tarjeta as="div" className="p-4">
                      <p className="text-sm"><strong className="font-semibold">{e.Titulo_puesto}</strong> en {e.Nombre_empresa}</p>
                      <p className="text-xs text-texto-sec">{mesAnio(e.Fecha_inicio)} a {mesAnio(e.Fecha_finalizacion)}</p>
                    </Tarjeta>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-texto-sec">Todavía no has agregado experiencia laboral.</p>
            )}
            <Desplegable key={`exp-${ronda}`} titulo="Agregar experiencia">{() => <FormExperiencia alGuardar={guardado} />}</Desplegable>
          </Seccion>

          <Seccion titulo="Educación" icono={<GraduationCap className="size-5 text-texto-tenue" aria-hidden />}>
            {perfil.educacion.length ? (
              <ul className="flex flex-col gap-2">
                {perfil.educacion.map((e) => (
                  <li key={e.Id_educacion}>
                    <Tarjeta as="div" className="p-4">
                      <p className="text-sm"><strong className="font-semibold">{e.Titulo_Carrera_Grado}</strong> en {e.Institucion_educativa}</p>
                      <p className="text-xs text-texto-sec">{e.Estado_estudio}, desde {mesAnio(e.Fecha_inicio)}</p>
                    </Tarjeta>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-texto-sec">Todavía no has agregado educación.</p>
            )}
            <Desplegable key={`edu-${ronda}`} titulo="Agregar educación">{() => <FormEducacion alGuardar={guardado} />}</Desplegable>
          </Seccion>
        </div>
      )}
    </>
  );
}
