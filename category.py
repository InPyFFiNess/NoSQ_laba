import asyncio
from typing import List, Literal, Union
from beanie import Document, init_beanie, Link
from pymongo import AsyncMongoClient 
from pydantic import BaseModel

class Motherboard(BaseModel):
    type: Literal["Материнская плата"] = "Материнская плата"
    format: str
    socket: str
    description: str


class Processor(BaseModel):
    type: Literal["Процессор"] = "Процессор"
    socket: str
    frequency: str
    description: str


class OZU(BaseModel):
    type: Literal["ОЗУ"] = "ОЗУ"
    frequency: str
    volume: str
    description: str


class PZU(BaseModel):
    type: Literal["ПЗУ"] = "ПЗУ"
    format: str
    volume: str
    description: str


class GPU(BaseModel):
    type: Literal["Видеокарта"] = "Видеокарта"
    volume: str
    ports: List[str]  
    description: str

class Avatars(Document):
    name: str
    file: bytes

    class Settings:
        name = "avatars"


class Product(Document):
    production: str
    model: str
    price: float
    category: Union[Motherboard, Processor, OZU, PZU, GPU]

    class Settings:
        name = "PC_components"

components_data = [
    # Материнские платы
    Product(production="ASUS", model="ROG STRIX B650-A", price=239.99, category=Motherboard(description="Игровая плата AM5", format="ATX", socket="AM5")),
    Product(production="MSI", model="MAG B760 TOMAHAWK", price=189.99, category=Motherboard(description="Надежная плата LGA1700", format="ATX", socket="LGA1700")),
    Product(production="Gigabyte", model="B650M DS3H", price=119.99, category=Motherboard(description="Бюджетная плата Micro-ATX", format="Micro-ATX", socket="AM5")),
    Product(production="ASRock", model="Z790 Pro RS", price=209.99, category=Motherboard(description="Плата для разгона Intel", format="ATX", socket="LGA1700")),
    Product(production="ASUS", model="PRIME H610M-K", price=79.99, category=Motherboard(description="Офисное решение", format="Micro-ATX", socket="LGA1700")),
    Product(production="MSI", model="MPG X670E CARBON", price=459.99, category=Motherboard(description="Премиум плата для Ryzen 9", format="ATX", socket="AM5")),

    # Процессоры
    Product(production="AMD", model="Ryzen 5 7600X", price=229.00, category=Processor(description="6-ядерный игровой CPU", socket="AM5", frequency="4.7 GHz")),
    Product(production="Intel", model="Core i5-13600K", price=319.00, category=Processor(description="14-ядерный народный CPU", socket="LGA1700", frequency="3.5 GHz")),
    Product(production="AMD", model="Ryzen 7 7800X3D", price=399.00, category=Processor(description="Лучший игровой процессор", socket="AM5", frequency="4.2 GHz")),
    Product(production="Intel", model="Core i9-14900K", price=549.00, category=Processor(description="Флагманский CPU Intel", socket="LGA1700", frequency="3.2 GHz")),
    Product(production="AMD", model="Ryzen 5 5600", price=134.00, category=Processor(description="Доступный народный хит", socket="AM4", frequency="3.5 GHz")),
    Product(production="Intel", model="Core i3-12100F", price=92.00, category=Processor(description="Бюджетный четырехъядерник", socket="LGA1700", frequency="3.3 GHz")),

    # ОЗУ
    Product(production="Corsair", model="Vengeance DDR5", price=115.00, category=OZU(description="Комплект скоростной памяти", frequency="6000 MHz", volume="32 GB")),
    Product(production="Kingston", model="Fury Beast DDR4", price=65.00, category=OZU(description="Надежная DDR4 память", frequency="3200 MHz", volume="16 GB")),
    Product(production="G.Skill", model="Trident Z5 RGB", price=185.00, category=OZU(description="Топовая память с подсветкой", frequency="6400 MHz", volume="32 GB")),
    Product(production="Crucial", model="Basics DDR5", price=45.00, category=OZU(description="Простая планка без радиатора", frequency="4800 MHz", volume="8 GB")),
    Product(production="TeamGroup", model="T-Force Delta", price=129.00, category=OZU(description="Игровая DDR5 белого цвета", frequency="6000 MHz", volume="32 GB")),
    Product(production="Patriot", model="Viper Steel", price=39.00, category=OZU(description="Бюджетная DDR4 для апгрейда", frequency="3600 MHz", volume="8 GB")),

    # ПЗУ
    Product(production="Samsung", model="990 PRO", price=169.99, category=PZU(description="Сверхбыстрый NVMe SSD", format="M.2 2280", volume="2 TB")),
    Product(production="WD", model="Blue SN580", price=69.99, category=PZU(description="Доступный NVMe накопитель", format="M.2 2280", volume="1 TB")),
    Product(production="Crucial", model="BX500", price=34.99, category=PZU(description="Базовый SATA SSD", format="2.5-inch", volume="500 GB")),
    Product(production="Seagate", model="BarraCuda", price=54.99, category=PZU(description="Жесткий диск для архивов", format="3.5-inch", volume="2 TB")),
    Product(production="Kingston", model="KC3000", price=99.99, category=PZU(description="Производительный SSD PCIe 4.0", format="M.2 2280", volume="1 TB")),
    Product(production="SanDisk", model="Ultra 3D", price=119.99, category=PZU(description="Емкий SATA SSD", format="2.5-inch", volume="2 TB")),

    # Видеокарты
    Product(production="NVIDIA", model="RTX 4070 Ti Super", price=799.99, category=GPU(description="Мощная видеокарта для 2K/4K", volume="16 GB", ports=["HDMI 2.1", "DisplayPort 1.4a"])),
    Product(production="AMD", model="Radeon RX 7800 XT", price=499.99, category=GPU(description="Отличный баланс цены и производительности", volume="16 GB", ports=["HDMI 2.1", "DisplayPort 2.1"])),
    Product(production="ASUS", model="Dual RTX 4060", price=299.99, category=GPU(description="Компактная карта для FullHD", volume="8 GB", ports=["HDMI 2.1", "DisplayPort 1.4a"])),
    Product(production="MSI", model="RTX 4090 SUPRIM X", price=1999.99, category=GPU(description="Ультимативный флагман", volume="24 GB", ports=["HDMI 2.1", "DisplayPort 1.4a"])),
    Product(production="Sapphire", model="Pulse RX 7600", price=269.99, category=GPU(description="Бюджетное решение от AMD", volume="8 GB", ports=["HDMI 2.1", "DisplayPort 1.4a"])),
    Product(production="Gigabyte", model="RTX 4080 SUPER", price=999.99, category=GPU(description="Высокая производительность с трассировкой лучей", volume="16 GB", ports=["HDMI 2.1", "DisplayPort 1.4a"]))
]


async def main():
    client = AsyncMongoClient("mongodb://localhost:27017")
    database = client.Catalog
    
    await init_beanie(database=database, document_models=[Product, Avatars])
    print("Успешное подключение к БД 'Catalog' и инициализация Beanie.")

    await Product.find_all().delete()

    result = await Product.insert_many(components_data)
    print(f"Успешно добавлено документов: {len(result.inserted_ids)}")


if __name__ == "__main__":
    asyncio.run(main())