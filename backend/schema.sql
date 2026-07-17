-- 生活缴费系统 MySQL 数据库脚本
-- 用法: mysql -u root < schema.sql

CREATE DATABASE IF NOT EXISTS life_system DEFAULT CHARSET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE life_system;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    real_name VARCHAR(50),
    phone VARCHAR(20),
    role ENUM('user','admin') DEFAULT 'user',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS households (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    household_no VARCHAR(32) NOT NULL UNIQUE,
    address VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS meters (
    id INT AUTO_INCREMENT PRIMARY KEY,
    household_id INT NOT NULL,
    type ENUM('electricity','water','gas') NOT NULL,
    meter_no VARCHAR(32) NOT NULL,
    current_reading DECIMAL(12,2) DEFAULT 0,
    FOREIGN KEY (household_id) REFERENCES households(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS bill_type_rules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    type ENUM('electricity','water','gas') NOT NULL,
    tier INT NOT NULL,
    min_usage DECIMAL(12,2) NOT NULL,
    max_usage DECIMAL(12,2),
    unit_price DECIMAL(10,4) NOT NULL,
    description VARCHAR(255)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS bills (
    id INT AUTO_INCREMENT PRIMARY KEY,
    household_id INT NOT NULL,
    meter_id INT NOT NULL,
    type ENUM('electricity','water','gas') NOT NULL,
    period VARCHAR(7) NOT NULL,
    previous_reading DECIMAL(12,2) NOT NULL,
    current_reading DECIMAL(12,2) NOT NULL,
    usage_amount DECIMAL(12,2) NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    status ENUM('unpaid','paid') DEFAULT 'unpaid',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    paid_at DATETIME NULL,
    FOREIGN KEY (household_id) REFERENCES households(id),
    FOREIGN KEY (meter_id) REFERENCES meters(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bill_id INT NOT NULL UNIQUE,
    amount DECIMAL(12,2) NOT NULL,
    method VARCHAR(20) DEFAULT 'alipay',
    transaction_no VARCHAR(64) NOT NULL,
    paid_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bill_id) REFERENCES bills(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS repair_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    type ENUM('electricity','water','gas','other') NOT NULL,
    description TEXT NOT NULL,
    phone VARCHAR(20) NOT NULL,
    urgency ENUM('normal','urgent') DEFAULT 'normal',
    status ENUM('pending','processing','resolved') DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    resolved_at DATETIME NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
