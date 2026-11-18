// Vacantes: búsqueda (#9), filtros (#15), alerta (#17) y listado (#8) — VacantesFront.mostrar_listado_vacantes.
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { keepPreviousData, useQuery, useQueryClient } from "@tanstack/react-query";
import { BellPlus, ChevronDown, MapPin, Search, SearchX } from "lucide-react";
import { api, type Respuesta } from "../../api/cliente";
import { Aviso, Boton, Campo, Encabezado, EstadoVacio, EsqueletoTarjetas, Mensaje, Selector, Tarjeta } from "../../componentes/ui";
import { textoDia } from "../../lib/fechas";
import { describirAlerta, MODALIDADES, salarioModalidad, type Vacante } from "../../lib/vacantes";

function TarjetaVacante({ v }: { v: Vacante }) {
  const [abierta, setAbierta] = useState(false);
  return (
    <Tarjeta as="article" className="flex flex-col gap-3">
      <div className="flex flex-col gap-1 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h3 className="text-base font-semibold text-texto">{v.Cargo}</h3>
          <p className="text-sm text-texto"><strong className="font-medium">{v.Empresa}</strong> · <span className="inline-flex items-center gap-1"><MapPin className="size-3.5 text-texto-tenue" aria-hidden />{v.Ubicacion}</span></p>
          <p className="text-xs text-texto-sec">{salarioModalidad(v)}</p>
        </div>
        <Link to={`/vacantes/${v.Id_vacante}`} className="inline-flex h-10 items-center justify-center rounded-[var(--radius-control)] border border-borde px-4 text-sm font-medium text-texto hover:bg-fondo">
          Ver detalle
        </Link>
      </div>
      <button type="button" aria-expanded={abierta} onClick={() => setAbierta(!abierta)} className="flex items-center gap-1 self-start text-sm text-primario cursor-pointer">
        Ver descripción y requisitos <ChevronDown className={`size-4 transition-transform ${abierta ? "rotate-180" : ""}`} aria-hidden />
      </button>
      {abierta && (
        <div className="flex flex-col gap-2 border-t border-borde pt-3 text-sm">
          <p className="font-medium">Descripción</p><p className="text-texto-sec">{v.Descripcion}</p>
          <p className="font-medium">Requisitos</p><p className="text-texto-sec">{v.Requisitos}</p>
          <p className="text-xs text-texto-tenue">Publicada el {textoDia(v.Fecha_publicacion)}</p>
        </div>
      )}
    </Tarjeta>
  );
}

function resumenResultados(cantidad: number, palabra: string, hayFiltros: boolean) {
  if (hayFiltros) {
    const verbo = cantidad === 1 ? "vacante cumple" : "vacantes cumplen";
    const coincide = cantidad === 1 ? "coincide" : "coinciden";
    return `${cantidad} ${verbo} los filtros${palabra ? ` y ${coincide} con «${palabra}»` : ""}`;
  }
  if (palabra) return `${cantidad} ${cantidad === 1 ? "vacante coincide" : "vacantes coinciden"} con «${palabra}»`;
  return `${cantidad} ${cantidad === 1 ? "vacante disponible" : "vacantes disponibles"}`;
}

export function Listado() {
  const cliente = useQueryClient();
  const [texto, setTexto] = useState("");
  const [palabra, setPalabra] = useState("");
  const [ubicacion, setUbicacion] = useState("Todas");
  const [salario, setSalario] = useState("");
  const [modalidad, setModalidad] = useState("Todas");
  const [mensajeAlerta, setMensajeAlerta] = useState<Pick<Respuesta, "ok" | "mensaje"> | null>(null);

  // La búsqueda se aplica al dejar de escribir (en Streamlit, al pulsar Enter).
  useEffect(() => {
    const t = setTimeout(() => setPalabra(texto.trim()), 350);
    return () => clearTimeout(t);
  }, [texto]);

  const filtros = {
    ubicacion: ubicacion === "Todas" ? null : ubicacion,
    salario_minimo: Number(salario) > 0 ? Number(salario) : null,
    modalidad: modalidad === "Todas" ? null : modalidad,
  };
  const hayFiltros = !!(filtros.ubicacion || filtros.salario_minimo || filtros.modalidad);
  const hayCriterios = !!(palabra || hayFiltros);

  const ubicaciones = useQuery({ queryKey: ["ubicaciones"], queryFn: () => api.get<string[]>("/vacantes/ubicaciones") });
  const vacantes = useQuery({
    queryKey: ["vacantes", palabra, filtros],
    queryFn: () => {
      const q = new URLSearchParams();
      if (palabra) q.set("palabra_clave", palabra);
      Object.entries(filtros).forEach(([k, v]) => v != null && q.set(k, String(v)));
      return api.get<Vacante[]>(`/vacantes?${q}`);
    },
    placeholderData: keepPreviousData,
  });

  const crearAlerta = async () => {
    const r = await api.put("/alerta", { palabra_clave: palabra || null, ...filtros });
    const criterios = describirAlerta(palabra, filtros.ubicacion, filtros.salario_minimo, filtros.modalidad);
    setMensajeAlerta(r.ok ? { ok: true, mensaje: `${r.mensaje} Criterios: ${criterios}.` } : r);
    if (r.ok) cliente.invalidateQueries({ queryKey: ["alerta"] });
  };

  const lista = vacantes.data?.ok ? vacantes.data.datos : [];
  return (
    <>
      <Encabezado titulo="Vacantes disponibles" />
      <Tarjeta className="mb-6 flex flex-col gap-4">
        <div className="relative">
          <Campo
            etiqueta="Buscar por palabra clave" placeholder="Ej.: Python, analista, remoto" value={texto}
            onChange={(e) => setTexto(e.target.value)} onKeyDown={(e) => e.key === "Enter" && setPalabra(texto.trim())}
            ayuda="Busca en el cargo y en la descripción. Borra el texto para ver todas." className="pl-9"
          />
          <Search className="pointer-events-none absolute left-3 top-[38px] size-4 text-texto-tenue" aria-hidden />
        </div>
        <div className="grid gap-4 sm:grid-cols-3">
          <Selector etiqueta="Ubicación" value={ubicacion} onChange={(e) => setUbicacion(e.target.value)}
            opciones={["Todas", ...(ubicaciones.data?.ok ? ubicaciones.data.datos : [])]} />
          <Campo etiqueta="Salario mínimo (COP al mes)" type="number" min={0} step={500000} placeholder="Sin mínimo"
            value={salario} onChange={(e) => setSalario(e.target.value)} />
          <Selector etiqueta="Modalidad" value={modalidad} onChange={(e) => setModalidad(e.target.value)}
            opciones={[{ valor: "Todas", texto: "Todas" }, ...Object.entries(MODALIDADES).map(([valor, texto]) => ({ valor, texto }))]} />
        </div>
        {ubicaciones.data && !ubicaciones.data.ok && <Aviso tipo="error">{ubicaciones.data.mensaje}</Aviso>}
        <div className="flex flex-col gap-2">
          <div>
            <Boton icono={BellPlus} onClick={crearAlerta} disabled={!hayCriterios}
              title={hayCriterios
                ? "Te avisaremos en Notificaciones cuando se publique una vacante nueva que cumpla la búsqueda y los filtros actuales."
                : "Escribe una palabra clave o elige al menos un filtro."}>
              Crear alerta con estos filtros
            </Boton>
          </div>
          <Mensaje resultado={mensajeAlerta} />
        </div>
      </Tarjeta>

      {vacantes.isLoading ? <EsqueletoTarjetas /> :
        !vacantes.data?.ok ? <Aviso tipo="error">{vacantes.data?.mensaje}</Aviso> :
        !lista.length ? (
          <EstadoVacio
            icono={SearchX}
            titulo={hayFiltros
              ? `Sin resultados: ninguna vacante${palabra ? ` con «${palabra}»` : ""} cumple los filtros seleccionados. Prueba quitando alguno.`
              : palabra ? `Sin resultados para «${palabra}». Prueba con otra palabra.`
              : "Por ahora no hay vacantes disponibles. Vuelve a revisar más tarde."}
          />
        ) : (
          <div className="flex flex-col gap-3">
            <p className="text-sm text-texto-sec">{resumenResultados(lista.length, palabra, hayFiltros)}</p>
            {lista.map((v) => <TarjetaVacante key={v.Id_vacante} v={v} />)}
          </div>
        )}
    </>
  );
}
