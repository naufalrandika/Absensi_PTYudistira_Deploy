"""
Controller untuk presensi
"""
from flask import Blueprint, render_template, request, jsonify, session, flash, redirect, url_for
from models import db
from models.attendance import Attendance
from models.employee import Employee
from utils.decorators import login_required, role_required
from utils.audit_logger import AuditLogger
from utils.geolocation import validate_location
from utils.device_info import get_device_info
from utils.notification_helper import NotificationHelper
from datetime import datetime, date, time
from config import Config

attendance_bp = Blueprint('attendance', __name__)

@attendance_bp.route('/')
@login_required
def index():
    """Halaman presensi"""
    employee_id = session.get('employee_id')
    
    if not employee_id:
        flash('Data karyawan tidak ditemukan', 'error')
        return redirect(url_for('dashboard.index'))
    
    # Get today's attendance
    today = date.today()
    today_attendance = Attendance.query.filter_by(
        employee_id=employee_id,
        attendance_date=today
    ).first()
    
    # Get attendance history
    attendances = Attendance.query.filter_by(
        employee_id=employee_id
    ).order_by(Attendance.attendance_date.desc()).limit(30).all()
    
    role = session.get('role')
    
    # Office location for map - ambil dari database, fallback ke config
    from models.office import Office
    from config import Config
    
    offices = Office.query.filter_by(is_active=True).all()
    if offices:
        # Ambil kantor pertama sebagai default untuk map (bisa dikembangkan untuk multiple marker)
        office_location = {
            'latitude': offices[0].latitude,
            'longitude': offices[0].longitude,
            'radius': offices[0].radius_meters,
            'offices': [{'name': o.name, 'lat': o.latitude, 'lng': o.longitude, 'radius': o.radius_meters} for o in offices]
        }
    else:
        # Fallback ke config
        office_location = {
            'latitude': Config.OFFICE_LATITUDE,
            'longitude': Config.OFFICE_LONGITUDE,
            'radius': Config.GEO_RADIUS_METERS,
            'offices': []
        }
    
    return render_template('attendance/index.html', 
                         today_attendance=today_attendance,
                         attendances=attendances,
                         role=role,
                         office_location=office_location,
                         current_date=date.today())

@attendance_bp.route('/check-in', methods=['POST'])
@login_required
def check_in():
    """Check-in presensi"""
    employee_id = session.get('employee_id')
    user_id = session.get('user_id')
    
    if not employee_id:
        return jsonify({'success': False, 'message': 'Data karyawan tidak ditemukan'}), 400
    
    # Check if already checked in today
    today = date.today()
    existing = Attendance.query.filter_by(
        employee_id=employee_id,
        attendance_date=today
    ).first()
    
    if existing and existing.check_in_time:
        return jsonify({'success': False, 'message': 'Anda sudah melakukan presensi masuk hari ini'}), 400
    
    # Get location from request
    data = request.get_json()
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    
    if not latitude or not longitude:
        return jsonify({'success': False, 'message': 'Lokasi tidak ditemukan'}), 400
    
    # Validate location
    is_valid, distance, office_name = validate_location(latitude, longitude)
    if not is_valid:
        office_info = f" ({office_name})" if office_name else ""
        return jsonify({
            'success': False, 
            'message': f'Anda berada di luar radius kantor{office_info}. Jarak: {distance:.0f}m'
        }), 400
    
    # Get device info
    device_info = get_device_info()
    
    # Create or update attendance
    now = datetime.utcnow()
    check_in_time = now.time()
    
    # Determine status (terlambat or hadir)
    check_in_start = datetime.strptime(Config.CHECK_IN_START, '%H:%M').time()
    status = 'terlambat' if check_in_time > check_in_start else 'hadir'
    
    if existing:
        existing.check_in_time = now
        existing.check_in_latitude = latitude
        existing.check_in_longitude = longitude
        existing.check_in_ip = device_info['ip_address']
        existing.check_in_browser = device_info['browser']
        existing.check_in_os = device_info['os']
        existing.status = status
        attendance = existing
    else:
        attendance = Attendance(
            employee_id=employee_id,
            attendance_date=today,
            check_in_time=now,
            check_in_latitude=latitude,
            check_in_longitude=longitude,
            check_in_ip=device_info['ip_address'],
            check_in_browser=device_info['browser'],
            check_in_os=device_info['os'],
            status=status
        )
        db.session.add(attendance)
    
    db.session.commit()
    
    # Log audit
    AuditLogger.log_presensi(
        user_id, 
        session.get('username'),
        'check_in',
        attendance.id,
        f'Location: {latitude}, {longitude}'
    )
    
    # Create notification
    NotificationHelper.notify_presensi_success(user_id, attendance.id)
    
    return jsonify({
        'success': True,
        'message': 'Presensi masuk berhasil',
        'check_in_time': now.isoformat(),
        'status': status
    })

@attendance_bp.route('/check-out', methods=['POST'])
@login_required
def check_out():
    """Check-out presensi"""
    employee_id = session.get('employee_id')
    user_id = session.get('user_id')
    
    if not employee_id:
        return jsonify({'success': False, 'message': 'Data karyawan tidak ditemukan'}), 400
    
    # Check if checked in today
    today = date.today()
    attendance = Attendance.query.filter_by(
        employee_id=employee_id,
        attendance_date=today
    ).first()
    
    if not attendance or not attendance.check_in_time:
        return jsonify({'success': False, 'message': 'Anda belum melakukan presensi masuk hari ini'}), 400
    
    if attendance.check_out_time:
        return jsonify({'success': False, 'message': 'Anda sudah melakukan presensi pulang hari ini'}), 400
    
    # Get location from request
    data = request.get_json()
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    
    if not latitude or not longitude:
        return jsonify({'success': False, 'message': 'Lokasi tidak ditemukan'}), 400
    
    # Validate location
    is_valid, distance, office_name = validate_location(latitude, longitude)
    if not is_valid:
        office_info = f" ({office_name})" if office_name else ""
        return jsonify({
            'success': False, 
            'message': f'Anda berada di luar radius kantor{office_info}. Jarak: {distance:.0f}m'
        }), 400
    
    # Get device info
    device_info = get_device_info()
    
    # Update attendance
    now = datetime.utcnow()
    check_out_time = now.time()
    
    # Check if pulang cepat
    check_out_start = datetime.strptime(Config.CHECK_OUT_START, '%H:%M').time()
    if attendance.status == 'hadir' and check_out_time < check_out_start:
        attendance.status = 'pulang_cepat'
    
    attendance.check_out_time = now
    attendance.check_out_latitude = latitude
    attendance.check_out_longitude = longitude
    attendance.check_out_ip = device_info['ip_address']
    attendance.check_out_browser = device_info['browser']
    attendance.check_out_os = device_info['os']
    
    db.session.commit()
    
    # Log audit
    AuditLogger.log_presensi(
        user_id,
        session.get('username'),
        'check_out',
        attendance.id,
        f'Location: {latitude}, {longitude}'
    )
    
    return jsonify({
        'success': True,
        'message': 'Presensi pulang berhasil',
        'check_out_time': now.isoformat()
    })

@attendance_bp.route('/manual-request', methods=['POST'])
@login_required
def manual_request():
    """Ajukan cuti manual"""
    employee_id = session.get('employee_id')
    user_id = session.get('user_id')
    
    if not employee_id:
        return jsonify({'success': False, 'message': 'Data karyawan tidak ditemukan'}), 400
    
    # Get data from request
    data = request.get_json()
    attendance_date_str = data.get('attendance_date')
    notes = data.get('notes', '').strip()
    status = data.get('status', 'alpha')  # Default to alpha if not provided
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    
    # Validate required fields
    if not attendance_date_str:
        return jsonify({'success': False, 'message': 'Tanggal tidak boleh kosong'}), 400
    
    if not notes:
        return jsonify({'success': False, 'message': 'Alasan tidak boleh kosong'}), 400
    
    if not latitude or not longitude:
        return jsonify({'success': False, 'message': 'Lokasi tidak ditemukan. Pastikan izin lokasi diaktifkan'}), 400
    
    # Validate status
    allowed_statuses = ['alpha', 'wfa', 'hadir', 'terlambat', 'pulang_cepat']
    if status not in allowed_statuses:
        return jsonify({'success': False, 'message': 'Status tidak valid'}), 400
    
    try:
        attendance_date = datetime.strptime(attendance_date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'message': 'Format tanggal tidak valid'}), 400
    
    # Validate date (cannot be in the future)
    today = date.today()
    if attendance_date > today:
        return jsonify({'success': False, 'message': 'Tidak bisa mengajukan untuk tanggal di masa depan'}), 400
    
    # Check if attendance already exists for this date
    existing = Attendance.query.filter_by(
        employee_id=employee_id,
        attendance_date=attendance_date
    ).first()
    
    if existing and existing.check_in_time:
        return jsonify({'success': False, 'message': 'Anda sudah melakukan presensi pada tanggal tersebut'}), 400
    
    # Get device info
    device_info = get_device_info()
    
    # Create or update attendance record
    now = datetime.utcnow()
    
    # Set default check-in and check-out time for manual request
    # Check-in: 08:00, Check-out: 17:00 pada tanggal yang dipilih
    check_in_default = datetime.combine(attendance_date, datetime.strptime(Config.CHECK_IN_START, '%H:%M').time())
    check_out_default = datetime.combine(attendance_date, datetime.strptime(Config.CHECK_OUT_START, '%H:%M').time())
    
    if existing:
        # Update existing record
        existing.notes = notes
        existing.check_in_time = check_in_default
        existing.check_out_time = check_out_default
        existing.check_in_latitude = latitude
        existing.check_in_longitude = longitude
        existing.check_out_latitude = latitude  # Use same location for both
        existing.check_out_longitude = longitude
        existing.check_in_ip = device_info['ip_address']
        existing.check_in_browser = device_info['browser']
        existing.check_in_os = device_info['os']
        existing.check_out_ip = device_info['ip_address']
        existing.check_out_browser = device_info['browser']
        existing.check_out_os = device_info['os']
        existing.status = status  # Use status from request
        attendance = existing
    else:
        # Create new attendance record
        attendance = Attendance(
            employee_id=employee_id,
            attendance_date=attendance_date,
            check_in_time=check_in_default,  # Set default check-in time
            check_out_time=check_out_default,  # Set default check-out time
            check_in_latitude=latitude,
            check_in_longitude=longitude,
            check_out_latitude=latitude,  # Use same location for both
            check_out_longitude=longitude,
            check_in_ip=device_info['ip_address'],
            check_in_browser=device_info['browser'],
            check_in_os=device_info['os'],
            check_out_ip=device_info['ip_address'],
            check_out_browser=device_info['browser'],
            check_out_os=device_info['os'],
            status=status,  # Use status from request
            notes=notes
        )
        db.session.add(attendance)
    
    db.session.commit()
    
    # Log audit
    AuditLogger.log_presensi(
        user_id,
        session.get('username'),
        'manual_request',
        attendance.id,
        f'Manual request for date: {attendance_date}, Location: {latitude}, {longitude}, Notes: {notes[:50]}'
    )
    
    return jsonify({
        'success': True,
        'message': 'Pengajuan cuti manual berhasil diajukan',
        'attendance_id': attendance.id,
        'attendance_date': attendance_date.isoformat()
    })

@attendance_bp.route('/history')
@login_required
def history():
    """Riwayat presensi"""
    employee_id = session.get('employee_id')
    role = session.get('role')
    
    # Get filter parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = Attendance.query
    
    # Filter by employee (if not admin/hrd)
    if role == 'karyawan':
        query = query.filter_by(employee_id=employee_id)
    elif role == 'atasan':
        # Show subordinates only
        employee = Employee.query.get(employee_id)
        if employee:
            subordinate_ids = [e.id for e in employee.subordinates]
            query = query.filter(Attendance.employee_id.in_(subordinate_ids))
    
    # Date filter
    if start_date:
        query = query.filter(Attendance.attendance_date >= datetime.strptime(start_date, '%Y-%m-%d').date())
    if end_date:
        query = query.filter(Attendance.attendance_date <= datetime.strptime(end_date, '%Y-%m-%d').date())
    
    attendances = query.order_by(Attendance.attendance_date.desc()).all()
    
    return render_template('attendance/history.html', attendances=attendances, role=role)
