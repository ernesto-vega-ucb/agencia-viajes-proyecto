export interface CancellationPolicy {
  daysBefore: number;
  refundPercentage: number;
}

export interface TourPackage {
  id: string;
  code: string;
  title: string;
  destination: string;
  country: string;
  description: string;
  category: string;
  durationDays: number;
  basePrice: number;
  currency: string;
  maxTravelers: number;
  images: string[];
  startDates: string[];
  cancelDaysBefore: number;
  cancelRefundPercent: number;
  rating: number;
  active: boolean;
  source: string;
}

export interface BookingRequestItem {
  packageId: string;
  startDate: string;
  travelers: number;
}

export interface BookingRequest {
  items: BookingRequestItem[];
}

export interface Booking {
  id: string;
  userId: string;
  status: "PENDING" | "CONFIRMED" | "PAID" | "CANCELLED";
  currency: string;
  totalPrice: number;
  createdAt: string;
  items: BookingItem[];
}

export interface BookingItem {
  id: string;
  packageId: string;
  packageTitle: string;
  startDate: string;
  travelers: number;
  unitPrice: number;
  subtotal: number;
}

export interface SearchResult {
  packages: TourPackage[];
  suggestions: string[];
  query: string;
}

export interface ScrapedPackage {
  id: number;
  source: string;
  source_id?: string | null;
  title: string;
  destination?: string | null;
  price?: number | null;
  currency?: string | null;
  url?: string | null;
  scraped_at: string;
}

export interface ScrapeRefreshResult {
  status: string;
  indice_reconstruido: boolean;
  funcion: string;
  extraidos: number;
  nuevos_guardados: number;
  actualizados?: number;
  fuente: string;
}

export interface NlpDebug {
  intent: string;
  confidence: number;
  entities: Record<string, unknown[]>;
  scores: Record<string, number>;
  model: string;
}

export interface AgentStep {
  step: number;
  thought: string;
  tool?: string | null;
  tool_params?: Record<string, unknown>;
  tool_output?: string | Record<string, unknown> | null;
}

export interface AgentTrace {
  model: string;
  mode: "llm" | "planner";
  steps: AgentStep[];
  thought?: string | null;
  tool_used?: string | null;
  tool_output?: string | Record<string, unknown> | null;
}

export interface ChatResponse {
  message: string;
  intent: string;
  confidence: number;
  scores: Record<string, number>;
  entities: Record<string, unknown[]>;
  context: Record<string, number | string | null>;
  suggestions: TourPackage[];
  nlp_debug?: NlpDebug;
  agent_trace?: AgentTrace;
}

export interface AgentMetrics {
  tool_selection_accuracy: number;
  task_success_rate: number;
  mode: string;
}

export interface MetricsSummary {
  datos: {
    interacciones_sinteticas: number;
    paquetes_sinteticos: number;
    scrapeados: number;
    total_fusion: number;
    embeddings: string;
    ml_enabled: boolean;
  };
  asistente: {
    macro_f1_intenciones: number;
    booking_success_rate: number;
  };
  buscador: {
    ndcg_at_5: number;
  };
  entidades: Record<string, number>;
  agente: AgentMetrics;
}