/**
 * PostgreSQL Database Service for AiFood
 * Handles food log entries and user goals
 */

import pg from 'pg';
import type { FoodLogEntry, UserGoals, DailyTotals, MealType, PluginConfig } from '../types/index.js';

const { Pool } = pg;

export class DatabaseService {
  private pool: pg.Pool;

  constructor(config: Pick<PluginConfig, 'databaseUrl'>) {
    this.pool = new Pool({
      connectionString: config.databaseUrl,
    });
  }

  /**
   * Initialize database tables
   */
  async initialize(): Promise<void> {
    const client = await this.pool.connect();
    try {
      await client.query(`
        CREATE TABLE IF NOT EXISTS food_log_entry (
          id BIGSERIAL PRIMARY KEY,
          odentity VARCHAR(255) NOT NULL,
          food_id VARCHAR(255),
          food_name VARCHAR(500) NOT NULL,
          brand_name VARCHAR(255),
          serving_id VARCHAR(255),
          serving_description VARCHAR(500),
          serving_size NUMERIC(10, 2),
          serving_unit VARCHAR(50),
          number_of_servings NUMERIC(10, 2) DEFAULT 1.0 NOT NULL,
          calories NUMERIC(10, 2) NOT NULL,
          protein NUMERIC(10, 2),
          carbohydrates NUMERIC(10, 2),
          fat NUMERIC(10, 2),
          fiber NUMERIC(10, 2),
          sugar NUMERIC(10, 2),
          sodium NUMERIC(10, 2),
          meal_type VARCHAR(20),
          consumed_at TIMESTAMPTZ NOT NULL,
          created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
          is_deleted BOOLEAN DEFAULT FALSE NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_food_log_odentity ON food_log_entry(odentity);
        CREATE INDEX IF NOT EXISTS idx_food_log_consumed_at ON food_log_entry(consumed_at);

        CREATE TABLE IF NOT EXISTS user_goals (
          odentity VARCHAR(255) PRIMARY KEY,
          target_calories INTEGER,
          target_protein INTEGER,
          target_carbs INTEGER,
          target_fat INTEGER,
          target_fiber INTEGER,
          created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
          updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
        );
      `);
    } finally {
      client.release();
    }
  }

  /**
   * Log a food entry
   */
  async logFood(entry: Omit<FoodLogEntry, 'id' | 'createdAt' | 'isDeleted'>): Promise<FoodLogEntry> {
    const result = await this.pool.query(
      `INSERT INTO food_log_entry (
        odentity, food_id, food_name, brand_name, serving_id, serving_description,
        serving_size, serving_unit, number_of_servings, calories, protein,
        carbohydrates, fat, fiber, sugar, sodium, meal_type, consumed_at
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18)
      RETURNING *`,
      [
        entry.odentity,
        entry.foodId,
        entry.foodName,
        entry.brandName,
        entry.servingId,
        entry.servingDescription,
        entry.servingSize,
        entry.servingUnit,
        entry.numberOfServings,
        entry.calories,
        entry.protein,
        entry.carbohydrates,
        entry.fat,
        entry.fiber,
        entry.sugar,
        entry.sodium,
        entry.mealType,
        entry.consumedAt,
      ]
    );

    return this.mapRowToEntry(result.rows[0] as Record<string, unknown>);
  }

  /**
   * Get entries for a specific date
   */
  async getEntriesByDate(odentity: string, date: Date): Promise<FoodLogEntry[]> {
    const startOfDay = new Date(date);
    startOfDay.setHours(0, 0, 0, 0);

    const endOfDay = new Date(date);
    endOfDay.setHours(23, 59, 59, 999);

    const result = await this.pool.query(
      `SELECT * FROM food_log_entry
       WHERE odentity = $1
         AND consumed_at >= $2
         AND consumed_at <= $3
         AND is_deleted = FALSE
       ORDER BY consumed_at ASC`,
      [odentity, startOfDay, endOfDay]
    );

    return result.rows.map((row) => this.mapRowToEntry(row));
  }

  /**
   * Get entries for a date range
   */
  async getEntriesByDateRange(odentity: string, startDate: Date, endDate: Date): Promise<FoodLogEntry[]> {
    const result = await this.pool.query(
      `SELECT * FROM food_log_entry
       WHERE odentity = $1
         AND consumed_at >= $2
         AND consumed_at <= $3
         AND is_deleted = FALSE
       ORDER BY consumed_at ASC`,
      [odentity, startDate, endDate]
    );

    return result.rows.map((row) => this.mapRowToEntry(row));
  }

  /**
   * Calculate daily totals
   */
  async getDailyTotals(odentity: string, date: Date): Promise<DailyTotals> {
    const entries = await this.getEntriesByDate(odentity, date);

    const totals: DailyTotals = {
      date: date.toISOString().split('T')[0],
      calories: 0,
      protein: 0,
      carbohydrates: 0,
      fat: 0,
      fiber: 0,
      sugar: 0,
      sodium: 0,
      entries: entries.length,
    };

    for (const entry of entries) {
      totals.calories += entry.calories;
      totals.protein += entry.protein ?? 0;
      totals.carbohydrates += entry.carbohydrates ?? 0;
      totals.fat += entry.fat ?? 0;
      totals.fiber += entry.fiber ?? 0;
      totals.sugar += entry.sugar ?? 0;
      totals.sodium += entry.sodium ?? 0;
    }

    return totals;
  }

  /**
   * Calculate weekly totals (average per day)
   */
  async getWeeklyTotals(odentity: string, endDate: Date): Promise<DailyTotals[]> {
    const startDate = new Date(endDate);
    startDate.setDate(startDate.getDate() - 6);

    const dailyTotals: DailyTotals[] = [];

    for (let i = 0; i < 7; i++) {
      const date = new Date(startDate);
      date.setDate(date.getDate() + i);
      const totals = await this.getDailyTotals(odentity, date);
      dailyTotals.push(totals);
    }

    return dailyTotals;
  }

  /**
   * Soft delete an entry
   */
  async deleteEntry(id: number, odentity: string): Promise<boolean> {
    const result = await this.pool.query(
      `UPDATE food_log_entry
       SET is_deleted = TRUE
       WHERE id = $1 AND odentity = $2`,
      [id, odentity]
    );

    return (result.rowCount ?? 0) > 0;
  }

  /**
   * Get user goals
   */
  async getGoals(odentity: string): Promise<UserGoals | null> {
    const result = await this.pool.query(
      'SELECT * FROM user_goals WHERE odentity = $1',
      [odentity]
    );

    if (result.rows.length === 0) return null;

    const row = result.rows[0];
    return {
      odentity: row.odentity,
      targetCalories: row.target_calories,
      targetProtein: row.target_protein,
      targetCarbs: row.target_carbs,
      targetFat: row.target_fat,
      targetFiber: row.target_fiber,
      createdAt: row.created_at,
      updatedAt: row.updated_at,
    };
  }

  /**
   * Set user goals
   */
  async setGoals(goals: UserGoals): Promise<UserGoals> {
    const result = await this.pool.query(
      `INSERT INTO user_goals (odentity, target_calories, target_protein, target_carbs, target_fat, target_fiber)
       VALUES ($1, $2, $3, $4, $5, $6)
       ON CONFLICT (odentity) DO UPDATE SET
         target_calories = COALESCE($2, user_goals.target_calories),
         target_protein = COALESCE($3, user_goals.target_protein),
         target_carbs = COALESCE($4, user_goals.target_carbs),
         target_fat = COALESCE($5, user_goals.target_fat),
         target_fiber = COALESCE($6, user_goals.target_fiber),
         updated_at = NOW()
       RETURNING *`,
      [
        goals.odentity,
        goals.targetCalories,
        goals.targetProtein,
        goals.targetCarbs,
        goals.targetFat,
        goals.targetFiber,
      ]
    );

    const row = result.rows[0];
    return {
      odentity: row.odentity,
      targetCalories: row.target_calories,
      targetProtein: row.target_protein,
      targetCarbs: row.target_carbs,
      targetFat: row.target_fat,
      targetFiber: row.target_fiber,
      createdAt: row.created_at,
      updatedAt: row.updated_at,
    };
  }

  /**
   * Close database connection
   */
  async close(): Promise<void> {
    await this.pool.end();
  }

  /**
   * Map database row to FoodLogEntry
   */
  private mapRowToEntry(row: Record<string, unknown>): FoodLogEntry {
    return {
      id: Number(row.id),
      odentity: String(row.odentity),
      foodId: row.food_id ? String(row.food_id) : '',
      foodName: String(row.food_name),
      brandName: row.brand_name ? String(row.brand_name) : undefined,
      servingId: row.serving_id ? String(row.serving_id) : undefined,
      servingDescription: row.serving_description ? String(row.serving_description) : undefined,
      servingSize: row.serving_size ? Number(row.serving_size) : undefined,
      servingUnit: row.serving_unit ? String(row.serving_unit) : undefined,
      numberOfServings: Number(row.number_of_servings),
      calories: Number(row.calories),
      protein: row.protein ? Number(row.protein) : undefined,
      carbohydrates: row.carbohydrates ? Number(row.carbohydrates) : undefined,
      fat: row.fat ? Number(row.fat) : undefined,
      fiber: row.fiber ? Number(row.fiber) : undefined,
      sugar: row.sugar ? Number(row.sugar) : undefined,
      sodium: row.sodium ? Number(row.sodium) : undefined,
      mealType: row.meal_type as MealType | undefined,
      consumedAt: new Date(row.consumed_at as string),
      createdAt: new Date(row.created_at as string),
      isDeleted: Boolean(row.is_deleted),
    };
  }
}
