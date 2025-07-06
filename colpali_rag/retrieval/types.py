from enum import Enum


class SearchType(str, Enum):
    COLBERT = "colbert"
    HYBRID = "hybrid"
    MATRIOSKA = "matrioska"
    FUSION = "fusion"
