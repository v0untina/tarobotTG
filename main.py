#СДЕЛАТЬ ОБРАБОТКУ СООБЩЕНИЙ, ЧТОБЫ ПОЛЬЗОВАТЕЛЬ МОГ НАПИСАТЬ ТОЛЬКО ОДНО СООБЩЕНИЕ
#ОПТИМИЗИРОВАТЬ РАБОТУ ИИ
#ПОДКЛЮЧИТЬ К БД И ОГРАНИЧИТЬ КОЛИЧЕСТВО ЗАПРОСОВ В ДЕНЬ
#СДЕЛАТЬ РЕКЛАМУ И ПРОДУМАТЬ МАРКЕТИНГ
#СДЕЛАТЬ ФИШКИ ПО ТИПУ РАСКЛАД КАЖДОДНЕВНЫЙ
#ДОБАВЛЯТЬ ФОТКИ КАРТОЧЕК
#СДЕЛАТЬ ПОДБОРКУ ЛЮДЕЙ С ПОХОЖИМИ ЗАПРОСАМИ И ПРОБЛЕМАМИ

import random
import asyncio
from pprint import pprint
from typing import Dict, List, Optional
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.database import db_start,get_user_id,get_update_count
import httpx
from dotenv import load_dotenv
from typing import List, Tuple
import os
from tarot_deck import TAROT_DECK, LOADING_MESSAGES, WELCOME_TEXT
from app.keyboards import  get_spreads_keyboard, get_continue_keyboard

load_dotenv()

TOKEN = os.getenv('BOT_TOKEN')
TAROT_API_URL = os.getenv('TAROT_API_URL')
TAROT_API_KEY = os.getenv('TAROT_API_KEY')

bot = Bot(token=TOKEN)
dp = Dispatcher()


# Состояния FSM
class TarotReading(StatesGroup):
    awaiting_spread_type = State()
    awaiting_custom_spread = State()
    awaiting_question = State()

# Клавиатуры
get_spreads_keyboard()
get_continue_keyboard()

async def on_startup():
    await db_start()
    print('Tarot Bot Started')

# Хэндлеры
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await get_user_id(message.from_user.id,message.from_user.username)

    await state.set_state(TarotReading.awaiting_spread_type)
    await message.answer(
        WELCOME_TEXT,
        parse_mode='MarkdownV2',
        reply_markup=get_spreads_keyboard()
    )

@dp.callback_query(F.data == "new_reading")
async def new_reading_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)


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
    is_allowed = await get_update_count(user_id=message.from_user.id)
    if not is_allowed:
        await message.answer("⛔ Вы израсходовали лимит бесплатных раскладов на сегодня. Попробуйте снова завтра.")
        await state.clear()
        return False
    user_data = await state.get_data()
    spread_type = user_data.get("spread_type")
    question = message.text
    loading_message, loading_task = await animate_loading(message, LOADING_MESSAGES)

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
    loading_task.cancel()
    try:
        await loading_task
    except asyncio.CancelledError:
        pass

    try:
        await loading_message.delete()
    except Exception as e:
        print(f"[animate_loading] Не удалось удалить сообщение: {e}")
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
    await get_update_count(user_id=message.from_user.id)
    await state.clear()


async def animate_loading(message: types.Message, phrases: List[str], interval: float = 1.5) -> Tuple[types.Message, asyncio.Task]:
    msg = await message.answer(phrases[0])

    async def updater():
        i = 1
        while True:
            await asyncio.sleep(interval)
            try:
                await msg.edit_text(phrases[i % len(phrases)])
                i += 1
            except Exception as e:
                print(f"[animate_loading] Ошибка обновления: {e}")
                continue

    task = asyncio.create_task(updater())
    return msg, task

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
        "model": "Qwen/Qwen3-235B-A22B-FP8",
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
    dp.startup.register(on_startup)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())