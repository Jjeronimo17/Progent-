// Crear cuenta / iniciar sesión (LoginFront.py). Mismos textos y validaciones.
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import * as Tabs from "@radix-ui/react-tabs";
import { useQueryClient } from "@tanstack/react-query";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { api } from "../api/cliente";
import { Aviso, Boton, Campo, Mensaje, Tarjeta } from "../componentes/ui";
import { useSesion } from "../sesion";

// La validación de la pantalla da UN mensaje para el formulario, como en Streamlit.
const esquemaRegistro = z
  .object({ correo: z.string(), contrasena: z.string() })
  .superRefine((d, ctx) => {
    const err = (message: string) => ctx.addIssue({ code: z.ZodIssueCode.custom, path: ["formulario"], message });
    if (!d.correo.trim() || !d.contrasena) return err("Completa el correo y la contraseña.");
    if (!d.correo.includes("@")) return err("Escribe un correo válido.");
    if (d.contrasena.length < 8) return err("La contraseña debe tener al menos 8 caracteres.");
  });

const esquemaLogin = z
  .object({ correo: z.string(), contrasena: z.string() })
  .superRefine((d, ctx) => {
    if (!d.correo.trim() || !d.contrasena)
      ctx.addIssue({ code: z.ZodIssueCode.custom, path: ["formulario"], message: "Escribe tu correo y tu contraseña." });
  });

type Datos = { correo: string; contrasena: string };
type Resultado = { ok: boolean; mensaje: string | null } | null;

function errorFormulario(errores: Record<string, { message?: string } | undefined>) {
  return (errores as { formulario?: { message?: string } }).formulario?.message;
}

function FormularioCrear() {
  const [resultado, setResultado] = useState<Resultado>(null);
  const { register, handleSubmit, formState } = useForm<Datos>({
    resolver: zodResolver(esquemaRegistro),
    defaultValues: { correo: "", contrasena: "" },
  });
  const enviar = handleSubmit(async (d) => setResultado(await api.post("/auth/registro", d)));
  const error = errorFormulario(formState.errors as never);

  return (
    <form onSubmit={enviar} className="flex flex-col gap-4" noValidate>
      <Campo etiqueta="Correo electrónico" type="email" autoComplete="email" {...register("correo")} />
      <Campo etiqueta="Contraseña" type="password" autoComplete="new-password" ayuda="Mínimo 8 caracteres." {...register("contrasena")} />
      {error && <Aviso tipo="error">{error}</Aviso>}
      <Mensaje resultado={resultado} />
      <Boton type="submit" variante="primario" ancho cargando={formState.isSubmitting}>Crear cuenta</Boton>
    </form>
  );
}

function FormularioEntrar() {
  const [resultado, setResultado] = useState<Resultado>(null);
  const cliente = useQueryClient();
  const navegar = useNavigate();
  const desde = (useLocation().state as { desde?: string } | null)?.desde ?? "/perfil";
  const { register, handleSubmit, formState } = useForm<Datos>({
    resolver: zodResolver(esquemaLogin),
    defaultValues: { correo: "", contrasena: "" },
  });
  const enviar = handleSubmit(async (d) => {
    const r = await api.post<{ correo: string }>("/auth/login", d);
    if (r.ok) {
      cliente.setQueryData(["sesion"], r.datos.correo);
      navegar(desde, { replace: true });
    } else {
      setResultado(r);
    }
  });
  const error = errorFormulario(formState.errors as never);

  return (
    <form onSubmit={enviar} className="flex flex-col gap-4" noValidate>
      <Campo etiqueta="Correo electrónico" type="email" autoComplete="email" {...register("correo")} />
      <Campo etiqueta="Contraseña" type="password" autoComplete="current-password" {...register("contrasena")} />
      {error && <Aviso tipo="error">{error}</Aviso>}
      <Mensaje resultado={resultado} />
      <Boton type="submit" variante="primario" ancho cargando={formState.isSubmitting}>Iniciar sesión</Boton>
    </form>
  );
}

const estiloPestana =
  "flex-1 rounded-[calc(var(--radius-control)-2px)] h-9 text-sm font-medium text-texto-sec transition-colors " +
  "data-[state=active]:bg-superficie data-[state=active]:text-texto data-[state=active]:shadow-suave cursor-pointer";

export function Login() {
  const { data: correo } = useSesion();
  if (correo) return <Navigate to="/perfil" replace />;

  return (
    <div className="grid min-h-dvh place-items-center px-4 py-10">
      <div className="w-full max-w-[420px]">
        <div className="mb-8 flex flex-col items-center gap-3 text-center">
          <img src="/icono.svg" alt="" className="size-12" />
          <div>
            <p className="text-2xl font-semibold tracking-tight text-texto">Progent</p>
            <p className="mt-1 text-sm text-texto-sec">Tu perfil profesional, con un agente que te ayuda a postularte.</p>
          </div>
        </div>

        <Tarjeta className="p-6">
          <Tabs.Root defaultValue="crear">
            <Tabs.List className="mb-6 flex gap-1 rounded-[var(--radius-control)] bg-fondo p-1" aria-label="Acceso">
              <Tabs.Trigger value="crear" className={estiloPestana}>Crear cuenta</Tabs.Trigger>
              <Tabs.Trigger value="entrar" className={estiloPestana}>Iniciar sesión</Tabs.Trigger>
            </Tabs.List>
            <Tabs.Content value="crear"><FormularioCrear /></Tabs.Content>
            <Tabs.Content value="entrar"><FormularioEntrar /></Tabs.Content>
          </Tabs.Root>

          <div className="my-5 flex items-center gap-3 text-xs text-texto-tenue">
            <span className="h-px flex-1 bg-borde" /> o <span className="h-px flex-1 bg-borde" />
          </div>

          {/* Pendiente: requiere configurar OAuth (decisión del equipo: por ahora, autenticación propia). */}
          <Boton ancho disabled title="Pendiente: requiere configurar OAuth con Google y LinkedIn.">
            Continuar con Google / LinkedIn
          </Boton>
          <p className="mt-2 text-center text-xs text-texto-tenue">Pendiente: requiere configurar OAuth con Google y LinkedIn.</p>

          {/* Pendiente: «¿Olvidaste tu contraseña?» todavía no hace nada (igual que en Streamlit). */}
          <p className="mt-4 text-center">
            <a href="#" onClick={(e) => e.preventDefault()} className="text-sm text-texto-sec underline-offset-4 hover:text-primario hover:underline">
              ¿Olvidaste tu contraseña?
            </a>
          </p>
        </Tarjeta>
      </div>
    </div>
  );
}
