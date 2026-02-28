/**
 * Set Goals Tool
 * Set daily nutrition targets for the user
 */
import type { DatabaseService } from '../services/database.js';
import type { SetGoalsParams } from '../types/index.js';
interface ToolContext {
    odentity: string;
}
export declare function createSetGoalsTool(db: DatabaseService): {
    name: string;
    description: string;
    parameters: {
        type: string;
        properties: {
            calories: {
                type: string;
                description: string;
            };
            protein: {
                type: string;
                description: string;
            };
            carbs: {
                type: string;
                description: string;
            };
            fat: {
                type: string;
                description: string;
            };
            fiber: {
                type: string;
                description: string;
            };
        };
    };
    handler: (params: SetGoalsParams, ctx: ToolContext) => Promise<{
        success: boolean;
        message: string;
        goals?: undefined;
    } | {
        success: boolean;
        message: string;
        goals: {
            calories: number | undefined;
            protein: number | undefined;
            carbs: number | undefined;
            fat: number | undefined;
            fiber: number | undefined;
        };
    }>;
};
export {};
//# sourceMappingURL=set-goals.d.ts.map