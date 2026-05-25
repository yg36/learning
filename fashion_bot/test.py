from intent.spacy_extractor import extract_intent

queries = [

    "Looking for trendy black jackets under 5k",

    "Need luxury hoodies above 8k",

    "Show me sporty blue sneakers",

    "oversized streetwear jackets"
]

for q in queries:

    print("\nQUERY:", q)

    print(
        extract_intent(q)
    )