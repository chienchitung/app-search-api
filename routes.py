from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from scraper import AppSearchManager
import asyncio

router = APIRouter()

class SearchRequest(BaseModel):
    searchTerm: str

@router.post("/search")
async def search_apps(request: SearchRequest):
    try:
        if not request.searchTerm:
            raise HTTPException(status_code=400, detail="搜尋詞不能為空")

        search_manager = AppSearchManager()
        results = await search_manager.search_all_platforms([request.searchTerm])
        
        return {"data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 