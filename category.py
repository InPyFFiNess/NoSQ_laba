from beanie import Document, init_beanie
from pydantic import BaseModel
import asyncio
from pymongo import AsyncMongoClient

class Category(BaseModel):
    tip: str
    description: str

class PC_Components(Document):
    production: str
    model: str
    price: float
    category: Category

    class Settings:
        name = "PC_Components"

async def main():
    client = AsyncMongoClient("mongodb://localhost:27017")
    await init_beanie(database=client.Catalog, document_models=[PC_Components])
    
    await PC_Components(production="NVIDIA", model="RTX 3050", price=3000, Category(tip="video card", )).insert()
    await PC_Components().insert()
    await PC_Components().insert()
    
    items = await Product.find().skip(1).limit(2).to_list()
    print([f"{i.name} - ${i.price}" for i in items])
    
    prod = await Product.find(Product.name == "Laptop").first_or_none()
    if prod:
        prod.price = 1200
        await prod.save()
        print("Обновлено:", prod.name, prod.price)
        
    sorted_items = await Product.find().sort("-price").to_list()
    print("Отсортировано:", [f"{i.name}({i.price})" for i in sorted_items])
    
    expensive = await Product.find(Product.price > 600).to_list()
    print("Дороже 600:", [i.name for i in expensive])
    
    cheap = await Product.find(Product.price <= 500).to_list()
    print("500 и дешевле:", [i.name for i in cheap])

    await Product.find(Product.name == "Tablet").delete()
    print("Удален Tablet")

asyncio.run(main())