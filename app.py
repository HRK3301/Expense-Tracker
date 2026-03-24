from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from sqlalchemy import func
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expenses.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ── Models ──────────────────────────────────────────────────────────────────

class Category(db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    name     = db.Column(db.String(50), nullable=False, unique=True)
    color    = db.Column(db.String(7), default='#6366f1')
    icon     = db.Column(db.String(10), default='💰')
    expenses = db.relationship('Expense', backref='category_ref', lazy=True)

    def to_dict(self):
        return {'id': self.id, 'name': self.name,
                'color': self.color, 'icon': self.icon}


class Expense(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(100), nullable=False)
    amount      = db.Column(db.Float, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    tags        = db.Column(db.String(200), default='')
    date        = db.Column(db.Date, nullable=False, default=date.today)
    note        = db.Column(db.Text, default='')
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'amount': self.amount,
            'category_id': self.category_id,
            'category': self.category_ref.to_dict() if self.category_ref else None,
            'tags': self.tags.split(',') if self.tags else [],
            'date': self.date.isoformat(),
            'note': self.note,
        }

# ── Routes: Pages ────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')

# ── Routes: Categories ───────────────────────────────────────────────────────

@app.route('/api/categories', methods=['GET'])
def get_categories():
    cats = Category.query.all()
    return jsonify([c.to_dict() for c in cats])

@app.route('/api/categories', methods=['POST'])
def create_category():
    d = request.json
    cat = Category(name=d['name'], color=d.get('color', '#6366f1'), icon=d.get('icon', '💰'))
    db.session.add(cat)
    db.session.commit()
    return jsonify(cat.to_dict()), 201

@app.route('/api/categories/<int:cid>', methods=['DELETE'])
def delete_category(cid):
    cat = Category.query.get_or_404(cid)
    db.session.delete(cat)
    db.session.commit()
    return jsonify({'ok': True})

# ── Routes: Expenses ─────────────────────────────────────────────────────────

@app.route('/api/expenses', methods=['GET'])
def get_expenses():
    q = Expense.query
    if cat := request.args.get('category'):
        q = q.filter_by(category_id=int(cat))
    if tag := request.args.get('tag'):
        q = q.filter(Expense.tags.contains(tag))
    expenses = q.order_by(Expense.date.desc()).all()
    return jsonify([e.to_dict() for e in expenses])

@app.route('/api/expenses', methods=['POST'])
def create_expense():
    d = request.json
    exp = Expense(
        title=d['title'],
        amount=float(d['amount']),
        category_id=int(d['category_id']),
        tags=','.join(d.get('tags', [])),
        date=date.fromisoformat(d.get('date', date.today().isoformat())),
        note=d.get('note', '')
    )
    db.session.add(exp)
    db.session.commit()
    return jsonify(exp.to_dict()), 201

@app.route('/api/expenses/<int:eid>', methods=['PUT'])
def update_expense(eid):
    exp = Expense.query.get_or_404(eid)
    d   = request.json
    exp.title       = d.get('title', exp.title)
    exp.amount      = float(d.get('amount', exp.amount))
    exp.category_id = int(d.get('category_id', exp.category_id))
    exp.tags        = ','.join(d.get('tags', exp.tags.split(',') if exp.tags else []))
    exp.date        = date.fromisoformat(d.get('date', exp.date.isoformat()))
    exp.note        = d.get('note', exp.note)
    db.session.commit()
    return jsonify(exp.to_dict())

@app.route('/api/expenses/<int:eid>', methods=['DELETE'])
def delete_expense(eid):
    exp = Expense.query.get_or_404(eid)
    db.session.delete(exp)
    db.session.commit()
    return jsonify({'ok': True})

# ── Routes: Analytics ────────────────────────────────────────────────────────

@app.route('/api/analytics', methods=['GET'])
def analytics():
    # Total per category
    by_cat = (
        db.session.query(Category.name, Category.color, Category.icon,
                         func.sum(Expense.amount).label('total'))
        .join(Expense, Expense.category_id == Category.id)
        .group_by(Category.id)
        .all()
    )

    # Monthly totals (last 6 months)
    monthly = (
        db.session.query(
            func.strftime('%Y-%m', Expense.date).label('month'),
            func.sum(Expense.amount).label('total')
        )
        .group_by('month')
        .order_by('month')
        .limit(6)
        .all()
    )

    total = db.session.query(func.sum(Expense.amount)).scalar() or 0

    return jsonify({
        'total': round(total, 2),
        'by_category': [
            {'name': r.name, 'color': r.color, 'icon': r.icon, 'total': round(r.total, 2)}
            for r in by_cat
        ],
        'monthly': [
            {'month': r.month, 'total': round(r.total, 2)}
            for r in monthly
        ],
    })

# ── Seed & Init ───────────────────────────────────────────────────────────────

def seed():
    if Category.query.count() == 0:
        defaults = [
            ('Food & Dining',   '#f97316', '🍔'),
            ('Transport',       '#3b82f6', '🚗'),
            ('Shopping',        '#ec4899', '🛍️'),
            ('Entertainment',   '#8b5cf6', '🎬'),
            ('Health',          '#10b981', '💊'),
            ('Utilities',       '#f59e0b', '⚡'),
        ]
        for name, color, icon in defaults:
            db.session.add(Category(name=name, color=color, icon=icon))

        # Sample expenses
        cats = {c.name: c.id for c in Category.query.all()}
        samples = [
            ('Grocery run',   1200, 'Food & Dining',   '2025-03-01'),
            ('Uber ride',      350, 'Transport',        '2025-03-03'),
            ('Netflix',        649, 'Entertainment',    '2025-03-05'),
            ('Pharmacy',       450, 'Health',           '2025-03-08'),
            ('Electricity',   1500, 'Utilities',        '2025-03-10'),
            ('Zomato order',   580, 'Food & Dining',   '2025-03-12'),
            ('Amazon order',  2200, 'Shopping',         '2025-03-15'),
            ('Metro card',     200, 'Transport',        '2025-03-18'),
        ]
        for title, amount, cat, d in samples:
            db.session.add(Expense(
                title=title, amount=amount,
                category_id=cats[cat],
                date=date.fromisoformat(d)
            ))
        db.session.commit()

with app.app_context():
    db.create_all()
    seed()

if __name__ == '__main__':
    app.run(debug=True)
