/**
 * AiFood OpenClaw Plugin
 * Nutrition tracking plugin
 */

import { DatabaseService } from './services/database.js';
import type { PluginConfig, MealType } from './types/index.js';

interface TextContent {
  type: 'text';
  text: string;
}

interface ToolResult {
  content: TextContent[];
  details: Record<string, unknown>;
}

interface OpenClawPluginApi {
  config: PluginConfig;
  pluginConfig: PluginConfig;
  logger: {
    info: (msg: string) => void;
    error: (msg: string, err?: unknown) => void;
  };
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  registerTool(tool: any, options?: { optional?: boolean }): void;
}

// JSON Schema definitions (compatible with TypeBox output format)
const LogFoodSchema = {
  type: 'object' as const,
  properties: {
    foodName: { type: 'string' as const, description: 'Name of the food (e.g., "2 eggs", "chicken breast 150g")' },
    calories: { type: 'number' as const, description: 'Calories in kcal' },
    protein: { type: 'number' as const, description: 'Protein in grams' },
    carbs: { type: 'number' as const, description: 'Carbohydrates in grams' },
    fat: { type: 'number' as const, description: 'Fat in grams' },
    fiber: { type: 'number' as const, description: 'Fiber in grams' },
    meal: { type: 'string' as const, description: 'Meal type: breakfast, lunch, dinner, snack' },
    date: { type: 'string' as const, description: 'Date in YYYY-MM-DD format. Defaults to today.' },
  },
  required: ['foodName', 'calories'] as const,
};

const DailyReportSchema = {
  type: 'object' as const,
  properties: {
    date: { type: 'string' as const, description: 'Date in YYYY-MM-DD format. Defaults to today.' },
  },
};

const SetGoalsSchema = {
  type: 'object' as const,
  properties: {
    calories: { type: 'number' as const, description: 'Daily calorie target' },
    protein: { type: 'number' as const, description: 'Daily protein target in grams' },
    carbs: { type: 'number' as const, description: 'Daily carbohydrate target in grams' },
    fat: { type: 'number' as const, description: 'Daily fat target in grams' },
    fiber: { type: 'number' as const, description: 'Daily fiber target in grams' },
  },
};

let db: DatabaseService | null = null;

export default {
  id: 'aifood',
  name: 'AiFood Nutrition Tracker',
  configSchema: {
    type: 'object',
    properties: {
      databaseUrl: {
        type: 'string',
        description: 'PostgreSQL connection URL',
        default: 'postgresql://aifood:aifood_secure_password_2024@localhost:5433/aifood',
      },
    },
  },

  async register(api: OpenClawPluginApi) {
    const config = api.pluginConfig || api.config || {};

    // Initialize database
    const dbUrl =
      (config as Record<string, unknown>).databaseUrl as string ||
      'postgresql://aifood:aifood_secure_password_2024@localhost:5433/aifood';

    db = new DatabaseService({ databaseUrl: dbUrl });

    // Initialize database tables
    try {
      await db.initialize();
      api.logger.info('AiFood: Database initialized');
    } catch (error) {
      api.logger.error('AiFood: Failed to initialize database', error);
      return;
    }

    // Register log_food tool
    api.registerTool({
      name: 'log_food',
      label: 'Log Food',
      description:
        'Log food consumption with nutritional data. Use this when the user wants to record what they ate.',
      parameters: LogFoodSchema,
      async execute(
        _toolCallId: string,
        params: {
          foodName: string;
          calories: number;
          protein?: number;
          carbs?: number;
          fat?: number;
          fiber?: number;
          meal?: string;
          date?: string;
        }
      ): Promise<ToolResult> {
        const { foodName, calories, protein, carbs, fat, fiber, meal, date } = params;

        const consumedAt = date ? new Date(date) : new Date();
        consumedAt.setHours(new Date().getHours(), new Date().getMinutes());

        const entry = await db!.logFood({
          odentity: 'default',
          foodId: '',
          foodName,
          brandName: undefined,
          servingId: undefined,
          servingDescription: undefined,
          servingSize: undefined,
          servingUnit: undefined,
          numberOfServings: 1,
          calories,
          protein,
          carbohydrates: carbs,
          fat,
          fiber,
          sugar: undefined,
          sodium: undefined,
          mealType: meal as MealType | undefined,
          consumedAt,
        });

        const totals = await db!.getDailyTotals('default', consumedAt);

        const message = `Logged: ${foodName} (${Math.round(calories)} kcal). Daily total: ${Math.round(totals.calories)} kcal`;

        return {
          content: [{ type: 'text', text: message }],
          details: {
            success: true,
            entry: {
              id: entry.id,
              food: foodName,
              calories: Math.round(calories),
              protein: protein ? Math.round(protein) : null,
              carbs: carbs ? Math.round(carbs) : null,
              fat: fat ? Math.round(fat) : null,
            },
            dailyTotals: {
              calories: Math.round(totals.calories),
              protein: Math.round(totals.protein),
              carbs: Math.round(totals.carbohydrates),
              fat: Math.round(totals.fat),
              entries: totals.entries,
            },
          },
        };
      },
    });

    // Register daily_nutrition_report tool
    api.registerTool({
      name: 'daily_nutrition_report',
      label: 'Daily Nutrition Report',
      description:
        'Get nutrition summary for today or a specific date. Shows calories, protein, carbs, fat consumed.',
      parameters: DailyReportSchema,
      async execute(
        _toolCallId: string,
        params: { date?: string }
      ): Promise<ToolResult> {
        const { date } = params;
        const targetDate = date ? new Date(date) : new Date();

        const totals = await db!.getDailyTotals('default', targetDate);
        const goals = await db!.getGoals('default');
        const entries = await db!.getEntriesByDate('default', targetDate);

        const dateStr = targetDate.toISOString().split('T')[0];
        let message = `Nutrition report for ${dateStr}:\n`;
        message += `Calories: ${Math.round(totals.calories)} kcal`;
        if (goals?.targetCalories) {
          message += ` / ${goals.targetCalories} kcal (${Math.round((totals.calories / goals.targetCalories) * 100)}%)`;
        }
        message += `\nProtein: ${Math.round(totals.protein)}g`;
        if (goals?.targetProtein) {
          message += ` / ${goals.targetProtein}g`;
        }
        message += `\nCarbs: ${Math.round(totals.carbohydrates)}g`;
        if (goals?.targetCarbs) {
          message += ` / ${goals.targetCarbs}g`;
        }
        message += `\nFat: ${Math.round(totals.fat)}g`;
        if (goals?.targetFat) {
          message += ` / ${goals.targetFat}g`;
        }
        message += `\n\nEntries: ${entries.length}`;

        return {
          content: [{ type: 'text', text: message }],
          details: {
            success: true,
            date: dateStr,
            summary: totals,
            goals: goals || null,
            entries: entries.map((e) => ({
              food: e.foodName,
              calories: Math.round(e.calories),
              meal: e.mealType,
            })),
          },
        };
      },
    });

    // Register set_nutrition_goals tool
    api.registerTool({
      name: 'set_nutrition_goals',
      label: 'Set Nutrition Goals',
      description: 'Set daily nutrition goals for calories, protein, carbs, and fat.',
      parameters: SetGoalsSchema,
      async execute(
        _toolCallId: string,
        params: {
          calories?: number;
          protein?: number;
          carbs?: number;
          fat?: number;
          fiber?: number;
        }
      ): Promise<ToolResult> {
        const { calories, protein, carbs, fat, fiber } = params;

        if (!calories && !protein && !carbs && !fat && !fiber) {
          return {
            content: [{ type: 'text', text: 'Please specify at least one goal (calories, protein, carbs, fat, or fiber)' }],
            details: { success: false },
          };
        }

        const goals = await db!.setGoals({
          odentity: 'default',
          targetCalories: calories,
          targetProtein: protein,
          targetCarbs: carbs,
          targetFat: fat,
          targetFiber: fiber,
          createdAt: new Date(),
          updatedAt: new Date(),
        });

        let message = 'Nutrition goals updated:\n';
        if (goals.targetCalories) message += `Calories: ${goals.targetCalories} kcal\n`;
        if (goals.targetProtein) message += `Protein: ${goals.targetProtein}g\n`;
        if (goals.targetCarbs) message += `Carbs: ${goals.targetCarbs}g\n`;
        if (goals.targetFat) message += `Fat: ${goals.targetFat}g\n`;
        if (goals.targetFiber) message += `Fiber: ${goals.targetFiber}g\n`;

        return {
          content: [{ type: 'text', text: message.trim() }],
          details: {
            success: true,
            goals: {
              calories: goals.targetCalories,
              protein: goals.targetProtein,
              carbs: goals.targetCarbs,
              fat: goals.targetFat,
              fiber: goals.targetFiber,
            },
          },
        };
      },
    });

    api.logger.info('AiFood: Plugin registered with 3 tools');
  },
};
