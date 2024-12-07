### Database Design:
- **SQLite3** was chosen for its simplicity and lightweight nature, making it ideal for a small-scale web application.

- **Tables:**
  •	users Table: This table stores information about each user, including:
        •	username: A unique identifier for the user.
        •	hash: A hashed version of the user’s password for secure authentication.
        •	filter: JSON data capturing the user’s ingredient preferences and constraints.
        •	dietary_restrictions: JSON data storing the user’s selected dietary restrictions.
        •	unavailable_equipment: JSON data specifying equipment the user doesn’t have access to.
This design supports personalized recipe recommendations by dynamically retrieving user preferences during filtering.
	
  •	recipes table: This table contains the core data for all recipes, including:
        •	id: A unique identifier for each recipe.
        •	Title: The recipe name.
        •	Parsed_Ingredients: A detailed breakdown of ingredients, including quantities and units.
        •	Cleaned_Ingredients: Preprocessed and normalized ingredient data for streamlined filtering.
        •	Instructions: Step-by-step directions for preparing the recipe.
        •	Image_Name: A reference to the recipe’s image file for display.
        •   Normalized_Ingredients: has the ingredients and amount all normalized in grams in order to compare.
This structure allows recipes to be fully described and easily queried for display or filtering.
	
  •	‘favorites’ table: Tracks which recipes are marked as favorites by users:
        •	user_id: Links the favorite entry to a specific user.
        •	recipe_id: Links the favorite entry to a specific recipe.
The use of foreign keys ensures that only valid user and recipe IDs are stored, maintaining data integrity.

 	•	'equipment' table: Stores the types of kitchen equipment required for recipes. Each row contains:
        •	id: A unique identifier for the equipment.
        •	equipment_name: The name of the equipment (e.g., oven, stove, blender).
This table ensures that recipes can be filtered based on available or unavailable equipment.

	•	'dietary_restrictions' table: Contains a list of dietary restrictions to categorize recipes. Each row includes:
        •	id: A unique identifier for the dietary restriction.
        •	restriction_name: The name of the dietary restriction (e.g., vegetarian, vegan).
This table helps associate recipes with specific dietary needs for accurate filtering.

	•	'recipe_equipment' table: Links recipes to the equipment they require. Each row includes:
        •	recipe_id: The ID of the recipe.
        •	equipment_id: The ID of the equipment.
This relationship ensures that recipes can be excluded if a user lacks certain kitchen tools.

	•	'recipe_dietary_restrictions' table: Links recipes to applicable dietary restrictions. Each row contains:
        •	recipe_id: The ID of the recipe.
        •	restriction_id: The ID of the dietary restriction.
This linkage ensures that users can exclude recipes that do not meet their dietary requirements.

The users table serves as the foundation for personalizing the application by storing each user’s preferences, including ingredient filters, dietary restrictions, and unavailable equipment. These preferences directly influence how recipes are filtered and displayed to match individual needs.

The recipes table provides the core data for the application, detailing each recipe’s title, ingredients, instructions, and images. The inclusion of Normalized_Ingredients ensures compatibility with user-defined filters, allowing for precise matching and streamlined processing.

The recipe_dietary_restrictions and recipe_equipment tables dynamically associate recipes with dietary restrictions and required equipment, respectively. These relationships were established using fuzzy matching algorithms, which aimed to identify and link keywords from the recipe data. However, due to inconsistencies in the original data and the inherent limitations of fuzzy matching, there are some remaining inaccuracies in the associations that could not be fully resolved.

Together, these tables interact to deliver a highly personalized and dynamic experience. User preferences guide the filtering of recipes, while the relational design ensures that favorites and preferences remain consistent, secure, and easy to access. Despite some imperfections in the data due to the nature of fuzzy matching, this interconnected system remains a key component of FlavorFinder’s ability to provide tailored recipe recommendations efficiently and effectively.

### Backend:

- **Flask**: A lightweight Python web framework used for building the application.

- **Flask-Session**: Used for managing user sessions securely.

- **Helper functions:**
    The helper functions collectively streamline the application’s functionality. Core functions like normalize_quantity and group_ingredients_by_name standardize ingredient data, ensuring accurate filtering and user preferences alignment. validate_filters verifies user inputs for filtering recipes, while get_filtered_recipes uses these inputs to fetch recipes matching user criteria, integrating dietary restrictions and unavailable equipment.
    Pagination is handled by paginate, optimizing large datasets for display. Error handling is centralized in apology, providing clear feedback for user or system errors. Database interactions are safely managed with db_connection, while login_required ensures user authentication across protected routes.
    Together, these functions form a cohesive backend framework that integrates data processing, validation, and error management for a seamless user experience.

### Frontend:

- **HTML Templates:**
  - Built using **Jinja2** templating engine for dynamic content rendering.
  - Modular structure with `base.html` as the main template.

- **CSS Framework:**
  - **Bootstrap 4.5** for responsive design and consistent styling.

- **JavaScript:**
  - Handles dynamic form elements (e.g., adding/removing ingredient filters, and the search bars).

- **Templates:**
  
  •	home.html: Displays all or fitlered recipes with ability to use search bar and (if logged in) can favorite recipes.
  
  •	about.html: Displays an overview of the application, its purpose, and features, tailored for the logged-in user.
	
  •	apology.html: Renders error messages or user feedback, providing a consistent format for system or user errors.
	
  •	favorites.html: Lists recipes marked as favorites by the user, with pagination, options for interaction, and search bar.
	
  •	filter.html: Allows users to set and manage ingredient filters, dietary restrictions, and unavailable equipment preferences.
	
  •	login.html: Provides a login form for users to access their personalized account.
	
  •	register.html: Facilitates user registration with fields for username, password, and confirmation.
	
  •	template.html: A base template used to define the common structure for other pages, including headers, footers, and styles.
	
  •	view_recipe.html: Displays detailed information about a specific recipe, including ingredients, instructions, and user interaction options.

### Error Handling:
- **Validation:**
  - Ensures all filter fields are filled before saving.
  - Displays error messages via `flash` when invalid inputs are detected.

- **Database Operations:**
  - Errors during database operations are logged for debugging.

- **login, logout, register**
  - returns apology.html to handle errors

### Key Design Decisions:
1. **Ingredient Normalization:**
  To ensure consistency and enable accurate filtering, all ingredient quantities are normalized to grams. This uniform representation simplifies comparisons between user preferences and recipe data.
	
  The normalization process leverages a comprehensive set of pre-defined conversion factors in helpers.py for common units such as cups, tablespoons, ounces, and pounds. For instance, one cup of an ingredient is converted to its equivalent weight in grams.
	
  Fractions and mixed numbers like “1 1/2” are also parsed and converted to numeric values before applying unit conversions.
	
  Comparison Process:
	
  •	Once ingredients are normalized, recipes are compared against user-defined filters. This is achieved using the group_ingredients_by_name function, which dynamically aggregates ingredient quantities based on user-provided filters.
	
  •	Fuzzy matching is applied to account for variations in ingredient naming (e.g., “sugar” vs. “granulated sugar”). This ensures flexibility in matching while maintaining accuracy (although it is not perfect).
	
  •	For each ingredient filter, the system checks whether the total quantity of a matched ingredient in a recipe exceeds the user’s specified limit. Recipes that surpass these constraints are excluded from the results.
	
  •	By grouping and summing quantities dynamically, the system supports recipes with repeated or split ingredient listings, ensuring accurate adherence to user constraints.

2. **Fuzzy Matching:**
   - RapidFuzz library is used to match user-provided ingredient names with recipe ingredients and group ingredients in the same recipe to add and compare accurately (e.g. sugar, powdered sugar).
   - Ensures flexibility in ingredient filtering.

3. **Session Management:**
   - Flask-Session ensures the secure handling of user preferences across sessions.

---

### Summary:
FlavorFinder combines the power of Flask for backend development and SQLite3 for efficient data management to create a seamless and user-friendly recipe-searching platform. Key features like ingredient normalization and fuzzy matching enhance the precision and flexibility of recipe filtering, ensuring users can easily find recipes tailored to their preferences. The polished front end, built with Bootstrap, delivers an intuitive and visually appealing interface, making the overall experience engaging and accessible for users.