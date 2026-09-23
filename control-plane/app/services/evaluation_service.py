"""Evaluation 服务：评测集 / 用例 / 评测任务"""
import asyncio
import random
from typing import List, Optional
from uuid import uuid4
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.database import DBEvalDataset, DBEvalCase, DBEvalTask
from shared.schemas.evaluation import DatasetCreate, CaseCreate, TaskCreate


class EvaluationService:
    """评测中心服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ---------- 评测集 ----------

    async def create_dataset(self, user_id: str, payload: DatasetCreate) -> DBEvalDataset:
        ds = DBEvalDataset(
            id=str(uuid4()),
            user_id=user_id,
            name=payload.name,
            description=payload.description,
            case_count=0,
            created_at=datetime.utcnow(),
        )
        self.db.add(ds)
        await self.db.commit()
        await self.db.refresh(ds)
        return ds

    async def list_datasets(self, user_id: str) -> List[DBEvalDataset]:
        result = await self.db.execute(
            select(DBEvalDataset)
            .where(DBEvalDataset.user_id == user_id)
            .order_by(DBEvalDataset.created_at.desc())
        )
        return result.scalars().all()

    async def get_dataset(self, user_id: str, dataset_id: str) -> Optional[DBEvalDataset]:
        result = await self.db.execute(
            select(DBEvalDataset).where(
                DBEvalDataset.id == dataset_id, DBEvalDataset.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def delete_dataset(self, ds: DBEvalDataset) -> None:
        await self.db.delete(ds)
        await self.db.commit()

    # ---------- 用例 ----------

    async def add_case(self, dataset_id: str, payload: CaseCreate) -> DBEvalCase:
        case = DBEvalCase(
            id=str(uuid4()),
            dataset_id=dataset_id,
            question=payload.question,
            expected=payload.expected,
            actual="",
            score=0.0,
            status="passed",
            created_at=datetime.utcnow(),
        )
        self.db.add(case)
        # 更新数据集用例数
        await self._refresh_case_count(dataset_id)
        await self.db.commit()
        await self.db.refresh(case)
        return case

    async def list_cases(self, dataset_id: str) -> List[DBEvalCase]:
        result = await self.db.execute(
            select(DBEvalCase)
            .where(DBEvalCase.dataset_id == dataset_id)
            .order_by(DBEvalCase.created_at)
        )
        return result.scalars().all()

    async def update_case(self, case: DBEvalCase, payload) -> DBEvalCase:
        data = payload.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(case, field, value)
        await self.db.commit()
        await self.db.refresh(case)
        return case

    async def _refresh_case_count(self, dataset_id: str):
        result = await self.db.execute(
            select(func.count()).select_from(DBEvalCase).where(
                DBEvalCase.dataset_id == dataset_id
            )
        )
        count = result.scalar_one() or 0
        ds = await self.db.get(DBEvalDataset, dataset_id)
        if ds:
            ds.case_count = count

    # ---------- 评测任务 ----------

    async def create_task(self, user_id: str, payload: TaskCreate) -> DBEvalTask:
        task = DBEvalTask(
            id=str(uuid4()),
            user_id=user_id,
            name=payload.name,
            agent_id=payload.agent_id,
            agent_name=payload.agent_name,
            dataset_id=payload.dataset_id,
            status="pending",
            progress=0,
            total_cases=0,
            passed_cases=0,
            report=dict(averages={}, cases=[]),
            created_at=datetime.utcnow(),
        )
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)

        # 取数据集用例数
        cases = await self.list_cases(payload.dataset_id)
        task.total_cases = len(cases)
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def list_tasks(self, user_id: str) -> List[DBEvalTask]:
        result = await self.db.execute(
            select(DBEvalTask)
            .where(DBEvalTask.user_id == user_id)
            .order_by(DBEvalTask.created_at.desc())
        )
        return result.scalars().all()

    async def get_task(self, user_id: str, task_id: str) -> Optional[DBEvalTask]:
        result = await self.db.execute(
            select(DBEvalTask).where(
                DBEvalTask.id == task_id, DBEvalTask.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def get_task_report(self, task: DBEvalTask) -> dict:
        """评测报告：通过率、通过用例数、用例明细（对应前端报告弹窗）"""
        cases = await self.list_cases(task.dataset_id) if task.dataset_id else []
        report = task.report or {}
        return {
            "task_id": task.id,
            "name": task.name,
            "status": task.status,
            "agent_name": task.agent_name,
            "total_cases": task.total_cases,
            "passed_cases": task.passed_cases,
            "pass_rate": _rate(task.passed_cases, task.total_cases),
            "avg_score": report.get("avg_score", 0.0),
            "cases": [
                {
                    "id": c.id,
                    "question": c.question,
                    "expected": c.expected,
                    "actual": c.actual,
                    "score": c.score,
                    "status": c.status,
                }
                for c in cases
            ],
        }


def _rate(passed: int, total: int) -> float:
    return round(passed * 100.0 / total, 1) if total else 0.0