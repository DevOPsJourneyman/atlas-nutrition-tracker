from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import date, timedelta
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////data/meal_tracker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ─── Models ──────────────────────────────────────────────────────────────────

class Ingredient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    unit = db.Column(db.String(20), nullable=False)  # g, ml, piece, tbsp, tsp
    stock_qty = db.Column(db.Float, default=0)
    price_per_unit = db.Column(db.Float, default=0)  # price per unit (e.g. per 100g)
    price_unit_size = db.Column(db.Float, default=100)  # the size the price applies to
    store = db.Column(db.String(50), default='')

class Meal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    meal_type = db.Column(db.String(20), nullable=False)  # smoothie, cooked, salad
    calories = db.Column(db.Integer, default=0)
    protein = db.Column(db.Float, default=0)
    fibre = db.Column(db.Float, default=0)
    ingredients_json = db.Column(db.Text, default='[]')  # [{ingredient_id, qty}]

class DailyLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    log_date = db.Column(db.Date, nullable=False)
    meal_id = db.Column(db.Integer, db.ForeignKey('meal.id'), nullable=False)
    eaten = db.Column(db.Boolean, default=False)
    meal = db.relationship('Meal', backref='logs')

class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    purchase_date = db.Column(db.Date, nullable=False, default=date.today)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredient.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    total_cost = db.Column(db.Float, nullable=False)
    store = db.Column(db.String(50), default='')
    ingredient = db.relationship('Ingredient', backref='purchases')


# ─── Seed Data ───────────────────────────────────────────────────────────────

def seed_database():
    if Ingredient.query.count() > 0:
        return  # Already seeded

    ingredients_data = [
        # Smoothie
        {'name': 'Coconut Milk (Plenish)', 'unit': 'ml', 'price_per_unit': 2.00, 'price_unit_size': 250, 'store': 'Supermarket'},
        {'name': 'Pea Protein Powder', 'unit': 'g', 'price_per_unit': 1.50, 'price_unit_size': 30, 'store': 'Online'},
        {'name': 'Spirulina', 'unit': 'tbsp', 'price_per_unit': 0.20, 'price_unit_size': 1, 'store': 'Online'},
        {'name': 'Peanut Butter', 'unit': 'tbsp', 'price_per_unit': 0.10, 'price_unit_size': 1, 'store': 'Supermarket'},
        {'name': 'Frozen Mixed Berries', 'unit': 'g', 'price_per_unit': 2.00, 'price_unit_size': 80, 'store': 'Supermarket'},
        {'name': 'Frozen Pineapple', 'unit': 'g', 'price_per_unit': 2.00, 'price_unit_size': 80, 'store': 'Supermarket'},
        {'name': 'Cinnamon', 'unit': 'tsp', 'price_per_unit': 0.05, 'price_unit_size': 1, 'store': 'Source Bulk'},
        {'name': 'Ginger Powder', 'unit': 'tsp', 'price_per_unit': 0.08, 'price_unit_size': 1, 'store': 'Source Bulk'},
        {'name': 'Banana', 'unit': 'piece', 'price_per_unit': 0.15, 'price_unit_size': 1, 'store': 'Supermarket'},
        {'name': 'Hemp Seeds', 'unit': 'tbsp', 'price_per_unit': 0.15, 'price_unit_size': 1, 'store': 'Source Bulk'},
        # Grains
        {'name': 'Quinoa', 'unit': 'g', 'price_per_unit': 4.85, 'price_unit_size': 388, 'store': 'Source Bulk'},
        {'name': 'Buckwheat', 'unit': 'g', 'price_per_unit': 2.00, 'price_unit_size': 308, 'store': 'Source Bulk'},
        # Meal 1 - Stir Fry
        {'name': 'Tempeh (Tiba)', 'unit': 'g', 'price_per_unit': 2.50, 'price_unit_size': 200, 'store': 'Supermarket'},
        {'name': 'Broccoli', 'unit': 'g', 'price_per_unit': 1.00, 'price_unit_size': 100, 'store': 'Supermarket'},
        {'name': 'Peppers', 'unit': 'g', 'price_per_unit': 0.50, 'price_unit_size': 80, 'store': 'Supermarket'},
        {'name': 'Courgette', 'unit': 'g', 'price_per_unit': 0.50, 'price_unit_size': 80, 'store': 'Supermarket'},
        {'name': 'Tamari', 'unit': 'tbsp', 'price_per_unit': 0.10, 'price_unit_size': 1, 'store': 'Supermarket'},
        {'name': 'Sesame Oil', 'unit': 'tsp', 'price_per_unit': 0.15, 'price_unit_size': 1, 'store': 'Source Bulk'},
        {'name': 'Garlic', 'unit': 'piece', 'price_per_unit': 0.05, 'price_unit_size': 1, 'store': 'Supermarket'},
        {'name': 'Ginger Root', 'unit': 'g', 'price_per_unit': 0.50, 'price_unit_size': 50, 'store': 'Supermarket'},
        {'name': 'Sesame Seeds', 'unit': 'tsp', 'price_per_unit': 0.05, 'price_unit_size': 1, 'store': 'Source Bulk'},
        {'name': 'Nutritional Yeast (Nooch)', 'unit': 'tbsp', 'price_per_unit': 0.10, 'price_unit_size': 1, 'store': 'Supermarket'},
        {'name': 'Rice Vinegar', 'unit': 'tbsp', 'price_per_unit': 0.05, 'price_unit_size': 1, 'store': 'Supermarket'},
        # Meal 2 - Bolognese
        {'name': 'Sunflower Mince', 'unit': 'g', 'price_per_unit': 6.72, 'price_unit_size': 158, 'store': 'Source Bulk'},
        {'name': 'Soy Spaghetti', 'unit': 'g', 'price_per_unit': 2.00, 'price_unit_size': 80, 'store': 'Lidl'},
        {'name': 'Tinned Tomatoes', 'unit': 'g', 'price_per_unit': 0.50, 'price_unit_size': 400, 'store': 'Supermarket'},
        {'name': 'Onion', 'unit': 'piece', 'price_per_unit': 0.25, 'price_unit_size': 1, 'store': 'Supermarket'},
        {'name': 'Olive Oil', 'unit': 'tsp', 'price_per_unit': 0.05, 'price_unit_size': 1, 'store': 'Supermarket'},
        {'name': 'Spinach', 'unit': 'g', 'price_per_unit': 1.00, 'price_unit_size': 30, 'store': 'Supermarket'},
        # Meal 3 - Tofu Scramble
        {'name': 'Firm Tofu', 'unit': 'g', 'price_per_unit': 1.75, 'price_unit_size': 400, 'store': 'Supermarket'},
        {'name': 'Mushrooms', 'unit': 'g', 'price_per_unit': 1.00, 'price_unit_size': 80, 'store': 'Supermarket'},
        {'name': 'Cherry Tomatoes', 'unit': 'g', 'price_per_unit': 1.00, 'price_unit_size': 60, 'store': 'Supermarket'},
        {'name': 'Turmeric', 'unit': 'tsp', 'price_per_unit': 0.05, 'price_unit_size': 1, 'store': 'Supermarket'},
        {'name': 'Smoked Paprika', 'unit': 'tsp', 'price_per_unit': 0.05, 'price_unit_size': 1, 'store': 'Source Bulk'},
        {'name': 'Black Salt (Kala Namak)', 'unit': 'pinch', 'price_per_unit': 0.02, 'price_unit_size': 1, 'store': 'Supermarket'},
        {'name': 'Garlic Powder', 'unit': 'tsp', 'price_per_unit': 0.05, 'price_unit_size': 1, 'store': 'Supermarket'},
        # Power Salad
        {'name': 'Spinach & Arugula Mix', 'unit': 'g', 'price_per_unit': 1.00, 'price_unit_size': 80, 'store': 'Supermarket'},
        {'name': 'Chickpeas (tinned)', 'unit': 'g', 'price_per_unit': 0.50, 'price_unit_size': 120, 'store': 'Supermarket'},
        {'name': 'Avocado', 'unit': 'piece', 'price_per_unit': 0.65, 'price_unit_size': 1, 'store': 'Supermarket'},
        {'name': 'Red Onion', 'unit': 'g', 'price_per_unit': 0.25, 'price_unit_size': 20, 'store': 'Supermarket'},
        {'name': 'Sunflower Seeds', 'unit': 'tbsp', 'price_per_unit': 0.05, 'price_unit_size': 1, 'store': 'Source Bulk'},
        {'name': 'Lemon', 'unit': 'piece', 'price_per_unit': 0.35, 'price_unit_size': 1, 'store': 'Supermarket'},
        {'name': 'Black Pepper', 'unit': 'pinch', 'price_per_unit': 0.01, 'price_unit_size': 1, 'store': 'Supermarket'},
    ]

    ingredient_map = {}
    for ing_data in ingredients_data:
        ing = Ingredient(**ing_data)
        db.session.add(ing)
        db.session.flush()
        ingredient_map[ing.name] = ing.id

    # Meals
    smoothie = Meal(
        name='Morning Smoothie',
        meal_type='smoothie',
        calories=525, protein=37, fibre=11,
        ingredients_json=json.dumps([
            {'name': 'Coconut Milk (Plenish)', 'qty': 250},
            {'name': 'Pea Protein Powder', 'qty': 30},
            {'name': 'Spirulina', 'qty': 1},
            {'name': 'Peanut Butter', 'qty': 1},
            {'name': 'Frozen Mixed Berries', 'qty': 80},
            {'name': 'Frozen Pineapple', 'qty': 80},
            {'name': 'Cinnamon', 'qty': 1},
            {'name': 'Ginger Powder', 'qty': 1},
            {'name': 'Banana', 'qty': 1},
            {'name': 'Hemp Seeds', 'qty': 1},
        ])
    )

    stir_fry = Meal(
        name='Tempeh Stir-Fry',
        meal_type='cooked',
        calories=830, protein=57, fibre=15,
        ingredients_json=json.dumps([
            {'name': 'Tempeh (Tiba)', 'qty': 200},
            {'name': 'Quinoa', 'qty': 75},
            {'name': 'Broccoli', 'qty': 100},
            {'name': 'Peppers', 'qty': 80},
            {'name': 'Courgette', 'qty': 80},
            {'name': 'Tamari', 'qty': 1},
            {'name': 'Sesame Oil', 'qty': 1},
            {'name': 'Garlic', 'qty': 2},
            {'name': 'Ginger Root', 'qty': 20},
            {'name': 'Sesame Seeds', 'qty': 1},
            {'name': 'Nutritional Yeast (Nooch)', 'qty': 1},
            {'name': 'Rice Vinegar', 'qty': 1},
        ])
    )

    bolognese = Meal(
        name='Sunflower Mince Bolognese',
        meal_type='cooked',
        calories=800, protein=72, fibre=19,
        ingredients_json=json.dumps([
            {'name': 'Sunflower Mince', 'qty': 100},
            {'name': 'Soy Spaghetti', 'qty': 80},
            {'name': 'Tinned Tomatoes', 'qty': 400},
            {'name': 'Onion', 'qty': 1},
            {'name': 'Garlic', 'qty': 2},
            {'name': 'Olive Oil', 'qty': 1},
            {'name': 'Spinach', 'qty': 30},
            {'name': 'Nutritional Yeast (Nooch)', 'qty': 1},
        ])
    )

    tofu_scramble = Meal(
        name='Tofu Scramble Bowl',
        meal_type='cooked',
        calories=780, protein=55, fibre=10,
        ingredients_json=json.dumps([
            {'name': 'Firm Tofu', 'qty': 400},
            {'name': 'Quinoa', 'qty': 75},
            {'name': 'Mushrooms', 'qty': 80},
            {'name': 'Spinach', 'qty': 50},
            {'name': 'Cherry Tomatoes', 'qty': 60},
            {'name': 'Olive Oil', 'qty': 1},
            {'name': 'Nutritional Yeast (Nooch)', 'qty': 1},
            {'name': 'Hemp Seeds', 'qty': 1},
            {'name': 'Turmeric', 'qty': 1},
            {'name': 'Garlic Powder', 'qty': 1},
            {'name': 'Smoked Paprika', 'qty': 1},
            {'name': 'Black Salt (Kala Namak)', 'qty': 1},
        ])
    )

    power_salad = Meal(
        name='Power Salad',
        meal_type='salad',
        calories=706, protein=33, fibre=19,
        ingredients_json=json.dumps([
            {'name': 'Spinach & Arugula Mix', 'qty': 80},
            {'name': 'Chickpeas (tinned)', 'qty': 120},
            {'name': 'Tempeh (Tiba)', 'qty': 80},
            {'name': 'Hemp Seeds', 'qty': 1},
            {'name': 'Sunflower Seeds', 'qty': 1},
            {'name': 'Avocado', 'qty': 0.5},
            {'name': 'Cherry Tomatoes', 'qty': 50},
            {'name': 'Red Onion', 'qty': 20},
            {'name': 'Olive Oil', 'qty': 1},
            {'name': 'Lemon', 'qty': 0.5},
            {'name': 'Tamari', 'qty': 1},
            {'name': 'Garlic Powder', 'qty': 1},
            {'name': 'Black Pepper', 'qty': 1},
        ])
    )

    for meal in [smoothie, stir_fry, bolognese, tofu_scramble, power_salad]:
        db.session.add(meal)

    db.session.commit()


# ─── Routes ──────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    today = date.today()
    tomorrow = today + timedelta(days=1)
    
    today_logs = DailyLog.query.filter_by(log_date=today).all()
    tomorrow_logs = DailyLog.query.filter_by(log_date=tomorrow).all()
    
    cooked_meals = Meal.query.filter_by(meal_type='cooked').all()
    
    today_cooked = next((l for l in today_logs if l.meal.meal_type == 'cooked'), None)
    tomorrow_cooked = next((l for l in tomorrow_logs if l.meal.meal_type == 'cooked'), None)
    
    today_total = _calc_totals(today_logs)
    
    return render_template('index.html',
        today=today,
        tomorrow=tomorrow,
        cooked_meals=cooked_meals,
        today_logs=today_logs,
        tomorrow_logs=tomorrow_logs,
        today_cooked=today_cooked,
        tomorrow_cooked=tomorrow_cooked,
        today_total=today_total
    )


@app.route('/select-meals', methods=['POST'])
def select_meals():
    today = date.today()
    tomorrow = today + timedelta(days=1)
    
    today_cooked_id = request.form.get('today_cooked')
    tomorrow_cooked_id = request.form.get('tomorrow_cooked')
    
    # Always add fixed meals (smoothie + salad) for both days
    fixed_types = ['smoothie', 'salad']
    for log_date in [today, tomorrow]:
        for meal_type in fixed_types:
            meal = Meal.query.filter_by(meal_type=meal_type).first()
            if meal:
                existing = DailyLog.query.filter_by(log_date=log_date, meal_id=meal.id).first()
                if not existing:
                    db.session.add(DailyLog(log_date=log_date, meal_id=meal.id))
        
        # Add selected cooked meal
        cooked_id = today_cooked_id if log_date == today else tomorrow_cooked_id
        if cooked_id:
            # Remove previous cooked meal for this day
            existing_cooked = DailyLog.query.join(Meal).filter(
                DailyLog.log_date == log_date,
                Meal.meal_type == 'cooked'
            ).first()
            if existing_cooked:
                db.session.delete(existing_cooked)
            db.session.add(DailyLog(log_date=log_date, meal_id=int(cooked_id)))
    
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/shopping-list')
def shopping_list():
    today = date.today()
    tomorrow = today + timedelta(days=1)
    
    # Get all meals for today and tomorrow
    logs = DailyLog.query.filter(DailyLog.log_date.in_([today, tomorrow])).all()
    
    needed = {}  # ingredient_name -> total_qty_needed
    for log in logs:
        ingredients = json.loads(log.meal.ingredients_json)
        for ing_data in ingredients:
            name = ing_data['name']
            qty = ing_data['qty']
            needed[name] = needed.get(name, 0) + qty
    
    # Compare against stock
    shopping_items = []
    total_cost = 0
    
    for name, qty_needed in needed.items():
        ing = Ingredient.query.filter_by(name=name).first()
        if not ing:
            continue
        
        in_stock = ing.stock_qty
        to_buy = max(0, qty_needed - in_stock)
        
        if to_buy > 0:
            # Calculate cost
            cost = (to_buy / ing.price_unit_size) * ing.price_per_unit
            total_cost += cost
            shopping_items.append({
                'name': name,
                'needed': qty_needed,
                'in_stock': in_stock,
                'to_buy': to_buy,
                'unit': ing.unit,
                'estimated_cost': round(cost, 2),
                'store': ing.store
            })
    
    # Group by store
    by_store = {}
    for item in shopping_items:
        store = item['store'] or 'Unknown'
        if store not in by_store:
            by_store[store] = []
        by_store[store].append(item)
    
    return render_template('shopping.html',
        by_store=by_store,
        total_cost=round(total_cost, 2),
        today=today,
        tomorrow=tomorrow
    )


@app.route('/stock')
def stock():
    ingredients = Ingredient.query.order_by(Ingredient.name).all()
    return render_template('stock.html', ingredients=ingredients)


@app.route('/update-stock', methods=['POST'])
def update_stock():
    ingredient_id = int(request.form['ingredient_id'])
    action = request.form['action']  # 'set' or 'add'
    qty = float(request.form['qty'])
    cost = request.form.get('cost', 0)
    store = request.form.get('store', '')
    
    ing = Ingredient.query.get(ingredient_id)
    if action == 'set':
        ing.stock_qty = qty
    else:
        ing.stock_qty += qty
    
    if cost and float(cost) > 0:
        purchase = Purchase(
            ingredient_id=ingredient_id,
            quantity=qty,
            total_cost=float(cost),
            store=store or ing.store
        )
        db.session.add(purchase)
        # Update price per unit
        if qty > 0:
            ing.price_per_unit = float(cost)
            ing.price_unit_size = qty
    
    db.session.commit()
    return redirect(url_for('stock'))


@app.route('/log-eaten', methods=['POST'])
def log_eaten():
    log_id = int(request.form['log_id'])
    log = DailyLog.query.get(log_id)
    if log:
        log.eaten = not log.eaten
        if log.eaten:
            # Deduct from stock
            ingredients = json.loads(log.meal.ingredients_json)
            for ing_data in ingredients:
                ing = Ingredient.query.filter_by(name=ing_data['name']).first()
                if ing:
                    ing.stock_qty = max(0, ing.stock_qty - ing_data['qty'])
        db.session.commit()
    return redirect(url_for('index'))


@app.route('/spending')
def spending():
    purchases = Purchase.query.order_by(Purchase.purchase_date.desc()).limit(50).all()
    
    # Weekly total
    today = date.today()
    week_start = today - timedelta(days=(today.weekday() + 2) % 7)
    week_purchases = Purchase.query.filter(Purchase.purchase_date >= week_start).all()
    week_total = sum(p.total_cost for p in week_purchases)
    
    return render_template('spending.html',
        purchases=purchases,
        week_total=round(week_total, 2),
        week_start=week_start
    )


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _calc_totals(logs):
    totals = {'calories': 0, 'protein': 0, 'fibre': 0}
    for log in logs:
        totals['calories'] += log.meal.calories
        totals['protein'] += log.meal.protein
        totals['fibre'] += log.meal.fibre
    return totals


# ─── Init ────────────────────────────────────────────────────────────────────

with app.app_context():
    db.create_all()
    seed_database()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
