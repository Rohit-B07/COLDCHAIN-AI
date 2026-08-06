/** Shared domain types mirroring the backend response contracts. */

export interface HealthResponse {
  status: string;
  database: string;
}

export interface Shipment {
  shipment_id: string;
  origin: string;
  destination: string;
  status: string;
  created_at: string;
  dispatched_at: string | null;
}

export interface ExcursionReport {
  predicted: boolean;
  confidence: number;
  risk_level: "low" | "medium" | "high";
  contributing_factors: string[];
}
