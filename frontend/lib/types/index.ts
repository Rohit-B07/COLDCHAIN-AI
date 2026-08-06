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

/** Uniform success envelope returned by every API response. */
export interface ApiEnvelope<T> {
  success: boolean;
  data: T | null;
}

/** Single structured error item from the backend. */
export interface ApiErrorDetail {
  field: string | null;
  message: string;
}

/** Uniform error envelope returned on failed requests. */
export interface ApiErrorResponse {
  success: boolean;
  error_code: string;
  message: string;
  details: ApiErrorDetail[];
}

export type UserRole =
  "super_admin" | "admin" | "dispatcher" | "logistics" | "driver";

/** Current user returned by `/auth/me` and `/auth/login`. */
export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string | null;
}

/** Full login response containing tokens and the authenticated user. */
export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

/** Rotation response from `/auth/refresh` and `/auth/token`. */
export interface AccessTokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

/** Uniform pagination envelope from the backend. */
export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export type ShipmentStatus =
  | "created"
  | "predicted"
  | "dispatched"
  | "in_transit"
  | "delivered"
  | "cancelled";

export type PriorityLevel = "low" | "medium" | "high";

export type RouteStatus =
  | "planned"
  | "optimized"
  | "selected"
  | "completed"
  | "cancelled";

export type VehicleStatus = "active" | "maintenance" | "retired";

export type DriverStatus = "available" | "assigned" | "on_leave";

export type AlertSeverity = "info" | "warning" | "critical";

export type AlertStatus = "open" | "acknowledged" | "resolved";

export type RiskLevel = "low" | "medium" | "high" | "critical";

export interface ShipmentRead {
  id: string;
  tracking_code: string;
  vaccine_name: string;
  dose_count: number;
  priority: PriorityLevel;
  temperature_min: number;
  temperature_max: number;
  warehouse_id: string;
  destination_id: string;
  container_id: string | null;
  driver_id: string | null;
  status: ShipmentStatus;
  dispatched_at: string | null;
  delivered_at: string | null;
  estimated_delivery_at: string | null;
  created_at: string;
  is_deleted: boolean;
  deleted_at: string | null;
}

export interface WaypointRead {
  id: string;
  route_id: string;
  sequence: number;
  name: string;
  latitude: number;
  longitude: number;
  arrival_at: string | null;
  departure_at: string | null;
}

export interface RouteRead {
  id: string;
  shipment_id: string;
  distance_km: number;
  duration_minutes: number;
  stops: Record<string, unknown>[];
  polyline: string;
  weather_factor: number;
  safety_score: number;
  is_selected: boolean;
  status: RouteStatus;
  optimization_metadata: Record<string, unknown>;
  waypoints: WaypointRead[];
  is_deleted: boolean;
  created_at: string | null;
}

export interface WarehouseRead {
  id: string;
  name: string;
  code: string;
  latitude: number;
  longitude: number;
  address: string;
  capacity: number;
  is_deleted: boolean;
  created_at: string | null;
}

export interface PhcRead {
  id: string;
  name: string;
  code: string;
  district: string;
  state: string;
  latitude: number;
  longitude: number;
  contact: string;
  capacity: number;
  priority_level: number;
  is_deleted: boolean;
  created_at: string | null;
}

export interface VehicleRead {
  id: string;
  registration_number: string;
  vehicle_type: string;
  capacity_kg: number;
  is_reefer: boolean;
  status: VehicleStatus;
  maintenance_status: string;
  last_maintenance_at: string | null;
  next_maintenance_due_at: string | null;
  is_deleted: boolean;
  created_at: string | null;
}

export interface DriverRead {
  id: string;
  name: string;
  license_number: string;
  phone: string;
  status: DriverStatus;
  vehicle_id: string | null;
  is_deleted: boolean;
  created_at: string | null;
}

export interface AlertRead {
  id: string;
  shipment_id: string | null;
  container_id: string | null;
  severity: AlertSeverity;
  alert_type: string;
  message: string;
  status: AlertStatus;
  acknowledged_by: string | null;
  acknowledged_at: string | null;
  created_at: string | null;
}

export interface PredictionRead {
  id: string;
  shipment_id: string;
  excursion_risk: number;
  risk_level: RiskLevel;
  confidence: number;
  expected_min_temp: number;
  expected_max_temp: number;
  model_version: string;
  features: Record<string, unknown>;
  explanations: Record<string, unknown>;
  created_at: string | null;
}
