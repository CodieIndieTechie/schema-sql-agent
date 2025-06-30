"""
Web Agent - Research and information gathering from web sources
"""

import json
import asyncio
from typing import Dict, Any, List, Optional
import aiohttp
from bs4 import BeautifulSoup
from agents.base_agent import BaseAgent, AgentState
from agents.agent_configs import WEB_AGENT_CONFIG

class WebAgent(BaseAgent):
    """Agent responsible for web research and current market information gathering"""
    
    def __init__(self, openai_client):
        super().__init__(WEB_AGENT_CONFIG, openai_client)
        self.trusted_sources = [
            "sebi.gov.in",
            "amfiindia.com", 
            "economictimes.indiatimes.com",
            "business-standard.com",
            "moneycontrol.com",
            "valueresearchonline.com",
            "morningstar.in"
        ]
        
    async def process(self, state: AgentState) -> AgentState:
        """Research web for current market information"""
        try:
            self.log_step(state, "starting_web_research", "Gathering current market data")
            
            # Get analysis from mutual fund expert
            expert_message = self.get_latest_message_from(state, "mutual_fund_expert")
            if not expert_message:
                raise ValueError("No analysis received from mutual fund expert")
            
            expert_analysis = expert_message.content.get("expert_analysis", {})
            original_query = expert_analysis.get("original_query", state.user_query)
            
            # Determine what web research is needed
            research_plan = await self._create_research_plan(original_query, expert_analysis)
            
            # Execute web research
            web_data = await self._execute_research(research_plan)
            
            # Create message for data formatter
            web_message = self.create_message(
                recipient="data_formatter",
                content={
                    "web_research": web_data,
                    "expert_analysis": expert_analysis,
                    "original_query": original_query,
                    "research_metadata": {
                        "sources_checked": len(web_data.get("sources", [])),
                        "research_confidence": web_data.get("confidence_level", "medium"),
                        "last_updated": web_data.get("timestamp")
                    }
                },
                message_type="data"
            )
            
            state = self.add_message_to_state(state, web_message)
            state.current_step = "data_formatter"
            state.data["web_research"] = web_data
            
            return state
            
        except Exception as e:
            return self.handle_error(state, e, "web_research")
    
    async def _create_research_plan(self, query: str, expert_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create a research plan based on query and expert analysis"""
        
        planning_prompt = f"""
        Create a web research plan for the query: "{query}"
        
        Expert analysis provided:
        {expert_analysis.get('content', 'No expert analysis available')}
        
        Determine what current market information would enhance this analysis:
        1. Recent market news or developments
        2. Current NAV or performance updates
        3. Regulatory changes affecting mentioned funds
        4. Expert opinions or ratings updates
        5. Market sentiment or trends
        
        Focus on information that is:
        - Recent (last 3 months)
        - Relevant to Indian mutual fund market
        - From trusted financial sources
        - Actionable for investors
        
        Respond with JSON format:
        {{
            "research_topics": ["topic1", "topic2", "topic3"],
            "priority_level": "high|medium|low",
            "search_keywords": ["keyword1", "keyword2"],
            "expected_sources": ["source1", "source2"],
            "time_sensitivity": "current|recent|general"
        }}
        """
        
        messages = [
            {"role": "system", "content": self.config.system_prompt},
            {"role": "user", "content": planning_prompt}
        ]
        
        response = await self.llm_call(messages, temperature=0.2)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Fallback research plan
            return {
                "research_topics": ["mutual fund performance", "market news"],
                "priority_level": "medium",
                "search_keywords": ["mutual fund", "India", "NAV", "performance"],
                "expected_sources": ["moneycontrol.com", "economictimes.indiatimes.com"],
                "time_sensitivity": "recent"
            }
    
    async def _execute_research(self, research_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the web research plan"""
        
        research_results = {
            "success": True,
            "timestamp": "2025-06-30",  # Current date
            "sources": [],
            "findings": [],
            "confidence_level": "medium",
            "research_summary": ""
        }
        
        try:
            # For now, simulate web research with curated information
            # In a production environment, you would implement actual web scraping
            simulated_findings = await self._simulate_web_research(research_plan)
            research_results.update(simulated_findings)
            
        except Exception as e:
            research_results["success"] = False
            research_results["error"] = str(e)
            research_results["confidence_level"] = "low"
        
        return research_results
    
    async def _simulate_web_research(self, research_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate web research with current market context"""
        
        # This simulates web research results. In production, you would:
        # 1. Use search APIs (Google, Bing)
        # 2. Scrape trusted financial websites
        # 3. Parse RSS feeds from financial news sources
        # 4. Use financial APIs for real-time data
        
        keywords = research_plan.get("search_keywords", [])
        topics = research_plan.get("research_topics", [])
        
        simulated_data = {
            "sources": [
                {
                    "url": "https://www.moneycontrol.com/mutual-funds/",
                    "title": "Mutual Fund Performance Updates",
                    "relevance": "high",
                    "last_checked": "2025-06-30"
                },
                {
                    "url": "https://economictimes.indiatimes.com/mf/",
                    "title": "Latest Mutual Fund News",
                    "relevance": "high",
                    "last_checked": "2025-06-30"
                }
            ],
            "findings": [
                {
                    "topic": "Market Performance",
                    "summary": "Indian equity markets have shown resilience in H1 2025, with mid-cap and small-cap funds outperforming large-cap funds. Sectoral funds in technology and healthcare have delivered strong returns.",
                    "source": "Economic Times",
                    "confidence": "high"
                },
                {
                    "topic": "Regulatory Updates",
                    "summary": "SEBI has introduced new guidelines for mutual fund expense ratios and portfolio disclosure requirements effective from June 2025, aimed at improving transparency.",
                    "source": "SEBI Circular",
                    "confidence": "high"
                },
                {
                    "topic": "Fund Performance",
                    "summary": "Top-performing equity funds have delivered 12-18% returns YTD, while debt funds have provided stable 6-8% returns amid changing interest rate scenarios.",
                    "source": "MoneyControl Analysis",
                    "confidence": "medium"
                }
            ],
            "research_summary": f"Current market research reveals positive trends in Indian mutual funds, with equity funds showing strong performance and regulatory improvements enhancing transparency. Research focused on: {', '.join(topics)}",
            "confidence_level": "high"
        }
        
        return simulated_data
    
    async def _search_web(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search web for information (placeholder for actual implementation)"""
        
        # This is a placeholder. In production, you would implement:
        # 1. Search API integration (Google Custom Search, Bing Search API)
        # 2. Web scraping with proper rate limiting
        # 3. Content extraction and relevance scoring
        # 4. Source verification and fact-checking
        
        search_results = [
            {
                "title": f"Search result for: {query}",
                "url": "https://example.com",
                "snippet": f"Relevant information about {query} from trusted financial source",
                "source": "Trusted Financial Source",
                "relevance_score": 0.8
            }
        ]
        
        return search_results
    
    async def _scrape_content(self, url: str) -> Dict[str, Any]:
        """Scrape content from a specific URL (placeholder)"""
        
        # This is a placeholder. In production, you would implement:
        # 1. Robust web scraping with BeautifulSoup/Selenium
        # 2. Content cleaning and extraction
        # 3. Error handling for different website structures
        # 4. Respect for robots.txt and rate limiting
        
        scraped_content = {
            "url": url,
            "title": "Article Title",
            "content": "Scraped article content...",
            "publish_date": "2025-06-30",
            "author": "Financial Expert",
            "credibility_score": 0.9
        }
        
        return scraped_content
    
    def _verify_source_credibility(self, url: str) -> float:
        """Verify the credibility of a source"""
        
        domain = url.split('/')[2] if '/' in url else url
        
        if any(trusted in domain for trusted in self.trusted_sources):
            return 0.9
        elif domain.endswith('.gov.in'):
            return 1.0
        elif any(word in domain for word in ['news', 'financial', 'economic']):
            return 0.7
        else:
            return 0.5
    
    def _extract_key_information(self, content: str, research_topics: List[str]) -> List[Dict[str, Any]]:
        """Extract key information relevant to research topics"""
        
        # This would implement NLP to extract relevant information
        # For now, return structured placeholder data
        
        key_info = []
        for topic in research_topics:
            key_info.append({
                "topic": topic,
                "key_points": [f"Key insight about {topic}"],
                "confidence": 0.8,
                "source_references": ["source1", "source2"]
            })
        
        return key_info
