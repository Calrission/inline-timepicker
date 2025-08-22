import abc
import datetime
from dataclasses import dataclass
from typing import Optional
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from inline_timepicker.time_utils import incH, incM


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

    @property
    @abc.abstractmethod
    def Reset(self):
        pass


class EnglishLocalization(Localization):
    @property
    def Reset(self):
        return "Reset"

    @property
    def OK(self):
        return "OK"

    @property
    def Cancel(self):
        return "Cancel"


@dataclass
class InlineTimepickerData:
    current_time: datetime.time
    base_time: datetime.time
    prev_time: datetime.time | None
    min_time: datetime.time
    max_time: datetime.time
    minute_step: int
    hour_step: int
    localization: Localization


class TimepickerCallback(CallbackData, prefix="inline_timepicker"):
    action: str  # 'inc', 'dec', 'toggle', 'success', 'cancel', 'reset' 'wrong_choice'
    data: str  # 'hour', 'minute', 'period', '-'


class InlineTimepicker:
    def __init__(self):
        self.data = {}

    def _get_user_info(self, chat_id: int) -> Optional[InlineTimepickerData]:
        return self.data.get(chat_id, None)

    def _set_user_info(self, chat_id: int, data: Optional[InlineTimepickerData]):
        self.data[chat_id] = data

    def init(
            self,
            chat_id: int,
            base_time: datetime.time = datetime.time(12, 0),
            minimum_time: datetime.time = datetime.time(0, 0),
            maximum_time: datetime.time = datetime.time(23, 59),
            minute_step: int = 15,
            hour_step: int = 1,
            localization: Optional[Localization] = None,
    ):
        if localization is None:
            localization = EnglishLocalization()
        self._set_user_info(
            chat_id,
            InlineTimepickerData(
                base_time=base_time,
                current_time=base_time,
                minute_step=minute_step,
                hour_step=hour_step,
                localization=localization,
                min_time=minimum_time,
                max_time=maximum_time,
                prev_time=None,
            )
        )

    def is_inited(self, chat_id: int) -> bool:
        return self._get_user_info(chat_id) is not None

    def reset(self, chat_id: int):
        self._set_user_info(chat_id, None)

    def get_keyboard(self, chat_id: int) -> InlineKeyboardMarkup:
        if not self.is_inited(chat_id):
            raise ValueError('Timepicker not initialized')

        builder = InlineKeyboardBuilder()
        user_info = self._get_user_info(chat_id)
        current_time = user_info.current_time

        # Increment buttons row
        builder.button(text="↑", callback_data=TimepickerCallback(action="inc", data="hour"))
        builder.button(text="↑", callback_data=TimepickerCallback(action="inc", data="minute"))

        builder.button(text=f"{current_time.hour:02d}",
                       callback_data=TimepickerCallback(action="wrong_choice", data="-"))
        builder.button(text=f"{current_time.minute:02d}",
                       callback_data=TimepickerCallback(action="wrong_choice", data="-"))

        # Decrement buttons row
        builder.button(text="↓", callback_data=TimepickerCallback(action="dec", data="hour"))
        builder.button(text="↓", callback_data=TimepickerCallback(action="dec", data="minute"))

        # Cancel button row
        builder.button(text=user_info.localization.Cancel, callback_data=TimepickerCallback(action="cancel", data="-"))

        # OK button row
        builder.button(text=user_info.localization.OK, callback_data=TimepickerCallback(action="success", data="-"))

        # Reset button row
        builder.button(text=user_info.localization.Reset, callback_data=TimepickerCallback(action="reset", data="-"))

        # Adjust layout
        builder.adjust(2, 2, 2, 2, 1)  # 2 columns

        return builder.as_markup()

    def handle(self, chat_id: int, callback_data: TimepickerCallback) -> tuple[bool, Optional[datetime.time], Optional[datetime.time]]:
        if not self.is_inited(chat_id):
            raise ValueError("Timepicker not initialized")

        user_info = self._get_user_info(chat_id)
        prev_time = user_info.prev_time
        current_time = user_info.current_time

        if callback_data.action == 'success':
            self.reset(chat_id)
            return False, prev_time, current_time
        elif callback_data.action == 'cancel':
            self.reset(chat_id)
            return False, None, None
        elif callback_data.action == 'reset':
            user_info.prev_time = current_time
            user_info.current_time = user_info.base_time
            self._set_user_info(chat_id, user_info)
            return True, user_info.prev_time, user_info.current_time
        else:
            k = -1 if callback_data.action == 'dec' else 1
            if callback_data.data == 'hour':
                new_time = incH(current_time, k*user_info.hour_step, user_info.max_time, user_info.min_time)
            else:
                # elif callback_data.data == 'minute':
                new_time = incM(current_time, k*user_info.minute_step, user_info.max_time, user_info.min_time)

            user_info.prev_time = current_time
            user_info.current_time = new_time
            self._set_user_info(chat_id, user_info)
            return True, user_info.prev_time, user_info.current_time
