/**
 * Daily Report Tool
 * Get nutrition summary for today or a specific date
 */
export function createDailyReportTool(db) {
    return {
        name: 'daily_nutrition_report',
        description: 'Get nutrition summary for today or a specific date. Shows calories, protein, carbs, fat consumed and comparison with goals.',
        parameters: {
            type: 'object',
            properties: {
                date: {
                    type: 'string',
                    description: 'Date in YYYY-MM-DD format. Defaults to today.',
                },
            },
        },
        handler: async (params, ctx) => {
            const date = params.date ? new Date(params.date) : new Date();
            // Get daily totals
            const totals = await db.getDailyTotals(ctx.odentity, date);
            // Get user goals
            const goals = await db.getGoals(ctx.odentity);
            // Get all entries for the day
            const entries = await db.getEntriesByDate(ctx.odentity, date);
            // Format entries by meal
            const byMeal = {
                breakfast: [],
                lunch: [],
                dinner: [],
                snack: [],
                other: [],
            };
            for (const entry of entries) {
                const meal = entry.mealType || 'other';
                byMeal[meal].push({
                    name: entry.foodName,
                    calories: Math.round(entry.calories),
                });
            }
            // Calculate progress toward goals
            const progress = goals
                ? {
                    calories: goals.targetCalories
                        ? { current: Math.round(totals.calories), target: goals.targetCalories, percent: Math.round((totals.calories / goals.targetCalories) * 100) }
                        : null,
                    protein: goals.targetProtein
                        ? { current: Math.round(totals.protein), target: goals.targetProtein, percent: Math.round((totals.protein / goals.targetProtein) * 100) }
                        : null,
                    carbs: goals.targetCarbs
                        ? { current: Math.round(totals.carbohydrates), target: goals.targetCarbs, percent: Math.round((totals.carbohydrates / goals.targetCarbs) * 100) }
                        : null,
                    fat: goals.targetFat
                        ? { current: Math.round(totals.fat), target: goals.targetFat, percent: Math.round((totals.fat / goals.targetFat) * 100) }
                        : null,
                }
                : null;
            return {
                success: true,
                date: totals.date,
                summary: {
                    calories: Math.round(totals.calories),
                    protein: Math.round(totals.protein),
                    carbs: Math.round(totals.carbohydrates),
                    fat: Math.round(totals.fat),
                    fiber: Math.round(totals.fiber),
                    entries: totals.entries,
                },
                progress,
                byMeal: {
                    breakfast: byMeal.breakfast.length > 0 ? byMeal.breakfast : null,
                    lunch: byMeal.lunch.length > 0 ? byMeal.lunch : null,
                    dinner: byMeal.dinner.length > 0 ? byMeal.dinner : null,
                    snack: byMeal.snack.length > 0 ? byMeal.snack : null,
                },
            };
        },
    };
}
//# sourceMappingURL=daily-report.js.map