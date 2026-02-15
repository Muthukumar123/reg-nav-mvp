"""
Analytics Module for Regulation Navigator

Tracks usage metrics, query patterns, and system performance.
"""

from datetime import datetime, timedelta
from typing import Dict, List
import time

class Analytics:
    """Track application metrics and analytics."""
    
    def __init__(self):
        self.total_queries = 0
        self.total_logins = 0
        self.successful_queries = 0
        self.failed_queries = 0
        self.query_times = []  # Track response times
        self.query_keywords = {}  # Track common keywords
        self.regulations_accessed = {}  # Track which regulations are queried
        self.languages_used = {}  # Track language usage
        self.start_time = datetime.now()
    
    def track_query(self, question: str, response_time: float, success: bool, regulations_used: List[str] = None):
        """Track a query with its metadata."""
        self.total_queries += 1
        
        if success:
            self.successful_queries += 1
        else:
            self.failed_queries += 1
        
        self.query_times.append({
            'timestamp': datetime.now(),
            'time_ms': response_time * 1000,
            'question': question[:50]  # Store first 50 chars
        })
        
        # Keep only last 1000 queries
        if len(self.query_times) > 1000:
            self.query_times = self.query_times[-1000:]
        
        # Track keywords
        words = question.lower().split()
        for word in words:
            if len(word) > 3 and word not in ['what', 'that', 'with', 'this', 'from', 'have', 'when', 'does', 'about']:
                self.query_keywords[word] = self.query_keywords.get(word, 0) + 1
        
        # Track regulations
        if regulations_used:
            for reg in regulations_used:
                doc_name = reg.split('|')[0].strip() if '|' in reg else reg
                self.regulations_accessed[doc_name] = self.regulations_accessed.get(doc_name, 0) + 1
    
    def track_login(self, username: str, language: str = "en"):
        """Track user login and language preference."""
        self.total_logins += 1
        self.languages_used[language] = self.languages_used.get(language, 0) + 1
    
    def get_stats(self) -> Dict:
        """Get current analytics stats."""
        avg_response_time = sum(q['time_ms'] for q in self.query_times) / len(self.query_times) if self.query_times else 0
        uptime_seconds = (datetime.now() - self.start_time).total_seconds()
        uptime_hours = uptime_seconds / 3600
        
        # Get top keywords
        top_keywords = sorted(self.query_keywords.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Get top regulations
        top_regulations = sorted(self.regulations_accessed.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # EU Regulatory Statistics
        total_articles = 50  # Total articles in database
        eu_directives = {
            "AML (2015/849)": self.regulations_accessed.get("EU Directive 2015/849", 0),
            "GDPR (2016/679)": self.regulations_accessed.get("Regulation (EU) 2016/679", 0),
            "PSD2 (2015/2366)": self.regulations_accessed.get("Directive (EU) 2015/2366", 0),
            "MiFID II (2014/65/EU)": self.regulations_accessed.get("Directive 2014/65/EU", 0),
            "Crypto/MiCA (2023/1114)": self.regulations_accessed.get("EU Regulation 2023/1114", 0),
            "DORA (2026/2408)": self.regulations_accessed.get("EU Directive 2026/2408", 0),
        }
        
        success_rate = (self.successful_queries / self.total_queries * 100) if self.total_queries > 0 else 0
        
        return {
            "total_queries": self.total_queries,
            "successful_queries": self.successful_queries,
            "failed_queries": self.failed_queries,
            "success_rate": round(success_rate, 2),
            "total_logins": self.total_logins,
            "avg_response_time_ms": round(avg_response_time, 2),
            "uptime_hours": round(uptime_hours, 2),
            "uptime_formatted": self._format_uptime(uptime_seconds),
            "top_keywords": [{"keyword": k, "count": v} for k, v in top_keywords],
            "top_regulations": [{"regulation": k, "queries": v} for k, v in top_regulations],
            "eu_regulatory_coverage": eu_directives,
            "total_articles_in_db": total_articles,
            "languages_used": self.languages_used,
            "coverage_years": "2005-2026",
            "latest_regulations": ["MiCA 2023", "DORA 2026", "Net-Zero 2024", "Cybersecurity 2025"],
            "query_distribution": self._get_query_distribution(),
        }
    
    def _get_query_distribution(self) -> Dict:
        """Get time-based query distribution."""
        now = datetime.now()
        last_hour = [q for q in self.query_times if (now - q['timestamp']).total_seconds() < 3600]
        last_day = [q for q in self.query_times if (now - q['timestamp']).total_seconds() < 86400]
        
        return {
            "last_hour": len(last_hour),
            "last_day": len(last_day),
            "total": len(self.query_times),
        }
    
    def _format_uptime(self, seconds: float) -> str:
        """Format uptime in human-readable format."""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"

# Global analytics instance
analytics = Analytics()
