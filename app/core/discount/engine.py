from typing import List, Tuple, Optional
from app.core.discount.base import DiscountStrategy
from app.core.discount.strategies import FirstOrderDiscount, FreeDeliveryDiscount
from app.core.models.order import Order
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DiscountEngine:

    def __init__(self) -> None:
        self.strategies: List[DiscountStrategy] = []

    def add_strategy(self, strategy: DiscountStrategy):

        if any(s.name == strategy.name for s in self.strategies):
            logger.warning("Стратегия с таким именем уже существует")
            return self

        self.strategies.append(strategy)
        logger.info(f"Стратегия: {strategy.name} успешно добавлена")
        return self

    def add_default_strategies(self, **kwargs):
        self.strategies = [
            FirstOrderDiscount(user_order_count=kwargs.get("user_order_count", 0)),
            FreeDeliveryDiscount(threshold=kwargs.get("threshold", 1000)),
        ]

        return self

    def remove_strategy(self, strategy_name: str) -> "DiscountEngine":
        original_count = len(self.strategies)
        self.strategies = [
            strategy for strategy in self.strategies if strategy.name != strategy_name
        ]

        if len(self.strategies) < len(original_count):
            logger.info(f"Стратегия {strategy_name} успешно удалена")

        else:
            logger.warning(f"Не удалось найти стратегию {strategy_name}")

        return self

    def calculate_total_discount(
        self, order: Order
    ) -> Tuple[float, List[Tuple[str, float]]]:
        """Расчитать сумму всех приминимых скидок
        Возвращает: (общая_скидка, [(название_скидки, сумма), ...])
        """

        total_discount = 0.0
        applied_strategies = []

        sorted_strategies = sorted(
            self.strategies, key=lambda s: s.priority, reverse=True
        )

        for strategy in sorted_strategies:
            if strategy.is_applicable(order):
                discount = strategy.discount(order)
                if discount > 0:
                    total_discount += discount
                    applied_strategies.append((strategy.name, discount))
                    logger.debug(f"Applied {strategy.name}, {discount}")

        total_discount = min(total_discount, order.subtotal)

        if applied_strategies:
            logger.info(
                f"Total discount {total_discount} from {len(applied_strategies)} strategy"
            )

        return total_discount, applied_strategies

    def get_max_possible_discount(self, order: Order):

        total = 0.0

        for strategy in self.strategies:
            if strategy.is_applicable(order):
                total += strategy.discount(order)

        return min(total, order.subtotal)
