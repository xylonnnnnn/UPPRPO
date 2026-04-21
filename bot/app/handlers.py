import os
from pathlib import Path
from typing import Optional

import httpx
from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

import app.keyboards as kb
from db.crud import create_board, create_pin, get_user_boards, verify_user
from db.database import session_factory

router = Router()

# In-memory auth is enough for a running bot process. For production, persist this mapping.
AUTH_USERS: dict[int, dict[str, int | str]] = {}


def current_auth(message_or_callback: Message | CallbackQuery) -> Optional[dict[str, int | str]]:
    user = message_or_callback.from_user
    if not user:
        return None
    return AUTH_USERS.get(user.id)


@router.message(CommandStart())
async def start(message: Message):
    await message.answer("Привет!", reply_markup=kb.menu)


class Acc(StatesGroup):
    email = State()
    password = State()


@router.callback_query(F.data == "reg")
async def reg(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Acc.email)
    await callback.message.edit_text("Напишите свою почту")


@router.message(Acc.email, F.text)
async def email(message: Message, state: FSMContext):
    await state.update_data(email=message.text.strip())
    await state.set_state(Acc.password)
    await message.answer("Напишите свой пароль")


@router.message(Acc.password, F.text)
async def password(message: Message, state: FSMContext):
    data = await state.get_data()
    email_value = (data.get("email") or "").strip()
    password_value = message.text.strip()

    async with session_factory()() as session:
        user = await verify_user(session, email=email_value, password=password_value)

    if user:
        AUTH_USERS[message.from_user.id] = {"user_id": user.id, "username": user.username}
        await message.answer("Успешно! Выберите действие:", reply_markup=kb.functions)
    else:
        await message.answer(
            "Аккаунт не найден или пароль неверный. Создайте аккаунт на сайте.",
            reply_markup=kb.menu,
        )

    await state.clear()


class PinUpload(StatesGroup):
    board_name = State()
    photo = State()
    title = State()
    description = State()


@router.callback_query(F.data == "photo")
async def photo(callback: CallbackQuery, state: FSMContext):
    auth = current_auth(callback)
    if not auth:
        await callback.message.answer("Сначала войдите в аккаунт.", reply_markup=kb.menu)
        await callback.answer()
        return

    async with session_factory()() as session:
        boards = await get_user_boards(session, int(auth["user_id"]))

    await state.clear()
    if boards:
        await callback.message.edit_text(
            "Выберите доску, в которую нужно загрузить фото, или создайте новую:",
            reply_markup=kb.boards_keyboard(boards),
        )
    else:
        await state.set_state(PinUpload.board_name)
        await callback.message.edit_text("У вас пока нет досок. Напишите название новой доски.")
    await callback.answer()


@router.callback_query(F.data.startswith("board:"))
async def choose_board(callback: CallbackQuery, state: FSMContext):
    auth = current_auth(callback)
    if not auth:
        await callback.message.answer("Сначала войдите в аккаунт.", reply_markup=kb.menu)
        await callback.answer()
        return

    board_value = callback.data.split(":", 1)[1]
    if board_value == "create":
        await state.set_state(PinUpload.board_name)
        await callback.message.edit_text("Напишите название новой доски.")
        await callback.answer()
        return

    await state.update_data(board_id=int(board_value))
    await state.set_state(PinUpload.photo)
    await callback.message.edit_text("Отправьте фото, которое нужно добавить на сайт.")
    await callback.answer()


@router.message(PinUpload.board_name, F.text)
async def new_board_name(message: Message, state: FSMContext):
    auth = current_auth(message)
    if not auth:
        await message.answer("Сначала войдите в аккаунт.", reply_markup=kb.menu)
        await state.clear()
        return

    board_name = message.text.strip()
    if not board_name:
        await message.answer("Название доски не должно быть пустым.")
        return
    if len(board_name) > 100:
        await message.answer("Название доски должно быть не длиннее 100 символов.")
        return

    try:
        async with session_factory()() as session:
            board = await create_board(session, user_id=int(auth["user_id"]), name=board_name)
    except ValueError:
        await message.answer("Доска с таким названием уже есть. Выберите ее из списка или введите другое название.")
        return

    await state.update_data(board_id=board.id)
    await state.set_state(PinUpload.photo)
    await message.answer(f"Доска «{board.name}» создана. Теперь отправьте фото.")


async def upload_image_to_cloudflare(file_path: str) -> Optional[str]:
    account_id = os.getenv("CF_ACCOUNT_ID")
    api_key = os.getenv("CF_IMAGES_API_KEY")
    if not account_id or not api_key:
        return None

    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/images/v1"
    headers = {"Authorization": f"Bearer {api_key}"}

    path = Path(file_path)
    async with httpx.AsyncClient(timeout=60) as client:
        with path.open("rb") as file:
            response = await client.post(
                url,
                headers=headers,
                files={"file": (path.name, file, "image/jpeg")},
            )

    response.raise_for_status()
    result = response.json()
    if not result.get("success"):
        raise RuntimeError(str(result.get("errors") or "Cloudflare upload failed"))

    image_id = result["result"]["id"]
    return f"https://imagedelivery.net/{account_id}/{image_id}/public"


@router.message(PinUpload.photo, F.photo)
async def get_photo(message: Message, state: FSMContext):
    photo_file = message.photo[-1]

    data_dir = Path("data")
    data_dir.mkdir(parents=True, exist_ok=True)
    dst = data_dir / f"{photo_file.file_id}.jpg"
    await message.bot.download(photo_file, destination=dst)

    try:
        image_url = await upload_image_to_cloudflare(str(dst))
    except Exception as exc:
        await message.answer(f"Не получилось загрузить картинку в Cloudflare: {exc}")
        return

    if not image_url:
        image_url = str(dst)
        await message.answer(
            "Cloudflare не настроен, поэтому временно сохраню локальный путь. "
            "Для отображения на сайте нужен публичный image_url."
        )

    await state.update_data(image_url=image_url)
    await state.set_state(PinUpload.title)
    await message.answer("Фото загружено. Теперь напишите название карточки.")


@router.message(PinUpload.photo)
async def invalid_photo(message: Message):
    await message.answer("Нужно отправить именно фото.")


@router.message(PinUpload.title, F.text)
async def pin_title(message: Message, state: FSMContext):
    title = message.text.strip()
    if not title:
        await message.answer("Название не должно быть пустым.")
        return
    if len(title) > 200:
        await message.answer("Название должно быть не длиннее 200 символов.")
        return

    await state.update_data(title=title)
    await state.set_state(PinUpload.description)
    await message.answer("Добавьте описание карточки.")


@router.message(PinUpload.description, F.text)
async def save_pin(message: Message, state: FSMContext):
    auth = current_auth(message)
    if not auth:
        await message.answer("Сначала войдите в аккаунт.", reply_markup=kb.menu)
        await state.clear()
        return

    data = await state.get_data()
    board_id = data.get("board_id")
    title = data.get("title")
    image_url = data.get("image_url")
    description = message.text.strip() or None

    if not board_id or not title or not image_url:
        await message.answer("Не хватает данных для создания карточки. Начните загрузку заново.")
        await state.clear()
        return

    async with session_factory()() as session:
        pin = await create_pin(
            session,
            user_id=int(auth["user_id"]),
            board_id=int(board_id),
            title=title,
            description=description,
            image_url=image_url,
        )

    await message.answer(
        f"Карточка «{pin.title}» добавлена в выбранную доску.",
        reply_markup=kb.functions,
    )
    await state.clear()
