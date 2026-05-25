import re
import spacy

nlp = spacy.load("en_core_web_sm")


CATEGORY_MAP = {
    "sofa": "seating",
    "chair": "seating",
    "table": "coffee_table",
    "lamp": "lighting",
    "mirror": "wall_decor",
    "rug": "rug",
    "bed": "bed",
}


STYLE_MAP = {
    "minimal": "minimal",
    "modern": "modern",
    "boho": "boho",
    "rustic": "rustic",
    "luxury": "premium",
    "premium": "premium",
}


ROOM_MAP = {
    "bedroom": "bedroom",
    "living": "living_room",
    "kitchen": "kitchen",
    "office": "office",
    "study": "study_room",
}


MATERIAL_MAP = {
    "wood": "wood",
    "wooden": "wood",
    "metal": "metal",
    "glass": "glass",
    "velvet": "velvet",
}


def normalize_price(value, has_k=False):

    value = int(value)

    if has_k:
        value *= 1000

    return value


def extract_intent(query):

    doc = nlp(query.lower())

    intent = {}

    styles = []

    phrases = []

    # -------------------------
    # TOKEN EXTRACTION
    # -------------------------

    for token in doc:

        lemma = token.lemma_

        if lemma in CATEGORY_MAP:
            intent["category"] = CATEGORY_MAP[lemma]

        if lemma in MATERIAL_MAP:
            intent["material"] = MATERIAL_MAP[lemma]

        if lemma in ROOM_MAP:
            intent["room"] = ROOM_MAP[lemma]

        if lemma in STYLE_MAP:
            styles.append(STYLE_MAP[lemma])

    # -------------------------
    # PHRASE EXTRACTION
    # -------------------------

    for chunk in doc.noun_chunks:

        phrases.append(chunk.text)

    if phrases:
        intent["phrases"] = phrases

    if styles:
        intent["styles"] = list(set(styles))

    # -------------------------
    # PRICE EXTRACTION
    # -------------------------

    under_match = re.search(
        r'under\s+(\d+)(k)?',
        query.lower()
    )

    if under_match:

        has_k = under_match.group(2) is not None

        intent["max_price"] = normalize_price(
            under_match.group(1),
            has_k
        )

    return intent