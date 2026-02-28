/**
 * AiFood OpenClaw Plugin Types
 */

// Plugin configuration
export interface PluginConfig {
  databaseUrl: string;
  // FatSecret API (optional, for future use)
  fatsecretClientId?: string;
  fatsecretClientSecret?: string;
}

// FatSecret API types
export interface Food {
  foodId: string;
  foodName: string;
  foodType: string;
  brandName?: string;
  foodDescription?: string;
}

export interface Serving {
  servingId: string;
  servingDescription: string;
  servingUrl?: string;
  metricServingAmount?: number;
  metricServingUnit?: string;
  numberOfUnits?: number;
  measurementDescription?: string;
  calories?: number;
  carbohydrate?: number;
  protein?: number;
  fat?: number;
  saturatedFat?: number;
  polyunsaturatedFat?: number;
  monounsaturatedFat?: number;
  transFat?: number;
  cholesterol?: number;
  sodium?: number;
  potassium?: number;
  fiber?: number;
  sugar?: number;
}

export interface FoodWithServings extends Food {
  servings: Serving[];
}

// Database types
export type MealType = 'breakfast' | 'lunch' | 'dinner' | 'snack';

export interface FoodLogEntry {
  id: number;
  odentity: string; // OpenClaw user identity
  foodId: string;
  foodName: string;
  brandName?: string;
  servingId?: string;
  servingDescription?: string;
  servingSize?: number;
  servingUnit?: string;
  numberOfServings: number;
  calories: number;
  protein?: number;
  carbohydrates?: number;
  fat?: number;
  fiber?: number;
  sugar?: number;
  sodium?: number;
  mealType?: MealType;
  consumedAt: Date;
  createdAt: Date;
  isDeleted: boolean;
}

export interface UserGoals {
  odentity: string;
  targetCalories?: number;
  targetProtein?: number;
  targetCarbs?: number;
  targetFat?: number;
  targetFiber?: number;
  createdAt: Date;
  updatedAt: Date;
}

export interface DailyTotals {
  date: string;
  calories: number;
  protein: number;
  carbohydrates: number;
  fat: number;
  fiber: number;
  sugar: number;
  sodium: number;
  entries: number;
}

// Tool parameters
export interface LogFoodParams {
  food: string;
  amount?: string;
  meal?: MealType;
  date?: string;
}

export interface SearchFoodParams {
  query: string;
  maxResults?: number;
}

export interface ReportParams {
  date?: string;
  startDate?: string;
  endDate?: string;
}

export interface SetGoalsParams {
  calories?: number;
  protein?: number;
  carbs?: number;
  fat?: number;
  fiber?: number;
}
