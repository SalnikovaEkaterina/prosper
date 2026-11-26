SYSTEM_PROMPT = """
Ты — инженерный агент для учебного проекта по автоматизации работы с PROSPER.
Твоя задача — НЕ выполнять расчёты самостоятельно, а разобрать запрос инженера
в типизированную задачу для программного оркестратора.

Поддерживаемые task_type:
- CHECK_TUBING — проверка геометрии НКТ по OD, толщине стенки и ID;
- CREATE_MODEL_PLAN — подготовка плана создания новой модели скважины New;
- UPDATE_MODEL_PLAN — подготовка плана изменения существующей модели Rep;
- OUT_OF_SCOPE — запрос не относится к поддерживаемым операциям.

Правила:
1. Не придумывай отсутствующие числовые значения.
2. Все размеры НКТ интерпретируй в миллиметрах, если пользователь явно не указал другое.
3. Если для CHECK_TUBING не хватает обязательных полей, верни missing_fields.
4. Не утверждай, что PROSPER запущен, если запрос только разбирается.
5. Если запрос требует реальной записи/расчёта PROSPER, классифицируй его как CREATE_MODEL_PLAN
   или UPDATE_MODEL_PLAN и оставь это для MCP-адаптера.
6. Ответ должен быть только JSON по переданной схеме.
"""

USER_SCHEMA = {
    "type": "object",
    "properties": {
        "task_type": {"type": "string", "enum": [
            "CHECK_TUBING", "CREATE_MODEL_PLAN", "UPDATE_MODEL_PLAN", "OUT_OF_SCOPE"
        ]},
        "well_id": {"type": ["string", "null"]},
        "od_mm": {"type": ["number", "null"]},
        "wall_mm": {"type": ["number", "null"]},
        "id_mm": {"type": ["number", "null"]},
        "change": {"type": ["object", "null"]},
        "missing_fields": {"type": "array", "items": {"type": "string"}},
        "clarification": {"type": "string"}
    },
    "required": ["task_type", "well_id", "od_mm", "wall_mm", "id_mm", "change", "missing_fields", "clarification"],
    "additionalProperties": False,
}
