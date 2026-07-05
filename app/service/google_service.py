from app.core.logger import logger
from app.config.setting import settings
import httpx
import os
from dotenv import load_dotenv
import re
from bs4 import BeautifulSoup

load_dotenv()
_cfg = settings.research

dummy_data = {"searchParameters":{"q":"who is the cm of tamil nadu","type":"search","page":5,"engine":"google"},"organic":[{"title":"List of all Chief Ministers of Tamil Nadu (1952-2026)","link":"https://www.jagranjosh.com/general-knowledge/chief-ministers-of-tamil-nadu-their-tenures-and-parties-1620292428-1","snippet":"Joseph Vijay is serving as the current Chief Minister of Tamil Nadu. The actor-turned-politician and founder of the Tamilaga Vettri Kazhagam ( ...","date":"May 10, 2026","position":1},{"title":"List of deputy chief ministers of Tamil Nadu - Wikipedia","link":"https://en.wikipedia.org/wiki/List_of_deputy_chief_ministers_of_Tamil_Nadu","snippet":"Most recently, Udhayanidhi Stalin of the Dravida Munnetra Kazhagam was appointed deputy chief minister while also serving as minister for youth welfare and ...","position":2},{"title":"List of Chief Ministers of Tamil Nadu & Their Service Periods","link":"https://www.oneindia.com/list-of-chief-ministers-of-tamil-nadu/","snippet":"Janaki Ramachandran has the shortest tenure for 23 days. C. Rajagopalachari served as the last Governor of India before becoming Chief Minister of undivided ...","position":3},{"title":"List of Chief Ministers of Tamilnadu From 1920 to 2026 - StudyIQ","link":"https://www.studyiq.com/articles/chief-ministers-of-tamilnadu/?srsltid=AfmBOorrXIYagwaWTBelhw5Li0PNWybJAtFE652arbFYx0pFEslsU9nZ","snippet":"The Governor appoints the Chief Minister of Tamil Nadu and holds office for a term of five years, with the possibility of re-election. · The CM ...","date":"May 10, 2026","position":4},{"title":"CM C Joseph Vijay led Cabinet in Tamil Nadu expanded to 33 ...","link":"https://newsonair.gov.in/tamil-nadu-chief-minister-c-joseph-vijay-to-expand-his-cabinet-today/","snippet":"With the latest expansion, the Cabinet strength has risen to 32, including Chief Minister C. Joseph Vijay. The Congress has now returned to the ...","date":"May 21, 2026","position":5},{"title":"Muthuvel Karunanidhi Stalin - Chief minister of Tamilnadu - LinkedIn","link":"https://in.linkedin.com/in/muthuvel-karunanidhi-stalin-71875120a","snippet":"Muthuvel Karunanidhi Stalin · Chief minister of Tamilnadu · View mutual connections with Muthuvel Karunanidhi · About · Experience · View Muthuvel Karunanidhi's ...","position":6},{"title":"MK Stalin: The Boy From Chennai's Marina Beach - NDTV","link":"https://www.ndtv.com/india-news/tamil-nadu-assembly-election-news-mk-stalin-profile-who-is-mk-stalin-chennai-marina-beach-11442178","snippet":"On the shores of the Bay of Bengal, Tamil Nadu welcomed Muthuvel Karunanidhi Stalin. Latest and Breaking News on NDTV. The father, M Karunanidhi (File). Today, ...","position":7},{"title":"List of All Chief Ministers of Tamil Nadu - Entri Blog","link":"https://entri.app/blog/list-of-all-chief-ministers-of-tamil-nadu/","snippet":"M.K Stalin – Current CM of Tamil Nadu. Muthuvel Karunanidhi Stalin was born was 01 March 1953. He is serving as the 8th Chief Minister of ...","date":"Jun 11, 2021","position":8},{"title":"Vijay has become the CM of Tamil Nadu.. - Instagram","link":"https://www.instagram.com/p/DX6pwY4EUnF/","snippet":"12K likes, 22 comments - 69casm on May 4, 2026: \"Vijay has become the CM of Tamil Nadu..\".","date":"May 4, 2026","position":9},{"title":"Chief Minister of Tamil Nadu (@CMOTamilnadu) Reels - Facebook","link":"https://www.facebook.com/CMOTamilnadu/reels/","snippet":"Chief Minister of Tamil Nadu Reels. 620782 likes · 95039 talking about this. The Official page of the Chief Minister of Tamil Nadu.. Watch the latest...","position":10}],"credits":1}

async def google_search_service(query:str,num_results:int = None)->list[dict]:
    number = num_results or _cfg["num_results"]
    params = {
        "q" : query,
        "page" : min(number,10),
    }
    headers = {
         "X-API-KEY": os.getenv("SERPER_KEY"),
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