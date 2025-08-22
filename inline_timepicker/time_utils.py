import datetime


def incH(
    time: datetime.time,
    step_h: int,
    max_time: datetime.time,
    min_time: datetime.time
) -> datetime.time:
    return incDelta(time, datetime.timedelta(hours=step_h), max_time, min_time)


def incM(
    time: datetime.time,
    step_m: int,
    max_time: datetime.time,
    min_time: datetime.time
) -> datetime.time:
    return incDelta(time, datetime.timedelta(minutes=step_m), max_time, min_time)


def incDelta(
    time: datetime.time,
    timedelta: datetime.timedelta,
    max_time: datetime.time,
    min_time: datetime.time
) -> datetime.time:
    new_time = (datetime.datetime.combine(datetime.date.today(), time) + timedelta).time()
    if new_time > max_time:
        new_time = max_time
    elif new_time < min_time:
        new_time = min_time
    return new_time
