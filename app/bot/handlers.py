from aiogram import types, F
from fastapi import HTTPException
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, StateFilter
from sqlalchemy.ext.asyncio import AsyncSession

from .states import FileState
from app.core.config import Config
from app.services.data_processing import FileService
from app.db.crud import get_product_prices, clear_tables
from app.services.functions import get_price_and_save


async def show_main_menu(message: types.Message):
    """Отображение главного меню
    :param message:
    :return:
    """
    # Создание клавиатуры
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [
                types.KeyboardButton(text="Добавить товары (загрузить файл)"),
            ],
            [
                types.KeyboardButton(text="Получить цены"),
            ],
            [
                types.KeyboardButton(text="Посмотреть цены"),
            ],

        ],
        resize_keyboard=True
    )

    await message.reply("Парсер цен. Выберите действие.", reply_markup=keyboard)


async def handle_get_file(message: types.Message, db: AsyncSession, state: FSMContext):
    """Прием файла и импорт данных в БД
    :param message:
    :param db:
    :param state:
    :return:
    """
    if message.content_type == 'document':
        # Обработка загрузки файла
        file_extension = message.document.file_name.split('.')[-1].lower()
        if file_extension in ['xls', 'xlsx', 'csv']:
            file_id = message.document.file_id
            file = await message.bot.get_file(file_id)
            file_path = file.file_path

            # Загрузка файла
            success = await FileService.download_file(message.bot, file_path,
                                                      f'{Config.FILE_PATH}/{message.document.file_name}')
            if success:
                await message.answer(f"Обработка файла...")

                try:
                    # Получение данных из файла и сохранение в БД
                    res = await FileService.import_product_data(success, db)

                    answer = ""
                    for product in res[0]:
                        pre_answer = f"Название:\n{product.title}\n\nurl:\n{product.url}\n\nxpath:\n{product.xpath}\n\n"

                        if len(answer) + len(pre_answer) > 4096:
                            await message.answer(answer)
                            answer = ""
                        answer += pre_answer

                    await message.answer(answer)
                    await message.answer(f"\nИмпортировано {res[1]} товаров")

                except HTTPException as e:
                    await message.answer(e.detail)
                except Exception as e:
                    await message.answer(str(e))

            else:
                await message.answer("Не удалось скачать файл.")

            await state.clear()  # Сбрасываем состояние после загрузки файла
        else:
            await message.answer("Допустимые типы файлов: xls, xlsx, csv.")
    else:
        await message.answer("Пожалуйста, загрузите файл.")


async def handle_parser(message: types.Message, db: AsyncSession):
    """Парсинг цен товаров
    :param message:
    :param db:
    :return:
    """
    await message.answer(
        "В зависимости от количества задач, процесс может потребовать длительного времени. Пожалуйста, ожидайте.")
    async for answer in get_price_and_save(db):
        await message.answer(answer, parse_mode="Markdown", disable_web_page_preview=True)


async def view_price(message: types.Message, db: AsyncSession):
    """Вывод списка цен товаров
    :param message:
    :param db:
    :return:
    """
    await message.answer("Список отслеживаемых ресурсов и цен по датам.")
    result = await get_product_prices(db)
    answer = ""
    for title, url, dates in result:
        title = f"[{title}]({url})"
        pre_answer = f"{title}\n"
        for date, price in dates.items():
            pre_answer += f"{date} - {price / 100:.2f} ₽\n"
        pre_answer += "\n"

        if len(answer) + len(pre_answer) > 4096:
            await message.answer(answer, parse_mode="Markdown", disable_web_page_preview=True)
            answer = ""
        answer += pre_answer

    if not answer:
        answer = "Список пуст"
    await message.answer(answer, parse_mode="Markdown", disable_web_page_preview=True)


async def clear_db(message: types.Message, db: AsyncSession):
    """Очистка БД
    :param message:
    :param db:
    :return:
    """
    await message.answer(await clear_tables(db))


async def handle_main_menu(message: types.Message, state: FSMContext):
    """Обработка нажатий на кнопки главного меню
    :param message:
    :param state:
    :return
    """
    await state.set_state(FileState.send_file)  # Устанавливаем состояние
    await message.answer("Загрузите файл:")


async def start_command(message: types.Message):
    """Обработка команды /start"""
    await show_main_menu(message)  # Отображение главного меню


async def help_command(message: types.Message):
    """Обработка команды /help"""
    help_text = f"""
Я прослежу за изменением цен выбранных Вами товаров. Все очень просто!
1. Создайте xlsx файл с 3 столбцами: 
    - title - это название записи (подойдет название магазина/товара)
    - url   - url адрес интересующего Вас товара
    - xpath - путь к тегу с ценой (та самая циферка).
    
2. Нажимаете кнопку "Добавить товары (загрузить файл)", я Вам предложу загрузить файл.
   Обратите внимание, принимаю только файлы электронных таблиц с расширениями: xls, xlsx, csv.

3. Загрузите подготовленный файл.

4. После обработки я добавлю выбранные товары в список отслеживания.

Чтобы обновить информацию о ценах отслеживаемых товаров, нажмите кнопку "Получить цены".
Я сбегаю на сайты и запишу что у них теперь с ценами.
Иногда ответ получить не удается, тогда в цену товара записывается 0.

Если хотите посмотреть цены, нажмите кнопку "Посмотреть цены".
Я выведу список дат и цен, которые собирались при нажатии кнопки "Получить цены" для каждого товара.

Доступные команды:
/start - Начать работу с ботом.
/help - Показать эту справку.
/clear - Очистить базу данных.
"""
    await message.answer(help_text)


async def handle_unknown_message(message: types.Message):
    """Обработчик для неизвестных сообщений"""
    await message.answer("Извините, я не понимаю это сообщение. Пожалуйста, используйте доступные команды или кнопки.")


def register_handlers(router):
    """Регистрация обработчиков сообщений
    :param router:
    :return:
    """
    router.message.register(start_command, Command(commands=['start']))
    router.message.register(help_command, Command(commands=['help']))
    router.message.register(clear_db, Command(commands=['clear']))
    router.message.register(handle_main_menu, F.text.in_(["Добавить товары (загрузить файл)"]))
    router.message.register(handle_parser, F.text.in_(["Получить цены"]))
    router.message.register(view_price, F.text.in_(["Посмотреть цены"]))
    router.message.register(handle_get_file, StateFilter(FileState.send_file), F.content_type == 'document')
    router.message.register(handle_unknown_message)  # Обработчик по умолчанию
