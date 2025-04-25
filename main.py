import requests
import asyncio
import aiohttp
import ssl
import json
from datetime import datetime
import argparse


DATA_FILE = "api_data.json"
ERROR_LOG = "errors.log"

def log_error(error_msg):
    """Логирование ошибок в файл"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(ERROR_LOG, "a") as f:
        f.write(f"[{timestamp}] {error_msg}\n")

def save_to_file(data):
    """Сохранение данных в JSON-файл"""
    try:
        with open(DATA_FILE, "a+") as f:
            f.seek(0)
            try:
                existing = json.load(f)
            except json.JSONDecodeError:
                existing = []
            existing.append(data)
            f.seek(0)
            json.dump(existing, f, indent=2)
        print(f"💾 Данные сохранены в {DATA_FILE}")
    except Exception as e:
        log_error(f"Ошибка сохранения: {str(e)}")
        print("❌ Ошибка сохранения данных")

def get_sync_cat_fact(save=False):
    """Синхронный запрос фактов о кошках с возможностью сохранения"""
    url = "https://catfact.ninja/fact"
    
    try:
        start = datetime.now()
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        print("\n🐱 Синхронный факт о кошках:")
        print(f"{data['fact']} (Длина: {data['length']} символов)")
        
        if save:
            save_data = {
                "type": "cat_fact",
                "data": data,
                "timestamp": str(start)
            }
            save_to_file(save_data)
            
        print(f"⏱ Время выполнения: {(datetime.now() - start).total_seconds():.2f} сек")

    except requests.exceptions.RequestException as e:
        error_msg = f"Синхронный запрос: {str(e)}"
        log_error(error_msg)
        print(f"\n❌ {error_msg}")

async def fetch_async(session, url, category):
    """Улучшенный асинхронный запрос с повторами"""
    retries = 3
    for attempt in range(retries):
        try:
            async with session.get(url, ssl=False) as response:
                if response.status == 200:
                    data = await response.json()
                    return (category, data)
                print(f"⚠️ Попытка {attempt+1}/{retries}: Ошибка {category} (HTTP {response.status})")
        except Exception as e:
            print(f"⚠️ Попытка {attempt+1}/{retries}: Ошибка {category} - {str(e)}")
        await asyncio.sleep(1)
    return (category, None)

async def get_async_data(categories, save=False):
    """Асинхронный сбор данных с выбором категорий"""
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    endpoints = {
        "quote": "https://api.quotable.io/random",
        "todo": "https://jsonplaceholder.typicode.com/todos/1",
        "user": "https://randomuser.me/api/"
    }

    async with aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=15),
        connector=aiohttp.TCPConnector(ssl=ssl_context)
    ) as session:
        
        tasks = [fetch_async(session, endpoints[cat], cat) for cat in categories]
        results = await asyncio.gather(*tasks)
        
        print("\n🔍 Асинхронные результаты:")
        saved_data = []
        
        for category, data in results:
            if data:
                result = format_result(category, data)
                print(result)
                if save:
                    saved_data.append({
                        "type": category,
                        "data": data,
                        "timestamp": str(datetime.now())
                    })
            else:
                print(f"❌ {category.capitalize()} не получен")
        
        if save and saved_data:
            save_to_file({"async_data": saved_data})

def format_result(category, data):
    """Форматирование вывода результатов"""
    if category == "quote":
        return f"📜 Цитата дня:\n«{data['content']}»\n— {data['author']}"
    elif category == "todo":
        return f"✅ Задача:\n{data['title']}\nСтатус: {'выполнено' if data['completed'] else 'не выполнено'}"
    elif category == "user":
        user = data['results'][0]
        return f"👤 Пользователь:\n{user['name']['first']} {user['name']['last']}\nEmail: {user['email']}"
    return ""

def main():
    parser = argparse.ArgumentParser(description="Сбор данных с различных API")
    parser.add_argument('--sync', action='store_true', help="Выполнить синхронный запрос")
    parser.add_argument('--async-cats', nargs='+', choices=['quote', 'todo', 'user'],
                      default=['quote', 'todo'], help="Выбор асинхронных категорий")
    parser.add_argument('--save', action='store_true', help="Сохранить результаты в файл")
    args = parser.parse_args()

    print("🚀 Начинаем сбор данных...")
    
    if args.sync:
        get_sync_cat_fact(args.save)
    
    if args.async_cats:
        start_time = datetime.now()
        asyncio.run(get_async_data(args.async_cats, args.save))
        print(f"⏱ Общее асинхронное время: {(datetime.now() - start_time).total_seconds():.2f} сек")

if __name__ == "__main__":
    main()