/**
 * Configuration Loader
 * Loads and validates gateway configuration from environment variables
 */

import dotenv from 'dotenv';
import { GatewayConfig, OutputProfile } from '../types/config';

// Load .env file
dotenv.config();

/**
 * Load and validate gateway configuration
 * @throws Error if required environment variables are missing
 */
export function loadConfig(): GatewayConfig {
  // Validate required variables
  const requiredVars = ['GEMINI_API_KEY'];
  const missing = requiredVars.filter(varName => !process.env[varName]);

  if (missing.length > 0) {
    throw new Error(`Missing required environment variables: ${missing.join(', ')}`);
  }

  return {
    server: {
      port: parseInt(process.env.GATEWAY_PORT || '9000', 10),
      host: process.env.GATEWAY_HOST || '0.0.0.0',
    },

    gemini: {
      baseUrl: process.env.GEMINI_BASE_URL || 'https://generativelanguage.googleapis.com/v1beta/openai',
      apiKey: process.env.GEMINI_API_KEY!,
      model: process.env.GEMINI_MODEL || 'gemini-1.5-flash',
      timeout: parseInt(process.env.GEMINI_TIMEOUT || '60000', 10),
      retries: parseInt(process.env.GEMINI_RETRIES || '3', 10),
    },

    redis: {
      url: process.env.REDIS_URL || 'redis://localhost:6379/1',
    },

    routes: {
      brief: {
        provider: 'gemini',
        actualModel: process.env.GEMINI_MODEL || 'gemini-1.5-flash',
        profile: OutputProfile.BRIEF,
      },
      standard: {
        provider: 'gemini',
        actualModel: process.env.GEMINI_MODEL || 'gemini-1.5-flash',
        profile: OutputProfile.STANDARD,
      },
      analysis: {
        provider: 'gemini',
        actualModel: process.env.GEMINI_MODEL_PRO || 'gemini-1.5-pro',
        profile: OutputProfile.LONG,
      },
    },

    tokenPolicy: {
      historyWindowTokens: parseInt(process.env.HISTORY_WINDOW_TOKENS || '12000', 10),
      historyWindowMessages: parseInt(process.env.HISTORY_WINDOW_MESSAGES || '8', 10),
      summaryTriggerTokens: parseInt(process.env.SUMMARY_TRIGGER_TOKENS || '12000', 10),
      summaryTargetTokens: parseInt(process.env.SUMMARY_TARGET_TOKENS || '1000', 10),
      ragBudgetTokens: parseInt(process.env.RAG_BUDGET_TOKENS || '2000', 10),
      outputProfiles: {
        [OutputProfile.BRIEF]: 512,
        [OutputProfile.STANDARD]: 1200,
        [OutputProfile.LONG]: 4000,
      },
      cacheEnabled: process.env.CACHE_ENABLED === 'true',
      cacheTTL: parseInt(process.env.CACHE_TTL || '3600', 10),
    },

    quotas: {
      default: {
        dailyTokens: parseInt(process.env.QUOTA_DAILY_TOKENS || '100000', 10),
        monthlyUSD: parseFloat(process.env.QUOTA_MONTHLY_USD || '50'),
      },
    },

    observability: {
      logsLevel: (process.env.LOG_LEVEL as 'debug' | 'info' | 'warn' | 'error') || 'info',
      metricsEnabled: process.env.METRICS_ENABLED === 'true',
      tracingEnabled: process.env.TRACING_ENABLED === 'true',
    },
  };
}

/**
 * Global configuration instance
 */
export const config = loadConfig();
