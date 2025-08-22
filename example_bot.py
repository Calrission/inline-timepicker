import datetime
import logging
import sys
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import CallbackQuery
from inline_timepicker.inline_timepicker import InlineTimepicker, TimepickerCallback, Localization
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# Initialize dispatcher
dp = Dispatcher()
inline_timepicker = InlineTimepicker()


# You can write your localization
class MyLanguageLocalization(Localization):
    @property
    def Reset(self):
        return "Сбросить"

    @property
    def OK(self):
        return "Принять"

    @property
    def Cancel(self):
        return "Отмена"


async def get_user_locale(user: types.User) -> str:
    """Get user locale or fallback to en_US"""
    return user.language_code or "en_US"


@dp.message(Command('time'))
async def show_timepicker(message: types.Message):
    inline_timepicker.init(
        message.from_user.id,
        maximum_time=datetime.time(18, 30),  # You can set the upper time edge
        minimum_time=datetime.time(10, 0),   # You can set the lower time edge
        localization=MyLanguageLocalization()  # and using you localization (optional, default is English)
    )
    await message.answer(
        "Select time:",
        reply_markup=inline_timepicker.get_keyboard(message.from_user.id)
    )


@dp.callback_query(TimepickerCallback.filter())
async def handle_timepicker(query: CallbackQuery, callback_data: TimepickerCallback):
    is_continue, prev_time, current_time = inline_timepicker.handle(query.from_user.id, callback_data)
    if is_continue:
        if prev_time == current_time:
            # The user has reached one edge
            text = "maximum" if current_time == datetime.time(18, 30) else "minimum"
            await query.answer(f"This is {text} time")
        else:
            await query.message.edit_reply_markup(
                reply_markup=inline_timepicker.get_keyboard(query.from_user.id)
            )
    else:
        if current_time is not None:  # Time was selected
            formatted_time = current_time.strftime("%H:%M")
            await query.message.edit_text(
                f"Selected time: {formatted_time}",
                reply_markup=None
            )
        else:
            await query.message.edit_text("Time not selected", reply_markup=None)


async def main() -> None:
    # Initialize Bot instance with a default parse mode which will be passed to all API calls
    bot = Bot("7327799319:AAF3avmf9E8TZRdsn6jqqma0-7QxB8ugqeY",
              default=DefaultBotProperties(parse_mode=ParseMode.HTML))  # works from aiogram v.3.7.0

    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
