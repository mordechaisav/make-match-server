import enum


class ReferenceType(str, enum.Enum):
    RABBI_TEACHER = "רב/מלמד"
    FRIEND = "חבר"
    FAMILY = "משפחה"


class RelationType(str, enum.Enum):
    FATHER = "אבא"
    MOTHER = "אמא"
    SIBLING = "אח או אחות"
