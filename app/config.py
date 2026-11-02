"""Configuration & LLM Proxy Client Setup
อ่านค่า Environment variables และสร้าง OpenAI client สำหรับเชื่อมต่อ Class Proxy
"""

import os
from dotenv import load_dotenv
from openai import OpenAI, AsyncOpenAI

# โหลดตัวแปรจากไฟล์ .env
load_dotenv()

# การตั้งค่า LLM Proxy ตามข้อกำหนดของรายวิชา
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "")
MODEL_NAME = os.getenv("MODEL_NAME", "gemma-4-E4B-it")

# การตั้งค่า Web Server
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))

def get_openai_client() -> OpenAI:
    """
    สร้างและคืนค่า OpenAI client ที่เชื่อมต่อกับ Class Proxy
    โดยอ่าน API Key และ Base URL จาก Environment Variables โดยตรง (ปลอดภัย ไม่ฮาร์ดโค้ด)
    """
    kwargs = {}
    if OPENAI_BASE_URL:
        kwargs["base_url"] = OPENAI_BASE_URL
    if OPENAI_API_KEY:
        kwargs["api_key"] = OPENAI_API_KEY

    return OpenAI(**kwargs)

def get_async_openai_client() -> AsyncOpenAI:
    kwargs = {}
    if OPENAI_BASE_URL:
        kwargs["base_url"] = OPENAI_BASE_URL
    if OPENAI_API_KEY:
        kwargs["api_key"] = OPENAI_API_KEY

    return AsyncOpenAI(**kwargs)


