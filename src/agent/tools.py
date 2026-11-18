"""Расчётные инструменты агента. Тот же файл потом переедет в репозиторий пары."""

import math


def ipr_vogel(p_res: float, p_test: float, q_test: float, p_wf: float) -> float:
    """Дебит по Вогелю, м3/сут. Давления абсолютные, атм."""

    # TODO B: проверка диапазонов
    if p_res <= 0:
        raise ValueError("Пластовое давление должно быть > 0 атм")

    if not 0 <= p_test < p_res:
        raise ValueError("Тестовое давление должно быть от 0 до p_res (не включая p_res)")

    if q_test <= 0:
        raise ValueError("Тестовый дебит должен быть > 0 м3/сут")

    if not 0 <= p_wf <= p_res:
        raise ValueError("Забойное давление должно быть от 0 до p_res")

    # Формула Вогеля
    def vogel_factor(p):
        ratio = p / p_res
        return 1 - 0.2 * ratio - 0.8 * ratio**2

    q_max = q_test / vogel_factor(p_test)
    q = q_max * vogel_factor(p_wf)

    return q


def arps_decline(q0: float, annual_decline: float, years: float) -> float:
    """Экспоненциальный спад дебита, м3/сут."""

    # TODO B: проверка диапазонов
    if q0 <= 0:
        raise ValueError("Начальный дебит должен быть > 0 м3/сут")

    if not 0 <= annual_decline <= 1:
        raise ValueError("Годовой коэффициент спада должен быть от 0 до 1")

    if years < 0:
        raise ValueError("Время не может быть отрицательным")

    # Экспоненциальная модель Арпса
    q = q0 * math.exp(-annual_decline * years)

    return q
