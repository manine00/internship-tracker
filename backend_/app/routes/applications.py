from http.client import HTTPException
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_db
from ..models.application import Application
from ..models.company import Company
from sqlalchemy.future import select
from sqlalchemy import join

router = APIRouter()



# Return all applications with company names
@router.get("", tags=["applications"])
async def get_applications(db: AsyncSession = Depends(get_db)):
    stmt = (
        select(
            Application.id,
            Application.position,
            Application.sent_date,
            Application.email_id,
            Application.status,
            Application.summary,
            Company.name.label("company_name")
        ).join(Company, Application.company_id == Company.id)
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