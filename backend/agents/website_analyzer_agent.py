"""
Website Analyzer Agent
Comprehensive website analysis for SEO, performance, and optimization
"""

import os
import json
import asyncio
import aiohttp
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging
from urllib.parse import urljoin, urlparse
import re
from textstat import flesch_reading_ease, flesch_kincaid_grade
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class WebsiteAnalysisResult:
    """Data structure for website analysis results"""
    url: str
    analysis_date: datetime
    seo_score: int
    performance_score: int
    accessibility_score: int
    best_practices_score: int
    seo_analysis: Dict[str, Any]
    performance_analysis: Dict[str, Any]
    content_analysis: Dict[str, Any]
    technical_analysis: Dict[str, Any]
    recommendations: List[Dict[str, Any]]
    raw_data: Dict[str, Any]

class WebsiteAnalyzerAgent:
    """Agent for comprehensive website analysis"""
    
    def __init__(self):
        self.pagespeed_api_key = os.getenv("GOOGLE_PAGESPEED_API_KEY")
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if not self.pagespeed_api_key:
            logger.warning("GOOGLE_PAGESPEED_API_KEY not found. PageSpeed analysis will be limited.")
    
    async def analyze_website(self, url: str, user_id: str) -> WebsiteAnalysisResult:
        """Perform comprehensive website analysis"""
        try:
            logger.info(f"Starting website analysis for: {url}")
            
            # Validate URL
            if not self._is_valid_url(url):
                raise ValueError("Invalid URL format")
            
            # Check cache first
            cached_result = await self._get_cached_analysis(url)
            if cached_result and self._is_cache_valid(cached_result):
                logger.info("Returning cached analysis result")
                return cached_result
            
            # Perform analysis tasks in parallel
            tasks = [
                self._analyze_seo(url),
                self._analyze_performance(url),
                self._analyze_content(url),
                self._analyze_technical(url)
            ]
            
            seo_analysis, performance_analysis, content_analysis, technical_analysis = await asyncio.gather(*tasks)
            
            # Generate AI-powered recommendations from all analysis data
            recommendations = await self._generate_recommendations(seo_analysis, performance_analysis, content_analysis, technical_analysis)
            
            # Calculate overall scores from PageSpeed Insights
            seo_score = self._calculate_seo_score_from_pagespeed(performance_analysis)
            performance_score = self._calculate_performance_score(performance_analysis)
            accessibility_score = self._calculate_accessibility_score_from_pagespeed(performance_analysis)
            best_practices_score = self._calculate_best_practices_score_from_pagespeed(performance_analysis)
            
            # Create result object
            result = WebsiteAnalysisResult(
                url=url,
                analysis_date=datetime.now(),
                seo_score=seo_score,
                performance_score=performance_score,
                accessibility_score=accessibility_score,
                best_practices_score=best_practices_score,
                seo_analysis=seo_analysis,
                performance_analysis=performance_analysis,
                content_analysis=content_analysis,
                technical_analysis=technical_analysis,
                recommendations=recommendations,
                raw_data={
                    "seo": seo_analysis,
                    "performance": performance_analysis,
                    "content": content_analysis,
                    "technical": technical_analysis
                }
            )
            
            # Cache the result
            await self._cache_analysis_result(result, user_id)
            
            logger.info(f"Website analysis completed for: {url}")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing website {url}: {str(e)}")
            raise
    
    async def _analyze_seo(self, url: str) -> Dict[str, Any]:
        """Analyze SEO aspects of the website"""
        try:
            response = requests.get(url, timeout=30, headers={
                'User-Agent': 'Mozilla/5.0 (compatible; WebsiteAnalyzer/1.0)'
            })
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract meta information
            title = soup.find('title')
            title_text = title.get_text().strip() if title else ""
            
            meta_description = soup.find('meta', attrs={'name': 'description'})
            meta_description_text = meta_description.get('content', '') if meta_description else ""
            
            # Analyze headings structure
            headings = {
                'h1': [h.get_text().strip() for h in soup.find_all('h1')],
                'h2': [h.get_text().strip() for h in soup.find_all('h2')],
                'h3': [h.get_text().strip() for h in soup.find_all('h3')],
                'h4': [h.get_text().strip() for h in soup.find_all('h4')],
                'h5': [h.get_text().strip() for h in soup.find_all('h5')],
                'h6': [h.get_text().strip() for h in soup.find_all('h6')]
            }
            
            # Analyze images
            images = soup.find_all('img')
            images_with_alt = [img for img in images if img.get('alt')]
            images_without_alt = [img for img in images if not img.get('alt')]
            
            # Analyze links
            internal_links = []
            external_links = []
            broken_links = []
            
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.startswith('http'):
                    if urlparse(href).netloc == urlparse(url).netloc:
                        internal_links.append(href)
                    else:
                        external_links.append(href)
                elif href.startswith('/'):
                    internal_links.append(urljoin(url, href))
            
            # Check for schema markup
            schema_scripts = soup.find_all('script', type='application/ld+json')
            schema_markup = len(schema_scripts) > 0
            
            # Analyze meta tags
            meta_tags = {
                'viewport': soup.find('meta', attrs={'name': 'viewport'}) is not None,
                'robots': soup.find('meta', attrs={'name': 'robots'}) is not None,
                'canonical': soup.find('link', attrs={'rel': 'canonical'}) is not None,
                'og_title': soup.find('meta', attrs={'property': 'og:title'}) is not None,
                'og_description': soup.find('meta', attrs={'property': 'og:description'}) is not None,
                'twitter_card': soup.find('meta', attrs={'name': 'twitter:card'}) is not None
            }
            
            return {
                'title': {
                    'text': title_text,
                    'length': len(title_text),
                    'optimal': 50 <= len(title_text) <= 60
                },
                'meta_description': {
                    'text': meta_description_text,
                    'length': len(meta_description_text),
                    'optimal': 150 <= len(meta_description_text) <= 160
                },
                'headings': headings,
                'images': {
                    'total': len(images),
                    'with_alt': len(images_with_alt),
                    'without_alt': len(images_without_alt),
                    'alt_coverage': len(images_with_alt) / len(images) if images else 0
                },
                'links': {
                    'internal': len(internal_links),
                    'external': len(external_links),
                    'broken': len(broken_links)
                },
                'schema_markup': schema_markup,
                'meta_tags': meta_tags,
                'url_structure': {
                    'has_https': url.startswith('https://'),
                    'www_usage': 'www.' in url,
                    'url_length': len(url)
                }
            }
            
        except Exception as e:
            logger.error(f"Error in SEO analysis: {str(e)}")
            return {}
    
    async def _analyze_performance(self, url: str) -> Dict[str, Any]:
        """Analyze website performance using PageSpeed Insights API"""
        try:
            if not self.pagespeed_api_key:
                logger.warning("PageSpeed API key not configured")
                return {'error': 'PageSpeed API key not configured'}
            
            logger.info(f"Calling PageSpeed API for: {url}")
            # PageSpeed Insights API call
            pagespeed_url = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
            params = {
                'url': url,
                'key': self.pagespeed_api_key,
                'strategy': 'desktop',  # Analyze desktop performance
                'category': ['performance', 'accessibility', 'best-practices', 'seo']
            }
            
            logger.info(f"PageSpeed API URL: {pagespeed_url}")
            logger.info(f"PageSpeed API params: {params}")
            
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(pagespeed_url, params=params) as response:
                    logger.info(f"PageSpeed API response status: {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        logger.info("PageSpeed API call successful, parsing data...")
                        result = self._parse_pagespeed_data(data)
                        logger.info(f"Parsed PageSpeed data: {result}")
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(f"PageSpeed API error: {response.status} - {error_text}")
                        return {'error': f'PageSpeed API returned status {response.status}: {error_text}'}
                        
        except Exception as e:
            logger.error(f"Error in performance analysis: {str(e)}")
            return {'error': str(e)}
    
    def _parse_pagespeed_data(self, data: Dict) -> Dict[str, Any]:
        """Parse PageSpeed Insights API response"""
        try:
            lighthouse_result = data.get('lighthouseResult', {})
            categories = lighthouse_result.get('categories', {})
            audits = lighthouse_result.get('audits', {})
            
            # Extract scores
            scores = {}
            for category, details in categories.items():
                scores[category] = {
                    'score': details.get('score', 0),
                    'title': details.get('title', ''),
                    'description': details.get('description', '')
                }
            
            # Extract Core Web Vitals
            core_web_vitals = {}
            if 'first-contentful-paint' in audits:
                fcp = audits['first-contentful-paint']
                core_web_vitals['fcp'] = {
                    'value': fcp.get('numericValue', 0),
                    'score': fcp.get('score', 0),
                    'displayValue': fcp.get('displayValue', '')
                }
            
            if 'largest-contentful-paint' in audits:
                lcp = audits['largest-contentful-paint']
                core_web_vitals['lcp'] = {
                    'value': lcp.get('numericValue', 0),
                    'score': lcp.get('score', 0),
                    'displayValue': lcp.get('displayValue', '')
                }
            
            if 'cumulative-layout-shift' in audits:
                cls = audits['cumulative-layout-shift']
                core_web_vitals['cls'] = {
                    'value': cls.get('numericValue', 0),
                    'score': cls.get('score', 0),
                    'displayValue': cls.get('displayValue', '')
                }
            
            # Extract INP (Interaction to Next Paint)
            if 'interaction-to-next-paint' in audits:
                inp = audits['interaction-to-next-paint']
                core_web_vitals['inp'] = {
                    'value': inp.get('numericValue', 0),
                    'score': inp.get('score', 0),
                    'displayValue': inp.get('displayValue', '')
                }
            elif 'experimental-interaction-to-next-paint' in audits:
                inp = audits['experimental-interaction-to-next-paint']
                core_web_vitals['inp'] = {
                    'value': inp.get('numericValue', 0),
                    'score': inp.get('score', 0),
                    'displayValue': inp.get('displayValue', '')
                }
            
            # Extract opportunities and diagnostics
            opportunities = []
            diagnostics = []
            
            for audit_id, audit in audits.items():
                if audit.get('score') is not None and audit.get('score') < 0.9:
                    if audit.get('details', {}).get('type') == 'opportunity':
                        opportunities.append({
                            'id': audit_id,
                            'title': audit.get('title', ''),
                            'description': audit.get('description', ''),
                            'score': audit.get('score', 0),
                            'savings': audit.get('details', {}).get('overallSavingsMs', 0)
                        })
                    else:
                        diagnostics.append({
                            'id': audit_id,
                            'title': audit.get('title', ''),
                            'description': audit.get('description', ''),
                            'score': audit.get('score', 0)
                        })
            
            return {
                'scores': scores,
                'core_web_vitals': core_web_vitals,
                'opportunities': opportunities[:10],  # Top 10 opportunities
                'diagnostics': diagnostics[:10],  # Top 10 diagnostics
                'raw_data': data
            }
            
        except Exception as e:
            logger.error(f"Error parsing PageSpeed data: {str(e)}")
            return {'error': str(e)}
    
    async def _analyze_content(self, url: str) -> Dict[str, Any]:
        """Analyze content quality and structure"""
        try:
            response = requests.get(url, timeout=30, headers={
                'User-Agent': 'Mozilla/5.0 (compatible; WebsiteAnalyzer/1.0)'
            })
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract text content
            for script in soup(["script", "style"]):
                script.decompose()
            
            text = soup.get_text()
            words = text.split()
            word_count = len(words)
            
            # Calculate readability scores
            readability_score = flesch_reading_ease(text)
            grade_level = flesch_kincaid_grade(text)
            
            # Analyze content structure
            paragraphs = soup.find_all('p')
            paragraph_count = len(paragraphs)
            avg_paragraph_length = sum(len(p.get_text().split()) for p in paragraphs) / paragraph_count if paragraph_count > 0 else 0
            
            # Analyze keyword density (basic)
            text_lower = text.lower()
            common_words = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
            word_freq = {}
            for word in words:
                word_lower = word.lower().strip('.,!?;:"')
                if word_lower and word_lower not in common_words and len(word_lower) > 3:
                    word_freq[word_lower] = word_freq.get(word_lower, 0) + 1
            
            # Get top keywords
            top_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
            
            return {
                'word_count': word_count,
                'paragraph_count': paragraph_count,
                'avg_paragraph_length': round(avg_paragraph_length, 2),
                'readability': {
                    'flesch_score': round(readability_score, 2),
                    'grade_level': round(grade_level, 2),
                    'readability_level': self._get_readability_level(readability_score)
                },
                'keywords': {
                    'top_keywords': top_keywords,
                    'keyword_density': len(word_freq)
                },
                'content_structure': {
                    'has_intro': any('introduction' in p.get_text().lower() for p in paragraphs[:3]),
                    'has_conclusion': any('conclusion' in p.get_text().lower() for p in paragraphs[-3:]),
                    'has_subheadings': len(soup.find_all(['h2', 'h3', 'h4'])) > 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error in content analysis: {str(e)}")
            return {}
    
    async def _analyze_technical(self, url: str) -> Dict[str, Any]:
        """Analyze technical aspects of the website"""
        try:
            response = requests.get(url, timeout=30, headers={
                'User-Agent': 'Mozilla/5.0 (compatible; WebsiteAnalyzer/1.0)'
            })
            
            # Check SSL certificate
            ssl_info = {
                'has_ssl': url.startswith('https://'),
                'certificate_valid': True  # Simplified check
            }
            
            # Check response headers
            headers = response.headers
            security_headers = {
                'content_security_policy': 'content-security-policy' in headers,
                'x_frame_options': 'x-frame-options' in headers,
                'x_content_type_options': 'x-content-type-options' in headers,
                'strict_transport_security': 'strict-transport-security' in headers
            }
            
            # Check robots.txt
            robots_url = urljoin(url, '/robots.txt')
            try:
                robots_response = requests.get(robots_url, timeout=10)
                robots_txt = robots_response.text if robots_response.status_code == 200 else ""
            except:
                robots_txt = ""
            
            # Check sitemap
            sitemap_url = urljoin(url, '/sitemap.xml')
            sitemap_info = {
                'exists': False,
                'url': sitemap_url,
                'url_count': 0,
                'last_modified': None,
                'has_robots_reference': False
            }
            
            try:
                sitemap_response = requests.get(sitemap_url, timeout=10)
                if sitemap_response.status_code == 200:
                    sitemap_info['exists'] = True
                    # Parse sitemap XML
                    try:
                        soup = BeautifulSoup(sitemap_response.content, 'xml')
                        urls = soup.find_all('url')
                        sitemap_info['url_count'] = len(urls)
                        
                        # Get last modified dates
                        lastmods = [url.find('lastmod') for url in urls if url.find('lastmod')]
                        if lastmods:
                            # Get the most recent lastmod
                            dates = [lastmod.text for lastmod in lastmods if lastmod.text]
                            if dates:
                                sitemap_info['last_modified'] = max(dates)
                        
                        # Check if robots.txt references sitemap
                        if 'sitemap' in robots_txt.lower():
                            sitemap_info['has_robots_reference'] = True
                    except Exception as e:
                        logger.warning(f"Error parsing sitemap XML: {e}")
            except Exception as e:
                logger.debug(f"Sitemap not found: {e}")
            
            return {
                'ssl': ssl_info,
                'security_headers': security_headers,
                'response_time': response.elapsed.total_seconds(),
                'status_code': response.status_code,
                'content_type': headers.get('content-type', ''),
                'content_length': len(response.content),
                'robots_txt': {
                    'exists': bool(robots_txt),
                    'content': robots_txt[:500] if robots_txt else "",
                    'references_sitemap': 'sitemap' in robots_txt.lower() if robots_txt else False
                },
                'sitemap': sitemap_info,
                'server_info': {
                    'server': headers.get('server', ''),
                    'powered_by': headers.get('x-powered-by', '')
                }
            }
            
        except Exception as e:
            logger.error(f"Error in technical analysis: {str(e)}")
            return {}
    
    async def _generate_recommendations_from_pagespeed(self, performance_analysis: Dict) -> List[Dict[str, Any]]:
        """Generate 3 AI-powered recommendations based on PageSpeed Insights data only"""
        try:
            if 'error' in performance_analysis:
                return [{
                    'category': 'Performance',
                    'title': 'PageSpeed Analysis Unavailable',
                    'description': 'Unable to analyze website performance. Please check your PageSpeed API key configuration.',
                    'impact': 'High'
                }]
            
            if not self.openai_api_key:
                return self._generate_basic_recommendations_from_pagespeed(performance_analysis)
            
            # Extract PageSpeed data for recommendations
            scores = performance_analysis.get('scores', {})
            core_web_vitals = performance_analysis.get('core_web_vitals', {})
            
            # Prepare data for LLM
            pagespeed_data = {
                'scores': {
                    'performance': scores.get('performance', {}).get('score', 0),
                    'accessibility': scores.get('accessibility', {}).get('score', 0),
                    'best_practices': scores.get('best-practices', {}).get('score', 0),
                    'seo': scores.get('seo', {}).get('score', 0)
                },
                'core_web_vitals': {
                    'lcp': {
                        'value': core_web_vitals.get('lcp', {}).get('value', 0),
                        'score': core_web_vitals.get('lcp', {}).get('score', 0),
                        'displayValue': core_web_vitals.get('lcp', {}).get('displayValue', 'N/A')
                    },
                    'fcp': {
                        'value': core_web_vitals.get('fcp', {}).get('value', 0),
                        'score': core_web_vitals.get('fcp', {}).get('score', 0),
                        'displayValue': core_web_vitals.get('fcp', {}).get('displayValue', 'N/A')
                    },
                    'inp': {
                        'value': core_web_vitals.get('inp', {}).get('value', 0),
                        'score': core_web_vitals.get('inp', {}).get('score', 0),
                        'displayValue': core_web_vitals.get('inp', {}).get('displayValue', 'N/A')
                    },
                    'cls': {
                        'value': core_web_vitals.get('cls', {}).get('value', 0),
                        'score': core_web_vitals.get('cls', {}).get('score', 0),
                        'displayValue': core_web_vitals.get('cls', {}).get('displayValue', 'N/A')
                    }
                }
            }
            
            # Call OpenAI API for recommendations
            import openai
            from openai import AsyncOpenAI
            
            prompt = f"""
            Analyze this Google PageSpeed Insights data and provide exactly 3 actionable recommendations for improving the website's performance.
            
            Focus on the Core Web Vitals (LCP, FCP, INP, CLS) and the performance scores.
            
            Return as a JSON array with exactly 3 items in this format:
            [
                {{
                    "category": "Performance",
                    "title": "Short recommendation title",
                    "description": "Detailed explanation of the recommendation and how to implement it",
                    "impact": "High|Medium|Low"
                }}
            ]
            
            PageSpeed Insights Data:
            {json.dumps(pagespeed_data, indent=2)}
            
            Make sure to return exactly 3 recommendations focusing on the most critical issues based on the scores and Core Web Vitals values.
            """
            
            client = AsyncOpenAI(api_key=self.openai_api_key)
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.7
            )
            
            recommendations_text = response.choices[0].message.content.strip()
            
            # Try to extract JSON from markdown code blocks if present
            if recommendations_text.startswith('```'):
                import re
                json_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', recommendations_text, re.DOTALL)
                if json_match:
                    recommendations_text = json_match.group(1)
            
            recommendations = json.loads(recommendations_text)
            
            # Ensure exactly 3 recommendations
            if isinstance(recommendations, list):
                return recommendations[:3]
            else:
                return [recommendations] if recommendations else []
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing LLM recommendations JSON: {str(e)}")
            logger.error(f"LLM response: {recommendations_text if 'recommendations_text' in locals() else 'N/A'}")
            return self._generate_basic_recommendations_from_pagespeed(performance_analysis)
        except Exception as e:
            logger.error(f"Error generating AI recommendations: {str(e)}")
            return self._generate_basic_recommendations_from_pagespeed(performance_analysis)
    
    def _generate_basic_recommendations_from_pagespeed(self, performance_analysis: Dict) -> List[Dict[str, Any]]:
        """Generate basic recommendations from PageSpeed data without AI"""
        recommendations = []
        
        if 'error' in performance_analysis:
            return [{
                'category': 'Performance',
                'title': 'PageSpeed Analysis Unavailable',
                'description': 'Unable to analyze website performance.',
                'impact': 'High'
            }]
        
        scores = performance_analysis.get('scores', {})
        core_web_vitals = performance_analysis.get('core_web_vitals', {})
        
        # Check performance score
        perf_score = scores.get('performance', {}).get('score', 0)
        if perf_score < 0.7:
            recommendations.append({
                'category': 'Performance',
                'title': 'Improve Page Load Performance',
                'description': f'Your performance score is {int(perf_score * 100)}/100. Optimize images, minify CSS/JS, and enable caching to improve load times.',
                'impact': 'High'
            })
        
        # Check LCP
        lcp_value = core_web_vitals.get('lcp', {}).get('value', 0)
        if lcp_value > 2500:  # LCP should be under 2.5s
            recommendations.append({
                'category': 'Performance',
                'title': 'Optimize Largest Contentful Paint (LCP)',
                'description': f'Your LCP is {core_web_vitals.get("lcp", {}).get("displayValue", "high")}. Optimize images, use a CDN, and improve server response times.',
                'impact': 'High'
            })
        
        # Check CLS
        cls_value = core_web_vitals.get('cls', {}).get('value', 0)
        if cls_value > 0.1:  # CLS should be under 0.1
            recommendations.append({
                'category': 'Performance',
                'title': 'Reduce Cumulative Layout Shift (CLS)',
                'description': f'Your CLS is {core_web_vitals.get("cls", {}).get("displayValue", "high")}. Set size attributes on images and avoid inserting content above existing content.',
                'impact': 'Medium'
            })
        
        # Ensure we have exactly 3 recommendations
        while len(recommendations) < 3:
            recommendations.append({
                'category': 'Performance',
                'title': 'Continue Monitoring Performance',
                'description': 'Regularly monitor your website performance using PageSpeed Insights and address any new issues.',
                'impact': 'Low'
            })
        
        return recommendations[:3]
    
    async def _generate_recommendations(self, seo_analysis: Dict, performance_analysis: Dict, 
                                      content_analysis: Dict, technical_analysis: Dict) -> List[Dict[str, Any]]:
        """Generate 3 AI-powered recommendations based on all analysis data plus PageSpeed Core Web Vitals"""
        try:
            if not self.openai_api_key:
                return self._generate_basic_recommendations(seo_analysis, performance_analysis, content_analysis, technical_analysis)
            
            # Calculate current scores to identify areas needing improvement
            seo_score = self._calculate_seo_score_from_pagespeed(performance_analysis)
            performance_score = self._calculate_performance_score(performance_analysis)
            accessibility_score = self._calculate_accessibility_score_from_pagespeed(performance_analysis)
            best_practices_score = self._calculate_best_practices_score_from_pagespeed(performance_analysis)
            
            # Extract Core Web Vitals and Performance scores from PageSpeed
            scores = performance_analysis.get('scores', {})
            core_web_vitals = performance_analysis.get('core_web_vitals', {})
            
            # Identify areas that need improvement (scores < 90)
            areas_needing_improvement = []
            if seo_score < 90:
                areas_needing_improvement.append(('SEO', seo_score))
            if performance_score < 90:
                areas_needing_improvement.append(('Performance', performance_score))
            if accessibility_score < 90:
                areas_needing_improvement.append(('Accessibility', accessibility_score))
            if best_practices_score < 90:
                areas_needing_improvement.append(('Best Practices', best_practices_score))
            
            # Sort by score (lowest first) to prioritize worst areas
            areas_needing_improvement.sort(key=lambda x: x[1])
            
            # Prepare analysis summary for AI with all data plus PageSpeed metrics
            analysis_summary = {
                'current_scores': {
                    'seo': seo_score,
                    'performance': performance_score,
                    'accessibility': accessibility_score,
                    'best_practices': best_practices_score,
                    'overall': (seo_score + performance_score + accessibility_score + best_practices_score) // 4
                },
                'areas_needing_improvement': [area[0] for area in areas_needing_improvement],
                'seo': seo_analysis,
                'performance': performance_analysis,
                'content': content_analysis,
                'technical': technical_analysis,
                'pagespeed_scores': {
                    'performance': scores.get('performance', {}).get('score', 0),
                    'accessibility': scores.get('accessibility', {}).get('score', 0),
                    'best_practices': scores.get('best-practices', {}).get('score', 0),
                    'seo': scores.get('seo', {}).get('score', 0)
                },
                'core_web_vitals': {
                    'lcp': {
                        'value': core_web_vitals.get('lcp', {}).get('value', 0),
                        'score': core_web_vitals.get('lcp', {}).get('score', 0),
                        'displayValue': core_web_vitals.get('lcp', {}).get('displayValue', 'N/A')
                    },
                    'fcp': {
                        'value': core_web_vitals.get('fcp', {}).get('value', 0),
                        'score': core_web_vitals.get('fcp', {}).get('score', 0),
                        'displayValue': core_web_vitals.get('fcp', {}).get('displayValue', 'N/A')
                    },
                    'inp': {
                        'value': core_web_vitals.get('inp', {}).get('value', 0),
                        'score': core_web_vitals.get('inp', {}).get('score', 0),
                        'displayValue': core_web_vitals.get('inp', {}).get('displayValue', 'N/A')
                    },
                    'cls': {
                        'value': core_web_vitals.get('cls', {}).get('value', 0),
                        'score': core_web_vitals.get('cls', {}).get('score', 0),
                        'displayValue': core_web_vitals.get('cls', {}).get('displayValue', 'N/A')
                    }
                }
            }
            
            # Call OpenAI API for recommendations
            import openai
            from openai import AsyncOpenAI
            
            # Build focus areas message
            if not areas_needing_improvement:
                focus_message = "All areas are performing well (scores above 90). Provide general optimization recommendations to further improve the overall website score."
            else:
                focus_areas = ", ".join([f"{area[0]} ({area[1]}/100)" for area in areas_needing_improvement[:3]])
                focus_message = f"CRITICAL: Focus recommendations ONLY on these areas that need improvement: {focus_areas}. DO NOT provide recommendations for areas with scores of 90 or above."
            
            prompt = f"""
You are a helpful website improvement advisor. Analyze this website data and provide up to 3 actionable recommendations to improve the overall website score.

CRITICAL INSTRUCTIONS:
1. {focus_message}
2. Write in SIMPLE, PLAIN ENGLISH that anyone can understand - no technical jargon
3. Explain technical terms if you must use them (e.g., "images that load slowly" instead of "render-blocking resources")
4. Use everyday language - imagine explaining to a friend who doesn't know about websites
5. Keep descriptions complete but concise - users need to see the full text
6. Provide practical, step-by-step advice that non-technical people can follow
7. Maximum 3 recommendations - each must be UNIQUE and DIFFERENT from the others
8. Each recommendation must be specific and actionable - tell users EXACTLY what to do

Example of GOOD non-technical language:
- "Your website takes too long to load (Performance score: 75). Try making your images smaller before uploading them. You can use free tools like TinyPNG.com to compress images. Simply upload your image, download the compressed version, and replace the original on your website."
- "Your page is missing descriptions that help search engines understand your content (SEO score: 65). Add a description between 150-160 characters that explains what your page is about. You can add this in your website's settings or ask your web developer to add it."

Example of BAD technical language (DO NOT USE):
- "Optimize render-blocking resources and defer non-critical CSS"
- "Implement lazy loading for above-the-fold content"
- Generic advice like "Continue monitoring performance"

Current Website Scores:
- SEO: {seo_score}/100
- Performance: {performance_score}/100
- Accessibility: {accessibility_score}/100
- Best Practices: {best_practices_score}/100
- Overall: {(seo_score + performance_score + accessibility_score + best_practices_score) // 4}/100

Return as a JSON array with up to 3 UNIQUE items in this format:
[
    {{
        "category": "SEO|Performance|Accessibility|Best Practices|Content|Technical",
        "title": "Short, simple title (avoid technical terms)",
        "description": "Complete, specific explanation in plain English. Explain: 1) What the problem is, 2) Why it matters in simple terms, 3) EXACT step-by-step instructions on how to fix it. Be specific - tell users exactly what to do, where to go, or what tools to use. Make sure the description is complete and doesn't get cut off.",
        "impact": "High|Medium|Low"
    }}
]

IMPORTANT: 
- Each recommendation must be DIFFERENT and address a DIFFERENT issue
- Do NOT repeat the same recommendation
- Focus on areas with scores below 90
- Provide SPECIFIC, ACTIONABLE steps - not generic advice

Analysis data:
{json.dumps(analysis_summary, indent=2)}

Focus on the lowest scoring areas and provide practical, actionable advice that non-technical users can follow.
"""
            
            client = AsyncOpenAI(api_key=self.openai_api_key)
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.7
            )
            
            recommendations_text = response.choices[0].message.content.strip()
            
            # Try to extract JSON from markdown code blocks if present
            if recommendations_text.startswith('```'):
                import re
                json_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', recommendations_text, re.DOTALL)
                if json_match:
                    recommendations_text = json_match.group(1)
            
            recommendations = json.loads(recommendations_text)
            
            # Ensure up to 3 unique recommendations (can be less)
            if isinstance(recommendations, list):
                # Remove duplicates based on title
                seen_titles = set()
                unique_recommendations = []
                for rec in recommendations:
                    title = rec.get('title', '').lower().strip()
                    if title and title not in seen_titles:
                        seen_titles.add(title)
                        unique_recommendations.append(rec)
                    if len(unique_recommendations) >= 3:
                        break
                return unique_recommendations[:3]
            else:
                return [recommendations] if recommendations else []
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing LLM recommendations JSON: {str(e)}")
            logger.error(f"LLM response: {recommendations_text if 'recommendations_text' in locals() else 'N/A'}")
            return self._generate_basic_recommendations(seo_analysis, performance_analysis, content_analysis, technical_analysis)
        except Exception as e:
            logger.error(f"Error generating AI recommendations: {str(e)}")
            return self._generate_basic_recommendations(seo_analysis, performance_analysis, content_analysis, technical_analysis)
    
    def _generate_basic_recommendations(self, seo_analysis: Dict, performance_analysis: Dict, 
                                      content_analysis: Dict, technical_analysis: Dict) -> List[Dict[str, Any]]:
        """Generate basic recommendations without AI, focusing on lowest scoring areas"""
        recommendations = []
        
        # Calculate scores to identify areas needing improvement
        seo_score = self._calculate_seo_score_from_pagespeed(performance_analysis)
        performance_score = self._calculate_performance_score(performance_analysis)
        accessibility_score = self._calculate_accessibility_score_from_pagespeed(performance_analysis)
        best_practices_score = self._calculate_best_practices_score_from_pagespeed(performance_analysis)
        
        # Create list of scores with their categories
        score_list = [
            ('SEO', seo_score, seo_analysis),
            ('Performance', performance_score, performance_analysis),
            ('Accessibility', accessibility_score, technical_analysis),
            ('Best Practices', best_practices_score, technical_analysis)
        ]
        
        # Sort by score (lowest first) - only consider scores below 90
        score_list = [item for item in score_list if item[1] < 90]
        score_list.sort(key=lambda x: x[1])
        
        # Generate recommendations for lowest scoring areas only
        for category, score, analysis_data in score_list[:3]:
            if category == 'SEO' and score < 90:
                if seo_analysis.get('title', {}).get('length', 0) < 30:
                    recommendations.append({
                        'category': 'SEO',
                        'title': 'Improve Your Page Title',
                        'description': f'Your page title is too short (currently {seo_analysis.get("title", {}).get("length", 0)} characters). Add more descriptive words about what your page is about. Aim for 50-60 characters total. You can edit this in your website settings or content management system.',
                        'impact': 'High'
                    })
                elif not seo_analysis.get('meta_description', {}).get('text'):
                    recommendations.append({
                        'category': 'SEO',
                        'title': 'Add a Page Description',
                        'description': 'Your page is missing a description that helps search engines understand your content. Add a compelling description between 150-160 characters that explains what your page is about. You can add this in your website settings or ask your web developer to add it.',
                        'impact': 'High'
                    })
                elif seo_analysis.get('images', {}).get('alt_coverage', 1) < 0.8:
                    recommendations.append({
                        'category': 'SEO',
                        'title': 'Add Descriptions to Your Images',
                        'description': f'Some of your images are missing descriptions (alt text). This helps search engines understand your images and improves accessibility. Go through your images and add short descriptions of what each image shows. You can do this when uploading images or by editing existing images in your website editor.',
                        'impact': 'Medium'
                    })
            
            elif category == 'Performance' and score < 90:
                perf_score_value = performance_analysis.get('scores', {}).get('performance', {}).get('score', 0)
                lcp_value = performance_analysis.get('core_web_vitals', {}).get('lcp', {}).get('value', 0)
                
                if lcp_value > 2500:  # LCP should be under 2.5s
                    recommendations.append({
                        'category': 'Performance',
                        'title': 'Speed Up Your Website Loading',
                        'description': f'Your website takes too long to show the main content ({performance_analysis.get("core_web_vitals", {}).get("lcp", {}).get("displayValue", "too long")}). Make your images smaller before uploading them. Use free tools like TinyPNG.com or Squoosh.app to compress images. Simply upload your image, download the compressed version, and replace it on your website.',
                        'impact': 'High'
                    })
                elif perf_score_value < 0.7:
                    recommendations.append({
                        'category': 'Performance',
                        'title': 'Improve Your Website Speed',
                        'description': f'Your website is loading slowly (Performance score: {int(perf_score_value * 100)}/100). Make your images smaller using free tools like TinyPNG.com. Also, consider using a content delivery network (CDN) if you have many visitors. Contact your web hosting provider for help setting this up.',
                        'impact': 'High'
                    })
            
            elif category == 'Accessibility' and score < 90:
                recommendations.append({
                    'category': 'Accessibility',
                    'title': 'Improve Website Accessibility',
                    'description': f'Your website accessibility score is {accessibility_score}/100. Add descriptions (alt text) to all images, ensure text has good contrast with backgrounds, and make sure all buttons and links are clearly labeled. This helps people with disabilities use your website and improves your search rankings.',
                    'impact': 'Medium'
                })
            
            elif category == 'Best Practices' and score < 90:
                if not technical_analysis.get('ssl', {}).get('has_ssl', False):
                    recommendations.append({
                        'category': 'Best Practices',
                        'title': 'Enable Secure Connection (HTTPS)',
                        'description': 'Your website is not using a secure connection (HTTPS). This is important for protecting visitor information and improving search rankings. Contact your web hosting provider to enable SSL/HTTPS - most hosting providers offer this for free.',
                        'impact': 'High'
                    })
                else:
                    recommendations.append({
                        'category': 'Best Practices',
                        'title': 'Improve Website Security',
                        'description': f'Your website security practices score is {best_practices_score}/100. Ensure your website has proper security headers and keep all software updated. Contact your web developer or hosting provider for assistance with security improvements.',
                        'impact': 'Medium'
                    })
            
            if len(recommendations) >= 3:
                break
        
        # Return unique recommendations (max 3)
        return recommendations[:3]
    
    def _calculate_seo_score(self, seo_analysis: Dict) -> int:
        """Calculate SEO score (0-100)"""
        score = 0
        
        # Title optimization (20 points)
        if seo_analysis.get('title', {}).get('optimal', False):
            score += 20
        elif seo_analysis.get('title', {}).get('length', 0) > 0:
            score += 10
        
        # Meta description (20 points)
        if seo_analysis.get('meta_description', {}).get('optimal', False):
            score += 20
        elif seo_analysis.get('meta_description', {}).get('length', 0) > 0:
            score += 10
        
        # Image alt texts (20 points)
        alt_coverage = seo_analysis.get('images', {}).get('alt_coverage', 0)
        score += int(alt_coverage * 20)
        
        # Schema markup (20 points)
        if seo_analysis.get('schema_markup', False):
            score += 20
        
        # Meta tags (20 points)
        meta_tags = seo_analysis.get('meta_tags', {})
        meta_score = sum(1 for tag in meta_tags.values() if tag)
        score += int((meta_score / len(meta_tags)) * 20) if meta_tags else 0
        
        return min(score, 100)
    
    def _calculate_performance_score(self, performance_analysis: Dict) -> int:
        """Calculate performance score (0-100) from PageSpeed Insights"""
        if 'error' in performance_analysis:
            return 0
        
        scores = performance_analysis.get('scores', {})
        performance_score = scores.get('performance', {}).get('score', 0)
        return int(performance_score * 100)
    
    def _calculate_seo_score_from_pagespeed(self, performance_analysis: Dict) -> int:
        """Calculate SEO score (0-100) from PageSpeed Insights"""
        if 'error' in performance_analysis:
            return 0
        
        scores = performance_analysis.get('scores', {})
        seo_score = scores.get('seo', {}).get('score', 0)
        return int(seo_score * 100)
    
    def _calculate_accessibility_score_from_pagespeed(self, performance_analysis: Dict) -> int:
        """Calculate accessibility score (0-100) from PageSpeed Insights"""
        if 'error' in performance_analysis:
            return 0
        
        scores = performance_analysis.get('scores', {})
        accessibility_score = scores.get('accessibility', {}).get('score', 0)
        return int(accessibility_score * 100)
    
    def _calculate_best_practices_score_from_pagespeed(self, performance_analysis: Dict) -> int:
        """Calculate best practices score (0-100) from PageSpeed Insights"""
        if 'error' in performance_analysis:
            return 0
        
        scores = performance_analysis.get('scores', {})
        best_practices_score = scores.get('best-practices', {}).get('score', 0)
        return int(best_practices_score * 100)
    
    def _calculate_accessibility_score(self, technical_analysis: Dict) -> int:
        """Calculate accessibility score (0-100)"""
        # This would be enhanced with actual accessibility testing
        score = 0
        
        # Basic checks
        if technical_analysis.get('ssl', {}).get('has_ssl', False):
            score += 20
        
        security_headers = technical_analysis.get('security_headers', {})
        security_score = sum(1 for header in security_headers.values() if header)
        score += int((security_score / len(security_headers)) * 30) if security_headers else 0
        
        return min(score, 100)
    
    def _calculate_best_practices_score(self, technical_analysis: Dict) -> int:
        """Calculate best practices score (0-100)"""
        score = 0
        
        # SSL (30 points)
        if technical_analysis.get('ssl', {}).get('has_ssl', False):
            score += 30
        
        # Security headers (40 points)
        security_headers = technical_analysis.get('security_headers', {})
        security_score = sum(1 for header in security_headers.values() if header)
        score += int((security_score / len(security_headers)) * 40) if security_headers else 0
        
        # Sitemap (15 points)
        if technical_analysis.get('sitemap', {}).get('exists', False):
            score += 15
        
        # Robots.txt (15 points)
        if technical_analysis.get('robots_txt', {}).get('exists', False):
            score += 15
        
        return min(score, 100)
    
    def _is_valid_url(self, url: str) -> bool:
        """Validate URL format"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def _get_readability_level(self, flesch_score: float) -> str:
        """Convert Flesch score to readability level"""
        if flesch_score >= 90:
            return "Very Easy"
        elif flesch_score >= 80:
            return "Easy"
        elif flesch_score >= 70:
            return "Fairly Easy"
        elif flesch_score >= 60:
            return "Standard"
        elif flesch_score >= 50:
            return "Fairly Difficult"
        elif flesch_score >= 30:
            return "Difficult"
        else:
            return "Very Difficult"
    
    async def _get_cached_analysis(self, url: str) -> Optional[WebsiteAnalysisResult]:
        """Get cached analysis result"""
        # Implementation would check database for recent analysis
        return None
    
    def _is_cache_valid(self, result: WebsiteAnalysisResult) -> bool:
        """Check if cached result is still valid (24 hours)"""
        if not result:
            return False
        
        time_diff = datetime.now() - result.analysis_date
        return time_diff.total_seconds() < 86400  # 24 hours
    
    async def _cache_analysis_result(self, result: WebsiteAnalysisResult, user_id: str):
        """Cache analysis result in database"""
        # Implementation would save to database
        pass
