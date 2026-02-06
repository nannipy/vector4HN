import httpx
import asyncio
from typing import List, Dict, Any, Optional
import trafilatura

HN_API_BASE = "https://hacker-news.firebaseio.com/v0"

class HNClient:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0, follow_redirects=True)

    async def close(self):
        await self.client.aclose()

    async def fetch_item(self, item_id: int) -> Dict[str, Any]:
        try:
            response = await self.client.get(f"{HN_API_BASE}/item/{item_id}.json")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching item {item_id}: {e}")
            return {}

    async def fetch_top_stories(self, page: int = 1, limit: int = 50) -> List[Dict[str, Any]]:
        try:
            response = await self.client.get(f"{HN_API_BASE}/topstories.json")
            response.raise_for_status()
            all_ids = response.json()
            
            start = (page - 1) * limit
            end = start + limit
            ids = all_ids[start:end]
            
            tasks = [self.fetch_item(id) for id in ids]
            stories = await asyncio.gather(*tasks)
            return [s for s in stories if s]
        except Exception as e:
            print(f"Error fetching top stories: {e}")
            return []

    async def fetch_comments(self, item_ids: List[int], limit: int = 100) -> List[Dict[str, Any]]:
        """
        BFS traversal to fetch comments up to a limit.
        """
        comments = []
        queue = [(id, 0) for id in item_ids] # (id, depth)
        fetched_count = 0

        while queue and fetched_count < limit:
            batch_with_depth = queue[:10]
            queue = queue[10:]
            
            tasks = [self.fetch_item(pair[0]) for pair in batch_with_depth]
            results = await asyncio.gather(*tasks)
            
            for i, res in enumerate(results):
                if not res or res.get("deleted") or res.get("dead"):
                    continue
                
                depth = batch_with_depth[i][1]
                res["depth"] = depth
                comments.append(res)
                fetched_count += 1
                
                if "kids" in res:
                    queue.extend([(kid_id, depth + 1) for kid_id in res["kids"]])
                    
                if fetched_count >= limit:
                    break
        
        return comments

    async def fetch_article_text(self, url: str) -> str:
        if not url:
            return "No URL provided."
        
        # Skip PDF or non-text files based on extension (simple check)
        if url.lower().endswith('.pdf'):
            return "PDF content extraction not supported."

        try:
            # User-Agent is important for some sites
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
            }
            response = await self.client.get(url, headers=headers)
            response.raise_for_status()
            
            extracted_text = trafilatura.extract(response.text, include_links=True, include_comments=False)
            
            if extracted_text:
                 # Truncate if too long (approx 20k chars)
                return extracted_text[:20000]
            else:
                 return "Could not extract article text."

        except Exception as e:
            return f"Failed to extract text: {e}"

# Singleton instance helper if needed
async def get_hn_client():
    return HNClient()
