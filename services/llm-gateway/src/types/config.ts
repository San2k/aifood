/**
 * Gateway Configuration Types
 */

export enum OutputProfile {
  BRIEF = 'brief',
  STANDARD = 'standard',
  LONG = 'long',
}

export interface ServerConfig {
  port: number;
  host: string;
}

export interface GeminiConfig {
  baseUrl: string;
  apiKey: string;
  model: string;
  timeout: number;
  retries: number;
}

export interface RouteConfig {
  provider: string;
  actualModel: string;
  profile: OutputProfile;
}

export interface TokenPolicyConfig {
  historyWindowTokens: number;
  historyWindowMessages: number;
  summaryTriggerTokens: number;
  summaryTargetTokens: number;
  ragBudgetTokens: number;
  outputProfiles: Record<OutputProfile, number>;
  cacheEnabled: boolean;
  cacheTTL: number;
}

export interface QuotaConfig {
  dailyTokens: number;
  monthlyUSD: number;
}

export interface ObservabilityConfig {
  logsLevel: 'debug' | 'info' | 'warn' | 'error';
  metricsEnabled: boolean;
  tracingEnabled: boolean;
}

export interface GatewayConfig {
  server: ServerConfig;
  gemini: GeminiConfig;
  redis: {
    url: string;
  };
  routes: Record<string, RouteConfig>;
  tokenPolicy: TokenPolicyConfig;
  quotas: {
    default: QuotaConfig;
  };
  observability: ObservabilityConfig;
}
