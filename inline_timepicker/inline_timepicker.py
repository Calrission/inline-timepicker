import datetime
from dataclasses import dataclass
from typing import Optional

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


@dataclass
class InlineTimepickerData:
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

    def init(
        self,
        chat_id: int,  # Now required as first positional argument
        base_time: datetime.time = datetime.time(12, 0),
        minute_step: int = 15,
        hour_step: int = 1
    ):
        self._set_user_info(
            chat_id,
            InlineTimepickerData(
                current_time=base_time,
                minute_step=minute_step,
                hour_step=hour_step
            )
        )

    def is_inited(self, chat_id: int) -> bool:
        return self._get_user_info(chat_id) is not None

    def reset(self, chat_id: int):
        self._set_user_info(chat_id, None)

    def _adjust_time(self, time: datetime.time, hours: int = 0, minutes: int = 0) -> datetime.time:
        """Adjust time with proper circular behavior for 24-hour format"""
        total_minutes = time.hour * 60 + time.minute
        total_minutes += hours * 60 + minutes
        
        # Handle 24-hour circular behavior
        total_minutes %= 24 * 60
        
        # Convert back to hours and minutes
        new_hour = total_minutes // 60
        new_minute = total_minutes % 60
        
        # Special case: 24:00 should be displayed as 24:00
        if new_hour == 0 and (hours or minutes):
            new_hour = 24
            new_minute = 0
            
        return datetime.time(new_hour if new_hour != 0 else 24, new_minute)

    def get_keyboard(self, chat_id: int) -> InlineKeyboardMarkup:
        if not self.is_inited(chat_id):
            raise ValueError('Timepicker not initialized')

        builder = InlineKeyboardBuilder()
        user_info = self._get_user_info(chat_id)
        current_time = user_info.current_time
        
         # Simply use the actual hour (0-23) for display
        display_hour = current_time.hour
        display_minute = current_time.minute

        # Always show arrows (circular navigation)
        # Hour increase button
        builder.button(
            text="↑", 
            callback_data=TimepickerCallback(action="inc", data="hour")
        )
        
        # Minute increase button
        builder.button(
            text="↑", 
            callback_data=TimepickerCallback(action="inc", data="minute")
        )

        builder.button(
        text=f"{display_hour:02d}",  # This will show 00 for midnight
        callback_data=TimepickerCallback(action="wrong_choice", data="-")
        )
        
        builder.button(
            text=f"{display_minute:02d}",
            callback_data=TimepickerCallback(action="wrong_choice", data="-")
        )

        # Hour decrease button
        builder.button(
            text="↓", 
            callback_data=TimepickerCallback(action="dec", data="hour")
        )
        
        # Minute decrease button
        builder.button(
            text="↓", 
            callback_data=TimepickerCallback(action="dec", data="minute")
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
        current_time = user_info.current_time

        if callback_data.action == 'success':
            self.reset(chat_id)
            return current_time  # Always return proper time object (0-23 hours)

        new_hour = current_time.hour
        new_minute = current_time.minute

        if callback_data.action == 'inc' and callback_data.data == 'minute':
            new_minute += user_info.minute_step
            if new_minute >= 60:
                new_minute -= 60
                new_hour += 1
            if new_hour >= 24:
                new_hour = 0

        elif callback_data.action == 'dec' and callback_data.data == 'minute':
            new_minute -= user_info.minute_step
            if new_minute < 0:
                new_minute += 60
                new_hour -= 1
            if new_hour < 0:
                new_hour = 23

        elif callback_data.action == 'inc' and callback_data.data == 'hour':
            new_hour += user_info.hour_step
            if new_hour >= 24:
                new_hour = 0

        elif callback_data.action == 'dec' and callback_data.data == 'hour':
            new_hour -= user_info.hour_step
            if new_hour < 0:
                new_hour = 23

        # Store time properly (0-23 hours)
        new_time = datetime.time(new_hour, new_minute)
        user_info.current_time = new_time
        self._set_user_info(chat_id, user_info)
        return None
