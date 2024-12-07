import ast
import json
import logging
import sqlite3
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from flask_session import Session
from helpers import (
    normalize_quantity,
    db_connection,
    apology,
    paginate,
    login_required,
    get_filtered_recipes
)
from werkzeug.security import check_password_hash, generate_password_hash

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Routes
@app.route("/")
def home():
    """
    Home page showing filtered recipes based on user filters.
    """
    page = request.args.get("page", 1, type=int)  # Current page number
    per_page = 24  # Recipes per page
    user_id = session.get("user_id")  # Logged-in user ID

    # Default values for user preferences
    filters, dietary_restrictions, unavailable_equipment = [], [], []

    # Load user-specific preferences if logged in
    if user_id:
        with db_connection() as conn:
            user_data = conn.execute(
                """
                SELECT filter, dietary_restrictions, unavailable_equipment
                FROM users
                WHERE rowid = ?
                """,
                (user_id,)
            ).fetchone()

            if user_data:
                # Parse filters and preferences
                filters = json.loads(user_data["filter"]) if user_data["filter"] else []
                dietary_restrictions = json.loads(user_data["dietary_restrictions"]) if user_data["dietary_restrictions"] else []
                unavailable_equipment = json.loads(user_data["unavailable_equipment"]) if user_data["unavailable_equipment"] else []
    # Ensure filters is a list of dictionaries
    if isinstance(filters, list):
        filter_list = filters
    elif isinstance(filters, dict):
        # Convert dictionary-style filters to a list of dictionaries
        filter_list = [{"ingredient": key, "amount": value["amount"], "unit": value["unit"]} for key, value in filters.items()]
    else:
        filter_list = []

    # Fetch and filter recipes
    filtered_recipes = get_filtered_recipes(filter_list, dietary_restrictions, unavailable_equipment)

    # Paginate filtered recipes
    total_items = len(filtered_recipes)
    total_pages = (total_items + per_page - 1) // per_page
    paginated_recipes = filtered_recipes[(page - 1) * per_page: page * per_page]

    # Fetch user's favorite recipes
    user_favorites = []
    if user_id:
        with db_connection() as conn:
            favorites = conn.execute(
                "SELECT recipe_id FROM favorites WHERE user_id = ?", (user_id,)
            ).fetchall()
            user_favorites = [fav["recipe_id"] for fav in favorites]

    # Render the home page
    return render_template(
        "home.html",
        recipes=paginated_recipes,
        page=page,
        total_pages=total_pages,
        user=user_id,
        user_favorites=user_favorites,
    )

@app.route("/about")
def about():
   """About page"""
   return render_template("about.html", user=session.get("user_id"))

@app.route("/register", methods=["GET", "POST"])
def register():
   """Register a new user"""
   if request.method == "POST":
       username = request.form.get("username")
       password = request.form.get("password")
       confirmation = request.form.get("confirmation")

       # Ensure username and password were submitted
       if not username:
           return apology("Must provide username", 400)
       elif not password:
           return apology("Must provide password", 400)
       elif password != confirmation:
           return apology("Passwords do not match", 400)

       # Hash the user's password
       hashed_password = generate_password_hash(password)

       # Insert the new user into the database
       try:
           with db_connection() as conn:
               conn.execute(
                   "INSERT INTO users (username, hash) VALUES (?, ?)",
                   (username, hashed_password)
               )
               conn.commit()
               user_id = conn.execute(
                   "SELECT rowid FROM users WHERE username = ?",
                   (username,)
               ).fetchone()["rowid"]
       except sqlite3.IntegrityError:
           return apology("Username already taken", 400)
       except Exception as e:
           logging.error(f"Error registering user: {e}")
           return apology("Unexpected error occurred. Please try again.", 500)

       # Log the user in
       session["user_id"] = user_id
       flash("Registered successfully! You are now logged in.", "success")
       return redirect(url_for("home"))

   # GET request
   return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
   """Log user in"""
   # Clear any existing session data
   session.clear()

   if request.method == "POST":
       # Retrieve the form data
       username = request.form.get("username")
       password = request.form.get("password")

       # Ensure username and password are provided
       if not username:
           return apology("Must provide username", 400)
       if not password:
           return apology("Must provide password", 400)

       # Query the database for the user
       with db_connection() as conn:
           user = conn.execute(
               "SELECT * FROM users WHERE username = ?", (username,)
           ).fetchone()

       # Check if the user exists and the password is correct
       if user is None or not check_password_hash(user["hash"], password):
           return apology("Invalid username and/or password", 400)

       # Log the user in by saving their user ID in the session
       session["user_id"] = user["rowid"]
       flash("Logged in successfully!", "success")
       return redirect(url_for("home"))

   # Render the login page for GET requests
   return render_template("login.html")

@app.route("/logout")
def logout():
   """Log user out"""
   session.clear()
   return redirect(url_for("home"))

@app.route("/favorites")
@login_required
def favorites():
    """Display the user's favorite recipes with pagination."""
    page = request.args.get("page", 1, type=int)  # Current page number
    per_page = 24  # Number of favorites per page

    user_id = session["user_id"]  # Logged-in user ID

    with db_connection() as conn:
        # Fetch all favorites for the user, including Image_Name
        all_favorites = conn.execute(
            """
            SELECT recipes.rowid AS id, recipes.Title, recipes.Ingredients, recipes.Image_Name
            FROM recipes
            JOIN favorites ON recipes.rowid = favorites.recipe_id
            WHERE favorites.user_id = ?
            """,
            (user_id,)
        ).fetchall()

        # Fetch only the recipe IDs for user_favorites
        user_favorites = [fav["id"] for fav in all_favorites]

    # Paginate the favorites
    paginated_favorites, total_pages = paginate(all_favorites, page, per_page)

    # Render the favorites page
    return render_template(
        "favorites.html",
        favorites=paginated_favorites,
        page=page,
        total_pages=total_pages,
        user_favorites=user_favorites,  # Pass recipe IDs for star logic
        user=user_id,
    )

@app.route("/recipe/<int:recipe_id>")
def view_recipe(recipe_id):
   """Display the details of a specific recipe."""
   with db_connection() as conn:
       # Fetch the specific recipe by ID, including Cleaned_Ingredients
       recipe = conn.execute(
           """
           SELECT rowid AS id, Title, Parsed_Ingredients, Cleaned_Ingredients, Instructions, Image_Name
           FROM recipes
           WHERE rowid = ?
           """,
           (recipe_id,)
       ).fetchone()

       if not recipe:
           flash("Recipe not found", "error")
           return redirect(url_for("home"))

       # Use Parsed_Ingredients and Cleaned_Ingredients directly
       parsed_ingredients = []
       cleaned_ingredients = ast.literal_eval(recipe["Cleaned_Ingredients"])

       if recipe["Parsed_Ingredients"]:
           try:
               parsed_ingredients = json.loads(recipe["Parsed_Ingredients"])
           except (ValueError, json.JSONDecodeError) as e:
               logging.error(f"Error parsing Parsed_Ingredients: {e}")
               flash("Error parsing ingredients for this recipe.", "error")

       # Fetch user's favorite recipes if logged in
       user_id = session.get("user_id")
       user_favorites = []
       if user_id:
           favorites = conn.execute(
               "SELECT recipe_id FROM favorites WHERE user_id = ?", (user_id,)
           ).fetchall()
           user_favorites = [fav["recipe_id"] for fav in favorites]

   # Render the recipe details page
   return render_template(
       "view_recipe.html",
       recipe=recipe,
       parsed_ingredients=parsed_ingredients,
       ingredients=cleaned_ingredients,
       user=user_id,
       user_favorites=user_favorites,
   )

@app.route("/filter_view", methods=["GET", "POST"])
@login_required
def filter_view():
    """View and save ingredient filters, dietary restrictions, and unavailable equipment."""
    user_id = session["user_id"]

    # Predefined valid options
    VALID_DIETARY_RESTRICTIONS = ["vegetarian", "vegan", "gluten-free", "nut-free", "dairy-free"]
    VALID_EQUIPMENT = ["oven", "stove", "microwave", "blender"]

    if request.method == "POST":
        action = request.form.get("action")
        if action == "clear":
            logging.debug("Clear All action triggered.")
            # Clear all filters and preferences
            try:
                with db_connection() as conn:
                    conn.execute(
                        """
                        UPDATE users
                        SET filter = ?, normalized_filters = ?, dietary_restrictions = ?, unavailable_equipment = ?
                        WHERE rowid = ?
                        """,
                        (json.dumps([]), json.dumps([]), json.dumps([]), json.dumps([]), user_id),
                    )
                    conn.commit()
                    logging.debug("All filters cleared in the database.")
            except sqlite3.Error as e:
                logging.error(f"Error clearing filters: {e}")
                return "", 500
            return redirect(url_for("filter_view"))

        else:  # Save all filters and preferences
            total_ingredients = int(request.form.get("total_ingredients", 0))
            filters = []
            normalized_filters = []
            # Iterate through all ingredients and store user-provided filters
            for i in range(1, total_ingredients + 1):
                ingredient = request.form.get(f"ingredient{i}", "").strip()
                amount = request.form.get(f"amount{i}", "").strip()
                unit = request.form.get(f"unit{i}", "").strip().lower()

                if not ingredient and not amount and not unit:
                    continue

                if bool(ingredient) + bool(amount) + bool(unit) not in [0, 3]:
                    flash("Please fill in fields for ingredients.", "error")
                    return redirect(url_for("filter_view"))
                
                # Validate and store user-provided filters
                filters.append({"ingredient": ingredient, "amount": amount, "unit": unit})

                # Normalize the filters for processing
                try:
                    normalized_amount = normalize_quantity(amount, unit)
                    normalized_filters.append({"ingredient": ingredient.lower(), "amount": normalized_amount, "unit": "grams"})
                except ValueError as e:
                    logging.warning(f"Failed to normalize filter: {ingredient}, {amount}, {unit}. Error: {e}")
                    continue
            
            # Validate dietary restrictions
            dietary_restrictions = request.form.getlist("dietary_restrictions")
            invalid_dietary = [restriction for restriction in dietary_restrictions if restriction not in VALID_DIETARY_RESTRICTIONS]
            if invalid_dietary:
                flash(f"Invalid dietary restrictions: {', '.join(invalid_dietary)}", "error")
                return redirect(url_for("filter_view"))

            # Validate unavailable equipment
            unavailable_equipment = request.form.getlist("unavailable_equipment")
            invalid_equipment = [equipment for equipment in unavailable_equipment if equipment not in VALID_EQUIPMENT]
            if invalid_equipment:
                flash(f"Invalid equipment preferences: {', '.join(invalid_equipment)}", "error")
                return redirect(url_for("filter_view"))

            # Save filters and normalized filters in the database
            try:
                with db_connection() as conn:
                    conn.execute(
                        """
                        UPDATE users
                        SET filter = ?, normalized_filters = ?, dietary_restrictions = ?, unavailable_equipment = ?
                        WHERE rowid = ?
                        """,
                        (
                            json.dumps(filters),
                            json.dumps(normalized_filters),
                            json.dumps(dietary_restrictions),
                            json.dumps(unavailable_equipment),
                            user_id,
                        ),
                    )
                    conn.commit()
                    flash("Search saved successfully!", "success")
            except sqlite3.Error as e:
                logging.error(f"Error saving selections: {e}")
                flash("An error occurred while saving selections.", "error")
            return redirect(url_for("home"))

    # Handle GET requests: Load existing filters
    try:
        with db_connection() as conn:
            user_data = conn.execute(
                "SELECT filter, normalized_filters, dietary_restrictions, unavailable_equipment FROM users WHERE rowid = ?",
                (user_id,),
            ).fetchone()
            filters = json.loads(user_data["filter"]) if user_data and user_data["filter"] else []
            dietary_restrictions = json.loads(user_data["dietary_restrictions"]) if user_data and user_data["dietary_restrictions"] else []
            unavailable_equipment = json.loads(user_data["unavailable_equipment"]) if user_data and user_data["unavailable_equipment"] else []
    except sqlite3.Error as e:
        logging.error(f"Error loading filters: {e}")
        flash("An error occurred while loading selections.", "error")
        filters, dietary_restrictions, unavailable_equipment = [], [], []

    return render_template(
        "filter.html",
        filters=filters,
        dietary_restrictions=dietary_restrictions,
        unavailable_equipment=unavailable_equipment,
    )

@app.route("/add_favorite", methods=["POST"])
@login_required
def add_favorite():
    """Add a recipe to user's favorites"""
    user_id = session["user_id"]
    recipe_id = request.json.get("recipe_id")
    # Ensure recipe_id is provided
    try:
        with db_connection() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO favorites (user_id, recipe_id) VALUES (?, ?)",
                (user_id, recipe_id)
            )
            conn.commit()
        return jsonify(success=True)
    except sqlite3.Error as e:
        logging.error(f"Error adding favorite: {e}")
        return jsonify(success=False, error=str(e)), 500

@app.route("/remove_favorite", methods=["POST"])
@login_required
def remove_favorite():
    """Remove a recipe from user's favorites"""
    user_id = session["user_id"]
    recipe_id = request.json.get("recipe_id")
    # Ensure recipe_id is provided
    try:
        with db_connection() as conn:
            conn.execute(
                "DELETE FROM favorites WHERE user_id = ? AND recipe_id = ?",
                (user_id, recipe_id)
            )
            conn.commit()
        return jsonify(success=True)
    except sqlite3.Error as e:
        logging.error(f"Error removing favorite: {e}")
        return jsonify(success=False, error=str(e)), 500
    
