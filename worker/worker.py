import asyncio
import json
import os
import logging
from kafka import KafkaConsumer
from aiogram import Bot

logging.basicConfig(level=logging.INFO)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_HOST = "-4710531535"

if not TELEGRAM_BOT_TOKEN:
    logging.error("TELEGRAM_BOT_TOKEN не задан! Укажите его в .env")
    exit(1)

KAFKA_BROKER_URL = "kafka:9092"
KAFKA_TOPIC = "user_registration"

bot = Bot(token=TELEGRAM_BOT_TOKEN)

async def send_telegram_message(contact: str, message: str):
    try:
        logging.info(f"Отправка сообщения {message} пользователю {contact}")
        await bot.send_message(contact, message)
    except Exception as e:
        logging.error(f"Ошибка при отправке сообщения: {e}")

consumer = KafkaConsumer(
    KAFKA_TOPIC,
    bootstrap_servers=KAFKA_BROKER_URL,
    group_id="telegram_worker",
    value_deserializer=lambda x: json.loads(x.decode('utf-8')) if x else None
)

async def listen_to_kafka():
    logging.info("Kafka worker запущен, слушаем сообщения...")
    for message in consumer:
        raw_value = message.value
        logging.info(f"Получено сообщение: {raw_value}")

        if raw_value is None:
            logging.warning("Получено пустое сообщение! Пропускаем...")
            continue 

        try:
            if isinstance(raw_value, str):
                data = json.loads(raw_value)
            else:
                data = raw_value
            contact = data.get("contact")
            message_text = data.get("message")

            if not contact or not message_text:
                logging.warning(f"Пропущено сообщение {data}, т.к. нет 'contact' или 'message'")
                await send_telegram_message(TELEGRAM_HOST, message_text)
                continue
            logging.info(f"Отправляем сообщение '{message_text}' контакту {contact}")
            await send_telegram_message(contact, message_text)
            await send_telegram_message(TELEGRAM_HOST, message_text)
        except json.JSONDecodeError as e:
            logging.error(f"Ошибка декодирования JSON: {e}. Исходное сообщение: {raw_value}")

if __name__ == "__main__":
    asyncio.run(listen_to_kafka())
