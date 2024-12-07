from sqlite3 import Error
from contextlib import contextmanager
import sqlite3
import logging
from rapidfuzz import fuzz, process
import re

equipment_keywords = {
    "oven": [
        "bake", "roast", "broil", "grill", "braise", "toast", "dehydrate",
        "proof", "reheat", "slow cook", "convection bake", "convection roast",
        "preheat", "medium heat", "high heat", "low heat", "medium-high", "high-medium", "medium-low"
    ],
    "stove": [
        "boil", "simmer", "pan-fry", "stir-fry", "saute", "sear", "poach",
        "steam", "deep-fry", "blanch", "reduce", "caramelize", "scald"
    ],
    "microwave": [
        "microwave", "heat", "defrost", "reheat", "melt", "steam", "cook"
    ],
    "blender": [
        "blend", "puree", "mix", "chop", "grind", "whip", "emulsify",
        "liquefy", "crush", "pulse", "smooth", "process", "crumb", "powder", "mince"
    ]
}

ingredients_keywords = {
    "vegetarian": [
        "chicken", "beef", "pork", "fish", "seafood", "bacon", "gelatin",
        "lamb", "duck", "turkey", "ham", "sausage", "venison", "veal"
    ],
    "vegan": [
        "chicken", "beef", "pork", "fish", "seafood", "bacon", "gelatin",
        "milk", "cheese", "butter", "honey", "eggs", "cream", "yogurt",
        "whey", "casein", "lactose", "albumin", "mayonnaise", "gelato"
    ],
    "gluten-free": [
        "wheat", "barley", "rye", "flour", "bread", "pasta", "cake", "cookie",
        "cracker", "beer", "soy sauce", "macaroni", "couscous", "bulgur",
        "farro", "seitan", "spelt", "semolina", "triticale", "malt"
    ],
    "nut-free": [
        "almond", "walnut", "cashew", "pecan", "peanut", "hazelnut", "nut",
        "pistachio", "macadamia", "brazil nut", "pine nut", "chestnut"
    ],
    "dairy-free": [
        "milk", "cheese", "butter", "cream", "yogurt", "whey", "casein",
        "lactose", "gelato", "ice cream", "custard", "sour cream", "ghee",
        "kefir", "buttermilk", "ricotta", "paneer", "mascarpone", "quark"
    ]
}

# Context manager for database connection
@contextmanager
def db_connection():
    try:
        conn = sqlite3.connect('personalized_recipes.db')
        conn.row_factory = sqlite3.Row
        yield conn
    except Error as e:
        logging.error(f"Database error: {e}")
    finally:
        conn.close()

def populate_tables():
    """Populate dietary_restrictions and equipment tables."""
    try:
        # Data to insert
        dietary_restrictions = [
            "vegetarian", "vegan", "gluten-free", "nut-free", "dairy-free"
        ]
        equipment_list = ["oven", "stove", "microwave", "blender"]

        # Insert data into tables
        with db_connection() as conn:
            # Insert dietary restrictions
            conn.executemany(
                "INSERT OR IGNORE INTO dietary_restrictions (restriction_name) VALUES (?)",
                [(restriction,) for restriction in dietary_restrictions]
            )

            # Insert equipment
            conn.executemany(
                "INSERT OR IGNORE INTO equipment (equipment_name) VALUES (?)",
                [(equipment,) for equipment in equipment_list]
            )

            conn.commit()
            logging.info("Tables populated successfully!")

    except sqlite3.Error as e:
        logging.error(f"Error populating tables: {e}")


def dynamic_associate_recipes():
    """
    Dynamically associate recipes with dietary restrictions and equipment using fuzzy matching.
    """
    try:
        with db_connection() as conn:
            # Fetch all recipes, using rowid as the unique identifier
            recipes = conn.execute("SELECT rowid AS id, ingredients, instructions FROM recipes").fetchall()

            # Iterate through each recipe
            for recipe in recipes:
                recipe_id = recipe["id"]  # rowid is now treated as id
                ingredients = recipe["ingredients"].lower() if recipe["ingredients"] else ""
                instructions = recipe["instructions"].lower() if recipe["instructions"] else ""

                # Break instructions into sentences for better matching
                sentences = re.split(r'[.!?]', instructions)

                """# Associate dietary restrictions based on ingredients
                for restriction, keywords in ingredients_keywords.items():
                    for keyword in keywords:
                        if keyword in ingredients:
                            restriction_id = conn.execute(
                                "SELECT id FROM dietary_restrictions WHERE restriction_name = ?",
                                (restriction,)
                            ).fetchone()
                            if restriction_id:
                                conn.execute(
                                    "INSERT OR IGNORE INTO recipe_dietary_restrictions (recipe_id, restriction_id) VALUES (?, ?)",
                                    (recipe_id, restriction_id["id"])
                                )"""

                # Associate equipment based on instructions
                for equipment, keywords in equipment_keywords.items():
                    for sentence in sentences:
                        matches = process.extract(sentence, keywords, scorer=fuzz.WRatio, limit=1)
                        if matches and matches[0][1] > 70:  # Lower threshold
                            logging.debug(f"Matched {equipment} for recipe {recipe_id} with keyword {matches[0][0]}")
                            equipment_id = conn.execute(
                                "SELECT id FROM equipment WHERE equipment_name = ?",
                                (equipment,)
                            ).fetchone()
                            if equipment_id:
                                conn.execute(
                                    "INSERT OR IGNORE INTO recipe_equipment (recipe_id, equipment_id) VALUES (?, ?)",
                                    (recipe_id, equipment_id["id"])
                                )

            conn.commit()
            logging.info("Dynamic associations created successfully!")

    except sqlite3.Error as e:
        logging.error(f"Error during dynamic association: {e}")


# Run the function
if __name__ == "__main__":
    dynamic_associate_recipes()