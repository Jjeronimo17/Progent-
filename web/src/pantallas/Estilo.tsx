// /_estilo: tokens y componentes base, para que Jerónimo apruebe la dirección visual.
import { useState } from "react";
import { Bookmark, Inbox, Sparkles } from "lucide-react";
import {
  AgenteTrabajando, AreaTexto, Aviso, BarraNivel, BloqueDudoso, Boton, Campo, Casilla, Encabezado,
  EstadoVacio, EsqueletoTarjetas, ETAPAS, EtiquetaAgente, EtiquetaEtapa, Selector, Tarjeta,
} from "../componentes/ui";

const COLORES: [string, string, string][] = [
  ["Primario", "--color-primario", "#4F46E5"],
  ["Primario hover", "--color-primario-hover", "#4338CA"],
  ["Primario suave", "--color-primario-suave", "#EEF2FF"],
  ["Acento", "--color-acento", "#14B8A6"],
  ["Acento suave", "--color-acento-suave", "#F0FDFA"],
  ["Texto", "--color-texto", "#0F172A"],
  ["Texto secundario", "--color-texto-sec", "#475569"],
  ["Texto tenue", "--color-texto-tenue", "#94A3B8"],
  ["Fondo", "--color-fondo", "#F8FAFC"],
  ["Superficie", "--color-superficie", "#FFFFFF"],
  ["Borde", "--color-borde", "#E2E8F0"],
  ["Éxito", "--color-exito", "#10B981"],
  ["Aviso", "--color-aviso", "#F59E0B"],
  ["Error", "--color-error", "#F43F5E"],
  ["Info", "--color-info", "#0EA5E9"],
];

function Seccion({ titulo, children }: { titulo: string; children: React.ReactNode }) {
  return (
    <section className="flex flex-col gap-4">
      <h2 className="text-lg font-semibold text-texto">{titulo}</h2>
      {children}
    </section>
  );
}

export function Estilo() {
  const [cargando, setCargando] = useState(false);
  return (
    <div className="mx-auto flex max-w-[1100px] flex-col gap-12 px-4 py-10 md:px-10">
      <Encabezado
        titulo="Guía de estilo de Progent"
        descripcion="Tokens y componentes base. Minimalista y claro: una acción principal por bloque, jerarquía con tamaño y peso de letra, y todo lo que propone el agente se ve igual en toda la app."
      />

      <Seccion titulo="Colores">
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
          {COLORES.map(([nombre, variable, hex]) => (
            <div key={variable} className="overflow-hidden rounded-[var(--radius-tarjeta)] border border-borde bg-superficie">
              <div className="h-14" style={{ background: `var(${variable})` }} />
              <div className="p-3">
                <p className="text-sm font-medium">{nombre}</p>
                <p className="text-xs text-texto-sec">{hex}</p>
              </div>
            </div>
          ))}
        </div>
      </Seccion>

      <Seccion titulo="Tipografía (Inter · 12 / 14 / 16 / 20 / 24 / 32)">
        <Tarjeta className="flex flex-col gap-2">
          <p className="text-2xl font-semibold tracking-tight">32 · Título de página</p>
          <p className="text-xl font-semibold">24 · Título de sección</p>
          <p className="text-lg font-medium">20 · Subtítulo</p>
          <p className="text-base">16 · Texto de lectura</p>
          <p className="text-sm text-texto-sec">14 · Texto de interfaz y descripciones</p>
          <p className="text-xs text-texto-tenue">12 · Ayudas y metadatos</p>
        </Tarjeta>
      </Seccion>

      <Seccion titulo="Botones">
        <div className="flex flex-wrap gap-3">
          <Boton variante="primario" icono={Sparkles}>Acción principal</Boton>
          <Boton>Secundario</Boton>
          <Boton variante="texto">De texto</Boton>
          <Boton variante="peligro">Descartar</Boton>
          <Boton variante="primario" cargando={cargando} onClick={() => { setCargando(true); setTimeout(() => setCargando(false), 1500); }}>
            Con carga
          </Boton>
          <Boton disabled>Deshabilitado</Boton>
        </div>
      </Seccion>

      <Seccion titulo="Campos (cada uno con su etiqueta)">
        <Tarjeta className="grid gap-4 sm:grid-cols-2">
          <Campo etiqueta="Nombre completo *" placeholder="Ej.: Laura Gómez" />
          <Campo etiqueta="Correo de contacto *" error="Escribe un correo de contacto válido." defaultValue="laura" />
          <Selector etiqueta="Modalidad" opciones={["Sin especificar", "Hibrido", "Presencial", "Virtual"]} />
          <Campo etiqueta="Fecha de inicio *" type="date" />
          <div className="sm:col-span-2"><AreaTexto etiqueta="Descripción de funciones *" ayuda="Lo que hacías en el cargo." /></div>
          <Casilla etiqueta="Trabajo aquí actualmente" />
        </Tarjeta>
      </Seccion>

      <Seccion titulo="Etapas del proceso">
        <div className="flex flex-wrap gap-2">{ETAPAS.map((e) => <EtiquetaEtapa key={e} etapa={e} />)}</div>
      </Seccion>

      <Seccion titulo="Lo que propone el agente">
        <Tarjeta className="flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <p className="font-medium">Desarrollador Backend Python · Andina Software</p>
            <EtiquetaAgente />
          </div>
          <p className="text-sm text-texto-sec">Coincide con tu experiencia en Python y APIs REST.</p>
          <BloqueDudoso titulo="Recomendación de menor relevancia">
            El agente no quedó seguro: solo coincide en parte con los requisitos.
          </BloqueDudoso>
          <BarraNivel nivel="Media" porcentaje={62} />
          <div className="flex flex-wrap gap-2">
            <Boton variante="primario">Me interesa</Boton>
            <Boton icono={Bookmark}>Guardar</Boton>
            <Boton variante="texto">Descartar</Boton>
          </div>
        </Tarjeta>
        <AgenteTrabajando texto="El agente está leyendo tu archivo..." />
      </Seccion>

      <Seccion titulo="Avisos">
        <div className="grid gap-3 sm:grid-cols-2">
          <Aviso tipo="exito">Guardaste esta vacante. La encuentras en Guardadas.</Aviso>
          <Aviso tipo="error">Correo o contraseña incorrectos.</Aviso>
          <Aviso tipo="aviso">La entrevista del 20/11/2026 a las 10:00 ya pasó.</Aviso>
          <Aviso tipo="info">Es un borrador: nada se guarda hasta que lo confirmes.</Aviso>
        </div>
      </Seccion>

      <Seccion titulo="Estados vacíos y de carga">
        <div className="grid gap-4 md:grid-cols-2">
          <EstadoVacio
            icono={Inbox}
            titulo="Sin postulaciones en esta etapa."
            texto="Cuando te postules a una vacante, la verás aquí."
            accion={<Boton variante="primario">Ver vacantes</Boton>}
          />
          <EsqueletoTarjetas n={2} />
        </div>
      </Seccion>
    </div>
  );
}
