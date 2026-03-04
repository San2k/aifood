/**
 * AiFood OpenClaw Plugin
 * Nutrition tracking plugin
 */
import { Type } from '@sinclair/typebox';
import { DatabaseService } from './services/database.js';
import * as fs from 'fs';
// TypeBox Schema definitions (compatible with OpenClaw's pi-agent-core)
const LogFoodSchema = Type.Object({
    foodName: Type.String({ description: 'Name of the food (e.g., "2 eggs", "chicken breast 150g")' }),
    calories: Type.Number({ description: 'Calories in kcal' }),
    protein: Type.Optional(Type.Number({ description: 'Protein in grams' })),
    carbs: Type.Optional(Type.Number({ description: 'Carbohydrates in grams' })),
    fat: Type.Optional(Type.Number({ description: 'Fat in grams' })),
    fiber: Type.Optional(Type.Number({ description: 'Fiber in grams' })),
    meal: Type.Optional(Type.String({ description: 'Meal type: breakfast, lunch, dinner, snack' })),
    date: Type.Optional(Type.String({ description: 'Date in YYYY-MM-DD format. Defaults to today.' })),
});
const DailyReportSchema = Type.Object({
    date: Type.Optional(Type.String({ description: 'Date in YYYY-MM-DD format. Defaults to today.' })),
});
const SetGoalsSchema = Type.Object({
    calories: Type.Optional(Type.Number({ description: 'Daily calorie target' })),
    protein: Type.Optional(Type.Number({ description: 'Daily protein target in grams' })),
    carbs: Type.Optional(Type.Number({ description: 'Daily carbohydrate target in grams' })),
    fat: Type.Optional(Type.Number({ description: 'Daily fat target in grams' })),
    fiber: Type.Optional(Type.Number({ description: 'Daily fiber target in grams' })),
});
const LogFoodFromPhotoSchema = Type.Object({
    photoUrl: Type.String({ description: 'URL of the nutrition label photo' }),
    meal: Type.Optional(Type.String({ description: 'Meal type: breakfast, lunch, dinner, snack' })),
    date: Type.Optional(Type.String({ description: 'Date in YYYY-MM-DD format. Defaults to today.' })),
});
const ConfirmFoodFromPhotoSchema = Type.Object({
    grams: Type.Number({ description: 'Amount consumed in grams (e.g., 150)' }),
    meal: Type.Optional(Type.String({ description: 'Meal type: breakfast, lunch, dinner, snack' })),
});
let db = null;
export default {
    id: 'aifood',
    name: 'AiFood Nutrition Tracker',
    configSchema: {
        type: 'object',
        properties: {
            databaseUrl: {
                type: 'string',
                description: 'PostgreSQL connection URL',
                default: 'postgresql://aifood:aifood_secure_password_2024@localhost:5433/aifood',
            },
            agentApiUrl: {
                type: 'string',
                description: 'Agent API URL for label processing',
                default: 'http://localhost:8000',
            },
        },
    },
    async register(api) {
        const config = api.pluginConfig || api.config || {};
        // Initialize database
        const dbUrl = config.databaseUrl ||
            'postgresql://aifood:aifood_secure_password_2024@localhost:5433/aifood';
        db = new DatabaseService({ databaseUrl: dbUrl });
        // Initialize database tables
        try {
            await db.initialize();
            api.logger.info('AiFood: Database initialized');
        }
        catch (error) {
            api.logger.error('AiFood: Failed to initialize database', error);
            return;
        }
        // Using standard OpenAI tool format
        api.logger.info('AiFood: Using standard OpenAI tool format');
        // Register log_food tool
        api.registerTool({
            name: 'log_food',
            label: 'Log Food',
            description: 'Log food consumption with nutritional data. Use this when the user wants to record what they ate.',
            parameters: LogFoodSchema,
            async execute(_toolCallId, params) {
                const { foodName, calories, protein, carbs, fat, fiber, meal, date } = params;
                const consumedAt = date ? new Date(date) : new Date();
                consumedAt.setHours(new Date().getHours(), new Date().getMinutes());
                const entry = await db.logFood({
                    odentity: 'default',
                    foodId: '',
                    foodName,
                    brandName: undefined,
                    servingId: undefined,
                    servingDescription: undefined,
                    servingSize: undefined,
                    servingUnit: undefined,
                    numberOfServings: 1,
                    calories,
                    protein,
                    carbohydrates: carbs,
                    fat,
                    fiber,
                    sugar: undefined,
                    sodium: undefined,
                    mealType: meal,
                    consumedAt,
                });
                const totals = await db.getDailyTotals('default', consumedAt);
                const message = `Logged: ${foodName} (${Math.round(calories)} kcal). Daily total: ${Math.round(totals.calories)} kcal`;
                return {
                    content: [{ type: 'text', text: message }],
                    details: {
                        success: true,
                        entry: {
                            id: entry.id,
                            food: foodName,
                            calories: Math.round(calories),
                            protein: protein ? Math.round(protein) : null,
                            carbs: carbs ? Math.round(carbs) : null,
                            fat: fat ? Math.round(fat) : null,
                        },
                        dailyTotals: {
                            calories: Math.round(totals.calories),
                            protein: Math.round(totals.protein),
                            carbs: Math.round(totals.carbohydrates),
                            fat: Math.round(totals.fat),
                            entries: totals.entries,
                        },
                    },
                };
            },
        });
        // Helper function to create progress bar
        const createProgressBar = (current, target, width = 10) => {
            const percentage = Math.min(current / target, 1);
            const filled = Math.round(percentage * width);
            const empty = width - filled;
            const bar = '█'.repeat(filled) + '░'.repeat(empty);
            const pct = Math.round(percentage * 100);
            return `${bar} ${pct}%`;
        };
        // Register daily_nutrition_report tool
        api.registerTool({
            name: 'daily_nutrition_report',
            label: 'Daily Nutrition Report',
            description: 'Get nutrition summary for today or a specific date. Shows calories, protein, carbs, fat consumed with progress bars.',
            parameters: DailyReportSchema,
            async execute(_toolCallId, params) {
                const { date } = params;
                const targetDate = date ? new Date(date) : new Date();
                const totals = await db.getDailyTotals('default', targetDate);
                const goals = await db.getGoals('default');
                const entries = await db.getEntriesByDate('default', targetDate);
                const dateStr = targetDate.toISOString().split('T')[0];
                let message = `📊 Отчёт за ${dateStr}\n\n`;
                // Calories
                message += `🔥 Калории: ${Math.round(totals.calories)}`;
                if (goals?.targetCalories) {
                    message += ` / ${goals.targetCalories} ккал\n`;
                    message += `   ${createProgressBar(totals.calories, goals.targetCalories)}\n`;
                }
                else {
                    message += ` ккал\n`;
                }
                // Protein
                message += `\n🥩 Белок: ${Math.round(totals.protein)}`;
                if (goals?.targetProtein) {
                    message += ` / ${goals.targetProtein}г\n`;
                    message += `   ${createProgressBar(totals.protein, goals.targetProtein)}\n`;
                }
                else {
                    message += `г\n`;
                }
                // Carbs
                message += `\n🍞 Углеводы: ${Math.round(totals.carbohydrates)}`;
                if (goals?.targetCarbs) {
                    message += ` / ${goals.targetCarbs}г\n`;
                    message += `   ${createProgressBar(totals.carbohydrates, goals.targetCarbs)}\n`;
                }
                else {
                    message += `г\n`;
                }
                // Fat
                message += `\n🧈 Жиры: ${Math.round(totals.fat)}`;
                if (goals?.targetFat) {
                    message += ` / ${goals.targetFat}г\n`;
                    message += `   ${createProgressBar(totals.fat, goals.targetFat)}\n`;
                }
                else {
                    message += `г\n`;
                }
                // Fiber (if goal set)
                if (goals?.targetFiber) {
                    message += `\n🥬 Клетчатка: ${Math.round(totals.fiber)} / ${goals.targetFiber}г\n`;
                    message += `   ${createProgressBar(totals.fiber, goals.targetFiber)}\n`;
                }
                message += `\n📝 Записей: ${entries.length}`;
                return {
                    content: [{ type: 'text', text: message }],
                    details: {
                        success: true,
                        date: dateStr,
                        summary: totals,
                        goals: goals || null,
                        entries: entries.map((e) => ({
                            food: e.foodName,
                            calories: Math.round(e.calories),
                            meal: e.mealType,
                        })),
                    },
                };
            },
        });
        // Register set_nutrition_goals tool
        api.registerTool({
            name: 'set_nutrition_goals',
            label: 'Set Nutrition Goals',
            description: 'Set daily nutrition goals for calories, protein, carbs, and fat.',
            parameters: SetGoalsSchema,
            async execute(_toolCallId, params) {
                api.logger.info(`AiFood: set_nutrition_goals called with params: ${JSON.stringify(params)}`);
                try {
                    const { calories, protein, carbs, fat, fiber } = params;
                    if (!calories && !protein && !carbs && !fat && !fiber) {
                        return {
                            content: [{ type: 'text', text: 'Please specify at least one goal (calories, protein, carbs, fat, or fiber)' }],
                            details: { success: false },
                        };
                    }
                    const goals = await db.setGoals({
                        odentity: 'default',
                        targetCalories: calories,
                        targetProtein: protein,
                        targetCarbs: carbs,
                        targetFat: fat,
                        targetFiber: fiber,
                        createdAt: new Date(),
                        updatedAt: new Date(),
                    });
                    let message = 'Nutrition goals updated:\n';
                    if (goals.targetCalories)
                        message += `Calories: ${goals.targetCalories} kcal\n`;
                    if (goals.targetProtein)
                        message += `Protein: ${goals.targetProtein}g\n`;
                    if (goals.targetCarbs)
                        message += `Carbs: ${goals.targetCarbs}g\n`;
                    if (goals.targetFat)
                        message += `Fat: ${goals.targetFat}g\n`;
                    if (goals.targetFiber)
                        message += `Fiber: ${goals.targetFiber}g\n`;
                    api.logger.info(`AiFood: set_nutrition_goals success: ${message.trim()}`);
                    return {
                        content: [{ type: 'text', text: message.trim() }],
                        details: {
                            success: true,
                            goals: {
                                calories: goals.targetCalories,
                                protein: goals.targetProtein,
                                carbs: goals.targetCarbs,
                                fat: goals.targetFat,
                                fiber: goals.targetFiber,
                            },
                        },
                    };
                }
                catch (error) {
                    api.logger.error(`AiFood: set_nutrition_goals error: ${error}`);
                    return {
                        content: [{ type: 'text', text: `Error setting goals: ${error}` }],
                        details: { success: false, error: String(error) },
                    };
                }
            },
        });
        // Register log_food_from_photo tool
        api.registerTool({
            name: 'log_food_from_photo',
            label: 'Log Food from Photo',
            description: 'Process nutrition label photo to extract and log product data. Use when user sends a photo of a nutrition label.',
            parameters: LogFoodFromPhotoSchema,
            async execute(_toolCallId, params) {
                const { photoUrl, meal, date } = params;
                const agentApiUrl = config.agentApiUrl || 'http://localhost:8000';
                api.logger.info(`AiFood: Processing nutrition label photo: ${photoUrl}`);
                try {
                    // Check if photoUrl is a local file path or a URL
                    const isLocalFile = photoUrl.startsWith('/') || photoUrl.startsWith('file://');
                    let requestBody;
                    if (isLocalFile) {
                        // Read local file and encode as base64
                        api.logger.info(`AiFood: Reading local file: ${photoUrl}`);
                        const filePath = photoUrl.replace('file://', '');
                        if (!fs.existsSync(filePath)) {
                            throw new Error(`File not found: ${filePath}`);
                        }
                        const imageBuffer = fs.readFileSync(filePath);
                        const imageBase64 = imageBuffer.toString('base64');
                        requestBody = {
                            odentity: 'default',
                            image_base64: imageBase64,
                            meal_type: meal,
                            consumed_at: date ? new Date(date).toISOString() : undefined,
                        };
                    }
                    else {
                        // Use URL (original behavior)
                        requestBody = {
                            odentity: 'default',
                            photo_url: photoUrl,
                            meal_type: meal,
                            consumed_at: date ? new Date(date).toISOString() : undefined,
                        };
                    }
                    // Step 1: Submit photo for processing
                    const processResponse = await fetch(`${agentApiUrl}/v1/process_label`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(requestBody),
                    });
                    if (!processResponse.ok) {
                        throw new Error(`Agent API error: ${processResponse.statusText}`);
                    }
                    const result = (await processResponse.json());
                    const { scan_id, status, product, error } = result;
                    if (status === 'failed') {
                        api.logger.error(`AiFood: Label processing failed: ${error}`);
                        return {
                            content: [{ type: 'text', text: `Ошибка обработки этикетки: ${error}` }],
                            details: { success: false, error },
                        };
                    }
                    // Step 2: Poll for completion (max 30 seconds)
                    let attempts = 0;
                    const maxAttempts = 30;
                    let finalStatus = status;
                    let finalProduct = product;
                    while (finalStatus === 'processing' && attempts < maxAttempts) {
                        await new Promise((resolve) => setTimeout(resolve, 1000));
                        attempts++;
                        const statusResponse = await fetch(`${agentApiUrl}/v1/scan_status/${scan_id}`);
                        if (statusResponse.ok) {
                            const statusData = (await statusResponse.json());
                            finalStatus = statusData.status;
                            finalProduct = statusData.product || finalProduct;
                        }
                    }
                    if (finalStatus === 'processing') {
                        return {
                            content: [
                                {
                                    type: 'text',
                                    text: 'Обработка занимает больше времени, чем ожидалось. Попробуйте позже.',
                                },
                            ],
                            details: { success: false, timeout: true },
                        };
                    }
                    if (finalStatus === 'failed') {
                        return {
                            content: [{ type: 'text', text: `Ошибка обработки этикетки` }],
                            details: { success: false },
                        };
                    }
                    // Step 3: Show confirmation card
                    if (!finalProduct) {
                        return {
                            content: [{ type: 'text', text: 'Не удалось распознать продукт' }],
                            details: { success: false },
                        };
                    }
                    const p = finalProduct;
                    const n = p.nutrition_per_100g;
                    let message = `📊 Распознан продукт:\n\n`;
                    message += `**${p.product_name}**\n`;
                    if (p.brand)
                        message += `Бренд: ${p.brand}\n`;
                    message += `\nКБЖУ на 100г:\n`;
                    message += `🔥 ${Math.round(n.calories_kcal)} ккал\n`;
                    message += `🥩 Белок: ${Math.round(n.protein_g)}г\n`;
                    message += `🍞 Углеводы: ${Math.round(n.carbs_g)}г\n`;
                    message += `🧈 Жиры: ${Math.round(n.fat_g)}г\n`;
                    if (n.fiber_g) {
                        message += `🥬 Клетчатка: ${Math.round(n.fiber_g)}г\n`;
                    }
                    message += `\n📝 Метод: ${p.extraction_method === 'paddleocr' ? 'OCR' : 'Vision AI'}\n`;
                    message += `\n✅ Для подтверждения напишите: "подтвердить 150г"\n`;
                    message += `❌ Для отмены: "отменить"`;
                    api.logger.info(`AiFood: Label recognized - ${p.product_name}`);
                    return {
                        content: [{ type: 'text', text: message }],
                        details: {
                            success: true,
                            scan_id,
                            product: p,
                            awaitingConfirmation: true,
                        },
                    };
                }
                catch (error) {
                    api.logger.error(`AiFood: log_food_from_photo error: ${error}`);
                    return {
                        content: [{ type: 'text', text: `Ошибка: ${error}` }],
                        details: { success: false, error: String(error) },
                    };
                }
            },
        });
        // Register confirm_food_from_photo tool
        api.registerTool({
            name: 'confirm_food_from_photo',
            label: 'Confirm Food from Photo',
            description: 'Confirm and log food from scanned nutrition label. Use when user says "подтвердить" or "confirm" after seeing label scan results.',
            parameters: ConfirmFoodFromPhotoSchema,
            async execute(_toolCallId, params) {
                const { grams, meal } = params;
                const agentApiUrl = config.agentApiUrl || 'http://localhost:8000';
                api.logger.info(`AiFood: Confirming food from photo - ${grams}g`);
                try {
                    // Send confirmation message to agent API
                    const confirmResponse = await fetch(`${agentApiUrl}/v1/confirm_message`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            odentity: 'default',
                            message_text: `подтвердить ${grams}г${meal ? ` ${meal}` : ''}`,
                        }),
                    });
                    if (!confirmResponse.ok) {
                        throw new Error(`Agent API error: ${confirmResponse.statusText}`);
                    }
                    const result = (await confirmResponse.json());
                    const { action, entry_id, message } = result;
                    if (action === 'confirm' && entry_id) {
                        const totals = await db.getDailyTotals('default', new Date());
                        return {
                            content: [
                                {
                                    type: 'text',
                                    text: `${message}\n\nДневной итог: ${Math.round(totals.calories)} ккал`,
                                },
                            ],
                            details: {
                                success: true,
                                entry_id,
                                dailyTotals: {
                                    calories: Math.round(totals.calories),
                                    protein: Math.round(totals.protein),
                                    carbs: Math.round(totals.carbohydrates),
                                    fat: Math.round(totals.fat),
                                },
                            },
                        };
                    }
                    else if (action === 'cancel') {
                        return {
                            content: [{ type: 'text', text: message }],
                            details: { success: true, cancelled: true },
                        };
                    }
                    else {
                        return {
                            content: [{ type: 'text', text: message || 'Нет ожидающего подтверждения сканирования' }],
                            details: { success: false },
                        };
                    }
                }
                catch (error) {
                    api.logger.error(`AiFood: confirm_food_from_photo error: ${error}`);
                    return {
                        content: [{ type: 'text', text: `Ошибка подтверждения: ${error}` }],
                        details: { success: false, error: String(error) },
                    };
                }
            },
        });
        // Register /aifood help command
        api.registerCommand({
            name: 'aifood',
            description: 'Show AiFood nutrition tracker help',
            requireAuth: false,
            handler: () => {
                return {
                    markdown: `# 🥗 AiFood - Трекер питания

## Доступные команды

Просто напиши что ты ел, и я запишу это:
- "Съел 2 яйца на завтрак"
- "Курица 150г и рис на обед"
- "Запиши банан"

**📸 Новое! Сканирование этикеток:**
- Отправь фото этикетки продукта
- Я распознаю КБЖУ автоматически
- Подтверди порцию: "подтвердить 150г"

## Примеры запросов

| Запрос | Что сделает |
|--------|-------------|
| [фото этикетки] | Распознает КБЖУ с этикетки |
| "подтвердить 150г" | Запишет распознанный продукт |
| "Покажи отчёт" | Покажет КБЖУ за сегодня |
| "Отчёт за вчера" | Покажет КБЖУ за вчера |
| "Установи цель 2000 ккал" | Установит дневную норму |
| "Моя цель: 2100 ккал, 180г белка" | Установит несколько целей |

## Инструменты

- \`log_food\` - записать еду вручную
- \`log_food_from_photo\` - распознать этикетку
- \`confirm_food_from_photo\` - подтвердить распознанный продукт
- \`daily_nutrition_report\` - отчёт за день
- \`set_nutrition_goals\` - установить цели

---
*AiFood v1.0.0*`,
                };
            },
        });
        api.logger.info('AiFood: Plugin registered with 5 tools and /aifood command');
    },
};
//# sourceMappingURL=index.js.map