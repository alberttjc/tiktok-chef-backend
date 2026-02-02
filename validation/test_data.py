#!/usr/bin/env python3
"""
Test cases for recipe agent evaluation.
Add new test cases here with their expected responses.
"""

TEST_CASES = [
    {
        "id": 1,
        "name": "Spicy Garlic Noodles",
        "video_url": "https://www.tiktok.com/@khanhong/video/7557275818255273234",
        "description": "Spicy garlic noodles with chili oil",
        "expected_response": {
            "success": True,
            "recipe": {
                "recipe_overview": {
                    "title": "Spicy Garlic Noodles",
                    "prep_time": "10 minutes",
                    "cook_time": "5 minutes",
                    "servings": 1,
                    "difficulty": "Easy",
                    "cuisine_type": "Asian",
                },
                "ingredients": [
                    {
                        "item": "Fresh noodles",
                        "amount": "1",
                        "unit": "serving",
                        "notes": "approx. 200-250g",
                    },
                    {
                        "item": "Garlic",
                        "amount": "3-4",
                        "unit": "cloves",
                        "notes": "minced",
                    },
                    {"item": "Chili flakes", "amount": "1", "unit": "tablespoon"},
                    {
                        "item": "Green onions",
                        "amount": "1-2",
                        "unit": "stalks",
                        "notes": "chopped, white and green parts separated",
                    },
                    {"item": "Soy sauce", "amount": "1", "unit": "tablespoon"},
                    {"item": "Oyster sauce", "amount": "0.5", "unit": "tablespoon"},
                    {
                        "item": "Dark soy sauce",
                        "amount": "0.5",
                        "unit": "teaspoon",
                        "notes": "for color",
                    },
                    {"item": "Sugar", "amount": "0.5", "unit": "teaspoon"},
                    {"item": "Sesame oil", "amount": "0.5", "unit": "teaspoon"},
                    {
                        "item": "Neutral oil",
                        "amount": "2-3",
                        "unit": "tablespoons",
                        "notes": "e.g., vegetable, canola, for heating",
                    },
                ],
                "instructions": [
                    "Boil fresh noodles according to package directions until al dente. Drain well and set aside.",
                    "In a heatproof bowl, combine the minced garlic, chili flakes, and the white parts of the chopped green onions.",
                    "In a separate small bowl, whisk together the soy sauce, oyster sauce, dark soy sauce, sugar, and sesame oil to create the sauce mixture.",
                    "Heat 2-3 tablespoons of neutral oil in a small saucepan or wok over high heat until it is smoking hot.",
                    "Carefully pour the hot oil over the garlic, chili flakes, and green onion mixture in the heatproof bowl. It should sizzle vigorously. Stir well to infuse the oil with the aromatics.",
                    "Add the prepared sauce mixture to the hot oil and aromatic mixture. Stir thoroughly to combine all ingredients.",
                    "Add the drained noodles to the bowl with the sauce. Using tongs or chopsticks, toss the noodles thoroughly to coat them evenly with the spicy garlic sauce.",
                    "Garnish with the green parts of the chopped green onions. Serve immediately and enjoy!",
                ],
            },
        },
    },
    {
        "id": 2,
        "name": "Thai Crying Tiger Salad",
        "video_url": "https://www.tiktok.com/@khanhong/video/7566389133237603605",
        "description": "Thai style crying tiger beef salad",
        "expected_response": {
            "success": True,
            "recipe": {
                "recipe_overview": {
                    "title": "Thai Style Crying Tiger Salad",
                    "prep_time": None,
                    "cook_time": None,
                    "servings": 2,
                    "difficulty": "Intermediate",
                    "cuisine_type": "Thai",
                },
                "ingredients": [
                    {"item": "Instant noodles", "amount": "1", "unit": "pack"},
                    {"item": "Butter", "amount": "1", "unit": "tbsp"},
                    {
                        "item": "Garlic",
                        "amount": "3",
                        "unit": "cloves",
                        "notes": "minced",
                    },
                    {"item": "Heavy cream", "amount": "1/4", "unit": "cup"},
                    {
                        "item": "Parmesan cheese",
                        "amount": "1/4",
                        "unit": "cup",
                        "notes": "grated",
                    },
                    {"item": "Soy sauce", "amount": "1", "unit": "tbsp"},
                    {"item": "Brown sugar", "amount": "1", "unit": "tsp"},
                    {"item": "Black pepper", "amount": "1/2", "unit": "tsp"},
                    {
                        "item": "Noodle water",
                        "amount": "1/4",
                        "unit": "cup",
                        "notes": "reserved from boiling noodles",
                    },
                    {
                        "item": "Green onion",
                        "amount": "1",
                        "unit": "stalk",
                        "notes": "chopped, for garnish",
                    },
                ],
                "instructions": [
                    "Boil instant noodles according to package directions until al dente. Reserve 1/4 cup of the noodle cooking water, then drain the noodles and set aside.",
                    "In a pan, melt 1 tablespoon of butter over medium heat.",
                    "Add the 3 minced garlic cloves to the pan and sauté for about 30 seconds to 1 minute, until fragrant but not browned.",
                    "Pour in 1/4 cup of heavy cream and stir.",
                    "Add 1/4 cup of grated Parmesan cheese and stir until melted and combined.",
                    "Stir in 1 tablespoon of soy sauce, 1 teaspoon of brown sugar, and 1/2 teaspoon of black pepper.",
                    "Pour in the reserved 1/4 cup of noodle water.",
                    "Bring the sauce to a gentle simmer and cook for 1-2 minutes, stirring occasionally, until it slightly thickens.",
                    "Add the drained noodles to the pan with the sauce.",
                    "Toss the noodles thoroughly to ensure they are evenly coated with the creamy garlic sauce.",
                    "Garnish with chopped green onion before serving.",
                    "Serve immediately and enjoy.",
                ],
            },
        },
    },
]
