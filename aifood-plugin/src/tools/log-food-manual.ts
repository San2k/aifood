/**
 * Log Food Manual Tool
 * Allows users to log food with manual nutrition entry (without FatSecret)
 */

import type { DatabaseService } from '../services/database.js';
import type { MealType } from '../types/index.js';

interface LogFoodManualParams {
  foodName: string;
  calories: number;
  protein?: number;
  carbs?: number;
  fat?: number;
  fiber?: number;
  meal?: string;
  date?: string;
}

interface ToolContext {
  odentity: string;
}

export function createLogFoodManualTool(db: DatabaseService) {
  return {
    name: 'log_food',
    description: 'Log food consumption with nutritional data. Use this when the user wants to record what they ate.',
    parameters: {
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
    handler: async (params: LogFoodManualParams, ctx: ToolContext) => {
      const { foodName, calories, protein, carbs, fat, fiber, meal, date } = params;

      // Determine consumed date
      const consumedAt = date ? new Date(date) : new Date();
      consumedAt.setHours(new Date().getHours(), new Date().getMinutes());

      // Save to database
      const entry = await db.logFood({
        odentity: ctx.odentity,
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

      // Get updated daily totals
      const totals = await db.getDailyTotals(ctx.odentity, consumedAt);

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
  };
}
