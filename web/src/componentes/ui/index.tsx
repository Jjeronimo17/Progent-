// Componentes base de Progent. Todos usan los tokens de estilos.css.
import {
  forwardRef, useId,
  type ButtonHTMLAttributes, type InputHTMLAttributes, type ReactNode,
  type SelectHTMLAttributes, type TextareaHTMLAttributes,
} from "react";
import { AlertTriangle, CheckCircle2, Info, Loader2, Sparkles, XCircle, type LucideIcon } from "lucide-react";

const cx = (...c: (string | false | null | undefined)[]) => c.filter(Boolean).join(" ");

// ---------------------------------------------------------------- Botón
type Variante = "primario" | "secundario" | "texto" | "peligro";

const estilosBoton: Record<Variante, string> = {
  primario: "bg-primario text-white hover:bg-primario-hover shadow-suave",
  secundario: "bg-superficie text-texto border border-borde hover:bg-fondo hover:border-texto-tenue",
  texto: "text-primario hover:bg-primario-suave",
  peligro: "bg-superficie text-error-fuerte border border-borde hover:bg-error-suave",
};

export const Boton = forwardRef<
  HTMLButtonElement,
  ButtonHTMLAttributes<HTMLButtonElement> & { variante?: Variante; cargando?: boolean; icono?: LucideIcon; ancho?: boolean }
>(function Boton({ variante = "secundario", cargando, icono: Icono, ancho, className, children, disabled, ...props }, ref) {
  return (
    <button
      ref={ref}
      type={props.type ?? "button"}
      disabled={disabled || cargando}
      className={cx(
        "inline-flex items-center justify-center gap-2 rounded-[var(--radius-control)] px-4 h-10 text-sm font-medium",
        "transition-colors disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer",
        estilosBoton[variante],
        ancho && "w-full",
        className,
      )}
      {...props}
    >
      {cargando ? <Loader2 className="size-4 animate-spin" aria-hidden /> : Icono && <Icono className="size-4" aria-hidden />}
      {children}
    </button>
  );
});

// ---------------------------------------------------------------- Campos (siempre con <label>)
type BaseCampo = { etiqueta: string; error?: string; ayuda?: ReactNode };

function Envoltura({ id, etiqueta, error, ayuda, children }: BaseCampo & { id: string; children: ReactNode }) {
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className="text-sm font-medium text-texto">{etiqueta}</label>
      {children}
      {ayuda && !error && <p className="text-xs text-texto-sec">{ayuda}</p>}
      {error && <p className="text-xs text-error-fuerte" role="alert">{error}</p>}
    </div>
  );
}

const estiloControl =
  "w-full rounded-[var(--radius-control)] border border-borde bg-superficie px-3 text-sm text-texto " +
  "placeholder:text-texto-tenue transition-colors hover:border-texto-tenue focus:border-primario focus:outline-none " +
  "focus:ring-2 focus:ring-primario-suave aria-[invalid=true]:border-error";

export const Campo = forwardRef<HTMLInputElement, BaseCampo & InputHTMLAttributes<HTMLInputElement>>(
  function Campo({ etiqueta, error, ayuda, id, className, ...props }, ref) {
    const auto = useId();
    const idc = id ?? auto;
    return (
      <Envoltura id={idc} etiqueta={etiqueta} error={error} ayuda={ayuda}>
        <input ref={ref} id={idc} aria-invalid={!!error} className={cx(estiloControl, "h-10", className)} {...props} />
      </Envoltura>
    );
  },
);

export const AreaTexto = forwardRef<HTMLTextAreaElement, BaseCampo & TextareaHTMLAttributes<HTMLTextAreaElement>>(
  function AreaTexto({ etiqueta, error, ayuda, id, className, ...props }, ref) {
    const auto = useId();
    const idc = id ?? auto;
    return (
      <Envoltura id={idc} etiqueta={etiqueta} error={error} ayuda={ayuda}>
        <textarea ref={ref} id={idc} aria-invalid={!!error} rows={4} className={cx(estiloControl, "py-2", className)} {...props} />
      </Envoltura>
    );
  },
);

export const Selector = forwardRef<
  HTMLSelectElement,
  BaseCampo & SelectHTMLAttributes<HTMLSelectElement> & { opciones: (string | { valor: string; texto: string })[] }
>(function Selector({ etiqueta, error, ayuda, id, opciones, className, ...props }, ref) {
  const auto = useId();
  const idc = id ?? auto;
  return (
    <Envoltura id={idc} etiqueta={etiqueta} error={error} ayuda={ayuda}>
      <select ref={ref} id={idc} aria-invalid={!!error} className={cx(estiloControl, "h-10", className)} {...props}>
        {opciones.map((o) => {
          const { valor, texto } = typeof o === "string" ? { valor: o, texto: o } : o;
          return <option key={valor} value={valor}>{texto}</option>;
        })}
      </select>
    </Envoltura>
  );
});

export function Casilla({ etiqueta, ...props }: { etiqueta: string } & InputHTMLAttributes<HTMLInputElement>) {
  const id = useId();
  return (
    <div className="flex items-start gap-2">
      <input id={id} type="checkbox" className="mt-0.5 size-4 accent-[var(--color-primario)]" {...props} />
      <label htmlFor={id} className="text-sm text-texto">{etiqueta}</label>
    </div>
  );
}

// ---------------------------------------------------------------- Tarjeta y títulos
export function Tarjeta({ children, className, as: Etiqueta = "section" }: { children: ReactNode; className?: string; as?: "section" | "div" | "article" }) {
  return (
    <Etiqueta className={cx("rounded-[var(--radius-tarjeta)] border border-borde bg-superficie p-5 shadow-suave", className)}>
      {children}
    </Etiqueta>
  );
}

export function Encabezado({ titulo, descripcion, accion }: { titulo: string; descripcion?: ReactNode; accion?: ReactNode }) {
  return (
    <header className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h1 className="text-xl font-semibold tracking-tight text-texto sm:text-2xl">{titulo}</h1>
        {descripcion && <p className="mt-1 max-w-2xl text-sm text-texto-sec">{descripcion}</p>}
      </div>
      {accion}
    </header>
  );
}

// ---------------------------------------------------------------- Etapas (#23)
export const ETAPAS = ["Postulado", "En revisión", "Entrevista", "Oferta", "Rechazado", "Retirado"] as const;
const colorEtapa: Record<string, string> = {
  Postulado: "var(--color-etapa-postulado)",
  "En revisión": "var(--color-etapa-revision)",
  Entrevista: "var(--color-etapa-entrevista)",
  Oferta: "var(--color-etapa-oferta)",
  Rechazado: "var(--color-etapa-rechazado)",
  Retirado: "var(--color-etapa-retirado)",
};

/** En la base los estados van sin tilde ("En revision"); en pantalla, con tilde. */
export const etiquetaEstado = (estado: string) => (estado === "En revision" ? "En revisión" : estado);
export const colorDeEtapa = (estado: string) => colorEtapa[etiquetaEstado(estado)] ?? "var(--color-texto-tenue)";

export function EtiquetaEtapa({ etapa: valor }: { etapa: string }) {
  const etapa = etiquetaEstado(valor);
  const color = colorEtapa[etapa] ?? "var(--color-texto-tenue)";
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium text-texto"
      style={{ background: `color-mix(in srgb, ${color} 12%, white)` }}
    >
      <span className="size-2 rounded-full" style={{ background: color }} aria-hidden />
      {etapa}
    </span>
  );
}

// ---------------------------------------------------------------- Lo que viene del agente
export function EtiquetaAgente({ texto = "Sugerencia del agente" }: { texto?: string }) {
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-primario-suave px-2.5 py-0.5 text-xs font-medium text-primario">
      <Sparkles className="size-3.5" aria-hidden />
      {texto}
    </span>
  );
}

/** El mismo bloque ámbar en toda la app para lo que el agente marcó como dudoso. */
export function BloqueDudoso({ children, titulo }: { children: ReactNode; titulo?: string }) {
  return (
    <div className="flex gap-3 rounded-[var(--radius-control)] border border-aviso/40 bg-aviso-suave p-3 text-sm text-aviso-fuerte" role="note">
      <AlertTriangle className="mt-0.5 size-4 shrink-0" aria-hidden />
      <div>
        {titulo && <p className="font-medium">{titulo}</p>}
        <div className="text-texto">{children}</div>
      </div>
    </div>
  );
}

/** Mientras el agente trabaja: dice qué está haciendo (no bloquea la página). */
export function AgenteTrabajando({ texto }: { texto: string }) {
  return (
    <div className="flex items-center gap-3 rounded-[var(--radius-control)] bg-primario-suave p-4 text-sm text-primario" role="status" aria-live="polite">
      <Loader2 className="size-4 animate-spin" aria-hidden />
      {texto}
    </div>
  );
}

// ---------------------------------------------------------------- Avisos
type TipoAviso = "exito" | "error" | "aviso" | "info";
const avisos: Record<TipoAviso, { clase: string; Icono: LucideIcon }> = {
  exito: { clase: "bg-exito-suave text-exito-fuerte border-exito/30", Icono: CheckCircle2 },
  error: { clase: "bg-error-suave text-error-fuerte border-error/30", Icono: XCircle },
  aviso: { clase: "bg-aviso-suave text-aviso-fuerte border-aviso/40", Icono: AlertTriangle },
  info: { clase: "bg-info-suave text-info-fuerte border-info/30", Icono: Info },
};

export function Aviso({ tipo = "info", children, className }: { tipo?: TipoAviso; children: ReactNode; className?: string }) {
  const { clase, Icono } = avisos[tipo];
  return (
    <div
      className={cx("flex gap-3 rounded-[var(--radius-control)] border p-3 text-sm", clase, className)}
      role={tipo === "error" ? "alert" : "status"}
    >
      <Icono className="mt-0.5 size-4 shrink-0" aria-hidden />
      <div className="whitespace-pre-line">{children}</div>
    </div>
  );
}

/** Un mensaje de la API: verde si ok, rojo si no. */
export function Mensaje({ resultado }: { resultado?: { ok: boolean; mensaje: string | null } | null }) {
  if (!resultado?.mensaje) return null;
  return <Aviso tipo={resultado.ok ? "exito" : "error"}>{resultado.mensaje}</Aviso>;
}

// ---------------------------------------------------------------- Estados vacíos y de carga
export function EstadoVacio({ icono: Icono = Info, titulo, texto, accion }: { icono?: LucideIcon; titulo: string; texto?: ReactNode; accion?: ReactNode }) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-[var(--radius-tarjeta)] border border-dashed border-borde bg-superficie px-6 py-10 text-center">
      <span className="grid size-11 place-items-center rounded-full bg-primario-suave text-primario">
        <Icono className="size-5" aria-hidden />
      </span>
      <p className="text-base font-medium text-texto">{titulo}</p>
      {texto && <p className="max-w-sm text-sm text-texto-sec">{texto}</p>}
      {accion}
    </div>
  );
}

export function Esqueleto({ className }: { className?: string }) {
  return <div className={cx("esqueleto rounded-[var(--radius-control)]", className)} aria-hidden />;
}

export function EsqueletoTarjetas({ n = 3 }: { n?: number }) {
  return (
    <div className="flex flex-col gap-3" aria-busy="true" aria-label="Cargando">
      {Array.from({ length: n }, (_, i) => (
        <Tarjeta key={i}>
          <Esqueleto className="h-4 w-1/3" />
          <Esqueleto className="mt-3 h-3 w-2/3" />
          <Esqueleto className="mt-2 h-3 w-1/2" />
        </Tarjeta>
      ))}
    </div>
  );
}

/** Barra de compatibilidad (#26): Alta = éxito, Media = aviso, Baja = error. */
export function BarraNivel({ nivel, porcentaje }: { nivel: "Alta" | "Media" | "Baja"; porcentaje: number }) {
  const color = { Alta: "var(--color-exito)", Media: "var(--color-aviso)", Baja: "var(--color-error)" }[nivel];
  const texto = { Alta: "text-exito-fuerte", Media: "text-aviso-fuerte", Baja: "text-error-fuerte" }[nivel];
  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-baseline justify-between text-sm">
        <span className={cx("font-semibold", texto)}>{nivel}</span>
        <span className="text-texto-sec">{porcentaje}%</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-borde" role="progressbar" aria-valuenow={porcentaje} aria-valuemin={0} aria-valuemax={100} aria-label={`Compatibilidad ${nivel}`}>
        <div className="h-full rounded-full" style={{ width: `${porcentaje}%`, background: color }} />
      </div>
    </div>
  );
}
