import json
import sqlite3
import re
import logging

from rapidfuzz import process
import json
import re
import logging

# Conversion factors for unit to grams
conversion_factors = {
        'grams': 1, 'g': 1, 'pinch': 0.5, 'pinchs': 0.5, 'dash': 0.5, 'dashs': 0.5, 'kilograms': 1000, 'kilogram': 1000, 'kg': 1000,
        'milliliters': 1, 'milliliter': 1, 'ml': 1, 'liters': 1000, 'liter': 1000, 'l': 1000,
        'cups': 240, 'cup': 240, 'tablespoons': 15, 'tablespoon': 15, 'tbsp': 15,
        'teaspoons': 5, 'teaspoon': 5,'tsp': 5, 'ounce': 28.35, 'ounces': 28.35, 'oz': 28.35,
        'pound': 453.592, 'pounds': 453.592, 'lb': 453.592, 'lbs': 453.592, 'unit': 1, 'units': 1, '': 1
    }

def normalize_quantity_and_extract_ingredient(ingredient):
    """
    Normalize the quantity of an ingredient to grams and extract the core ingredient name.

    Args:
        ingredient (dict): A dictionary with "quantity", "unit", and "ingredient".

    Returns:
        dict: The updated ingredient dictionary with normalized quantity in grams and cleaned ingredient name.
    """
    try:
        # Ensure the fields are the correct types
        raw_quantity = ingredient.get("quantity", 1)  # Default quantity to 1 if missing
        raw_unit = str(ingredient.get("unit", "")).strip()  # Ensure unit is a string
        raw_name = str(ingredient.get("ingredient", "")).strip().lower()  # Ensure ingredient is a string

        # Convert raw_quantity to a float, handle invalid cases
        try:
            quantity = float(raw_quantity)
        except (ValueError, TypeError):
            logging.warning(f"Invalid quantity: {raw_quantity}. Defaulting to 1.")
            quantity = 1  # Default to 1 if invalid

        # Handle fractions and mixed numbers in quantity
        fraction_pattern = r"^(\d+)?\s?(\d+/\d+)?$"
        match = re.match(fraction_pattern, str(raw_quantity))
        if match:
            whole_number = int(match.group(1)) if match.group(1) else 0
            fraction = eval(match.group(2)) if match.group(2) else 0
            quantity = whole_number + fraction

        # Fuzzy match the unit to known conversion factors
        matched_unit = process.extractOne(raw_unit.lower(), conversion_factors.keys(), score_cutoff=80)
        if matched_unit:
            conversion_factor = conversion_factors[matched_unit[0]]
            quantity *= conversion_factor
        else:
            logging.warning(f"Unrecognized unit: {raw_unit}. Assuming quantity is already in grams.")

        # Clean the core ingredient name
        cleaned_ingredient = re.sub(r"\b(of|with|for|and)\b", "", raw_name)  # Remove noise words
        cleaned_ingredient = re.sub(r"(\d+[\w\s]*)?\b" + re.escape(raw_unit) + r"\b", "", cleaned_ingredient).strip()

        return {"quantity": quantity, "ingredient": cleaned_ingredient}

    except Exception as e:
        logging.error(f"Error processing ingredient: {ingredient}. Error: {e}")
        return {"quantity": 0.0, "ingredient": "unknown"}

def preprocess_database(db_path="personalized_recipes.db"):
    """
    Preprocess the database by normalizing ingredients and storing them in a new column.

    Args:
        db_path (str): Path to the SQLite database.
    """
    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Fetch all recipes
            recipes = cursor.execute("SELECT rowid, Parsed_Ingredients FROM recipes").fetchall()
            for recipe in recipes:
                try:
                    parsed_ingredients = json.loads(recipe["Parsed_Ingredients"]) if recipe["Parsed_Ingredients"] else []
                    normalized_ingredients = normalize_ingredients(parsed_ingredients)
                    cursor.execute(
                        "UPDATE recipes SET Normalized_Ingredients = ? WHERE rowid = ?",
                        (normalized_ingredients, recipe["rowid"])
                    )
                except Exception as e:
                    logging.error(f"Error preprocessing recipe ID {recipe['rowid']}: {e}")
                    continue

            conn.commit()
            logging.info("Database successfully preprocessed.")
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")

def normalize_ingredients(parsed_ingredients):
    """
    Normalize parsed ingredients by converting quantities to grams and extracting core ingredient names.

    Args:
        parsed_ingredients (list): List of ingredient dictionaries with keys: quantity, unit, ingredient.

    Returns:
        str: JSON string of normalized ingredients.
    """
    normalized = []

    for ingredient in parsed_ingredients:
        try:
            normalized_ingredient = normalize_quantity_and_extract_ingredient(ingredient)
            normalized.append(normalized_ingredient)
        except Exception as e:
            logging.error(f"Error processing ingredient: {ingredient}. Error: {e}")
            continue

    return json.dumps(normalized)

if __name__ == "__main__":
    preprocess_database()