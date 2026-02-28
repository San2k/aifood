/**
 * Weekly Report Tool
 * Get nutrition summary for the past 7 days
 */
import type { DatabaseService } from '../services/database.js';
import type { ReportParams } from '../types/index.js';
interface ToolContext {
    odentity: string;
}
export declare function createWeeklyReportTool(db: DatabaseService): {
    name: string;
    description: string;
    parameters: {
        type: string;
        properties: {
            endDate: {
                type: string;
                description: string;
            };
        };
    };
    handler: (params: ReportParams, ctx: ToolContext) => Promise<{
        success: boolean;
        period: {
            start: string;
            end: string;
            daysTracked: number;
        };
        averages: {
            calories: number;
            protein: number;
            carbs: number;
            fat: number;
            fiber: number;
        };
        totals: {
            calories: number;
            protein: number;
            carbs: number;
            fat: number;
        };
        daily: {
            date: string;
            calories: number;
            protein: number;
            carbs: number;
            fat: number;
            entries: number;
        }[];
        goalAdherence: {
            daysOnTarget: number;
            daysOver: number;
            daysUnder: number;
        } | null;
    }>;
};
export {};
//# sourceMappingURL=weekly-report.d.ts.map