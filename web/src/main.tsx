import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { MutationCache, QueryCache, QueryClient, QueryClientProvider } from "@tanstack/react-query";
import "./estilos.css";
import { SinSesion } from "./api/cliente";
import { Layout } from "./componentes/Layout";
import { ConSesion } from "./sesion";
import { Login } from "./pantallas/Login";
import { Estilo } from "./pantallas/Estilo";
import { Eleccion } from "./pantallas/perfil/Eleccion";
import { Manual } from "./pantallas/perfil/Manual";
import { Importar } from "./pantallas/perfil/Importar";
import { Mejorar } from "./pantallas/perfil/Mejorar";
import { GenerarCv } from "./pantallas/perfil/GenerarCv";
import { Listado } from "./pantallas/vacantes/Listado";
import { DetalleVacante } from "./pantallas/vacantes/Detalle";
import { Guardadas } from "./pantallas/Guardadas";
import { Recomendaciones } from "./pantallas/Recomendaciones";
import { Notificaciones } from "./pantallas/Notificaciones";
import { Postulaciones } from "./pantallas/Postulaciones";

// Si la sesión expira en medio de algo, se vuelve al login.
const alExpirar = (error: unknown) => {
  if (error instanceof SinSesion) {
    cliente.setQueryData(["sesion"], null);
  }
};
const cliente: QueryClient = new QueryClient({
  queryCache: new QueryCache({ onError: alExpirar }),
  mutationCache: new MutationCache({ onError: alExpirar }),
  defaultOptions: { queries: { retry: false, refetchOnWindowFocus: false } },
});

createRoot(document.getElementById("raiz")!).render(
  <StrictMode>
    <QueryClientProvider client={cliente}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/_estilo" element={<Estilo />} />
          <Route element={<ConSesion><Layout /></ConSesion>}>
            <Route path="/perfil" element={<Eleccion />} />
            <Route path="/perfil/manual" element={<Manual />} />
            <Route path="/perfil/hoja-de-vida" element={<Importar key="cv" origen="cv" />} />
            <Route path="/perfil/linkedin" element={<Importar key="linkedin" origen="linkedin" />} />
            <Route path="/perfil/mejorar" element={<Mejorar />} />
            <Route path="/perfil/generar-cv" element={<GenerarCv />} />
            <Route path="/vacantes" element={<Listado />} />
            <Route path="/vacantes/:id" element={<DetalleVacante />} />
            <Route path="/recomendaciones" element={<Recomendaciones />} />
            <Route path="/guardadas" element={<Guardadas />} />
            <Route path="/postulaciones" element={<Postulaciones />} />
            <Route path="/notificaciones" element={<Notificaciones />} />
          </Route>
          <Route path="*" element={<Navigate to="/perfil" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
);
