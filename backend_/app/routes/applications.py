from http.client import HTTPException
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_db
from ..models.application import Application
from ..models.company import Company
from sqlalchemy.future import select
from sqlalchemy import outerjoin, func

router = APIRouter()



# Return all applications with company names
@router.get("", tags=["applications"])
async def get_applications(db: AsyncSession = Depends(get_db)):
    stmt = (
        select(
            Application.id,
            # Use coalesce to replace NULLs with safe fallback strings
            func.coalesce(Application.position, "Analyzing...").label("position"),
            Application.sent_date,
            Application.email_id,
            Application.status,
            func.coalesce(Application.summary, "").label("summary"),
            func.coalesce(Company.name, "Pending AI").label("company_name")
        )
        # Use outerjoin so we don't hide unprocessed emails
        .outerjoin(Company, Application.company_id == Company.id) 
    )
    result = await db.execute(stmt)
    return [dict(row._mapping) for row in result.all()]



from ..test.prompt_tst import prmpt_test

@router.get("/test")
async def prompt_test():
    result = await prmpt_test()
    return result 

from ..services.mistral_service import ping

@router.get("/ping")
async def ping_test():
    return await ping()