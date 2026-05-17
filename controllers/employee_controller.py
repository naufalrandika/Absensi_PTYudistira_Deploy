"""
Controller untuk manajemen data karyawan
"""
from flask import Blueprint, render_template, request, jsonify, session, flash, redirect, url_for, send_file
from models import db
from models.employee import Employee
from models.user import User
from utils.decorators import login_required, hrd_required
from utils.audit_logger import AuditLogger
from werkzeug.utils import secure_filename
import csv
import io
from datetime import datetime

employee_bp = Blueprint('employee', __name__)

@employee_bp.route('/')
@login_required
@hrd_required
def index():
    """Daftar karyawan"""
    employees = Employee.query.order_by(Employee.full_name).all()
    return render_template('employee/index.html', employees=employees)

@employee_bp.route('/create', methods=['GET', 'POST'])
@login_required
@hrd_required
def create():
    """Tambah karyawan baru"""
    if request.method == 'POST':
        nik = request.form.get('nik')
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        position = request.form.get('position')
        division = request.form.get('division')
        supervisor_id = request.form.get('supervisor_id') or None
        hire_date = request.form.get('hire_date') or None
        
        # Validate
        if Employee.query.filter_by(nik=nik).first():
            flash('NIK sudah terdaftar', 'error')
            return render_template('employee/create.html')
        
        if Employee.query.filter_by(email=email).first():
            flash('Email sudah terdaftar', 'error')
            return render_template('employee/create.html')
        
        # Create employee
        employee = Employee(
            nik=nik,
            full_name=full_name,
            email=email,
            phone=phone,
            position=position,
            division=division,
            supervisor_id=int(supervisor_id) if supervisor_id else None,
            hire_date=datetime.strptime(hire_date, '%Y-%m-%d').date() if hire_date else None
        )
        
        db.session.add(employee)
        db.session.flush()  # Get employee.id without committing
        
        # Create user account if requested
        create_user = request.form.get('create_user') == '1'
        if create_user:
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
            user_role = request.form.get('user_role', 'karyawan')
            
            # Auto-generate username from NIK if not provided
            if not username:
                username = nik.lower()
            
            # Auto-generate password from NIK if not provided
            if not password:
                password = nik  # Default password is NIK
            
            # Validate username uniqueness
            if User.query.filter_by(username=username).first():
                db.session.rollback()
                flash(f'Nama pengguna "{username}" sudah terdaftar. Silakan gunakan nama pengguna lain.', 'error')
                supervisors = Employee.query.filter_by(status='aktif').all()
                return render_template('employee/create.html', supervisors=supervisors)
            
            # Validate email uniqueness for user
            if User.query.filter_by(email=email).first():
                db.session.rollback()
                flash(f'Email "{email}" sudah terdaftar sebagai pengguna. Silakan gunakan email lain.', 'error')
                supervisors = Employee.query.filter_by(status='aktif').all()
                return render_template('employee/create.html', supervisors=supervisors)
            
            # Create user
            user = User(
                username=username,
                email=email,
                role=user_role,
                employee_id=employee.id,
                is_active=True
            )
            user.set_password(password)
            db.session.add(user)
            
            # Log audit for user creation
            AuditLogger.log_data_change(
                session.get('user_id'),
                session.get('username'),
                'create',
                'users',
                user.id,
                f'Created user account for employee: {full_name} (username: {username})'
            )
        
        db.session.commit()
        
        # Log audit for employee creation
        AuditLogger.log_data_change(
            session.get('user_id'),
            session.get('username'),
            'create',
            'employees',
            employee.id,
            f'Created employee: {full_name}'
        )
        
        if create_user:
            flash(f'Karyawan dan akun pengguna berhasil ditambahkan. Nama pengguna: {username}, Kata sandi: {password}', 'success')
        else:
            flash('Karyawan berhasil ditambahkan', 'success')
        
        return redirect(url_for('employee.index'))
    
    # Get supervisors for dropdown
    supervisors = Employee.query.filter_by(status='aktif').all()
    return render_template('employee/create.html', supervisors=supervisors)

@employee_bp.route('/<int:employee_id>/edit', methods=['GET', 'POST'])
@login_required
@hrd_required
def edit(employee_id):
    """Edit data karyawan"""
    employee = Employee.query.get_or_404(employee_id)
    
    if request.method == 'POST':
        employee.nik = request.form.get('nik')
        employee.full_name = request.form.get('full_name')
        employee.email = request.form.get('email')
        employee.phone = request.form.get('phone')
        employee.position = request.form.get('position')
        employee.division = request.form.get('division')
        employee.supervisor_id = int(request.form.get('supervisor_id')) if request.form.get('supervisor_id') else None
        employee.status = request.form.get('status')
        
        if request.form.get('hire_date'):
            employee.hire_date = datetime.strptime(request.form.get('hire_date'), '%Y-%m-%d').date()
        
        # Handle user account update or creation
        existing_user = User.query.filter_by(employee_id=employee.id).first()
        create_user = request.form.get('create_user') == '1'
        
        if existing_user:
            # Update existing user
            new_username = request.form.get('username', '').strip()
            new_user_email = request.form.get('user_email', '').strip()
            new_user_role = request.form.get('user_role', 'karyawan')
            user_is_active = request.form.get('user_is_active') == '1'
            
            # Update username if changed
            if new_username and new_username != existing_user.username:
                # Check if new username is available
                if User.query.filter(User.username == new_username, User.id != existing_user.id).first():
                    flash(f'Nama pengguna "{new_username}" sudah terdaftar. Silakan gunakan nama pengguna lain.', 'error')
                    supervisors = Employee.query.filter_by(status='aktif').all()
                    return render_template('employee/edit.html', employee=employee, supervisors=supervisors)
                existing_user.username = new_username
            
            # Update email if changed
            if new_user_email and new_user_email != existing_user.email:
                # Check if new email is available
                if User.query.filter(User.email == new_user_email, User.id != existing_user.id).first():
                    flash(f'Email "{new_user_email}" sudah terdaftar sebagai pengguna lain. Silakan gunakan email lain.', 'error')
                    supervisors = Employee.query.filter_by(status='aktif').all()
                    return render_template('employee/edit.html', employee=employee, supervisors=supervisors)
                existing_user.email = new_user_email
            
            # Update role
            if new_user_role != existing_user.role:
                existing_user.role = new_user_role
            
            # Update is_active
            existing_user.is_active = user_is_active
            
            # Log audit for user update
            AuditLogger.log_data_change(
                session.get('user_id'),
                session.get('username'),
                'update',
                'users',
                existing_user.id,
                f'Updated user account for employee: {employee.full_name}'
            )
            
        elif create_user:
            # Create new user account
            username = request.form.get('username', '').strip()
            user_email = request.form.get('user_email', '').strip() or employee.email
            password = request.form.get('password', '').strip()
            user_role = request.form.get('user_role', 'karyawan')
            
            # Auto-generate username from NIK if not provided
            if not username:
                username = employee.nik.lower()
            
            # Auto-generate password from NIK if not provided
            if not password:
                password = employee.nik
            
            # Validate username uniqueness
            if User.query.filter_by(username=username).first():
                flash(f'Nama pengguna "{username}" sudah terdaftar. Silakan gunakan nama pengguna lain.', 'error')
                supervisors = Employee.query.filter_by(status='aktif').all()
                return render_template('employee/edit.html', employee=employee, supervisors=supervisors)
            
            # Validate email uniqueness for user
            if User.query.filter_by(email=user_email).first():
                flash(f'Email "{user_email}" sudah terdaftar sebagai pengguna. Silakan gunakan email lain.', 'error')
                supervisors = Employee.query.filter_by(status='aktif').all()
                return render_template('employee/edit.html', employee=employee, supervisors=supervisors)
            
            # Create user
            user = User(
                username=username,
                email=user_email,
                role=user_role,
                employee_id=employee.id,
                is_active=True
            )
            user.set_password(password)
            db.session.add(user)
            
            # Log audit for user creation
            AuditLogger.log_data_change(
                session.get('user_id'),
                session.get('username'),
                'create',
                'users',
                user.id,
                f'Created user account for employee: {employee.full_name} (username: {username})'
            )
        
        db.session.commit()
        
        # Log audit for employee update
        AuditLogger.log_data_change(
            session.get('user_id'),
            session.get('username'),
            'update',
            'employees',
            employee.id,
            f'Updated employee: {employee.full_name}'
        )
        
        flash('Data karyawan berhasil diperbarui', 'success')
        return redirect(url_for('employee.index'))
    
    supervisors = Employee.query.filter_by(status='aktif').all()
    return render_template('employee/edit.html', employee=employee, supervisors=supervisors)

@employee_bp.route('/<int:employee_id>/delete', methods=['POST'])
@login_required
@hrd_required
def delete(employee_id):
    """Hapus karyawan"""
    employee = Employee.query.get_or_404(employee_id)
    
    # Soft delete (ubah status)
    employee.status = 'nonaktif'
    db.session.commit()
    
    # Log audit
    AuditLogger.log_data_change(
        session.get('user_id'),
        session.get('username'),
        'delete',
        'employees',
        employee.id,
        f'Deleted employee: {employee.full_name}'
    )
    
    flash('Karyawan berhasil dinonaktifkan', 'success')
    return redirect(url_for('employee.index'))

@employee_bp.route('/import', methods=['GET', 'POST'])
@login_required
@hrd_required
def import_data():
    """Import data karyawan dari CSV/Excel"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('File tidak ditemukan', 'error')
            return redirect(url_for('employee.import_data'))
        
        file = request.files['file']
        if file.filename == '':
            flash('File tidak dipilih', 'error')
            return redirect(url_for('employee.import_data'))
        
        # Read CSV
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_input = csv.DictReader(stream)
        
        imported = 0
        errors = []
        
        for row in csv_input:
            try:
                # Check if exists
                if Employee.query.filter_by(nik=row['nik']).first():
                    errors.append(f"NIK {row['nik']} sudah terdaftar")
                    continue
                
                employee = Employee(
                    nik=row['nik'],
                    full_name=row['full_name'],
                    email=row['email'],
                    phone=row.get('phone'),
                    position=row['position'],
                    division=row['division'],
                    status=row.get('status', 'aktif')
                )
                db.session.add(employee)
                imported += 1
            except Exception as e:
                errors.append(f"Error importing {row.get('nik', 'unknown')}: {str(e)}")
        
        db.session.commit()
        
        flash(f'Berhasil mengimport {imported} data karyawan', 'success')
        if errors:
            flash(f'Terjadi {len(errors)} kesalahan: {", ".join(errors[:5])}', 'warning')
        
        return redirect(url_for('employee.index'))
    
    return render_template('employee/import.html')

@employee_bp.route('/export')
@login_required
@hrd_required
def export_data():
    """Export data karyawan ke CSV"""
    employees = Employee.query.all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['NIK', 'Nama Lengkap', 'Email', 'Phone', 'Jabatan', 'Divisi', 'Status'])
    
    # Data
    for emp in employees:
        writer.writerow([
            emp.nik,
            emp.full_name,
            emp.email,
            emp.phone or '',
            emp.position,
            emp.division,
            emp.status
        ])
    
    output.seek(0)
    
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'employees_{datetime.now().strftime("%Y%m%d")}.csv'
    )
