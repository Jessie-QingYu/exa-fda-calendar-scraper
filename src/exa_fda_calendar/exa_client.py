import os
from typing import Any, Dict, Optional
from dotenv import load_dotenv
from exa_py import Exa

class ExaClient:
    def __init__(self, api_key: Optional[str] = None) -> None:
        load_dotenv()
        api_key = api_key or os.getenv("EXA_API_KEY")
        if not api_key:
            raise RuntimeError("Missing EXA_API_KEY in environment. Put it in .env")
        self.client = Exa(api_key)

    def get_text(self, url: str, livecrawl: str = "preferred") -> str:
        """
        Fetch page text only (no HTML). Try several livecrawl modes if needed.
        """
        tried = []
        for mode in [livecrawl, "always", "fallback"]:
            if mode in tried:
                continue
            tried.append(mode)
            try:
                res = self.client.get_contents([url], text=True, livecrawl=mode)
                if getattr(res, "results", None):
                    txt = (getattr(res.results[0], "text", "") or "").strip()
                    if txt:
                        if mode != livecrawl:
                            print(f"[get_text] succeeded with livecrawl='{mode}' (requested '{livecrawl}')")
                        return txt
            except Exception as e:
                print(f"[get_text] mode '{mode}' error: {e}")
        print(f"[get_text] empty after modes: {tried}")
        return ""

    def get_structured(self, url: str, schema: Dict[str, Any], query: Optional[str] = None,
                       livecrawl: str = "preferred") -> Dict[str, Any]:
        summary: Dict[str, Any] = {"schema": schema}
        if query:
            summary["query"] = query
        try:
            res = self.client.get_contents([url], summary=summary, livecrawl=livecrawl)
            if getattr(res, "results", None) and getattr(res.results[0], "summary", None):
                import json
                return json.loads(res.results[0].summary) or {}
        except Exception as e:
            print(f"[get_structured] error livecrawl='{livecrawl}': {e}")
        if livecrawl != "always":
            try:
                res = self.client.get_contents([url], summary=summary, livecrawl="always")
                if getattr(res, "results", None) and getattr(res.results[0], "summary", None):
                    import json
                    print("[get_structured] succeeded with livecrawl='always'.")
                    return json.loads(res.results[0].summary) or {}
            except Exception as e:
                print(f"[get_structured] fallback 'always' error: {e}")
        return {}
