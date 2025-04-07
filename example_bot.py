import logging
import sys
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import CallbackQuery
from inline_timepicker.inline_timepicker import InlineTimepicker, TimepickerCallback
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from config import API_TOKEN


# Initialize dispatcher
dp = Dispatcher()
inline_timepicker = InlineTimepicker()

async def get_user_locale(user: types.User) -> str:
    """Get user locale or fallback to en_US"""
    return user.language_code or "en_US"

@dp.message(Command('time'))
async def show_timepicker(message: types.Message):
    locale = await get_user_locale(message.from_user)
    inline_timepicker.init(message.from_user.id)
    await message.answer(
        "Select time:",
        reply_markup=inline_timepicker.get_keyboard(message.from_user.id, locale)
    )

@dp.callback_query(TimepickerCallback.filter())
async def handle_timepicker(query: CallbackQuery, callback_data: TimepickerCallback):
    locale = await get_user_locale(query.from_user)
    handle_result = inline_timepicker.handle(query.from_user.id, callback_data)
    
    if handle_result is not None:  # Time was selected
        formatted_time = inline_timepicker.format_time_output(handle_result, locale)
        await query.message.edit_text(
            f"Selected time: {formatted_time}",
            reply_markup=None
        )
    else:  # Time was adjusted
        await query.message.edit_reply_markup(
            reply_markup=inline_timepicker.get_keyboard(query.from_user.id, locale)
        )


async def main() -> None:
    # Initialize Bot instance with a default parse mode which will be passed to all API calls
    bot = Bot(API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))   # works from aiogram v.3.7.0

    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
