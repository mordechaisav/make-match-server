import enum


class ReferenceType(str, enum.Enum):
    RABBI_TEACHER = "rabbi_teacher"
    FRIEND = "friend"
    FAMILY = "family"


class RelationType(str, enum.Enum):
    FATHER = "father"
    MOTHER = "mother"
    SIBLING = "sibling"
