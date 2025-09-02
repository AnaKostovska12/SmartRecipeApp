
import requests
from django.shortcuts import render
from django.conf import settings
# Imports Django settings, so you can access settings.SPOONACULAR_API_KEY (if you stored your API key in settings.py).
# Use settings if you move your API key there, otherwise fallback to hardcoded
API_KEY = getattr(settings, "SPOONACULAR_API_KEY", "f0bb9f1a96c645038fdc57083ff67c25")


def home(request):
    # Defines a Django view named home.
    """Home page with ingredient selection."""
    return render(request, "recipes/home.html")


def tips(request):
    """Tips page with cooking/kitchen tips."""
    return render(request, "recipes/tips.html")


def recipe_detail(request, recipe_id):
    """Show detailed information about a specific recipe."""
    url = f"https://api.spoonacular.com/recipes/{recipe_id}/information?includeNutrition=true&apiKey={API_KEY}"
    response = requests.get(url)
    # Sends a GET request to Spoonacular.
    recipe = response.json() if response.status_code == 200 else None

    return render(request, "recipes/recipe_detail.html", {"recipe": recipe})


def get_recipes(request):
    """
    Handle recipe search, random recipe fetch, or custom recipes by ingredients.
    Supports sorting by popularity, calories, price, healthiness, and protein.
    """
    sort = request.GET.get("sort", "")
    query = request.GET.get("query", "")
    recipes = []
    ingredients = []
# sort → sorting option (string from URL, default empty).

# query → search keyword (string from URL, default empty).

# recipes → results container (starts empty, filled later).

# ingredients → user’s chosen ingredients (starts empty, filled later).
    # ---------------- POST REQUESTS ---------------- #
    if request.method == "POST":
        action = request.POST.get("action")
# 3. action = request.POST.get("action")

# .get("action") tries to fetch the value associated with the key "action" from the POST data.
        # 🌟 Random Recipe
        if action == "random":
            url = f"https://api.spoonacular.com/recipes/random?number=1&apiKey={API_KEY}"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                recipes = data.get("recipes", [])
            else:
                ingredients = []
                # print("❌ Error fetching random recipe:", response.status_code, response.text)
                return render(request, "recipes/home.html", {
    "error": f"❌ Error fetching random recipe: {response.status_code}"
                })

            

        # 🌟 Custom Recipe by Selected Ingredients
        elif action == "custom":
            ingredients = request.POST.getlist("ingredients")
            if not ingredients:
                return render(request, "recipes/home.html", {"error": "Please select at least one ingredient."})

            query = ",".join(ingredients)
            search_url = (
                f"https://api.spoonacular.com/recipes/findByIngredients"
                f"?ingredients={query}&number=20&ranking=1&ignorePantry=true&apiKey={API_KEY}"
            )
            search_response = requests.get(search_url)
            if search_response.status_code != 200:
                print("❌ Error fetching recipes:", search_response.status_code, search_response.text)
                return render(request, "recipes/home.html", {"error": "Failed to fetch recipes. Try again later."})

            raw_recipes = search_response.json()[:20]  # top 10 recipes
            recipes = []
            for r in raw_recipes:
                recipe_id = r["id"]
                info_url = f"https://api.spoonacular.com/recipes/{recipe_id}/information?includeNutrition=true&apiKey={API_KEY}"
                info_response = requests.get(info_url)
                if info_response.status_code == 200:
                    recipes.append(info_response.json())
                else:
                    print(f"⚠️ Failed to fetch detailed info for recipe {recipe_id}: {info_response.status_code}")

        # Save recipes + ingredients to session
        request.session["recipes"] = recipes
        request.session["ingredients"] = ingredients

        return render(
            request,
            "recipes/recipe_list.html",
            {"recipes": recipes, "ingredients": ingredients, "sort": sort},
        )

    # ---------------- GET REQUESTS ---------------- #
    elif request.method == "GET":
        # 🔎 Handle search bar query
        if query:
            url = f"https://api.spoonacular.com/recipes/complexSearch?query={query}&number=12&addRecipeInformation=true&apiKey={API_KEY}"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                recipes = data.get("results", [])

                # ---------------- Sorting ---------------- #
                if sort == "popularity":
                    recipes.sort(key=lambda r: r.get("spoonacularScore", 0), reverse=True)
                elif sort == "calories":
                    def get_calories(recipe):
                        nutrients = recipe.get("nutrition", {}).get("nutrients", [])
                        for n in nutrients:
                            if n["name"].lower() == "calories":
                                return n["amount"]
                        return float("inf")
                    recipes.sort(key=get_calories)
                elif sort == "price":
                    recipes.sort(key=lambda r: r.get("pricePerServing", float("inf")))
                elif sort == "healthiness":
                    recipes.sort(key=lambda r: r.get("healthScore", 0), reverse=True)
                elif sort == "protein":
                    def get_protein(recipe):
                        nutrients = recipe.get("nutrition", {}).get("nutrients", [])
                        for n in nutrients:
                            if n["name"].lower() == "protein":
                                return n["amount"]
                        return 0
                    recipes.sort(key=get_protein, reverse=True)

            else:
                print("❌ Error fetching search results:", response.status_code, response.text)

            return render(
                request,
                "recipes/recipe_list.html",
                {"recipes": recipes, "ingredients": [], "sort": sort, "query": query},
            )

        # Reuse recipes from session if available
        elif "recipes" in request.session:
            recipes = request.session.get("recipes", [])
            ingredients = request.session.get("ingredients", [])

            # ---------------- Sorting ---------------- #
            if sort == "popularity":
                recipes.sort(key=lambda r: r.get("spoonacularScore", 0), reverse=True)
            elif sort == "calories":
                def get_calories(recipe):
                    nutrients = recipe.get("nutrition", {}).get("nutrients", [])
                    for n in nutrients:
                        if n["name"].lower() == "calories":
                            return n["amount"]
                    return float("inf")
                recipes.sort(key=get_calories)
            elif sort == "price":
                recipes.sort(key=lambda r: r.get("pricePerServing", float("inf")))
            elif sort == "healthiness":
                recipes.sort(key=lambda r: r.get("healthScore", 0), reverse=True)
            elif sort == "protein":
                def get_protein(recipe):
                    nutrients = recipe.get("nutrition", {}).get("nutrients", [])
                    for n in nutrients:
                        if n["name"].lower() == "protein":
                            return n["amount"]
                    return 0
                recipes.sort(key=get_protein, reverse=True)

            return render(
                request,
                "recipes/recipe_list.html",
                {"recipes": recipes, "ingredients": ingredients, "sort": sort},
            )

    # ---------------- Fallback ---------------- #
    return render(request, "recipes/home.html")
# def get_recipes(request):
#     """
#     Handle recipe search, random recipe fetch, or custom recipes by ingredients.
#     Supports sorting by popularity, calories, price, healthiness, and protein.
#     """

#     sort = request.GET.get("sort", "")
#     query = request.GET.get("query", "")
#     recipes = []
#     ingredients = []

#     # ---------------- POST REQUESTS ---------------- #
#     if request.method == "POST":
#         action = request.POST.get("action")

#         # 🌟 Random Recipe
#         if action == "random":
#             url = f"https://api.spoonacular.com/recipes/random?number=1&apiKey={API_KEY}"
#             response = requests.get(url)
#             if response.status_code == 200:
#                 data = response.json()
#                 recipes = data.get("recipes", [])
#             else:
#                 return render(request, "recipes/home.html", {
#                     "error": f"❌ Error fetching random recipe: {response.status_code}"
#                 })

#         # 🌟 Custom Recipe by Selected Ingredients
#         elif action == "custom":
#             ingredients = request.POST.getlist("ingredients")
#             if not ingredients:
#                 return render(request, "recipes/home.html", {"error": "Please select at least one ingredient."})

#             query = ",".join(ingredients)
#             search_url = (
#                 f"https://api.spoonacular.com/recipes/findByIngredients"
#                 f"?ingredients={query}&number=20&ranking=1&ignorePantry=true&apiKey={API_KEY}"
#             )
#             search_response = requests.get(search_url)
#             if search_response.status_code != 200:
#                 print("❌ Error fetching recipes:", search_response.status_code, search_response.text)
#                 return render(request, "recipes/home.html", {"error": "Failed to fetch recipes. Try again later."})

#             raw_recipes = search_response.json()[:20]

#             # ✅ Option 1: Keep only recipes whose ingredients are a subset of selected ones
#             allowed = set(i.lower() for i in ingredients)
#             filtered = []
#             for r in raw_recipes:
#                 recipe_ings = set()
#                 for ing in r.get("usedIngredients", []):
#                     recipe_ings.add(ing["name"].lower())
#                 for ing in r.get("missedIngredients", []):
#                     recipe_ings.add(ing["name"].lower())

#                 if recipe_ings.issubset(allowed):
#                     filtered.append(r)

#             # Fetch full details only for the filtered recipes
#             recipes = []
#             for r in filtered:
#                 recipe_id = r["id"]
#                 info_url = f"https://api.spoonacular.com/recipes/{recipe_id}/information?includeNutrition=true&apiKey={API_KEY}"
#                 info_response = requests.get(info_url)
#                 if info_response.status_code == 200:
#                     recipes.append(info_response.json())
#                 else:
#                     print(f"⚠️ Failed to fetch detailed info for recipe {recipe_id}: {info_response.status_code}")

#         # Save results to session
#         request.session["recipes"] = recipes
#         request.session["ingredients"] = ingredients

#         return render(
#             request,
#             "recipes/recipe_list.html",
#             {"recipes": recipes, "ingredients": ingredients, "sort": sort},
#         )

#     # ---------------- GET REQUESTS ---------------- #
#     elif request.method == "GET":
#         # 🔎 Handle search bar query
#         if query:
#             url = f"https://api.spoonacular.com/recipes/complexSearch?query={query}&number=12&addRecipeInformation=true&apiKey={API_KEY}"
#             response = requests.get(url)
#             if response.status_code == 200:
#                 data = response.json()
#                 recipes = data.get("results", [])

#                 # ---------------- Sorting ---------------- #
#                 if sort == "popularity":
#                     recipes.sort(key=lambda r: r.get("spoonacularScore", 0), reverse=True)
#                 elif sort == "calories":
#                     def get_calories(recipe):
#                         nutrients = recipe.get("nutrition", {}).get("nutrients", [])
#                         for n in nutrients:
#                             if n["name"].lower() == "calories":
#                                 return n["amount"]
#                         return float("inf")
#                     recipes.sort(key=get_calories)
#                 elif sort == "price":
#                     recipes.sort(key=lambda r: r.get("pricePerServing", float("inf")))
#                 elif sort == "healthiness":
#                     recipes.sort(key=lambda r: r.get("healthScore", 0), reverse=True)
#                 elif sort == "protein":
#                     def get_protein(recipe):
#                         nutrients = recipe.get("nutrition", {}).get("nutrients", [])
#                         for n in nutrients:
#                             if n["name"].lower() == "protein":
#                                 return n["amount"]
#                         return 0
#                     recipes.sort(key=get_protein, reverse=True)

#             else:
#                 print("❌ Error fetching search results:", response.status_code, response.text)

#             return render(
#                 request,
#                 "recipes/recipe_list.html",
#                 {"recipes": recipes, "ingredients": [], "sort": sort, "query": query},
#             )

#         # Reuse recipes from session if available
#         elif "recipes" in request.session:
#             recipes = request.session.get("recipes", [])
#             ingredients = request.session.get("ingredients", [])

#             # ---------------- Sorting ---------------- #
#             if sort == "popularity":
#                 recipes.sort(key=lambda r: r.get("spoonacularScore", 0), reverse=True)
#             elif sort == "calories":
#                 def get_calories(recipe):
#                     nutrients = recipe.get("nutrition", {}).get("nutrients", [])
#                     for n in nutrients:
#                         if n["name"].lower() == "calories":
#                             return n["amount"]
#                     return float("inf")
#                 recipes.sort(key=get_calories)
#             elif sort == "price":
#                 recipes.sort(key=lambda r: r.get("pricePerServing", float("inf")))
#             elif sort == "healthiness":
#                 recipes.sort(key=lambda r: r.get("healthScore", 0), reverse=True)
#             elif sort == "protein":
#                 def get_protein(recipe):
#                     nutrients = recipe.get("nutrition", {}).get("nutrients", [])
#                     for n in nutrients:
#                         if n["name"].lower() == "protein":
#                             return n["amount"]
#                         return 0
#                 recipes.sort(key=get_protein, reverse=True)

#             return render(
#                 request,
#                 "recipes/recipe_list.html",
#                 {"recipes": recipes, "ingredients": ingredients, "sort": sort},
#             )

#     # ---------------- Fallback ---------------- #
#     return render(request, "recipes/home.html")
