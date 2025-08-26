# -*- coding: utf-8 -*-
"""
نظام قاعدة البيانات لبوت تيليجرام الذكي
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import config

class DatabaseManager:
    """مدير قاعدة البيانات الرئيسي"""
    
    def __init__(self, db_path: str = config.DATABASE_PATH):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """تهيئة قاعدة البيانات وإنشاء الجداول"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # جدول المستخدمين
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT,
                        first_name TEXT,
                        last_name TEXT,
                        language_code TEXT DEFAULT 'ar',
                        is_admin BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        settings TEXT DEFAULT '{}'
                    )
                ''')
                
                # جدول الملفات
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS files (
                        file_id TEXT PRIMARY KEY,
                        user_id INTEGER,
                        file_name TEXT,
                        file_type TEXT,
                        file_size INTEGER,
                        file_path TEXT,
                        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        processed BOOLEAN DEFAULT FALSE,
                        analysis_result TEXT,
                        metadata TEXT DEFAULT '{}',
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                ''')
                
                # جدول الوكلاء
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS agents (
                        agent_id TEXT PRIMARY KEY,
                        agent_type TEXT,
                        agent_name TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        capabilities TEXT DEFAULT '[]',
                        settings TEXT DEFAULT '{}'
                    )
                ''')
                
                # جدول المهام
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tasks (
                        task_id TEXT PRIMARY KEY,
                        user_id INTEGER,
                        agent_id TEXT,
                        task_type TEXT,
                        task_data TEXT,
                        status TEXT DEFAULT 'pending',
                        priority INTEGER DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        scheduled_for TIMESTAMP,
                        completed_at TIMESTAMP,
                        result TEXT,
                        FOREIGN KEY (user_id) REFERENCES users (user_id),
                        FOREIGN KEY (agent_id) REFERENCES agents (agent_id)
                    )
                ''')
                
                # جدول البحث
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS searches (
                        search_id TEXT PRIMARY KEY,
                        user_id INTEGER,
                        query TEXT,
                        results TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        search_type TEXT DEFAULT 'web',
                        metadata TEXT DEFAULT '{}'
                    )
                ''')
                
                # جدول الجدولة
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS schedules (
                        schedule_id TEXT PRIMARY KEY,
                        user_id INTEGER,
                        task_type TEXT,
                        schedule_data TEXT,
                        cron_expression TEXT,
                        next_run TIMESTAMP,
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                ''')
                
                # جدول الإشعارات
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS notifications (
                        notification_id TEXT PRIMARY KEY,
                        user_id INTEGER,
                        title TEXT,
                        message TEXT,
                        notification_type TEXT,
                        is_read BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        scheduled_for TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                ''')
                
                # إنشاء المستخدم الأدمن
                self.create_admin_user()
                
                conn.commit()
                logging.info("تم تهيئة قاعدة البيانات بنجاح")
                
        except Exception as e:
            logging.error(f"خطأ في تهيئة قاعدة البيانات: {e}")
    
    def create_admin_user(self):
        """إنشاء المستخدم الأدمن"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # التحقق من وجود المستخدم الأدمن
                cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (config.ADMIN_USER_ID,))
                if not cursor.fetchone():
                    cursor.execute('''
                        INSERT INTO users (user_id, username, first_name, last_name, is_admin, settings)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        config.ADMIN_USER_ID,
                        'admin',
                        'مدير النظام',
                        'الأدمن',
                        True,
                        json.dumps({'language': 'ar', 'notifications': True, 'auto_save': True})
                    ))
                    conn.commit()
                    logging.info("تم إنشاء المستخدم الأدمن بنجاح")
                    
        except Exception as e:
            logging.error(f"خطأ في إنشاء المستخدم الأدمن: {e}")
    
    def add_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None, language_code: str = 'ar') -> bool:
        """إضافة مستخدم جديد"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, language_code)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, username, first_name, last_name, language_code))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"خطأ في إضافة المستخدم: {e}")
            return False
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """الحصول على بيانات المستخدم"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
                row = cursor.fetchone()
                if row:
                    columns = [description[0] for description in cursor.description]
                    return dict(zip(columns, row))
                return None
        except Exception as e:
            logging.error(f"خطأ في الحصول على بيانات المستخدم: {e}")
            return None
    
    def update_user_activity(self, user_id: int):
        """تحديث آخر نشاط للمستخدم"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users SET last_activity = CURRENT_TIMESTAMP 
                    WHERE user_id = ?
                ''', (user_id,))
                conn.commit()
        except Exception as e:
            logging.error(f"خطأ في تحديث نشاط المستخدم: {e}")
    
    def add_file(self, file_id: str, user_id: int, file_name: str, file_type: str, file_size: int, file_path: str) -> bool:
        """إضافة ملف جديد"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO files (file_id, user_id, file_name, file_type, file_size, file_path)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (file_id, user_id, file_name, file_type, file_size, file_path))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"خطأ في إضافة الملف: {e}")
            return False
    
    def update_file_analysis(self, file_id: str, analysis_result: str, metadata: Dict = None):
        """تحديث نتيجة تحليل الملف"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                metadata_str = json.dumps(metadata) if metadata else '{}'
                cursor.execute('''
                    UPDATE files SET processed = TRUE, analysis_result = ?, metadata = ?
                    WHERE file_id = ?
                ''', (analysis_result, metadata_str, file_id))
                conn.commit()
        except Exception as e:
            logging.error(f"خطأ في تحديث تحليل الملف: {e}")
    
    def get_user_files(self, user_id: int) -> List[Dict]:
        """الحصول على ملفات المستخدم"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM files WHERE user_id = ? ORDER BY uploaded_at DESC', (user_id,))
                rows = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logging.error(f"خطأ في الحصول على ملفات المستخدم: {e}")
            return []
    
    def add_task(self, task_id: str, user_id: int, agent_id: str, task_type: str, task_data: Dict, scheduled_for: str = None) -> bool:
        """إضافة مهمة جديدة"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                task_data_str = json.dumps(task_data)
                cursor.execute('''
                    INSERT INTO tasks (task_id, user_id, agent_id, task_type, task_data, scheduled_for)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (task_id, user_id, agent_id, task_type, task_data_str, scheduled_for))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"خطأ في إضافة المهمة: {e}")
            return False
    
    def update_task_status(self, task_id: str, status: str, result: str = None):
        """تحديث حالة المهمة"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                if result:
                    cursor.execute('''
                        UPDATE tasks SET status = ?, result = ?, completed_at = CURRENT_TIMESTAMP
                        WHERE task_id = ?
                    ''', (status, result, task_id))
                else:
                    cursor.execute('''
                        UPDATE tasks SET status = ? WHERE task_id = ?
                    ''', (status, task_id))
                conn.commit()
        except Exception as e:
            logging.error(f"خطأ في تحديث حالة المهمة: {e}")
    
    def get_pending_tasks(self) -> List[Dict]:
        """الحصول على المهام المعلقة"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM tasks WHERE status = 'pending' 
                    ORDER BY priority DESC, created_at ASC
                ''')
                rows = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logging.error(f"خطأ في الحصول على المهام المعلقة: {e}")
            return []
    
    def add_search(self, search_id: str, user_id: int, query: str, results: List[Dict], search_type: str = 'web') -> bool:
        """إضافة بحث جديد"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                results_str = json.dumps(results)
                cursor.execute('''
                    INSERT INTO searches (search_id, user_id, query, results, search_type)
                    VALUES (?, ?, ?, ?, ?)
                ''', (search_id, user_id, query, results_str, search_type))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"خطأ في إضافة البحث: {e}")
            return False
    
    def add_notification(self, notification_id: str, user_id: int, title: str, message: str, notification_type: str, scheduled_for: str = None) -> bool:
        """إضافة إشعار جديد"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO notifications (notification_id, user_id, title, message, notification_type, scheduled_for)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (notification_id, user_id, title, message, notification_type, scheduled_for))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"خطأ في إضافة الإشعار: {e}")
            return False
    
    def get_user_notifications(self, user_id: int, unread_only: bool = True) -> List[Dict]:
        """الحصول على إشعارات المستخدم"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                if unread_only:
                    cursor.execute('''
                        SELECT * FROM notifications WHERE user_id = ? AND is_read = FALSE
                        ORDER BY created_at DESC
                    ''', (user_id,))
                else:
                    cursor.execute('''
                        SELECT * FROM notifications WHERE user_id = ? 
                        ORDER BY created_at DESC LIMIT 50
                    ''', (user_id,))
                rows = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logging.error(f"خطأ في الحصول على إشعارات المستخدم: {e}")
            return []
    
    def mark_notification_read(self, notification_id: str):
        """تحديد الإشعار كمقروء"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE notifications SET is_read = TRUE WHERE notification_id = ?
                ''', (notification_id,))
                conn.commit()
        except Exception as e:
            logging.error(f"خطأ في تحديث حالة الإشعار: {e}")
    
    def get_statistics(self, user_id: int = None) -> Dict:
        """الحصول على إحصائيات النظام"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                stats = {}
                
                # إحصائيات المستخدمين
                if user_id:
                    cursor.execute('SELECT COUNT(*) FROM users WHERE user_id = ?', (user_id,))
                    stats['total_users'] = cursor.fetchone()[0]
                else:
                    cursor.execute('SELECT COUNT(*) FROM users')
                    stats['total_users'] = cursor.fetchone()[0]
                
                # إحصائيات الملفات
                if user_id:
                    cursor.execute('SELECT COUNT(*) FROM files WHERE user_id = ?', (user_id,))
                    stats['total_files'] = cursor.fetchone()[0]
                else:
                    cursor.execute('SELECT COUNT(*) FROM files')
                    stats['total_files'] = cursor.fetchone()[0]
                
                # إحصائيات المهام
                if user_id:
                    cursor.execute('SELECT COUNT(*) FROM tasks WHERE user_id = ?', (user_id,))
                    stats['total_tasks'] = cursor.fetchone()[0]
                else:
                    cursor.execute('SELECT COUNT(*) FROM tasks')
                    stats['total_tasks'] = cursor.fetchone()[0]
                
                # إحصائيات البحث
                if user_id:
                    cursor.execute('SELECT COUNT(*) FROM searches WHERE user_id = ?', (user_id,))
                    stats['total_searches'] = cursor.fetchone()[0]
                else:
                    cursor.execute('SELECT COUNT(*) FROM searches')
                    stats['total_searches'] = cursor.fetchone()[0]
                
                return stats
        except Exception as e:
            logging.error(f"خطأ في الحصول على الإحصائيات: {e}")
            return {}