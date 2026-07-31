import random
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.core.utils import infer_category
from app.models import RepairOrder, User
from app.schemas.common import ApiResponse, PageData
from app.schemas.repair import RepairCreate, RepairOut

router = APIRouter(prefix="/api/repairs", tags=["报修"], dependencies=[Depends(get_current_user)])


def _gen_order_no() -> str:
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    rnd = "".join(random.choices("0123456789", k=6))
    return f"R{ts}{rnd}"


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@router.post("/", response_model=ApiResponse[RepairOut])
def create_repair(
    repair_in: RepairCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    category = repair_in.category or infer_category(repair_in.repair_type)

    order = RepairOrder(
        order_no=_gen_order_no(),
        user_id=current_user.id,
        repair_type=repair_in.repair_type,
        category=category,
        urgency=repair_in.urgency,
        address=repair_in.address,
        contact_name=repair_in.contact_name,
        contact_phone=repair_in.contact_phone,
        description=repair_in.description,
        image_urls=repair_in.image_urls or [],
        status="pending",
        progress_timeline=[
            {
                "status": "pending",
                "time": _utcnow_iso(),
                "note": "工单已提交，等待受理",
            }
        ],
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return ApiResponse(code=200, message="提交成功", data=RepairOut.model_validate(order))


@router.get("/", response_model=ApiResponse[PageData[RepairOut]])
def list_repairs(
    status: str = Query("all", description="all/pending/processing/completed/cancelled"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(RepairOrder).filter(RepairOrder.user_id == current_user.id)
    if status and status != "all":
        query = query.filter(RepairOrder.status == status)

    total = query.count()
    items = (
        query.order_by(RepairOrder.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    out_items = [RepairOut.model_validate(it) for it in items]
    return ApiResponse(
        code=200,
        message="获取成功",
        data=PageData(items=out_items, total=total, page=page, page_size=page_size),
    )


@router.get("/{repair_id}", response_model=ApiResponse[RepairOut])
def get_repair_detail(
    repair_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = db.query(RepairOrder).filter(RepairOrder.id == repair_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="工单不存在")
    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权查看该工单")
    return ApiResponse(code=200, message="获取成功", data=RepairOut.model_validate(order))


@router.post("/{repair_id}/cancel", response_model=ApiResponse[RepairOut])
def cancel_repair(
    repair_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = db.query(RepairOrder).filter(RepairOrder.id == repair_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="工单不存在")
    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作该工单")

    if order.status != "pending":
        raise HTTPException(status_code=400, detail="当前状态不可取消")

    order.status = "cancelled"
    timeline = list(order.progress_timeline or [])
    timeline.append({
        "status": "cancelled",
        "time": _utcnow_iso(),
        "note": "用户取消工单",
    })
    order.progress_timeline = timeline
    order.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(order)
    return ApiResponse(code=200, message="取消成功", data=RepairOut.model_validate(order))


debug_router = APIRouter(prefix="/api/repairs", tags=["报修调试"], dependencies=[Depends(get_current_user)])


@debug_router.post("/{repair_id}/debug/transition", response_model=ApiResponse[RepairOut])
def debug_transition(
    repair_id: int,
    next: str = Query(..., description="processing|completed"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if next not in ("processing", "completed"):
        raise HTTPException(status_code=400, detail="next 参数必须是 processing 或 completed")

    order = db.query(RepairOrder).filter(RepairOrder.id == repair_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="工单不存在")
    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作该工单")

    note_map = {
        "processing": "调试：工单进入处理中状态",
        "completed": "调试：工单已完成",
    }

    order.status = next
    timeline = list(order.progress_timeline or [])
    timeline.append({
        "status": next,
        "time": _utcnow_iso(),
        "note": note_map[next],
    })
    order.progress_timeline = timeline
    order.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(order)
    return ApiResponse(code=200, message="状态流转成功", data=RepairOut.model_validate(order))
