from abc import ABC, abstractmethod
from app.core.models.order import Order


class DiscountStrategy(ABC):

    @abstractmethod
    def discount(self, order: Order) -> float:
        """Расчитать сумму скидки в рублях"""
        pass

    @abstractmethod
    def is_applicable(self, order: Order) -> bool:
        """Проверить, принима ли скидка к данному заказу
        Возвращает True: если скидку можно применить
        """

    @property
    @abstractmethod
    def name(self) -> str:
        """Название скидки (для логов и отчётов)"""
        pass

    @property
    def priority(self) -> int:
        """
        Приоритет применения (чем выше число, тем раньше применяется)
        По умолчанию 0 - можно переопределить
        """
        return 0
