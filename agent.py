import json
from openai import OpenAI
from src.tools import get_tools, call_tool

class ProsperAgent:
    def __init__(self, api_key: str, base_url: str, model_name: str, prosper_client):
        """
        Инициализация агента.
        api_key: ключ от RouterAI
        base_url: https://routerai.ru/api/v1
        model_name: название модели (например, deepseek-chat)
        prosper_client: экземпляр класса ProsperClient
        """
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model_name
        self.prosper = prosper_client
        self.tools = get_tools()

    def run(self, user_prompt: str, max_steps: int = 5) -> str:
        """
        Главный цикл агента: получает запрос, думает, вызывает инструменты,
        возвращает финальный текстовый ответ.
        """
        messages = [
            {
                "role": "system", 
                "content": (
                    "Ты — инженерный ассистент. Используй инструменты PROSPER для расчетов. "
                    "Не придумывай значения, всегда вызывай инструменты. "
                    "Если тебе нужно прочитать параметр, используй get_prosper_parameter. "
                    "Если нужно изменить — set_prosper_parameter. "
                    "Для запуска расчета — run_prosper_calculation."
                )
            },
            {"role": "user", "content": user_prompt}
        ]

        for step in range(max_steps):
            print(f"\n--- Шаг {step + 1} ---")
            
            # Отправляем запрос в LLM (RouterAI)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools,
                tool_choice="auto",
                temperature=0.1
            )
            
            response_message = response.choices[0].message
            messages.append(response_message)

            # Если LLM решила вызвать инструменты
            if response_message.tool_calls:
                for tool_call in response_message.tool_calls:
                    # Вызываем инструмент (который дергает PROSPER)
                    tool_result = call_tool(tool_call, self.prosper)
                    print(f"   ✅ Результат инструмента: {tool_result}")
                    
                    # Возвращаем результат обратно в LLM
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_call.function.name,
                        "content": tool_result
                    })
            else:
                # Если вызовов нет — это финальный ответ
                print("\n🤖 Ответ агента готов.")
                return response_message.content

        return "Агент превысил лимит шагов. Возможно, произошло зацикливание."
