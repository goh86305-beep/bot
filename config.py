# -*- coding: utf-8 -*-
"""
ملف الإعدادات والثوابت لبوت تيليجرام الذكي
"""

import os
from typing import Dict, List

# مفاتيح API
TELEGRAM_TOKEN = "8079187209:AAGa0RQ4sZta4tUu1jsTSHXsOnUqLpdVBBo"
GEMINI_API_KEY = "AIzaSyBA5fBhhxIRuJxG9kNPu1JQ8wLMce9p_bg"

# معرف المستخدم الأدمن
ADMIN_USER_ID = 6572227539

# إعدادات Gemini
GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_MAX_TOKENS = 8192
GEMINI_TEMPERATURE = 0.7

# إعدادات قاعدة البيانات
DATABASE_PATH = "ai_agent_bot.db"

# إعدادات الملفات
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
SUPPORTED_FORMATS = {
    'pdf': ['.pdf'],
    'word': ['.doc', '.docx'],
    'excel': ['.xls', '.xlsx'],
    'text': ['.txt', '.md'],
    'code': ['.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.scala']
}

# إعدادات البحث
DUCKDUCKGO_MAX_RESULTS = 10
SEARCH_TIMEOUT = 30

# إعدادات الجدولة
SCHEDULER_INTERVAL = 60  # ثانية

# إعدادات الأمان
ENCRYPTION_KEY = "your-secret-encryption-key-here"
SESSION_TIMEOUT = 3600  # ساعة

# إعدادات اللغات المدعومة
SUPPORTED_LANGUAGES = ['ar', 'en', 'fr', 'es', 'de', 'zh', 'ja', 'ko', 'ru']

# إعدادات الوكلاء
AGENT_TYPES = {
    'file_analyzer': 'محلل الملفات',
    'web_searcher': 'باحث الويب',
    'content_summarizer': 'ملخص المحتوى',
    'file_generator': 'منشئ الملفات',
    'task_manager': 'مدير المهام',
    'data_analyzer': 'محلل البيانات'
}

# إعدادات التسجيل
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = "bot.log"