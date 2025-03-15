from datetime import datetime
from sqlalchemy import Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import mapped_column, Mapped, relationship

from app.core.database import Base


class ProductInfo(Base):
    """
    Данные для парсинга товара
    """
    __tablename__ = "product_info"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True,
        doc="Уникальный идентификатор записи")
    title: Mapped[str] = mapped_column(String(length=255), nullable=False, doc="Название продукта")
    url: Mapped[str] = mapped_column(String(length=500), nullable=False, doc="URL продукта на сайте")
    xpath: Mapped[str] = mapped_column(String(length=500), nullable=False, doc="XPath для парсинга цены на странице")

    # Связь один-ко-многим с таблицей цен
    price_scans: Mapped[list["PriceScan"]] = relationship("PriceScan",back_populates="product",
        doc="Список всех записей о сканировании цен для данного продукта")

    def __repr__(self) -> str:
        return f"<ProductInfo(title='{self.title}', url='{self.url}', xpath='{self.xpath}')>"


class PriceScan(Base):
    """
    История цен на товары в модели с данными для парсинга
    """
    __tablename__ = "price_scans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True,
        doc="Уникальный идентификатор записи сканирования")
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("product_info.id", ondelete="CASCADE"),
        nullable=False, index=True, doc="ID связанного продукта из таблицы product_info")
    price: Mapped[int] = mapped_column(Integer, nullable=False, doc="Цена в копейках на момент сканирования")
    scan_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow,
        doc="Дата и время сканирования в формате UTC")

    # Обратная связь с ProductInfo
    product: Mapped["ProductInfo"] = relationship("ProductInfo", back_populates="price_scans",
        doc="Связанный продукт")

    def __repr__(self) -> str:
        return f"<PriceScan(id={self.id}, product_id={self.product_id}, price={self.price}, time={self.scan_time})>"
