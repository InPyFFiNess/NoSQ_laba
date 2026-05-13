from beanie import Document
from pydantic import BaseModel
from beanie import init_beanie
import asyncio
from pymongo import AsyncMongoClient
import base64

def image_to_base64_str(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        type_img = image_file.name.split('.', 1)[1]
    return encoded_string, type_img

def base64_str_to_image(base64_string, output_path):
    with open(output_path, "wb") as image_file:
        decoded_data = base64.b64decode(base64_string)
        image_file.write(decoded_data)
    


#сделать так, чтобы возвращало не только картинку, но и формат файла

class Profiles(Document):
    name: str
    description: str
    avatar: bytes
    type_img: str

    class Settings:
        name = "profiles"

async def main():
    client = AsyncMongoClient("mongodb://localhost:27017/")
    db = client.MyDB

    await init_beanie(database=db, document_models=[Profiles])

    img = image_to_base64_str("image.png")
    
    product = Profiles(name="User2", description="...", avatar=img[0], type_img=img[1])
    await product.insert()

    user = await Profiles.find_one(Profiles.name == "User2")
    base64_str_to_image(user.avatar, f"outuput_img.{user.type_img}")

if __name__ == "__main__":
    asyncio.run(main())