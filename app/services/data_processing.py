import os
import httpx
import pandas as pd
from aiogram import Bot
from typing import List, Tuple
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import ProductInfo


class FileService:
    @staticmethod
    async def download_file(bot: Bot, file_path: str, destination_path: str) -> str | None:
        """
        Асинхронно скачивает файл по указанному пути и сохраняет его на диск.
        Если файл с таким именем уже существует, добавляет числовой суффикс.

        :param bot: Экземпляр бота, используемый для получения токена.
        :param file_path: Путь к файлу на сервере Telegram.
        :param destination_path: Локальный путь, куда будет сохранен файл.
        :return: Кортеж (путь, имя файла) если файл успешно скачан и сохранен, иначе None.
        """
        url = f'https://api.telegram.org/file/bot{bot.token}/{file_path}'

        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            if response.status_code == 200:
                # Извлекаем имя файла из пути
                file_name = os.path.basename(destination_path)
                name, ext = os.path.splitext(file_name)

                # Проверяем наличие файла и добавляем суффикс при необходимости
                counter = 1
                new_file_path = destination_path
                while os.path.exists(new_file_path):
                    new_file_path = os.path.join(os.path.dirname(destination_path), f"{name}_{counter}{ext}")
                    counter += 1

                # Сохраняем файл
                with open(new_file_path, 'wb') as f:
                    f.write(response.content)

                return new_file_path
            else:
                return None

    @staticmethod
    async def import_product_data(file_path: str, db: AsyncSession) -> Tuple[List[ProductInfo], int]:
        """
        Асинхронно читает файл таблицы по указанному пути, извлекает из него данные
        трех текстовых столбцов (title, url, xpath) и записывает их в таблицу ProductInfo.

        :param file_path: Путь к файлу таблицы (поддерживаются форматы CSV, Excel)
        :param db: Асинхронная сессия SQLAlchemy для работы с БД

        :return Tuple[List[ProductInfo], int]: Кортеж, содержащий список созданных объектов ProductInfo и их количество

        :raises HTTPException: В случае ошибки чтения файла или сохранения данных в БД
        """
        try:
            # Определяем формат файла по расширению
            file_ext = os.path.splitext(file_path)[1].lower()

            # Читаем файл в зависимости от формата
            if file_ext == '.csv':
                df = pd.read_csv(file_path)
            elif file_ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Неподдерживаемый формат файла: {file_ext}. Поддерживаются только CSV и Excel."
                )

            # Проверяем наличие необходимых столбцов
            required_columns = ['title', 'url', 'xpath']
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                raise HTTPException(status_code=400,
                    detail=f"В таблице отсутствуют обязательные столбцы: {', '.join(missing_columns)}"
                )

            # Создаем список объектов ProductInfo
            product_info_objects = []

            # Проходим по каждой строке DataFrame
            for _, row in df.iterrows():
                product_info = ProductInfo(
                    title=row['title'],
                    url=row['url'],
                    xpath=row['xpath']
                )
                product_info_objects.append(product_info)

            # Добавляем объекты в БД
            db.add_all(product_info_objects)
            await db.commit()

            # Обновляем объекты после коммита, чтобы получить их ID
            for product_info in product_info_objects:
                await db.refresh(product_info)

            return product_info_objects, len(product_info_objects)

        except pd.errors.EmptyDataError:
            await db.rollback()
            raise HTTPException(
                status_code=400,
                detail="Файл таблицы пуст или содержит некорректные данные"
            )
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при сохранении данных в БД"
            )
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Произошла ошибка при обработке файла"
            )
