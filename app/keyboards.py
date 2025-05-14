from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder


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
