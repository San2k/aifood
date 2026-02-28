/**
 * AiFood OpenClaw Plugin
 * Nutrition tracking plugin
 */

import { DatabaseService } from './services/database.js';
import type { PluginConfig, MealType } from './types/index.js';

interface OpenClawAPI {
  config: PluginConfig;
  logger: {
    info: (msg: string) => void;
    error: (msg: string, err?: unknown) => void;
  };
  registerTool(tool: {
    name: string;
    description: string;
    inputSchema: Record<string, unknown>;
    handler: (input: Record<string, unknown>) => Promise<unknown>;
  }): void;
}

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

  async register(api: OpenClawAPI) {
    const config = api.config;

    // Initialize database
    db = new DatabaseService({
      databaseUrl:
        config.databaseUrl ||
        'postgresql://aifood:aifood_secure_password_2024@localhost:5433/aifood',
    });

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
      description:
        'Log food consumption with nutritional data. Use this when the user wants to record what they ate.',
      inputSchema: {
        type: 'object',
        properties: {
          foodName: {
            type: 'string',
            description: 'Name of the food (e.g., "2 eggs", "chicken breast 150g")',
          },
          calories: {
            type: 'number',
            description: 'Calories in kcal',
          },
          protein: {
            type: 'number',
            description: 'Protein in grams',
          },
          carbs: {
            type: 'number',
            description: 'Carbohydrates in grams',
          },
          fat: {
            type: 'number',
            description: 'Fat in grams',
          },
          fiber: {
            type: 'number',
            description: 'Fiber in grams',
          },
          meal: {
            type: 'string',
            enum: ['breakfast', 'lunch', 'dinner', 'snack'],
            description: 'Meal type',
          },
          date: {
            type: 'string',
            description: 'Date in YYYY-MM-DD format. Defaults to today.',
          },
        },
        required: ['foodName', 'calories'],
      },
      handler: async (input) => {
        const {
          foodName,
          calories,
          protein,
          carbs,
          fat,
          fiber,
          meal,
          date,
        } = input as {
          foodName: string;
          calories: number;
          protein?: number;
          carbs?: number;
          fat?: number;
          fiber?: number;
          meal?: string;
          date?: string;
        };

        const consumedAt = date ? new Date(date) : new Date();
        consumedAt.setHours(new Date().getHours(), new Date().getMinutes());

        const entry = await db!.logFood({
          odentity: 'default', // TODO: get from context when available
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

        return {
          success: true,
          message: `Logged: ${foodName}`,
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
        };
      },
    });

    // Register daily_nutrition_report tool
    api.registerTool({
      name: 'daily_nutrition_report',
      description:
        'Get nutrition summary for today or a specific date. Shows calories, protein, carbs, fat consumed.',
      inputSchema: {
        type: 'object',
        properties: {
          date: {
            type: 'string',
            description: 'Date in YYYY-MM-DD format. Defaults to today.',
          },
        },
      },
      handler: async (input) => {
        const { date } = input as { date?: string };
        const targetDate = date ? new Date(date) : new Date();

        const totals = await db!.getDailyTotals('default', targetDate);
        const goals = await db!.getGoals('default');
        const entries = await db!.getEntriesByDate('default', targetDate);

        // Group by meal type
        const byMeal: Record<string, unknown[]> = {
          breakfast: [],
          lunch: [],
          dinner: [],
          snack: [],
          other: [],
        };

        for (const entry of entries) {
          const mealKey = entry.mealType || 'other';
          if (!byMeal[mealKey]) byMeal[mealKey] = [];
          byMeal[mealKey].push({
            food: entry.foodName,
            calories: Math.round(entry.calories),
            protein: entry.protein ? Math.round(entry.protein) : null,
          });
        }

        return {
          success: true,
          date: targetDate.toISOString().split('T')[0],
          summary: {
            calories: Math.round(totals.calories),
            protein: Math.round(totals.protein),
            carbs: Math.round(totals.carbohydrates),
            fat: Math.round(totals.fat),
            fiber: Math.round(totals.fiber),
            entries: totals.entries,
          },
          progress: goals
            ? {
                caloriesGoal: goals.targetCalories,
                caloriesRemaining: goals.targetCalories
                  ? goals.targetCalories - Math.round(totals.calories)
                  : null,
                proteinGoal: goals.targetProtein,
                proteinRemaining: goals.targetProtein
                  ? goals.targetProtein - Math.round(totals.protein)
                  : null,
              }
            : null,
          byMeal,
        };
      },
    });

    // Register set_nutrition_goals tool
    api.registerTool({
      name: 'set_nutrition_goals',
      description: 'Set daily nutrition goals for calories, protein, carbs, and fat.',
      inputSchema: {
        type: 'object',
        properties: {
          calories: {
            type: 'number',
            description: 'Daily calorie target',
          },
          protein: {
            type: 'number',
            description: 'Daily protein target in grams',
          },
          carbs: {
            type: 'number',
            description: 'Daily carbohydrate target in grams',
          },
          fat: {
            type: 'number',
            description: 'Daily fat target in grams',
          },
          fiber: {
            type: 'number',
            description: 'Daily fiber target in grams',
          },
        },
      },
      handler: async (input) => {
        const { calories, protein, carbs, fat, fiber } = input as {
          calories?: number;
          protein?: number;
          carbs?: number;
          fat?: number;
          fiber?: number;
        };

        if (!calories && !protein && !carbs && !fat && !fiber) {
          return {
            success: false,
            message: 'Please specify at least one goal (calories, protein, carbs, fat, or fiber)',
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

        return {
          success: true,
          message: 'Nutrition goals updated',
          goals: {
            calories: goals.targetCalories,
            protein: goals.targetProtein,
            carbs: goals.targetCarbs,
            fat: goals.targetFat,
            fiber: goals.targetFiber,
          },
        };
      },
    });

    api.logger.info('AiFood: Plugin registered with 3 tools');
  },
};
