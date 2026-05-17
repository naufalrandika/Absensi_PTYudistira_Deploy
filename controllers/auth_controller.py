"""
Controller untuk autentikasi
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models import db
from models.user import User
from models.employee import Employee
from utils.decorators import login_required
from utils.audit_logger import AuditLogger
from utils.device_info import get_device_info
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Halaman login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Nama pengguna dan kata sandi harus diisi', 'error')
            return render_template('auth/login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Akun Anda tidak aktif', 'error')
                AuditLogger.log_login(None, username, success=False)
                return render_template('auth/login.html')
            
            # Update last login
            device_info = get_device_info()
            user.last_login = datetime.utcnow()
            user.last_login_ip = device_info['ip_address']
            db.session.commit()
            
            # Set session
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            session['employee_id'] = user.employee_id
            session.permanent = True
            
            # Log audit
            AuditLogger.log_login(user.id, user.username, success=True)
            
            flash('Berhasil masuk', 'success')
            return redirect(url_for('dashboard.index'))
        else:
            flash('Nama pengguna atau kata sandi salah', 'error')
            AuditLogger.log_login(None, username, success=False)
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Logout user"""
    user_id = session.get('user_id')
    username = session.get('username')
    
    # Log audit
    AuditLogger.log_logout(user_id, username)
    
    # Clear session
    session.clear()
    flash('Anda telah keluar', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """Reset password (placeholder)"""
    if request.method == 'POST':
        email = request.form.get('email')
        # TODO: Implement reset password logic
        flash('Fitur atur ulang kata sandi belum tersedia', 'info')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html')
