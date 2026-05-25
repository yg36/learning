import re


# =========================
# CATEGORY MAP
# =========================

CATEGORY_MAP = {

    # JACKETS
    "jacket": "jackets",
    "jackets": "jackets",
    "hoodie": "jackets",
    "hoodies": "jackets",
    "coat": "jackets",
    "coats": "jackets",
    "windbreaker": "jackets",
    "blazer": "jackets",
    "bomber": "jackets",
    "parka": "jackets",

    # SHIRTS
    "shirt": "shirts",
    "shirts": "shirts",
    "tshirt": "shirts",
    "t-shirt": "shirts",
    "tee": "shirts",
    "polo": "shirts",

    # JEANS
    "jeans": "jeans",
    "denim": "jeans",
    "cargo": "jeans",

    # SHOES
    "shoes": "shoes",
    "sneakers": "shoes",
    "boots": "shoes",
    "trainers": "shoes",
}


# =========================
# COLOR MAP
# =========================

COLOR_MAP = {
    "black": "black",
    "blue": "blue",
    "red": "red",
    "white": "white",
    "green": "green",
    "navy": "navy",
    "grey": "grey",
    "gray": "grey",
    "pink": "pink",
    "yellow": "yellow",
    "brown": "brown",
    "beige": "beige",
    "purple": "purple",
    "orange": "orange",
    "olive": "olive",
}


# =========================
# STYLE MAP
# =========================

STYLE_MAP = {

    # PREMIUM
    "premium": "premium",
    "luxury": "premium",
    "expensive": "premium",
    "high-end": "premium",
    "designer": "premium",

    # TRENDY
    "trendy": "trendy",
    "stylish": "trendy",
    "fashionable": "trendy",
    "streetwear": "trendy",
    "oversized": "trendy",

    # CASUAL
    "casual": "casual",
    "daily": "casual",
    "everyday": "casual",

    # SPORTS
    "sports": "sports",
    "sporty": "sports",
    "gym": "sports",
    "running": "sports",
    "training": "sports",

    # MINIMAL
    "minimal": "minimal",
    "simple": "minimal",
    "clean": "minimal",

    # WINTER
    "winter": "winter",
    "warm": "winter",
    "thermal": "winter",
}


# =========================
# PRICE NORMALIZER
# =========================

def normalize_price(value, has_k=False):

    value = int(value)

    if has_k:
        value *= 1000

    return value


# =========================
# INTENT EXTRACTOR
# =========================

def extract_intent(query):

    query = query.lower()

    intent = {}

    words = query.split()

    # -------------------------
    # CATEGORY
    # -------------------------

    for word in words:

        if word in CATEGORY_MAP:
            intent["category"] = CATEGORY_MAP[word]

    # -------------------------
    # COLOR
    # -------------------------

    for word in words:

        if word in COLOR_MAP:
            intent["color"] = COLOR_MAP[word]

    # -------------------------
    # STYLE
    # -------------------------

    detected_styles = []

    for word in words:

        if word in STYLE_MAP:
            detected_styles.append(STYLE_MAP[word])

    if detected_styles:
        intent["styles"] = list(set(detected_styles))

    # -------------------------
    # UNDER PRICE
    # -------------------------

    under_match = re.search(
        r'under\s+(\d+)(k)?',
        query
    )

    if under_match:

        has_k = under_match.group(2) is not None

        price = normalize_price(
            under_match.group(1),
            has_k
        )

        intent["max_price"] = price

    # -------------------------
    # ABOVE PRICE
    # -------------------------

    above_match = re.search(
        r'(above|over)\s+(\d+)(k)?',
        query
    )

    if above_match:

        has_k = above_match.group(3) is not None

        price = normalize_price(
            above_match.group(2),
            has_k
        )

        intent["min_price"] = price

    # -------------------------
    # BETWEEN PRICE
    # -------------------------

    between_match = re.search(
        r'between\s+(\d+)(k)?\s+and\s+(\d+)(k)?',
        query
    )

    if between_match:

        min_has_k = between_match.group(2) is not None
        max_has_k = between_match.group(4) is not None

        min_price = normalize_price(
            between_match.group(1),
            min_has_k
        )

        max_price = normalize_price(
            between_match.group(3),
            max_has_k
        )

        intent["min_price"] = min_price
        intent["max_price"] = max_price

    # -------------------------
    # CHEAP / AFFORDABLE
    # -------------------------

    if "cheap" in query or "affordable" in query:

        if "max_price" not in intent:
            intent["max_price"] = 3000

    # -------------------------
    # PREMIUM / LUXURY
    # -------------------------

    if "premium" in query or "luxury" in query:

        if "min_price" not in intent:
            intent["min_price"] = 5000

    return intent