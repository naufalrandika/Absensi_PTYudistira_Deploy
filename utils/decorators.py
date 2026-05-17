"""
Decorators untuk autentikasi dan autorisasi
"""
from functools import wraps
from flask import session, redirect, url_for, flash, jsonify

def login_required(f):
    """Decorator untuk memastikan user sudah login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Silakan masuk terlebih dahulu', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    """Decorator untuk memastikan user memiliki role yang diizinkan"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Silakan masuk terlebih dahulu', 'warning')
                return redirect(url_for('auth.login'))
            
            user_role = session.get('role')
            if user_role not in roles:
                flash('Anda tidak memiliki akses untuk halaman ini', 'error')
                return redirect(url_for('dashboard.index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """Decorator untuk memastikan user adalah admin"""
    return role_required('admin')(f)

def hrd_required(f):
    """Decorator untuk memastikan user adalah HRD atau admin"""
    return role_required('admin', 'hrd')(f)

def supervisor_required(f):
    """Decorator untuk memastikan user adalah atasan atau admin"""
    return role_required('admin', 'hrd', 'atasan')(f)
