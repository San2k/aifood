/**
 * Weekly Report Tool
 * Get nutrition summary for the past 7 days
 */
export function createWeeklyReportTool(db) {
    return {
        name: 'weekly_nutrition_report',
        description: 'Get nutrition summary for the past 7 days. Shows daily averages and trends.',
        parameters: {
            type: 'object',
            properties: {
                endDate: {
                    type: 'string',
                    description: 'End date of the week in YYYY-MM-DD format. Defaults to today.',
                },
            },
        },
        handler: async (params, ctx) => {
            const endDate = params.endDate ? new Date(params.endDate) : new Date();
            // Get weekly totals
            const dailyTotals = await db.getWeeklyTotals(ctx.odentity, endDate);
            // Get user goals for comparison
            const goals = await db.getGoals(ctx.odentity);
            // Calculate averages
            const daysWithEntries = dailyTotals.filter((d) => d.entries > 0);
            const numDays = daysWithEntries.length || 1;
            const totals = {
                calories: dailyTotals.reduce((sum, d) => sum + d.calories, 0),
                protein: dailyTotals.reduce((sum, d) => sum + d.protein, 0),
                carbs: dailyTotals.reduce((sum, d) => sum + d.carbohydrates, 0),
                fat: dailyTotals.reduce((sum, d) => sum + d.fat, 0),
                fiber: dailyTotals.reduce((sum, d) => sum + d.fiber, 0),
            };
            const averages = {
                calories: Math.round(totals.calories / numDays),
                protein: Math.round(totals.protein / numDays),
                carbs: Math.round(totals.carbs / numDays),
                fat: Math.round(totals.fat / numDays),
                fiber: Math.round(totals.fiber / numDays),
            };
            // Format daily breakdown
            const daily = dailyTotals.map((d) => ({
                date: d.date,
                calories: Math.round(d.calories),
                protein: Math.round(d.protein),
                carbs: Math.round(d.carbohydrates),
                fat: Math.round(d.fat),
                entries: d.entries,
            }));
            // Calculate goal adherence
            const goalAdherence = goals?.targetCalories
                ? {
                    daysOnTarget: daysWithEntries.filter((d) => d.calories >= goals.targetCalories * 0.9 && d.calories <= goals.targetCalories * 1.1).length,
                    daysOver: daysWithEntries.filter((d) => d.calories > goals.targetCalories * 1.1).length,
                    daysUnder: daysWithEntries.filter((d) => d.calories < goals.targetCalories * 0.9).length,
                }
                : null;
            return {
                success: true,
                period: {
                    start: dailyTotals[0].date,
                    end: dailyTotals[6].date,
                    daysTracked: daysWithEntries.length,
                },
                averages,
                totals: {
                    calories: Math.round(totals.calories),
                    protein: Math.round(totals.protein),
                    carbs: Math.round(totals.carbs),
                    fat: Math.round(totals.fat),
                },
                daily,
                goalAdherence,
            };
        },
    };
}
//# sourceMappingURL=weekly-report.js.map