# -*- coding: utf-8 -*-
"""
مدير الوكلاء لإدارة الوكلاء الفرعيين
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import uuid
import json
from database import DatabaseManager
from gemini_client import GeminiClient
from file_processor import FileProcessor
from web_searcher import WebSearcher
import config

class Agent:
    """الوكيل الأساسي"""
    
    def __init__(self, agent_id: str, agent_type: str, agent_name: str, capabilities: List[str] = None):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.agent_name = agent_name
        self.capabilities = capabilities or []
        self.status = "active"
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.settings = {}
        self.task_queue = []
        self.is_busy = False
    
    async def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """تنفيذ مهمة (يجب تجاوزها في الوكلاء الفرعية)"""
        raise NotImplementedError("يجب تجاوز هذه الطريقة في الوكلاء الفرعية")
    
    def update_activity(self):
        """تحديث آخر نشاط"""
        self.last_activity = datetime.now()
    
    def add_task(self, task: Dict[str, Any]):
        """إضافة مهمة للطابور"""
        self.task_queue.append(task)
    
    def get_status(self) -> Dict[str, Any]:
        """الحصول على حالة الوكيل"""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "agent_name": self.agent_name,
            "status": self.status,
            "capabilities": self.capabilities,
            "is_busy": self.is_busy,
            "queue_length": len(self.task_queue),
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat()
        }

class FileAnalysisAgent(Agent):
    """وكيل تحليل الملفات"""
    
    def __init__(self, agent_id: str, gemini_client: GeminiClient, file_processor: FileProcessor):
        super().__init__(agent_id, "file_analyzer", "محلل الملفات", 
                         ["pdf_analysis", "word_analysis", "excel_analysis", "code_analysis", "text_analysis"])
        self.gemini_client = gemini_client
        self.file_processor = file_processor
    
    async def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """تنفيذ مهمة تحليل الملف"""
        try:
            self.is_busy = True
            self.update_activity()
            
            file_path = task_data.get("file_path")
            analysis_type = task_data.get("analysis_type", "general")
            
            if not file_path:
                return {"status": "error", "error": "مسار الملف مطلوب"}
            
            # قراءة الملف
            file_info = self.file_processor.get_file_info(file_path)
            if not file_info["exists"]:
                return {"status": "error", "error": "الملف غير موجود"}
            
            # معالجة الملف
            file_content = self.file_processor.process_file(file_path, file_info["file_size"])
            
            if file_content["status"] == "error":
                return {"status": "error", "error": file_content["error"]}
            
            # تحليل المحتوى باستخدام Gemini
            if file_content["content"]:
                analysis_result = await self.gemini_client.analyze_text(
                    file_content["content"], 
                    analysis_type
                )
                
                # إضافة معلومات الملف للنتيجة
                analysis_result["file_info"] = file_info
                analysis_result["file_content"] = file_content
                
                return analysis_result
            else:
                return {"status": "error", "error": "لا يمكن قراءة محتوى الملف"}
                
        except Exception as e:
            logging.error(f"خطأ في تنفيذ مهمة تحليل الملف: {e}")
            return {"status": "error", "error": str(e)}
        finally:
            self.is_busy = False

class WebSearchAgent(Agent):
    """وكيل البحث في الويب"""
    
    def __init__(self, agent_id: str, gemini_client: GeminiClient, web_searcher: WebSearcher):
        super().__init__(agent_id, "web_searcher", "باحث الويب", 
                         ["web_search", "news_search", "academic_search", "local_search", "trending_search"])
        self.gemini_client = gemini_client
        self.web_searcher = web_searcher
    
    async def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """تنفيذ مهمة البحث"""
        try:
            self.is_busy = True
            self.update_activity()
            
            query = task_data.get("query")
            search_type = task_data.get("search_type", "web")
            max_results = task_data.get("max_results", 10)
            filters = task_data.get("filters", {})
            
            if not query:
                return {"status": "error", "error": "استعلام البحث مطلوب"}
            
            # تنفيذ البحث
            if search_type == "academic":
                search_results = await self.web_searcher.search_academic(query)
            elif search_type == "trending":
                category = task_data.get("category", "general")
                search_results = await self.web_searcher.search_trending_topics(category)
            elif search_type == "local":
                location = task_data.get("location", "")
                search_results = await self.web_searcher.search_local(query, location)
            elif search_type == "recent":
                days = task_data.get("days", 7)
                search_results = await self.web_searcher.search_recent(query, days)
            else:
                search_results = await self.web_searcher.search_web(query, max_results, search_type)
            
            if not search_results:
                return {"status": "success", "message": "لم يتم العثور على نتائج", "results": []}
            
            # معالجة النتائج باستخدام Gemini
            processed_results = await self.gemini_client.process_search_results(query, search_results)
            
            return processed_results
                
        except Exception as e:
            logging.error(f"خطأ في تنفيذ مهمة البحث: {e}")
            return {"status": "error", "error": str(e)}
        finally:
            self.is_busy = False

class ContentSummarizerAgent(Agent):
    """وكيل تلخيص المحتوى"""
    
    def __init__(self, agent_id: str, gemini_client: GeminiClient):
        super().__init__(agent_id, "content_summarizer", "ملخص المحتوى", 
                         ["text_summarization", "content_analysis", "key_points_extraction"])
        self.gemini_client = gemini_client
    
    async def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """تنفيذ مهمة التلخيص"""
        try:
            self.is_busy = True
            self.update_activity()
            
            content = task_data.get("content")
            summary_type = task_data.get("summary_type", "general")
            max_length = task_data.get("max_length", 500)
            
            if not content:
                return {"status": "error", "error": "المحتوى مطلوب"}
            
            # توليد الملخص
            summary = await self.gemini_client.summarize_content(content, max_length)
            
            # تحليل إضافي حسب النوع
            if summary_type == "key_points":
                analysis = await self.gemini_client.analyze_text(content, "summary")
                return {
                    "status": "success",
                    "summary": summary,
                    "key_points": analysis["analysis_result"],
                    "original_length": len(content),
                    "summary_length": len(summary)
                }
            else:
                return {
                    "status": "success",
                    "summary": summary,
                    "original_length": len(content),
                    "summary_length": len(summary)
                }
                
        except Exception as e:
            logging.error(f"خطأ في تنفيذ مهمة التلخيص: {e}")
            return {"status": "error", "error": str(e)}
        finally:
            self.is_busy = False

class FileGeneratorAgent(Agent):
    """وكيل إنشاء الملفات"""
    
    def __init__(self, agent_id: str, gemini_client: GeminiClient, file_processor: FileProcessor):
        super().__init__(agent_id, "file_generator", "منشئ الملفات", 
                         ["text_generation", "code_generation", "report_generation", "document_creation"])
        self.gemini_client = gemini_client
        self.file_processor = file_processor
    
    async def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """تنفيذ مهمة إنشاء الملف"""
        try:
            self.is_busy = True
            self.update_activity()
            
            file_type = task_data.get("file_type")
            content_description = task_data.get("content_description")
            file_name = task_data.get("file_name", f"generated_file_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            format_specs = task_data.get("format_specs", {})
            
            if not file_type or not content_description:
                return {"status": "error", "error": "نوع الملف ووصف المحتوى مطلوبان"}
            
            # توليد المحتوى باستخدام Gemini
            content = await self.gemini_client.generate_file_content(file_type, content_description, format_specs)
            
            if not content:
                return {"status": "error", "error": "فشل في توليد المحتوى"}
            
            # حفظ الملف
            output_path = self.file_processor.save_file(content, file_name, file_type)
            
            return {
                "status": "success",
                "file_path": output_path,
                "file_name": file_name,
                "file_type": file_type,
                "content_length": len(content),
                "generated_at": datetime.now().isoformat()
            }
                
        except Exception as e:
            logging.error(f"خطأ في تنفيذ مهمة إنشاء الملف: {e}")
            return {"status": "error", "error": str(e)}
        finally:
            self.is_busy = False

class TaskManagerAgent(Agent):
    """وكيل إدارة المهام"""
    
    def __init__(self, agent_id: str, gemini_client: GeminiClient, agents_manager):
        super().__init__(agent_id, "task_manager", "مدير المهام", 
                         ["task_planning", "task_coordination", "workflow_management", "resource_allocation"])
        self.gemini_client = gemini_client
        self.agents_manager = agents_manager
    
    async def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """تنفيذ مهمة إدارة المهام"""
        try:
            self.is_busy = True
            self.update_activity()
            
            task_description = task_data.get("task_description")
            task_type = task_data.get("task_type", "general")
            
            if not task_description:
                return {"status": "error", "error": "وصف المهمة مطلوب"}
            
            if task_type == "planning":
                # توليد خطة تنفيذ المهمة
                available_agents = self.agents_manager.get_available_agents()
                agent_names = [agent.agent_name for agent in available_agents]
                
                plan = await self.gemini_client.generate_task_plan(task_description, agent_names)
                return plan
                
            elif task_type == "coordination":
                # تنسيق المهام بين الوكلاء
                subtasks = task_data.get("subtasks", [])
                coordination_result = await self._coordinate_subtasks(subtasks)
                return coordination_result
                
            else:
                return {"status": "error", "error": f"نوع المهمة غير مدعوم: {task_type}"}
                
        except Exception as e:
            logging.error(f"خطأ في تنفيذ مهمة إدارة المهام: {e}")
            return {"status": "error", "error": str(e)}
        finally:
            self.is_busy = False
    
    async def _coordinate_subtasks(self, subtasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """تنسيق المهام الفرعية"""
        try:
            results = []
            for subtask in subtasks:
                agent_id = subtask.get("agent_id")
                agent = self.agents_manager.get_agent(agent_id)
                
                if agent:
                    result = await agent.execute_task(subtask)
                    results.append({
                        "subtask_id": subtask.get("subtask_id"),
                        "agent_id": agent_id,
                        "result": result
                    })
                else:
                    results.append({
                        "subtask_id": subtask.get("subtask_id"),
                        "agent_id": agent_id,
                        "result": {"status": "error", "error": "الوكيل غير موجود"}
                    })
            
            return {
                "status": "success",
                "subtasks_results": results,
                "total_subtasks": len(subtasks),
                "completed_subtasks": len([r for r in results if r["result"]["status"] == "success"])
            }
            
        except Exception as e:
            logging.error(f"خطأ في تنسيق المهام الفرعية: {e}")
            return {"status": "error", "error": str(e)}

class DataAnalyzerAgent(Agent):
    """وكيل تحليل البيانات"""
    
    def __init__(self, agent_id: str, gemini_client: GeminiClient):
        super().__init__(agent_id, "data_analyzer", "محلل البيانات", 
                         ["data_analysis", "statistical_analysis", "trend_analysis", "insight_generation"])
        self.gemini_client = gemini_client
    
    async def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """تنفيذ مهمة تحليل البيانات"""
        try:
            self.is_busy = True
            self.update_activity()
            
            data = task_data.get("data")
            analysis_type = task_data.get("analysis_type", "general")
            
            if not data:
                return {"status": "error", "error": "البيانات مطلوبة"}
            
            # تحليل البيانات باستخدام Gemini
            if analysis_type == "statistical":
                analysis_result = await self._perform_statistical_analysis(data)
            elif analysis_type == "trend":
                analysis_result = await self._perform_trend_analysis(data)
            else:
                analysis_result = await self.gemini_client.analyze_text(str(data), "technical")
            
            # توليد تقرير
            report = await self.gemini_client.generate_report(data, analysis_type)
            
            return {
                "status": "success",
                "analysis_result": analysis_result,
                "report": report,
                "data_summary": {
                    "data_type": type(data).__name__,
                    "data_size": len(str(data)),
                    "analysis_type": analysis_type
                }
            }
                
        except Exception as e:
            logging.error(f"خطأ في تنفيذ مهمة تحليل البيانات: {e}")
            return {"status": "error", "error": str(e)}
        finally:
            self.is_busy = False
    
    async def _perform_statistical_analysis(self, data: Any) -> str:
        """إجراء تحليل إحصائي"""
        try:
            prompt = f"""
            قم بإجراء تحليل إحصائي شامل للبيانات التالية:
            
            البيانات: {data}
            
            المطلوب:
            1. حساب الإحصائيات الأساسية (المتوسط، الوسيط، الانحراف المعياري)
            2. تحديد الأنماط والاتجاهات
            3. تحديد القيم الشاذة
            4. تقديم توصيات للتحليل
            
            التحليل الإحصائي:
            """
            
            return await self.gemini_client.generate_response(prompt)
            
        except Exception as e:
            logging.error(f"خطأ في التحليل الإحصائي: {e}")
            return f"خطأ في التحليل الإحصائي: {str(e)}"
    
    async def _perform_trend_analysis(self, data: Any) -> str:
        """إجراء تحليل الاتجاهات"""
        try:
            prompt = f"""
            قم بتحليل الاتجاهات والأنماط في البيانات التالية:
            
            البيانات: {data}
            
            المطلوب:
            1. تحديد الاتجاهات الرئيسية
            2. تحليل الأنماط الموسمية
            3. التنبؤ بالاتجاهات المستقبلية
            4. تحديد العوامل المؤثرة
            
            تحليل الاتجاهات:
            """
            
            return await self.gemini_client.generate_response(prompt)
            
        except Exception as e:
            logging.error(f"خطأ في تحليل الاتجاهات: {e}")
            return f"خطأ في تحليل الاتجاهات: {str(e)}"

class AgentsManager:
    """مدير الوكلاء الرئيسي"""
    
    def __init__(self, database_manager: DatabaseManager, gemini_client: GeminiClient):
        self.database_manager = database_manager
        self.gemini_client = gemini_client
        self.agents = {}
        self.agents_by_type = {}
        
        # إنشاء معالجات الملفات والبحث
        self.file_processor = FileProcessor()
        self.web_searcher = WebSearcher()
        
        # تهيئة الوكلاء
        self._initialize_agents()
    
    def _initialize_agents(self):
        """تهيئة الوكلاء"""
        try:
            # إنشاء الوكلاء
            agents_config = [
                {
                    "type": "file_analyzer",
                    "class": FileAnalysisAgent,
                    "args": [self.gemini_client, self.file_processor]
                },
                {
                    "type": "web_searcher",
                    "class": WebSearchAgent,
                    "args": [self.gemini_client, self.web_searcher]
                },
                {
                    "type": "content_summarizer",
                    "class": ContentSummarizerAgent,
                    "args": [self.gemini_client]
                },
                {
                    "type": "file_generator",
                    "class": FileGeneratorAgent,
                    "args": [self.gemini_client, self.file_processor]
                },
                {
                    "type": "task_manager",
                    "class": TaskManagerAgent,
                    "args": [self.gemini_client, self]
                },
                {
                    "type": "data_analyzer",
                    "class": DataAnalyzerAgent,
                    "args": [self.gemini_client]
                }
            ]
            
            for config_item in agents_config:
                agent_id = str(uuid.uuid4())
                agent_class = config_item["class"]
                agent_args = config_item["args"]
                
                agent = agent_class(agent_id, *agent_args)
                self.agents[agent_id] = agent
                
                if config_item["type"] not in self.agents_by_type:
                    self.agents_by_type[config_item["type"]] = []
                self.agents_by_type[config_item["type"]].append(agent)
            
            logging.info(f"تم تهيئة {len(self.agents)} وكيل بنجاح")
            
        except Exception as e:
            logging.error(f"خطأ في تهيئة الوكلاء: {e}")
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """الحصول على وكيل بواسطة المعرف"""
        return self.agents.get(agent_id)
    
    def get_agents_by_type(self, agent_type: str) -> List[Agent]:
        """الحصول على الوكلاء حسب النوع"""
        return self.agents_by_type.get(agent_type, [])
    
    def get_available_agents(self) -> List[Agent]:
        """الحصول على الوكلاء المتاحة"""
        return [agent for agent in self.agents.values() if agent.status == "active"]
    
    def get_busy_agents(self) -> List[Agent]:
        """الحصول على الوكلاء المشغولة"""
        return [agent for agent in self.agents.values() if agent.is_busy]
    
    async def execute_task_with_agent(self, agent_type: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """تنفيذ مهمة باستخدام وكيل من نوع معين"""
        try:
            agents = self.get_agents_by_type(agent_type)
            
            if not agents:
                return {"status": "error", "error": f"لا توجد وكلاء من النوع: {agent_type}"}
            
            # اختيار أول وكيل متاح
            available_agent = None
            for agent in agents:
                if not agent.is_busy and agent.status == "active":
                    available_agent = agent
                    break
            
            if not available_agent:
                return {"status": "error", "error": f"جميع الوكلاء من النوع {agent_type} مشغولة"}
            
            # تنفيذ المهمة
            result = await available_agent.execute_task(task_data)
            
            # تحديث قاعدة البيانات
            task_id = str(uuid.uuid4())
            self.database_manager.add_task(
                task_id, 
                task_data.get("user_id", 0),
                available_agent.agent_id,
                task_data.get("task_type", "general"),
                task_data
            )
            
            return result
            
        except Exception as e:
            logging.error(f"خطأ في تنفيذ المهمة مع الوكيل: {e}")
            return {"status": "error", "error": str(e)}
    
    async def execute_complex_task(self, task_description: str, user_id: int) -> Dict[str, Any]:
        """تنفيذ مهمة معقدة باستخدام عدة وكلاء"""
        try:
            # توليد خطة تنفيذ المهمة
            available_agents = self.get_available_agents()
            agent_names = [agent.agent_name for agent in available_agents]
            
            plan = await self.gemini_client.generate_task_plan(task_description, agent_names)
            
            if plan["status"] == "error":
                return plan
            
            # تنفيذ الخطة
            execution_results = []
            for step in plan["execution_plan"].split('\n'):
                if step.strip() and ':' in step:
                    step_description = step.split(':', 1)[1].strip()
                    
                    # تحديد الوكيل المناسب
                    agent = self._find_best_agent_for_task(step_description, available_agents)
                    
                    if agent:
                        step_result = await agent.execute_task({
                            "task_description": step_description,
                            "user_id": user_id,
                            "task_type": "step_execution"
                        })
                        
                        execution_results.append({
                            "step": step_description,
                            "agent": agent.agent_name,
                            "result": step_result
                        })
            
            return {
                "status": "success",
                "task_description": task_description,
                "execution_plan": plan["execution_plan"],
                "execution_results": execution_results,
                "summary": plan["summary"]
            }
            
        except Exception as e:
            logging.error(f"خطأ في تنفيذ المهمة المعقدة: {e}")
            return {"status": "error", "error": str(e)}
    
    def _find_best_agent_for_task(self, task_description: str, available_agents: List[Agent]) -> Optional[Agent]:
        """العثور على أفضل وكيل للمهمة"""
        try:
            best_agent = None
            best_score = 0
            
            for agent in available_agents:
                if agent.is_busy or agent.status != "active":
                    continue
                
                # حساب درجة المطابقة
                score = 0
                task_lower = task_description.lower()
                
                for capability in agent.capabilities:
                    if capability.lower() in task_lower:
                        score += 1
                
                if score > best_score:
                    best_score = score
                    best_agent = agent
            
            return best_agent
            
        except Exception as e:
            logging.error(f"خطأ في العثور على أفضل وكيل: {e}")
            return None
    
    def get_system_status(self) -> Dict[str, Any]:
        """الحصول على حالة النظام"""
        try:
            total_agents = len(self.agents)
            active_agents = len(self.get_available_agents())
            busy_agents = len(self.get_busy_agents())
            
            agents_status = {}
            for agent_type, agents in self.agents_by_type.items():
                agents_status[agent_type] = {
                    "total": len(agents),
                    "active": len([a for a in agents if a.status == "active"]),
                    "busy": len([a for a in agents if a.is_busy])
                }
            
            return {
                "total_agents": total_agents,
                "active_agents": active_agents,
                "busy_agents": busy_agents,
                "agents_by_type": agents_status,
                "system_health": "healthy" if active_agents > 0 else "degraded"
            }
            
        except Exception as e:
            logging.error(f"خطأ في الحصول على حالة النظام: {e}")
            return {"status": "error", "error": str(e)}