"""
models.py
---------
SQLModel definitions untuk Credit-Based Billing system.
Table: users, transactions, projects, tasks, evaluations
"""

from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Field, SQLModel
from sqlalchemy import Column, BigInteger, DateTime


class User(SQLModel, table=True):
    __tablename__ = "users"

    user_id: Optional[int] = Field(
        sa_column=Column(BigInteger, primary_key=True),
        description="Telegram User ID",
    )
    username: Optional[str] = Field(default=None)
    balance: int = Field(default=500, description="Saldo dalam Poin")
    is_registered: bool = Field(default=False)
    selected_lang: str = Field(default="ID")
    selected_project: Optional[str] = Field(default=None, description="Kode Proyek (e.g. CHERRY_OPAL)")
    selected_task: str = Field(default="PR")
    selected_tier: str = Field(default="BASIC", description="BASIC atau PREMIUM")


class Project(SQLModel, table=True):
    __tablename__ = "projects"

    code: str = Field(primary_key=True, description="Unique code (e.g. CHERRY_OPAL)")
    name: str = Field(description="Display name")


class Task(SQLModel, table=True):
    __tablename__ = "tasks"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_code: str = Field(index=True, description="FK ke projects.code")
    code: str = Field(description="Task code (e.g. PR, AFM)")
    name: str = Field(description="Display name")


class Transaction(SQLModel, table=True):
    __tablename__ = "transactions"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(
        sa_column=Column(BigInteger, index=True),
        description="FK ke users.user_id",
    )
    amount: int = Field(default=0, description="Positif=topup, Negatif=deduction")
    type: str = Field(default="deduction", description="deduction | topup")
    task_type: str = Field(default="")
    model_used: str = Field(default="")
    timestamp: datetime = Field(
        sa_column=Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)),
        description="Timestamp aware (UTC)",
    )


class Evaluation(SQLModel, table=True):
    __tablename__ = "evaluations"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(
        sa_column=Column(BigInteger, index=True),
        description="FK ke users.user_id",
    )
    task_code: str = Field(default="", description="Task e.g. PR, VCG_EDIT")
    user_input: str = Field(description="Dynamic input text from user (Question)")
    ai_output: str = Field(description="Response from AI (Answer)")
    feedback: Optional[str] = Field(default=None, description="positive | negative | None")
    timestamp: datetime = Field(
        sa_column=Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)),
        description="Timestamp aware (UTC)",
    )