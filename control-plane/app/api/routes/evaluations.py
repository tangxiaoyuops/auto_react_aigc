"""Evaluation 路由：评测集 / 用例 / 评测任务 / 报告"""
import asyncio
import random
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db, AsyncSessionLocal, DBEvalTask, DBEvalCase
from app.core.security import get_current_user, TokenPayload
from app.services.evaluation_service import EvaluationService
from shared.schemas.evaluation import (
    DatasetCreate, CaseCreate, CaseUpdate, TaskCreate,
)

logger = logging.getLogger("evaluation")
router = APIRouter()


def get_eval_service(db: AsyncSession = Depends(get_db)) -> EvaluationService:
    return EvaluationService(db=db)


def _serialize_ds(ds) -> dict:
    return {
        "id": ds.id,
        "name": ds.name,
        "description": ds.description,
        "case_count": ds.case_count,
        "created_at": ds.created_at,
        "updated_at": ds.updated_at,
    }


def _serialize_case(c) -> dict:
    return {
        "id": c.id,
        "dataset_id": c.dataset_id,
        "question": c.question,
        "expected": c.expected,
        "actual": c.actual,
        "score": c.score,
        "status": c.status,
        "created_at": c.created_at,
    }


def _serialize_task(t) -> dict:
    return {
        "id": t.id,
        "name": t.name,
        "agent_id": t.agent_id,
        "agent_name": t.agent_name,
        "dataset_id": t.dataset_id,
        "status": t.status,
        "progress": t.progress,
        "total_cases": t.total_cases,
        "passed_cases": t.passed_cases,
        "report": t.report or {},
        "created_at": t.created_at,
        "completed_at": t.completed_at,
    }


# ---------- 评测集 ----------

@router.get("/datasets", response_model=dict)
async def list_datasets(
    current_user: TokenPayload = Depends(get_current_user),
    service: EvaluationService = Depends(get_eval_service),
):
    dss = await service.list_datasets(current_user.user_id)
    return {"datasets": [_serialize_ds(d) for d in dss], "total": len(dss)}


@router.post("/datasets", response_model=dict)
async def create_dataset(
    payload: DatasetCreate,
    current_user: TokenPayload = Depends(get_current_user),
    service: EvaluationService = Depends(get_eval_service),
):
    ds = await service.create_dataset(current_user.user_id, payload)
    return _serialize_ds(ds)


@router.delete("/datasets/{dataset_id}")
async def delete_dataset(
    dataset_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    service: EvaluationService = Depends(get_eval_service),
):
    ds = await service.get_dataset(current_user.user_id, dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    await service.delete_dataset(ds)
    return {"message": "Dataset deleted"}


# ---------- 用例 ----------

@router.get("/datasets/{dataset_id}/cases", response_model=dict)
async def list_cases(
    dataset_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    service: EvaluationService = Depends(get_eval_service),
):
    ds = await service.get_dataset(current_user.user_id, dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    cases = await service.list_cases(dataset_id)
    return {"cases": [_serialize_case(c) for c in cases], "total": len(cases)}


@router.post("/datasets/{dataset_id}/cases", response_model=dict)
async def add_case(
    dataset_id: str,
    payload: CaseCreate,
    current_user: TokenPayload = Depends(get_current_user),
    service: EvaluationService = Depends(get_eval_service),
):
    ds = await service.get_dataset(current_user.user_id, dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    case = await service.add_case(dataset_id, payload)
    return _serialize_case(case)


@router.put("/cases/{case_id}", response_model=dict)
async def update_case(
    case_id: str,
    payload: CaseUpdate,
    current_user: TokenPayload = Depends(get_current_user),
    service: EvaluationService = Depends(get_eval_service),
    db: AsyncSession = Depends(get_db),
):
    case = await db.get(DBEvalCase, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    case = await service.update_case(case, payload)
    return _serialize_case(case)


# ---------- 评测任务 ----------

@router.post("/tasks", response_model=dict)
async def create_task(
    payload: TaskCreate,
    current_user: TokenPayload = Depends(get_current_user),
    service: EvaluationService = Depends(get_eval_service),
):
    task = await service.create_task(current_user.user_id, payload)
    # 后台异步执行评测
    asyncio.create_task(_run_eval(task_id=task.id, user_id=current_user.user_id))
    return _serialize_task(task)


@router.get("/tasks", response_model=dict)
async def list_tasks(
    current_user: TokenPayload = Depends(get_current_user),
    service: EvaluationService = Depends(get_eval_service),
):
    tasks = await service.list_tasks(current_user.user_id)
    return {"tasks": [_serialize_task(t) for t in tasks], "total": len(tasks)}


@router.get("/tasks/{task_id}/report", response_model=dict)
async def task_report(
    task_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    service: EvaluationService = Depends(get_eval_service),
):
    task = await service.get_task(current_user.user_id, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return await service.get_task_report(task)


async def _run_eval(task_id: str, user_id: str):
    """后台模拟执行评测：逐用例评分，进度递增，最终生成报告"""
    async with AsyncSessionLocal() as db:
        task = await db.get(DBEvalTask, task_id)
        if not task:
            return
        task.status = "running"
        await db.commit()

        service = EvaluationService(db=db)
        cases = await service.list_cases(task.dataset_id) if task.dataset_id else []

        total = len(cases)
        passed = 0
        score_sum = 0.0
        case_report = []
        for idx, case in enumerate(cases):
            # 模拟 Agent 推理结果（deterministic seed 使可复现）
            ok = _decide(case.question)
            score = 1.0 if ok else round(0.4 + random.random() * 0.3, 2)
            if ok:
                passed += 1
            score_sum += score
            case.actual = case.expected if ok else "（模拟结果）未能命中期望答案"
            case.score = score
            case.status = "passed" if ok else "failed"
            case_report.append({
                "id": case.id, "question": case.question, "expected": case.expected,
                "actual": case.actual, "score": score, "status": case.status,
            })
            await db.commit()
            # 更新进度
            task.progress = int((idx + 1) / total * 100) if total else 100
            task.passed_cases = passed
            avg = round(score_sum / (idx + 1), 2)
            task.report = {
                "avg_score": avg,
                "pass_rate": _rate(passed, idx + 1),
                "cases": case_report,
            }
            await db.commit()
            await asyncio.sleep(0.15)  # 模拟延迟，让前端看到进度

        task.status = "completed"
        task.progress = 100
        task.passed_cases = passed
        task.total_cases = total
        task.completed_at = datetime.utcnow()
        task.report = {
            "avg_score": round(score_sum / total, 2) if total else 0.0,
            "pass_rate": _rate(passed, total),
            "pass_count": passed,
            "total_count": total,
            "cases": case_report,
        }
        await db.commit()


def _decide(question: str) -> bool:
    """确定性伪评测：根据问题特征决定是否通过（演示用）"""
    s = 0
    for ch in question:
        s += ord(ch)
    return s % 3 != 0


def _rate(passed: float, total: int) -> float:
    return round(passed * 100.0 / total, 1) if total else 0.0