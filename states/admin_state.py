from aiogram.fsm.state import State, StatesGroup


class AdminStates(StatesGroup):

    # ==============================================
    # ОДНО ОКНО
    # ==============================================

    waiting_date = State()
    waiting_time = State()

    # ==============================================
    # МАССОВОЕ ДОБАВЛЕНИЕ
    # ==============================================

    selecting_times = State()

    # Пользовательский интервал
    custom_interval_start = State()
    custom_interval_end = State()
    custom_interval_step = State()

    # ==============================================
    # РАСПИСАНИЕ НА НЕДЕЛЮ
    # ==============================================

    week_start_date = State()

    # ==============================================
    # УДАЛЕНИЕ
    # ==============================================

    deleting_slot = State()
    deleting_day = State()