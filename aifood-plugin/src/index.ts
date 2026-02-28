/**
 * AiFood OpenClaw Plugin
 * Nutrition tracking plugin
 */

import { DatabaseService } from './services/database.js';
import { createLogFoodManualTool } from './tools/log-food-manual.js';
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

let db: DatabaseService | null = null;

export default async function register(api: OpenClawAPI) {
  const config = api.getConfig();

  // Initialize database
  db = new DatabaseService({
    databaseUrl: config.databaseUrl || 'postgresql://localhost:5433/aifood',
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
  api.registerTool(createLogFoodManualTool(db));
  api.registerTool(createDailyReportTool(db));
  api.registerTool(createWeeklyReportTool(db));
  api.registerTool(createSetGoalsTool(db));

  console.log('AiFood: Plugin registered with 4 tools');
}

// Cleanup on unload
export async function unload() {
  if (db) {
    await db.close();
  }
}
