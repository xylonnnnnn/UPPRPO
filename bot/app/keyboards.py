from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text = 'Зайти в аккаунт', callback_data='reg')]
])

functions = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text = 'Загрузка фото', callback_data='photo')],
])


def boards_keyboard(boards) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for board in boards:
        builder.button(text=board.name, callback_data=f"board:{board.id}")
    builder.button(text="Создать новую доску", callback_data="board:create")
    builder.adjust(1)
    return builder.as_markup()
