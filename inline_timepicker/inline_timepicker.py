import abc
import datetime
from dataclasses import dataclass
from typing import Optional
from babel import Locale
from babel.dates import get_time_format
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


@dataclass
class Localization(abc.ABC):
    @property
    @abc.abstractmethod
    def OK(self):
        pass

    @property
    @abc.abstractmethod
    def Cancel(self):
        pass


class EnglishLocalization(Localization):
    @property
    def OK(self):
        return "OK"

    @property
    def Cancel(self):
        return "Cancel"


@dataclass
class InlineTimepickerData:
    current_time: datetime.time
    minute_step: int
    hour_step: int
    localization: Localization


class TimepickerCallback(CallbackData, prefix="inline_timepicker"):
    action: str  # 'inc', 'dec', 'toggle', 'success', 'cancel', 'wrong_choice'
    data: str  # 'hour', 'minute', 'period', '-'


class InlineTimepicker:
    def __init__(self):
        self.data = {}

    def _get_user_info(self, chat_id: int) -> Optional[InlineTimepickerData]:
        return self.data.get(chat_id, None)

    def _set_user_info(self, chat_id: int, data: Optional[InlineTimepickerData]):
        self.data[chat_id] = data

    def init(self, chat_id: int, base_time: datetime.time = datetime.time(12, 0),
             minute_step: int = 15, hour_step: int = 1, localization: Optional[Localization] = None):
        if localization is None:
            localization = EnglishLocalization()
        self._set_user_info(
            chat_id,
            InlineTimepickerData(
                current_time=base_time,
                minute_step=minute_step,
                hour_step=hour_step,
                localization=localization
            )
        )

    def is_inited(self, chat_id: int) -> bool:
        return self._get_user_info(chat_id) is not None

    def reset(self, chat_id: int):
        self._set_user_info(chat_id, None)

    def uses_12h_format(self, locale: str) -> bool:
        """Check if locale typically uses 12-hour format"""
        try:
            loc = Locale.parse(locale)
            return 'h' in str(get_time_format(locale=loc))
        except:
            return False

    def format_time_output(self, time: datetime.time, locale: str) -> str:
        """Format time for display with AM/PM when needed"""
        if self.uses_12h_format(locale):
            hour = time.hour % 12 or 12
            period = "AM" if time.hour < 12 else "PM"
            return f"{hour:02d}:{time.minute:02d} {period}"
        return f"{time.hour:02d}:{time.minute:02d}"

    def get_keyboard(self, chat_id: int, locale: str = "en_US") -> InlineKeyboardMarkup:
        if not self.is_inited(chat_id):
            raise ValueError('Timepicker not initialized')

        builder = InlineKeyboardBuilder()
        user_info = self._get_user_info(chat_id)
        current_time = user_info.current_time
        use_12h = self.uses_12h_format(locale)

        # Increment buttons row
        builder.button(text="↑", callback_data=TimepickerCallback(action="inc", data="hour"))
        builder.button(text="↑", callback_data=TimepickerCallback(action="inc", data="minute"))
        if use_12h:
            builder.button(text="↑", callback_data=TimepickerCallback(action="inc", data="period"))

        # Display values row
        if use_12h:
            display_hour = current_time.hour % 12 or 12
            period = "AM" if current_time.hour < 12 else "PM"
            builder.button(text=f"{display_hour:02d}",
                           callback_data=TimepickerCallback(action="wrong_choice", data="-"))
            builder.button(text=f"{current_time.minute:02d}",
                           callback_data=TimepickerCallback(action="wrong_choice", data="-"))
            builder.button(text=period, callback_data=TimepickerCallback(action="toggle", data="period"))
        else:
            builder.button(text=f"{current_time.hour:02d}",
                           callback_data=TimepickerCallback(action="wrong_choice", data="-"))
            builder.button(text=f"{current_time.minute:02d}",
                           callback_data=TimepickerCallback(action="wrong_choice", data="-"))

        # Decrement buttons row
        builder.button(text="↓", callback_data=TimepickerCallback(action="dec", data="hour"))
        builder.button(text="↓", callback_data=TimepickerCallback(action="dec", data="minute"))
        if use_12h:
            builder.button(text="↓", callback_data=TimepickerCallback(action="dec", data="period"))

        # Cancel button row
        builder.button(text=user_info.localization.Cancel, callback_data=TimepickerCallback(action="cancel", data="-"))

        # OK button row
        builder.button(text=user_info.localization.OK, callback_data=TimepickerCallback(action="success", data="-"))

        # Adjust layout
        if use_12h:
            builder.adjust(3, 3, 3, 2)  # 3 columns for 12h format
        else:
            builder.adjust(2, 2, 2, 2)  # 2 columns for 24h format

        return builder.as_markup()

    def handle(self, chat_id: int, callback_data: TimepickerCallback) -> tuple[bool, Optional[datetime.time]]:
        if not self.is_inited(chat_id):
            raise ValueError("Timepicker not initialized")

        user_info = self._get_user_info(chat_id)
        current_time = user_info.current_time
        new_hour = current_time.hour
        new_minute = current_time.minute

        if callback_data.action == 'success':
            self.reset(chat_id)
            return False, current_time

        if callback_data.action == 'cancel':
            self.reset(chat_id)
            return False, None

        if callback_data.action == 'inc':
            if callback_data.data == 'hour':
                new_hour = (new_hour + user_info.hour_step) % 24
            elif callback_data.data == 'minute':
                new_minute += user_info.minute_step
                if new_minute >= 60:
                    new_minute -= 60
                    new_hour = (new_hour + 1) % 24
            elif callback_data.data == 'period':
                new_hour = (new_hour + 12) % 24

        elif callback_data.action == 'dec':
            if callback_data.data == 'hour':
                new_hour = (new_hour - user_info.hour_step) % 24
            elif callback_data.data == 'minute':
                new_minute -= user_info.minute_step
                if new_minute < 0:
                    new_minute += 60
                    new_hour = (new_hour - 1) % 24
            elif callback_data.data == 'period':
                new_hour = (new_hour + 12) % 24

        elif callback_data.action == 'toggle' and callback_data.data == 'period':
            new_hour = (new_hour + 12) % 24

        new_time = datetime.time(new_hour, new_minute)
        user_info.current_time = new_time
        self._set_user_info(chat_id, user_info)
        return True, None
