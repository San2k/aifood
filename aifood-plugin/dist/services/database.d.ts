/**
 * PostgreSQL Database Service for AiFood
 * Handles food log entries and user goals
 */
import type { FoodLogEntry, UserGoals, DailyTotals, PluginConfig } from '../types/index.js';
export declare class DatabaseService {
    private pool;
    constructor(config: Pick<PluginConfig, 'databaseUrl'>);
    /**
     * Initialize database tables
     */
    initialize(): Promise<void>;
    /**
     * Log a food entry
     */
    logFood(entry: Omit<FoodLogEntry, 'id' | 'createdAt' | 'isDeleted'>): Promise<FoodLogEntry>;
    /**
     * Get entries for a specific date
     */
    getEntriesByDate(odentity: string, date: Date): Promise<FoodLogEntry[]>;
    /**
     * Get entries for a date range
     */
    getEntriesByDateRange(odentity: string, startDate: Date, endDate: Date): Promise<FoodLogEntry[]>;
    /**
     * Calculate daily totals
     */
    getDailyTotals(odentity: string, date: Date): Promise<DailyTotals>;
    /**
     * Calculate weekly totals (average per day)
     */
    getWeeklyTotals(odentity: string, endDate: Date): Promise<DailyTotals[]>;
    /**
     * Soft delete an entry
     */
    deleteEntry(id: number, odentity: string): Promise<boolean>;
    /**
     * Get user goals
     */
    getGoals(odentity: string): Promise<UserGoals | null>;
    /**
     * Set user goals
     */
    setGoals(goals: UserGoals): Promise<UserGoals>;
    /**
     * Close database connection
     */
    close(): Promise<void>;
    /**
     * Map database row to FoodLogEntry
     */
    private mapRowToEntry;
}
//# sourceMappingURL=database.d.ts.map