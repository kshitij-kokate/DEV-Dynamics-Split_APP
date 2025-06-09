from flask import Blueprint, request, jsonify
from app import db
from models import Person, Expense, ExpenseSplit, SplitMethod
from settlement_calculator import SettlementCalculator
from decimal import Decimal, InvalidOperation
import logging
from sqlalchemy.exc import SQLAlchemyError

api = Blueprint('api', __name__)

@api.errorhandler(SQLAlchemyError)
def handle_db_error(error):
    logging.error(f"Database error: {str(error)}")
    return create_response(
        success=False,
        message="A database error occurred",
        data={"error": str(error) if api.debug else "Internal server error"},
        status_code=500
    )

@api.route('/health')
def health_check():
    try:
        db.session.execute('SELECT 1')
        return create_response(
            success=True,
            message="API and database are healthy",
            data={"database": "connected", "status": "healthy"}
        )
    except Exception as e:
        return create_response(
            success=False,
            message="Database connection failed",
            data={"error": str(e)},
            status_code=503
        )

def create_response(success=True, data=None, message="", status_code=200):
    """Create standardized API response"""
    response = {
        'success': success,
        'data': data,
        'message': message
    }
    return jsonify(response), status_code

def validate_expense_data(data):
    """Validate expense data"""
    errors = []
    
    if not data.get('amount'):
        errors.append("Amount is required")
    else:
        try:
            amount = Decimal(str(data['amount']))
            if amount <= 0:
                errors.append("Amount must be greater than 0")
        except (InvalidOperation, ValueError):
            errors.append("Amount must be a valid number")
    
    if not data.get('description') or not data['description'].strip():
        errors.append("Description is required and cannot be empty")
    
    if not data.get('paid_by') or not data['paid_by'].strip():
        errors.append("paid_by is required and cannot be empty")
    
    split_method = data.get('split_method', 'equal')
    if split_method not in ['equal', 'exact', 'percentage']:
        errors.append("split_method must be one of: equal, exact, percentage")
    
    if split_method in ['exact', 'percentage'] and 'splits' in data:
        splits = data.get('splits', [])
        if not splits:
            errors.append(f"splits array is required for {split_method} split method")
        else:
            errors.extend(validate_splits(splits, split_method, data.get('amount')))
    
    return errors

def validate_splits(splits, split_method, total_amount):
    """Validate splits array based on split method"""
    errors = []
    
    if not isinstance(splits, list):
        errors.append("splits must be an array")
        return errors
    
    if len(splits) == 0:
        errors.append("splits array cannot be empty")
        return errors
    
    people_names = []
    for split in splits:
        if not isinstance(split, dict):
            errors.append("Each split must be an object")
            continue
            
        person = split.get('person', '').strip()
        if not person:
            errors.append("Each split must have a person name")
            continue
            
        if person in people_names:
            errors.append(f"Duplicate person '{person}' in splits")
        else:
            people_names.append(person)
    
    if split_method == 'exact':
        total_splits = Decimal('0')
        for split in splits:
            try:
                amount = Decimal(str(split.get('amount', 0)))
                if amount <= 0:
                    errors.append(f"Split amount for {split.get('person', 'unknown')} must be greater than 0")
                total_splits += amount
            except (InvalidOperation, ValueError):
                errors.append(f"Invalid amount for {split.get('person', 'unknown')}")
        
        if total_amount and abs(total_splits - Decimal(str(total_amount))) > Decimal('0.01'):
            errors.append(f"Split amounts ({total_splits}) must equal total expense amount ({total_amount})")
    
    elif split_method == 'percentage':
        total_percentage = Decimal('0')
        for split in splits:
            try:
                percentage = Decimal(str(split.get('percentage', 0)))
                if percentage <= 0 or percentage > 100:
                    errors.append(f"Percentage for {split.get('person', 'unknown')} must be between 0 and 100")
                total_percentage += percentage
            except (InvalidOperation, ValueError):
                errors.append(f"Invalid percentage for {split.get('person', 'unknown')}")
        
        if abs(total_percentage - Decimal('100')) > Decimal('0.01'):
            errors.append(f"Percentages must total 100% (current total: {total_percentage}%)")
    
    return errors

@api.route('/expenses', methods=['POST'])
def create_expense():
    """Create a new expense"""
    try:
        data = request.get_json()
        if not data:
            return create_response(False, None, "Request body is required", 400)
        
        errors = validate_expense_data(data)
        if errors:
            return create_response(False, None, "; ".join(errors), 400)
        
        paid_by_name = data['paid_by'].strip()
        person = Person.query.filter_by(name=paid_by_name).first()
        if not person:
            person = Person(name=paid_by_name)
            db.session.add(person)
            db.session.flush()
        
        split_method_str = data.get('split_method', 'equal')
        split_method = SplitMethod(split_method_str)
        
        expense = Expense(
            amount=Decimal(str(data['amount'])),
            description=data['description'].strip(),
            paid_by_id=person.id,
            split_method=split_method
        )
        db.session.add(expense)
        db.session.flush()
        
        if split_method_str == 'equal':
            participants = data.get('participants', [paid_by_name])
            if paid_by_name not in participants:
                participants.append(paid_by_name)
            SettlementCalculator.create_equal_splits(expense.id, participants)
        elif split_method_str in ['exact', 'percentage']:
            SettlementCalculator.create_custom_splits(expense.id, data['splits'], split_method_str)
        
        db.session.commit()
        
        return create_response(True, expense.to_dict(), "Expense created successfully", 201)
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error creating expense: {str(e)}")
        return create_response(False, None, f"Internal server error: {str(e)}", 500)

@api.route('/expenses', methods=['GET'])
def get_expenses():
    """Get all expenses"""
    try:
        expenses = Expense.query.all()
        return create_response(True, [expense.to_dict() for expense in expenses])
    except Exception as e:
        logging.error(f"Error getting expenses: {str(e)}")
        return create_response(False, None, f"Internal server error: {str(e)}", 500)

@api.route('/people', methods=['GET'])
def get_people():
    """Get all people"""
    try:
        people = Person.query.all()
        return create_response(True, [person.to_dict() for person in people])
    except Exception as e:
        logging.error(f"Error getting people: {str(e)}")
        return create_response(False, None, f"Internal server error: {str(e)}", 500)

@api.route('/balances', methods=['GET'])
def get_balances():
    """Get balances for all people"""
    try:
        calculator = SettlementCalculator()
        balances = calculator.calculate_balances()
        return create_response(True, balances)
    except Exception as e:
        logging.error(f"Error calculating balances: {str(e)}")
        return create_response(False, None, f"Internal server error: {str(e)}", 500)

@api.route('/settlements', methods=['GET'])
def get_settlements():
    """Get settlement plan"""
    try:
        calculator = SettlementCalculator()
        settlements = calculator.calculate_settlements()
        return create_response(True, settlements)
    except Exception as e:
        logging.error(f"Error calculating settlements: {str(e)}")
        return create_response(False, None, f"Internal server error: {str(e)}", 500)
