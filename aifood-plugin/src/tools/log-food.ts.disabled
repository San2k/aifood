/**
 * Log Food Tool
 * Allows users to log food consumption with nutritional data from FatSecret
 */

import type { FatSecretClient } from '../services/fatsecret.js';
import type { DatabaseService } from '../services/database.js';
import type { LogFoodParams, MealType, Serving } from '../types/index.js';

interface ToolContext {
  odentity: string;
}

export function createLogFoodTool(fatsecret: FatSecretClient, db: DatabaseService) {
  return {
    name: 'log_food',
    description: 'Log food consumption with nutritional data from FatSecret database. Use this when the user wants to record what they ate.',
    parameters: {
      type: 'object',
      properties: {
        food: {
          type: 'string',
          description: 'Food name or description (e.g., "2 eggs", "150g chicken breast", "apple")',
        },
        amount: {
          type: 'string',
          description: 'Amount with unit (e.g., "150g", "2 pieces", "1 cup"). If not specified, default serving will be used.',
        },
        meal: {
          type: 'string',
          enum: ['breakfast', 'lunch', 'dinner', 'snack'],
          description: 'Meal type for categorization',
        },
        date: {
          type: 'string',
          description: 'Date in YYYY-MM-DD format. Defaults to today.',
        },
      },
      required: ['food'],
    },
    handler: async (params: LogFoodParams, ctx: ToolContext) => {
      const { food, amount, meal, date } = params;

      // Parse amount if provided
      const { quantity, unit } = parseAmount(amount);

      // Search for food in FatSecret
      const foods = await fatsecret.searchFoods(food, 5);

      if (foods.length === 0) {
        return {
          success: false,
          message: `Could not find "${food}" in the FatSecret database. Try a different search term or add it as a custom entry.`,
        };
      }

      // Get the first (best match) food with servings
      const foodWithServings = await fatsecret.getFood(foods[0].foodId);

      if (!foodWithServings || foodWithServings.servings.length === 0) {
        return {
          success: false,
          message: `No nutritional data available for "${foods[0].foodName}".`,
        };
      }

      // Find best matching serving
      const serving = findBestServing(foodWithServings.servings, quantity, unit);
      const numberOfServings = calculateServings(serving, quantity, unit);

      // Calculate nutrition based on servings
      const nutrition = {
        calories: (serving.calories ?? 0) * numberOfServings,
        protein: serving.protein ? serving.protein * numberOfServings : undefined,
        carbohydrates: serving.carbohydrate ? serving.carbohydrate * numberOfServings : undefined,
        fat: serving.fat ? serving.fat * numberOfServings : undefined,
        fiber: serving.fiber ? serving.fiber * numberOfServings : undefined,
        sugar: serving.sugar ? serving.sugar * numberOfServings : undefined,
        sodium: serving.sodium ? serving.sodium * numberOfServings : undefined,
      };

      // Determine consumed date
      const consumedAt = date ? new Date(date) : new Date();
      consumedAt.setHours(new Date().getHours(), new Date().getMinutes());

      // Save to database
      const entry = await db.logFood({
        odentity: ctx.odentity,
        foodId: foodWithServings.foodId,
        foodName: foodWithServings.foodName,
        brandName: foodWithServings.brandName,
        servingId: serving.servingId,
        servingDescription: serving.servingDescription,
        servingSize: serving.metricServingAmount,
        servingUnit: serving.metricServingUnit,
        numberOfServings,
        calories: nutrition.calories,
        protein: nutrition.protein,
        carbohydrates: nutrition.carbohydrates,
        fat: nutrition.fat,
        fiber: nutrition.fiber,
        sugar: nutrition.sugar,
        sodium: nutrition.sodium,
        mealType: meal as MealType | undefined,
        consumedAt,
      });

      // Get updated daily totals
      const totals = await db.getDailyTotals(ctx.odentity, consumedAt);

      return {
        success: true,
        message: `Logged: ${foodWithServings.foodName}`,
        entry: {
          id: entry.id,
          food: foodWithServings.foodName,
          brand: foodWithServings.brandName,
          serving: `${numberOfServings.toFixed(1)} × ${serving.servingDescription}`,
          calories: Math.round(nutrition.calories),
          protein: nutrition.protein ? Math.round(nutrition.protein) : null,
          carbs: nutrition.carbohydrates ? Math.round(nutrition.carbohydrates) : null,
          fat: nutrition.fat ? Math.round(nutrition.fat) : null,
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

/**
 * Parse amount string into quantity and unit
 */
function parseAmount(amount?: string): { quantity: number; unit: string } {
  if (!amount) {
    return { quantity: 1, unit: 'serving' };
  }

  // Match patterns like "150g", "2 pieces", "1.5 cups"
  const match = amount.match(/^([\d.]+)\s*(.*)$/);

  if (match) {
    return {
      quantity: parseFloat(match[1]),
      unit: match[2].trim().toLowerCase() || 'serving',
    };
  }

  return { quantity: 1, unit: amount.toLowerCase() };
}

/**
 * Find best matching serving for given unit
 */
function findBestServing(servings: Serving[], quantity: number, unit: string): Serving {
  // Normalize unit
  const normalizedUnit = normalizeUnit(unit);

  // Priority: metric match > measurement match > first serving
  const gramServing = servings.find(
    (s) => s.metricServingUnit?.toLowerCase() === 'g' || s.measurementDescription?.toLowerCase().includes('gram')
  );

  if (normalizedUnit === 'g' && gramServing) {
    return gramServing;
  }

  // Try to match by measurement description
  const matchedServing = servings.find((s) => {
    const desc = s.measurementDescription?.toLowerCase() || '';
    return desc.includes(normalizedUnit) || desc.includes(unit);
  });

  if (matchedServing) {
    return matchedServing;
  }

  // Default to first serving (usually "serving" or "100g")
  return servings[0];
}

/**
 * Calculate number of servings based on quantity and unit
 */
function calculateServings(serving: Serving, quantity: number, unit: string): number {
  const normalizedUnit = normalizeUnit(unit);

  // If unit is grams and we have metric serving amount
  if (normalizedUnit === 'g' && serving.metricServingAmount) {
    return quantity / serving.metricServingAmount;
  }

  // Otherwise use quantity as number of servings
  return quantity;
}

/**
 * Normalize unit strings
 */
function normalizeUnit(unit: string): string {
  const unitMap: Record<string, string> = {
    gram: 'g',
    grams: 'g',
    gr: 'g',
    г: 'g',
    грамм: 'g',
    грамма: 'g',
    граммов: 'g',
    piece: 'piece',
    pieces: 'piece',
    шт: 'piece',
    штука: 'piece',
    штуки: 'piece',
    cup: 'cup',
    cups: 'cup',
    чашка: 'cup',
    tbsp: 'tbsp',
    tablespoon: 'tbsp',
    tsp: 'tsp',
    teaspoon: 'tsp',
    serving: 'serving',
    порция: 'serving',
  };

  return unitMap[unit.toLowerCase()] || unit.toLowerCase();
}
