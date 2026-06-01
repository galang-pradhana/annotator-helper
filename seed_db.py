import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_session, init_db
from models import Project, Task
from sqlmodel import select

async def seed_data():
    print("Seeding projects and tasks...")
    async with get_session() as session:
        # 1. Projects
        projects = [
            Project(code="CHERRY_OPAL", name="Cherry Opal"),
            Project(code="LIGHTHOUSE", name="Lighthouse"),
        ]
        
        for p in projects:
            # Check if exists
            statement = select(Project).where(Project.code == p.code)
            result = await session.execute(statement)
            if not result.scalar_one_or_none():
                session.add(p)
                print(f"Added project: {p.name}")

        # 2. Tasks
        tasks = [
            # Cherry Opal
            Task(project_code="CHERRY_OPAL", code="PR", name="Anotasi PR Fine Tuning"),
            Task(project_code="CHERRY_OPAL", code="AFM", name="AFM (Multi Modal)"),
            
            # Lighthouse
            Task(project_code="LIGHTHOUSE", code="VCG", name="VCG (Visual Content Generation)"),
            Task(project_code="LIGHTHOUSE", code="CYU", name="CYU (Website Topic)"),
            Task(project_code="LIGHTHOUSE", code="TA_TC", name="TA/TC (Text Composition)"),
        ]

        for t in tasks:
            # Check if exists
            statement = select(Task).where(Task.project_code == t.project_code, Task.code == t.code)
            result = await session.execute(statement)
            if not result.scalar_one_or_none():
                session.add(t)
                print(f"Added task: {t.name} to {t.project_code}")

        try:
            await session.commit()
            print("Seeding completed successfully.")
        except Exception as e:
            print(f"Error seeding data: {e}")
            await session.rollback()

if __name__ == "__main__":
    async def main():
        await init_db()
        await seed_data()
    
    asyncio.run(main())
