from aiogram.fsm.state import State, StatesGroup


class FileState(StatesGroup):
    """Состояния пользователя
    """
    send_file = State()  # Ожидание файла
