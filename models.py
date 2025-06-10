from extensions import db
from datetime import datetime
from decimal import Decimal
from enum import Enum

class SplitMethod(Enum):
    EQUAL = "equal"
    EXACT = "exact"
    PERCENTAGE = "percentage"

class Person(db.Model):
    __tablename__ = 'people'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    expenses_paid = db.relationship('Expense', backref='payer', lazy=True)
    expense_splits = db.relationship('ExpenseSplit', backref='person', lazy=True)
    
    def __repr__(self):
        return f'<Person {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Expense(db.Model):
    __tablename__ = 'expenses'
    
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    paid_by_id = db.Column(db.Integer, db.ForeignKey('people.id'), nullable=False)
    split_method = db.Column(db.Enum(SplitMethod), default=SplitMethod.EQUAL, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    splits = db.relationship('ExpenseSplit', backref='expense', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Expense {self.description}: ${self.amount}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'amount': float(self.amount),
            'description': self.description,
            'paid_by': self.payer.name,
            'paid_by_id': self.paid_by_id,
            'split_method': self.split_method.value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'splits': [split.to_dict() for split in self.splits]
        }

class ExpenseSplit(db.Model):
    __tablename__ = 'expense_splits'
    
    id = db.Column(db.Integer, primary_key=True)
    expense_id = db.Column(db.Integer, db.ForeignKey('expenses.id'), nullable=False)
    person_id = db.Column(db.Integer, db.ForeignKey('people.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    percentage = db.Column(db.Numeric(5, 2), nullable=True)  # For percentage splits
    
    # Unique constraint to prevent duplicate splits for same expense-person combination
    __table_args__ = (db.UniqueConstraint('expense_id', 'person_id', name='unique_expense_person_split'),)
    
    def __repr__(self):
        return f'<ExpenseSplit Expense:{self.expense_id} Person:{self.person_id} Amount:${self.amount}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'expense_id': self.expense_id,
            'person_id': self.person_id,
            'person_name': self.person.name,
            'amount': float(self.amount),
            'percentage': float(self.percentage) if self.percentage else None
        }
