import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Tuple
from urllib.parse import urlparse, unquote
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
class WikiScraper:
    def __init__(self, url: str):
        self.url = url
        self.soup = None
        self.title = None
        self.raw_html = None
        
    def validate_url(self) -> bool:
        """Validate if URL is a valid Wikipedia article"""
        try:
            parsed = urlparse(self.url)
            return "wikipedia.org" in parsed.netloc
        except Exception as e:
            logger.error(f"URL validation error: {e}")
            return False
    
    def fetch_content(self) -> bool:
        """Fetch and parse Wikipedia article"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.'
            }
            response = requests.get(self.url, headers=headers, timeout=10)
            response.raise_for_status()
            
            self.raw_html = response.text
            self.soup = BeautifulSoup(response.content, 'html.parser')
            return True
        except requests.RequestException as e:
            logger.error(f"Failed to fetch URL: {e}")
            return False
    
    def get_title(self) -> str:
        """Extract article title"""
        if self.soup:
            title_elem = self.soup.find(id="firstHeading")
            if title_elem:
                self.title = title_elem.get_text()
                return self.title
        return "Unknown"
    
    def get_summary(self) -> str:
        """Extract article summary (first paragraph)"""
        if self.soup:
            # Find the main content area
            content = self.soup.find("div", {"id": "mw-content-text"})
            if content:
                # Get first paragraph that's not empty
                paragraphs = content.find_all("p")
                for p in paragraphs:
                    text = p.get_text().strip()
                    if len(text) > 100 and not text.startswith("Coordinates"):
                        return text[:500]  # Limit to 500 chars
        return ""
    
    def get_sections(self) -> List[str]:
        """Extract main section headings"""
        sections = []
        if self.soup:
            # Find all h2 and h3 headings (main sections)
            headings = self.soup.find_all(["h2", "h3"])
            for heading in headings[:10]:  # Limit to first 10 sections
                # Extract text and remove edit link
                text = heading.get_text().strip()
                text = text.replace("[edit]", "").strip()
                if text and text not in sections:
                    sections.append(text)
        return sections
    
    def get_key_entities(self) -> Dict[str, List[str]]:
        """Extract key entities from article"""
        entities = {
            "people": [],
            "organizations": [],
            "locations": []
        }
        
        if self.soup:
            # Simple entity extraction from links
            links = self.soup.find_all("a", {"title": True})
            for link in links[:30]:  # Sample first 30 links
                title = link.get("title")
                text = link.get_text()
                
                # Basic categorization (can be improved)
                if any(x in title.lower() for x in ["birth", "death", "born"]):
                    if text not in entities["people"]:
                        entities["people"].append(text)
                elif any(x in title.lower() for x in ["university", "company", "organizat"]):
                    if text not in entities["organizations"]:
                        entities["organizations"].append(text)
                elif any(x in title.lower() for x in ["country", "city", "town"]):
                    if text not in entities["locations"]:
                        entities["locations"].append(text)
        
        return entities
    
    def get_all_content(self) -> Dict:
        """Get all extracted content"""
        if not self.validate_url():
            raise ValueError(f"Invalid Wikipedia URL: {self.url}")
        
        if not self.fetch_content():
            raise Exception("Failed to fetch article content")
        
        return {
            "title": self.get_title(),
            "summary": self.get_summary(),
            "sections": self.get_sections(),
            "key_entities": self.get_key_entities(),
            "raw_html": self.raw_html
        }
