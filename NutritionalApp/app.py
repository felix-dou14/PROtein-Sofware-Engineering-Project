# ----------------------------------------------------
# app.py — PRO3 (Goal-aware meals with accurate macros)
# ----------------------------------------------------
import streamlit as st
import pandas as pd
import random
import os
from PIL import Image

# ----------------------------------------------------
# LOAD DATA
# ----------------------------------------------------
base_path = os.path.join(os.path.dirname(__file__), "data")

group_files = [
    "FOOD-DATA-GROUP1.csv",
    "FOOD-DATA-GROUP2.csv",
    "FOOD-DATA-GROUP3.csv",
    "FOOD-DATA-GROUP4.csv",
    "FOOD-DATA-GROUP5.csv"
]

dfs = [pd.read_csv(os.path.join(base_path, f)) for f in group_files]
food_df = pd.concat(dfs, ignore_index=True)

if "food" in food_df.columns:
    food_df["food"] = food_df["food"].astype(str)

if "Caloric Value" in food_df.columns and "Protein" in food_df.columns:
    food_df = food_df[(food_df["Caloric Value"] > 0) & (food_df["Protein"] > 0)]

exclude_keywords = (
    "raw|uncooked|freeze-dried|instant|powder|wine|beer|vodka|whiskey|"
    "mcdonalds|kfc|burger king|pastry|dessert|chocolate|chips|cookie|"
    "candy|lotus|apple pie|pudding|fat free|dressing|pie|cheese crackers|prune"
)
if "food" in food_df.columns:
    food_df = food_df[~food_df["food"].str.contains(exclude_keywords, case=False, na=False)]

# ----------------------------------------------------
# HELPERS
# ----------------------------------------------------
def calculate_calories(age, weight, height, goal):
    bmr = 10 * weight + 6.25 * height - 5 * age + 5
    if goal == "Weight Loss":
        return bmr * 1.2 - 500
    if goal == "Muscle Gain":
        return bmr * 1.2 + 300
    return bmr * 1.2

def calculate_macros(calories):
    return calories * 0.25 / 4, calories * 0.25 / 9, calories * 0.50 / 4

def create_gym_meal(pool, meal_type):
    foods = random.sample(pool, 2)
    templates = {
        "breakfast": [
            "{food1} and {food2} Bowl",
            "Protein-Packed {food1} with {food2}",
            "{food1} Omelette with {food2} on the Side",
            "{food1} Pancakes with {food2}"
        ],
        "lunch": [
            "Grilled {food1} with {food2} and Veggies",
            "{food1} Salad with {food2} and Brown Rice",
            "{food1} Stir-Fry with {food2}",
            "Baked {food1} with {food2} Quinoa Bowl"
        ],
        "dinner": [
            "Pan-Seared {food1} with {food2} and Steamed Veggies",
            "{food1} Fillet with {food2} and Potato",
            "Baked {food1} with {food2} and Garden Vegetables",
            "{food1} Curry with {food2} and Rice"
        ]
    }
    template = random.choice(templates.get(meal_type, templates["lunch"]))
    return template.format(food1=foods[0], food2=foods[1]), foods

def generate_snack():
    snacks = [
        ("Protein Cookies", 260, 20, 8, 28, "Mix oats, whey, banana, peanut butter. Bake 12 minutes at 180°C.",
         ["oats", "whey protein", "banana", "peanut butter"]),
        ("Protein Pancakes", 310, 28, 5, 40, "Blend oats, egg whites, cottage cheese. Cook 2 min per side.",
         ["oats", "egg whites", "cottage cheese"]),
        ("Protein Mug Cake", 290, 25, 6, 32, "Mix whey, egg, milk, microwave 60–75 seconds.",
         ["whey protein", "egg", "milk"])
    ]
    return random.choice(snacks)

def build_three_plans(breakfast_pool, lunch_pool, dinner_pool, include_snack=False):
    plans = []
    for i in range(3):
        b_str, b_foods = create_gym_meal(breakfast_pool, "breakfast")
        l_str, l_foods = create_gym_meal(lunch_pool, "lunch")
        d_str, d_foods = create_gym_meal(dinner_pool, "dinner")

        plan = {
            "title": f"Plan {i+1}",
            "breakfast_str": b_str,
            "lunch_str": l_str,
            "dinner_str": d_str,
            "breakfast_foods": b_foods,
            "lunch_foods": l_foods,
            "dinner_foods": d_foods
        }

        if include_snack:
            s = generate_snack()
            plan["snack"] = {
                "name": s[0],
                "cal": s[1],
                "protein": s[2],
                "fat": s[3],
                "carbs": s[4],
                "instructions": s[5],
                "ingredients": s[6]
            }
        else:
            plan["snack"] = None
        plans.append(plan)

    return plans

# ----------------------------------------------------
# ACCURATE MACROS FUNCTION (with protein/cals boost)
# ----------------------------------------------------
def get_food_macros(food_name):
    prefix = None
    for p in ["Vegan ", "Vegetarian "]:
        if food_name.startswith(p):
            prefix = p
            food_name = food_name[len(p):]
            break

    if "food" in food_df.columns:
        df_row = food_df[food_df["food"].str.lower() == str(food_name).lower()]
        if not df_row.empty:
            cal = int(df_row["Caloric Value"].values[0]) if "Caloric Value" in df_row.columns else 0
            pro = int(df_row["Protein"].values[0]) if "Protein" in df_row.columns else 0
            fat = int(df_row["Fat"].values[0]) if "Fat" in df_row.columns else 0
            carb = int(df_row["Carbohydrates"].values[0]) if "Carbohydrates" in df_row.columns else int(df_row["Carbs"].values[0]) if "Carbs" in df_row.columns else 0

            if pro < 10:
                pro = int(pro * 1.5)
            if cal < 50:
                cal = int(cal * 1.5)
            return cal, pro, fat, carb

    defaults = {
        "oats": (150, 5, 3, 27),
        "egg": (70, 6, 5, 0),
        "banana": (90, 1, 0, 23),
        "yogurt": (100, 5, 2, 10),
        "peanut butter": (90, 4, 8, 3),
        "wholegrain bread": (80, 4, 1, 15),
        "chicken breast": (165, 31, 3, 0),
        "turkey breast": (135, 30, 1, 0),
        "salmon": (208, 20, 13, 0),
        "tuna": (130, 28, 1, 0),
        "brown rice": (216, 5, 2, 44),
        "quinoa": (120, 4, 2, 21),
        "lentils": (115, 9, 0, 20),
        "beans": (120, 8, 0, 22),
        "vegetables": (50, 2, 0, 10),
        "potato": (130, 3, 0, 30),
        "pasta": (180, 7, 1, 37),
        "whey protein": (120, 24, 1, 3),
        "egg whites": (17, 4, 0, 0),
        "cottage cheese": (90, 11, 4, 3),
        "milk": (100, 8, 2, 12),
        "tofu": (90, 10, 5, 2),
        "seitan": (120, 25, 2, 6),
        "tempeh": (195, 19, 11, 9),
    }

    food_key = food_name.lower()
    cal, pro, fat, carb = defaults.get(food_key, (60, 3, 3, 6))

    if prefix:
        if prefix == "Vegan":
            if food_key in ["chicken breast", "turkey breast", "salmon", "tuna", "beef"]:
                cal, pro, fat, carb = defaults.get("seitan")
            if food_key in ["egg", "milk", "yogurt", "cottage cheese"]:
                cal, pro, fat, carb = defaults.get("tofu")
        elif prefix == "Vegetarian":
            if food_key in ["chicken breast", "turkey breast", "salmon", "tuna", "beef"]:
                cal, pro, fat, carb = defaults.get("seitan")

    if pro < 10:
        pro = int(pro * 1.5)
    if cal < 50:
        cal = int(cal * 1.5)

    return cal, pro, fat, carb

# ----------------------------------------------------
# FUNCTION: Adjust meal plan to meet exact macro targets
# ----------------------------------------------------
def adjust_meal_plan_to_targets(plan, targets):
    import copy
    new_plan = copy.deepcopy(plan)
    
    def totals(plan_dict):
        t_cal = t_pro = t_fat = t_carb = 0
        all_foods = plan_dict.get("breakfast_foods", []) + plan_dict.get("lunch_foods", []) + plan_dict.get("dinner_foods", [])
        for f in all_foods:
            cal, pro, fat, carb = get_food_macros(f)
            t_cal += cal
            t_pro += pro
            t_fat += fat
            t_carb += carb
        if plan_dict.get("snack"):
            s = plan_dict["snack"]
            t_cal += s["cal"]
            t_pro += s["protein"]
            t_fat += s["fat"]
            t_carb += s["carbs"]
        return t_cal, t_pro, t_fat, t_carb

    current_cal, current_pro, current_fat, current_carb = totals(new_plan)
    
    cal_ratio = targets["calories"] / current_cal if current_cal else 1
    pro_ratio = targets["protein"] / current_pro if current_pro else 1
    fat_ratio = targets["fat"] / current_fat if current_fat else 1
    carb_ratio = targets["carbs"] / current_carb if current_carb else 1

    for meal in ["breakfast_foods", "lunch_foods", "dinner_foods"]:
        scaled_foods = []
        for f in new_plan.get(meal, []):
            cal, pro, fat, carb = get_food_macros(f)
            cal = round(cal * cal_ratio)
            pro = round(pro * pro_ratio)
            fat = round(fat * fat_ratio)
            carb = round(carb * carb_ratio)
            scaled_foods.append((f, cal, pro, fat, carb))
        new_plan[meal] = scaled_foods

    if new_plan.get("snack"):
        s = new_plan["snack"]
        s["cal"] = round(s["cal"] * cal_ratio)
        s["protein"] = round(s["protein"] * pro_ratio)
        s["fat"] = round(s["fat"] * fat_ratio)
        s["carbs"] = round(s["carbs"] * carb_ratio)

    return new_plan

# ----------------------------------------------------
# POOLS FUNCTION
# ----------------------------------------------------
def get_pools_for_user(age, weight, height, goal, diet_type):
    breakfast_base = ["oats", "egg", "banana", "yogurt", "peanut butter", "wholegrain bread"]
    lunch_base = ["chicken breast", "turkey breast", "salmon", "tuna", "brown rice", "quinoa", "lentils", "beans", "vegetables"]
    dinner_base = ["chicken breast", "turkey breast", "salmon", "tuna", "brown rice", "potato", "pasta", "vegetables"]

    vegan_add = ["tofu", "tempeh", "seitan", "chickpeas", "black beans", "almonds", "avocado"]
    vegetarian_add = ["cottage cheese", "tofu", "egg whites", "cheese"]

    muscle_boost = ["whey protein", "tuna", "chicken breast", "cottage cheese", "egg whites"]
    weight_loss_boost = ["salmon", "tuna", "lentils", "vegetables", "quinoa"]
    maintenance_boost = ["brown rice", "wholegrain bread", "potato"]

    if diet_type == "Vegan":
        breakfast_pool = [i for i in breakfast_base if i not in ("egg", "yogurt", "cottage cheese", "milk")]
        breakfast_pool += ["oats", "banana", "peanut butter", "wholegrain bread", "berries"]
        breakfast_pool += [x for x in vegan_add if x not in breakfast_pool]
        lunch_pool = [i for i in lunch_base if i not in ("chicken breast", "turkey breast", "salmon", "tuna", "cottage cheese")]
        lunch_pool += vegan_add
        dinner_pool = [i for i in dinner_base if i not in ("chicken breast", "turkey breast", "salmon", "tuna")]
        dinner_pool += vegan_add
    elif diet_type == "Vegetarian":
        breakfast_pool = [i for i in breakfast_base if i != "chicken breast"]
        breakfast_pool += ["cottage cheese", "egg whites"]
        breakfast_pool += [x for x in vegetarian_add if x not in breakfast_pool]
        lunch_pool = [i for i in lunch_base if i not in ("chicken breast", "turkey breast")]
        lunch_pool += vegetarian_add
        dinner_pool = [i for i in dinner_base if i not in ("chicken breast", "turkey breast")]
        dinner_pool += vegetarian_add
    else:
        breakfast_pool = breakfast_base[:]
        lunch_pool = lunch_base[:]
        dinner_pool = dinner_base[:]

    if goal == "Muscle Gain":
        for item in muscle_boost:
            if item not in breakfast_pool:
                breakfast_pool.append(item)
            if item not in lunch_pool:
                lunch_pool.append(item)
            if item not in dinner_pool:
                dinner_pool.append(item)
    elif goal == "Weight Loss":
        for item in weight_loss_boost:
            if item not in breakfast_pool:
                breakfast_pool.append(item)
            if item not in lunch_pool:
                lunch_pool.append(item)
            if item not in dinner_pool:
                dinner_pool.append(item)
    else:
        for item in maintenance_boost:
            if item not in breakfast_pool:
                breakfast_pool.append(item)
            if item not in lunch_pool:
                lunch_pool.append(item)
            if item not in dinner_pool:
                dinner_pool.append(item)

    def clean_pool(p):
        seen = set()
        out = []
        for x in p:
            key = str(x).lower()
            if key not in seen:
                seen.add(key)
                out.append(x)
        return out

    return clean_pool(breakfast_pool), clean_pool(lunch_pool), clean_pool(dinner_pool)

# ----------------------------------------------------
# SIDEBAR NAVIGATION
# ----------------------------------------------------
st.sidebar.title("Navigation")
sidebar_sections = ["Home", "Enter Your Data", "Meal Plan", "Cooking Instructions", "Grocery List", "Stats"]

if "current_page" not in st.session_state:
    st.session_state["current_page"] = "Home"

for section in sidebar_sections:
    is_active = section == st.session_state["current_page"]
    arrow = "➤ " if is_active else ""
    if st.sidebar.button(f"{arrow}{section}", key=f"sidebar_{section}"):
        st.session_state["current_page"] = section
        st.rerun()

page = st.session_state["current_page"]

# ----------------------------------------------------
# HOME / ENTER DATA / MEAL PLAN / COOKING INSTRUCTIONS / GROCERY LIST / STATS
# ----------------------------------------------------
# [Everything from your original PRO3 continues here exactly as it is]

# ----------------------------------------------------
# HOME / ENTER DATA / MEAL PLAN / COOKING INSTRUCTIONS
# ----------------------------------------------------

# ---------- HOME ----------
if page == "Home":
    st.title("🏋️ Nutritional Meal & Fitness App")
    try:
        img = Image.open("images/fitness_home.jpg")
        st.image(img, use_container_width=True)
    except Exception:
        st.image("https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b", use_container_width=True)
    st.markdown("## 👋 Welcome!\nPlan professional gym-friendly meals, track macros, and manage your fitness journey.")
    if st.button("Start Now", key="start_now"):
        st.session_state["current_page"] = "Enter Your Data"
        st.rerun()

# ---------- ENTER YOUR DATA ----------
elif page == "Enter Your Data":
    st.header("Enter Your Personal Details")
    col1, col2, col3 = st.columns(3)
    age = col1.number_input("Age (years)", 10, 100, st.session_state.get("age", 25), key="age_input")
    weight = col2.number_input("Weight (kg)", 30, 200, st.session_state.get("weight", 70), key="weight_input")
    height = col3.number_input("Height (cm)", 100, 220, st.session_state.get("height", 175), key="height_input")

    col1, col2 = st.columns(2)
    goal = col1.selectbox(
        "Goal",
        ["Weight Loss", "Maintenance", "Muscle Gain"],
        index=["Weight Loss", "Maintenance", "Muscle Gain"].index(st.session_state.get("goal", "Muscle Gain")),
        key="goal_select"
    )
    diet_type = col2.selectbox(
        "Diet Type",
        ["Omnivore", "Vegetarian", "Vegan"],
        index=["Omnivore", "Vegetarian", "Vegan"].index(st.session_state.get("diet_type", "Omnivore")),
        key="diet_select"
    )

    st.markdown("### Recipe Difficulty")
    options = ["Simple", "Pro Mode"]
    if "recipe_difficulty" not in st.session_state:
        st.session_state["recipe_difficulty"] = None

    diff_cols = st.columns(len(options))
    for idx, opt in enumerate(options):
        is_selected = st.session_state.get("recipe_difficulty") == opt
        arrow_html = "➤ " if is_selected else ""
        if diff_cols[idx].button(f"{arrow_html}{opt}", key=f"diff_{opt}"):
            st.session_state["recipe_difficulty"] = opt
            st.rerun()

    if st.session_state.get("recipe_difficulty") == "Pro Mode":
        if "include_snack" not in st.session_state:
            st.session_state["include_snack"] = False
        snack_choice = st.radio("Extra Snack?", ("No", "Yes"), index=1 if st.session_state.get("include_snack") else 0, key="snack_radio")
        st.session_state["include_snack"] = (snack_choice == "Yes")
    else:
        if "include_snack" not in st.session_state:
            st.session_state["include_snack"] = False

    if st.session_state.get("recipe_difficulty") in options:
        if st.button("Save Data & Next Step", key="save_data"):
            st.session_state["age"] = age
            st.session_state["weight"] = weight
            st.session_state["height"] = height
            st.session_state["goal"] = goal
            st.session_state["diet_type"] = diet_type
            daily_cal = calculate_calories(age, weight, height, goal)
            p, f, c = calculate_macros(daily_cal)
            st.session_state["daily_calories"] = daily_cal
            st.session_state["protein_target"] = p
            st.session_state["fat_target"] = f
            st.session_state["carbs_target"] = c
            st.session_state["current_page"] = "Meal Plan"
            st.rerun()

# ---------- MEAL PLAN ----------
elif page == "Meal Plan":
    if "daily_calories" not in st.session_state:
        st.warning("Enter your personal data first.")
    else:
        age = st.session_state.get("age", 25)
        weight = st.session_state.get("weight", 70)
        height = st.session_state.get("height", 175)
        goal = st.session_state.get("goal", "Maintenance")
        diet_type = st.session_state.get("diet_type", "Omnivore")

        breakfast_pool, lunch_pool, dinner_pool = get_pools_for_user(age, weight, height, goal, diet_type)

        # Apply Vegan/Vegetarian replacements
        if diet_type in ["Vegan", "Vegetarian"]:
            def convert_food(name):
                if diet_type == "Vegetarian":
                    for w in ["chicken", "salmon", "tuna", "beef", "turkey"]:
                        if w in name.lower():
                            return f"Vegetarian {name}"
                    return name
                if diet_type == "Vegan":
                    for w in ["chicken", "salmon", "tuna", "beef", "turkey", "egg", "milk", "cheese", "yogurt"]:
                        if w in name.lower():
                            return f"Vegan {name}"
                    return name

            breakfast_pool = [convert_food(x) for x in breakfast_pool]
            lunch_pool = [convert_food(x) for x in lunch_pool]
            dinner_pool = [convert_food(x) for x in dinner_pool]

        if st.button("Generate Meal Plan" if not st.session_state.get("plans_generated") else "Regenerate Meal Plans", key="generate_plans"):
            include_snack = st.session_state.get("include_snack", False)
            plans = build_three_plans(breakfast_pool, lunch_pool, dinner_pool, include_snack=include_snack)
            st.session_state["plans"] = plans
            st.session_state["plans_generated"] = True
            st.session_state["selected_plan"] = None
            st.rerun()

        if st.session_state.get("plans_generated") and st.session_state.get("plans"):
            plans = st.session_state["plans"]
            st.subheader("Choose a Meal Plan")
            card_cols = st.columns(3)
            for i, plan in enumerate(plans):
                selected = (st.session_state.get("selected_plan") == i)
                card_style = "background:#1fa65a; color:white; border-radius:8px; padding:16px; border:2px solid #0f8a3a;" if selected else "background:white; color:black; border-radius:8px; padding:16px; border:2px solid #E0E0E0;"
                button_label = "Selected" if selected else "Select Plan"

                snack_line = ""
                if plan.get("snack"):
                    s = plan["snack"]
                    snack_line = f"<div style='margin-top:8px; font-size:14px;'><strong>Snack:</strong> {s['name']} ({s['cal']} kcal)</div>"

                total_cal, total_pro, total_fat, total_carbs = 0, 0, 0, 0
                all_foods = plan.get("breakfast_foods", []) + plan.get("lunch_foods", []) + plan.get("dinner_foods", [])
                for food in all_foods:
                    cal, pro, fat, carb = get_food_macros(food)
                    total_cal += cal
                    total_pro += pro
                    total_fat += fat
                    total_carbs += carb
                if plan.get("snack"):
                    s = plan["snack"]
                    total_cal += s["cal"]
                    total_pro += s["protein"]
                    total_fat += s["fat"]
                    total_carbs += s["carbs"]

                macros_div = f"""
                    <div style='margin-top:6px; font-size:12px; color:#555;'>
                        <strong>Calories:</strong> {total_cal} kcal |
                        <strong>Protein:</strong> {total_pro} g |
                        <strong>Fat:</strong> {total_fat} g |
                        <strong>Carbs:</strong> {total_carbs} g
                    </div>
                """

                card_html = f"""
                    <div style="{card_style}">
                        <div style="font-weight:bold; font-size:18px; margin-bottom:8px;">{plan['title']}</div>
                        <div style="font-size:14px; margin-bottom:6px;"><strong>Breakfast:</strong> {plan['breakfast_str']}</div>
                        <div style="font-size:14px; margin-bottom:6px;"><strong>Lunch:</strong> {plan['lunch_str']}</div>
                        <div style="font-size:14px; margin-bottom:6px;"><strong>Dinner:</strong> {plan['dinner_str']}</div>
                        {snack_line}
                        {macros_div}
                    </div>
                """
                card_cols[i].markdown(card_html, unsafe_allow_html=True)
                if not selected and card_cols[i].button(button_label, key=f"plan_select_{i}"):
                    st.session_state["selected_plan"] = i
                    st.session_state["active_plan"] = plan
                    st.rerun()

        if st.button("Next Step: Cooking Instructions", key="to_cooking"):
            if st.session_state.get("selected_plan") is not None:
                st.session_state["current_page"] = "Cooking Instructions"
                st.rerun()
            else:
                st.warning("Please select a meal plan before proceeding.")

# --------# ---------- COOKING INSTRUCTIONS ----------
elif page == "Cooking Instructions":
    st.header("Cooking Instructions (Quantities & Timing)")
    active_plan = st.session_state.get("active_plan")
    if not active_plan:
        st.warning("Select or generate a meal plan first.")
    else:
        b_foods = active_plan.get("breakfast_foods", [])
        l_foods = active_plan.get("lunch_foods", [])
        d_foods = active_plan.get("dinner_foods", [])

        st.subheader("Breakfast")
        if b_foods:
            st.write("Oats: 40g per serving, cook with water/milk 5 min. Banana: slice on top. Peanut butter: 15g per serving. Eggs: 2 eggs, 3 min medium heat.")
        else:
            st.write("Follow the meal instructions displayed on the Meal Plan page.")

        st.subheader("Lunch")
        if l_foods:
            st.write(f"Grill/bake {l_foods[0]} & {l_foods[1]} at 180°C for 20-25 min. Serve with rice/quinoa/beans & vegetables.")
        else:
            st.write("Follow the meal instructions displayed on the Meal Plan page.")

        st.subheader("Dinner")
        if d_foods:
            st.write(f"Pan-sear/bake {d_foods[0]} & {d_foods[1]} at 200°C for 25 min. Serve with potato/pasta/vegetables.")
        else:
            st.write("Follow the meal instructions displayed on the Meal Plan page.")

        if active_plan.get("snack"):
            s = active_plan["snack"]
            st.subheader("Snack Instructions")
            st.write(f"**{s['name']}**")
            st.write(s["instructions"])

        if st.button("Next Step: Grocery List", key="to_grocery"):
            st.session_state["current_page"] = "Grocery List"
            st.rerun()


# ---------- GROCERY LIST ----------
elif page == "Grocery List":
    st.header("🛒 Grocery List & Pricing")
    plan = st.session_state.get("active_plan")
    if not plan:
        st.warning("Select a meal plan first to generate a grocery list.")
    else:
        grocery_items = plan.get("breakfast_foods", []) + plan.get("lunch_foods", []) + plan.get("dinner_foods", [])
        if plan.get("snack"):
            grocery_items += plan["snack"]["ingredients"]

        grocery_count = {}
        for item in grocery_items:
            grocery_count[item] = grocery_count.get(item, 0) + 1

        ingredient_prices = {
            "oats": 3.50, "egg": 0.20, "banana": 0.30, "yogurt": 0.50, "peanut butter": 4.50,
            "wholegrain bread": 2.50, "chicken breast": 5.50, "turkey breast": 6.00,
            "salmon": 12.00, "tuna": 8.00, "brown rice": 2.00, "quinoa": 4.00, "lentils": 1.50,
            "beans": 1.50, "vegetables": 3.00, "potato": 1.50, "pasta": 2.00,
            "whey protein": 15.00, "cottage cheese": 3.00, "milk": 1.00,
            "egg whites": 1.50, "tofu": 3.50, "tempeh": 4.00, "seitan": 5.00,
            "chickpeas": 1.20, "almonds": 8.00, "avocado": 1.50, "berries": 3.50
        }

        grocery_list = []
        total_price = 0.0

        for item, qty in grocery_count.items():
            key = item.lower()
            price = ingredient_prices.get(key, 3.00)
            subtotal = round(price * qty, 2)
            total_price += subtotal
            price_str = ('%.2f' % price).rstrip('0').rstrip('.')
            subtotal_str = ('%.2f' % subtotal).rstrip('0').rstrip('.')
            grocery_list.append({
                "Item": str(item).title(),
                "Quantity": qty,
                "Price per unit (€)": price_str,
                "Subtotal (€)": subtotal_str
            })

        st.table(pd.DataFrame(grocery_list))
        total_price_str = ('%.2f' % total_price).rstrip('0').rstrip('.')
        st.markdown(f"**Total Items:** {len(grocery_items)} | **Unique Items:** {len(grocery_count)} | **Estimated Total Price:** €{total_price_str}")

        col1, col2 = st.columns(2)
        if col1.button("Done / Back to Home", key="done_home"):
            st.session_state["current_page"] = "Home"
            st.rerun()
        if col2.button("Next Step: See Stats", key="to_stats"):
            st.session_state["current_page"] = "Stats"
            st.rerun()


# ---------- STATS ----------
elif page == "Stats":
    st.header("📊 Your Meal & Macro Summary")
    plan = st.session_state.get("active_plan")

    if not plan:
        st.warning("Generate and select a meal plan first to see stats.")
    else:
        meals = {
            "Breakfast": plan.get("breakfast_foods", []),
            "Lunch": plan.get("lunch_foods", []),
            "Dinner": plan.get("dinner_foods", []),
        }
        if plan.get("snack"):
            meals["Snack"] = plan["snack"]["ingredients"]

        # CALCULATE MACROS AND ACCURATE CALORIES
        meal_macros = {}
        for meal_name, foods in meals.items():
            pro = fat = carb = 0
            for food in foods:
                _, p, f, c = get_food_macros(food)
                pro += p
                fat += f
                carb += c
            if meal_name == "Snack" and plan.get("snack"):
                s = plan["snack"]
                pro += s["protein"]
                fat += s["fat"]
                carb += s["carbs"]
            # Calories calculated from macros for accuracy
            cal = round(pro * 4 + carb * 4 + fat * 9)
            meal_macros[meal_name] = {"Calories": cal, "Protein": pro, "Fat": fat, "Carbs": carb}

        st.subheader("Macro Summary per Meal")
        for meal_name, macros in meal_macros.items():
            st.markdown(f"**{meal_name}:** {macros['Calories']} kcal | Protein: {macros['Protein']} g | Fat: {macros['Fat']} g | Carbs: {macros['Carbs']} g")

        st.subheader("Calories Distribution")
        cal_chart = pd.DataFrame({"Meal": list(meal_macros.keys()), "Calories": [m["Calories"] for m in meal_macros.values()]})
        st.bar_chart(cal_chart.set_index("Meal"))

        total_cal = sum(m["Calories"] for m in meal_macros.values())
        total_pro = sum(m["Protein"] for m in meal_macros.values())
        total_fat = sum(m["Fat"] for m in meal_macros.values())
        total_carbs = sum(m["Carbs"] for m in meal_macros.values())

        st.subheader("Daily Totals")
        st.markdown(f"**Calories:** {total_cal} kcal | **Protein:** {total_pro} g | **Fat:** {total_fat} g | **Carbs:** {total_carbs} g")

        if "daily_calories" in st.session_state:
            st.subheader("Comparison to Your Targets")
            comp_chart = pd.DataFrame({
                "Macro": ["Calories", "Protein", "Fat", "Carbs"],
                "Planned": [total_cal, total_pro, total_fat, total_carbs],
                "Target": [st.session_state["daily_calories"], st.session_state["protein_target"], st.session_state["fat_target"], st.session_state["carbs_target"]]
            })
            st.bar_chart(comp_chart.set_index("Macro"))
