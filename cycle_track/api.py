"""
CycleTrack API v2 - Fixed Whitelisting
"""

import frappe
from frappe.utils import getdate, flt, add_days, nowdate
from frappe import _
import json


# ============================================================================
# CUSTOMER ROUTES - WHITELISTED
# ============================================================================

@frappe.whitelist(allow_guest=False)
def route_create_customer():
    """Create a new customer"""
    try:
        data = get_request_data()
        return CustomerController.create(data)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'route_create_customer Error')
        return error_response(str(e), 500)


@frappe.whitelist(allow_guest=False)
def route_get_customer_profile():
    """Get current logged-in customer's profile"""
    try:
        return CustomerController.get_profile()
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'route_get_customer_profile Error')
        return error_response(str(e), 500)


@frappe.whitelist(allow_guest=False)
def route_list_customers():
    """Get all customers (admin only)"""
    try:
        limit = frappe.request.args.get('limit', 50)
        return CustomerController.list_all(int(limit))
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'route_list_customers Error')
        return error_response(str(e), 500)


@frappe.whitelist(allow_guest=False)
def route_get_customer():
    """Get customer by ID"""
    try:
        customer_id = frappe.request.args.get('customer_id')
        if not customer_id:
            return error_response('customer_id is required', 400)
        return CustomerController.get_by_id(customer_id)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'route_get_customer Error')
        return error_response(str(e), 500)


@frappe.whitelist(allow_guest=False)
def route_update_customer():
    """Update customer profile"""
    try:
        data = get_request_data()
        customer_id = data.get('customer_id')
        if not customer_id:
            return error_response('customer_id is required', 400)
        return CustomerController.update(customer_id, data)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'route_update_customer Error')
        return error_response(str(e), 500)


@frappe.whitelist(allow_guest=False)
def route_delete_customer():
    """Delete customer (admin only)"""
    try:
        data = get_request_data()
        customer_id = data.get('customer_id')
        if not customer_id:
            return error_response('customer_id is required', 400)
        return CustomerController.delete(customer_id)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'route_delete_customer Error')
        return error_response(str(e), 500)


# ============================================================================
# MOTORCYCLE ROUTES - WHITELISTED
# ============================================================================

@frappe.whitelist(allow_guest=False)
def route_create_motorcycle():
    """Create a new motorcycle"""
    try:
        data = get_request_data()
        return MotorcycleController.create(data)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'route_create_motorcycle Error')
        return error_response(str(e), 500)


@frappe.whitelist(allow_guest=False)
def route_list_motorcycles():
    """Get all motorcycles"""
    try:
        limit = frappe.request.args.get('limit', 100)
        status = frappe.request.args.get('status', None)
        return MotorcycleController.list_all(int(limit), status)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'route_list_motorcycles Error')
        return error_response(str(e), 500)


@frappe.whitelist(allow_guest=False)
def route_get_motorcycle():
    """Get motorcycle by ID"""
    try:
        motorcycle_id = frappe.request.args.get('motorcycle_id')
        if not motorcycle_id:
            return error_response('motorcycle_id is required', 400)
        return MotorcycleController.get_by_id(motorcycle_id)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'route_get_motorcycle Error')
        return error_response(str(e), 500)


@frappe.whitelist(allow_guest=False)
def route_update_motorcycle():
    """Update motorcycle"""
    try:
        data = get_request_data()
        motorcycle_id = data.get('motorcycle_id')
        if not motorcycle_id:
            return error_response('motorcycle_id is required', 400)
        return MotorcycleController.update(motorcycle_id, data)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'route_update_motorcycle Error')
        return error_response(str(e), 500)


@frappe.whitelist(allow_guest=False)
def route_get_available_motorcycles():
    """Get available motorcycles"""
    try:
        return MotorcycleController.get_available()
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'route_get_available_motorcycles Error')
        return error_response(str(e), 500)


# ============================================================================
# CONTROLLER CLASSES
# ============================================================================

class CustomerController:
    """Handle all Customer-related operations"""
    
    @staticmethod
    def create(data):
        """Create a new customer"""
        try:
            # Validate required fields
            if not data.get('full_name'):
                return error_response('full_name is required', 400)
            if not data.get('phone'):
                return error_response('phone is required', 400)
            
            # Check if customer already exists with same phone
            existing = frappe.db.exists('Customer Profile', {'phone': data['phone']})
            if existing:
                return error_response('Customer with this phone already exists', 409)
            
            # Create customer document
            customer = frappe.get_doc({
                'doctype': 'Customer Profile',
                'full_name': data['full_name'],
                'phone': data['phone'],
                'email': data.get('email', ''),
                'user': data.get('user', None),
                'status': data.get('status', 'Active')
            })
            customer.insert(ignore_permissions=True)
            frappe.db.commit()
            
            return success_response(
                data=customer_to_dict(customer),
                message='Customer created successfully',
                status_code=201
            )
        
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), 'Customer Creation Error')
            return error_response(str(e), 500)
    
    @staticmethod
    def get_profile():
        """Get current logged-in customer's profile"""
        try:
            user = frappe.session.user
            if user == 'Guest':
                return error_response('Not authenticated', 401)
            
            # Find customer profile linked to user
            profile_name = frappe.db.get_value(
                'Customer Profile',
                {'user': user},
                'name'
            )
            
            if not profile_name:
                return error_response('No customer profile found', 404)
            
            customer = frappe.get_doc('Customer Profile', profile_name)
            
            return success_response(
                data=customer_to_dict(customer),
                message='Profile retrieved successfully'
            )
        
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), 'Get Profile Error')
            return error_response(str(e), 500)
    
    @staticmethod
    def get_by_id(customer_id):
        """Get customer by ID"""
        try:
            if not frappe.db.exists('Customer Profile', customer_id):
                return error_response('Customer not found', 404)
            
            customer = frappe.get_doc('Customer Profile', customer_id)
            
            return success_response(
                data=customer_to_dict(customer),
                message='Customer retrieved successfully'
            )
        
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), 'Get Customer Error')
            return error_response(str(e), 500)
    
    @staticmethod
    def list_all(limit=50):
        """Get all customers (admin only)"""
        try:
            # Check admin permission
            if not is_admin():
                return error_response('Admin access required', 403)
            
            customers = frappe.get_all(
                'Customer Profile',
                fields=['name', 'full_name', 'phone', 'email', 'status', 'creation'],
                order_by='creation desc',
                limit=limit
            )
            
            # Add contract count for each customer
            for c in customers:
                c['contract_count'] = frappe.db.count('Contract', {'customer': c['name']})
            
            return success_response(
                data=customers,
                message='Customers retrieved successfully'
            )
        
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), 'List Customers Error')
            return error_response(str(e), 500)
    
    @staticmethod
    def update(customer_id, data):
        """Update customer profile"""
        try:
            if not frappe.db.exists('Customer Profile', customer_id):
                return error_response('Customer not found', 404)
            
            customer = frappe.get_doc('Customer Profile', customer_id)
            
            # Update fields
            if data.get('full_name'):
                customer.full_name = data['full_name']
            if data.get('phone'):
                customer.phone = data['phone']
            if data.get('email'):
                customer.email = data['email']
            if data.get('status'):
                customer.status = data['status']
            
            customer.save(ignore_permissions=True)
            frappe.db.commit()
            
            return success_response(
                data=customer_to_dict(customer),
                message='Customer updated successfully'
            )
        
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), 'Update Customer Error')
            return error_response(str(e), 500)
    
    @staticmethod
    def delete(customer_id):
        """Delete customer (admin only)"""
        try:
            if not is_admin():
                return error_response('Admin access required', 403)
            
            if not frappe.db.exists('Customer Profile', customer_id):
                return error_response('Customer not found', 404)
            
            # Check if customer has active contracts
            active_contracts = frappe.db.count(
                'Contract',
                {'customer': customer_id, 'status': 'Active'}
            )
            
            if active_contracts > 0:
                return error_response(
                    'Cannot delete customer with active contracts',
                    409
                )
            
            frappe.delete_doc('Customer Profile', customer_id, force=True)
            frappe.db.commit()
            
            return success_response(
                data={},
                message='Customer deleted successfully'
            )
        
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), 'Delete Customer Error')
            return error_response(str(e), 500)


class MotorcycleController:
    """Handle all Motorcycle-related operations"""
    
    @staticmethod
    def create(data):
        """Create a new motorcycle"""
        try:
            if not is_admin():
                return error_response('Admin access required', 403)
            
            # Validate required fields
            if not data.get('brand'):
                return error_response('brand is required', 400)
            if not data.get('model'):
                return error_response('model is required', 400)
            if not data.get('price'):
                return error_response('price is required', 400)
            
            # Check if plate number already exists
            if data.get('plate_number'):
                existing = frappe.db.exists(
                    'Motorcycle',
                    {'plate_number': data['plate_number']}
                )
                if existing:
                    return error_response('Motorcycle with this plate number already exists', 409)
            
            # Create motorcycle document
            motorcycle = frappe.get_doc({
                'doctype': 'Motorcycle',
                'brand': data['brand'],
                'model': data['model'],
                'year': int(data.get('year', 2024)),
                'plate_number': data.get('plate_number', ''),
                'price': flt(data['price']),
                'status': 'Available'
            })
            motorcycle.insert(ignore_permissions=True)
            frappe.db.commit()
            
            return success_response(
                data=motorcycle_to_dict(motorcycle),
                message='Motorcycle created successfully',
                status_code=201
            )
        
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), 'Motorcycle Creation Error')
            return error_response(str(e), 500)
    
    @staticmethod
    def get_by_id(motorcycle_id):
        """Get motorcycle by ID"""
        try:
            if not frappe.db.exists('Motorcycle', motorcycle_id):
                return error_response('Motorcycle not found', 404)
            
            motorcycle = frappe.get_doc('Motorcycle', motorcycle_id)
            
            return success_response(
                data=motorcycle_to_dict(motorcycle),
                message='Motorcycle retrieved successfully'
            )
        
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), 'Get Motorcycle Error')
            return error_response(str(e), 500)
    
    @staticmethod
    def list_all(limit=100, status=None):
        """Get all motorcycles"""
        try:
            filters = {}
            if status:
                filters['status'] = status
            
            motorcycles = frappe.get_all(
                'Motorcycle',
                filters=filters,
                fields=['name', 'brand', 'model', 'year', 'plate_number', 'price', 'status'],
                order_by='creation desc',
                limit=limit
            )
            
            return success_response(
                data=motorcycles,
                message='Motorcycles retrieved successfully'
            )
        
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), 'List Motorcycles Error')
            return error_response(str(e), 500)
    
    @staticmethod
    def get_available():
        """Get only available motorcycles"""
        try:
            motorcycles = frappe.get_all(
                'Motorcycle',
                filters={'status': 'Available'},
                fields=['name', 'brand', 'model', 'year', 'plate_number', 'price']
            )
            
            return success_response(
                data=motorcycles,
                message='Available motorcycles retrieved successfully'
            )
        
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), 'Get Available Motorcycles Error')
            return error_response(str(e), 500)
    
    @staticmethod
    def update(motorcycle_id, data):
        """Update motorcycle"""
        try:
            if not is_admin():
                return error_response('Admin access required', 403)
            
            if not frappe.db.exists('Motorcycle', motorcycle_id):
                return error_response('Motorcycle not found', 404)
            
            motorcycle = frappe.get_doc('Motorcycle', motorcycle_id)
            
            # Update fields
            if data.get('brand'):
                motorcycle.brand = data['brand']
            if data.get('model'):
                motorcycle.model = data['model']
            if data.get('year'):
                motorcycle.year = int(data['year'])
            if data.get('plate_number'):
                motorcycle.plate_number = data['plate_number']
            if data.get('price'):
                motorcycle.price = flt(data['price'])
            if data.get('status'):
                motorcycle.status = data['status']
            
            motorcycle.save(ignore_permissions=True)
            frappe.db.commit()
            
            return success_response(
                data=motorcycle_to_dict(motorcycle),
                message='Motorcycle updated successfully'
            )
        
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), 'Update Motorcycle Error')
            return error_response(str(e), 500)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_request_data():
    """Extract JSON data from request body"""
    try:
        if frappe.request.method in ['POST', 'PUT']:
            data = frappe.request.get_json()
            return data if data else {}
        return {}
    except:
        return {}


def is_admin():
    """Check if current user is admin"""
    try:
        user = frappe.session.user
        if user == 'Administrator':
            return True
        
        user_doc = frappe.get_doc('User', user)
        return any(role.role in ['Administrator', 'Admin'] for role in user_doc.roles)
    except:
        return False


def customer_to_dict(customer_doc):
    """Convert Customer Profile doc to dictionary"""
    return {
        'name': customer_doc.name,
        'full_name': customer_doc.full_name,
        'phone': customer_doc.phone,
        'email': customer_doc.email,
        'status': customer_doc.status,
        'user': customer_doc.user or None,
        'creation': str(customer_doc.creation),
        'modified': str(customer_doc.modified)
    }


def motorcycle_to_dict(motorcycle_doc):
    """Convert Motorcycle doc to dictionary"""
    return {
        'name': motorcycle_doc.name,
        'brand': motorcycle_doc.brand,
        'model': motorcycle_doc.model,
        'year': motorcycle_doc.year,
        'plate_number': motorcycle_doc.plate_number,
        'price': motorcycle_doc.price,
        'status': motorcycle_doc.status,
        'creation': str(motorcycle_doc.creation),
        'modified': str(motorcycle_doc.modified)
    }


def success_response(data=None, message='Success', status_code=200):
    """Return standardized success response"""
    return {
        'success': True,
        'status': status_code,
        'message': message,
        'data': data or {}
    }


def error_response(message='Error', status_code=500):
    """Return standardized error response"""
    return {
        'success': False,
        'status': status_code,
        'message': message,
        'data': None
    }