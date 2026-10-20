"""
Curated 30 Real-World Target Websites for PS-027 Empirical Study
Categorized across 6 critical infrastructure and digital economy sectors.
"""

from typing import List, Dict, Any

BENCHMARK_TARGETS: List[Dict[str, Any]] = [
    # 1. Government & Public Services
    {"id": "gov_1", "name": "National Portal of India", "url": "https://india.gov.in", "sector": "Government & Public Services"},
    {"id": "gov_2", "name": "Digital India", "url": "https://digitalindia.gov.in", "sector": "Government & Public Services"},
    {"id": "gov_3", "name": "IRCTC Official Portal", "url": "https://irctc.co.in", "sector": "Government & Public Services"},
    {"id": "gov_4", "name": "UIDAI (Aadhaar)", "url": "https://uidai.gov.in", "sector": "Government & Public Services"},
    {"id": "gov_5", "name": "Ministry of Electronics & IT", "url": "https://meity.gov.in", "sector": "Government & Public Services"},

    # 2. E-Commerce & Retail
    {"id": "ecom_1", "name": "Amazon India", "url": "https://amazon.in", "sector": "E-Commerce & Retail"},
    {"id": "ecom_2", "name": "Flipkart", "url": "https://flipkart.com", "sector": "E-Commerce & Retail"},
    {"id": "ecom_3", "name": "Myntra", "url": "https://myntra.com", "sector": "E-Commerce & Retail"},
    {"id": "ecom_4", "name": "Meesho", "url": "https://meesho.com", "sector": "E-Commerce & Retail"},
    {"id": "ecom_5", "name": "Ajio", "url": "https://ajio.com", "sector": "E-Commerce & Retail"},

    # 3. News & Media
    {"id": "news_1", "name": "The Hindu", "url": "https://thehindu.com", "sector": "News & Media"},
    {"id": "news_2", "name": "Times of India", "url": "https://timesofindia.indiatimes.com", "sector": "News & Media"},
    {"id": "news_3", "name": "NDTV", "url": "https://ndtv.com", "sector": "News & Media"},
    {"id": "news_4", "name": "The Indian Express", "url": "https://indianexpress.com", "sector": "News & Media"},
    {"id": "news_5", "name": "BBC News", "url": "https://bbc.com", "sector": "News & Media"},

    # 4. Higher Education & Research
    {"id": "edu_1", "name": "IIT Delhi", "url": "https://iitd.ac.in", "sector": "Higher Education & Research"},
    {"id": "edu_2", "name": "IIT Bombay", "url": "https://iitb.ac.in", "sector": "Higher Education & Research"},
    {"id": "edu_3", "name": "IISc Bengaluru", "url": "https://iisc.ac.in", "sector": "Higher Education & Research"},
    {"id": "edu_4", "name": "AIORI Portal", "url": "https://aiori.in", "sector": "Higher Education & Research"},
    {"id": "edu_5", "name": "NPTEL", "url": "https://nptel.ac.in", "sector": "Higher Education & Research"},

    # 5. SaaS, Cloud & Big Tech
    {"id": "tech_1", "name": "Google", "url": "https://google.com", "sector": "SaaS, Cloud & Big Tech"},
    {"id": "tech_2", "name": "GitHub", "url": "https://github.com", "sector": "SaaS, Cloud & Big Tech"},
    {"id": "tech_3", "name": "Wikipedia", "url": "https://wikipedia.org", "sector": "SaaS, Cloud & Big Tech"},
    {"id": "tech_4", "name": "Microsoft", "url": "https://microsoft.com", "sector": "SaaS, Cloud & Big Tech"},
    {"id": "tech_5", "name": "Cloudflare", "url": "https://cloudflare.com", "sector": "SaaS, Cloud & Big Tech"},

    # 6. Banking & Financial Core
    {"id": "fin_1", "name": "State Bank of India", "url": "https://sbi.co.in", "sector": "Banking & Financial Core"},
    {"id": "fin_2", "name": "HDFC Bank", "url": "https://hdfcbank.com", "sector": "Banking & Financial Core"},
    {"id": "fin_3", "name": "ICICI Bank", "url": "https://icicibank.com", "sector": "Banking & Financial Core"},
    {"id": "fin_4", "name": "Reserve Bank of India", "url": "https://rbi.org.in", "sector": "Banking & Financial Core"},
    {"id": "fin_5", "name": "NPCI (Unified Payments / UPI)", "url": "https://npci.org.in", "sector": "Banking & Financial Core"},
]
