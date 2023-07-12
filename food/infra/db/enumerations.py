from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple, Type

import sqlalchemy as sa
from sqlalchemy.engine import Dialect


class EnumNameValues(Enum):
    """
    Override Enum's auto values generation to make them being Enum's names instead of members.
    """
    @staticmethod
    def _generate_next_value_(name: str, start: int, count: int, last_values: List[Any]) -> str:
        return name


class StrEnumNameValues(str, EnumNameValues):
    pass


class StrEnum(sa.types.TypeDecorator[Enum]):
    """SQLAlchemy TypeDecorator so that we can store enums as strings in the database.
    By default, SQLAalchemy will store `.name` in the database, but we override this logic to
    allow us to reduce the use of casting to `EnumType(value)`, and reduce the use of the
    `.value` property when using the field elsewhere.
    """
    impl = sa.String

    cache_ok = True

    def __init__(self, enumtype: Type[Enum], args: Tuple[Any], *kwargs: Dict[str, Any]) -> None:
        super().__init__(*args, **kwargs)
        self._enumtype = enumtype

    # Alembic requires that `__repr__` return a constructor for this type that can be passed into
    # `eval()`.  The default implementation for `__repr__` does not do this well for custom types.
    def __repr__(self) -> str:
        return f'StrEnum({self._enumtype.__name__})'

    def process_bind_param(self, value: Optional[Enum], dialect: Dialect) -> Optional[str]:
        return value.value if value is not None else None

    def process_result_value(self, value: Optional[str], dialect: Dialect) -> Optional[Enum]:
        return self._enumtype(value) if value is not None else None


class FoodsTypeEnum(StrEnumNameValues):
    PIZZA = auto()
    SHAWERMA = auto()
    ZINGER = auto()
    FAHETA = auto()
    BURGER = auto()


class SizeEnum(StrEnumNameValues):
    SMALL = auto()
    MEDUIM = auto()
    LARGE = auto()


class ContentsMealType(StrEnumNameValues):
    SINGLE = auto()
    MEAL = auto()


class SortOrderEnum(StrEnumNameValues):
    ASCENDING = auto()
    DESCINDING = auto()
