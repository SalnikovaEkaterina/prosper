import os
import streamlit as st
from dotenv import load_dotenv

# Импортируем наши модули
from src.prosper_client import ProsperClient
from agent import ProsperAgent

# Загружаем переменные окружения из .env
load_dotenv()

# Настройка страницы Streamlit
st.set_page_config(page_title="PROSPER AI Assistant", page_icon="🛢️", layout="centered")
st.title("🛢️ AI-Ассистент PROSPER")
st.markdown("Задайте вопрос по модели или попросите выполнить расчет.")

@st.cache_resource
def init_system():
    """Инициализация клиента PROSPER и Агента (кэшируется)."""
    # Получаем ключи из переменных окружения
    prosper_url = os.getenv("PROSPER_API_URL")
    prosper_token = os.getenv("PROSPER_API_TOKEN")
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    deepseek_model = os.getenv("DEEPSEEK_MODEL")

    if not all([prosper_url, prosper_token, deepseek_key, deepseek_model]):
        st.error("Ошибка: Не все переменные окружения заданы. Проверьте файл .env")
        return None, None

    # 1. Инициализируем клиент PROSPER
    prosper = ProsperClient(base_url=prosper_url, token=prosper_token)
    
    # 2. Проверяем здоровье сервера
    status, health = prosper.health()
    if status != 200:
        st.error(f"Сервер PROSPER недоступен. Статус: {status}, Ответ: {health}")
        return None, None

    # 3. Открываем сессию
    if not prosper.open_session():
        st.error("Не удалось открыть сессию PROSPER. Возможно, токен уже занят другим студентом.")
        return None, None

    # 4. Создаем агента (используем RouterAI как базу)
    agent = ProsperAgent(
        api_key=deepseek_key,
        base_url="https://routerai.ru/api/v1",
        model_name=deepseek_model,
        prosper_client=prosper
    )
    
    return agent, prosper

# Инициализируем систему при первом запуске
agent, prosper = init_system()

if agent and prosper:
    # Хранилище сообщений в сессии Streamlit
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Отображаем историю чата
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Поле ввода для пользователя
    if prompt := st.chat_input("Например: прочитай параметр PROSPER.PVT.Input.Solgor"):
        # Добавляем сообщение пользователя в историю
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Получаем ответ от агента
        with st.chat_message("assistant"):
            with st.spinner("Думаю..."):
                response = agent.run(prompt)
                st.markdown(response)
        
        # Добавляем ответ агента в историю
        st.session_state.messages.append({"role": "assistant", "content": response})
