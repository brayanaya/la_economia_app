import axios from 'axios';

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1',
  headers: { 'Content-Type': 'application/json' },
});

export interface ProductoRecuperado {
  producto_id: string;
  nombre: string;
  categoria_nombre: string | null;
  precio: number;
  stock_sede: number | null;
  similitud: number;
}

export interface BusquedaSemanticaRequest {
  consulta: string;
  sede_id?: string | null;
  top_k?: number;
  limite_resultados?: number;
}

export interface BusquedaSemanticaResponse {
  consulta: string;
  resultados: ProductoRecuperado[];
  candidatos_ampliados: boolean;
}

export interface AgenteChatRequest {
  mensaje: string;
  sede_id?: string | null;
}

export interface AgenteChatResponse {
  mensaje: string;
  respuesta: string;
  productos_recomendados: ProductoRecuperado[];
  hubo_resultados_relevantes: boolean;
}

export async function buscarProductos(
  payload: BusquedaSemanticaRequest
): Promise<BusquedaSemanticaResponse> {
  const { data } = await api.post<BusquedaSemanticaResponse>(
    '/busqueda/semantica',
    payload
  );
  return data;
}

export async function enviarMensajeAgente(
  payload: AgenteChatRequest
): Promise<AgenteChatResponse> {
  const { data } = await api.post<AgenteChatResponse>('/agente/chat', payload);
  return data;
}
