import logging
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_db
from ..models.application import Application
from ..models.company import Company
from sqlalchemy.future import select
from sqlalchemy import join
from ..services.mistral_service import extract_internship_description

router = APIRouter()

async def get_applications_by_company(company_name: str, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(
            Application.id,
            Application.position,
            Application.sent_date,
            Application.email_id,
            Application.status,
            Application.summary,
            Company.name.label("company_name")
        )
        .join(Company, Application.company_id == Company.id)
        .where(Company.name == company_name)
    )
    result = await db.execute(stmt)
    applications = [dict(row._mapping) for row in result.all()]
    if not applications:
        raise HTTPException(404, "No applications found for this company")
    return applications


# Return applications filtered by company name
@router.get("/{company_name}", tags=["company"])
async def get_companies(company_name: str, db: AsyncSession = Depends(get_db)):
    company_result = await db.execute(
        select(
            Company.name,
            Company.internship_description
        ).where(Company.name == company_name)
    )

    company = company_result.fetchone()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # await the coroutine and pass db properly
    timeline = await get_applications_by_company(company_name, db)

    return {
        "name": company.name,
        "internship_description": company.internship_description,
        "timeline": timeline
    }


@router.get("", tags=["company"])
async def get_companies(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Company))
    return result.scalars().all()



@router.post("/description/{company_name}", tags=["company"])
async def submit_description(company_name, data = Body(...), db: AsyncSession = Depends(get_db)):
    try:
        stmt = select(Company).where(Company.name == company_name)
        result = await db.execute(stmt)
        company = result.scalar_one_or_none()

        if not company:
            raise HTTPException(
                status_code=404, 
                detail=f"Company '{company_name}' not found in the database."
            )
        
        processed_text = await extract_internship_description(data["summary"])

        company.internship_description = processed_text

        await db.commit()
        
        return {
            "message": f"Internship description for {company_name} successfully updated.",
            "new_description_summary": processed_text[:100] + "..."
        }

    except Exception as e:
        db.rollback()
        logging.error(f"Error processing or updating description for {company_name}: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to process or store the description due to an internal error."
        )

@router.get("/t/test", tags=["company"])
async def test_description():
    desc = f"""
        We are looking for a Frontend Development Intern to join our team at TechNova Solutions for a 4-month internship starting in March 2025.
        The intern will work closely with senior developers to build and optimize our internal dashboard using Vue.js 3 (Composition API) and TypeScript.
        Responsibilities include implementing reusable UI components, integrating RESTful APIs, and improving performance metrics.
        Requirements:
        Basic understanding of JavaScript/TypeScript and Vue.js
        Familiarity with version control (Git) and REST APIs
        Curiosity, problem-solving mindset, and attention to detail
        What we offer:
        Remote-friendly work environment
        Daily mentorship sessions with senior engineers
        Internship allowance (€600/month)
        Possibility of full-time offer after internship

        """

    from ..services.mistral_service import extract_internship_description
    result = await extract_internship_description(desc)
    return result