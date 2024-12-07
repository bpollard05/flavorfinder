from collections import defaultdict
from contextlib import contextmanager
from flask import flash, redirect, render_template, session, url_for
from functools import wraps
import json
import logging
import re
import sqlite3
from rapidfuzz import fuzz

# Conversion factors for unit to grams
conversion_factors = {
        'grams': 1, 'g': 1, 'pinch': 0.5, 'pinchs': 0.5, 'dash': 0.5, 'dashs': 0.5, 'kilograms': 1000, 'kilogram': 1000, 'kg': 1000,
        'milliliters': 1, 'milliliter': 1, 'ml': 1, 'liters': 1000, 'liter': 1000, 'l': 1000,
        'cups': 240, 'cup': 240, 'tablespoons': 15, 'tablespoon': 15, 'tbsp': 15,
        'teaspoons': 5, 'teaspoon': 5,'tsp': 5, 'ounce': 28.35, 'ounces': 28.35, 'oz': 28.35,
        'pound': 453.592, 'pounds': 453.592, 'lb': 453.592, 'lbs': 453.592, 'unit': 1, 'units': 1, '': 1
    }


def group_ingredients_by_name(normalized_ingredients, filters):
    """
    Dynamically groups ingredients based on user filter items and sums their quantities.

    Args:
        normalized_ingredients (list): List of ingredient dictionaries with "ingredient" and "quantity".
        filters (list): List of user-specified ingredient filters with "ingredient".

    Returns:
        dict: A dictionary with grouped ingredient names (from filters) and total quantities.
    """
    grouped_ingredients = defaultdict(float)

    # Extract the ingredient names from filters
    filter_ingredients = [f["ingredient"].lower() for f in filters]

    for ingredient in normalized_ingredients:
        name = ingredient["ingredient"].lower()
        quantity = ingredient.get("quantity", 0)

        # Check if the ingredient matches any user filter dynamically
        matched_filter = None
        for filter_ingredient in filter_ingredients:
            if fuzz.partial_ratio(name, filter_ingredient) > 80:  # Fuzzy matching threshold
                matched_filter = filter_ingredient
                break

        if matched_filter:
            # Add quantity to the matched group
            grouped_ingredients[matched_filter] += quantity
        else:
            # Add ingredient as-is if it doesn't match any filter
            grouped_ingredients[name] += quantity

    return grouped_ingredients


def fuzzy_match(user_ingredient, recipe_ingredient):
    return fuzz.partial_ratio(user_ingredient.lower(), recipe_ingredient.lower()) > 80


def normalize_quantity(quantity, unit):
    """
    Normalize the quantity to grams using conversion factors.

    Args:
        quantity (str or float): The raw quantity value.
        unit (str): The unit of measurement.

    Returns:
        float: The normalized quantity in grams, or 0.0 if invalid.
    """
    # Normalize unit
    unit = unit.lower().strip()

    # Pattern to match mixed numbers like "1 1/2" or "1½"
    mixed_number_pattern = r"^(\d+)?\s?(\d+/\d+)?$"

    try:
        # Handle fractions and mixed numbers
        match = re.match(mixed_number_pattern, quantity)
        if match:
            whole_number = match.group(1)  # The whole number part
            fraction = match.group(2)     # The fraction part
            whole_number = int(whole_number) if whole_number else 0
            fraction = eval(fraction) if fraction else 0
            normalized_quantity = whole_number + fraction
        else:
            # Attempt to directly evaluate simple fractions like "½"
            normalized_quantity = eval(quantity.replace("¼", "0.25")
                                            .replace("½", "0.5")
                                            .replace("¾", "0.75")
                                            .replace("⅓", "0.33")
                                            .replace("⅔", "0.67"))
    except (SyntaxError, NameError, ValueError) as e:
        logging.warning(f"Invalid fraction or value: {quantity}. Defaulting to 0.0.")
        return 0.0

    # Convert to grams
    if unit in conversion_factors:
        return normalized_quantity * conversion_factors[unit]
    else:
        logging.warning(f"Invalid or unrecognized unit: {unit}. Defaulting to 0.0.")
        return 0.0

def normalize_ingredients(parsed_ingredients):
    """
    Normalize parsed ingredients by converting quantities and units to a standard format.
    
    Args:
        parsed_ingredients (list): List of ingredient dictionaries with keys: quantity, unit, ingredient.
    
    Returns:
        str: JSON string of normalized ingredients.
    """
    normalized = []
    # Iterate over each ingredient
    for ingredient in parsed_ingredients:
        try:
            # Extract fields
            raw_quantity = ingredient.get("quantity", "")
            unit = ingredient.get("unit", "").lower().strip()
            name = ingredient.get("ingredient", "").lower().strip()

            # Handle non-numeric or descriptive quantities
            if isinstance(raw_quantity, (int, float)):
                quantity = float(raw_quantity)
            elif isinstance(raw_quantity, str):
                # Attempt to normalize mixed fractions and plain numbers
                quantity = normalize_quantity(raw_quantity, unit)
            else:
                logging.warning(f"Invalid descriptive quantity for ingredient '{name}': {raw_quantity}. Moving to name.")
                name = f"{raw_quantity} {name}".strip()
                quantity = 0.0

            # Convert unit to grams
            quantity_in_grams = quantity * conversion_factors.get(unit, 1)

            # Normalize ingredient name
            name = re.sub(r"(^|\s)of\s", " ", name).strip()

            # Append normalized ingredient
            normalized.append({"quantity": quantity_in_grams, "ingredient": name})

        except Exception as e:
            logging.error(f"Error processing ingredient {ingredient}: {e}")
            continue

    return json.dumps(normalized)

# Return an apology
def apology(message, code=400):
   """Render message as an apology to user."""
   def escape(s):
       for old, new in [
           ("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
           ("%", "~p"), ("#", "~h"), ("/", "~s"), ('"', "''"),
       ]:
           s = s.replace(old, new)
       return s

   return render_template("apology.html", top=code, bottom=escape(message)), code
 
def validate_filters(filters):
    """
    Validate and normalize user-provided filters.
    
    Args:
        filters (list of dict): List of ingredient filters.
    
    Returns:
        list of dict: Normalized and validated filters.
    """
    # Ensure filters is a valid list
    if not isinstance(filters, list):
        logging.error("Invalid filters input: Expected a list.")
        return []
    if not filters:
        logging.warning("Empty filters received.")
        return []

    validated_filters = []
    logging.debug(f"Validating filters: {filters}")
    for filter_item in filters:
        ingredient = filter_item.get("ingredient", "").strip().lower()
        amount = filter_item.get("amount", 0)
        unit = filter_item.get("unit", "").strip().lower()

        # Validate ingredient name
        if not validate_ingredient(ingredient):
            logging.warning(f"Skipping invalid ingredient name: {ingredient}")
            continue

        # Normalize amount and unit
        try:
            normalized_amount = convert_to_grams(int(amount), unit)  # Ensure amount is a string for parsing
            logging.debug(f"Normalized: {ingredient}, {normalized_amount} grams")
        except ValueError as e:
            logging.warning(f"Invalid amount '{amount}' for ingredient '{ingredient}': {e}")
            continue

        # Append validated filter
        validated_filters.append({
            "ingredient": ingredient,
            "amount": normalized_amount,
            "unit": "grams"  # Always normalize to grams
        })
        logging.debug(f"Added validated filter: {validated_filters[-1]}")

    # Log the result and return validated filters
    logging.info(f"Validated filters: {validated_filters}")
    return validated_filters

# Pagination helper function
def paginate(data, page, per_page):
   offset = (page - 1) * per_page
   total_items = len(data)
   total_pages = (total_items + per_page - 1) // per_page
   return data[offset:offset + per_page], total_pages

@contextmanager
def db_connection():
   """Context manager for SQLite database connection."""
   conn = None
   try:
       conn = sqlite3.connect('personalized_recipes.db')
       conn.row_factory = sqlite3.Row
       logging.debug("Database connection established")
       yield conn
   except sqlite3.Error as e:
       logging.error(f"Database connection error: {e}")
       raise e
   finally:
       if conn:
           conn.close()
           logging.debug("Database connection closed")

# Convert amount to grams
def convert_to_grams(amount, unit):
    unit = unit.lower().rstrip('.,')
    # Security: handle negative amount.
    if amount < 0:
        flash("Invalid amount")
    # Security: handle invalid unit.
    if unit not in conversion_factors:
        flash("Invalid unit")
    return amount * conversion_factors.get(unit, 1)  # Default to 1 if unit is not recognized

def validate_ingredient(ingredient_name):
    # Allow letters, numbers, spaces, and dashes
    return bool(re.match(r"^[a-zA-Z0-9\s-]+$", ingredient_name))

def validate_unit(unit):
    valid_units = [
        'grams', 'g', 'pinch', 'pinchs', 'dash', 'dashs', 'kilograms', 'kilogram', 'kg',
       'milliliters', 'milliliter', 'ml', 'liters', 'liter', 'l',
       'cups', 'cup', 'tablespoons', 'tablespoon', 'tbsp',
       'teaspoons', 'teaspoon','tsp', 'ounce', 'ounces', 'oz',
       'pound', 'pounds', 'lb', 'lbs', 'unit', 'units', ''
    ]
    if unit in valid_units:
        return True
    logging.debug(f"Processing unit: '{unit}'")
    return False

def is_within_range(actual, expected, tolerance=0.1):
    """
    Check if the actual value is within the tolerance range of the expected value.

    Args:
        actual (float or str): The actual value (e.g., from the recipe).
        expected (float or str): The expected value (e.g., from the user filter).
        tolerance (float): The allowable percentage difference (default 10%).

    Returns:
        bool: True if within range, False otherwise.
    """
    try:
        actual = float(actual)
        expected = float(expected)
        if expected == 0:  # Prevent division by zero
            return False
        return abs(actual - expected) / expected <= tolerance
    except (ValueError, TypeError):
        logging.error(f"Invalid values for is_within_range: actual={actual}, expected={expected}")
        return False

def get_filtered_recipes(filters, dietary_restrictions, unavailable_equipment, db_path="personalized_recipes.db"):
    """
    Fetch and filter recipes based on user preferences.

    Args:
        filters (list of dict): List of ingredient filters with 'ingredient', 'amount', and 'unit'.
        dietary_restrictions (list of str): List of dietary restrictions (e.g., "vegetarian").
        unavailable_equipment (list of str): List of equipment unavailable to the user.
        db_path (str): Path to the SQLite database.

    Returns:
        list of dict: Recipes, prioritized by compliance with filters.
    """
    if not isinstance(filters, list):
        logging.error("Invalid 'filters' type. Expected a list.")
        return []
    if not isinstance(dietary_restrictions, list):
        logging.error("Invalid 'dietary_restrictions' type. Expected a list.")
        return []
    if not isinstance(unavailable_equipment, list):
        logging.error("Invalid 'unavailable_equipment' type. Expected a list.")
        return []

    # Base query
    query = """
        SELECT r.rowid AS id, r.Title, r.Normalized_Ingredients, r.Instructions, r.Image_Name
        FROM recipes r
        WHERE 1=1
    """
    params = []

    # Add conditions for dietary restrictions
    if dietary_restrictions:
        query += """
            AND r.rowid NOT IN (
                SELECT rdr.recipe_id
                FROM recipe_dietary_restrictions rdr
                INNER JOIN dietary_restrictions dr ON rdr.restriction_id = dr.id
                WHERE dr.restriction_name IN ({placeholders})
            )
        """.format(placeholders=", ".join("?" for _ in dietary_restrictions))
        params.extend(dietary_restrictions)

    # Add conditions for unavailable equipment
    if unavailable_equipment:
        query += """
            AND r.rowid NOT IN (
                SELECT re.recipe_id
                FROM recipe_equipment re
                INNER JOIN equipment e ON re.equipment_id = e.id
                WHERE e.equipment_name IN ({placeholders})
            )
        """.format(placeholders=", ".join("?" for _ in unavailable_equipment))
        params.extend(unavailable_equipment)

    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            results = conn.execute(query, params).fetchall()
    except sqlite3.Error as e:
        logging.error(f"Database query failed: {e}")
        return []
    
    # Filter recipes based on ingredient constraints
    filtered_results = []
    for row in results:
        try:
            # Parse ingredients
            normalized_ingredients = json.loads(row["Normalized_Ingredients"]) if row["Normalized_Ingredients"] else []

            # Exclude recipes exceeding ingredient constraints
            if not meets_ingredient_constraints(normalized_ingredients, filters):
                logging.debug(f"Recipe '{row['Title']}' exceeds ingredient constraints.")
                continue

            # Add the recipe to filtered results
            filtered_results.append(dict(row))
        except (ValueError, json.JSONDecodeError) as e:
            logging.error(f"Failed to parse ingredients for recipe '{row['Title']}': {e}")
            continue

    logging.debug(f"Number of recipes retrieved: {len(results)}")
    logging.debug(f"Number of filtered results: {len(filtered_results)}")
    return filtered_results

def meets_ingredient_constraints(normalized_ingredients, filters):
    """
    Check if a recipe meets ingredient constraints.

    Args:
        normalized_ingredients (list of dict): Preprocessed ingredients with normalized quantities.
        filters (list of dict): User-specified ingredient filters with 'ingredient' and 'amount'.

    Returns:
        bool: True if the recipe meets all constraints, False otherwise.
    """
    grouped_ingredients = group_ingredients_by_name(normalized_ingredients, filters)

    for filter_item in filters:
        user_ingredient = filter_item.get("ingredient", "").lower()
        user_quantity = float(filter_item.get("amount", 0))

        # If the ingredient is not in the recipe, it passes this filter
        if user_ingredient not in grouped_ingredients:
            continue

        # If the ingredient exceeds the user's specified amount, exclude the recipe
        total_quantity = grouped_ingredients[user_ingredient]
        if total_quantity > user_quantity:
            logging.debug(f"Ingredient {user_ingredient} exceeds limit: {total_quantity} > {user_quantity}")
            return False

    return True

# Login required decorator
def login_required(func):
   @wraps(func)
   def decorated_function(*args, **kwargs):
       if not session.get("user_id"):
           logging.debug("User not logged in - redirecting to login page.")
           return redirect(url_for("login"))
       logging.debug(f"User logged in with user_id: {session.get('user_id')}")
       return func(*args, **kwargs)
   return decorated_function
