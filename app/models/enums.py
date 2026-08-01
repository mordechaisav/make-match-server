import enum


class ReferenceType(str, enum.Enum):
    RABBI_TEACHER = "rabbi_teacher"
    FRIEND = "friend"
    FAMILY = "family"
