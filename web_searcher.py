# -*- coding: utf-8 -*-
"""
باحث الويب باستخدام DuckDuckGo
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from duckduckgo_search import DDGS
import config

class WebSearcher:
    """باحث الويب الرئيسي"""
    
    def __init__(self):
        """تهيئة باحث الويب"""
        self.max_results = config.DUCKDUCKGO_MAX_RESULTS
        self.timeout = config.SEARCH_TIMEOUT
        self.ddgs = DDGS()
    
    async def search_web(self, query: str, max_results: int = None, search_type: str = "web") -> List[Dict[str, Any]]:
        """البحث في الويب"""
        try:
            if max_results is None:
                max_results = self.max_results
            
            results = []
            
            # تحديد نوع البحث
            if search_type == "web":
                search_results = self.ddgs.text(query, max_results=max_results)
            elif search_type == "news":
                search_results = self.ddgs.news(query, max_results=max_results)
            elif search_type == "images":
                search_results = self.ddgs.images(query, max_results=max_results)
            elif search_type == "videos":
                search_results = self.ddgs.videos(query, max_results=max_results)
            else:
                search_results = self.ddgs.text(query, max_results=max_results)
            
            # معالجة النتائج
            for result in search_results:
                processed_result = {
                    "title": result.get("title", ""),
                    "link": result.get("link", ""),
                    "snippet": result.get("body", ""),
                    "source": result.get("source", ""),
                    "search_type": search_type
                }
                
                # إضافة معلومات إضافية حسب نوع البحث
                if search_type == "news":
                    processed_result["date"] = result.get("date", "")
                    processed_result["category"] = result.get("category", "")
                elif search_type == "images":
                    processed_result["image_url"] = result.get("image", "")
                    processed_result["width"] = result.get("width", "")
                    processed_result["height"] = result.get("height", "")
                elif search_type == "videos":
                    processed_result["duration"] = result.get("duration", "")
                    processed_result["thumbnail"] = result.get("thumbnail", "")
                
                results.append(processed_result)
            
            logging.info(f"تم العثور على {len(results)} نتيجة للبحث: {query}")
            return results
            
        except Exception as e:
            logging.error(f"خطأ في البحث في الويب: {e}")
            return []
    
    async def search_multiple_sources(self, query: str, sources: List[str] = None) -> Dict[str, List[Dict]]:
        """البحث في مصادر متعددة"""
        try:
            if sources is None:
                sources = ["web", "news"]
            
            all_results = {}
            
            for source in sources:
                try:
                    results = await self.search_web(query, search_type=source)
                    all_results[source] = results
                except Exception as e:
                    logging.warning(f"خطأ في البحث في المصدر {source}: {e}")
                    all_results[source] = []
            
            return all_results
            
        except Exception as e:
            logging.error(f"خطأ في البحث في المصادر المتعددة: {e}")
            return {}
    
    async def search_with_filters(self, query: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """البحث مع تطبيق فلاتر"""
        try:
            # تطبيق الفلاتر على النتائج
            results = await self.search_web(query, max_results=self.max_results * 2)
            
            filtered_results = []
            
            for result in results:
                # فلتر حسب الكلمات المفتاحية
                if "keywords" in filters:
                    keywords = filters["keywords"]
                    if not any(keyword.lower() in result["title"].lower() or 
                             keyword.lower() in result["snippet"].lower() 
                             for keyword in keywords):
                        continue
                
                # فلتر حسب المصدر
                if "sources" in filters:
                    sources = filters["sources"]
                    if not any(source.lower() in result["source"].lower() 
                             for source in sources):
                        continue
                
                # فلتر حسب التاريخ (للبحث في الأخبار)
                if "date_range" in filters and "date" in result:
                    # تطبيق فلتر التاريخ إذا كان متاحاً
                    pass
                
                filtered_results.append(result)
            
            # تحديد عدد النتائج المطلوبة
            max_results = filters.get("max_results", self.max_results)
            return filtered_results[:max_results]
            
        except Exception as e:
            logging.error(f"خطأ في البحث مع الفلاتر: {e}")
            return []
    
    async def search_trending_topics(self, category: str = "general") -> List[Dict[str, Any]]:
        """البحث عن المواضيع الرائجة"""
        try:
            trending_queries = {
                "general": ["أخبار اليوم", "أحداث مهمة", "تطورات حديثة"],
                "technology": ["تقنيات جديدة", "تطبيقات حديثة", "أخبار التكنولوجيا"],
                "business": ["أخبار الأعمال", "اقتصاد اليوم", "أسواق المال"],
                "sports": ["أخبار الرياضة", "مباريات اليوم", "نتائج الرياضة"]
            }
            
            queries = trending_queries.get(category, trending_queries["general"])
            all_results = []
            
            for query in queries:
                try:
                    results = await self.search_web(query, max_results=3, search_type="news")
                    all_results.extend(results)
                except Exception as e:
                    logging.warning(f"خطأ في البحث عن الموضوع الرائج {query}: {e}")
                    continue
            
            # إزالة التكرار
            unique_results = []
            seen_links = set()
            
            for result in all_results:
                if result["link"] not in seen_links:
                    unique_results.append(result)
                    seen_links.add(result["link"])
            
            return unique_results[:self.max_results]
            
        except Exception as e:
            logging.error(f"خطأ في البحث عن المواضيع الرائجة: {e}")
            return []
    
    async def search_academic(self, query: str) -> List[Dict[str, Any]]:
        """البحث الأكاديمي"""
        try:
            # إضافة كلمات مفتاحية أكاديمية
            academic_query = f"{query} research paper study analysis"
            
            results = await self.search_web(academic_query, max_results=self.max_results)
            
            # فلترة النتائج الأكاديمية
            academic_results = []
            academic_keywords = [
                "research", "study", "analysis", "paper", "journal", "academic",
                "university", "institute", "scientific", "methodology", "findings",
                "conclusion", "abstract", "introduction", "literature review"
            ]
            
            for result in results:
                title_lower = result["title"].lower()
                snippet_lower = result["snippet"].lower()
                
                # حساب درجة الأكاديمية
                academic_score = sum(1 for keyword in academic_keywords 
                                   if keyword in title_lower or keyword in snippet_lower)
                
                if academic_score >= 2:  # على الأقل كلمتين أكاديميتين
                    result["academic_score"] = academic_score
                    academic_results.append(result)
            
            # ترتيب حسب الدرجة الأكاديمية
            academic_results.sort(key=lambda x: x.get("academic_score", 0), reverse=True)
            
            return academic_results[:self.max_results]
            
        except Exception as e:
            logging.error(f"خطأ في البحث الأكاديمي: {e}")
            return []
    
    async def search_local(self, query: str, location: str) -> List[Dict[str, Any]]:
        """البحث المحلي"""
        try:
            # إضافة الموقع للاستعلام
            local_query = f"{query} {location}"
            
            results = await self.search_web(local_query, max_results=self.max_results)
            
            # فلترة النتائج المحلية
            local_results = []
            location_keywords = location.lower().split()
            
            for result in results:
                title_lower = result["title"].lower()
                snippet_lower = result["snippet"].lower()
                source_lower = result["source"].lower()
                
                # التحقق من وجود كلمات الموقع
                if any(loc in title_lower or loc in snippet_lower or loc in source_lower 
                       for loc in location_keywords):
                    result["local_relevance"] = True
                    local_results.append(result)
            
            return local_results[:self.max_results]
            
        except Exception as e:
            logging.error(f"خطأ في البحث المحلي: {e}")
            return []
    
    async def search_recent(self, query: str, days: int = 7) -> List[Dict[str, Any]]:
        """البحث في المحتوى الحديث"""
        try:
            # البحث في الأخبار للحصول على المحتوى الحديث
            results = await self.search_web(query, max_results=self.max_results * 2, search_type="news")
            
            # فلترة النتائج حسب التاريخ (إذا كان متاحاً)
            recent_results = []
            
            for result in results:
                if "date" in result and result["date"]:
                    # محاولة تحليل التاريخ
                    try:
                        # يمكن إضافة منطق أكثر تعقيداً لتحليل التواريخ
                        recent_results.append(result)
                    except:
                        recent_results.append(result)
                else:
                    # إذا لم يكن هناك تاريخ، نعتبره حديثاً
                    recent_results.append(result)
            
            return recent_results[:self.max_results]
            
        except Exception as e:
            logging.error(f"خطأ في البحث في المحتوى الحديث: {e}")
            return []
    
    def get_search_suggestions(self, query: str) -> List[str]:
        """الحصول على اقتراحات البحث"""
        try:
            # يمكن إضافة منطق لاقتراحات البحث
            suggestions = []
            
            # إضافة اقتراحات بسيطة
            if len(query) > 3:
                suggestions.append(query + " 2024")
                suggestions.append(query + " latest")
                suggestions.append(query + " guide")
                suggestions.append(query + " tutorial")
                suggestions.append(query + " examples")
            
            return suggestions[:5]
            
        except Exception as e:
            logging.error(f"خطأ في الحصول على اقتراحات البحث: {e}")
            return []
    
    async def search_with_context(self, query: str, context: str) -> List[Dict[str, Any]]:
        """البحث مع سياق إضافي"""
        try:
            # دمج السياق مع الاستعلام
            enhanced_query = f"{query} {context}"
            
            results = await self.search_web(enhanced_query, max_results=self.max_results)
            
            # إضافة السياق للنتائج
            for result in results:
                result["search_context"] = context
                result["enhanced_query"] = enhanced_query
            
            return results
            
        except Exception as e:
            logging.error(f"خطأ في البحث مع السياق: {e}")
            return []