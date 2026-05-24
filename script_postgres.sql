-- Skema PostgreSQL untuk Sistem Presensi (Neon)
-- Tabel juga dibuat otomatis oleh Flask-SQLAlchemy (python init_db.py)

CREATE TABLE IF NOT EXISTS employees (
    id SERIAL PRIMARY KEY,
    nik VARCHAR(20) NOT NULL UNIQUE,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    position VARCHAR(50) NOT NULL,
    division VARCHAR(50) NOT NULL,
    supervisor_id INTEGER REFERENCES employees(id),
    status VARCHAR(20) DEFAULT 'aktif',
    hire_date DATE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL,
    employee_id INTEGER REFERENCES employees(id),
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP,
    last_login_ip VARCHAR(45),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS offices (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    address VARCHAR(255),
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    radius_meters INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    description TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS attendances (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees(id),
    attendance_date DATE NOT NULL,
    check_in_time TIMESTAMP,
    check_out_time TIMESTAMP,
    check_in_latitude DOUBLE PRECISION,
    check_in_longitude DOUBLE PRECISION,
    check_out_latitude DOUBLE PRECISION,
    check_out_longitude DOUBLE PRECISION,
    check_in_ip VARCHAR(45),
    check_out_ip VARCHAR(45),
    check_in_browser VARCHAR(100),
    check_out_browser VARCHAR(100),
    check_in_os VARCHAR(50),
    check_out_os VARCHAR(50),
    status VARCHAR(20),
    notes TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    username VARCHAR(50),
    activity VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL,
    table_name VARCHAR(50),
    record_id INTEGER,
    ip_address VARCHAR(45),
    user_agent VARCHAR(255),
    details TEXT,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS leave_requests (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees(id),
    leave_type VARCHAR(20) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    reason TEXT NOT NULL,
    attachment_path VARCHAR(255),
    status VARCHAR(20),
    supervisor_approval BOOLEAN,
    supervisor_approval_date TIMESTAMP,
    supervisor_id INTEGER REFERENCES employees(id),
    hrd_approval BOOLEAN,
    hrd_approval_date TIMESTAMP,
    hrd_id INTEGER REFERENCES users(id),
    rejection_reason TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    notification_type VARCHAR(50) NOT NULL,
    is_read BOOLEAN,
    related_id INTEGER,
    created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS overtimes (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees(id),
    overtime_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    total_hours DOUBLE PRECISION NOT NULL,
    reason TEXT NOT NULL,
    status VARCHAR(20),
    supervisor_approval BOOLEAN,
    supervisor_approval_date TIMESTAMP,
    supervisor_id INTEGER REFERENCES employees(id),
    hrd_approval BOOLEAN,
    hrd_approval_date TIMESTAMP,
    hrd_id INTEGER REFERENCES users(id),
    rejection_reason TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS time_worksheets (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees(id),
    activity_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    duration_minutes INTEGER NOT NULL,
    activity_title VARCHAR(150) NOT NULL,
    activity_description TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_time_worksheets_activity_date ON time_worksheets (activity_date);

CREATE TABLE IF NOT EXISTS work_calendar_events (
    id SERIAL PRIMARY KEY,
    event_date DATE NOT NULL,
    title VARCHAR(150) NOT NULL,
    description TEXT,
    event_type VARCHAR(20) NOT NULL,
    created_by_user_id INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_work_calendar_events_event_date ON work_calendar_events (event_date);
