/**
 * FatSecret Platform API Client
 * OAuth2 authentication and API requests to FatSecret
 */

import type { Food, Serving, FoodWithServings, PluginConfig } from '../types/index.js';

interface TokenData {
  accessToken: string;
  expiresAt: number;
}

export class FatSecretClient {
  private clientId: string;
  private clientSecret: string;
  private apiUrl = 'https://platform.fatsecret.com/rest/server.api';
  private tokenUrl = 'https://oauth.fatsecret.com/connect/token';
  private tokenData: TokenData | null = null;

  constructor(config: Pick<PluginConfig, 'fatsecretClientId' | 'fatsecretClientSecret'>) {
    this.clientId = config.fatsecretClientId;
    this.clientSecret = config.fatsecretClientSecret;
  }

  /**
   * Get OAuth2 access token using client credentials flow
   */
  private async getAccessToken(): Promise<string> {
    // Check if we have a valid token
    if (this.tokenData && Date.now() < this.tokenData.expiresAt) {
      return this.tokenData.accessToken;
    }

    // Request new token
    const credentials = Buffer.from(`${this.clientId}:${this.clientSecret}`).toString('base64');

    const response = await fetch(this.tokenUrl, {
      method: 'POST',
      headers: {
        'Authorization': `Basic ${credentials}`,
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: 'grant_type=client_credentials&scope=basic',
    });

    if (!response.ok) {
      throw new Error(`Failed to get FatSecret access token: ${response.status}`);
    }

    const data = await response.json() as { access_token: string; expires_in: number };

    this.tokenData = {
      accessToken: data.access_token,
      // Set expiration with 5 minute buffer
      expiresAt: Date.now() + (data.expires_in - 300) * 1000,
    };

    return this.tokenData.accessToken;
  }

  /**
   * Make authenticated request to FatSecret API
   */
  private async makeRequest(method: string, params: Record<string, string>): Promise<Record<string, unknown>> {
    const token = await this.getAccessToken();

    const formData = new URLSearchParams({
      method,
      format: 'json',
      ...params,
    });

    const response = await fetch(this.apiUrl, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData.toString(),
    });

    if (!response.ok) {
      throw new Error(`FatSecret API request failed: ${response.status}`);
    }

    return response.json() as Promise<Record<string, unknown>>;
  }

  /**
   * Search for foods in FatSecret database
   */
  async searchFoods(query: string, maxResults = 10, pageNumber = 0): Promise<Food[]> {
    try {
      const response = await this.makeRequest('foods.search', {
        search_expression: query,
        max_results: String(maxResults),
        page_number: String(pageNumber),
      });

      const foodsData = response.foods as { food?: unknown[] | Record<string, unknown> } | undefined;
      if (!foodsData) return [];

      let foodList = foodsData.food;

      // Handle single food result (API returns object instead of array)
      if (foodList && !Array.isArray(foodList)) {
        foodList = [foodList];
      }

      if (!Array.isArray(foodList)) return [];

      return foodList.map((item) => {
        const food = item as Record<string, unknown>;
        return {
          foodId: String(food.food_id ?? ''),
          foodName: String(food.food_name ?? ''),
          foodType: String(food.food_type ?? ''),
          brandName: food.brand_name ? String(food.brand_name) : undefined,
          foodDescription: food.food_description ? String(food.food_description) : undefined,
        };
      });
    } catch (error) {
      console.error('Error searching foods:', error);
      return [];
    }
  }

  /**
   * Get detailed food information by ID
   */
  async getFood(foodId: string): Promise<FoodWithServings | null> {
    try {
      const response = await this.makeRequest('food.get.v3', { food_id: foodId });

      const foodData = response.food as Record<string, unknown> | undefined;
      if (!foodData) return null;

      const servingsData = foodData.servings as { serving?: unknown[] | Record<string, unknown> } | undefined;
      let servingsList = servingsData?.serving;

      // Handle single serving result
      if (servingsList && !Array.isArray(servingsList)) {
        servingsList = [servingsList];
      }

      const servings: Serving[] = Array.isArray(servingsList)
        ? servingsList.map((item) => this.parseServing(item as Record<string, unknown>))
        : [];

      return {
        foodId: String(foodData.food_id ?? ''),
        foodName: String(foodData.food_name ?? ''),
        foodType: String(foodData.food_type ?? ''),
        brandName: foodData.brand_name ? String(foodData.brand_name) : undefined,
        servings,
      };
    } catch (error) {
      console.error(`Error getting food ${foodId}:`, error);
      return null;
    }
  }

  /**
   * Get all serving options for a food
   */
  async getServings(foodId: string): Promise<Serving[]> {
    const food = await this.getFood(foodId);
    return food?.servings ?? [];
  }

  /**
   * Parse serving data from API response
   */
  private parseServing(data: Record<string, unknown>): Serving {
    return {
      servingId: String(data.serving_id ?? ''),
      servingDescription: String(data.serving_description ?? ''),
      servingUrl: data.serving_url ? String(data.serving_url) : undefined,
      metricServingAmount: this.toNumber(data.metric_serving_amount),
      metricServingUnit: data.metric_serving_unit ? String(data.metric_serving_unit) : undefined,
      numberOfUnits: this.toNumber(data.number_of_units),
      measurementDescription: data.measurement_description ? String(data.measurement_description) : undefined,
      calories: this.toNumber(data.calories),
      carbohydrate: this.toNumber(data.carbohydrate),
      protein: this.toNumber(data.protein),
      fat: this.toNumber(data.fat),
      saturatedFat: this.toNumber(data.saturated_fat),
      polyunsaturatedFat: this.toNumber(data.polyunsaturated_fat),
      monounsaturatedFat: this.toNumber(data.monounsaturated_fat),
      transFat: this.toNumber(data.trans_fat),
      cholesterol: this.toNumber(data.cholesterol),
      sodium: this.toNumber(data.sodium),
      potassium: this.toNumber(data.potassium),
      fiber: this.toNumber(data.fiber),
      sugar: this.toNumber(data.sugar),
    };
  }

  /**
   * Convert value to number, return undefined if conversion fails
   */
  private toNumber(value: unknown): number | undefined {
    if (value === null || value === undefined) return undefined;
    const num = Number(value);
    return isNaN(num) ? undefined : num;
  }
}
