import logging
import sys
import datetime
from typing import Dict
import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import CallbackQuery
from inline_timepicker.inline_timepicker import InlineTimepicker, TimepickerCallback
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from config import API_TOKEN


# Initialize dispatcher
dp = Dispatcher()
inline_timepicker = InlineTimepicker()


@dp.message(Command('time'))
async def send_welcome(message: types.Message):
    inline_timepicker.init(
        datetime.time(12),
        datetime.time(1),
        datetime.time(23),
        chat_id=message.from_user.id  # Explicitly provide chat_id
    )

    await message.answer(
        text='Select time:',
        reply_markup=inline_timepicker.get_keyboard(message.from_user.id)
    )

@dp.callback_query(TimepickerCallback.filter())
async def cb_handler(query: CallbackQuery, callback_data: TimepickerCallback):
    await query.answer()
    handle_result = inline_timepicker.handle(query.from_user.id, callback_data)

    if handle_result is not None:
        await query.message.edit_text(
            f"Selected time: {handle_result.strftime('%H:%M')}",
            reply_markup=None
        )
    else:
        await query.message.edit_reply_markup(
            reply_markup=inline_timepicker.get_keyboard(query.from_user.id)
        )


async def main() -> None:
    # Initialize Bot instance with a default parse mode which will be passed to all API calls
    bot = Bot(API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))   # works from aiogram v.3.7.0

    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
