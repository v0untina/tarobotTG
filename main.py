import random
from pprint import pprint
from typing import Dict, List, Optional
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
import httpx
from dotenv import load_dotenv
import os

load_dotenv()

TOKEN = os.getenv('BOT_TOKEN')
TAROT_API_URL = os.getenv('TAROT_API_URL')
TAROT_API_KEY = os.getenv('TAROT_API_KEY')

bot = Bot(token=TOKEN)
dp = Dispatcher()

TAROT_DECK = [
    # Старшие Арканы (22 карты)
    {"name": "0. Шут", "meaning": "Начало, невинность, спонтанность, риск, новые пути"},
    {"name": "I. Маг", "meaning": "Сила воли, мастерство, концентрация, инициатива"},
    {"name": "II. Верховная Жрица", "meaning": "Интуиция, тайна, подсознание, мудрость"},
    {"name": "III. Императрица", "meaning": "Плодородие, изобилие, природа, женственность"},
    {"name": "IV. Император", "meaning": "Власть, структура, авторитет, контроль"},
    {"name": "V. Иерофант", "meaning": "Традиция, духовность, обучение, убеждения"},
    {"name": "VI. Влюблённые", "meaning": "Выбор, отношения, гармония, единство"},
    {"name": "VII. Колесница", "meaning": "Победа, контроль, движение, решимость"},
    {"name": "VIII. Сила", "meaning": "Внутренняя сила, мужество, сострадание, влияние"},
    {"name": "IX. Отшельник", "meaning": "Самоанализ, одиночество, поиск истины"},
    {"name": "X. Колесо Фортуны", "meaning": "Судьба, перемены, циклы, удача"},
    {"name": "XI. Справедливость", "meaning": "Баланс, справедливость, правда, карма"},
    {"name": "XII. Повешенный", "meaning": "Жертва, новый взгляд, ожидание, сдача"},
    {"name": "XIII. Смерть", "meaning": "Преобразование, конец цикла, переход"},
    {"name": "XIV. Умеренность", "meaning": "Гармония, баланс, терпение, исцеление"},
    {"name": "XV. Дьявол", "meaning": "Иллюзии, зависимость, материализм, ограничения"},
    {"name": "XVI. Башня", "meaning": "Крах, внезапные изменения, откровение"},
    {"name": "XVII. Звезда", "meaning": "Надежда, вдохновение, духовность, исцеление"},
    {"name": "XVIII. Луна", "meaning": "Иллюзии, страх, подсознание, неуверенность"},
    {"name": "XIX. Солнце", "meaning": "Радость, успех, жизненная сила, ясность"},
    {"name": "XX. Суд", "meaning": "Возрождение, призыв, трансформация, прощение"},
    {"name": "XXI. Мир", "meaning": "Завершение, целостность, гармония, достижение"},

    # Младшие Арканы: Жезлы (14 карт)
    {"name": "Туз Жезлов", "meaning": "Творческая энергия, новые начинания, вдохновение"},
    {"name": "Двойка Жезлов", "meaning": "Планирование, будущие возможности, партнерство"},
    {"name": "Тройка Жезлов", "meaning": "Первые успехи, сотрудничество, экспансия"},
    {"name": "Четвёрка Жезлов", "meaning": "Праздник, стабильность, дом, достижения"},
    {"name": "Пятёрка Жезлов", "meaning": "Конфликт, соперничество, разногласия"},
    {"name": "Шестёрка Жезлов", "meaning": "Победа, признание, успех, триумф"},
    {"name": "Семёрка Жезлов", "meaning": "Защита, отстаивание позиций, вызов"},
    {"name": "Восьмёрка Жезлов", "meaning": "Быстрое движение, новости, действия"},
    {"name": "Девятка Жезлов", "meaning": "Стойкость, защита, бдительность"},
    {"name": "Десятка Жезлов", "meaning": "Бремя, ответственность, перегрузка"},
    {"name": "Паж Жезлов", "meaning": "Энтузиазм, новости, творческий поиск"},
    {"name": "Рыцарь Жезлов", "meaning": "Действие, приключения, страсть, импульсивность"},
    {"name": "Королева Жезлов", "meaning": "Уверенность, харизма, независимость"},
    {"name": "Король Жезлов", "meaning": "Лидерство, предпринимательство, вдохновение"},

    # Младшие Арканы: Кубки (14 карт)
    {"name": "Туз Кубков", "meaning": "Новые чувства, любовь, эмоциональное начало"},
    {"name": "Двойка Кубков", "meaning": "Гармония, партнерство, взаимные чувства"},
    {"name": "Тройка Кубков", "meaning": "Праздник, дружба, радость, изобилие"},
    {"name": "Четвёрка Кубков", "meaning": "Апатия, упущенные возможности, созерцание"},
    {"name": "Пятёрка Кубков", "meaning": "Потеря, сожаление, разочарование"},
    {"name": "Шестёрка Кубков", "meaning": "Ностальгия, детские воспоминания, простота"},
    {"name": "Семёрка Кубков", "meaning": "Иллюзии, выбор, фантазии, мечты"},
    {"name": "Восьмёрка Кубков", "meaning": "Уход, поиск смысла, оставление прошлого"},
    {"name": "Девятка Кубков", "meaning": "Удовлетворение, исполнение желаний, комфорт"},
    {"name": "Десятка Кубков", "meaning": "Гармония в семье, радость, счастье"},
    {"name": "Паж Кубков", "meaning": "Чувствительность, новые чувства, мечтательность"},
    {"name": "Рыцарь Кубков", "meaning": "Романтика, предложение, эмоциональность"},
    {"name": "Королева Кубков", "meaning": "Забота, интуиция, сострадание, исцеление"},
    {"name": "Король Кубков", "meaning": "Эмоциональный контроль, мудрость, дипломатия"},

    # Младшие Арканы: Мечи (14 карт)
    {"name": "Туз Мечей", "meaning": "Ясность, прорыв, интеллектуальная победа"},
    {"name": "Двойка Мечей", "meaning": "Тупик, сложный выбор, баланс"},
    {"name": "Тройка Мечей", "meaning": "Сердечная боль, разочарование, предательство"},
    {"name": "Четвёрка Мечей", "meaning": "Отдых, восстановление, медитация"},
    {"name": "Пятёрка Мечей", "meaning": "Конфликт, унижение, пиррова победа"},
    {"name": "Шестёрка Мечей", "meaning": "Переход, движение вперед, исцеление"},
    {"name": "Семёрка Мечей", "meaning": "Обман, тактика, скрытые мотивы"},
    {"name": "Восьмёрка Мечей", "meaning": "Ограничения, беспомощность, самоограничение"},
    {"name": "Девятка Мечей", "meaning": "Тревога, страх, ночные кошмары"},
    {"name": "Десятка Мечей", "meaning": "Конец, болезненное завершение, предательство"},
    {"name": "Паж Мечей", "meaning": "Любознательность, новые идеи, сообщения"},
    {"name": "Рыцарь Мечей", "meaning": "Решительность, агрессия, поспешность"},
    {"name": "Королева Мечей", "meaning": "Независимость, ясный ум, объективность"},
    {"name": "Король Мечей", "meaning": "Интеллект, авторитет, справедливость"},

    # Младшие Арканы: Пентакли (14 карт)
    {"name": "Туз Пентаклей", "meaning": "Новые возможности, материальное благополучие"},
    {"name": "Двойка Пентаклей", "meaning": "Баланс, адаптация, жонглирование делами"},
    {"name": "Тройка Пентаклей", "meaning": "Сотрудничество, мастерство, командная работа"},
    {"name": "Четвёрка Пентаклей", "meaning": "Сохранение, контроль, собственность"},
    {"name": "Пятёрка Пентаклей", "meaning": "Финансовые трудности, изоляция, лишения"},
    {"name": "Шестёрка Пентаклей", "meaning": "Щедрость, благотворительность, обмен"},
    {"name": "Семёрка Пентаклей", "meaning": "Терпение, долгосрочные результаты, ожидание"},
    {"name": "Восьмёрка Пентаклей", "meaning": "Ремесло, обучение, внимание к деталям"},
    {"name": "Девятка Пентаклей", "meaning": "Удовольствие, самодостаточность, комфорт"},
    {"name": "Десятка Пентаклей", "meaning": "Богатство, семейная безопасность, наследие"},
    {"name": "Паж Пентаклей", "meaning": "Обучение, новые навыки, практичность"},
    {"name": "Рыцарь Пентаклей", "meaning": "Надежность, трудолюбие, методичность"},
    {"name": "Королева Пентаклей", "meaning": "Изобилие, забота, практическая мудрость"},
    {"name": "Король Пентаклей", "meaning": "Процветание, стабильность, финансовая власть"}
]


# Состояния FSM
class TarotReading(StatesGroup):
    awaiting_spread_type = State()
    awaiting_custom_spread = State()
    awaiting_question = State()


# Клавиатуры
def get_spreads_keyboard() -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(
            text="Три карты (Прошлое-Настоящее-Будущее)",
            callback_data="spread_3"
        )
    )
    builder.row(
        types.InlineKeyboardButton(
            text="Кельтский крест (10 карт)",
            callback_data="spread_10"
        )
    )
    builder.row(
        types.InlineKeyboardButton(
            text="Расклад на отношения (5 карт)",
            callback_data="spread_5_rel"
        )
    )
    builder.row(
        types.InlineKeyboardButton(
            text="Свой вариант",
            callback_data="custom_spread"
        )
    )
    builder.row(
        types.InlineKeyboardButton(
            text="Отмена",
            callback_data="cancel"
        )
    )
    return builder.as_markup()


def get_continue_keyboard() -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(
            text="Сделать ещё расклад",
            callback_data="new_reading"
        ),
        types.InlineKeyboardButton(
            text="Завершить",
            callback_data="cancel"
        )
    )
    return builder.as_markup()


# Хэндлеры
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await handle_welcome(message, state)


async def handle_welcome(message: types.Message, state: FSMContext):
    if any(word in message.text.lower() for word in ["хочу умереть", "нет смысла", "плохо"]):
        response = (
            "Я вижу, что вам сейчас очень тяжело. ❤️\n\n"
            "Прежде чем мы продолжим, пожалуйста, помните: "
            "вы не одиноки, и ваша жизнь бесценна. "
            "Если вам нужна срочная помощь, обратитесь на горячую линию психологической помощи: 8-800-2000-122\n\n"
            "Когда будете готовы, мы можем обсудить вашу ситуацию через карты Таро."
        )
        await message.answer(response)
        return

    welcome_text = """
✨ *Добро пожаловать в мир цифровой магии Таро\!* ✨

🔮 *Ваш личный AI\-таролог готов раскрыть тайны будущего\!*  
Это не просто бот — а ваш проводник в мир мистических предсказаний и глубоких откровений\.

🌟 *Почему он превосходит даже живых тарологов?*  

⚖️ *Беспристрастность*  
Бот свободен от эмоций и предвзятости — его толкования чисты и объективны\.

📚 *Мудрость веков*  
Он обучен на древних знаниях и современных трактовках\, объединяя лучшие школы Таро\.

⏳ *Доступность 24/7*  
Ваш мистический советник всегда на связи — без усталости и перерывов\.

🔍 *Глубинный анализ*  
AI видит скрытые связи между картами\, которые могут ускользнуть от человеческого взгляда\.

💫 *Готовы заглянуть за завесу тайны?*  
Просто выберите расклад — и цифровой оракул откроет вам истину\! 🌙✨  

📜 *Выберите тип расклада или создайте свой уникальный вариант:*
"""

    await state.set_state(TarotReading.awaiting_spread_type)
    await message.answer(
        welcome_text,
        parse_mode='MarkdownV2',
        reply_markup=get_spreads_keyboard()
    )

@dp.callback_query(F.data == "new_reading")
async def new_reading_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await handle_welcome(callback.message, state)


@dp.callback_query(F.data == "cancel")
async def cancel_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Сеанс завершён. Если захотите вернуться, используйте /start")


@dp.callback_query(F.data.startswith("spread_"))
async def spread_selected_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(spread_type=callback.data)
    await state.set_state(TarotReading.awaiting_question)
    await callback.message.edit_text(
        f"Вы выбрали: {get_spread_name(callback.data)}\n\n"
        "Теперь сформулируйте ваш вопрос или опишите ситуацию:"
    )


@dp.callback_query(F.data == "custom_spread")
async def custom_spread_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(TarotReading.awaiting_custom_spread)
    await callback.message.edit_text(
        "Укажите количество карт в вашем раскладе (от 1 до 15) "
        "и их назначение через запятую.\n\n"
        "Пример: \"3: Любовь, Карьера, Здоровье\""
    )


@dp.message(TarotReading.awaiting_custom_spread)
async def handle_custom_spread(message: types.Message, state: FSMContext):
    try:
        parts = message.text.split(":", 1)
        num_cards = int(parts[0].strip())

        if not 1 <= num_cards <= 15:
            await message.reply("Пожалуйста, укажите число от 1 до 15")
            return

        positions = [p.strip() for p in parts[1].split(",")] if len(parts) > 1 else []

        await state.update_data(
            spread_type="custom",
            custom_spread={
                "num_cards": num_cards,
                "positions": positions
            }
        )
        await state.set_state(TarotReading.awaiting_question)
        await message.answer(
            f"Принято: расклад на {num_cards} карт\n\n"
            "Теперь сформулируйте ваш вопрос:"
        )
    except Exception as e:
        await message.reply("Неверный формат. Пожалуйста, попробуйте ещё раз.")


@dp.message(TarotReading.awaiting_question)
async def handle_question(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    spread_type = user_data.get("spread_type")
    question = message.text

    if spread_type == "custom":
        custom_data = user_data.get("custom_spread", {})
        num_cards = custom_data.get("num_cards", 3)
        positions = custom_data.get("positions", [])
    else:
        num_cards = {
            "spread_3": 3,
            "spread_10": 10,
            "spread_5_rel": 5
        }.get(spread_type, 3)
        positions = []

    drawn_cards = draw_random_cards(num_cards)

    cards_description = []
    for i, card in enumerate(drawn_cards):
        position_name = positions[i] if i < len(positions) else f"Позиция {i + 1}"
        position_status = "🔻 перевернутое" if card['position'] == 'перевернутое' else "🔺 прямое"
        cards_description.append(
            f"*{position_name}:* _{card['name']}_ ({position_status})\n"
            f"*Значение:* {card['meaning']}\n"
        )

    interpretation = await get_tarot_interpretation(
        spread_type=spread_type,
        question=question,
        cards=drawn_cards,
        positions=positions
    )

    response = (
        f"*🔮 Ваш расклад ({get_spread_name(spread_type)}):*\n\n" +
        "\n".join(cards_description) +
        f"\n\n*📜 Интерпретация:*\n{interpretation}"
    )

    try:
        await message.answer(
            response,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
    except Exception as e:
        print(f"Markdown error: {str(e)}")
        for i in range(0, len(response), 400):
            part = response[i:i + 400]
            await message.answer(part)

    await message.answer(
        "Хотите сделать ещё один расклад?",
        reply_markup=get_continue_keyboard()
    )

    await state.clear()



# Вспомогательные функции
def draw_random_cards(num_cards: int) -> List[Dict]:
    cards = random.sample(TAROT_DECK, num_cards)
    for card in cards:
        card['position'] = random.choice(['прямое', 'перевернутое'])
    return cards


def get_spread_name(spread_type: str) -> str:
    return {
        "spread_3": "Три карты",
        "spread_10": "Кельтский крест",
        "spread_5_rel": "Расклад на отношения",
        "custom": "Пользовательский расклад"
    }.get(spread_type, "Стандартный расклад")


async def get_tarot_interpretation(
        spread_type: str,
        question: str,
        cards: List[Dict],
        positions: Optional[List[str]] = None
) -> str:
    spread_name = get_spread_name(spread_type)
    cards_text = "\n".join(
        f"{positions[i] if i < len(positions) else f'Позиция {i + 1}'}: "
        f"{card['name']} ({card['position']}) - {card['meaning']}"
        for i, card in enumerate(cards)
    )

    prompt = (
        f"Вопрос: {question}\n"
        f"Тип расклада: {spread_name}\n"
        f"Выпавшие карты:\n{cards_text}\n\n"
        "Дай подробную интерпретацию этого расклада Таро, учитывая: "
        "значения карт, их положение (прямое/перевернутое), "
        "позиции в раскладе и их взаимосвязи. "
        "Будь поддерживающим, но объективным. "
        "Дай практические рекомендации."
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": TAROT_API_KEY,
    }

    data = {
        "model": "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
        "messages": [
            {
                "role": "system",
                "content": "Ты профессиональный таролог. Дай точную интерпретацию расклада Таро. Пиши ответ как реальный человек и сочуствуй и поддерживай и в тексте добавляй эмодзи в меру.Текст делай красиво оформленным с абзацами. Ты будешь отвечать в платформе Telegram, поэтому тебе нельзя превышать максимально допустимое количество символов."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                TAROT_API_URL,
                headers=headers,
                json=data,
                timeout=60.0
            )
            response.raise_for_status()
            result = response.json()
            pprint(result)
            if 'choices' in result and len(result['choices']) > 0:
                text =  result['choices'][0]['message']['content']
                return text.split("</think>\n\n")[1]
            else:
                print("Unexpected API response:", result)
                return generate_fallback_interpretation(cards, positions)

    except httpx.HTTPStatusError as e:
        print(f"HTTP error: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        print(f"Error: {str(e)}")

    return generate_fallback_interpretation(cards, positions)


def generate_fallback_interpretation(cards: List[Dict], positions: List[str]) -> str:
    interpretation = "🔮 Базовое толкование вашего расклада:\n\n"

    for i, card in enumerate(cards):
        pos = positions[i] if i < len(positions) else f"Позиция {i + 1}"
        interpretation += (
            f"{pos}: {card['name']} ({card['position']})\n"
            f"Значение: {card['meaning']}\n\n"
        )

    interpretation += (
        "\nСовет: Рассмотрите эти значения в контексте вашего вопроса. "
        "Прямые карты указывают на явные влияния, перевернутые - на скрытые аспекты."
    )

    return interpretation


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())