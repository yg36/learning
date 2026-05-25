import csv
import random
from datetime import datetime, timedelta
from pathlib import Path


OUTPUT_PATH = Path("data/skincare_history_catalog_500rows.csv")
ROW_COUNT = 760
RANDOM_SEED = 42


PRODUCTS = [
    {
        "title": "Vitamin C Glow Serum",
        "brand": "Minimalist",
        "subcategory": "Serum",
        "product_type": "serum",
        "ingredients": ["vitamin-c", "ferulic-acid", "vitamin-e"],
        "tags": ["glow", "dullness", "antioxidant", "morning"],
        "concerns": ["dullness", "dark spots", "uneven tone"],
        "skin_types": ["normal", "oily", "combination", "dry"],
        "usage_time": "morning",
        "routine_step": "treat",
        "texture": "lightweight serum",
        "finish": "natural glow",
        "price": 699,
        "size_ml": 30,
        "spf": 0,
        "pa": "",
        "comedogenic": "low",
        "flags": ["alcohol_free", "vegan", "cruelty_free"],
    },
    {
        "title": "Barrier Repair Ceramide Cream",
        "brand": "CeraVe",
        "subcategory": "Moisturizer",
        "product_type": "moisturizer",
        "ingredients": ["ceramide", "cholesterol", "hyaluronic-acid"],
        "tags": ["barrier", "repair", "dryness", "winter"],
        "concerns": ["dryness", "barrier damage", "flaking"],
        "skin_types": ["dry", "normal", "sensitive"],
        "usage_time": "night",
        "routine_step": "moisturize",
        "texture": "rich cream",
        "finish": "dewy",
        "price": 899,
        "size_ml": 50,
        "spf": 0,
        "pa": "",
        "comedogenic": "medium",
        "flags": ["fragrance_free", "essential_oil_free", "non_comedogenic"],
    },
    {
        "title": "Oil Control Niacinamide Serum",
        "brand": "The Ordinary",
        "subcategory": "Serum",
        "product_type": "serum",
        "ingredients": ["niacinamide", "zinc", "panthenol"],
        "tags": ["oil-control", "pores", "acne", "lightweight"],
        "concerns": ["oiliness", "pores", "acne"],
        "skin_types": ["oily", "combination", "normal"],
        "usage_time": "night",
        "routine_step": "treat",
        "texture": "water serum",
        "finish": "matte",
        "price": 650,
        "size_ml": 30,
        "spf": 0,
        "pa": "",
        "comedogenic": "low",
        "flags": ["alcohol_free", "fragrance_free", "vegan", "cruelty_free"],
    },
    {
        "title": "AHA BHA Clarifying Toner",
        "brand": "COSRX",
        "subcategory": "Toner",
        "product_type": "toner",
        "ingredients": ["salicylic-acid", "glycolic-acid", "willow-bark"],
        "tags": ["exfoliation", "acne", "blackheads", "texture"],
        "concerns": ["acne", "blackheads", "texture"],
        "skin_types": ["oily", "combination", "normal"],
        "usage_time": "night",
        "routine_step": "tone",
        "texture": "watery toner",
        "finish": "fresh",
        "price": 1090,
        "size_ml": 150,
        "spf": 0,
        "pa": "",
        "comedogenic": "low",
        "flags": ["vegan", "cruelty_free"],
    },
    {
        "title": "Centella Calming Gel",
        "brand": "Purito",
        "subcategory": "Gel",
        "product_type": "moisturizer",
        "ingredients": ["centella", "madecassoside", "green-tea"],
        "tags": ["calming", "redness", "sensitive", "lightweight"],
        "concerns": ["redness", "sensitivity", "irritation"],
        "skin_types": ["sensitive", "oily", "combination", "normal"],
        "usage_time": "anytime",
        "routine_step": "moisturize",
        "texture": "gel",
        "finish": "non-sticky",
        "price": 780,
        "size_ml": 50,
        "spf": 0,
        "pa": "",
        "comedogenic": "low",
        "flags": ["alcohol_free", "fragrance_free", "essential_oil_free", "vegan"],
    },
    {
        "title": "Daily Invisible Sunscreen SPF50",
        "brand": "Beauty of Joseon",
        "subcategory": "Sunscreen",
        "product_type": "sunscreen",
        "ingredients": ["rice-extract", "probiotics", "uv-filters"],
        "tags": ["spf", "sun-protection", "summer", "no-white-cast"],
        "concerns": ["sun protection", "dark spots", "photoaging"],
        "skin_types": ["normal", "dry", "combination", "sensitive"],
        "usage_time": "morning",
        "routine_step": "protect",
        "texture": "cream lotion",
        "finish": "natural",
        "price": 1190,
        "size_ml": 50,
        "spf": 50,
        "pa": "PA++++",
        "comedogenic": "low",
        "flags": ["alcohol_free", "cruelty_free"],
    },
    {
        "title": "Matte Mineral Sunscreen SPF50",
        "brand": "Re'equil",
        "subcategory": "Sunscreen",
        "product_type": "sunscreen",
        "ingredients": ["zinc-oxide", "titanium-dioxide", "silica"],
        "tags": ["spf", "matte", "oil-control", "outdoor"],
        "concerns": ["sun protection", "oiliness", "tanning"],
        "skin_types": ["oily", "combination", "sensitive"],
        "usage_time": "morning",
        "routine_step": "protect",
        "texture": "silicone gel",
        "finish": "matte",
        "price": 780,
        "size_ml": 50,
        "spf": 50,
        "pa": "PA+++",
        "comedogenic": "low",
        "flags": ["fragrance_free", "non_comedogenic"],
    },
    {
        "title": "Gentle Oat Cleanser",
        "brand": "Simple",
        "subcategory": "Cleanser",
        "product_type": "cleanser",
        "ingredients": ["oat", "glycerin", "panthenol"],
        "tags": ["gentle", "cleanse", "barrier", "sensitive"],
        "concerns": ["sensitivity", "dryness", "barrier damage"],
        "skin_types": ["dry", "sensitive", "normal", "combination"],
        "usage_time": "anytime",
        "routine_step": "cleanse",
        "texture": "cream gel",
        "finish": "soft",
        "price": 399,
        "size_ml": 150,
        "spf": 0,
        "pa": "",
        "comedogenic": "low",
        "flags": ["alcohol_free", "fragrance_free", "vegan"],
    },
    {
        "title": "Green Tea Balancing Toner",
        "brand": "Isntree",
        "subcategory": "Toner",
        "product_type": "toner",
        "ingredients": ["green-tea", "betaine", "allantoin"],
        "tags": ["hydration", "oil-control", "calming", "pores"],
        "concerns": ["oiliness", "pores", "redness"],
        "skin_types": ["oily", "combination", "normal", "sensitive"],
        "usage_time": "anytime",
        "routine_step": "tone",
        "texture": "watery toner",
        "finish": "fresh",
        "price": 950,
        "size_ml": 200,
        "spf": 0,
        "pa": "",
        "comedogenic": "low",
        "flags": ["alcohol_free", "vegan", "cruelty_free"],
    },
    {
        "title": "Retinol Renewal Night Serum",
        "brand": "Olay",
        "subcategory": "Serum",
        "product_type": "serum",
        "ingredients": ["retinol", "niacinamide", "peptide"],
        "tags": ["anti-aging", "fine-lines", "night", "texture"],
        "concerns": ["fine lines", "texture", "photoaging"],
        "skin_types": ["normal", "dry", "combination"],
        "usage_time": "night",
        "routine_step": "treat",
        "texture": "silky serum",
        "finish": "smooth",
        "price": 1450,
        "size_ml": 30,
        "spf": 0,
        "pa": "",
        "comedogenic": "medium",
        "flags": ["fragrance_free"],
    },
    {
        "title": "Peptide Firming Moisturizer",
        "brand": "The Inkey List",
        "subcategory": "Moisturizer",
        "product_type": "moisturizer",
        "ingredients": ["peptide", "squalane", "glycerin"],
        "tags": ["firming", "hydration", "anti-aging", "barrier"],
        "concerns": ["fine lines", "dryness", "barrier damage"],
        "skin_types": ["dry", "normal", "combination"],
        "usage_time": "night",
        "routine_step": "moisturize",
        "texture": "cream",
        "finish": "plump",
        "price": 1250,
        "size_ml": 50,
        "spf": 0,
        "pa": "",
        "comedogenic": "medium",
        "flags": ["cruelty_free"],
    },
    {
        "title": "Azelaic Acid Spot Corrector",
        "brand": "Paula's Choice",
        "subcategory": "Treatment",
        "product_type": "treatment",
        "ingredients": ["azelaic-acid", "licorice", "salicylic-acid"],
        "tags": ["dark-spots", "redness", "acne", "brightening"],
        "concerns": ["dark spots", "acne", "redness"],
        "skin_types": ["oily", "combination", "normal", "sensitive"],
        "usage_time": "night",
        "routine_step": "treat",
        "texture": "cream treatment",
        "finish": "natural",
        "price": 1590,
        "size_ml": 30,
        "spf": 0,
        "pa": "",
        "comedogenic": "low",
        "flags": ["fragrance_free", "non_comedogenic", "cruelty_free"],
    },
    {
        "title": "Snail Mucin Essence",
        "brand": "COSRX",
        "subcategory": "Essence",
        "product_type": "essence",
        "ingredients": ["snail-mucin", "hyaluronic-acid", "allantoin"],
        "tags": ["hydration", "repair", "glow", "kbeauty"],
        "concerns": ["dryness", "barrier damage", "dullness"],
        "skin_types": ["dry", "normal", "combination", "sensitive"],
        "usage_time": "anytime",
        "routine_step": "treat",
        "texture": "essence",
        "finish": "dewy",
        "price": 1350,
        "size_ml": 100,
        "spf": 0,
        "pa": "",
        "comedogenic": "low",
        "flags": ["alcohol_free"],
    },
    {
        "title": "Hyaluronic Acid Water Gel",
        "brand": "Neutrogena",
        "subcategory": "Gel",
        "product_type": "moisturizer",
        "ingredients": ["hyaluronic-acid", "glycerin", "olive-extract"],
        "tags": ["hydration", "lightweight", "summer", "plump"],
        "concerns": ["dryness", "dehydration", "dullness"],
        "skin_types": ["oily", "combination", "normal", "dry"],
        "usage_time": "anytime",
        "routine_step": "moisturize",
        "texture": "water gel",
        "finish": "fresh",
        "price": 720,
        "size_ml": 50,
        "spf": 0,
        "pa": "",
        "comedogenic": "low",
        "flags": ["non_comedogenic"],
    },
    {
        "title": "Rice Brightening Face Wash",
        "brand": "The Face Shop",
        "subcategory": "Cleanser",
        "product_type": "cleanser",
        "ingredients": ["rice-extract", "glycerin", "amino-acids"],
        "tags": ["cleanse", "brightening", "glow", "daily"],
        "concerns": ["dullness", "uneven tone", "oiliness"],
        "skin_types": ["normal", "combination", "oily"],
        "usage_time": "anytime",
        "routine_step": "cleanse",
        "texture": "foaming cream",
        "finish": "clean",
        "price": 590,
        "size_ml": 150,
        "spf": 0,
        "pa": "",
        "comedogenic": "low",
        "flags": ["cruelty_free"],
    },
    {
        "title": "Cica Barrier Sleeping Mask",
        "brand": "Laneige",
        "subcategory": "Mask",
        "product_type": "mask",
        "ingredients": ["centella", "squalane", "ceramide"],
        "tags": ["sleeping-mask", "barrier", "repair", "redness"],
        "concerns": ["barrier damage", "redness", "dryness"],
        "skin_types": ["dry", "sensitive", "normal", "combination"],
        "usage_time": "night",
        "routine_step": "mask",
        "texture": "balm gel",
        "finish": "comfort",
        "price": 1690,
        "size_ml": 60,
        "spf": 0,
        "pa": "",
        "comedogenic": "medium",
        "flags": ["alcohol_free"],
    },
    {
        "title": "Lip Barrier Balm SPF30",
        "brand": "Sebamed",
        "subcategory": "Lip Care",
        "product_type": "lip balm",
        "ingredients": ["shea-butter", "vitamin-e", "uv-filters"],
        "tags": ["lip-care", "spf", "barrier", "travel"],
        "concerns": ["sun protection", "dryness", "chapped lips"],
        "skin_types": ["all", "sensitive", "dry", "normal"],
        "usage_time": "morning",
        "routine_step": "protect",
        "texture": "balm",
        "finish": "soft sheen",
        "price": 350,
        "size_ml": 10,
        "spf": 30,
        "pa": "PA++",
        "comedogenic": "medium",
        "flags": ["alcohol_free"],
    },
    {
        "title": "Mandelic Acid Beginner Exfoliant",
        "brand": "By Wishtrend",
        "subcategory": "Exfoliant",
        "product_type": "exfoliant",
        "ingredients": ["mandelic-acid", "panthenol", "beta-glucan"],
        "tags": ["beginner", "exfoliation", "texture", "gentle"],
        "concerns": ["texture", "dullness", "blackheads"],
        "skin_types": ["sensitive", "normal", "dry", "combination"],
        "usage_time": "night",
        "routine_step": "treat",
        "texture": "watery liquid",
        "finish": "fresh",
        "price": 1280,
        "size_ml": 120,
        "spf": 0,
        "pa": "",
        "comedogenic": "low",
        "flags": ["alcohol_free", "vegan"],
    },
    {
        "title": "Squalane Nourishing Face Oil",
        "brand": "Inde Wild",
        "subcategory": "Face Oil",
        "product_type": "face oil",
        "ingredients": ["squalane", "rosehip", "vitamin-e"],
        "tags": ["nourishing", "dryness", "glow", "winter"],
        "concerns": ["dryness", "dullness", "barrier damage"],
        "skin_types": ["dry", "normal"],
        "usage_time": "night",
        "routine_step": "seal",
        "texture": "light oil",
        "finish": "dewy",
        "price": 990,
        "size_ml": 30,
        "spf": 0,
        "pa": "",
        "comedogenic": "medium",
        "flags": ["vegan", "cruelty_free"],
    },
    {
        "title": "Tea Tree Acne Patch",
        "brand": "Derma Co",
        "subcategory": "Treatment",
        "product_type": "acne patch",
        "ingredients": ["hydrocolloid", "tea-tree", "salicylic-acid"],
        "tags": ["acne", "spot-care", "quick-fix", "night"],
        "concerns": ["acne", "whiteheads", "inflammation"],
        "skin_types": ["oily", "combination", "normal"],
        "usage_time": "night",
        "routine_step": "treat",
        "texture": "patch",
        "finish": "invisible",
        "price": 299,
        "size_ml": 12,
        "spf": 0,
        "pa": "",
        "comedogenic": "low",
        "flags": ["fragrance_free", "non_comedogenic"],
    },
    {
        "title": "Aloe Recovery Mist",
        "brand": "Plum",
        "subcategory": "Mist",
        "product_type": "mist",
        "ingredients": ["aloe", "cucumber", "green-tea"],
        "tags": ["calming", "travel", "hydration", "summer"],
        "concerns": ["dehydration", "redness", "sun irritation"],
        "skin_types": ["all", "sensitive", "oily", "combination", "dry"],
        "usage_time": "anytime",
        "routine_step": "refresh",
        "texture": "mist",
        "finish": "fresh",
        "price": 420,
        "size_ml": 100,
        "spf": 0,
        "pa": "",
        "comedogenic": "low",
        "flags": ["alcohol_free", "vegan", "cruelty_free"],
    },
    {
        "title": "Kojic Acid Dark Spot Cream",
        "brand": "Deconstruct",
        "subcategory": "Treatment",
        "product_type": "treatment",
        "ingredients": ["kojic-acid", "alpha-arbutin", "niacinamide"],
        "tags": ["dark-spots", "pigmentation", "brightening", "night"],
        "concerns": ["dark spots", "pigmentation", "uneven tone"],
        "skin_types": ["normal", "oily", "combination", "dry"],
        "usage_time": "night",
        "routine_step": "treat",
        "texture": "cream",
        "finish": "natural",
        "price": 799,
        "size_ml": 30,
        "spf": 0,
        "pa": "",
        "comedogenic": "low",
        "flags": ["fragrance_free", "vegan", "cruelty_free"],
    },
    {
        "title": "Pore Smoothing Clay Mask",
        "brand": "Innisfree",
        "subcategory": "Mask",
        "product_type": "mask",
        "ingredients": ["kaolin", "volcanic-ash", "green-tea"],
        "tags": ["pores", "oil-control", "mask", "weekly"],
        "concerns": ["pores", "oiliness", "blackheads"],
        "skin_types": ["oily", "combination", "normal"],
        "usage_time": "night",
        "routine_step": "mask",
        "texture": "clay",
        "finish": "matte",
        "price": 850,
        "size_ml": 100,
        "spf": 0,
        "pa": "",
        "comedogenic": "low",
        "flags": ["vegan"],
    },
]


PERSONAS = [
    {
        "skin_type": "oily",
        "concerns": ["acne", "pores", "oiliness"],
        "favorite_ingredients": ["niacinamide", "salicylic-acid", "green-tea"],
        "disliked_ingredients": ["heavy-oils", "coconut-oil"],
        "preferred_types": ["serum", "cleanser", "sunscreen", "toner"],
    },
    {
        "skin_type": "dry",
        "concerns": ["dryness", "barrier damage", "dullness"],
        "favorite_ingredients": ["ceramide", "hyaluronic-acid", "squalane"],
        "disliked_ingredients": ["alcohol", "strong-fragrance"],
        "preferred_types": ["moisturizer", "essence", "face oil", "mask"],
    },
    {
        "skin_type": "sensitive",
        "concerns": ["redness", "sensitivity", "irritation"],
        "favorite_ingredients": ["centella", "oat", "panthenol"],
        "disliked_ingredients": ["fragrance", "essential-oils", "retinol"],
        "preferred_types": ["cleanser", "moisturizer", "mist", "sunscreen"],
    },
    {
        "skin_type": "combination",
        "concerns": ["dullness", "pores", "uneven tone"],
        "favorite_ingredients": ["vitamin-c", "niacinamide", "rice-extract"],
        "disliked_ingredients": ["mineral-oil", "heavy-oils"],
        "preferred_types": ["serum", "toner", "sunscreen", "moisturizer"],
    },
    {
        "skin_type": "normal",
        "concerns": ["fine lines", "sun protection", "texture"],
        "favorite_ingredients": ["peptide", "retinol", "vitamin-c"],
        "disliked_ingredients": ["strong-fragrance"],
        "preferred_types": ["serum", "sunscreen", "exfoliant", "moisturizer"],
    },
]


QUERIES = [
    "best {product_type} for {concern}",
    "{ingredient} product for {skin_type} skin",
    "skincare for {concern} under {budget}",
    "lightweight {product_type} for daily routine",
    "night skincare for {concern}",
    "morning skincare with {ingredient}",
    "sensitive skin {product_type} without fragrance",
    "what should I use after clicking {product_type}",
]


COUNTRIES = ["India"]
STATES = ["Delhi", "Haryana", "Karnataka", "Maharashtra", "Telangana", "West Bengal"]
CITIES = ["Delhi", "Gurgaon", "Bangalore", "Mumbai", "Hyderabad", "Kolkata", "Pune", "Chandigarh"]
PROFESSIONS = ["Intern", "Student", "Engineer", "Dancer", "Designer", "Manager", "Creator"]
GENDERS = ["Female", "Male", "Non-binary"]
DEVICES = [("Mobile", "Android"), ("Mobile", "iOS"), ("Laptop", "Windows"), ("Laptop", "macOS"), ("Tablet", "Android")]
BROWSERS = ["Chrome", "Edge", "Safari", "Firefox"]
NETWORKS = ["WiFi", "4G", "5G"]
WEATHER = [("hot", 37, 46), ("humid", 32, 78), ("cold", 15, 42), ("normal", 27, 55), ("rainy", 25, 84)]
TIMES = ["morning", "afternoon", "evening", "night"]
LAYOUTS = ["grid", "carousel", "routine_stack", "comparison", "list"]
THEMES = ["clean", "clinical", "fresh", "minimal", "premium"]
MOODS = ["focused", "curious", "rushed", "relaxed", "confused"]
ENGAGEMENT = ["low", "medium", "high"]


FIELDNAMES = [
    "user_id",
    "session_id",
    "event_id",
    "anonymous",
    "user_age",
    "user_gender",
    "user_profession",
    "skin_type",
    "skin_tone",
    "sensitivity_level",
    "acne_prone",
    "fragrance_preference",
    "pregnancy_safe_required",
    "vegan_preference",
    "cruelty_free_preference",
    "dermatologist_visit_history",
    "device_type",
    "device_os",
    "browser",
    "app_version",
    "network_type",
    "ip_location_country",
    "ip_location_state",
    "ip_location_city",
    "weather_condition",
    "temperature",
    "humidity",
    "uv_index",
    "pollution_aqi",
    "season",
    "day_of_week",
    "time_of_day",
    "festival_or_event",
    "routine_stage",
    "query",
    "normalized_query",
    "query_language",
    "query_length",
    "semantic_category",
    "intent",
    "desired_product_type",
    "requested_ingredient",
    "avoided_ingredients",
    "skin_concerns",
    "budget_min",
    "budget_max",
    "preferred_category",
    "user_mood",
    "engagement_level",
    "previous_queries",
    "previous_hovered_product_ids",
    "previous_hovered_product_titles",
    "previous_hovered_categories",
    "previous_hovered_tags",
    "hover_count_7d",
    "hover_count_30d",
    "previous_clicked_product_ids",
    "previous_clicked_product_titles",
    "previous_clicked_tags",
    "click_count_7d",
    "click_count_30d",
    "previous_added_to_cart_ids",
    "cart_count_30d",
    "previous_purchased_product_ids",
    "purchase_count_90d",
    "recently_viewed_brands",
    "favorite_brands",
    "favorite_ingredients",
    "disliked_ingredients",
    "returned_product_ids",
    "last_interaction_type",
    "last_interaction_minutes_ago",
    "average_dwell_time_30d",
    "average_scroll_depth_30d",
    "repeat_purchase_interval_days",
    "price_sensitivity",
    "brand_loyalty_score",
    "ingredient_affinity_score",
    "concern_affinity_score",
    "category_affinity_score",
    "history_affinity_score",
    "query_match_score",
    "collaborative_signal_score",
    "product_id",
    "product_title",
    "product_brand",
    "product_category",
    "product_subcategory",
    "product_type",
    "key_ingredients",
    "ingredient_tags",
    "product_tags",
    "product_price",
    "size_ml",
    "discount_percentage",
    "price_tier",
    "spf_rating",
    "pa_rating",
    "comedogenic_risk",
    "alcohol_free",
    "fragrance_free",
    "essential_oil_free",
    "non_comedogenic",
    "pregnancy_safe",
    "vegan",
    "cruelty_free",
    "suitable_skin_types",
    "target_concerns",
    "usage_time",
    "routine_step",
    "routine_stage_order",
    "am_routine_fit",
    "pm_routine_fit",
    "active_strength_level",
    "active_concentration_percent",
    "retinol_percentage",
    "niacinamide_percentage",
    "salicylic_acid_percentage",
    "vitamin_c_percentage",
    "minimum_recommended_age",
    "max_usage_per_week",
    "recommended_frequency",
    "sunscreen_required_after_use",
    "photosensitivity_risk",
    "patch_test_required",
    "avoid_with_ingredients",
    "compatible_with_steps",
    "contraindications",
    "pregnancy_safety_note",
    "sensitive_skin_caution",
    "routine_compatibility_tags",
    "semantic_document",
    "content_embedding_text",
    "ingredient_complexity_score",
    "barrier_support_score",
    "acne_safe_score",
    "oily_skin_fit_score",
    "dry_skin_fit_score",
    "sensitive_skin_fit_score",
    "texture",
    "finish",
    "inventory_status",
    "launch_year",
    "popularity_score",
    "rating",
    "review_count",
    "return_rate",
    "reorder_rate",
    "margin_score",
    "availability_score",
    "clinical_claim_strength",
    "layout_type",
    "theme",
    "recommendation_algorithm",
    "recommendation_score",
    "personalization_score",
    "diversity_score",
    "novelty_score",
    "rank_position",
    "redirect_url",
    "shown",
    "hovered",
    "clicked",
    "purchased",
    "added_to_cart",
    "wishlisted",
    "shared",
    "watch_time_seconds",
    "hover_time_seconds",
    "scroll_depth",
    "dwell_time_seconds",
    "feedback_rating",
    "conversion",
    "negative_feedback",
    "recommendation_reason",
    "next_best_action",
    "created_at",
]


def join(values):
    return "|".join(str(value) for value in values if str(value))


def price_tier(price):
    if price < 500:
        return "budget"
    if price < 1000:
        return "mid"
    if price < 1500:
        return "premium"
    return "luxury"


def bool_int(condition):
    return 1 if condition else 0


def routine_stage_order(step):
    order = {
        "cleanse": 1,
        "tone": 2,
        "treat": 3,
        "mask": 3,
        "moisturize": 4,
        "seal": 5,
        "protect": 6,
        "refresh": 7,
    }
    return order.get(step, 9)


def active_profile(product):
    ingredients = set(product["ingredients"])
    product_type = product["product_type"]

    concentration = 0.0
    level = "none"
    max_usage = 14
    frequency = "daily"
    minimum_age = 12
    photosensitivity = "low"
    sunscreen_required = False
    patch_test = False
    avoid_with = []

    if "retinol" in ingredients:
        concentration = 0.3
        level = "advanced"
        max_usage = 3
        frequency = "2-3 nights/week"
        minimum_age = 20
        photosensitivity = "high"
        sunscreen_required = True
        patch_test = True
        avoid_with = ["aha", "bha", "benzoyl-peroxide", "strong-vitamin-c"]
    elif "salicylic-acid" in ingredients or "glycolic-acid" in ingredients:
        concentration = 2.0 if "salicylic-acid" in ingredients else 5.0
        level = "intermediate"
        max_usage = 3
        frequency = "2-3 nights/week"
        minimum_age = 16
        photosensitivity = "medium"
        sunscreen_required = True
        patch_test = True
        avoid_with = ["retinol", "strong-exfoliants"]
    elif "mandelic-acid" in ingredients:
        concentration = 5.0
        level = "beginner"
        max_usage = 2
        frequency = "1-2 nights/week"
        minimum_age = 16
        photosensitivity = "medium"
        sunscreen_required = True
        patch_test = True
        avoid_with = ["retinol", "strong-exfoliants"]
    elif "vitamin-c" in ingredients:
        concentration = 10.0
        level = "intermediate"
        max_usage = 7
        frequency = "daily morning"
        minimum_age = 18
        photosensitivity = "low"
        sunscreen_required = True
        patch_test = True
        avoid_with = ["retinol same routine"]
    elif "niacinamide" in ingredients:
        concentration = 5.0
        level = "beginner"
        max_usage = 14
        frequency = "daily"
        minimum_age = 13
    elif product_type in {"mask", "face oil"}:
        level = "support"
        max_usage = 3
        frequency = "1-3 times/week"

    return {
        "active_strength_level": level,
        "active_concentration_percent": concentration,
        "retinol_percentage": concentration if "retinol" in ingredients else 0,
        "niacinamide_percentage": 5.0 if "niacinamide" in ingredients else 0,
        "salicylic_acid_percentage": 2.0 if "salicylic-acid" in ingredients else 0,
        "vitamin_c_percentage": 10.0 if "vitamin-c" in ingredients else 0,
        "minimum_recommended_age": minimum_age,
        "max_usage_per_week": max_usage,
        "recommended_frequency": frequency,
        "sunscreen_required_after_use": bool_int(sunscreen_required),
        "photosensitivity_risk": photosensitivity,
        "patch_test_required": bool_int(patch_test),
        "avoid_with_ingredients": join(avoid_with),
    }


def compatible_steps(product):
    step = product["routine_step"]
    if step == "cleanse":
        return ["tone", "treat", "moisturize"]
    if step == "tone":
        return ["treat", "moisturize", "protect"]
    if step == "treat":
        return ["moisturize", "protect"]
    if step == "moisturize":
        return ["protect", "seal"]
    if step == "seal":
        return ["moisturize"]
    if step == "protect":
        return ["cleanse"]
    return ["moisturize"]


def contraindications(product):
    ingredients = set(product["ingredients"])
    notes = []
    if "retinol" in ingredients:
        notes.extend(["pregnancy", "breastfeeding", "under-20-without-guidance", "same-night-strong-acids"])
    if "salicylic-acid" in ingredients:
        notes.extend(["pregnancy-caution", "aspirin-allergy", "over-exfoliation"])
    if "glycolic-acid" in ingredients:
        notes.extend(["over-exfoliation", "damaged-barrier"])
    if "fragrance" in product["tags"]:
        notes.append("fragrance-sensitive")
    return notes


def fit_score(product, target):
    if target in product["skin_types"] or "all" in product["skin_types"]:
        return 0.9
    if target == "sensitive" and "fragrance_free" in product["flags"]:
        return 0.75
    if target == "oily" and {"oil-control", "matte", "lightweight"} & set(product["tags"]):
        return 0.8
    if target == "dry" and {"hydration", "barrier", "nourishing"} & set(product["tags"]):
        return 0.8
    return 0.35


def compatibility_score(product, persona):
    score = 0.2

    if persona["skin_type"] in product["skin_types"] or "all" in product["skin_types"]:
        score += 0.22

    concern_overlap = set(persona["concerns"]) & set(product["concerns"])
    ingredient_overlap = set(persona["favorite_ingredients"]) & set(product["ingredients"])

    score += 0.08 * len(concern_overlap)
    score += 0.07 * len(ingredient_overlap)

    if product["product_type"] in persona["preferred_types"]:
        score += 0.13

    disliked_overlap = set(persona["disliked_ingredients"]) & set(product["ingredients"] + product["tags"])
    score -= 0.12 * len(disliked_overlap)

    return max(0.05, min(score, 0.99))


def make_query(product, persona, budget, rng):
    concern = rng.choice(persona["concerns"])
    ingredient = rng.choice(product["ingredients"])
    template = rng.choice(QUERIES)
    return template.format(
        product_type=product["product_type"],
        concern=concern,
        ingredient=ingredient.replace("-", " "),
        skin_type=persona["skin_type"],
        budget=budget,
    )


def make_history(product_pool, persona, rng):
    related = [
        product
        for product in product_pool
        if (
            persona["skin_type"] in product["skin_types"]
            or bool(set(persona["concerns"]) & set(product["concerns"]))
            or product["product_type"] in persona["preferred_types"]
        )
    ]
    rng.shuffle(related)
    hovered = related[: rng.randint(2, 5)]
    clicked = related[: rng.randint(1, min(3, len(related)))]
    carts = clicked[: rng.randint(0, min(2, len(clicked)))]
    purchases = clicked[: rng.randint(0, 1)]
    returned = rng.sample(purchases, k=1) if purchases and rng.random() < 0.12 else []

    previous_queries = [
        f"{rng.choice(persona['favorite_ingredients']).replace('-', ' ')} for {rng.choice(persona['concerns'])}",
        f"{rng.choice(persona['skin_type'].split())} skin {rng.choice(persona['preferred_types'])}",
        f"skincare for {rng.choice(persona['concerns'])}",
    ]

    return {
        "previous_queries": previous_queries,
        "hovered": hovered,
        "clicked": clicked,
        "carts": carts,
        "purchases": purchases,
        "returned": returned,
    }


def event_flags(score, rng):
    shown = 1
    hovered = bool_int(rng.random() < min(0.9, 0.25 + score * 0.65))
    clicked = bool_int(rng.random() < min(0.75, 0.08 + score * 0.55))
    added_to_cart = bool_int(clicked and rng.random() < min(0.62, 0.1 + score * 0.42))
    purchased = bool_int(added_to_cart and rng.random() < min(0.5, 0.08 + score * 0.32))
    wishlisted = bool_int(rng.random() < min(0.45, 0.05 + score * 0.25))
    shared = bool_int(rng.random() < min(0.25, 0.02 + score * 0.12))
    negative = bool_int(rng.random() < max(0.01, 0.12 - score * 0.1))
    conversion = bool_int(purchased or added_to_cart)
    return shown, hovered, clicked, added_to_cart, purchased, wishlisted, shared, negative, conversion


def generate_rows(row_count=ROW_COUNT, seed=RANDOM_SEED):
    rng = random.Random(seed)
    base_date = datetime(2026, 5, 21, 9, 0, 0)

    rows = []
    for idx in range(1, row_count + 1):
        persona = rng.choice(PERSONAS)
        product = rng.choice(PRODUCTS)
        history = make_history(PRODUCTS, persona, rng)
        weather, base_temp, base_humidity = rng.choice(WEATHER)
        time_of_day = rng.choice(TIMES)
        device_type, device_os = rng.choice(DEVICES)
        budget_max = rng.choice([500, 800, 1000, 1500, 2000, 2500])
        budget_min = rng.choice([0, 200, 300, 500])
        query = make_query(product, persona, budget_max, rng)
        score = compatibility_score(product, persona)

        history_titles = " ".join(item["title"].lower() for item in history["hovered"] + history["clicked"])
        product_terms = set(product["tags"] + product["ingredients"] + product["concerns"] + [product["product_type"]])
        history_terms = set(history_titles.replace("-", " ").split())
        raw_history_overlap = len(product_terms & history_terms)
        history_affinity = min(0.99, score + raw_history_overlap * 0.03 + rng.uniform(-0.05, 0.05))

        query_tokens = set(query.lower().replace("-", " ").split())
        query_match = min(0.99, 0.2 + len(query_tokens & set(" ".join(product_terms).replace("-", " ").split())) * 0.09)
        ingredient_affinity = min(0.99, 0.15 + len(set(product["ingredients"]) & set(persona["favorite_ingredients"])) * 0.22 + rng.uniform(0, 0.1))
        concern_affinity = min(0.99, 0.15 + len(set(product["concerns"]) & set(persona["concerns"])) * 0.19 + rng.uniform(0, 0.1))
        category_affinity = min(0.99, 0.25 + (0.35 if product["product_type"] in persona["preferred_types"] else 0) + rng.uniform(0, 0.2))
        collaborative = min(0.99, 0.25 + rng.random() * 0.55 + score * 0.2)
        personalization = round((history_affinity + ingredient_affinity + concern_affinity + category_affinity) / 4, 3)
        recommendation_score = round(
            min(0.99, 0.18 + score * 0.35 + history_affinity * 0.22 + query_match * 0.15 + collaborative * 0.1),
            3,
        )
        rank_position = max(1, int((1 - recommendation_score) * 20) + rng.randint(1, 4))

        shown, hovered, clicked, added_to_cart, purchased, wishlisted, shared, negative, conversion = event_flags(score, rng)

        hover_count_7d = len(history["hovered"]) + rng.randint(0, 4)
        click_count_7d = len(history["clicked"]) + rng.randint(0, 3)
        product_id = f"SK{1000 + (idx % 97):04d}"

        flags = set(product["flags"])
        active = active_profile(product)
        contraindication_terms = contraindications(product)
        semantic_document = " ".join(
            [
                product["title"],
                product["brand"],
                product["product_type"],
                product["subcategory"],
                join(product["ingredients"]),
                join(product["tags"]),
                join(product["concerns"]),
                join(product["skin_types"]),
                product["usage_time"],
                product["routine_step"],
                active["active_strength_level"],
            ]
        )
        row = {
            "user_id": f"U{rng.randint(100, 999):03d}",
            "session_id": f"S{rng.randint(10000, 99999)}",
            "event_id": f"E{idx:05d}",
            "anonymous": bool_int(rng.random() < 0.32),
            "user_age": rng.randint(18, 45),
            "user_gender": rng.choice(GENDERS),
            "user_profession": rng.choice(PROFESSIONS),
            "skin_type": persona["skin_type"],
            "skin_tone": rng.choice(["fair", "light", "medium", "tan", "deep"]),
            "sensitivity_level": rng.choice(["low", "medium", "high"]) if persona["skin_type"] != "sensitive" else "high",
            "acne_prone": bool_int("acne" in persona["concerns"] or rng.random() < 0.24),
            "fragrance_preference": "avoid" if "fragrance" in join(persona["disliked_ingredients"]) else rng.choice(["neutral", "mild", "avoid"]),
            "pregnancy_safe_required": bool_int(rng.random() < 0.08),
            "vegan_preference": bool_int(rng.random() < 0.28),
            "cruelty_free_preference": bool_int(rng.random() < 0.34),
            "dermatologist_visit_history": rng.choice(["never", "past_year", "past_month", "ongoing"]),
            "device_type": device_type,
            "device_os": device_os,
            "browser": rng.choice(BROWSERS),
            "app_version": f"{rng.randint(2, 4)}.{rng.randint(0, 9)}.{rng.randint(0, 9)}",
            "network_type": rng.choice(NETWORKS),
            "ip_location_country": rng.choice(COUNTRIES),
            "ip_location_state": rng.choice(STATES),
            "ip_location_city": rng.choice(CITIES),
            "weather_condition": weather,
            "temperature": base_temp + rng.randint(-3, 3),
            "humidity": max(20, min(95, base_humidity + rng.randint(-8, 8))),
            "uv_index": rng.randint(1, 11),
            "pollution_aqi": rng.randint(35, 260),
            "season": rng.choice(["summer", "monsoon", "winter", "spring"]),
            "day_of_week": rng.choice(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]),
            "time_of_day": time_of_day,
            "festival_or_event": rng.choice(["none", "wedding season", "travel", "office week", "college fest", "dance performance"]),
            "routine_stage": product["routine_step"],
            "query": query,
            "normalized_query": query.lower(),
            "query_language": "English",
            "query_length": len(query),
            "semantic_category": "skincare",
            "intent": rng.choice(["search", "recommendation", "routine_building", "comparison", "repurchase"]),
            "desired_product_type": product["product_type"],
            "requested_ingredient": rng.choice(product["ingredients"]),
            "avoided_ingredients": join(persona["disliked_ingredients"]),
            "skin_concerns": join(persona["concerns"]),
            "budget_min": budget_min,
            "budget_max": budget_max,
            "preferred_category": "skincare",
            "user_mood": rng.choice(MOODS),
            "engagement_level": rng.choice(ENGAGEMENT),
            "previous_queries": join(history["previous_queries"]),
            "previous_hovered_product_ids": join(f"SKH{rng.randint(100, 999)}" for _ in history["hovered"]),
            "previous_hovered_product_titles": join(item["title"] for item in history["hovered"]),
            "previous_hovered_categories": "skincare",
            "previous_hovered_tags": join(sorted({tag for item in history["hovered"] for tag in item["tags"] + item["ingredients"]})),
            "hover_count_7d": hover_count_7d,
            "hover_count_30d": hover_count_7d + rng.randint(2, 14),
            "previous_clicked_product_ids": join(f"SKC{rng.randint(100, 999)}" for _ in history["clicked"]),
            "previous_clicked_product_titles": join(item["title"] for item in history["clicked"]),
            "previous_clicked_tags": join(sorted({tag for item in history["clicked"] for tag in item["tags"] + item["ingredients"]})),
            "click_count_7d": click_count_7d,
            "click_count_30d": click_count_7d + rng.randint(1, 9),
            "previous_added_to_cart_ids": join(f"SKA{rng.randint(100, 999)}" for _ in history["carts"]),
            "cart_count_30d": len(history["carts"]) + rng.randint(0, 4),
            "previous_purchased_product_ids": join(f"SKP{rng.randint(100, 999)}" for _ in history["purchases"]),
            "purchase_count_90d": len(history["purchases"]) + rng.randint(0, 3),
            "recently_viewed_brands": join(sorted({item["brand"] for item in history["hovered"]})),
            "favorite_brands": join(sorted({item["brand"] for item in history["clicked"]})),
            "favorite_ingredients": join(persona["favorite_ingredients"]),
            "disliked_ingredients": join(persona["disliked_ingredients"]),
            "returned_product_ids": join(f"SKR{rng.randint(100, 999)}" for _ in history["returned"]),
            "last_interaction_type": rng.choice(["hover", "click", "cart", "purchase", "query"]),
            "last_interaction_minutes_ago": rng.randint(3, 1440),
            "average_dwell_time_30d": rng.randint(18, 220),
            "average_scroll_depth_30d": rng.randint(25, 100),
            "repeat_purchase_interval_days": rng.randint(21, 120),
            "price_sensitivity": rng.choice(["low", "medium", "high"]),
            "brand_loyalty_score": round(rng.uniform(0.15, 0.95), 3),
            "ingredient_affinity_score": round(ingredient_affinity, 3),
            "concern_affinity_score": round(concern_affinity, 3),
            "category_affinity_score": round(category_affinity, 3),
            "history_affinity_score": round(history_affinity, 3),
            "query_match_score": round(query_match, 3),
            "collaborative_signal_score": round(collaborative, 3),
            "product_id": product_id,
            "product_title": product["title"],
            "product_brand": product["brand"],
            "product_category": "skincare",
            "product_subcategory": product["subcategory"],
            "product_type": product["product_type"],
            "key_ingredients": join(product["ingredients"]),
            "ingredient_tags": join(product["ingredients"]),
            "product_tags": join(product["tags"] + product["ingredients"] + product["concerns"]),
            "product_price": product["price"],
            "size_ml": product["size_ml"],
            "discount_percentage": rng.randint(0, 35),
            "price_tier": price_tier(product["price"]),
            "spf_rating": product["spf"],
            "pa_rating": product["pa"],
            "comedogenic_risk": product["comedogenic"],
            "alcohol_free": bool_int("alcohol_free" in flags),
            "fragrance_free": bool_int("fragrance_free" in flags),
            "essential_oil_free": bool_int("essential_oil_free" in flags),
            "non_comedogenic": bool_int("non_comedogenic" in flags),
            "pregnancy_safe": bool_int("retinol" not in product["ingredients"] and "salicylic-acid" not in product["ingredients"]),
            "vegan": bool_int("vegan" in flags),
            "cruelty_free": bool_int("cruelty_free" in flags),
            "suitable_skin_types": join(product["skin_types"]),
            "target_concerns": join(product["concerns"]),
            "usage_time": product["usage_time"],
            "routine_step": product["routine_step"],
            "routine_stage_order": routine_stage_order(product["routine_step"]),
            "am_routine_fit": bool_int(product["usage_time"] in {"morning", "anytime"} or product["routine_step"] == "protect"),
            "pm_routine_fit": bool_int(product["usage_time"] in {"night", "anytime"} and product["routine_step"] != "protect"),
            "active_strength_level": active["active_strength_level"],
            "active_concentration_percent": active["active_concentration_percent"],
            "retinol_percentage": active["retinol_percentage"],
            "niacinamide_percentage": active["niacinamide_percentage"],
            "salicylic_acid_percentage": active["salicylic_acid_percentage"],
            "vitamin_c_percentage": active["vitamin_c_percentage"],
            "minimum_recommended_age": active["minimum_recommended_age"],
            "max_usage_per_week": active["max_usage_per_week"],
            "recommended_frequency": active["recommended_frequency"],
            "sunscreen_required_after_use": active["sunscreen_required_after_use"],
            "photosensitivity_risk": active["photosensitivity_risk"],
            "patch_test_required": active["patch_test_required"],
            "avoid_with_ingredients": active["avoid_with_ingredients"],
            "compatible_with_steps": join(compatible_steps(product)),
            "contraindications": join(contraindication_terms),
            "pregnancy_safety_note": "avoid" if "pregnancy" in contraindication_terms or "pregnancy-caution" in contraindication_terms else "generally compatible",
            "sensitive_skin_caution": "patch test first" if active["patch_test_required"] else "low caution",
            "routine_compatibility_tags": join(
                [
                    product["usage_time"],
                    product["routine_step"],
                    active["active_strength_level"],
                    *product["skin_types"],
                    *product["concerns"],
                ]
            ),
            "semantic_document": semantic_document,
            "content_embedding_text": semantic_document,
            "ingredient_complexity_score": min(1.0, len(product["ingredients"]) / 5),
            "barrier_support_score": round(0.85 if {"ceramide", "squalane", "panthenol", "hyaluronic-acid"} & set(product["ingredients"]) else 0.35, 3),
            "acne_safe_score": round(0.85 if product["comedogenic"] == "low" and "acne" in product["concerns"] else 0.55 if product["comedogenic"] == "low" else 0.35, 3),
            "oily_skin_fit_score": round(fit_score(product, "oily"), 3),
            "dry_skin_fit_score": round(fit_score(product, "dry"), 3),
            "sensitive_skin_fit_score": round(fit_score(product, "sensitive"), 3),
            "texture": product["texture"],
            "finish": product["finish"],
            "inventory_status": rng.choice(["In Stock", "In Stock", "Low Stock", "Backorder"]),
            "launch_year": rng.randint(2019, 2026),
            "popularity_score": rng.randint(55, 99),
            "rating": round(rng.uniform(3.9, 4.9), 1),
            "review_count": rng.randint(80, 8500),
            "return_rate": round(rng.uniform(0.01, 0.12), 3),
            "reorder_rate": round(rng.uniform(0.08, 0.72), 3),
            "margin_score": round(rng.uniform(0.15, 0.85), 3),
            "availability_score": round(rng.uniform(0.55, 1.0), 3),
            "clinical_claim_strength": rng.choice(["low", "medium", "high"]),
            "layout_type": rng.choice(LAYOUTS),
            "theme": rng.choice(THEMES),
            "recommendation_algorithm": rng.choice(["history_content_hybrid", "query_history_hybrid", "routine_contextual_ranker"]),
            "recommendation_score": recommendation_score,
            "personalization_score": personalization,
            "diversity_score": round(rng.uniform(0.15, 0.9), 3),
            "novelty_score": round(rng.uniform(0.08, 0.82), 3),
            "rank_position": rank_position,
            "redirect_url": f"https://skincare.example.com/products/{product_id.lower()}",
            "shown": shown,
            "hovered": hovered,
            "clicked": clicked,
            "purchased": purchased,
            "added_to_cart": added_to_cart,
            "wishlisted": wishlisted,
            "shared": shared,
            "watch_time_seconds": rng.randint(5, 260),
            "hover_time_seconds": rng.randint(1, 80) if hovered else 0,
            "scroll_depth": rng.randint(15, 100),
            "dwell_time_seconds": rng.randint(8, 300),
            "feedback_rating": rng.randint(1, 5) if rng.random() < 0.7 else "",
            "conversion": conversion,
            "negative_feedback": negative,
            "recommendation_reason": rng.choice(
                [
                    "matches prior clicks",
                    "similar to hovered ingredients",
                    "fits current query and skin concern",
                    "popular among users with similar history",
                    "supports next routine step",
                ]
            ),
            "next_best_action": rng.choice(["show routine bundle", "compare similar products", "surface reviews", "offer discount", "save for later"]),
            "created_at": (base_date - timedelta(minutes=idx * rng.randint(3, 17))).isoformat(),
        }
        rows.append(row)

    return rows


def write_dataset(path=OUTPUT_PATH):
    rows = generate_rows()
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    return path, len(rows), len(FIELDNAMES)


if __name__ == "__main__":
    output_path, row_count, column_count = write_dataset()
    print(f"Wrote {row_count} rows and {column_count} columns to {output_path}")
