#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ملف التشغيل الرئيسي لبوت تيليجرام الذكي
"""

import os
import sys
import logging
from pathlib import Path

# إضافة المجلد الحالي لمسار Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def setup_environment():
    """إعداد البيئة"""
    try:
        # إنشاء المجلدات المطلوبة
        folders = ['uploads', 'outputs', 'logs']
        for folder in folders:
            Path(folder).mkdir(exist_ok=True)
        
        # إعداد التسجيل
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/bot.log', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        logging.info("تم إعداد البيئة بنجاح")
        return True
        
    except Exception as e:
        print(f"خطأ في إعداد البيئة: {e}")
        return False

def check_dependencies():
    """التحقق من المكتبات المطلوبة"""
    try:
        import telegram
        import google.generativeai
        import PyPDF2
        import docx
        import openpyxl
        import requests
        import bs4
        import duckduckgo_search
        
        logging.info("جميع المكتبات متوفرة")
        return True
        
    except ImportError as e:
        print(f"مكتبة مفقودة: {e}")
        print("يرجى تثبيت المكتبات المطلوبة:")
        print("pip install -r requirements.txt")
        return False

def check_config():
    """التحقق من الإعدادات"""
    try:
        from config import TELEGRAM_TOKEN, GEMINI_API_KEY, ADMIN_USER_ID
        
        if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == "your-telegram-token":
            print("❌ خطأ: يرجى تعيين TELEGRAM_TOKEN في config.py")
            return False
        
        if not GEMINI_API_KEY or GEMINI_API_KEY == "your-gemini-api-key":
            print("❌ خطأ: يرجى تعيين GEMINI_API_KEY في config.py")
            return False
        
        if not ADMIN_USER_ID or ADMIN_USER_ID == 0:
            print("❌ خطأ: يرجى تعيين ADMIN_USER_ID في config.py")
            return False
        
        logging.info("تم التحقق من الإعدادات بنجاح")
        return True
        
    except Exception as e:
        print(f"خطأ في التحقق من الإعدادات: {e}")
        return False

def main():
    """الدالة الرئيسية"""
    print("🚀 بدء تشغيل بوت تيليجرام الذكي...")
    print("=" * 50)
    
    # إعداد البيئة
    if not setup_environment():
        print("❌ فشل في إعداد البيئة")
        sys.exit(1)
    
    # التحقق من المكتبات
    if not check_dependencies():
        print("❌ فشل في التحقق من المكتبات")
        sys.exit(1)
    
    # التحقق من الإعدادات
    if not check_config():
        print("❌ فشل في التحقق من الإعدادات")
        sys.exit(1)
    
    print("✅ جميع الفحوصات نجحت!")
    print("🤖 بدء تشغيل البوت...")
    print("=" * 50)
    
    try:
        # استيراد وتشغيل البوت
        from telegram_bot import TelegramBot
        
        bot = TelegramBot()
        bot.run()
        
    except KeyboardInterrupt:
        print("\n🛑 تم إيقاف البوت بواسطة المستخدم")
        logging.info("تم إيقاف البوت بواسطة المستخدم")
        
    except Exception as e:
        print(f"❌ خطأ في تشغيل البوت: {e}")
        logging.error(f"خطأ في تشغيل البوت: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()