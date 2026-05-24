"""
Aplikasi utama Sistem Presensi Karyawan
"""
import os
from dotenv import load_dotenv

# Load environment variables dari .env file
load_dotenv()

from flask import Flask
from config import Config
from models import db
# Import semua models untuk memastikan tabel dibuat
from models.office import Office
from controllers.auth_controller import auth_bp
from controllers.attendance_controller import attendance_bp
from controllers.employee_controller import employee_bp
from controllers.leave_controller import leave_bp
from controllers.overtime_controller import overtime_bp
from controllers.dashboard_controller import dashboard_bp
from controllers.notification_controller import notification_bp
from controllers.audit_controller import audit_bp
from controllers.office_controller import office_bp
from controllers.time_worksheet_controller import time_worksheet_bp
from controllers.work_calendar_controller import work_calendar_bp

def create_app():
    """Factory function untuk membuat Flask app"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize database
    db.init_app(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(attendance_bp, url_prefix='/attendance')
    app.register_blueprint(employee_bp, url_prefix='/employee')
    app.register_blueprint(leave_bp, url_prefix='/leave')
    app.register_blueprint(overtime_bp, url_prefix='/overtime')
    app.register_blueprint(dashboard_bp, url_prefix='/')
    app.register_blueprint(notification_bp, url_prefix='/notification')
    app.register_blueprint(audit_bp, url_prefix='/audit')
    app.register_blueprint(office_bp, url_prefix='/office')
    app.register_blueprint(time_worksheet_bp, url_prefix='/time-worksheet')
    app.register_blueprint(work_calendar_bp, url_prefix='/work-calendar')
    
    # =========================
    # DB INIT (SAFE FOR VERCEL)
    # =========================
    if os.getenv("VERCEL") is None:
        # hanya jalan di local
        with app.app_context():
            db.create_all()

    return app


# =========================
# WAJIB UNTUK VERCEL
# =========================
app = create_app()


# =========================
# LOCAL DEVELOPMENT ONLY
# =========================
if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
