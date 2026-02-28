/**
 * Daily Report Tool
 * Get nutrition summary for today or a specific date
 */
import type { DatabaseService } from '../services/database.js';
import type { ReportParams } from '../types/index.js';
interface ToolContext {
    odentity: string;
}
export declare function createDailyReportTool(db: DatabaseService): {
    name: string;
    description: string;
    parameters: {
        type: string;
        properties: {
            date: {
                type: string;
                description: string;
            };
        };
    };
    handler: (params: ReportParams, ctx: ToolContext) => Promise<{
        success: boolean;
        date: string;
        summary: {
            calories: number;
            protein: number;
            carbs: number;
            fat: number;
            fiber: number;
            entries: number;
        };
        progress: {
            calories: {
                current: number;
                target: number;
                percent: number;
            } | null;
            protein: {
                current: number;
                target: number;
                percent: number;
            } | null;
            carbs: {
                current: number;
                target: number;
                percent: number;
            } | null;
            fat: {
                current: number;
                target: number;
                percent: number;
            } | null;
        } | null;
        byMeal: {
            breakfast: {
                name: string;
                calories: number;
            }[] | null;
            lunch: {
                name: string;
                calories: number;
            }[] | null;
            dinner: {
                name: string;
                calories: number;
            }[] | null;
            snack: {
                name: string;
                calories: number;
            }[] | null;
        };
    }>;
};
export {};
//# sourceMappingURL=daily-report.d.ts.map