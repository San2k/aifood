/**
 * AiFood OpenClaw Plugin
 * Nutrition tracking with FatSecret database integration
 */

import { FatSecretClient } from './services/fatsecret.js';
import { DatabaseService } from './services/database.js';
import { createLogFoodTool } from './tools/log-food.js';
import { createSearchFoodTool } from './tools/search-food.js';
import { createDailyReportTool } from './tools/daily-report.js';
import { createWeeklyReportTool } from './tools/weekly-report.js';
import { createSetGoalsTool } from './tools/set-goals.js';
import type { PluginConfig } from './types/index.js';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type ToolHandler = (params: any, ctx: { odentity: string }) => Promise<unknown>;

interface OpenClawTool {
  name: string;
  description: string;
  parameters?: Record<string, unknown>;
  handler: ToolHandler;
}

interface OpenClawAPI {
  registerTool(tool: OpenClawTool): void;
  getConfig(): PluginConfig;
}

let fatsecret: FatSecretClient | null = null;
let db: DatabaseService | null = null;

export default async function register(api: OpenClawAPI) {
  const config = api.getConfig();

  // Validate required config
  if (!config.fatsecretClientId || !config.fatsecretClientSecret) {
    console.error('AiFood: Missing FatSecret API credentials in config');
    return;
  }

  // Initialize services
  fatsecret = new FatSecretClient({
    fatsecretClientId: config.fatsecretClientId,
    fatsecretClientSecret: config.fatsecretClientSecret,
  });

  db = new DatabaseService({
    databaseUrl: config.databaseUrl || 'postgresql://localhost:5432/aifood',
  });

  // Initialize database tables
  try {
    await db.initialize();
    console.log('AiFood: Database initialized');
  } catch (error) {
    console.error('AiFood: Failed to initialize database:', error);
    return;
  }

  // Register tools
  api.registerTool(createLogFoodTool(fatsecret, db));
  api.registerTool(createSearchFoodTool(fatsecret));
  api.registerTool(createDailyReportTool(db));
  api.registerTool(createWeeklyReportTool(db));
  api.registerTool(createSetGoalsTool(db));

  console.log('AiFood: Plugin registered with 5 tools');
}

// Cleanup on unload
export async function unload() {
  if (db) {
    await db.close();
  }
}
