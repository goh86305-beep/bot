# -*- coding: utf-8 -*-
"""
البوت الرئيسي لتيليجرام
"""

import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.constants import ParseMode
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
import uuid
from datetime import datetime

from config import *
from database import DatabaseManager
from gemini_client import GeminiClient
from agents_manager import AgentsManager
from file_processor import FileProcessor

# إعداد التسجيل
logging.basicConfig(
    format=LOG_FORMAT,
    level=getattr(logging, LOG_LEVEL),
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

class TelegramBot:
    """البوت الرئيسي لتيليجرام"""
    
    def __init__(self):
        """تهيئة البوت"""
        self.application = Application.builder().token(TELEGRAM_TOKEN).build()
        self.database_manager = DatabaseManager()
        self.gemini_client = GeminiClient()
        self.agents_manager = AgentsManager(self.database_manager, self.gemini_client)
        self.file_processor = FileProcessor()
        
        # إعداد المعالجات
        self._setup_handlers()
        
        logging.info("تم تهيئة البوت بنجاح")
    
    def _setup_handlers(self):
        """إعداد معالجات الأحداث"""
        # الأوامر الأساسية
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("menu", self.menu_command))
        
        # أوامر الأدمن
        self.application.add_handler(CommandHandler("admin", self.admin_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("users", self.users_command))
        
        # معالجة الرسائل النصية
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_message))
        
        # معالجة الملفات
        self.application.add_handler(MessageHandler(filters.Document.ALL, self.handle_document))
        
        # معالجة الأزرار
        self.application.add_handler(CallbackQueryHandler(self.handle_button_click))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة أمر البداية"""
        try:
            user_id = update.effective_user.id
            username = update.effective_user.username
            first_name = update.effective_user.first_name
            last_name = update.effective_user.last_name
            
            # إضافة المستخدم لقاعدة البيانات
            self.database_manager.add_user(user_id, username, first_name, last_name)
            
            welcome_message = f"""
مرحباً {first_name}! 👋

أنا بوت ذكي متقدم يمكنني:
📄 تحليل الملفات (PDF, Word, Excel, الكود)
🔍 البحث في الويب وجمع المعلومات
📝 تلخيص المحتوى وإنشاء التقارير
🤖 إدارة المهام المعقدة
📊 تحليل البيانات والإحصائيات

استخدم /menu لعرض القائمة الرئيسية
استخدم /help للمساعدة
            """
            
            await update.message.reply_text(welcome_message, parse_mode=ParseMode.HTML)
            
        except Exception as e:
            logging.error(f"خطأ في أمر البداية: {e}")
            await update.message.reply_text("عذراً، حدث خطأ. يرجى المحاولة مرة أخرى.")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة أمر المساعدة"""
        help_text = """
📚 <b>دليل الاستخدام</b>

<b>الأوامر الأساسية:</b>
/start - بدء البوت
/help - عرض هذه المساعدة
/menu - القائمة الرئيسية

<b>الوظائف المتاحة:</b>
📄 <b>تحليل الملفات:</b> أرسل أي ملف PDF أو Word أو Excel أو ملف كود
🔍 <b>البحث:</b> اكتب استعلام البحث وسأبحث لك
📝 <b>التلخيص:</b> أرسل نصاً وسأقوم بتلخيصه
🤖 <b>المهام المعقدة:</b> اكتب وصف المهمة وسأخطط لها

<b>أمثلة:</b>
• "ابحث عن الذكاء الاصطناعي"
• "حلل هذا الملف"
• "لخص هذا النص"
• "أنشئ تقرير عن التكنولوجيا"

<b>للمطورين:</b>
استخدم /admin للوصول لوظائف الإدارة
        """
        
        await update.message.reply_text(help_text, parse_mode=ParseMode.HTML)
    
    async def menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض القائمة الرئيسية"""
        keyboard = [
            [
                InlineKeyboardButton("📄 تحليل الملفات", callback_data="file_analysis"),
                InlineKeyboardButton("🔍 البحث في الويب", callback_data="web_search")
            ],
            [
                InlineKeyboardButton("📝 تلخيص المحتوى", callback_data="content_summary"),
                InlineKeyboardButton("🤖 إدارة المهام", callback_data="task_management")
            ],
            [
                InlineKeyboardButton("📊 تحليل البيانات", callback_data="data_analysis"),
                InlineKeyboardButton("⚙️ الإعدادات", callback_data="settings")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "🎯 <b>القائمة الرئيسية</b>\n\nاختر الوظيفة المطلوبة:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
    
    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر الأدمن"""
        user_id = update.effective_user.id
        
        if user_id != ADMIN_USER_ID:
            await update.message.reply_text("⛔ عذراً، هذا الأمر متاح للمدير فقط.")
            return
        
        keyboard = [
            [
                InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats"),
                InlineKeyboardButton("👥 المستخدمين", callback_data="admin_users")
            ],
            [
                InlineKeyboardButton("🤖 حالة الوكلاء", callback_data="admin_agents"),
                InlineKeyboardButton("📁 إدارة الملفات", callback_data="admin_files")
            ],
            [
                InlineKeyboardButton("⚙️ إعدادات النظام", callback_data="admin_settings"),
                InlineKeyboardButton("🔒 الأمان", callback_data="admin_security")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "🔐 <b>لوحة الإدارة</b>\n\nاختر الوظيفة الإدارية:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض الإحصائيات"""
        user_id = update.effective_user.id
        
        if user_id != ADMIN_USER_ID:
            await update.message.reply_text("⛔ عذراً، هذا الأمر متاح للمدير فقط.")
            return
        
        try:
            stats = self.database_manager.get_statistics()
            system_status = self.agents_manager.get_system_status()
            
            stats_message = f"""
📊 <b>إحصائيات النظام</b>

👥 <b>المستخدمين:</b>
• إجمالي المستخدمين: {stats.get('total_users', 0)}
• الملفات: {stats.get('total_files', 0)}
• المهام: {stats.get('total_tasks', 0)}
• عمليات البحث: {stats.get('total_searches', 0)}

🤖 <b>الوكلاء:</b>
• إجمالي الوكلاء: {system_status.get('total_agents', 0)}
• الوكلاء النشطة: {system_status.get('active_agents', 0)}
• الوكلاء المشغولة: {system_status.get('busy_agents', 0)}

🏥 <b>صحة النظام:</b> {system_status.get('system_health', 'unknown')}
            """
            
            await update.message.reply_text(stats_message, parse_mode=ParseMode.HTML)
            
        except Exception as e:
            logging.error(f"خطأ في عرض الإحصائيات: {e}")
            await update.message.reply_text("عذراً، حدث خطأ في عرض الإحصائيات.")
    
    async def users_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض المستخدمين"""
        user_id = update.effective_user.id
        
        if user_id != ADMIN_USER_ID:
            await update.message.reply_text("⛔ عذراً، هذا الأمر متاح للمدير فقط.")
            return
        
        await update.message.reply_text("👥 <b>إدارة المستخدمين</b>\n\nسيتم إضافة هذه الوظيفة قريباً.", parse_mode=ParseMode.HTML)
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة الرسائل النصية"""
        try:
            user_id = update.effective_user.id
            message_text = update.message.text
            
            # تحديث نشاط المستخدم
            self.database_manager.update_user_activity(user_id)
            
            # إرسال رسالة "جاري المعالجة"
            processing_msg = await update.message.reply_text("🤔 جاري التفكير في طلبك...")
            
            # تحليل الرسالة وتحديد نوع الطلب
            if "ابحث" in message_text or "search" in message_text.lower():
                await self._handle_search_request(update, context, message_text, processing_msg)
            elif "لخص" in message_text or "summarize" in message_text.lower():
                await self._handle_summary_request(update, context, message_text, processing_msg)
            elif "حلل" in message_text or "analyze" in message_text.lower():
                await self._handle_analysis_request(update, context, message_text, processing_msg)
            elif "أنشئ" in message_text or "create" in message_text.lower():
                await self._handle_creation_request(update, context, message_text, processing_msg)
            else:
                await self._handle_general_request(update, context, message_text, processing_msg)
                
        except Exception as e:
            logging.error(f"خطأ في معالجة الرسالة النصية: {e}")
            await update.message.reply_text("عذراً، حدث خطأ في معالجة رسالتك.")
    
    async def _handle_search_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE, message_text: str, processing_msg):
        """معالجة طلب البحث"""
        try:
            # استخراج استعلام البحث
            query = message_text.replace("ابحث", "").replace("search", "").strip()
            if not query:
                query = message_text
            
            # تنفيذ البحث
            result = await self.agents_manager.execute_task_with_agent("web_searcher", {
                "query": query,
                "search_type": "web",
                "max_results": 5,
                "user_id": update.effective_user.id
            })
            
            if result["status"] == "success":
                # عرض النتائج
                response = f"🔍 <b>نتائج البحث:</b> {query}\n\n"
                
                if "summary" in result:
                    response += f"📝 <b>الملخص:</b>\n{result['summary']}\n\n"
                
                response += "📋 <b>النتائج:</b>\n"
                for i, item in enumerate(result.get("search_results", [])[:3], 1):
                    response += f"{i}. <b>{item.get('title', 'بدون عنوان')}</b>\n"
                    response += f"   {item.get('snippet', 'بدون وصف')[:100]}...\n"
                    response += f"   🔗 <a href='{item.get('link', '#')}'>رابط</a>\n\n"
                
                await processing_msg.edit_text(response, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            else:
                await processing_msg.edit_text(f"❌ خطأ في البحث: {result.get('error', 'خطأ غير معروف')}")
                
        except Exception as e:
            logging.error(f"خطأ في معالجة طلب البحث: {e}")
            await processing_msg.edit_text("عذراً، حدث خطأ في البحث.")
    
    async def _handle_summary_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE, message_text: str, processing_msg):
        """معالجة طلب التلخيص"""
        try:
            # استخراج النص للتلخيص
            content = message_text.replace("لخص", "").replace("summarize", "").strip()
            if not content:
                content = message_text
            
            # تنفيذ التلخيص
            result = await self.agents_manager.execute_task_with_agent("content_summarizer", {
                "content": content,
                "summary_type": "general",
                "max_length": 300,
                "user_id": update.effective_user.id
            })
            
            if result["status"] == "success":
                response = f"📝 <b>ملخص المحتوى:</b>\n\n{result['summary']}\n\n"
                response += f"📊 <b>الإحصائيات:</b>\n"
                response += f"• النص الأصلي: {result.get('original_length', 0)} حرف\n"
                response += f"• الملخص: {result.get('summary_length', 0)} حرف\n"
                response += f"• نسبة التلخيص: {((result.get('summary_length', 0) / max(result.get('original_length', 1), 1)) * 100):.1f}%"
                
                await processing_msg.edit_text(response, parse_mode=ParseMode.HTML)
            else:
                await processing_msg.edit_text(f"❌ خطأ في التلخيص: {result.get('error', 'خطأ غير معروف')}")
                
        except Exception as e:
            logging.error(f"خطأ في معالجة طلب التلخيص: {e}")
            await processing_msg.edit_text("عذراً، حدث خطأ في التلخيص.")
    
    async def _handle_analysis_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE, message_text: str, processing_msg):
        """معالجة طلب التحليل"""
        try:
            # استخراج النص للتحليل
            content = message_text.replace("حلل", "").replace("analyze", "").strip()
            if not content:
                content = message_text
            
            # تنفيذ التحليل
            result = await self.agents_manager.execute_task_with_agent("content_summarizer", {
                "content": content,
                "summary_type": "key_points",
                "max_length": 500,
                "user_id": update.effective_user.id
            })
            
            if result["status"] == "success":
                response = f"🔍 <b>تحليل المحتوى:</b>\n\n"
                response += f"📝 <b>الملخص:</b>\n{result['summary']}\n\n"
                response += f"🎯 <b>النقاط الرئيسية:</b>\n{result.get('key_points', 'غير متوفر')}"
                
                await processing_msg.edit_text(response, parse_mode=ParseMode.HTML)
            else:
                await processing_msg.edit_text(f"❌ خطأ في التحليل: {result.get('error', 'خطأ غير معروف')}")
                
        except Exception as e:
            logging.error(f"خطأ في معالجة طلب التحليل: {e}")
            await processing_msg.edit_text("عذراً، حدث خطأ في التحليل.")
    
    async def _handle_creation_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE, message_text: str, processing_msg):
        """معالجة طلب الإنشاء"""
        try:
            # استخراج وصف المحتوى
            description = message_text.replace("أنشئ", "").replace("create", "").strip()
            if not description:
                description = message_text
            
            # تنفيذ الإنشاء
            result = await self.agents_manager.execute_task_with_agent("file_generator", {
                "file_type": "text",
                "content_description": description,
                "file_name": f"generated_content_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                "user_id": update.effective_user.id
            })
            
            if result["status"] == "success":
                response = f"✅ <b>تم إنشاء المحتوى بنجاح!</b>\n\n"
                response += f"📁 <b>اسم الملف:</b> {result['file_name']}\n"
                response += f"📊 <b>حجم المحتوى:</b> {result['content_length']} حرف\n"
                response += f"🕒 <b>وقت الإنشاء:</b> {result['generated_at']}\n\n"
                response += f"📝 <b>المحتوى:</b>\n{result.get('content', 'غير متوفر')[:500]}..."
                
                await processing_msg.edit_text(response, parse_mode=ParseMode.HTML)
            else:
                await processing_msg.edit_text(f"❌ خطأ في الإنشاء: {result.get('error', 'خطأ غير معروف')}")
                
        except Exception as e:
            logging.error(f"خطأ في معالجة طلب الإنشاء: {e}")
            await processing_msg.edit_text("عذراً، حدث خطأ في الإنشاء.")
    
    async def _handle_general_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE, message_text: str, processing_msg):
        """معالجة الطلبات العامة"""
        try:
            # استخدام Gemini للرد العام
            response = await self.gemini_client.generate_response(
                message_text,
                system_prompt="أنت مساعد ذكي مفيد. أجب باللغة العربية بطريقة ودية ومفيدة."
            )
            
            await processing_msg.edit_text(f"💡 <b>ردي:</b>\n\n{response}", parse_mode=ParseMode.HTML)
            
        except Exception as e:
            logging.error(f"خطأ في معالجة الطلب العام: {e}")
            await processing_msg.edit_text("عذراً، حدث خطأ في معالجة طلبك.")
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة الملفات المرسلة"""
        try:
            user_id = update.effective_user.id
            document = update.message.document
            
            # تحديث نشاط المستخدم
            self.database_manager.update_user_activity(user_id)
            
            # إرسال رسالة "جاري المعالجة"
            processing_msg = await update.message.reply_text("📄 جاري معالجة الملف...")
            
            # تحميل الملف
            file_path = await self._download_file(context, document)
            
            if not file_path:
                await processing_msg.edit_text("❌ فشل في تحميل الملف.")
                return
            
            # إضافة الملف لقاعدة البيانات
            self.database_manager.add_file(
                document.file_id,
                user_id,
                document.file_name,
                document.mime_type or "unknown",
                document.file_size,
                file_path
            )
            
            # تحليل الملف
            result = await self.agents_manager.execute_task_with_agent("file_analyzer", {
                "file_path": file_path,
                "analysis_type": "general",
                "user_id": user_id
            })
            
            if result["status"] == "success":
                response = f"📄 <b>تحليل الملف:</b> {document.file_name}\n\n"
                
                if "file_info" in result:
                    file_info = result["file_info"]
                    response += f"📊 <b>معلومات الملف:</b>\n"
                    response += f"• النوع: {file_info.get('file_type', 'غير معروف')}\n"
                    response += f"• الحجم: {file_info.get('file_size', 0) // 1024} KB\n"
                    response += f"• الامتداد: {file_info.get('extension', 'غير معروف')}\n\n"
                
                if "file_content" in result:
                    file_content = result["file_content"]
                    response += f"📝 <b>محتوى الملف:</b>\n"
                    response += f"• النوع: {file_content.get('file_type', 'غير معروف')}\n"
                    
                    if file_content.get('file_type') == 'pdf':
                        response += f"• عدد الصفحات: {file_content.get('pages', 0)}\n"
                    elif file_content.get('file_type') == 'word':
                        response += f"• عدد الفقرات: {file_content.get('paragraphs', 0)}\n"
                        response += f"• عدد الجداول: {file_content.get('tables', 0)}\n"
                    elif file_content.get('file_type') == 'excel':
                        response += f"• عدد الأوراق: {len(file_content.get('sheets', []))}\n"
                    elif file_content.get('file_type') == 'code':
                        response += f"• لغة البرمجة: {file_content.get('language', 'غير معروف')}\n"
                        response += f"• عدد الأسطر: {file_content.get('lines', 0)}\n"
                        response += f"• عدد الدوال: {file_content.get('functions', 0)}\n"
                        response += f"• عدد الفئات: {file_content.get('classes', 0)}\n"
                
                response += f"\n🔍 <b>التحليل:</b>\n{result.get('analysis_result', 'غير متوفر')}"
                
                await processing_msg.edit_text(response, parse_mode=ParseMode.HTML)
            else:
                await processing_msg.edit_text(f"❌ خطأ في تحليل الملف: {result.get('error', 'خطأ غير معروف')}")
                
        except Exception as e:
            logging.error(f"خطأ في معالجة الملف: {e}")
            await update.message.reply_text("عذراً، حدث خطأ في معالجة الملف.")
    
    async def _download_file(self, context: ContextTypes.DEFAULT_TYPE, document) -> Optional[str]:
        """تحميل الملف"""
        try:
            file = await context.bot.get_file(document.file_id)
            file_path = f"uploads/{document.file_name}"
            
            # إنشاء مجلد التحميل إذا لم يكن موجوداً
            os.makedirs("uploads", exist_ok=True)
            
            # تحميل الملف
            await file.download_to_drive(file_path)
            
            return file_path
            
        except Exception as e:
            logging.error(f"خطأ في تحميل الملف: {e}")
            return None
    
    async def handle_button_click(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة النقر على الأزرار"""
        try:
            query = update.callback_query
            await query.answer()
            
            callback_data = query.data
            
            if callback_data == "file_analysis":
                await self._show_file_analysis_menu(query)
            elif callback_data == "web_search":
                await self._show_web_search_menu(query)
            elif callback_data == "content_summary":
                await self._show_content_summary_menu(query)
            elif callback_data == "task_management":
                await self._show_task_management_menu(query)
            elif callback_data == "data_analysis":
                await self._show_data_analysis_menu(query)
            elif callback_data == "settings":
                await self._show_settings_menu(query)
            elif callback_data.startswith("admin_"):
                await self._handle_admin_callback(query, callback_data)
            else:
                await query.edit_message_text("❌ وظيفة غير معروفة.")
                
        except Exception as e:
            logging.error(f"خطأ في معالجة النقر على الزر: {e}")
            await update.callback_query.edit_message_text("عذراً، حدث خطأ.")
    
    async def _show_file_analysis_menu(self, query):
        """عرض قائمة تحليل الملفات"""
        keyboard = [
            [
                InlineKeyboardButton("📄 PDF", callback_data="analyze_pdf"),
                InlineKeyboardButton("📝 Word", callback_data="analyze_word")
            ],
            [
                InlineKeyboardButton("📊 Excel", callback_data="analyze_excel"),
                InlineKeyboardButton("💻 الكود", callback_data="analyze_code")
            ],
            [
                InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "📄 <b>تحليل الملفات</b>\n\nأرسل الملف الذي تريد تحليله:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
    
    async def _show_web_search_menu(self, query):
        """عرض قائمة البحث في الويب"""
        keyboard = [
            [
                InlineKeyboardButton("🌐 بحث عام", callback_data="search_web"),
                InlineKeyboardButton("📰 أخبار", callback_data="search_news")
            ],
            [
                InlineKeyboardButton("🎓 أكاديمي", callback_data="search_academic"),
                InlineKeyboardButton("🔥 رائج", callback_data="search_trending")
            ],
            [
                InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "🔍 <b>البحث في الويب</b>\n\nاكتب استعلام البحث:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
    
    async def _show_content_summary_menu(self, query):
        """عرض قائمة تلخيص المحتوى"""
        keyboard = [
            [
                InlineKeyboardButton("📝 تلخيص عام", callback_data="summary_general"),
                InlineKeyboardButton("🎯 نقاط رئيسية", callback_data="summary_key_points")
            ],
            [
                InlineKeyboardButton("📊 تحليل شامل", callback_data="summary_analysis"),
                InlineKeyboardButton("🔍 تحليل تقني", callback_data="summary_technical")
            ],
            [
                InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "📝 <b>تلخيص المحتوى</b>\n\nأرسل النص الذي تريد تلخيصه:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
    
    async def _show_task_management_menu(self, query):
        """عرض قائمة إدارة المهام"""
        keyboard = [
            [
                InlineKeyboardButton("📋 تخطيط المهام", callback_data="task_planning"),
                InlineKeyboardButton("🔄 تنسيق المهام", callback_data="task_coordination")
            ],
            [
                InlineKeyboardButton("⚡ مهام سريعة", callback_data="task_quick"),
                InlineKeyboardButton("📅 مهام مجدولة", callback_data="task_scheduled")
            ],
            [
                InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "🤖 <b>إدارة المهام</b>\n\nاكتب وصف المهمة:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
    
    async def _show_data_analysis_menu(self, query):
        """عرض قائمة تحليل البيانات"""
        keyboard = [
            [
                InlineKeyboardButton("📊 تحليل إحصائي", callback_data="analysis_statistical"),
                InlineKeyboardButton("📈 تحليل الاتجاهات", callback_data="analysis_trends")
            ],
            [
                InlineKeyboardButton("🔍 تحليل شامل", callback_data="analysis_comprehensive"),
                InlineKeyboardButton("📋 تقارير", callback_data="analysis_reports")
            ],
            [
                InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "📊 <b>تحليل البيانات</b>\n\nأرسل البيانات للتحليل:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
    
    async def _show_settings_menu(self, query):
        """عرض قائمة الإعدادات"""
        keyboard = [
            [
                InlineKeyboardButton("🌐 اللغة", callback_data="setting_language"),
                InlineKeyboardButton("🔔 الإشعارات", callback_data="setting_notifications")
            ],
            [
                InlineKeyboardButton("💾 الحفظ التلقائي", callback_data="setting_auto_save"),
                InlineKeyboardButton("🔒 الخصوصية", callback_data="setting_privacy")
            ],
            [
                InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "⚙️ <b>الإعدادات</b>\n\nاختر الإعداد المطلوب:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
    
    async def _handle_admin_callback(self, query, callback_data):
        """معالجة استدعاءات الأدمن"""
        user_id = query.from_user.id
        
        if user_id != ADMIN_USER_ID:
            await query.edit_message_text("⛔ عذراً، هذا متاح للمدير فقط.")
            return
        
        if callback_data == "admin_stats":
            await self._show_admin_stats(query)
        elif callback_data == "admin_users":
            await self._show_admin_users(query)
        elif callback_data == "admin_agents":
            await self._show_admin_agents(query)
        elif callback_data == "admin_files":
            await self._show_admin_files(query)
        elif callback_data == "admin_settings":
            await self._show_admin_settings(query)
        elif callback_data == "admin_security":
            await self._show_admin_security(query)
    
    async def _show_admin_stats(self, query):
        """عرض إحصائيات الأدمن"""
        try:
            stats = self.database_manager.get_statistics()
            system_status = self.agents_manager.get_system_status()
            
            stats_message = f"""
📊 <b>إحصائيات النظام</b>

👥 <b>المستخدمين:</b>
• إجمالي المستخدمين: {stats.get('total_users', 0)}
• الملفات: {stats.get('total_files', 0)}
• المهام: {stats.get('total_tasks', 0)}
• عمليات البحث: {stats.get('total_searches', 0)}

🤖 <b>الوكلاء:</b>
• إجمالي الوكلاء: {system_status.get('total_agents', 0)}
• الوكلاء النشطة: {system_status.get('active_agents', 0)}
• الوكلاء المشغولة: {system_status.get('busy_agents', 0)}

🏥 <b>صحة النظام:</b> {system_status.get('system_health', 'unknown')}
            """
            
            keyboard = [[InlineKeyboardButton("🔙 العودة", callback_data="admin")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(stats_message, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
            
        except Exception as e:
            logging.error(f"خطأ في عرض إحصائيات الأدمن: {e}")
            await query.edit_message_text("عذراً، حدث خطأ في عرض الإحصائيات.")
    
    async def _show_admin_users(self, query):
        """عرض مستخدمي الأدمن"""
        await query.edit_message_text("👥 <b>إدارة المستخدمين</b>\n\nسيتم إضافة هذه الوظيفة قريباً.", parse_mode=ParseMode.HTML)
    
    async def _show_admin_agents(self, query):
        """عرض وكلاء الأدمن"""
        await query.edit_message_text("🤖 <b>إدارة الوكلاء</b>\n\nسيتم إضافة هذه الوظيفة قريباً.", parse_mode=ParseMode.HTML)
    
    async def _show_admin_files(self, query):
        """عرض ملفات الأدمن"""
        await query.edit_message_text("📁 <b>إدارة الملفات</b>\n\nسيتم إضافة هذه الوظيفة قريباً.", parse_mode=ParseMode.HTML)
    
    async def _show_admin_settings(self, query):
        """عرض إعدادات الأدمن"""
        await query.edit_message_text("⚙️ <b>إعدادات النظام</b>\n\nسيتم إضافة هذه الوظيفة قريباً.", parse_mode=ParseMode.HTML)
    
    async def _show_admin_security(self, query):
        """عرض أمان الأدمن"""
        await query.edit_message_text("🔒 <b>أمان النظام</b>\n\nسيتم إضافة هذه الوظيفة قريباً.", parse_mode=ParseMode.HTML)
    
    def run(self):
        """تشغيل البوت"""
        try:
            logging.info("بدء تشغيل البوت...")
            self.application.run_polling()
        except Exception as e:
            logging.error(f"خطأ في تشغيل البوت: {e}")

if __name__ == "__main__":
    # إنشاء وتشغيل البوت
    bot = TelegramBot()
    bot.run()