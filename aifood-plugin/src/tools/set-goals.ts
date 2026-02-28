/**
 * Set Goals Tool
 * Set daily nutrition targets for the user
 */

import type { DatabaseService } from '../services/database.js';
import type { SetGoalsParams } from '../types/index.js';

interface ToolContext {
  odentity: string;
}

export function createSetGoalsTool(db: DatabaseService) {
  return {
    name: 'set_nutrition_goals',
    description: 'Set daily nutrition goals/targets for calories, protein, carbs, fat. Used to track progress and get personalized recommendations.',
    parameters: {
      type: 'object',
      properties: {
        calories: {
          type: 'number',
          description: 'Daily calorie target (e.g., 2000)',
        },
        protein: {
          type: 'number',
          description: 'Daily protein target in grams (e.g., 150)',
        },
        carbs: {
          type: 'number',
          description: 'Daily carbohydrate target in grams (e.g., 200)',
        },
        fat: {
          type: 'number',
          description: 'Daily fat target in grams (e.g., 65)',
        },
        fiber: {
          type: 'number',
          description: 'Daily fiber target in grams (e.g., 30)',
        },
      },
    },
    handler: async (params: SetGoalsParams, ctx: ToolContext) => {
      const { calories, protein, carbs, fat, fiber } = params;

      // At least one goal must be provided
      if (!calories && !protein && !carbs && !fat && !fiber) {
        return {
          success: false,
          message: 'Please provide at least one nutrition goal (calories, protein, carbs, fat, or fiber).',
        };
      }

      // Get existing goals
      const existingGoals = await db.getGoals(ctx.odentity);

      // Update goals
      const updatedGoals = await db.setGoals({
        odentity: ctx.odentity,
        targetCalories: calories ?? existingGoals?.targetCalories,
        targetProtein: protein ?? existingGoals?.targetProtein,
        targetCarbs: carbs ?? existingGoals?.targetCarbs,
        targetFat: fat ?? existingGoals?.targetFat,
        targetFiber: fiber ?? existingGoals?.targetFiber,
        createdAt: existingGoals?.createdAt ?? new Date(),
        updatedAt: new Date(),
      });

      return {
        success: true,
        message: 'Nutrition goals updated successfully',
        goals: {
          calories: updatedGoals.targetCalories,
          protein: updatedGoals.targetProtein,
          carbs: updatedGoals.targetCarbs,
          fat: updatedGoals.targetFat,
          fiber: updatedGoals.targetFiber,
        },
      };
    },
  };
}
