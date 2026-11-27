
import argparse
import asyncio
import json
import os
import re

from dotenv import load_dotenv
from fastmcp import Client
from openai import AsyncOpenAI
from pydantic import ValidationError

from src.agent.mcp_server import mcp
from src.agent.schemas import TubingInput


# Загружаем API-ключ из файла .env
load_dotenv()

MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")


async def extract_data_with_llm(request: str) -> TubingInput:
    """LLM извлекает параметры НКТ из русского текста."""

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError(
            "Не найден GROQ_API_KEY. Проверь файл .env"
        )

    llm = AsyncOpenAI(
        api_key=api_key,
        base_url="https://routerai.ru/api/v1",
        timeout=60,
        max_retries=1,
    )

    try:
        response = await llm.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты извлекаешь параметры НКТ из инженерного запроса. "
                        "Верни только JSON с полями: "
                        "well_id, od_mm, wall_mm, id_mm. "
                        "Все диаметры и толщина — в мм. "
                        "Не исправляй неправильные значения. "
                        "Не вычисляй внутренний диаметр вместо пользователя. "
                        "Не выдумывай отсутствующие параметры. "
                        "Для отсутствующих значений используй null. "
                        "Никакого Markdown и пояснений."
                    ),
                },
                {
                    "role": "user",
                    "content": request,
                },
            ],
            temperature=0,
            max_completion_tokens=300,
        )
    finally:
        await llm.close()

    if not response.choices:
        raise RuntimeError("Groq вернул пустой список choices")

    content = response.choices[0].message.content

    if not content:
        raise RuntimeError("Groq вернул пустой текст ответа")

    # Убираем Markdown, если модель добавила ```json
    content = re.sub(
        r"^```(?:json)?\s*|\s*```$",
        "",
        content.strip(),
        flags=re.IGNORECASE,
    ).strip()

    print("\n=== GROQ: ПАРАМЕТРЫ ИЗ ТЕКСТА ===")
    print(content)

    # Проверяем ответ модели через Pydantic
    return TubingInput.model_validate_json(content)


async def call_mcp(client, data: TubingInput):
    """Вызываем настоящий MCP-инструмент."""

    response = await client.call_tool(
        "check_tubing",
        data.model_dump(),
    )

    return response.data


async def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--llm",
        action="store_true",
        help="Разобрать запрос через Groq API",
    )

    parser.add_argument(
        "--request",
        type=str,
        default=None,
        help="Инженерный запрос на русском языке",
    )

    args = parser.parse_args()

    async with Client(mcp) as client:

        if args.llm:
            # Один текстовый запрос или два демонстрационных
            requests = (
                [args.request]
                if args.request
                else [
                    (
                        "Проверь НКТ скважины W-31: "
                        "наружный диаметр 73 мм, "
                        "толщина стенки 5.5 мм, "
                        "внутренний диаметр 62 мм."
                    ),
                    (
                        "Проверь НКТ скважины W-31: "
                        "наружный диаметр 73 мм, "
                        "толщина стенки 5.5 мм, "
                        "внутренний диаметр 80 мм."
                    ),
                ]
            )

            for request in requests:
                print("\n=== ЗАПРОС ПОЛЬЗОВАТЕЛЯ ===")
                print(request)

                try:
                    data = await extract_data_with_llm(request)

                    print("\n=== ВЫЗОВ MCP ===")
                    result = await call_mcp(client, data)

                    print("\n=== РЕЗУЛЬТАТ АГЕНТА ===")
                    print(json.dumps(
                        result,
                        ensure_ascii=False,
                        indent=2,
                    ))

                except (ValidationError, ValueError) as error:
                    print("\n=== ОШИБКА ВХОДНЫХ ДАННЫХ ===")
                    print(str(error))

                except Exception as error:
                    print("\n=== ОШИБКА LLM/API/MCP ===")
                    print(type(error).__name__, str(error)[:1000])

        else:
            # Старый режим — без LLM и без API-ключа
            for label, id_mm in [
                ("УСПЕШНЫЙ ЗАПРОС", 62),
                ("НЕКОРРЕКТНЫЙ ВХОД", 80),
            ]:
                print(f"\n=== {label} ===")

                response = await client.call_tool(
                    "check_tubing",
                    {
                        "well_id": "W-31",
                        "od_mm": 73,
                        "wall_mm": 5.5,
                        "id_mm": id_mm,
                    },
                )

                print(json.dumps(
                    response.data,
                    ensure_ascii=False,
                    indent=2,
                ))


if __name__ == "__main__":
    asyncio.run(main())
