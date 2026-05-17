"""
Controller untuk manajemen lokasi kantor (Admin only)
"""
from flask import Blueprint, render_template, request, jsonify, session, flash, redirect, url_for
from models import db
from models.office import Office
from utils.decorators import login_required, admin_required
from utils.audit_logger import AuditLogger

office_bp = Blueprint('office', __name__)

@office_bp.route('/')
@login_required
@admin_required
def index():
    """Daftar lokasi kantor"""
    offices = Office.query.order_by(Office.name).all()
    return render_template('office/index.html', offices=offices)

@office_bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create():
    """Tambah lokasi kantor baru"""
    if request.method == 'POST':
        name = request.form.get('name')
        address = request.form.get('address')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        radius_meters = request.form.get('radius_meters')
        description = request.form.get('description')
        is_active = request.form.get('is_active') == 'on'
        
        # Validate
        if not name or not latitude or not longitude or not radius_meters:
            flash('Nama, koordinat, dan radius harus diisi', 'error')
            return render_template('office/create.html')
        
        try:
            latitude = float(latitude)
            longitude = float(longitude)
            radius_meters = int(radius_meters)
        except ValueError:
            flash('Koordinat dan radius harus berupa angka', 'error')
            return render_template('office/create.html')
        
        # Validate coordinates
        if not (-90 <= latitude <= 90):
            flash('Latitude harus antara -90 dan 90', 'error')
            return render_template('office/create.html')
        
        if not (-180 <= longitude <= 180):
            flash('Longitude harus antara -180 dan 180', 'error')
            return render_template('office/create.html')
        
        if radius_meters <= 0:
            flash('Radius harus lebih besar dari 0', 'error')
            return render_template('office/create.html')
        
        # Create office
        try:
            office = Office(
                name=name,
                address=address,
                latitude=latitude,
                longitude=longitude,
                radius_meters=radius_meters,
                description=description,
                is_active=is_active
            )
            
            db.session.add(office)
            db.session.commit()
            
            # Log audit
            user_id = session.get('user_id')
            username = session.get('username')
            AuditLogger.log_data_change(
                user_id=user_id,
                username=username,
                action='create',
                table_name='offices',
                record_id=office.id,
                details=f'Membuat lokasi kantor: {name}'
            )
            
            flash(f'Lokasi kantor "{name}" berhasil ditambahkan', 'success')
            return redirect(url_for('office.index'))
        except Exception as e:
            db.session.rollback()
            import traceback
            error_msg = str(e)
            # Print error untuk debugging
            print(f"Error saat membuat office: {error_msg}")
            traceback.print_exc()
            
            # Jika error terkait tabel tidak ada, beri pesan yang lebih jelas
            if 'offices' in error_msg.lower() or 'table' in error_msg.lower() or 'does not exist' in error_msg.lower():
                flash('Tabel offices belum dibuat. Silakan restart aplikasi untuk membuat tabel.', 'error')
            elif 'duplicate' in error_msg.lower() or 'unique' in error_msg.lower():
                flash('Nama kantor sudah digunakan. Gunakan nama yang berbeda.', 'error')
            else:
                flash(f'Kesalahan saat menyimpan data: {error_msg}. Silakan cek log untuk detail.', 'error')
            return render_template('office/create.html')
    
    return render_template('office/create.html')

@office_bp.route('/<int:office_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit(office_id):
    """Edit lokasi kantor"""
    office = Office.query.get_or_404(office_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        address = request.form.get('address')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        radius_meters = request.form.get('radius_meters')
        description = request.form.get('description')
        is_active = request.form.get('is_active') == 'on'
        
        # Validate
        if not name or not latitude or not longitude or not radius_meters:
            flash('Nama, koordinat, dan radius harus diisi', 'error')
            return render_template('office/edit.html', office=office)
        
        try:
            latitude = float(latitude)
            longitude = float(longitude)
            radius_meters = int(radius_meters)
        except ValueError:
            flash('Koordinat dan radius harus berupa angka', 'error')
            return render_template('office/edit.html', office=office)
        
        # Validate coordinates
        if not (-90 <= latitude <= 90):
            flash('Latitude harus antara -90 dan 90', 'error')
            return render_template('office/edit.html', office=office)
        
        if not (-180 <= longitude <= 180):
            flash('Longitude harus antara -180 dan 180', 'error')
            return render_template('office/edit.html', office=office)
        
        if radius_meters <= 0:
            flash('Radius harus lebih besar dari 0', 'error')
            return render_template('office/edit.html', office=office)
        
        # Update office
        office.name = name
        office.address = address
        office.latitude = latitude
        office.longitude = longitude
        office.radius_meters = radius_meters
        office.description = description
        office.is_active = is_active
        
        db.session.commit()
        
        # Log audit
        user_id = session.get('user_id')
        username = session.get('username')
        AuditLogger.log_data_change(
            user_id=user_id,
            username=username,
            action='update',
            table_name='offices',
            record_id=office.id,
            details=f'Memperbarui lokasi kantor: {name}'
        )
        
        flash(f'Lokasi kantor "{name}" berhasil diperbarui', 'success')
        return redirect(url_for('office.index'))
    
    return render_template('office/edit.html', office=office)

@office_bp.route('/<int:office_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete(office_id):
    """Hapus lokasi kantor (soft delete - set is_active=False)"""
    office = Office.query.get_or_404(office_id)
    
    # Soft delete - set is_active to False
    office.is_active = False
    db.session.commit()
    
    # Log audit
    user_id = session.get('user_id')
    username = session.get('username')
    AuditLogger.log_data_change(
        user_id=user_id,
        username=username,
        action='delete',
        table_name='offices',
        record_id=office.id,
        details=f'Menonaktifkan lokasi kantor: {office.name}'
    )
    
    flash(f'Lokasi kantor "{office.name}" berhasil dinonaktifkan', 'success')
    return redirect(url_for('office.index'))

@office_bp.route('/<int:office_id>/activate', methods=['POST'])
@login_required
@admin_required
def activate(office_id):
    """Aktifkan kembali lokasi kantor"""
    office = Office.query.get_or_404(office_id)
    
    office.is_active = True
    db.session.commit()
    
    # Log audit
    user_id = session.get('user_id')
    username = session.get('username')
    AuditLogger.log_data_change(
        user_id=user_id,
        username=username,
        action='activate',
        table_name='offices',
        record_id=office.id,
        details=f'Mengaktifkan lokasi kantor: {office.name}'
    )
    
    flash(f'Lokasi kantor "{office.name}" berhasil diaktifkan', 'success')
    return redirect(url_for('office.index'))
