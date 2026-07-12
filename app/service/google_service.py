from app.core.logger import logger
from app.config.setting import settings
import httpx
import os
from dotenv import load_dotenv
import re
from bs4 import BeautifulSoup

load_dotenv()
_cfg = settings.research

async def google_search_service(query:str,num_results:int = None)->list[dict]:
    number = num_results or _cfg["num_results"]
    params = {
        "q" : query,
        "page" : min(number,10),
    }
    headers = {
         "X-API-KEY": _cfg["serper_key"],
         "content_Type": "application/json"
    }
    try:
        # data = dummy_data
        with httpx.Client(timeout=_cfg["fetch_timeout_seconds"]) as client:
                resp = client.post(_cfg["Google_API_Point"],headers=headers, params=params)
                data = resp.json()

    except httpx.HTTPStatusError as e:
        logger.info(f"Google CSE HTTP Error -> {e}")
        return []
    except Exception as e:
        logger.error(f"Google CSE request failed: {e}")
        return []
    
    items = data.get("organic",[])
    results = [          
         {
              "title" : item.get("title",""),
              "url": item.get("link",""),
              "snippet": item.get("snippet","")
         }
        for item in items
        ]
    logger.info(f"Google Search returned {len(results)} for '{query[:60]}'")
    return results

def read_url(url:str)->dict:
    max_chars = _cfg["max_chars_per_pages"]
    timeout = _cfg["fetch_timeout_seconds"]
    headers = {
          "User-Agent":"Mozilla/5.0 (compatible; ResearchAgent/1.0)"
    }

    try:
        with httpx.Client(timeout=timeout,follow_redirects=True,headers=headers) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                html = resp.text
            else:
                html = ""

    except Exception as e:
        logger.info(f"Failed to fetch -> {e}")
        return {"url": url, "title": "", "text": "", "success": False, "error": str(e)}
    
    # soup process

    try:
        soup = BeautifulSoup(html,"html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
            tag.decompose()

        title = soup.title.string.strip() if soup.title and soup.title.string else ""
        text = soup.get_text(separator="\n" , strip=True)

        text = re.sub(r"\n{3,}","\n\n",text)
        if len(text) > max_chars:
            text = text[:max_chars] + "\n..[truncated]"

    except Exception as e:
        logger.error(f"Failed to parse {url} -> {e}")
        return { "url": url, "title": "", "text": "", "success": False, "error": str(e) }
    
    logger.info(f"Read URL:{url} - {len(text)} chars extracted")
    return { "url":url, "title": title, "text":text, "success":True, "error":None}