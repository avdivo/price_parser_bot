import re
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.parser import get_element_content
from app.db.crud import get_all_products, add_price_scan


def convert_price_to_kopecks(price_str: str) -> int:
    """
    Преобразует строку с ценой в копейки.

    :param price_str: Строка с ценой, которая может содержать цифры, знак рубля и дробную запятую.
    :return: Цена в копейках как целое число или 0, если строка не соответствует формату.
    """
    # Проверяем длину строки
    if not price_str or len(price_str) > 20:
        return 0

    # Оставляем только цифры и дробную запятую
    cleaned_price = re.sub(r'[^0-9,]', '', price_str)

    # Заменяем запятую на точку для корректного преобразования в float
    cleaned_price = cleaned_price.replace(',', '.')

    try:
        # Преобразуем в число с плавающей точкой
        price_float = float(cleaned_price)

        # Переводим в копейки
        kopecks = int(price_float * 100)
        return kopecks
    except ValueError:
        # Если преобразование не удалось, возвращаем None
        return 0


async def get_price_and_save(session: AsyncSession) -> str:
    """
    С помощью функции получает все записи из таблицы ProductInfo.
    Запускает получение цен для каждого объекта.
    Обрабатывает и пересчитывает цену в копейки.
    Передает в функцию для сохранения в БД.

    :param session: Асинхронная сессия для взаимодействия с базой данных.
    :return: список с названий и цен в виде текста.
    """
    try:
        products = await get_all_products(session)

        # # Запуск всех запросов параллельно
        tasks = [get_element_content(p.title, p.url, p.xpath) for p in products]
        results = await asyncio.gather(*tasks)

        answer = ""
        for product, content in zip(products, results):
            price = convert_price_to_kopecks(content)
            await add_price_scan(session, product, price)  # Сохраняем цены в БД
            title = f"[{product.title}]({product.url})"
            answer += f"{title}\n  Цена: {price / 100:.2f} ₽\n"
    except:
        answer = "Извините. Произошла ошибка. Повторите позже."

    return answer
