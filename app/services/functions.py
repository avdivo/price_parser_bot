import re
import asyncio

from app.services.parser import get_element_content
from app.db.crud import get_all_products, add_price_scan
from app.models.models import ProductInfo

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


# Вспомогательная функция-обёртка
async def wrapped_task(product: ProductInfo, semaphore: asyncio.Semaphore) -> tuple:
    result = await get_element_content(product.url, product.xpath, semaphore)
    return product, result


async def get_price_and_save(session, max_concurrent_tasks: int = 10):
    try:
        products = await get_all_products(session)  # Получаем список товаров
        semaphore = asyncio.Semaphore(max_concurrent_tasks)  # Создаём семафор

        # Создаём список пар (task, product)
        tasks = [asyncio.create_task(wrapped_task(p, semaphore)) for p in products]

        count = 10  # Счетчик количества строк вывода
        answer = ""
        # Используем as_completed для обработки результатов по мере их готовности
        for task in asyncio.as_completed(tasks):
            product, content = await task  # Получаем результат текущей задачи

            # Обработка и сохранение результата
            price = convert_price_to_kopecks(content)
            await add_price_scan(session, product, price)
            title = f"[{product.title}]({product.url})"
            answer += f"{title}\n  Цена: {price / 100:.2f} ₽\n"

            count -= 1
            if count == 0:
                answer += "\nПродолжение следует..."
                yield answer
                answer = ""
                count = 10


    except Exception as e:
        answer = f"Извините. Произошла ошибка: {str(e)}"

    answer += "\nКонец списка."
    yield answer
