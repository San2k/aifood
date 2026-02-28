/**
 * Search Food Tool
 * Search FatSecret database for food items
 */

import type { FatSecretClient } from '../services/fatsecret.js';
import type { SearchFoodParams } from '../types/index.js';

export function createSearchFoodTool(fatsecret: FatSecretClient) {
  return {
    name: 'search_food',
    description: 'Search the FatSecret database for food items and their nutritional information. Use this when the user wants to find calories or nutrition info for a specific food without logging it.',
    parameters: {
      type: 'object',
      properties: {
        query: {
          type: 'string',
          description: 'Food name to search for (e.g., "chicken breast", "apple", "гречка")',
        },
        maxResults: {
          type: 'number',
          description: 'Maximum number of results to return (default: 5, max: 10)',
        },
      },
      required: ['query'],
    },
    handler: async (params: SearchFoodParams) => {
      const { query, maxResults = 5 } = params;

      // Search foods
      const foods = await fatsecret.searchFoods(query, Math.min(maxResults, 10));

      if (foods.length === 0) {
        return {
          success: false,
          message: `No foods found for "${query}". Try a different search term.`,
          results: [],
        };
      }

      // Get detailed info for each food
      const results = await Promise.all(
        foods.slice(0, maxResults).map(async (food) => {
          const details = await fatsecret.getFood(food.foodId);

          if (!details || details.servings.length === 0) {
            return {
              name: food.foodName,
              brand: food.brandName,
              description: food.foodDescription,
              servings: [],
            };
          }

          // Format servings info
          const servings = details.servings.slice(0, 3).map((s) => ({
            description: s.servingDescription,
            calories: s.calories ? Math.round(s.calories) : null,
            protein: s.protein ? Math.round(s.protein * 10) / 10 : null,
            carbs: s.carbohydrate ? Math.round(s.carbohydrate * 10) / 10 : null,
            fat: s.fat ? Math.round(s.fat * 10) / 10 : null,
          }));

          return {
            name: details.foodName,
            brand: details.brandName,
            servings,
          };
        })
      );

      return {
        success: true,
        message: `Found ${results.length} results for "${query}"`,
        results,
      };
    },
  };
}
