# README.md

## Link to video: https://youtu.be/yFy4a9K_LSw

## FlavorFinder: Recipe Search and Discovery Platform
FlavorFinder is an intuitive web application that allows users to search and discover recipes based on ingredients they already have, dietary restrictions, and available kitchen equipment. The platform provides personalized recipe filtering to ensure users find the most suitable recipes with minimal effort.

This project leverages Flask for the backend and SQLite3 for data management, paired with Bootstrap for a polished and responsive front end. With over 13,500 recipes, FlavorFinder is designed to streamline cooking for casual cooks and culinary enthusiasts alike.

---

### Features:
- **Ingredient Filtering**: Filter recipes by specifying ingredients, quantities, and units. Errors will be displayed through flash.
- **Dietary Restrictions:** Exclude recipes that do not adhere to specific dietary needs (e.g., vegetarian, vegan, gluten-free).
- **Unavailable Equipment:** Exclude recipes that require equipment you don’t have.
- **Favorite Recipes:** Save and manage your favorite recipes for quick access.
- **Pagination:** Easily browse through a large collection of recipes.
- **Login:** login to an existing account. You will be informed of any errors through apology.html.
- **Logout:** Log out of the account. You will be informed of any errors through apology.html.
- **Register:** Allows users to make an account. You will be informed of any errors through apology.html.
- **About:** Tells users our mission and gives credit to who created the recipes database (and links to the website).

This platform was designed with users’ convenience and functionality in mind. The combination of search and filtering features aims to simplify the process of finding recipes tailored to personal preferences, making cooking more enjoyable. Favorites allow users to save their go-to recipes for quick access, and pagination ensures a cleaner and more digestible interface when browsing through a vast collection of recipes. With over 13,500 recipes in the database, it ensures that users can easily navigate the content without feeling overwhelmed.

---

### Installation

1. Download the zip file

Then execute

2. unzip flavorfinder.zip

Than, we can remove the .zip file since it is not needed anymore

3. rm flavorfinder.zip

then cd into the folder

4. cd project

Create a new virtual environment

5. python3 -m venv venv

Activate the virtual environment

6. source venv/bin/activate  # Mac/Linux
venv\Scripts\activate  # Windows
 
Install the requirements.txt file:

7. pip install -r requirements.txt

**Run the Application:**

8. flask run
   - The website will be accessible at `http://127.0.0.1:5000/`.

The use of a virtual environment was to ensures that all dependencies for FlavorFinder are isolated from your system’s global Python installation. This ensures there are no conflicts with other Python projects or system-wide packages. By activating the virtual environment and using the provided requirements.txt file, you guarantee that the application runs with the exact dependencies it was designed to use, ensuring consistent behavior and easier troubleshooting.
---

### Usage:
1. **Register an Account:**
   - Sign up with a username and password. Make sure to confirm your password.

2. **Set Search Selections:**
   - Specify ingredients, dietary restrictions, and unavailable equipment on the Filter page.
   - Save your preferences to personalize recipe results.

3. **Search Recipes:**
   - View filtered recipes on the home page.

4. **View Recipe Details:**
   - Click on a recipe card to view ingredients and instructions. You will also be able to check boxes off so you don’t need to remember where you are (these however will not be saved if you go elsewhere and return).

5. **Favorites:**
   - Add recipes to your favorites and access them anytime from the Favorites page.

6. **About**
- See the goals of the website and where the recipes are from.

7. **Search Bar**
- You can use the search bar in favorites or on the home page to find recipes.

7. **Login/Logout**
- You can also login and logout of your acount.

The usage of FlavorFinder is designed to be intuitive and user-friendly, catering to both casual cooks and culinary enthusiasts. By enabling users to customize their recipe search through filters and dietary restrictions, the platform streamlines the process of finding recipes that fit individual preferences and limitations. Features like saving favorites and accessing them easily enhance convenience, while interactive recipe pages with checkbox functionality make following instructions more seamless.

## Error Handling

FlavorFinder incorporates a robust error-handling system to ensure a seamless user experience and maintain application stability. The key components of error handling include:

	•	Flash Messages: Errors encountered during user interactions, such as incomplete form submissions or invalid inputs, are displayed as flash messages. For example, when saving ingredient filters, a flash message informs users to fill in all required fields if they leave any incomplete.

	•	Apology Page: For critical errors, the apology.html page provides users with detailed error messages. This is used when more explanation is needed, such as during registration or login issues, to guide users on how to correct their inputs.

	•	Input Validation: Validation is performed at various points to ensure the integrity of user inputs. For example:
      •	Ingredient filters require all fields (ingredient, amount, unit) to be complete to proceed.
      •	Dietary restrictions and equipment selections are checked for validity.

By combining user-facing error messages and robust backend validation, FlavorFinder minimizes disruptions and ensures a user-friendly and reliable application experience.

## Examples: Testing the Search 

For ingredients: Eggs, 1, unit
Dietary restrictions: Gluten-Free
Unavailable equipment: Stove

For ingredients: Sugar, 3, Cups
Dietary restrictions: vegan
Unavailable equipment: blender

## Trouble shooting:

If you encounter issues:
	•  Check Dependencies: Ensure all packages in requirements.txt are installed.
	•	Virtual Environment: Confirm the virtual environment is activated before running the app.
	•	Database: Ensure personalized_recipes.db exists in the project directory and is not corrupted.
