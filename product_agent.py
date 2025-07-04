import os
import json
import chromadb
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI
from dotenv import load_dotenv


load_dotenv() # Загружаею переменные окружения

class ProductBot:
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
    
    def analyze_query(self, user_message):
        prompt = f"""
        Проанализируй запрос пользователя магазина техники.
        
        Категории: headphones, smartphones, smartwatches, laptops, robot_vacuums
        
        Запрос: "{user_message}"
        
        Ответь JSON:
        {{"category": "категория или null", "search_query": "улучшенный запрос"}}
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=100
            )
            
            result = json.loads(response.choices[0].message.content)
            return result.get('category'), result.get('search_query', user_message)
            
        except Exception as e:
            print(f"OpenAI ошибка: {e}")
            return None, user_message
    
    def search_products(self, query, category=None):
        """Поиск товаров в ChromaDB"""
        try:
            if category:
                collection = self.chroma_client.get_collection(f"darwin_{category}")
            else:
                # По умолчанию ищем в смартфонах
                collection = self.chroma_client.get_collection("darwin_smartphones")
            
            results = collection.query(
                query_texts=[query],
                n_results=3
            )
            
            products = []
            for i in range(len(results['documents'][0])):
                product = {
                    'name': results['metadatas'][0][i]['name'],
                    'price': results['metadatas'][0][i]['price'],
                    'description': results['metadatas'][0][i]['description']
                }
                products.append(product)
            
            return products
            
        except Exception as e:
            print(f"Поиск ошибка: {e}")
            return []

# Создаем бота
bot = ProductBot()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    message = """
Добро пожаловать в Darwin Store!

Я умный помощник по поиску техники:
Наушники
Смартфоны  
Умные часы
Ноутбуки
Роботы-пылесосы

Просто напишите что ищете!
"""
    await update.message.reply_text(message)

async def search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик поиска"""
    user_query = update.message.text
    
    await update.message.reply_text("🔍 Анализирую запрос...")
    
    # Анализируем запрос через OpenAI
    category, improved_query = bot.analyze_query(user_query)
    
    # Ищем товары
    products = bot.search_products(improved_query, category)
    
    if products:
        response = f"Найдено по запросу: '{user_query}'\n\n"
        
        for i, product in enumerate(products, 1):
            response += f"{i}. {product['name']}\n"
            response += f"💰 {product['price']} лей\n"
            response += f"📝 {product['description']}\n\n"
        
    else:
        response = "Ничего не найдено. Попробуйте другой запрос."
    
    await update.message.reply_text(response)

def main():

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not token:
        print("Не найден TELEGRAM_BOT_TOKEN в .env")
        return
    
    app = Application.builder().token(token).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_handler))
    
    print("Бот запущен")
    app.run_polling()

if __name__ == "__main__":
    main()