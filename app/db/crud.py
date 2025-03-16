import pytz
from typing import List, Dict, Tuple, Sequence
from datetime import datetime, timezone
from sqlalchemy import delete
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import ProductInfo, PriceScan
from app.core.database import engine, Base


async def get_all_products(session: AsyncSession) -> Sequence[ProductInfo]:
    """
    Асинхронно получает все записи из таблицы ProductInfo.

    :param session: Асинхронная сессия для взаимодействия с базой данных.
    :return: Список объектов ProductInfo.
    """
    result = await session.execute(select(ProductInfo))
    products = result.scalars().all()
    return products


async def add_price_scan(session: AsyncSession, product: ProductInfo, price: int):
    """
    Асинхронно добавляет запись в таблицу PriceScan для указанного продукта с текущей датой и ценой.

    :param session: Асинхронная сессия для взаимодействия с базой данных.
    :param product: Объект ProductInfo, для которого добавляется запись о цене.
    :param price: Цена продукта в копейках.
    """
    price_scan = PriceScan(
        product_id=product.id,
        price=price,
        scan_time=datetime.now(timezone.utc)  # Используем datetime.now с timezone.utc
    )
    session.add(price_scan)
    await session.commit()


async def get_product_prices(session: AsyncSession, user_timezone: str = 'Europe/Moscow') -> List[
    Tuple[str, str, Dict[str, int]]]:
    """
    Асинхронно извлекает историю цен всех продуктов из базы данных.

    :param session: Асинхронная сессия SQLAlchemy.
    :param user_timezone: Часовой пояс пользователя, например, 'Europe/Moscow'.
    :return: Список кортежей, где [0] - название продукта, [1] - url ресурса, а [2] - словарь {дата: цена},
             отсортированный по дате.
    """
    stmt = select(ProductInfo).options(selectinload(ProductInfo.price_scans))
    result = await session.execute(stmt)
    products = result.scalars().all()

    # Преобразование времени в часовой пояс пользователя
    user_tz = pytz.timezone(user_timezone)

    def convert_to_user_timezone(scan_time):
        # Если scan_time наивное (без часового пояса), привязываем к UTC
        if scan_time.tzinfo is None:
            scan_time = scan_time.replace(tzinfo=timezone.utc)
        # Преобразуем время в часовой пояс пользователя
        return scan_time.astimezone(user_tz)

    return [(
        product.title, product.url, {
            convert_to_user_timezone(scan.scan_time).strftime("%d.%m.%Y %H:%M"): scan.price
            for scan in sorted(product.price_scans, key=lambda x: x.scan_time)
        })
        for product in products
    ]


async def clear_tables(session: AsyncSession) -> str:
    """
    Удаляет все записи из таблиц ProductInfo и PriceScan.

    :param session: Асинхронная сессия для взаимодействия с базой данных.
    """
    try:
        pass
        # Удаляем все таблицы
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

        # Создаем все таблицы заново
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        await session.rollback()
        return f"Произошла ошибка при удалении записей: {e}"
    finally:
        await session.close()
        return "База данных очищена"
