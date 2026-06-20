from __future__ import annotations

import json
import re
from dataclasses import asdict
from typing import Any

from database import get_connection
from models.food_normalization_models import (
    CanonicalFood,
    CanonicalFoodAlias,
    CanonicalFoodNutrient,
    CanonicalFoodSearchResult,
    FoodSourceLink,
    RawFoodSourceRecord,
)

ALLOWED_FOOD_TYPES = {"raw", "cooked", "prepared", "branded", "generic"}
ALLOWED_SOURCE_POLICIES = {"direct_source", "averaged_sources", "manually_curated"}
ALLOWED_NUTRIENT_CONFIDENCE = {"Limited", "Low", "Moderate", "High"}
ALLOWED_SOURCE_RELATIONSHIPS = {
    "primary",
    "supporting",
    "equivalent",
    "alternate_preparation",
}

STARTER_CANONICAL_FOODS = [
    {
        "display_name": "Chicken Breast, Cooked, Skinless",
        "food_type": "cooked",
        "aliases": [
            "chicken",
            "chicken breast",
            "cooked chicken",
            "cooked chicken breast",
            "skinless chicken breast",
            "grilled chicken breast",
            "boneless chicken",
        ],
        "search_priority": 10,
        "nutrients_per_100g": {
            "Calories": (165.0, "kcal"),
            "Protein": (31.0, "g"),
            "Carbohydrate": (0.0, "g"),
            "Fat": (3.6, "g"),
        },
    },
    {
        "display_name": "Chicken Breast, Raw, Skinless",
        "food_type": "raw",
        "aliases": [
            "raw chicken breast",
            "uncooked chicken breast",
            "skinless raw chicken breast",
        ],
        "search_priority": 20,
        "nutrients_per_100g": {
            "Calories": (120.0, "kcal"),
            "Protein": (22.5, "g"),
            "Carbohydrate": (0.0, "g"),
            "Fat": (2.6, "g"),
        },
    },
    {
        "display_name": "Chicken Thigh, Cooked, Skinless",
        "food_type": "cooked",
        "aliases": [
            "chicken thigh",
            "cooked chicken thigh",
            "skinless chicken thigh",
            "boneless chicken thigh",
        ],
        "search_priority": 30,
        "nutrients_per_100g": {
            "Calories": (209.0, "kcal"),
            "Protein": (26.0, "g"),
            "Carbohydrate": (0.0, "g"),
            "Fat": (10.9, "g"),
        },
    },
    {
        "display_name": "Turkey Breast, Cooked",
        "food_type": "cooked",
        "aliases": [
            "turkey",
            "turkey breast",
            "cooked turkey breast",
            "sliced turkey breast",
        ],
        "search_priority": 30,
        "nutrients_per_100g": {
            "Calories": (135.0, "kcal"),
            "Protein": (29.0, "g"),
            "Carbohydrate": (0.0, "g"),
            "Fat": (1.6, "g"),
        },
    },
    {
        "display_name": "Pork Tenderloin, Cooked",
        "food_type": "cooked",
        "aliases": [
            "pork tenderloin",
            "cooked pork tenderloin",
            "pork loin",
        ],
        "search_priority": 40,
        "nutrients_per_100g": {
            "Calories": (143.0, "kcal"),
            "Protein": (26.2, "g"),
            "Carbohydrate": (0.0, "g"),
            "Fat": (3.5, "g"),
        },
    },
    {
        "display_name": "Tuna, Canned in Water",
        "food_type": "prepared",
        "aliases": [
            "tuna",
            "canned tuna",
            "tuna in water",
            "canned tuna in water",
        ],
        "search_priority": 20,
        "nutrients_per_100g": {
            "Calories": (116.0, "kcal"),
            "Protein": (25.5, "g"),
            "Carbohydrate": (0.0, "g"),
            "Fat": (0.8, "g"),
        },
    },
    {
        "display_name": "Shrimp, Cooked",
        "food_type": "cooked",
        "aliases": [
            "shrimp",
            "cooked shrimp",
            "prawns",
        ],
        "search_priority": 30,
        "nutrients_per_100g": {
            "Calories": (99.0, "kcal"),
            "Protein": (24.0, "g"),
            "Carbohydrate": (0.2, "g"),
            "Fat": (0.3, "g"),
        },
    },
    {
        "display_name": "Tilapia, Cooked",
        "food_type": "cooked",
        "aliases": [
            "tilapia",
            "cooked tilapia",
        ],
        "search_priority": 40,
        "nutrients_per_100g": {
            "Calories": (128.0, "kcal"),
            "Protein": (26.2, "g"),
            "Carbohydrate": (0.0, "g"),
            "Fat": (2.7, "g"),
        },
    },
    {
        "display_name": "Cod, Cooked",
        "food_type": "cooked",
        "aliases": [
            "cod",
            "cooked cod",
            "white fish",
        ],
        "search_priority": 40,
        "nutrients_per_100g": {
            "Calories": (105.0, "kcal"),
            "Protein": (22.8, "g"),
            "Carbohydrate": (0.0, "g"),
            "Fat": (0.9, "g"),
        },
    },
    {
        "display_name": "Sirloin Steak, Cooked",
        "food_type": "cooked",
        "aliases": [
            "sirloin",
            "sirloin steak",
            "steak",
            "cooked steak",
        ],
        "search_priority": 40,
        "nutrients_per_100g": {
            "Calories": (206.0, "kcal"),
            "Protein": (29.0, "g"),
            "Carbohydrate": (0.0, "g"),
            "Fat": (9.0, "g"),
        },
    },
    {
        "display_name": "Egg, Large",
        "food_type": "generic",
        "aliases": [
            "egg",
            "eggs",
            "large egg",
            "whole egg",
            "whole eggs",
        ],
        "search_priority": 10,
        "nutrients_per_100g": {
            "Calories": (143.0, "kcal"),
            "Protein": (12.6, "g"),
            "Carbohydrate": (0.7, "g"),
            "Fat": (9.5, "g"),
        },
    },
    {
        "display_name": "Egg Whites",
        "food_type": "generic",
        "aliases": [
            "egg whites",
            "egg white",
            "liquid egg whites",
        ],
        "search_priority": 20,
        "nutrients_per_100g": {
            "Calories": (52.0, "kcal"),
            "Protein": (10.9, "g"),
            "Carbohydrate": (0.7, "g"),
            "Fat": (0.2, "g"),
        },
    },
    {
        "display_name": "Ground Beef, 90/10",
        "food_type": "raw",
        "aliases": [
            "ground beef",
            "lean ground beef",
            "90/10 beef",
            "90 10 beef",
        ],
        "search_priority": 20,
        "nutrients_per_100g": {
            "Calories": (176.0, "kcal"),
            "Protein": (20.0, "g"),
            "Carbohydrate": (0.0, "g"),
            "Fat": (10.0, "g"),
        },
    },
    {
        "display_name": "Ground Beef, 80/20",
        "food_type": "raw",
        "aliases": [
            "80/20 beef",
            "80 20 beef",
            "ground chuck",
        ],
        "search_priority": 30,
        "nutrients_per_100g": {
            "Calories": (254.0, "kcal"),
            "Protein": (17.2, "g"),
            "Carbohydrate": (0.0, "g"),
            "Fat": (20.0, "g"),
        },
    },
    {
        "display_name": "Salmon, Cooked",
        "food_type": "cooked",
        "aliases": [
            "salmon",
            "cooked salmon",
        ],
        "search_priority": 20,
        "nutrients_per_100g": {
            "Calories": (206.0, "kcal"),
            "Protein": (22.1, "g"),
            "Carbohydrate": (0.0, "g"),
            "Fat": (12.4, "g"),
        },
    },
    {
        "display_name": "Greek Yogurt, Plain",
        "food_type": "generic",
        "aliases": [
            "greek yogurt",
            "plain greek yogurt",
            "yogurt",
        ],
        "search_priority": 20,
        "nutrients_per_100g": {
            "Calories": (59.0, "kcal"),
            "Protein": (10.3, "g"),
            "Carbohydrate": (3.6, "g"),
            "Fat": (0.4, "g"),
        },
    },
    {
        "display_name": "Cottage Cheese, Low Fat",
        "food_type": "generic",
        "aliases": [
            "cottage cheese",
            "low fat cottage cheese",
        ],
        "search_priority": 30,
        "nutrients_per_100g": {
            "Calories": (82.0, "kcal"),
            "Protein": (11.1, "g"),
            "Carbohydrate": (3.4, "g"),
            "Fat": (2.3, "g"),
        },
    },
    {
        "display_name": "Milk, 2%",
        "food_type": "generic",
        "aliases": [
            "milk",
            "2% milk",
            "two percent milk",
            "reduced fat milk",
        ],
        "search_priority": 30,
        "nutrients_per_100g": {
            "Calories": (50.0, "kcal"),
            "Protein": (3.3, "g"),
            "Carbohydrate": (4.8, "g"),
            "Fat": (2.0, "g"),
        },
    },
    {
        "display_name": "Milk, Whole",
        "food_type": "generic",
        "aliases": [
            "whole milk",
        ],
        "search_priority": 40,
        "nutrients_per_100g": {
            "Calories": (61.0, "kcal"),
            "Protein": (3.2, "g"),
            "Carbohydrate": (4.8, "g"),
            "Fat": (3.3, "g"),
        },
    },
    {
        "display_name": "Cheddar Cheese",
        "food_type": "generic",
        "aliases": [
            "cheddar",
            "cheese",
            "cheddar cheese",
        ],
        "search_priority": 40,
        "nutrients_per_100g": {
            "Calories": (403.0, "kcal"),
            "Protein": (24.9, "g"),
            "Carbohydrate": (1.3, "g"),
            "Fat": (33.1, "g"),
        },
    },
    {
        "display_name": "Whey Protein Powder, Generic",
        "food_type": "generic",
        "aliases": [
            "protein powder",
            "whey",
            "whey protein",
            "whey protein powder",
        ],
        "search_priority": 30,
        "nutrients_per_100g": {
            "Calories": (400.0, "kcal"),
            "Protein": (80.0, "g"),
            "Carbohydrate": (8.0, "g"),
            "Fat": (6.0, "g"),
        },
    },
    {
        "display_name": "White Rice, Cooked",
        "food_type": "cooked",
        "aliases": [
            "rice",
            "white rice",
            "cooked rice",
            "cooked white rice",
        ],
        "search_priority": 10,
        "nutrients_per_100g": {
            "Calories": (130.0, "kcal"),
            "Protein": (2.7, "g"),
            "Carbohydrate": (28.2, "g"),
            "Fat": (0.3, "g"),
        },
    },
    {
        "display_name": "Brown Rice, Cooked",
        "food_type": "cooked",
        "aliases": [
            "brown rice",
            "cooked brown rice",
        ],
        "search_priority": 20,
        "nutrients_per_100g": {
            "Calories": (123.0, "kcal"),
            "Protein": (2.7, "g"),
            "Carbohydrate": (25.6, "g"),
            "Fat": (1.0, "g"),
        },
    },
    {
        "display_name": "Jasmine Rice, Cooked",
        "food_type": "cooked",
        "aliases": [
            "jasmine rice",
            "cooked jasmine rice",
        ],
        "search_priority": 20,
        "nutrients_per_100g": {
            "Calories": (129.0, "kcal"),
            "Protein": (2.9, "g"),
            "Carbohydrate": (28.2, "g"),
            "Fat": (0.3, "g"),
        },
    },
    {
        "display_name": "Basmati Rice, Cooked",
        "food_type": "cooked",
        "aliases": [
            "basmati rice",
            "cooked basmati rice",
        ],
        "search_priority": 20,
        "nutrients_per_100g": {
            "Calories": (121.0, "kcal"),
            "Protein": (3.5, "g"),
            "Carbohydrate": (25.2, "g"),
            "Fat": (0.4, "g"),
        },
    },
    {
        "display_name": "Pasta, Cooked",
        "food_type": "cooked",
        "aliases": [
            "pasta",
            "cooked pasta",
            "noodles",
        ],
        "search_priority": 20,
        "nutrients_per_100g": {
            "Calories": (158.0, "kcal"),
            "Protein": (5.8, "g"),
            "Carbohydrate": (30.9, "g"),
            "Fat": (0.9, "g"),
        },
    },
    {
        "display_name": "Quinoa, Cooked",
        "food_type": "cooked",
        "aliases": [
            "quinoa",
            "cooked quinoa",
        ],
        "search_priority": 30,
        "nutrients_per_100g": {
            "Calories": (120.0, "kcal"),
            "Protein": (4.4, "g"),
            "Carbohydrate": (21.3, "g"),
            "Fat": (1.9, "g"),
        },
    },
    {
        "display_name": "Whole Wheat Bread",
        "food_type": "prepared",
        "aliases": [
            "bread",
            "whole wheat bread",
            "wheat bread",
        ],
        "search_priority": 30,
        "nutrients_per_100g": {
            "Calories": (247.0, "kcal"),
            "Protein": (12.4, "g"),
            "Carbohydrate": (41.3, "g"),
            "Fat": (4.2, "g"),
        },
    },
    {
        "display_name": "Bagel, Plain",
        "food_type": "prepared",
        "aliases": [
            "bagel",
            "plain bagel",
        ],
        "search_priority": 40,
        "nutrients_per_100g": {
            "Calories": (250.0, "kcal"),
            "Protein": (10.2, "g"),
            "Carbohydrate": (48.9, "g"),
            "Fat": (1.5, "g"),
        },
    },
    {
        "display_name": "Tortilla, Flour",
        "food_type": "prepared",
        "aliases": [
            "tortilla",
            "flour tortilla",
        ],
        "search_priority": 40,
        "nutrients_per_100g": {
            "Calories": (304.0, "kcal"),
            "Protein": (8.9, "g"),
            "Carbohydrate": (50.6, "g"),
            "Fat": (8.4, "g"),
        },
    },
    {
        "display_name": "Oats, Dry",
        "food_type": "raw",
        "aliases": [
            "oats",
            "oatmeal",
            "dry oats",
        ],
        "search_priority": 20,
        "nutrients_per_100g": {
            "Calories": (389.0, "kcal"),
            "Protein": (16.9, "g"),
            "Carbohydrate": (66.3, "g"),
            "Fat": (6.9, "g"),
        },
    },
    {
        "display_name": "Black Beans, Cooked",
        "food_type": "cooked",
        "aliases": [
            "beans",
            "black beans",
            "cooked black beans",
        ],
        "search_priority": 30,
        "nutrients_per_100g": {
            "Calories": (132.0, "kcal"),
            "Protein": (8.9, "g"),
            "Carbohydrate": (23.7, "g"),
            "Fat": (0.5, "g"),
        },
    },
    {
        "display_name": "Pinto Beans, Cooked",
        "food_type": "cooked",
        "aliases": [
            "pinto beans",
            "cooked pinto beans",
        ],
        "search_priority": 35,
        "nutrients_per_100g": {
            "Calories": (143.0, "kcal"),
            "Protein": (9.0, "g"),
            "Carbohydrate": (26.2, "g"),
            "Fat": (0.7, "g"),
        },
    },
    {
        "display_name": "Lentils, Cooked",
        "food_type": "cooked",
        "aliases": [
            "lentils",
            "cooked lentils",
        ],
        "search_priority": 35,
        "nutrients_per_100g": {
            "Calories": (116.0, "kcal"),
            "Protein": (9.0, "g"),
            "Carbohydrate": (20.1, "g"),
            "Fat": (0.4, "g"),
        },
    },
    {
        "display_name": "Potato, Baked",
        "food_type": "cooked",
        "aliases": [
            "potato",
            "potatoes",
            "baked potato",
        ],
        "search_priority": 20,
        "nutrients_per_100g": {
            "Calories": (93.0, "kcal"),
            "Protein": (2.5, "g"),
            "Carbohydrate": (21.2, "g"),
            "Fat": (0.1, "g"),
        },
    },
    {
        "display_name": "Sweet Potato, Baked",
        "food_type": "cooked",
        "aliases": [
            "sweet potato",
            "sweet potatoes",
            "baked sweet potato",
        ],
        "search_priority": 20,
        "nutrients_per_100g": {
            "Calories": (90.0, "kcal"),
            "Protein": (2.0, "g"),
            "Carbohydrate": (20.7, "g"),
            "Fat": (0.2, "g"),
        },
    },
    {
        "display_name": "Banana",
        "food_type": "generic",
        "aliases": [
            "banana",
            "bananas",
        ],
        "search_priority": 10,
        "nutrients_per_100g": {
            "Calories": (89.0, "kcal"),
            "Protein": (1.1, "g"),
            "Carbohydrate": (22.8, "g"),
            "Fat": (0.3, "g"),
        },
    },
    {
        "display_name": "Apple",
        "food_type": "generic",
        "aliases": [
            "apple",
            "apples",
        ],
        "search_priority": 20,
        "nutrients_per_100g": {
            "Calories": (52.0, "kcal"),
            "Protein": (0.3, "g"),
            "Carbohydrate": (13.8, "g"),
            "Fat": (0.2, "g"),
        },
    },
    {
        "display_name": "Orange",
        "food_type": "generic",
        "aliases": [
            "orange",
            "oranges",
        ],
        "search_priority": 20,
        "nutrients_per_100g": {
            "Calories": (47.0, "kcal"),
            "Protein": (0.9, "g"),
            "Carbohydrate": (11.8, "g"),
            "Fat": (0.1, "g"),
        },
    },
    {
        "display_name": "Blueberries",
        "food_type": "generic",
        "aliases": [
            "blueberries",
            "blueberry",
        ],
        "search_priority": 20,
        "nutrients_per_100g": {
            "Calories": (57.0, "kcal"),
            "Protein": (0.7, "g"),
            "Carbohydrate": (14.5, "g"),
            "Fat": (0.3, "g"),
        },
    },
    {
        "display_name": "Strawberries",
        "food_type": "generic",
        "aliases": [
            "strawberries",
            "strawberry",
        ],
        "search_priority": 20,
        "nutrients_per_100g": {
            "Calories": (32.0, "kcal"),
            "Protein": (0.7, "g"),
            "Carbohydrate": (7.7, "g"),
            "Fat": (0.3, "g"),
        },
    },
    {
        "display_name": "Grapes",
        "food_type": "generic",
        "aliases": [
            "grapes",
            "grape",
        ],
        "search_priority": 30,
        "nutrients_per_100g": {
            "Calories": (69.0, "kcal"),
            "Protein": (0.7, "g"),
            "Carbohydrate": (18.1, "g"),
            "Fat": (0.2, "g"),
        },
    },
    {
        "display_name": "Avocado",
        "food_type": "generic",
        "aliases": [
            "avocado",
            "avocados",
        ],
        "search_priority": 20,
        "nutrients_per_100g": {
            "Calories": (160.0, "kcal"),
            "Protein": (2.0, "g"),
            "Carbohydrate": (8.5, "g"),
            "Fat": (14.7, "g"),
        },
    },
    {
        "display_name": "Broccoli, Cooked",
        "food_type": "cooked",
        "aliases": [
            "broccoli",
            "cooked broccoli",
        ],
        "search_priority": 20,
        "nutrients_per_100g": {
            "Calories": (35.0, "kcal"),
            "Protein": (2.4, "g"),
            "Carbohydrate": (7.2, "g"),
            "Fat": (0.4, "g"),
        },
    },
    {
        "display_name": "Spinach",
        "food_type": "generic",
        "aliases": [
            "spinach",
        ],
        "search_priority": 20,
        "nutrients_per_100g": {
            "Calories": (23.0, "kcal"),
            "Protein": (2.9, "g"),
            "Carbohydrate": (3.6, "g"),
            "Fat": (0.4, "g"),
        },
    },
    {
        "display_name": "Romaine Lettuce",
        "food_type": "generic",
        "aliases": [
            "romaine",
            "romaine lettuce",
            "lettuce",
        ],
        "search_priority": 30,
        "nutrients_per_100g": {
            "Calories": (17.0, "kcal"),
            "Protein": (1.2, "g"),
            "Carbohydrate": (3.3, "g"),
            "Fat": (0.3, "g"),
        },
    },
    {
        "display_name": "Green Beans",
        "food_type": "generic",
        "aliases": [
            "green beans",
        ],
        "search_priority": 30,
        "nutrients_per_100g": {
            "Calories": (35.0, "kcal"),
            "Protein": (1.9, "g"),
            "Carbohydrate": (7.9, "g"),
            "Fat": (0.3, "g"),
        },
    },
    {
        "display_name": "Asparagus",
        "food_type": "generic",
        "aliases": [
            "asparagus",
        ],
        "search_priority": 30,
        "nutrients_per_100g": {
            "Calories": (22.0, "kcal"),
            "Protein": (2.4, "g"),
            "Carbohydrate": (4.1, "g"),
            "Fat": (0.2, "g"),
        },
    },
    {
        "display_name": "Carrots",
        "food_type": "generic",
        "aliases": [
            "carrot",
            "carrots",
        ],
        "search_priority": 30,
        "nutrients_per_100g": {
            "Calories": (41.0, "kcal"),
            "Protein": (0.9, "g"),
            "Carbohydrate": (9.6, "g"),
            "Fat": (0.2, "g"),
        },
    },
    {
        "display_name": "Bell Pepper",
        "food_type": "generic",
        "aliases": [
            "bell pepper",
            "peppers",
            "pepper",
        ],
        "search_priority": 30,
        "nutrients_per_100g": {
            "Calories": (31.0, "kcal"),
            "Protein": (1.0, "g"),
            "Carbohydrate": (6.0, "g"),
            "Fat": (0.3, "g"),
        },
    },
    {
        "display_name": "Onion",
        "food_type": "generic",
        "aliases": [
            "onion",
            "onions",
        ],
        "search_priority": 30,
        "nutrients_per_100g": {
            "Calories": (40.0, "kcal"),
            "Protein": (1.1, "g"),
            "Carbohydrate": (9.3, "g"),
            "Fat": (0.1, "g"),
        },
    },
    {
        "display_name": "Tomato",
        "food_type": "generic",
        "aliases": [
            "tomato",
            "tomatoes",
        ],
        "search_priority": 30,
        "nutrients_per_100g": {
            "Calories": (18.0, "kcal"),
            "Protein": (0.9, "g"),
            "Carbohydrate": (3.9, "g"),
            "Fat": (0.2, "g"),
        },
    },
    {
        "display_name": "Olive Oil",
        "food_type": "generic",
        "aliases": [
            "olive oil",
            "oil",
        ],
        "search_priority": 20,
        "nutrients_per_100g": {
            "Calories": (884.0, "kcal"),
            "Protein": (0.0, "g"),
            "Carbohydrate": (0.0, "g"),
            "Fat": (100.0, "g"),
        },
    },
    {
        "display_name": "Avocado Oil",
        "food_type": "generic",
        "aliases": [
            "avocado oil",
        ],
        "search_priority": 30,
        "nutrients_per_100g": {
            "Calories": (884.0, "kcal"),
            "Protein": (0.0, "g"),
            "Carbohydrate": (0.0, "g"),
            "Fat": (100.0, "g"),
        },
    },
    {
        "display_name": "Butter",
        "food_type": "generic",
        "aliases": [
            "butter",
        ],
        "search_priority": 30,
        "nutrients_per_100g": {
            "Calories": (717.0, "kcal"),
            "Protein": (0.9, "g"),
            "Carbohydrate": (0.1, "g"),
            "Fat": (81.1, "g"),
        },
    },
    {
        "display_name": "Peanut Butter",
        "food_type": "generic",
        "aliases": [
            "peanut butter",
            "pb",
        ],
        "search_priority": 20,
        "nutrients_per_100g": {
            "Calories": (588.0, "kcal"),
            "Protein": (25.0, "g"),
            "Carbohydrate": (20.0, "g"),
            "Fat": (50.0, "g"),
        },
    },
    {
        "display_name": "Almonds",
        "food_type": "generic",
        "aliases": [
            "almonds",
            "almond",
        ],
        "search_priority": 30,
        "nutrients_per_100g": {
            "Calories": (579.0, "kcal"),
            "Protein": (21.2, "g"),
            "Carbohydrate": (21.6, "g"),
            "Fat": (49.9, "g"),
        },
    },
    {
        "display_name": "Walnuts",
        "food_type": "generic",
        "aliases": [
            "walnuts",
            "walnut",
        ],
        "search_priority": 30,
        "nutrients_per_100g": {
            "Calories": (654.0, "kcal"),
            "Protein": (15.2, "g"),
            "Carbohydrate": (13.7, "g"),
            "Fat": (65.2, "g"),
        },
    },
    {
        "display_name": "Chicken Thigh, Raw, Skinless",
        "food_type": "raw",
        "aliases": [
            "raw chicken thigh",
            "uncooked chicken thigh",
            "chicken thigh raw",
            "dark meat chicken raw",
        ],
        "search_priority": 35,
        "nutrients_per_100g": {
            "Calories": (143.0, "kcal"),
            "Protein": (18.6, "g"),
            "Carbohydrate": (0.0, "g"),
            "Fat": (7.9, "g"),
        },
    },
    {
        "display_name": "Chicken Drumstick, Cooked",
        "food_type": "cooked",
        "aliases": [
            "chicken drumstick",
            "drumstick",
            "cooked drumstick",
            "chicken leg",
        ],
        "search_priority": 45,
        "nutrients_per_100g": {
            "Calories": (185.0, "kcal"),
            "Protein": (27.0, "g"),
            "Carbohydrate": (0.0, "g"),
            "Fat": (8.0, "g"),
        },
    },
    {
        "display_name": "Turkey Breast, Deli",
        "food_type": "prepared",
        "aliases": [
            "deli turkey",
            "turkey slices",
            "sliced turkey",
            "lunch meat turkey",
            "turkey deli meat",
        ],
        "search_priority": 28,
        "nutrients_per_100g": {
            "Calories": (104.0, "kcal"),
            "Protein": (17.0, "g"),
            "Carbohydrate": (4.0, "g"),
            "Fat": (2.0, "g"),
        },
    },
    {
        "display_name": "Turkey, Ground 93/7",
        "food_type": "raw",
        "aliases": [
            "ground turkey",
            "lean ground turkey",
            "93/7 turkey",
            "93 7 turkey",
            "turkey mince",
        ],
        "search_priority": 22,
        "nutrients_per_100g": {
            "Calories": (150.0, "kcal"),
            "Protein": (22.0, "g"),
            "Carbohydrate": (0.0, "g"),
            "Fat": (7.0, "g"),
        },
    },
    {
        "display_name": "Turkey, Ground 85/15",
        "food_type": "raw",
        "aliases": [
            "ground turkey 85/15",
            "85/15 turkey",
            "85 15 turkey",
            "fattier ground turkey",
        ],
        "search_priority": 34,
        "nutrients_per_100g": {
            "Calories": (212.0, "kcal"),
            "Protein": (18.0, "g"),
            "Carbohydrate": (0.0, "g"),
            "Fat": (15.0, "g"),
        },
    },
    {
        "display_name": "Pork Chop, Cooked",
        "food_type": "cooked",
        "aliases": ["pork chop", "cooked pork chop", "pork chops"],
        "search_priority": 45,
        "nutrients_per_100g": {
            "Calories": (231.0, "kcal"),
            "Protein": (25.0, "g"),
            "Carbohydrate": (0.0, "g"),
            "Fat": (14.0, "g"),
        },
    },
    {
        "display_name": "Ham, Deli",
        "food_type": "prepared",
        "aliases": ["ham", "deli ham", "sliced ham", "lunch meat ham"],
        "search_priority": 45,
        "nutrients_per_100g": {
            "Calories": (145.0, "kcal"),
            "Protein": (20.0, "g"),
            "Carbohydrate": (2.0, "g"),
            "Fat": (6.0, "g"),
        },
    },
    {
        "display_name": "Ribeye Steak, Cooked",
        "food_type": "cooked",
        "aliases": ["ribeye", "ribeye steak", "fatty steak", "cooked ribeye"],
        "search_priority": 55,
        "nutrients_per_100g": {
            "Calories": (291.0, "kcal"),
            "Protein": (24.0, "g"),
            "Carbohydrate": (0.0, "g"),
            "Fat": (21.0, "g"),
        },
    },
    {
        "display_name": "Beef, Ground 93/7",
        "food_type": "raw",
        "aliases": [
            "ground beef 93/7",
            "93/7 beef",
            "93 7 beef",
            "extra lean ground beef",
        ],
        "search_priority": 24,
        "nutrients_per_100g": {
            "Calories": (152.0, "kcal"),
            "Protein": (21.0, "g"),
            "Carbohydrate": (0.0, "g"),
            "Fat": (7.0, "g"),
        },
    },
    {
        "display_name": "Beef, Ground 85/15",
        "food_type": "raw",
        "aliases": ["ground beef 85/15", "85/15 beef", "85 15 beef", "hamburger meat"],
        "search_priority": 32,
        "nutrients_per_100g": {
            "Calories": (215.0, "kcal"),
            "Protein": (18.0, "g"),
            "Carbohydrate": (0.0, "g"),
            "Fat": (15.0, "g"),
        },
    },
    {
        "display_name": "Bacon, Cooked",
        "food_type": "prepared",
        "aliases": ["bacon", "cooked bacon", "bacon strips"],
        "search_priority": 55,
        "nutrients_per_100g": {
            "Calories": (541.0, "kcal"),
            "Protein": (37.0, "g"),
            "Carbohydrate": (1.4, "g"),
            "Fat": (42.0, "g"),
        },
    },
    {
        "display_name": "Turkey Bacon",
        "food_type": "prepared",
        "aliases": ["turkey bacon", "bacon turkey"],
        "search_priority": 55,
        "nutrients_per_100g": {
            "Calories": (226.0, "kcal"),
            "Protein": (29.0, "g"),
            "Carbohydrate": (1.0, "g"),
            "Fat": (12.0, "g"),
        },
    },
    {
        "display_name": "Chicken Sausage",
        "food_type": "prepared",
        "aliases": ["chicken sausage", "sausage chicken"],
        "search_priority": 60,
        "nutrients_per_100g": {
            "Calories": (180.0, "kcal"),
            "Protein": (17.0, "g"),
            "Carbohydrate": (2.0, "g"),
            "Fat": (11.0, "g"),
        },
    },
    {
        "display_name": "Lean Ham",
        "food_type": "prepared",
        "aliases": ["lean ham", "low fat ham"],
        "search_priority": 58,
        "nutrients_per_100g": {
            "Calories": (120.0, "kcal"),
            "Protein": (20.0, "g"),
            "Carbohydrate": (2.0, "g"),
            "Fat": (4.0, "g"),
        },
    },
    {
        "display_name": "Tuna, Canned in Oil",
        "food_type": "prepared",
        "aliases": ["tuna in oil", "canned tuna oil", "oil packed tuna"],
        "search_priority": 35,
        "nutrients_per_100g": {
            "Calories": (198.0, "kcal"),
            "Protein": (29.0, "g"),
            "Carbohydrate": (0.0, "g"),
            "Fat": (8.0, "g"),
        },
    },
    {
        "display_name": "Salmon, Raw",
        "food_type": "raw",
        "aliases": ["raw salmon", "salmon filet raw", "salmon fillet raw"],
        "search_priority": 38,
        "nutrients_per_100g": {
            "Calories": (208.0, "kcal"),
            "Protein": (20.0, "g"),
            "Carbohydrate": (0.0, "g"),
            "Fat": (13.0, "g"),
        },
    },
    {
        "display_name": "Sardines, Canned",
        "food_type": "prepared",
        "aliases": ["sardines", "canned sardines"],
        "search_priority": 50,
        "nutrients_per_100g": {
            "Calories": (208.0, "kcal"),
            "Protein": (25.0, "g"),
            "Carbohydrate": (0.0, "g"),
            "Fat": (11.0, "g"),
        },
    },
    {
        "display_name": "Greek Yogurt, Plain Nonfat",
        "food_type": "generic",
        "aliases": [
            "nonfat greek yogurt",
            "fat free greek yogurt",
            "0% greek yogurt",
            "plain nonfat yogurt",
        ],
        "search_priority": 22,
        "nutrients_per_100g": {
            "Calories": (59.0, "kcal"),
            "Protein": (10.3, "g"),
            "Carbohydrate": (3.6, "g"),
            "Fat": (0.4, "g"),
        },
    },
    {
        "display_name": "Greek Yogurt, Plain 2%",
        "food_type": "generic",
        "aliases": ["2% greek yogurt", "plain 2% yogurt", "low fat greek yogurt"],
        "search_priority": 24,
        "nutrients_per_100g": {
            "Calories": (73.0, "kcal"),
            "Protein": (9.0, "g"),
            "Carbohydrate": (3.9, "g"),
            "Fat": (2.0, "g"),
        },
    },
    {
        "display_name": "Greek Yogurt, Vanilla",
        "food_type": "generic",
        "aliases": ["vanilla greek yogurt", "greek yogurt vanilla", "vanilla yogurt"],
        "search_priority": 35,
        "nutrients_per_100g": {
            "Calories": (95.0, "kcal"),
            "Protein": (8.5, "g"),
            "Carbohydrate": (12.0, "g"),
            "Fat": (1.5, "g"),
        },
    },
    {
        "display_name": "Cottage Cheese, Full Fat",
        "food_type": "generic",
        "aliases": [
            "full fat cottage cheese",
            "4% cottage cheese",
            "regular cottage cheese",
        ],
        "search_priority": 35,
        "nutrients_per_100g": {
            "Calories": (103.0, "kcal"),
            "Protein": (11.5, "g"),
            "Carbohydrate": (3.4, "g"),
            "Fat": (4.3, "g"),
        },
    },
    {
        "display_name": "Milk, Skim",
        "food_type": "generic",
        "aliases": ["skim milk", "nonfat milk", "fat free milk"],
        "search_priority": 32,
        "nutrients_per_100g": {
            "Calories": (34.0, "kcal"),
            "Protein": (3.4, "g"),
            "Carbohydrate": (5.0, "g"),
            "Fat": (0.1, "g"),
        },
    },
    {
        "display_name": "Mozzarella Cheese",
        "food_type": "generic",
        "aliases": ["mozzarella", "mozzarella cheese", "part skim mozzarella"],
        "search_priority": 55,
        "nutrients_per_100g": {
            "Calories": (280.0, "kcal"),
            "Protein": (28.0, "g"),
            "Carbohydrate": (3.1, "g"),
            "Fat": (17.0, "g"),
        },
    },
    {
        "display_name": "Parmesan Cheese",
        "food_type": "generic",
        "aliases": ["parmesan", "parmesan cheese", "grated parmesan"],
        "search_priority": 60,
        "nutrients_per_100g": {
            "Calories": (431.0, "kcal"),
            "Protein": (38.0, "g"),
            "Carbohydrate": (4.1, "g"),
            "Fat": (29.0, "g"),
        },
    },
    {
        "display_name": "Cream Cheese",
        "food_type": "generic",
        "aliases": ["cream cheese"],
        "search_priority": 65,
        "nutrients_per_100g": {
            "Calories": (342.0, "kcal"),
            "Protein": (6.0, "g"),
            "Carbohydrate": (4.0, "g"),
            "Fat": (34.0, "g"),
        },
    },
    {
        "display_name": "Whole Wheat Pasta, Cooked",
        "food_type": "cooked",
        "aliases": [
            "whole wheat pasta",
            "whole grain pasta",
            "wheat pasta",
            "whole wheat noodles",
        ],
        "search_priority": 42,
        "nutrients_per_100g": {
            "Calories": (124.0, "kcal"),
            "Protein": (5.3, "g"),
            "Carbohydrate": (26.0, "g"),
            "Fat": (0.5, "g"),
        },
    },
    {
        "display_name": "Couscous, Cooked",
        "food_type": "cooked",
        "aliases": ["couscous", "cooked couscous"],
        "search_priority": 48,
        "nutrients_per_100g": {
            "Calories": (112.0, "kcal"),
            "Protein": (3.8, "g"),
            "Carbohydrate": (23.2, "g"),
            "Fat": (0.2, "g"),
        },
    },
    {
        "display_name": "Cream of Wheat, Cooked",
        "food_type": "cooked",
        "aliases": ["cream of wheat", "farina", "hot cereal"],
        "search_priority": 48,
        "nutrients_per_100g": {
            "Calories": (50.0, "kcal"),
            "Protein": (1.4, "g"),
            "Carbohydrate": (10.7, "g"),
            "Fat": (0.2, "g"),
        },
    },
    {
        "display_name": "White Bread",
        "food_type": "generic",
        "aliases": ["white bread", "bread", "toast"],
        "search_priority": 42,
        "nutrients_per_100g": {
            "Calories": (265.0, "kcal"),
            "Protein": (9.0, "g"),
            "Carbohydrate": (49.0, "g"),
            "Fat": (3.2, "g"),
        },
    },
    {
        "display_name": "Sourdough Bread",
        "food_type": "generic",
        "aliases": ["sourdough", "sourdough bread"],
        "search_priority": 43,
        "nutrients_per_100g": {
            "Calories": (289.0, "kcal"),
            "Protein": (11.0, "g"),
            "Carbohydrate": (56.0, "g"),
            "Fat": (1.8, "g"),
        },
    },
    {
        "display_name": "English Muffin",
        "food_type": "generic",
        "aliases": ["english muffin", "muffin bread"],
        "search_priority": 45,
        "nutrients_per_100g": {
            "Calories": (227.0, "kcal"),
            "Protein": (8.9, "g"),
            "Carbohydrate": (44.0, "g"),
            "Fat": (1.7, "g"),
        },
    },
    {
        "display_name": "Corn Tortilla",
        "food_type": "generic",
        "aliases": ["corn tortilla", "taco shell soft", "corn wrap"],
        "search_priority": 42,
        "nutrients_per_100g": {
            "Calories": (218.0, "kcal"),
            "Protein": (5.7, "g"),
            "Carbohydrate": (44.6, "g"),
            "Fat": (2.9, "g"),
        },
    },
    {
        "display_name": "Pita Bread",
        "food_type": "generic",
        "aliases": ["pita", "pita bread"],
        "search_priority": 48,
        "nutrients_per_100g": {
            "Calories": (275.0, "kcal"),
            "Protein": (9.1, "g"),
            "Carbohydrate": (55.0, "g"),
            "Fat": (1.2, "g"),
        },
    },
    {
        "display_name": "Kidney Beans, Cooked",
        "food_type": "cooked",
        "aliases": ["kidney beans", "red beans", "cooked kidney beans"],
        "search_priority": 46,
        "nutrients_per_100g": {
            "Calories": (127.0, "kcal"),
            "Protein": (8.7, "g"),
            "Carbohydrate": (22.8, "g"),
            "Fat": (0.5, "g"),
        },
    },
    {
        "display_name": "Chickpeas, Cooked",
        "food_type": "cooked",
        "aliases": ["chickpeas", "garbanzo beans", "cooked chickpeas"],
        "search_priority": 45,
        "nutrients_per_100g": {
            "Calories": (164.0, "kcal"),
            "Protein": (8.9, "g"),
            "Carbohydrate": (27.4, "g"),
            "Fat": (2.6, "g"),
        },
    },
    {
        "display_name": "Edamame",
        "food_type": "prepared",
        "aliases": ["edamame", "soybeans", "shelled edamame"],
        "search_priority": 50,
        "nutrients_per_100g": {
            "Calories": (121.0, "kcal"),
            "Protein": (11.9, "g"),
            "Carbohydrate": (8.9, "g"),
            "Fat": (5.2, "g"),
        },
    },
    {
        "display_name": "Raspberries",
        "food_type": "generic",
        "aliases": ["raspberries", "raspberry"],
        "search_priority": 45,
        "nutrients_per_100g": {
            "Calories": (52.0, "kcal"),
            "Protein": (1.2, "g"),
            "Carbohydrate": (11.9, "g"),
            "Fat": (0.7, "g"),
        },
    },
    {
        "display_name": "Pineapple",
        "food_type": "generic",
        "aliases": ["pineapple", "pineapple chunks"],
        "search_priority": 45,
        "nutrients_per_100g": {
            "Calories": (50.0, "kcal"),
            "Protein": (0.5, "g"),
            "Carbohydrate": (13.1, "g"),
            "Fat": (0.1, "g"),
        },
    },
    {
        "display_name": "Mango",
        "food_type": "generic",
        "aliases": ["mango", "mango chunks"],
        "search_priority": 45,
        "nutrients_per_100g": {
            "Calories": (60.0, "kcal"),
            "Protein": (0.8, "g"),
            "Carbohydrate": (15.0, "g"),
            "Fat": (0.4, "g"),
        },
    },
    {
        "display_name": "Watermelon",
        "food_type": "generic",
        "aliases": ["watermelon"],
        "search_priority": 45,
        "nutrients_per_100g": {
            "Calories": (30.0, "kcal"),
            "Protein": (0.6, "g"),
            "Carbohydrate": (7.6, "g"),
            "Fat": (0.2, "g"),
        },
    },
    {
        "display_name": "Pear",
        "food_type": "generic",
        "aliases": ["pear", "pears"],
        "search_priority": 45,
        "nutrients_per_100g": {
            "Calories": (57.0, "kcal"),
            "Protein": (0.4, "g"),
            "Carbohydrate": (15.2, "g"),
            "Fat": (0.1, "g"),
        },
    },
    {
        "display_name": "Peach",
        "food_type": "generic",
        "aliases": ["peach", "peaches"],
        "search_priority": 45,
        "nutrients_per_100g": {
            "Calories": (39.0, "kcal"),
            "Protein": (0.9, "g"),
            "Carbohydrate": (9.5, "g"),
            "Fat": (0.3, "g"),
        },
    },
    {
        "display_name": "Spring Mix",
        "food_type": "generic",
        "aliases": ["spring mix", "mixed greens", "salad greens"],
        "search_priority": 45,
        "nutrients_per_100g": {
            "Calories": (20.0, "kcal"),
            "Protein": (2.0, "g"),
            "Carbohydrate": (3.5, "g"),
            "Fat": (0.3, "g"),
        },
    },
    {
        "display_name": "Cucumber",
        "food_type": "generic",
        "aliases": ["cucumber", "cucumbers"],
        "search_priority": 45,
        "nutrients_per_100g": {
            "Calories": (15.0, "kcal"),
            "Protein": (0.7, "g"),
            "Carbohydrate": (3.6, "g"),
            "Fat": (0.1, "g"),
        },
    },
    {
        "display_name": "Zucchini",
        "food_type": "generic",
        "aliases": ["zucchini", "courgette"],
        "search_priority": 45,
        "nutrients_per_100g": {
            "Calories": (17.0, "kcal"),
            "Protein": (1.2, "g"),
            "Carbohydrate": (3.1, "g"),
            "Fat": (0.3, "g"),
        },
    },
    {
        "display_name": "Mushrooms",
        "food_type": "generic",
        "aliases": ["mushrooms", "button mushrooms"],
        "search_priority": 45,
        "nutrients_per_100g": {
            "Calories": (22.0, "kcal"),
            "Protein": (3.1, "g"),
            "Carbohydrate": (3.3, "g"),
            "Fat": (0.3, "g"),
        },
    },
    {
        "display_name": "Cauliflower",
        "food_type": "generic",
        "aliases": ["cauliflower"],
        "search_priority": 45,
        "nutrients_per_100g": {
            "Calories": (25.0, "kcal"),
            "Protein": (1.9, "g"),
            "Carbohydrate": (5.0, "g"),
            "Fat": (0.3, "g"),
        },
    },
    {
        "display_name": "Brussels Sprouts",
        "food_type": "generic",
        "aliases": ["brussels sprouts", "brussel sprouts"],
        "search_priority": 45,
        "nutrients_per_100g": {
            "Calories": (43.0, "kcal"),
            "Protein": (3.4, "g"),
            "Carbohydrate": (9.0, "g"),
            "Fat": (0.3, "g"),
        },
    },
    {
        "display_name": "Corn",
        "food_type": "generic",
        "aliases": ["corn", "sweet corn"],
        "search_priority": 45,
        "nutrients_per_100g": {
            "Calories": (96.0, "kcal"),
            "Protein": (3.4, "g"),
            "Carbohydrate": (21.0, "g"),
            "Fat": (1.5, "g"),
        },
    },
    {
        "display_name": "Peas",
        "food_type": "generic",
        "aliases": ["peas", "green peas"],
        "search_priority": 45,
        "nutrients_per_100g": {
            "Calories": (84.0, "kcal"),
            "Protein": (5.4, "g"),
            "Carbohydrate": (15.0, "g"),
            "Fat": (0.4, "g"),
        },
    },
    {
        "display_name": "Coconut Oil",
        "food_type": "generic",
        "aliases": ["coconut oil"],
        "search_priority": 62,
        "nutrients_per_100g": {
            "Calories": (892.0, "kcal"),
            "Protein": (0.0, "g"),
            "Carbohydrate": (0.0, "g"),
            "Fat": (100.0, "g"),
        },
    },
    {
        "display_name": "Almond Butter",
        "food_type": "generic",
        "aliases": ["almond butter"],
        "search_priority": 48,
        "nutrients_per_100g": {
            "Calories": (614.0, "kcal"),
            "Protein": (21.0, "g"),
            "Carbohydrate": (19.0, "g"),
            "Fat": (56.0, "g"),
        },
    },
    {
        "display_name": "Cashews",
        "food_type": "generic",
        "aliases": ["cashews", "cashew nuts"],
        "search_priority": 48,
        "nutrients_per_100g": {
            "Calories": (553.0, "kcal"),
            "Protein": (18.0, "g"),
            "Carbohydrate": (30.0, "g"),
            "Fat": (44.0, "g"),
        },
    },
    {
        "display_name": "Chia Seeds",
        "food_type": "generic",
        "aliases": ["chia seeds", "chia"],
        "search_priority": 55,
        "nutrients_per_100g": {
            "Calories": (486.0, "kcal"),
            "Protein": (16.5, "g"),
            "Carbohydrate": (42.0, "g"),
            "Fat": (30.7, "g"),
        },
    },
    {
        "display_name": "Flaxseed",
        "food_type": "generic",
        "aliases": ["flaxseed", "flax seed", "ground flaxseed"],
        "search_priority": 55,
        "nutrients_per_100g": {
            "Calories": (534.0, "kcal"),
            "Protein": (18.3, "g"),
            "Carbohydrate": (28.9, "g"),
            "Fat": (42.2, "g"),
        },
    },
    {
        "display_name": "Mayonnaise",
        "food_type": "prepared",
        "aliases": ["mayonnaise", "mayo"],
        "search_priority": 62,
        "nutrients_per_100g": {
            "Calories": (680.0, "kcal"),
            "Protein": (1.0, "g"),
            "Carbohydrate": (0.6, "g"),
            "Fat": (75.0, "g"),
        },
    },
    {
        "display_name": "Ketchup",
        "food_type": "prepared",
        "aliases": ["ketchup", "catsup"],
        "search_priority": 60,
        "nutrients_per_100g": {
            "Calories": (112.0, "kcal"),
            "Protein": (1.3, "g"),
            "Carbohydrate": (26.0, "g"),
            "Fat": (0.2, "g"),
        },
    },
    {
        "display_name": "Mustard",
        "food_type": "prepared",
        "aliases": ["mustard", "yellow mustard"],
        "search_priority": 60,
        "nutrients_per_100g": {
            "Calories": (66.0, "kcal"),
            "Protein": (4.4, "g"),
            "Carbohydrate": (5.8, "g"),
            "Fat": (3.3, "g"),
        },
    },
    {
        "display_name": "BBQ Sauce",
        "food_type": "prepared",
        "aliases": ["bbq sauce", "barbecue sauce", "barbeque sauce"],
        "search_priority": 60,
        "nutrients_per_100g": {
            "Calories": (172.0, "kcal"),
            "Protein": (0.8, "g"),
            "Carbohydrate": (40.0, "g"),
            "Fat": (0.6, "g"),
        },
    },
    {
        "display_name": "Ranch Dressing",
        "food_type": "prepared",
        "aliases": ["ranch", "ranch dressing", "dressing ranch"],
        "search_priority": 35,
        "nutrients_per_100g": {
            "Calories": (430.0, "kcal"),
            "Protein": (1.0, "g"),
            "Carbohydrate": (6.0, "g"),
            "Fat": (45.0, "g"),
        },
    },
    {
        "display_name": "Italian Dressing",
        "food_type": "prepared",
        "aliases": ["italian dressing", "dressing"],
        "search_priority": 45,
        "nutrients_per_100g": {
            "Calories": (292.0, "kcal"),
            "Protein": (0.4, "g"),
            "Carbohydrate": (9.0, "g"),
            "Fat": (28.0, "g"),
        },
    },
    {
        "display_name": "Salsa",
        "food_type": "prepared",
        "aliases": ["salsa", "pico de gallo"],
        "search_priority": 40,
        "nutrients_per_100g": {
            "Calories": (36.0, "kcal"),
            "Protein": (1.5, "g"),
            "Carbohydrate": (7.0, "g"),
            "Fat": (0.2, "g"),
        },
    },
    {
        "display_name": "Soy Sauce",
        "food_type": "prepared",
        "aliases": ["soy sauce", "soy"],
        "search_priority": 65,
        "nutrients_per_100g": {
            "Calories": (53.0, "kcal"),
            "Protein": (8.0, "g"),
            "Carbohydrate": (4.9, "g"),
            "Fat": (0.6, "g"),
        },
    },
    {
        "display_name": "Hot Sauce",
        "food_type": "prepared",
        "aliases": ["hot sauce", "buffalo sauce"],
        "search_priority": 65,
        "nutrients_per_100g": {
            "Calories": (12.0, "kcal"),
            "Protein": (0.9, "g"),
            "Carbohydrate": (1.8, "g"),
            "Fat": (0.4, "g"),
        },
    },
    {
        "display_name": "Honey",
        "food_type": "generic",
        "aliases": ["honey"],
        "search_priority": 55,
        "nutrients_per_100g": {
            "Calories": (304.0, "kcal"),
            "Protein": (0.3, "g"),
            "Carbohydrate": (82.4, "g"),
            "Fat": (0.0, "g"),
        },
    },
    {
        "display_name": "Maple Syrup",
        "food_type": "generic",
        "aliases": ["maple syrup", "syrup"],
        "search_priority": 55,
        "nutrients_per_100g": {
            "Calories": (260.0, "kcal"),
            "Protein": (0.0, "g"),
            "Carbohydrate": (67.0, "g"),
            "Fat": (0.1, "g"),
        },
    },
    {
        "display_name": "Granola",
        "food_type": "generic",
        "aliases": ["granola"],
        "search_priority": 50,
        "nutrients_per_100g": {
            "Calories": (471.0, "kcal"),
            "Protein": (10.0, "g"),
            "Carbohydrate": (64.0, "g"),
            "Fat": (20.0, "g"),
        },
    },
    {
        "display_name": "Cereal, Generic",
        "food_type": "generic",
        "aliases": ["cereal", "breakfast cereal"],
        "search_priority": 50,
        "nutrients_per_100g": {
            "Calories": (379.0, "kcal"),
            "Protein": (8.0, "g"),
            "Carbohydrate": (84.0, "g"),
            "Fat": (1.5, "g"),
        },
    },
    {
        "display_name": "Protein Bar, Generic",
        "food_type": "generic",
        "aliases": ["protein bar", "protein bars", "bar protein"],
        "search_priority": 50,
        "nutrients_per_100g": {
            "Calories": (350.0, "kcal"),
            "Protein": (30.0, "g"),
            "Carbohydrate": (35.0, "g"),
            "Fat": (10.0, "g"),
        },
    },
    {
        "display_name": "Rice Cakes",
        "food_type": "generic",
        "aliases": ["rice cakes", "rice cake"],
        "search_priority": 50,
        "nutrients_per_100g": {
            "Calories": (387.0, "kcal"),
            "Protein": (8.0, "g"),
            "Carbohydrate": (82.0, "g"),
            "Fat": (3.0, "g"),
        },
    },
    {
        "display_name": "Pretzels",
        "food_type": "generic",
        "aliases": ["pretzels", "pretzel"],
        "search_priority": 50,
        "nutrients_per_100g": {
            "Calories": (380.0, "kcal"),
            "Protein": (10.0, "g"),
            "Carbohydrate": (80.0, "g"),
            "Fat": (3.0, "g"),
        },
    },
    {
        "display_name": "Popcorn, Air-Popped",
        "food_type": "prepared",
        "aliases": ["popcorn", "air popped popcorn", "plain popcorn"],
        "search_priority": 50,
        "nutrients_per_100g": {
            "Calories": (387.0, "kcal"),
            "Protein": (13.0, "g"),
            "Carbohydrate": (78.0, "g"),
            "Fat": (4.5, "g"),
        },
    },
    {
        "display_name": "Crackers, Generic",
        "food_type": "generic",
        "aliases": ["crackers", "cracker"],
        "search_priority": 55,
        "nutrients_per_100g": {
            "Calories": (502.0, "kcal"),
            "Protein": (8.0, "g"),
            "Carbohydrate": (61.0, "g"),
            "Fat": (25.0, "g"),
        },
    },
    {
        "display_name": "Hummus",
        "food_type": "prepared",
        "aliases": ["hummus"],
        "search_priority": 45,
        "nutrients_per_100g": {
            "Calories": (166.0, "kcal"),
            "Protein": (7.9, "g"),
            "Carbohydrate": (14.3, "g"),
            "Fat": (9.6, "g"),
        },
    },
    {
        "display_name": "Chicken Tenderloins, Raw",
        "food_type": "raw",
        "aliases": [
            "chicken tenderloins raw",
            "raw chicken tenders",
            "raw chicken tenderloin",
        ],
        "search_priority": 50,
        "nutrients_per_100g": {
            "Calories": (106.0, "kcal"),
            "Protein": (23.1, "g"),
            "Carbohydrate": (0.0, "g"),
            "Fat": (1.2, "g"),
        },
    },
    {
        "display_name": "Chicken Tenderloins, Cooked",
        "food_type": "cooked",
        "aliases": [
            "chicken tenderloins",
            "chicken tenders",
            "cooked chicken tenders",
            "cooked chicken tenderloin",
        ],
        "search_priority": 45,
        "nutrients_per_100g": {
            "Calories": (153.0, "kcal"),
            "Protein": (30.2, "g"),
            "Carbohydrate": (0.0, "g"),
            "Fat": (3.1, "g"),
        },
    },
    {
        "display_name": "Chicken, Rotisserie, Meat Only",
        "food_type": "prepared",
        "aliases": [
            "rotisserie chicken",
            "rotisserie chicken meat",
            "chicken rotisserie meat",
        ],
        "search_priority": 45,
        "nutrients_per_100g": {
            "Calories": (190.0, "kcal"),
            "Protein": (28.0, "g"),
            "Carbohydrate": (0.0, "g"),
            "Fat": (8.0, "g"),
        },
    },
    {
        "display_name": "Chicken Breast, Deli",
        "food_type": "prepared",
        "aliases": [
            "deli chicken",
            "deli chicken breast",
            "sliced chicken breast",
        ],
        "search_priority": 55,
        "nutrients_per_100g": {
            "Calories": (110.0, "kcal"),
            "Protein": (22.0, "g"),
            "Carbohydrate": (2.0, "g"),
            "Fat": (2.0, "g"),
        },
    },
    {
        "display_name": "Chicken, Canned in Water",
        "food_type": "prepared",
        "aliases": [
            "canned chicken",
            "canned chicken breast",
            "chicken in water",
        ],
        "search_priority": 50,
        "nutrients_per_100g": {
            "Calories": (120.0, "kcal"),
            "Protein": (25.0, "g"),
            "Carbohydrate": (0.0, "g"),
            "Fat": (2.0, "g"),
        },
    },
    {
        "display_name": "Ground Chicken, Raw",
        "food_type": "raw",
        "aliases": [
            "ground chicken",
            "raw ground chicken",
        ],
        "search_priority": 55,
        "nutrients_per_100g": {
            "Calories": (143.0, "kcal"),
            "Protein": (17.0, "g"),
            "Carbohydrate": (0.0, "g"),
            "Fat": (8.0, "g"),
        },
    },
    {
        "display_name": "Turkey Cutlet, Cooked",
        "food_type": "cooked",
        "aliases": [
            "turkey cutlet",
            "cooked turkey cutlet",
            "turkey cutlets",
        ],
        "search_priority": 55,
        "nutrients_per_100g": {
            "Calories": (135.0, "kcal"),
            "Protein": (29.0, "g"),
            "Carbohydrate": (0.0, "g"),
            "Fat": (1.5, "g"),
        },
    },
    {
        "display_name": "Turkey Sausage, Cooked",
        "food_type": "prepared",
        "aliases": [
            "turkey sausage",
            "cooked turkey sausage",
        ],
        "search_priority": 65,
        "nutrients_per_100g": {
            "Calories": (196.0, "kcal"),
            "Protein": (24.0, "g"),
            "Carbohydrate": (2.0, "g"),
            "Fat": (10.0, "g"),
        },
    },
    {
        "display_name": "Beef Top Round, Cooked",
        "food_type": "cooked",
        "aliases": [
            "top round beef",
            "beef top round",
            "cooked top round",
        ],
        "search_priority": 60,
        "nutrients_per_100g": {
            "Calories": (180.0, "kcal"),
            "Protein": (29.0, "g"),
            "Carbohydrate": (0.0, "g"),
            "Fat": (6.0, "g"),
        },
    },
    {
        "display_name": "Beef Chuck Roast, Cooked",
        "food_type": "cooked",
        "aliases": [
            "chuck roast",
            "beef chuck roast",
            "cooked chuck roast",
        ],
        "search_priority": 70,
        "nutrients_per_100g": {
            "Calories": (250.0, "kcal"),
            "Protein": (27.0, "g"),
            "Carbohydrate": (0.0, "g"),
            "Fat": (16.0, "g"),
        },
    },
    {
        "display_name": "Beef Flank Steak, Cooked",
        "food_type": "cooked",
        "aliases": [
            "flank steak",
            "beef flank steak",
            "cooked flank steak",
        ],
        "search_priority": 60,
        "nutrients_per_100g": {
            "Calories": (192.0, "kcal"),
            "Protein": (28.0, "g"),
            "Carbohydrate": (0.0, "g"),
            "Fat": (8.0, "g"),
        },
    },
    {
        "display_name": "Pork Loin Chop, Cooked",
        "food_type": "cooked",
        "aliases": [
            "pork loin chop",
            "cooked pork loin chop",
            "pork loin chops",
        ],
        "search_priority": 65,
        "nutrients_per_100g": {
            "Calories": (196.0, "kcal"),
            "Protein": (29.0, "g"),
            "Carbohydrate": (0.0, "g"),
            "Fat": (7.0, "g"),
        },
    },
    {
        "display_name": "Pork Shoulder, Cooked",
        "food_type": "cooked",
        "aliases": [
            "pork shoulder",
            "cooked pork shoulder",
            "pulled pork plain",
        ],
        "search_priority": 80,
        "nutrients_per_100g": {
            "Calories": (269.0, "kcal"),
            "Protein": (25.0, "g"),
            "Carbohydrate": (0.0, "g"),
            "Fat": (18.0, "g"),
        },
    },
    {
        "display_name": "Tuna Steak, Cooked",
        "food_type": "cooked",
        "aliases": [
            "tuna steak",
            "cooked tuna steak",
            "ahi tuna cooked",
        ],
        "search_priority": 55,
        "nutrients_per_100g": {
            "Calories": (132.0, "kcal"),
            "Protein": (28.0, "g"),
            "Carbohydrate": (0.0, "g"),
            "Fat": (1.3, "g"),
        },
    },
    {
        "display_name": "Mahi Mahi, Cooked",
        "food_type": "cooked",
        "aliases": [
            "mahi mahi",
            "cooked mahi mahi",
        ],
        "search_priority": 60,
        "nutrients_per_100g": {
            "Calories": (109.0, "kcal"),
            "Protein": (24.0, "g"),
            "Carbohydrate": (0.0, "g"),
            "Fat": (0.9, "g"),
        },
    },
    {
        "display_name": "Halibut, Cooked",
        "food_type": "cooked",
        "aliases": [
            "halibut",
            "cooked halibut",
        ],
        "search_priority": 60,
        "nutrients_per_100g": {
            "Calories": (140.0, "kcal"),
            "Protein": (27.0, "g"),
            "Carbohydrate": (0.0, "g"),
            "Fat": (2.9, "g"),
        },
    },
    {
        "display_name": "Crab Meat, Cooked",
        "food_type": "cooked",
        "aliases": [
            "crab",
            "crab meat",
            "cooked crab",
        ],
        "search_priority": 65,
        "nutrients_per_100g": {
            "Calories": (97.0, "kcal"),
            "Protein": (19.0, "g"),
            "Carbohydrate": (0.0, "g"),
            "Fat": (1.5, "g"),
        },
    },
    {
        "display_name": "Scallops, Cooked",
        "food_type": "cooked",
        "aliases": [
            "scallops",
            "cooked scallops",
        ],
        "search_priority": 65,
        "nutrients_per_100g": {
            "Calories": (111.0, "kcal"),
            "Protein": (20.5, "g"),
            "Carbohydrate": (5.4, "g"),
            "Fat": (0.8, "g"),
        },
    },
    {
        "display_name": "Tofu, Firm",
        "food_type": "prepared",
        "aliases": [
            "tofu",
            "firm tofu",
        ],
        "search_priority": 55,
        "nutrients_per_100g": {
            "Calories": (144.0, "kcal"),
            "Protein": (17.0, "g"),
            "Carbohydrate": (2.8, "g"),
            "Fat": (8.7, "g"),
        },
    },
    {
        "display_name": "Tempeh",
        "food_type": "prepared",
        "aliases": [
            "tempeh",
            "soy tempeh",
        ],
        "search_priority": 65,
        "nutrients_per_100g": {
            "Calories": (192.0, "kcal"),
            "Protein": (20.3, "g"),
            "Carbohydrate": (7.6, "g"),
            "Fat": (10.8, "g"),
        },
    },
    {
        "display_name": "Egg, Hard-Boiled",
        "food_type": "generic",
        "aliases": [
            "hard boiled egg",
            "hard boiled eggs",
            "boiled egg",
        ],
        "search_priority": 40,
        "nutrients_per_100g": {
            "Calories": (155.0, "kcal"),
            "Protein": (12.6, "g"),
            "Carbohydrate": (1.1, "g"),
            "Fat": (10.6, "g"),
        },
    },
    {
        "display_name": "Skyr, Plain Nonfat",
        "food_type": "generic",
        "aliases": [
            "skyr",
            "plain skyr",
            "nonfat skyr",
            "icelandic yogurt",
        ],
        "search_priority": 45,
        "nutrients_per_100g": {
            "Calories": (63.0, "kcal"),
            "Protein": (11.0, "g"),
            "Carbohydrate": (4.0, "g"),
            "Fat": (0.2, "g"),
        },
    },
    {
        "display_name": "Cottage Cheese, Nonfat",
        "food_type": "generic",
        "aliases": [
            "nonfat cottage cheese",
            "fat free cottage cheese",
        ],
        "search_priority": 45,
        "nutrients_per_100g": {
            "Calories": (72.0, "kcal"),
            "Protein": (10.3, "g"),
            "Carbohydrate": (6.7, "g"),
            "Fat": (0.3, "g"),
        },
    },
    {
        "display_name": "Ricotta Cheese, Part Skim",
        "food_type": "generic",
        "aliases": [
            "ricotta",
            "part skim ricotta",
            "ricotta cheese",
        ],
        "search_priority": 65,
        "nutrients_per_100g": {
            "Calories": (138.0, "kcal"),
            "Protein": (11.4, "g"),
            "Carbohydrate": (5.1, "g"),
            "Fat": (7.9, "g"),
        },
    },
    {
        "display_name": "Feta Cheese",
        "food_type": "generic",
        "aliases": [
            "feta",
            "feta cheese",
        ],
        "search_priority": 70,
        "nutrients_per_100g": {
            "Calories": (264.0, "kcal"),
            "Protein": (14.2, "g"),
            "Carbohydrate": (4.1, "g"),
            "Fat": (21.3, "g"),
        },
    },
    {
        "display_name": "String Cheese, Part Skim Mozzarella",
        "food_type": "prepared",
        "aliases": [
            "string cheese",
            "mozzarella string cheese",
            "part skim string cheese",
        ],
        "search_priority": 65,
        "nutrients_per_100g": {
            "Calories": (286.0, "kcal"),
            "Protein": (25.0, "g"),
            "Carbohydrate": (3.6, "g"),
            "Fat": (17.9, "g"),
        },
    },
    {
        "display_name": "Kefir, Plain Low Fat",
        "food_type": "generic",
        "aliases": [
            "kefir",
            "plain kefir",
            "low fat kefir",
        ],
        "search_priority": 70,
        "nutrients_per_100g": {
            "Calories": (43.0, "kcal"),
            "Protein": (3.8, "g"),
            "Carbohydrate": (4.8, "g"),
            "Fat": (1.0, "g"),
        },
    },
    {
        "display_name": "Oatmeal, Cooked",
        "food_type": "cooked",
        "aliases": [
            "cooked oatmeal",
            "prepared oatmeal",
        ],
        "search_priority": 40,
        "nutrients_per_100g": {
            "Calories": (71.0, "kcal"),
            "Protein": (2.5, "g"),
            "Carbohydrate": (12.0, "g"),
            "Fat": (1.5, "g"),
        },
    },
    {
        "display_name": "Barley, Cooked",
        "food_type": "cooked",
        "aliases": [
            "barley",
            "cooked barley",
        ],
        "search_priority": 55,
        "nutrients_per_100g": {
            "Calories": (123.0, "kcal"),
            "Protein": (2.3, "g"),
            "Carbohydrate": (28.2, "g"),
            "Fat": (0.4, "g"),
        },
    },
    {
        "display_name": "Farro, Cooked",
        "food_type": "cooked",
        "aliases": [
            "farro",
            "cooked farro",
        ],
        "search_priority": 55,
        "nutrients_per_100g": {
            "Calories": (127.0, "kcal"),
            "Protein": (4.2, "g"),
            "Carbohydrate": (26.2, "g"),
            "Fat": (0.9, "g"),
        },
    },
    {
        "display_name": "Bulgur, Cooked",
        "food_type": "cooked",
        "aliases": [
            "bulgur",
            "cooked bulgur",
        ],
        "search_priority": 55,
        "nutrients_per_100g": {
            "Calories": (83.0, "kcal"),
            "Protein": (3.1, "g"),
            "Carbohydrate": (18.6, "g"),
            "Fat": (0.2, "g"),
        },
    },
    {
        "display_name": "Grits, Cooked",
        "food_type": "cooked",
        "aliases": [
            "grits",
            "cooked grits",
        ],
        "search_priority": 55,
        "nutrients_per_100g": {
            "Calories": (59.0, "kcal"),
            "Protein": (1.4, "g"),
            "Carbohydrate": (13.0, "g"),
            "Fat": (0.2, "g"),
        },
    },
    {
        "display_name": "Wild Rice, Cooked",
        "food_type": "cooked",
        "aliases": [
            "wild rice",
            "cooked wild rice",
        ],
        "search_priority": 55,
        "nutrients_per_100g": {
            "Calories": (101.0, "kcal"),
            "Protein": (4.0, "g"),
            "Carbohydrate": (21.3, "g"),
            "Fat": (0.3, "g"),
        },
    },
    {
        "display_name": "Egg Noodles, Cooked",
        "food_type": "cooked",
        "aliases": [
            "egg noodles",
            "cooked egg noodles",
        ],
        "search_priority": 65,
        "nutrients_per_100g": {
            "Calories": (138.0, "kcal"),
            "Protein": (4.5, "g"),
            "Carbohydrate": (25.2, "g"),
            "Fat": (2.1, "g"),
        },
    },
    {
        "display_name": "Naan Bread",
        "food_type": "prepared",
        "aliases": [
            "naan",
            "naan bread",
        ],
        "search_priority": 75,
        "nutrients_per_100g": {
            "Calories": (310.0, "kcal"),
            "Protein": (9.0, "g"),
            "Carbohydrate": (55.0, "g"),
            "Fat": (7.0, "g"),
        },
    },
    {
        "display_name": "White Potato, Boiled",
        "food_type": "cooked",
        "aliases": [
            "boiled potato",
            "boiled white potato",
            "white potato",
        ],
        "search_priority": 50,
        "nutrients_per_100g": {
            "Calories": (87.0, "kcal"),
            "Protein": (1.9, "g"),
            "Carbohydrate": (20.1, "g"),
            "Fat": (0.1, "g"),
        },
    },
    {
        "display_name": "Red Potato, Boiled",
        "food_type": "cooked",
        "aliases": [
            "red potato",
            "boiled red potato",
            "red potatoes",
        ],
        "search_priority": 55,
        "nutrients_per_100g": {
            "Calories": (87.0, "kcal"),
            "Protein": (1.9, "g"),
            "Carbohydrate": (20.1, "g"),
            "Fat": (0.1, "g"),
        },
    },
    {
        "display_name": "Butternut Squash, Cooked",
        "food_type": "cooked",
        "aliases": [
            "butternut squash",
            "cooked butternut squash",
        ],
        "search_priority": 65,
        "nutrients_per_100g": {
            "Calories": (45.0, "kcal"),
            "Protein": (1.0, "g"),
            "Carbohydrate": (11.7, "g"),
            "Fat": (0.1, "g"),
        },
    },
    {
        "display_name": "Navy Beans, Cooked",
        "food_type": "cooked",
        "aliases": [
            "navy beans",
            "cooked navy beans",
        ],
        "search_priority": 60,
        "nutrients_per_100g": {
            "Calories": (140.0, "kcal"),
            "Protein": (8.2, "g"),
            "Carbohydrate": (26.0, "g"),
            "Fat": (0.6, "g"),
        },
    },
    {
        "display_name": "Cannellini Beans, Cooked",
        "food_type": "cooked",
        "aliases": [
            "cannellini beans",
            "white beans",
            "cooked cannellini beans",
        ],
        "search_priority": 60,
        "nutrients_per_100g": {
            "Calories": (139.0, "kcal"),
            "Protein": (9.7, "g"),
            "Carbohydrate": (25.1, "g"),
            "Fat": (0.4, "g"),
        },
    },
    {
        "display_name": "Black-Eyed Peas, Cooked",
        "food_type": "cooked",
        "aliases": [
            "black eyed peas",
            "black-eyed peas",
            "cooked black eyed peas",
        ],
        "search_priority": 60,
        "nutrients_per_100g": {
            "Calories": (116.0, "kcal"),
            "Protein": (7.7, "g"),
            "Carbohydrate": (20.8, "g"),
            "Fat": (0.5, "g"),
        },
    },
    {
        "display_name": "Split Peas, Cooked",
        "food_type": "cooked",
        "aliases": [
            "split peas",
            "cooked split peas",
        ],
        "search_priority": 65,
        "nutrients_per_100g": {
            "Calories": (118.0, "kcal"),
            "Protein": (8.3, "g"),
            "Carbohydrate": (21.1, "g"),
            "Fat": (0.4, "g"),
        },
    },
    {
        "display_name": "Refried Beans, Fat-Free",
        "food_type": "prepared",
        "aliases": [
            "fat free refried beans",
            "refried beans",
            "refried beans fat free",
        ],
        "search_priority": 70,
        "nutrients_per_100g": {
            "Calories": (92.0, "kcal"),
            "Protein": (5.5, "g"),
            "Carbohydrate": (16.2, "g"),
            "Fat": (0.5, "g"),
        },
    },
    {
        "display_name": "Kiwi",
        "food_type": "generic",
        "aliases": [
            "kiwi",
            "kiwifruit",
        ],
        "search_priority": 60,
        "nutrients_per_100g": {
            "Calories": (61.0, "kcal"),
            "Protein": (1.1, "g"),
            "Carbohydrate": (14.7, "g"),
            "Fat": (0.5, "g"),
        },
    },
    {
        "display_name": "Cherries",
        "food_type": "generic",
        "aliases": [
            "cherries",
            "sweet cherries",
        ],
        "search_priority": 65,
        "nutrients_per_100g": {
            "Calories": (63.0, "kcal"),
            "Protein": (1.1, "g"),
            "Carbohydrate": (16.0, "g"),
            "Fat": (0.2, "g"),
        },
    },
    {
        "display_name": "Cantaloupe",
        "food_type": "generic",
        "aliases": [
            "cantaloupe",
            "cantaloupe melon",
        ],
        "search_priority": 65,
        "nutrients_per_100g": {
            "Calories": (34.0, "kcal"),
            "Protein": (0.8, "g"),
            "Carbohydrate": (8.2, "g"),
            "Fat": (0.2, "g"),
        },
    },
    {
        "display_name": "Honeydew Melon",
        "food_type": "generic",
        "aliases": [
            "honeydew",
            "honeydew melon",
        ],
        "search_priority": 65,
        "nutrients_per_100g": {
            "Calories": (36.0, "kcal"),
            "Protein": (0.5, "g"),
            "Carbohydrate": (9.1, "g"),
            "Fat": (0.1, "g"),
        },
    },
    {
        "display_name": "Raisins",
        "food_type": "generic",
        "aliases": [
            "raisins",
            "dried raisins",
        ],
        "search_priority": 75,
        "nutrients_per_100g": {
            "Calories": (299.0, "kcal"),
            "Protein": (3.1, "g"),
            "Carbohydrate": (79.2, "g"),
            "Fat": (0.5, "g"),
        },
    },
    {
        "display_name": "Dates, Medjool",
        "food_type": "generic",
        "aliases": [
            "dates",
            "medjool dates",
            "date",
        ],
        "search_priority": 75,
        "nutrients_per_100g": {
            "Calories": (277.0, "kcal"),
            "Protein": (1.8, "g"),
            "Carbohydrate": (75.0, "g"),
            "Fat": (0.2, "g"),
        },
    },
    {
        "display_name": "Grapefruit",
        "food_type": "generic",
        "aliases": [
            "grapefruit",
            "grapefruit sections",
        ],
        "search_priority": 65,
        "nutrients_per_100g": {
            "Calories": (42.0, "kcal"),
            "Protein": (0.8, "g"),
            "Carbohydrate": (10.7, "g"),
            "Fat": (0.1, "g"),
        },
    },
    {
        "display_name": "Kale, Raw",
        "food_type": "raw",
        "aliases": [
            "kale",
            "raw kale",
        ],
        "search_priority": 60,
        "nutrients_per_100g": {
            "Calories": (49.0, "kcal"),
            "Protein": (4.3, "g"),
            "Carbohydrate": (8.8, "g"),
            "Fat": (0.9, "g"),
        },
    },
    {
        "display_name": "Cabbage, Raw",
        "food_type": "raw",
        "aliases": [
            "cabbage",
            "raw cabbage",
        ],
        "search_priority": 65,
        "nutrients_per_100g": {
            "Calories": (25.0, "kcal"),
            "Protein": (1.3, "g"),
            "Carbohydrate": (5.8, "g"),
            "Fat": (0.1, "g"),
        },
    },
    {
        "display_name": "Celery, Raw",
        "food_type": "raw",
        "aliases": [
            "celery",
            "raw celery",
        ],
        "search_priority": 65,
        "nutrients_per_100g": {
            "Calories": (16.0, "kcal"),
            "Protein": (0.7, "g"),
            "Carbohydrate": (3.0, "g"),
            "Fat": (0.2, "g"),
        },
    },
    {
        "display_name": "Eggplant, Cooked",
        "food_type": "cooked",
        "aliases": [
            "eggplant",
            "cooked eggplant",
        ],
        "search_priority": 70,
        "nutrients_per_100g": {
            "Calories": (35.0, "kcal"),
            "Protein": (0.8, "g"),
            "Carbohydrate": (8.7, "g"),
            "Fat": (0.2, "g"),
        },
    },
    {
        "display_name": "Mixed Vegetables, Frozen, Cooked",
        "food_type": "cooked",
        "aliases": [
            "mixed vegetables",
            "frozen mixed vegetables",
            "cooked mixed vegetables",
        ],
        "search_priority": 55,
        "nutrients_per_100g": {
            "Calories": (65.0, "kcal"),
            "Protein": (3.3, "g"),
            "Carbohydrate": (13.1, "g"),
            "Fat": (0.2, "g"),
        },
    },
    {
        "display_name": "Salad Greens, Mixed",
        "food_type": "generic",
        "aliases": [
            "salad greens",
            "mixed salad greens",
            "mixed greens",
        ],
        "search_priority": 55,
        "nutrients_per_100g": {
            "Calories": (17.0, "kcal"),
            "Protein": (1.5, "g"),
            "Carbohydrate": (3.3, "g"),
            "Fat": (0.2, "g"),
        },
    },
    {
        "display_name": "Broccoli, Raw",
        "food_type": "raw",
        "aliases": [
            "raw broccoli",
            "broccoli florets raw",
        ],
        "search_priority": 60,
        "nutrients_per_100g": {
            "Calories": (34.0, "kcal"),
            "Protein": (2.8, "g"),
            "Carbohydrate": (6.6, "g"),
            "Fat": (0.4, "g"),
        },
    },
    {
        "display_name": "Cauliflower Rice",
        "food_type": "prepared",
        "aliases": [
            "cauliflower rice",
            "riced cauliflower",
        ],
        "search_priority": 60,
        "nutrients_per_100g": {
            "Calories": (25.0, "kcal"),
            "Protein": (1.9, "g"),
            "Carbohydrate": (5.0, "g"),
            "Fat": (0.3, "g"),
        },
    },
    {
        "display_name": "Pistachios",
        "food_type": "generic",
        "aliases": [
            "pistachios",
            "pistachio nuts",
        ],
        "search_priority": 75,
        "nutrients_per_100g": {
            "Calories": (562.0, "kcal"),
            "Protein": (20.2, "g"),
            "Carbohydrate": (27.5, "g"),
            "Fat": (45.3, "g"),
        },
    },
    {
        "display_name": "Pecans",
        "food_type": "generic",
        "aliases": [
            "pecans",
            "pecan nuts",
        ],
        "search_priority": 75,
        "nutrients_per_100g": {
            "Calories": (691.0, "kcal"),
            "Protein": (9.2, "g"),
            "Carbohydrate": (13.9, "g"),
            "Fat": (72.0, "g"),
        },
    },
    {
        "display_name": "Pumpkin Seeds",
        "food_type": "generic",
        "aliases": [
            "pumpkin seeds",
            "pepitas",
        ],
        "search_priority": 75,
        "nutrients_per_100g": {
            "Calories": (559.0, "kcal"),
            "Protein": (30.2, "g"),
            "Carbohydrate": (10.7, "g"),
            "Fat": (49.0, "g"),
        },
    },
    {
        "display_name": "Sunflower Seeds",
        "food_type": "generic",
        "aliases": [
            "sunflower seeds",
            "sunflower kernels",
        ],
        "search_priority": 75,
        "nutrients_per_100g": {
            "Calories": (584.0, "kcal"),
            "Protein": (20.8, "g"),
            "Carbohydrate": (20.0, "g"),
            "Fat": (51.5, "g"),
        },
    },
    {
        "display_name": "Tahini",
        "food_type": "generic",
        "aliases": [
            "tahini",
            "sesame paste",
        ],
        "search_priority": 80,
        "nutrients_per_100g": {
            "Calories": (595.0, "kcal"),
            "Protein": (17.0, "g"),
            "Carbohydrate": (21.0, "g"),
            "Fat": (54.0, "g"),
        },
    },
    {
        "display_name": "Olives, Black",
        "food_type": "prepared",
        "aliases": [
            "black olives",
            "olives",
        ],
        "search_priority": 75,
        "nutrients_per_100g": {
            "Calories": (115.0, "kcal"),
            "Protein": (0.8, "g"),
            "Carbohydrate": (6.3, "g"),
            "Fat": (10.7, "g"),
        },
    },
    {
        "display_name": "Guacamole, Generic",
        "food_type": "prepared",
        "aliases": [
            "guacamole",
            "plain guacamole",
        ],
        "search_priority": 80,
        "nutrients_per_100g": {
            "Calories": (157.0, "kcal"),
            "Protein": (1.8, "g"),
            "Carbohydrate": (8.5, "g"),
            "Fat": (14.7, "g"),
        },
    },
    {
        "display_name": "Marinara Sauce",
        "food_type": "prepared",
        "aliases": [
            "marinara",
            "marinara sauce",
            "pasta sauce",
        ],
        "search_priority": 70,
        "nutrients_per_100g": {
            "Calories": (54.0, "kcal"),
            "Protein": (1.4, "g"),
            "Carbohydrate": (8.4, "g"),
            "Fat": (1.5, "g"),
        },
    },
    {
        "display_name": "Tomato Sauce",
        "food_type": "prepared",
        "aliases": [
            "tomato sauce",
            "plain tomato sauce",
        ],
        "search_priority": 70,
        "nutrients_per_100g": {
            "Calories": (29.0, "kcal"),
            "Protein": (1.4, "g"),
            "Carbohydrate": (6.3, "g"),
            "Fat": (0.2, "g"),
        },
    },
    {
        "display_name": "Applesauce, Unsweetened",
        "food_type": "prepared",
        "aliases": [
            "applesauce",
            "unsweetened applesauce",
        ],
        "search_priority": 70,
        "nutrients_per_100g": {
            "Calories": (42.0, "kcal"),
            "Protein": (0.2, "g"),
            "Carbohydrate": (11.0, "g"),
            "Fat": (0.1, "g"),
        },
    },
    {
        "display_name": "Tortilla Chips",
        "food_type": "prepared",
        "aliases": [
            "tortilla chips",
            "corn chips",
        ],
        "search_priority": 85,
        "nutrients_per_100g": {
            "Calories": (489.0, "kcal"),
            "Protein": (7.0, "g"),
            "Carbohydrate": (64.0, "g"),
            "Fat": (24.0, "g"),
        },
    },
    {
        "display_name": "Pita Chips",
        "food_type": "prepared",
        "aliases": [
            "pita chips",
            "plain pita chips",
        ],
        "search_priority": 85,
        "nutrients_per_100g": {
            "Calories": (433.0, "kcal"),
            "Protein": (11.0, "g"),
            "Carbohydrate": (70.0, "g"),
            "Fat": (14.0, "g"),
        },
    },
    # Food Catalog Import Batch v1 - tiny reviewed USDA/FDC generic foods.
    # Source: USDA FoodData Central Foundation Foods, values normalized per 100g.
    {
        "display_name": "Alaska Pollock, Raw",
        "food_type": "raw",
        "aliases": ["alaska pollock", "pollock", "raw pollock"],
        "search_priority": 82,
        "notes": "Food Catalog Import Batch v1. Source: USDA FoodData Central Foundation Foods fdc_id 2768188, Alaska Pollock, raw. Reviewed per-100g generic row.",
        "source_policy": "direct_source",
        "confidence": "High",
        "nutrients_per_100g": {
            "Calories": (78.5, "kcal"),
            "Protein": (17.3, "g"),
            "Carbohydrate": (0.1, "g"),
            "Fat": (1.0, "g"),
        },
    },
    {
        "display_name": "Apricot, Raw",
        "food_type": "raw",
        "aliases": ["apricot", "apricots", "fresh apricot"],
        "search_priority": 82,
        "notes": "Food Catalog Import Batch v1. Source: USDA FoodData Central Foundation Foods fdc_id 2710815, Apricot, with skin, raw. Reviewed per-100g generic row.",
        "source_policy": "direct_source",
        "confidence": "High",
        "nutrients_per_100g": {
            "Calories": (48.4, "kcal"),
            "Protein": (1.0, "g"),
            "Carbohydrate": (10.2, "g"),
            "Fat": (0.4, "g"),
        },
    },
    {
        "display_name": "Arugula, Raw",
        "food_type": "raw",
        "aliases": ["arugula", "baby arugula", "rocket greens"],
        "search_priority": 82,
        "notes": "Food Catalog Import Batch v1. Source: USDA FoodData Central Foundation Foods fdc_id 2710822, Arugula, baby, raw. Reviewed per-100g generic row.",
        "source_policy": "direct_source",
        "confidence": "High",
        "nutrients_per_100g": {
            "Calories": (31.0, "kcal"),
            "Protein": (1.6, "g"),
            "Carbohydrate": (5.4, "g"),
            "Fat": (0.3, "g"),
        },
    },
    {
        "display_name": "Beets, Raw",
        "food_type": "raw",
        "aliases": ["beets", "raw beets", "beetroot"],
        "search_priority": 82,
        "notes": "Food Catalog Import Batch v1. Source: USDA FoodData Central Foundation Foods fdc_id 2685576, Beets, raw. Reviewed per-100g generic row.",
        "source_policy": "direct_source",
        "confidence": "High",
        "nutrients_per_100g": {
            "Calories": (44.6, "kcal"),
            "Protein": (1.7, "g"),
            "Carbohydrate": (8.8, "g"),
            "Fat": (0.3, "g"),
        },
    },
    {
        "display_name": "Beet Greens, Raw",
        "food_type": "raw",
        "aliases": ["beet greens", "raw beet greens"],
        "search_priority": 84,
        "notes": "Food Catalog Import Batch v1. Source: USDA FoodData Central Foundation Foods fdc_id 2747653, Beet greens, raw. Reviewed per-100g generic row.",
        "source_policy": "direct_source",
        "confidence": "High",
        "nutrients_per_100g": {
            "Calories": (26.4, "kcal"),
            "Protein": (1.6, "g"),
            "Carbohydrate": (4.7, "g"),
            "Fat": (0.1, "g"),
        },
    },
    {
        "display_name": "Bok Choy, Raw",
        "food_type": "raw",
        "aliases": ["bok choy", "raw bok choy", "pak choi"],
        "search_priority": 84,
        "notes": "Food Catalog Import Batch v1. Source: USDA FoodData Central Foundation Foods fdc_id 2685572, Cabbage, bok choy, raw. Reviewed per-100g generic row.",
        "source_policy": "direct_source",
        "confidence": "High",
        "nutrients_per_100g": {
            "Calories": (20.3, "kcal"),
            "Protein": (1.0, "g"),
            "Carbohydrate": (3.5, "g"),
            "Fat": (0.2, "g"),
        },
    },
    {
        "display_name": "Red Cabbage, Raw",
        "food_type": "raw",
        "aliases": ["red cabbage", "raw red cabbage"],
        "search_priority": 84,
        "notes": "Food Catalog Import Batch v1. Source: USDA FoodData Central Foundation Foods fdc_id 2346408, Cabbage, red, raw. Reviewed per-100g generic row.",
        "source_policy": "direct_source",
        "confidence": "High",
        "nutrients_per_100g": {
            "Calories": (34.1, "kcal"),
            "Protein": (1.2, "g"),
            "Carbohydrate": (6.8, "g"),
            "Fat": (0.2, "g"),
        },
    },
    {
        "display_name": "Collard Greens, Raw",
        "food_type": "raw",
        "aliases": ["collard greens", "collards", "raw collards"],
        "search_priority": 84,
        "notes": "Food Catalog Import Batch v1. Source: USDA FoodData Central Foundation Foods fdc_id 2685574, Collards, raw. Reviewed per-100g generic row.",
        "source_policy": "direct_source",
        "confidence": "High",
        "nutrients_per_100g": {
            "Calories": (46.9, "kcal"),
            "Protein": (3.0, "g"),
            "Carbohydrate": (7.0, "g"),
            "Fat": (0.8, "g"),
        },
    },
    {
        "display_name": "Fennel Bulb, Raw",
        "food_type": "raw",
        "aliases": ["fennel", "fennel bulb", "raw fennel"],
        "search_priority": 86,
        "notes": "Food Catalog Import Batch v1. Source: USDA FoodData Central Foundation Foods fdc_id 2747655, Fennel, bulb, raw. Reviewed per-100g generic row.",
        "source_policy": "direct_source",
        "confidence": "High",
        "nutrients_per_100g": {
            "Calories": (26.9, "kcal"),
            "Protein": (0.9, "g"),
            "Carbohydrate": (5.5, "g"),
            "Fat": (0.1, "g"),
        },
    },
    {
        "display_name": "Figs, Dried",
        "food_type": "generic",
        "aliases": ["figs", "dried figs", "fig"],
        "search_priority": 86,
        "notes": "Food Catalog Import Batch v1. Source: USDA FoodData Central Foundation Foods fdc_id 326905, Figs, dried, uncooked. Reviewed per-100g generic row.",
        "source_policy": "direct_source",
        "confidence": "High",
        "nutrients_per_100g": {
            "Calories": (249.0, "kcal"),
            "Protein": (3.3, "g"),
            "Carbohydrate": (63.9, "g"),
            "Fat": (0.9, "g"),
        },
    },
    {
        "display_name": "Haddock, Raw",
        "food_type": "raw",
        "aliases": ["haddock", "raw haddock"],
        "search_priority": 82,
        "notes": "Food Catalog Import Batch v1. Source: USDA FoodData Central Foundation Foods fdc_id 333374, Fish, haddock, raw. Reviewed per-100g generic row.",
        "source_policy": "direct_source",
        "confidence": "High",
        "nutrients_per_100g": {
            "Calories": (74.0, "kcal"),
            "Protein": (16.3, "g"),
            "Carbohydrate": (0.0, "g"),
            "Fat": (0.5, "g"),
        },
    },
    {
        "display_name": "Catfish, Raw",
        "food_type": "raw",
        "aliases": ["catfish", "raw catfish", "farm raised catfish"],
        "search_priority": 86,
        "notes": "Food Catalog Import Batch v1. Source: USDA FoodData Central Foundation Foods fdc_id 2684445, Fish, catfish, farm raised, raw. Reviewed per-100g generic row.",
        "source_policy": "direct_source",
        "confidence": "High",
        "nutrients_per_100g": {
            "Calories": (129.1, "kcal"),
            "Protein": (16.5, "g"),
            "Carbohydrate": (0.0, "g"),
            "Fat": (7.3, "g"),
        },
    },
    {
        "display_name": "Plantain, Raw",
        "food_type": "raw",
        "aliases": ["plantain", "plantains", "ripe plantain"],
        "search_priority": 86,
        "notes": "Food Catalog Import Batch v1. Source: USDA FoodData Central Foundation Foods fdc_id 2710817, Plantains, ripe, raw. Reviewed per-100g generic row.",
        "source_policy": "direct_source",
        "confidence": "High",
        "nutrients_per_100g": {
            "Calories": (136.5, "kcal"),
            "Protein": (1.2, "g"),
            "Carbohydrate": (31.0, "g"),
            "Fat": (0.9, "g"),
        },
    },
    {
        "display_name": "Mandarin, Raw",
        "food_type": "raw",
        "aliases": ["mandarin", "mandarins", "mandarin orange"],
        "search_priority": 86,
        "notes": "Food Catalog Import Batch v1. Source: USDA FoodData Central Foundation Foods fdc_id 2710832, Mandarin, seedless, peeled, raw. Reviewed per-100g generic row.",
        "source_policy": "direct_source",
        "confidence": "High",
        "nutrients_per_100g": {
            "Calories": (62.0, "kcal"),
            "Protein": (1.0, "g"),
            "Carbohydrate": (13.4, "g"),
            "Fat": (0.5, "g"),
        },
    },
    {
        "display_name": "Black Rice, Dry",
        "food_type": "raw",
        "aliases": ["black rice", "dry black rice", "forbidden rice"],
        "search_priority": 86,
        "notes": "Food Catalog Import Batch v1. Source: USDA FoodData Central Foundation Foods fdc_id 2710825, Rice, black, unenriched, raw. Reviewed per-100g generic row.",
        "source_policy": "direct_source",
        "confidence": "High",
        "nutrients_per_100g": {
            "Calories": (370.0, "kcal"),
            "Protein": (7.6, "g"),
            "Carbohydrate": (77.2, "g"),
            "Fat": (3.4, "g"),
        },
    },
    {
        "display_name": "Red Rice, Dry",
        "food_type": "raw",
        "aliases": ["red rice", "dry red rice"],
        "search_priority": 86,
        "notes": "Food Catalog Import Batch v1. Source: USDA FoodData Central Foundation Foods fdc_id 2710838, Rice, red, unenriched, dry, raw. Reviewed per-100g generic row.",
        "source_policy": "direct_source",
        "confidence": "High",
        "nutrients_per_100g": {
            "Calories": (369.8, "kcal"),
            "Protein": (8.6, "g"),
            "Carbohydrate": (76.2, "g"),
            "Fat": (3.4, "g"),
        },
    },
    {
        "display_name": "Fonio Grain, Dry",
        "food_type": "raw",
        "aliases": ["fonio", "fonio grain", "dry fonio"],
        "search_priority": 88,
        "notes": "Food Catalog Import Batch v1. Source: USDA FoodData Central Foundation Foods fdc_id 2710829, Fonio, grain, dry, raw. Reviewed per-100g generic row.",
        "source_policy": "direct_source",
        "confidence": "High",
        "nutrients_per_100g": {
            "Calories": (369.1, "kcal"),
            "Protein": (7.2, "g"),
            "Carbohydrate": (81.3, "g"),
            "Fat": (1.7, "g"),
        },
    },
    {
        "display_name": "Khorasan Grain, Dry",
        "food_type": "raw",
        "aliases": ["khorasan", "khorasan grain", "kamut", "dry khorasan"],
        "search_priority": 88,
        "notes": "Food Catalog Import Batch v1. Source: USDA FoodData Central Foundation Foods fdc_id 2710830, Khorasan, grain, dry, raw. Reviewed per-100g generic row.",
        "source_policy": "direct_source",
        "confidence": "High",
        "nutrients_per_100g": {
            "Calories": (371.4, "kcal"),
            "Protein": (14.8, "g"),
            "Carbohydrate": (71.8, "g"),
            "Fat": (2.8, "g"),
        },
    },
    {
        "display_name": "Parsnips, Raw",
        "food_type": "raw",
        "aliases": ["parsnips", "parsnip", "raw parsnips"],
        "search_priority": 86,
        "notes": "Food Catalog Import Batch v1. Source: USDA FoodData Central Foundation Foods fdc_id 2747659, Parsnips, raw. Reviewed per-100g generic row.",
        "source_policy": "direct_source",
        "confidence": "High",
        "nutrients_per_100g": {
            "Calories": (87.1, "kcal"),
            "Protein": (1.3, "g"),
            "Carbohydrate": (19.3, "g"),
            "Fat": (0.5, "g"),
        },
    },
    {
        "display_name": "Radishes, Raw",
        "food_type": "raw",
        "aliases": ["radishes", "radish", "red radishes"],
        "search_priority": 86,
        "notes": "Food Catalog Import Batch v1. Source: USDA FoodData Central Foundation Foods fdc_id 2747665, Radishes, red, raw. Reviewed per-100g generic row.",
        "source_policy": "direct_source",
        "confidence": "High",
        "nutrients_per_100g": {
            "Calories": (19.6, "kcal"),
            "Protein": (0.7, "g"),
            "Carbohydrate": (4.1, "g"),
            "Fat": (0.1, "g"),
        },
    },
]


def normalize_food_name(value: str) -> str:
    normalized = value.strip().lower()
    normalized = normalized.replace("&", " and ")
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def _normalize_food_type(food_type: str | None) -> str:
    normalized = normalize_food_name(food_type or "generic").replace(" ", "_")
    if normalized not in ALLOWED_FOOD_TYPES:
        return "generic"
    return normalized


def _normalize_default_unit(default_unit: str | None) -> str:
    normalized = normalize_food_name(default_unit or "grams")
    if normalized in {"g", "gram", "grams"}:
        return "grams"
    return normalized or "grams"


def _normalize_source_policy(source_policy: str | None) -> str:
    normalized = normalize_food_name(source_policy or "manually_curated").replace(
        " ", "_"
    )
    if normalized not in ALLOWED_SOURCE_POLICIES:
        return "manually_curated"
    return normalized


def _normalize_confidence(confidence: str | None) -> str:
    if not confidence:
        return "Moderate"

    normalized = confidence.strip().title()
    if normalized not in ALLOWED_NUTRIENT_CONFIDENCE:
        return "Moderate"

    return normalized


def _normalize_relationship_type(relationship_type: str | None) -> str:
    normalized = normalize_food_name(relationship_type or "primary").replace(" ", "_")
    if normalized not in ALLOWED_SOURCE_RELATIONSHIPS:
        return "primary"
    return normalized


def _encode_json_payload(source_payload: dict[str, Any] | str | None) -> str | None:
    if source_payload is None:
        return None
    if isinstance(source_payload, str):
        return source_payload
    return json.dumps(source_payload, sort_keys=True)


def ensure_food_normalization_tables() -> None:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS raw_food_source_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_name TEXT NOT NULL,
        source_record_id TEXT NOT NULL,
        raw_description TEXT NOT NULL,
        brand_name TEXT,
        food_category TEXT,
        source_payload_json TEXT,
        license TEXT,
        source_url TEXT,
        imported_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(source_name, source_record_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS canonical_foods (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        display_name TEXT NOT NULL,
        normalized_name TEXT NOT NULL,
        food_type TEXT NOT NULL DEFAULT 'generic',
        default_unit TEXT NOT NULL DEFAULT 'grams',
        default_grams REAL,
        search_priority INTEGER NOT NULL DEFAULT 100,
        active INTEGER NOT NULL DEFAULT 1,
        notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(normalized_name, food_type)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS canonical_food_aliases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        canonical_food_id INTEGER NOT NULL,
        alias TEXT NOT NULL,
        normalized_alias TEXT NOT NULL,
        priority INTEGER NOT NULL DEFAULT 100,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(canonical_food_id, normalized_alias),
        FOREIGN KEY (canonical_food_id) REFERENCES canonical_foods(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS canonical_food_nutrients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        canonical_food_id INTEGER NOT NULL,
        nutrient_name TEXT NOT NULL,
        nutrient_unit TEXT NOT NULL,
        amount_per_100g REAL NOT NULL,
        source_policy TEXT NOT NULL DEFAULT 'manually_curated',
        confidence TEXT NOT NULL DEFAULT 'Moderate',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(canonical_food_id, nutrient_name),
        FOREIGN KEY (canonical_food_id) REFERENCES canonical_foods(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS food_source_links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        canonical_food_id INTEGER NOT NULL,
        raw_food_source_record_id INTEGER NOT NULL,
        relationship_type TEXT NOT NULL DEFAULT 'primary',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(canonical_food_id, raw_food_source_record_id, relationship_type),
        FOREIGN KEY (canonical_food_id) REFERENCES canonical_foods(id),
        FOREIGN KEY (raw_food_source_record_id) REFERENCES raw_food_source_records(id)
    )
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_canonical_foods_normalized_name
    ON canonical_foods(normalized_name)
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_canonical_food_aliases_normalized_alias
    ON canonical_food_aliases(normalized_alias)
    """)

    conn.commit()
    conn.close()


def _row_to_raw_food_source_record(row) -> RawFoodSourceRecord:
    return RawFoodSourceRecord(
        id=row["id"],
        source_name=row["source_name"],
        source_record_id=row["source_record_id"],
        raw_description=row["raw_description"],
        brand_name=row["brand_name"],
        food_category=row["food_category"],
        source_payload_json=row["source_payload_json"],
        license=row["license"],
        source_url=row["source_url"],
        imported_at=row["imported_at"],
        updated_at=row["updated_at"],
    )


def _row_to_canonical_food(row) -> CanonicalFood:
    return CanonicalFood(
        id=row["id"],
        display_name=row["display_name"],
        normalized_name=row["normalized_name"],
        food_type=row["food_type"],
        default_unit=row["default_unit"],
        default_grams=row["default_grams"],
        search_priority=row["search_priority"],
        active=bool(row["active"]),
        notes=row["notes"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_canonical_food_alias(row) -> CanonicalFoodAlias:
    return CanonicalFoodAlias(
        id=row["id"],
        canonical_food_id=row["canonical_food_id"],
        alias=row["alias"],
        normalized_alias=row["normalized_alias"],
        priority=row["priority"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_canonical_food_nutrient(row) -> CanonicalFoodNutrient:
    return CanonicalFoodNutrient(
        id=row["id"],
        canonical_food_id=row["canonical_food_id"],
        nutrient_name=row["nutrient_name"],
        nutrient_unit=row["nutrient_unit"],
        amount_per_100g=row["amount_per_100g"],
        source_policy=row["source_policy"],
        confidence=row["confidence"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_food_source_link(row) -> FoodSourceLink:
    return FoodSourceLink(
        id=row["id"],
        canonical_food_id=row["canonical_food_id"],
        raw_food_source_record_id=row["raw_food_source_record_id"],
        relationship_type=row["relationship_type"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def create_raw_food_source_record(
    source_name: str,
    source_record_id: str,
    raw_description: str,
    brand_name: str | None = None,
    food_category: str | None = None,
    source_payload: dict[str, Any] | str | None = None,
    license: str | None = None,
    source_url: str | None = None,
) -> RawFoodSourceRecord:
    ensure_food_normalization_tables()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO raw_food_source_records (
            source_name,
            source_record_id,
            raw_description,
            brand_name,
            food_category,
            source_payload_json,
            license,
            source_url,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(source_name, source_record_id) DO UPDATE SET
            raw_description = excluded.raw_description,
            brand_name = excluded.brand_name,
            food_category = excluded.food_category,
            source_payload_json = excluded.source_payload_json,
            license = excluded.license,
            source_url = excluded.source_url,
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            source_name.strip(),
            str(source_record_id).strip(),
            raw_description.strip(),
            brand_name,
            food_category,
            _encode_json_payload(source_payload),
            license,
            source_url,
        ),
    )
    conn.commit()

    cursor.execute(
        """
        SELECT *
        FROM raw_food_source_records
        WHERE source_name = ? AND source_record_id = ?
        """,
        (source_name.strip(), str(source_record_id).strip()),
    )
    row = cursor.fetchone()
    conn.close()

    return _row_to_raw_food_source_record(row)


def get_raw_food_source_record(record_id: int) -> RawFoodSourceRecord | None:
    ensure_food_normalization_tables()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM raw_food_source_records WHERE id = ?",
        (record_id,),
    )
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return _row_to_raw_food_source_record(row)


def create_canonical_food(
    display_name: str,
    food_type: str = "generic",
    default_unit: str = "grams",
    default_grams: float | None = None,
    search_priority: int = 100,
    active: bool = True,
    notes: str | None = None,
) -> CanonicalFood:
    ensure_food_normalization_tables()

    normalized_food_type = _normalize_food_type(food_type)
    normalized_name = normalize_food_name(display_name)
    normalized_unit = _normalize_default_unit(default_unit)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO canonical_foods (
            display_name,
            normalized_name,
            food_type,
            default_unit,
            default_grams,
            search_priority,
            active,
            notes,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(normalized_name, food_type) DO UPDATE SET
            display_name = excluded.display_name,
            default_unit = excluded.default_unit,
            default_grams = excluded.default_grams,
            search_priority = excluded.search_priority,
            active = excluded.active,
            notes = excluded.notes,
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            display_name.strip(),
            normalized_name,
            normalized_food_type,
            normalized_unit,
            default_grams,
            int(search_priority),
            1 if active else 0,
            notes,
        ),
    )
    conn.commit()

    cursor.execute(
        """
        SELECT *
        FROM canonical_foods
        WHERE normalized_name = ? AND food_type = ?
        """,
        (normalized_name, normalized_food_type),
    )
    row = cursor.fetchone()
    conn.close()

    return _row_to_canonical_food(row)


def get_canonical_food(canonical_food_id: int) -> CanonicalFood | None:
    ensure_food_normalization_tables()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM canonical_foods WHERE id = ?", (canonical_food_id,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return _row_to_canonical_food(row)


def create_canonical_food_alias(
    canonical_food_id: int,
    alias: str,
    priority: int = 100,
) -> CanonicalFoodAlias:
    ensure_food_normalization_tables()

    normalized_alias = normalize_food_name(alias)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO canonical_food_aliases (
            canonical_food_id,
            alias,
            normalized_alias,
            priority,
            updated_at
        )
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(canonical_food_id, normalized_alias) DO UPDATE SET
            alias = excluded.alias,
            priority = excluded.priority,
            updated_at = CURRENT_TIMESTAMP
        """,
        (canonical_food_id, alias.strip(), normalized_alias, int(priority)),
    )
    conn.commit()

    cursor.execute(
        """
        SELECT *
        FROM canonical_food_aliases
        WHERE canonical_food_id = ? AND normalized_alias = ?
        """,
        (canonical_food_id, normalized_alias),
    )
    row = cursor.fetchone()
    conn.close()

    return _row_to_canonical_food_alias(row)


def create_canonical_food_nutrient(
    canonical_food_id: int,
    nutrient_name: str,
    nutrient_unit: str,
    amount_per_100g: float,
    source_policy: str = "manually_curated",
    confidence: str = "Moderate",
) -> CanonicalFoodNutrient:
    ensure_food_normalization_tables()

    normalized_source_policy = _normalize_source_policy(source_policy)
    normalized_confidence = _normalize_confidence(confidence)

    if amount_per_100g < 0:
        raise ValueError("Canonical nutrient amount_per_100g cannot be negative.")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO canonical_food_nutrients (
            canonical_food_id,
            nutrient_name,
            nutrient_unit,
            amount_per_100g,
            source_policy,
            confidence,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(canonical_food_id, nutrient_name) DO UPDATE SET
            nutrient_unit = excluded.nutrient_unit,
            amount_per_100g = excluded.amount_per_100g,
            source_policy = excluded.source_policy,
            confidence = excluded.confidence,
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            canonical_food_id,
            nutrient_name.strip(),
            nutrient_unit.strip(),
            float(amount_per_100g),
            normalized_source_policy,
            normalized_confidence,
        ),
    )
    conn.commit()

    cursor.execute(
        """
        SELECT *
        FROM canonical_food_nutrients
        WHERE canonical_food_id = ? AND nutrient_name = ?
        """,
        (canonical_food_id, nutrient_name.strip()),
    )
    row = cursor.fetchone()
    conn.close()

    return _row_to_canonical_food_nutrient(row)


def link_canonical_food_to_source(
    canonical_food_id: int,
    raw_food_source_record_id: int,
    relationship_type: str = "primary",
) -> FoodSourceLink:
    ensure_food_normalization_tables()

    normalized_relationship = _normalize_relationship_type(relationship_type)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO food_source_links (
            canonical_food_id,
            raw_food_source_record_id,
            relationship_type,
            updated_at
        )
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(
            canonical_food_id,
            raw_food_source_record_id,
            relationship_type
        ) DO UPDATE SET
            updated_at = CURRENT_TIMESTAMP
        """,
        (canonical_food_id, raw_food_source_record_id, normalized_relationship),
    )
    conn.commit()

    cursor.execute(
        """
        SELECT *
        FROM food_source_links
        WHERE canonical_food_id = ?
          AND raw_food_source_record_id = ?
          AND relationship_type = ?
        """,
        (canonical_food_id, raw_food_source_record_id, normalized_relationship),
    )
    row = cursor.fetchone()
    conn.close()

    return _row_to_food_source_link(row)


def get_source_links_for_canonical_food(canonical_food_id: int) -> list[FoodSourceLink]:
    ensure_food_normalization_tables()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT *
        FROM food_source_links
        WHERE canonical_food_id = ?
        ORDER BY
            CASE relationship_type
                WHEN 'primary' THEN 1
                WHEN 'equivalent' THEN 2
                WHEN 'supporting' THEN 3
                WHEN 'alternate_preparation' THEN 4
                ELSE 5
            END,
            id
        """,
        (canonical_food_id,),
    )
    rows = cursor.fetchall()
    conn.close()

    return [_row_to_food_source_link(row) for row in rows]


def get_aliases_for_canonical_food(canonical_food_id: int) -> list[CanonicalFoodAlias]:
    ensure_food_normalization_tables()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT *
        FROM canonical_food_aliases
        WHERE canonical_food_id = ?
        ORDER BY priority, alias
        """,
        (canonical_food_id,),
    )
    rows = cursor.fetchall()
    conn.close()

    return [_row_to_canonical_food_alias(row) for row in rows]


def get_nutrients_for_canonical_food(
    canonical_food_id: int,
) -> list[CanonicalFoodNutrient]:
    ensure_food_normalization_tables()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT *
        FROM canonical_food_nutrients
        WHERE canonical_food_id = ?
        ORDER BY nutrient_name
        """,
        (canonical_food_id,),
    )
    rows = cursor.fetchall()
    conn.close()

    return [_row_to_canonical_food_nutrient(row) for row in rows]


def _build_search_result(row) -> CanonicalFoodSearchResult:
    canonical_food = _row_to_canonical_food(row)
    aliases = [alias for alias in (row["aliases"] or "").split("||") if alias]
    return CanonicalFoodSearchResult(
        canonical_food=canonical_food,
        matched_on=row["matched_on"],
        matched_value=row["matched_value"],
        rank_score=row["rank_score"],
        aliases=aliases,
    )


def search_canonical_foods(
    search_term: str,
    limit: int = 10,
    include_inactive: bool = False,
) -> list[CanonicalFoodSearchResult]:
    ensure_food_normalization_tables()

    normalized_query = normalize_food_name(search_term)
    if not normalized_query:
        return []

    like_query = f"%{normalized_query}%"
    prefix_query = f"{normalized_query}%"
    include_inactive_flag = 1 if include_inactive else 0

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        WITH matched AS (
            SELECT
                canonical_foods.*,
                'display_name' AS matched_on,
                canonical_foods.display_name AS matched_value,
                CASE
                    WHEN canonical_foods.normalized_name = ? THEN 0
                    WHEN canonical_foods.normalized_name LIKE ? THEN 10
                    WHEN canonical_foods.normalized_name LIKE ? THEN 30
                    ELSE 80
                END + canonical_foods.search_priority AS rank_score
            FROM canonical_foods
            WHERE (? = 1 OR canonical_foods.active = 1)
              AND canonical_foods.normalized_name LIKE ?

            UNION ALL

            SELECT
                canonical_foods.*,
                'alias' AS matched_on,
                canonical_food_aliases.alias AS matched_value,
                CASE
                    WHEN canonical_food_aliases.normalized_alias = ? THEN 5
                    WHEN canonical_food_aliases.normalized_alias LIKE ? THEN 15
                    WHEN canonical_food_aliases.normalized_alias LIKE ? THEN 35
                    ELSE 90
                END
                + canonical_foods.search_priority
                + canonical_food_aliases.priority AS rank_score
            FROM canonical_food_aliases
            JOIN canonical_foods
                ON canonical_food_aliases.canonical_food_id = canonical_foods.id
            WHERE (? = 1 OR canonical_foods.active = 1)
              AND canonical_food_aliases.normalized_alias LIKE ?
        ),
        best_match AS (
            SELECT
                matched.*,
                ROW_NUMBER() OVER (
                    PARTITION BY matched.id
                    ORDER BY matched.rank_score, matched.display_name
                ) AS match_rank
            FROM matched
        )
        SELECT
            best_match.*,
            (
                SELECT GROUP_CONCAT(canonical_food_aliases.alias, '||')
                FROM canonical_food_aliases
                WHERE canonical_food_aliases.canonical_food_id = best_match.id
            ) AS aliases
        FROM best_match
        WHERE match_rank = 1
        ORDER BY rank_score, search_priority, display_name
        LIMIT ?
        """,
        (
            normalized_query,
            prefix_query,
            like_query,
            include_inactive_flag,
            like_query,
            normalized_query,
            prefix_query,
            like_query,
            include_inactive_flag,
            like_query,
            int(limit),
        ),
    )
    rows = cursor.fetchall()
    conn.close()

    return [_build_search_result(row) for row in rows]


def seed_starter_canonical_foods() -> list[CanonicalFood]:
    ensure_food_normalization_tables()

    conn = get_connection()
    cursor = conn.cursor()
    seeded_foods: list[CanonicalFood] = []

    for seed_food in STARTER_CANONICAL_FOODS:
        display_name = seed_food["display_name"]
        food_type = _normalize_food_type(seed_food["food_type"])
        normalized_name = normalize_food_name(display_name)
        default_unit = "grams"
        default_grams = 100.0
        search_priority = int(seed_food["search_priority"])
        notes = seed_food.get("notes", "Canonical food for app-facing search.")
        source_policy = seed_food.get("source_policy", "manually_curated")
        confidence = seed_food.get("confidence", "Moderate")

        cursor.execute(
            """
            INSERT INTO canonical_foods (
                display_name,
                normalized_name,
                food_type,
                default_unit,
                default_grams,
                search_priority,
                active,
                notes,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, 1, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(normalized_name, food_type) DO UPDATE SET
                display_name = excluded.display_name,
                default_unit = excluded.default_unit,
                default_grams = excluded.default_grams,
                search_priority = excluded.search_priority,
                active = excluded.active,
                notes = excluded.notes,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                display_name.strip(),
                normalized_name,
                food_type,
                default_unit,
                default_grams,
                search_priority,
                notes,
            ),
        )
        cursor.execute(
            """
            SELECT *
            FROM canonical_foods
            WHERE normalized_name = ? AND food_type = ?
            """,
            (normalized_name, food_type),
        )
        food_row = cursor.fetchone()
        canonical_food_id = int(food_row["id"])
        seeded_foods.append(_row_to_canonical_food(food_row))

        for index, alias in enumerate(seed_food["aliases"]):
            normalized_alias = normalize_food_name(alias)
            cursor.execute(
                """
                INSERT INTO canonical_food_aliases (
                    canonical_food_id,
                    alias,
                    normalized_alias,
                    priority,
                    updated_at
                )
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(canonical_food_id, normalized_alias) DO UPDATE SET
                    alias = excluded.alias,
                    priority = excluded.priority,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (canonical_food_id, alias.strip(), normalized_alias, 10 + index),
            )

        for nutrient_name, (amount, unit) in seed_food["nutrients_per_100g"].items():
            cursor.execute(
                """
                INSERT INTO canonical_food_nutrients (
                    canonical_food_id,
                    nutrient_name,
                    nutrient_unit,
                    amount_per_100g,
                    source_policy,
                    confidence,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(canonical_food_id, nutrient_name) DO UPDATE SET
                    nutrient_unit = excluded.nutrient_unit,
                    amount_per_100g = excluded.amount_per_100g,
                    source_policy = excluded.source_policy,
                    confidence = excluded.confidence,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    canonical_food_id,
                    nutrient_name,
                    unit,
                    float(amount),
                    source_policy,
                    confidence,
                ),
            )

    conn.commit()
    conn.close()
    return seeded_foods


def ensure_starter_canonical_foods_seeded() -> None:
    ensure_food_normalization_tables()

    required_names = [
        normalize_food_name(seed_food["display_name"])
        for seed_food in STARTER_CANONICAL_FOODS
    ]
    placeholders = ",".join("?" for _ in required_names)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT COUNT(*) AS count
        FROM canonical_foods
        WHERE normalized_name IN ({placeholders})
          AND active = 1
        """,
        required_names,
    )
    existing_count = cursor.fetchone()["count"]
    conn.close()

    if existing_count < len(required_names):
        seed_starter_canonical_foods()


def canonical_food_to_dict(food: CanonicalFood) -> dict[str, Any]:
    return asdict(food)


def raw_food_source_record_to_dict(record: RawFoodSourceRecord) -> dict[str, Any]:
    return asdict(record)


def canonical_search_result_to_dict(
    result: CanonicalFoodSearchResult,
) -> dict[str, Any]:
    return {
        "canonical_food": canonical_food_to_dict(result.canonical_food),
        "matched_on": result.matched_on,
        "matched_value": result.matched_value,
        "rank_score": result.rank_score,
        "aliases": result.aliases,
    }
