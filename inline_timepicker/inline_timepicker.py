import datetime
from dataclasses import dataclass
from typing import Optional

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


@dataclass
class InlineTimepickerData:
    min_time: datetime.time
    max_time: datetime.time
    current_time: datetime.time
    minute_step: int
    hour_step: int


class TimepickerCallback(CallbackData, prefix="inline_timepicker"):
    action: str  # 'inc', 'dec', 'success', 'wrong_choice'
    data: str    # 'hour', 'minute', '-'


class InlineTimepicker:
    def __init__(self):
        self.data = {}

    def _get_user_info(self, chat_id: int) -> Optional[InlineTimepickerData]:
        return self.data.get(chat_id, None)

    def _set_user_info(self, chat_id: int, data: Optional[InlineTimepickerData]):
        self.data[chat_id] = data

    def init(self,
             base_time: datetime.time,
             min_time: datetime.time,
             max_time: datetime.time,
             chat_id: int,  # Now required
             minute_step: int = 15,
             hour_step: int = 1):
        
        self._set_user_info(
            chat_id,
            InlineTimepickerData(
                min_time, max_time, base_time, minute_step, hour_step
            )
        )

    def is_inited(self, chat_id: int) -> bool:
        return self._get_user_info(chat_id) is not None

    def reset(self, chat_id: int):
        self._set_user_info(chat_id, None)

    def get_keyboard(self, chat_id: int) -> InlineKeyboardMarkup:
        if not self.is_inited(chat_id):
            raise ValueError('inline_timepicker is not inited properly')

        builder = InlineKeyboardBuilder()
        user_info = self._get_user_info(chat_id)
        
        # Convert times to datetime for comparison
        curr_dt = datetime.datetime.combine(datetime.date.today(), user_info.current_time)
        min_dt = datetime.datetime.combine(datetime.date.today(), user_info.min_time)
        max_dt = datetime.datetime.combine(datetime.date.today(), user_info.max_time)

        # Time deltas for steps
        minute_step = datetime.timedelta(minutes=user_info.minute_step)
        hour_step = datetime.timedelta(hours=user_info.hour_step)

        # Increase buttons
        builder.button(
            text="↑" if curr_dt + hour_step <= max_dt else " ",
            callback_data=TimepickerCallback(
                action="inc" if curr_dt + hour_step <= max_dt else "wrong_choice",
                data="hour"
            )
        )
        builder.button(
            text="↑" if curr_dt + minute_step <= max_dt else " ",
            callback_data=TimepickerCallback(
                action="inc" if curr_dt + minute_step <= max_dt else "wrong_choice",
                data="minute"
            )
        )

        # Time display
        builder.button(
            text=f"{user_info.current_time.hour:02d}",
            callback_data=TimepickerCallback(action="wrong_choice", data="-")
        )
        builder.button(
            text=f"{user_info.current_time.minute:02d}",
            callback_data=TimepickerCallback(action="wrong_choice", data="-")
        )

        # Decrease buttons
        builder.button(
            text="↓" if curr_dt - hour_step >= min_dt else " ",
            callback_data=TimepickerCallback(
                action="dec" if curr_dt - hour_step >= min_dt else "wrong_choice",
                data="hour"
            )
        )
        builder.button(
            text="↓" if curr_dt - minute_step >= min_dt else " ",
            callback_data=TimepickerCallback(
                action="dec" if curr_dt - minute_step >= min_dt else "wrong_choice",
                data="minute"
            )
        )

        # OK button
        builder.button(
            text="OK",
            callback_data=TimepickerCallback(action="success", data="-")
        )

        builder.adjust(2, 2, 2, 1)
        return builder.as_markup()

    def handle(self, chat_id: int, callback_data: TimepickerCallback) -> Optional[datetime.time]:
        if not self.is_inited(chat_id):
            raise ValueError("Timepicker not initialized")

        user_info = self._get_user_info(chat_id)
        curr_dt = datetime.datetime.combine(datetime.date.today(), user_info.current_time)
        min_dt = datetime.datetime.combine(datetime.date.today(), user_info.min_time)
        max_dt = datetime.datetime.combine(datetime.date.today(), user_info.max_time)

        if callback_data.action == 'success':
            self.reset(chat_id)
            return user_info.current_time

        if callback_data.action == 'inc':
            delta = datetime.timedelta(
                hours=user_info.hour_step if callback_data.data == 'hour' else 0,
                minutes=user_info.minute_step if callback_data.data == 'minute' else 0
            )
            new_dt = curr_dt + delta
        elif callback_data.action == 'dec':
            delta = datetime.timedelta(
                hours=user_info.hour_step if callback_data.data == 'hour' else 0,
                minutes=user_info.minute_step if callback_data.data == 'minute' else 0
            )
            new_dt = curr_dt - delta
        else:
            return None

        if min_dt <= new_dt <= max_dt:
            new_time = new_dt.time()
            user_info.current_time = new_time
            self._set_user_info(chat_id, user_info)
            return None

        return None
