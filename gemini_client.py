# -*- coding: utf-8 -*-
"""
عميل Gemini API للذكاء الاصطناعي
"""

import google.generativeai as genai
import logging
import json
from typing import Dict, List, Optional, Any
import config

class GeminiClient:
    """عميل Gemini API الرئيسي"""
    
    def __init__(self):
        """تهيئة عميل Gemini"""
        try:
            genai.configure(api_key=config.GEMINI_API_KEY)
            self.model = genai.GenerativeModel(config.GEMINI_MODEL)
            self.generation_config = genai.types.GenerationConfig(
                temperature=config.GEMINI_TEMPERATURE,
                max_output_tokens=config.GEMINI_MAX_TOKENS,
            )
            logging.info("تم تهيئة عميل Gemini بنجاح")
        except Exception as e:
            logging.error(f"خطأ في تهيئة عميل Gemini: {e}")
            raise
    
    async def generate_response(self, prompt: str, context: str = None, system_prompt: str = None) -> str:
        """توليد رد من Gemini"""
        try:
            # بناء الرسالة الكاملة
            full_prompt = ""
            if system_prompt:
                full_prompt += f"System: {system_prompt}\n\n"
            if context:
                full_prompt += f"Context: {context}\n\n"
            full_prompt += f"User: {prompt}\n\nAssistant:"
            
            # توليد الرد
            response = self.model.generate_content(
                full_prompt,
                generation_config=self.generation_config
            )
            
            return response.text.strip()
            
        except Exception as e:
            logging.error(f"خطأ في توليد رد Gemini: {e}")
            return f"عذراً، حدث خطأ في معالجة طلبك: {str(e)}"
    
    async def analyze_text(self, text: str, analysis_type: str = "general") -> Dict[str, Any]:
        """تحليل النص باستخدام Gemini"""
        try:
            analysis_prompts = {
                "general": "قم بتحليل النص التالي وتقديم ملخص شامل مع النقاط الرئيسية والرؤى المهمة:",
                "summary": "قم بتلخيص النص التالي في نقاط رئيسية واضحة ومختصرة:",
                "sentiment": "قم بتحليل مشاعر النص التالي وتحديد النبرة العامة:",
                "technical": "قم بتحليل النص التقني التالي وتحديد المفاهيم والمصطلحات المهمة:",
                "code": "قم بتحليل الكود التالي وتحديد الوظائف والمشاكل المحتملة:"
            }
            
            prompt = analysis_prompts.get(analysis_type, analysis_prompts["general"])
            full_prompt = f"{prompt}\n\nالنص:\n{text}\n\nالتحليل:"
            
            response = await self.generate_response(full_prompt)
            
            return {
                "analysis_type": analysis_type,
                "original_text": text,
                "analysis_result": response,
                "status": "success"
            }
            
        except Exception as e:
            logging.error(f"خطأ في تحليل النص: {e}")
            return {
                "analysis_type": analysis_type,
                "original_text": text,
                "analysis_result": f"خطأ في التحليل: {str(e)}",
                "status": "error"
            }
    
    async def summarize_content(self, content: str, max_length: int = 500) -> str:
        """تلخيص المحتوى"""
        try:
            prompt = f"""
            قم بتلخيص المحتوى التالي في {max_length} كلمة أو أقل:
            
            المحتوى:
            {content}
            
            الملخص:
            """
            
            response = await self.generate_response(prompt)
            return response[:max_length]
            
        except Exception as e:
            logging.error(f"خطأ في تلخيص المحتوى: {e}")
            return f"خطأ في التلخيص: {str(e)}"
    
    async def generate_file_content(self, file_type: str, content_description: str, format_specs: Dict = None) -> str:
        """إنشاء محتوى ملف جديد"""
        try:
            format_instructions = ""
            if format_specs:
                format_instructions = f"\nمتطلبات التنسيق: {json.dumps(format_specs, ensure_ascii=False)}"
            
            prompt = f"""
            قم بإنشاء محتوى لملف {file_type} بناءً على الوصف التالي:
            
            الوصف: {content_description}
            {format_instructions}
            
            المحتوى:
            """
            
            response = await self.generate_response(prompt)
            return response
            
        except Exception as e:
            logging.error(f"خطأ في إنشاء محتوى الملف: {e}")
            return f"خطأ في إنشاء المحتوى: {str(e)}"
    
    async def process_search_results(self, query: str, search_results: List[Dict]) -> Dict[str, Any]:
        """معالجة نتائج البحث وتحليلها"""
        try:
            # تجميع نتائج البحث
            results_text = ""
            for i, result in enumerate(search_results[:5], 1):  # أول 5 نتائج فقط
                results_text += f"{i}. {result.get('title', 'بدون عنوان')}\n"
                results_text += f"   {result.get('snippet', 'بدون وصف')}\n"
                results_text += f"   الرابط: {result.get('link', 'بدون رابط')}\n\n"
            
            prompt = f"""
            قم بتحليل نتائج البحث التالية والاستعلام "{query}":
            
            نتائج البحث:
            {results_text}
            
            المطلوب:
            1. تلخيص المعلومات الرئيسية
            2. تصنيف النتائج حسب الموضوع
            3. تحديد المصادر الأكثر موثوقية
            4. تقديم رؤى وتوصيات
            
            التحليل:
            """
            
            analysis = await self.generate_response(prompt)
            
            return {
                "query": query,
                "search_results": search_results,
                "analysis": analysis,
                "summary": await self.summarize_content(analysis, 300),
                "status": "success"
            }
            
        except Exception as e:
            logging.error(f"خطأ في معالجة نتائج البحث: {e}")
            return {
                "query": query,
                "search_results": search_results,
                "analysis": f"خطأ في المعالجة: {str(e)}",
                "summary": "فشل في معالجة نتائج البحث",
                "status": "error"
            }
    
    async def generate_code_analysis(self, code: str, language: str = "python") -> Dict[str, Any]:
        """تحليل الكود وتوليد تقرير شامل"""
        try:
            prompt = f"""
            قم بتحليل الكود التالي المكتوب بلغة {language}:
            
            الكود:
            ```{language}
            {code}
            ```
            
            المطلوب:
            1. شرح وظيفة الكود
            2. تحديد المشاكل المحتملة
            3. اقتراح تحسينات
            4. تقييم جودة الكود
            5. اقتراح اختبارات
            
            التحليل:
            """
            
            analysis = await self.generate_response(prompt)
            
            return {
                "code": code,
                "language": language,
                "analysis": analysis,
                "summary": await self.summarize_content(analysis, 200),
                "status": "success"
            }
            
        except Exception as e:
            logging.error(f"خطأ في تحليل الكود: {e}")
            return {
                "code": code,
                "language": language,
                "analysis": f"خطأ في التحليل: {str(e)}",
                "summary": "فشل في تحليل الكود",
                "status": "error"
            }
    
    async def generate_task_plan(self, task_description: str, available_agents: List[str]) -> Dict[str, Any]:
        """توليد خطة تنفيذ المهمة"""
        try:
            agents_text = "\n".join([f"- {agent}" for agent in available_agents])
            
            prompt = f"""
            قم بتخطيط تنفيذ المهمة التالية باستخدام الوكلاء المتاحة:
            
            المهمة: {task_description}
            
            الوكلاء المتاحة:
            {agents_text}
            
            المطلوب:
            1. تقسيم المهمة إلى خطوات
            2. تحديد الوكلاء المناسبة لكل خطوة
            3. ترتيب الخطوات
            4. تقدير الوقت المطلوب
            5. تحديد المتطلبات والموارد
            
            الخطة:
            """
            
            plan = await self.generate_response(prompt)
            
            return {
                "task_description": task_description,
                "available_agents": available_agents,
                "execution_plan": plan,
                "summary": await self.summarize_content(plan, 250),
                "status": "success"
            }
            
        except Exception as e:
            logging.error(f"خطأ في توليد خطة المهمة: {e}")
            return {
                "task_description": task_description,
                "available_agents": available_agents,
                "execution_plan": f"خطأ في التخطيط: {str(e)}",
                "summary": "فشل في تخطيط المهمة",
                "status": "error"
            }
    
    async def translate_text(self, text: str, target_language: str, source_language: str = "auto") -> str:
        """ترجمة النص"""
        try:
            prompt = f"""
            قم بترجمة النص التالي من {source_language} إلى {target_language}:
            
            النص الأصلي:
            {text}
            
            الترجمة:
            """
            
            response = await self.generate_response(prompt)
            return response
            
        except Exception as e:
            logging.error(f"خطأ في الترجمة: {e}")
            return f"خطأ في الترجمة: {str(e)}"
    
    async def generate_report(self, data: Dict[str, Any], report_type: str = "general") -> str:
        """توليد تقرير من البيانات"""
        try:
            data_summary = json.dumps(data, ensure_ascii=False, indent=2)
            
            prompt = f"""
            قم بإنشاء تقرير {report_type} بناءً على البيانات التالية:
            
            البيانات:
            {data_summary}
            
            المطلوب:
            1. ملخص تنفيذي
            2. النقاط الرئيسية
            3. التحليل والتفسير
            4. التوصيات
            5. الخلاصة
            
            التقرير:
            """
            
            report = await self.generate_response(prompt)
            return report
            
        except Exception as e:
            logging.error(f"خطأ في توليد التقرير: {e}")
            return f"خطأ في توليد التقرير: {str(e)}"