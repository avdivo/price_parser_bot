from typing import List, Dict, Tuple
from datetime import datetime, timezone
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import ProductInfo, PriceScan


async def get_all_products(session: AsyncSession) -> List[ProductInfo]:
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


async def get_product_prices(session: AsyncSession) -> List[Tuple[str, str, Dict[str, int]]]:
    """
    Асинхронно извлекает историю цен всех продуктов из базы данных.

    :param session: Асинхронная сессия SQLAlchemy.
    :return: Список кортежей, где [0] - название продукта, [1] - url ресурса, а [2] - словарь {дата: цена},
             отсортированный по дате.
    """
    stmt = select(ProductInfo).options(selectinload(ProductInfo.price_scans))
    result = await session.execute(stmt)
    products = result.scalars().all()

    return [(
        product.title, product.url, {
            scan.scan_time.strftime("%d.%m.%Y %H:%M"): scan.price
            for scan in sorted(product.price_scans, key=lambda x: x.scan_time)
        })
        for product in products
    ]
