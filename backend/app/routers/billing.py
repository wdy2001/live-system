from typing import Optional, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.billing import random_usage_for_type
from app.core.deps import get_db, get_current_user
from app.models import BillingRule, MeterUsage, User
from app.schemas.billing import BillingRuleOut, MeterUsageOut
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/api", tags=["计费"])


@router.get("/billing-rules", response_model=ApiResponse[List[BillingRuleOut]])
def list_billing_rules(
    type: Optional[str] = Query("all", description="electric/water/gas/all"),
    db: Session = Depends(get_db),
):
    query = db.query(BillingRule)
    if type and type != "all":
        query = query.filter(BillingRule.type == type)
    rules = query.order_by(BillingRule.type.asc(), BillingRule.tier_min.asc()).all()
    return ApiResponse(code=200, message="获取成功", data=[BillingRuleOut.model_validate(r) for r in rules])


@router.get("/meter-usage", response_model=ApiResponse[MeterUsageOut])
def get_meter_usage(
    house_no: str = Query(..., description="户号"),
    type: str = Query(..., description="electric/water/gas"),
    month: str = Query(..., description="YYYY-MM"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    usage = (
        db.query(MeterUsage)
        .filter(
            MeterUsage.house_no == house_no,
            MeterUsage.type == type,
            MeterUsage.month == month,
        )
        .first()
    )
    if usage:
        return ApiResponse(code=200, message="获取成功", data=MeterUsageOut.model_validate(usage))

    amount = random_usage_for_type(type)
    usage = MeterUsage(
        house_no=house_no,
        type=type,
        month=month,
        usage_amount=amount,
    )
    try:
        db.add(usage)
        db.commit()
        db.refresh(usage)
    except IntegrityError:
        db.rollback()
        usage = (
            db.query(MeterUsage)
            .filter(
                MeterUsage.house_no == house_no,
                MeterUsage.type == type,
                MeterUsage.month == month,
            )
            .first()
        )

    return ApiResponse(code=200, message="获取成功", data=MeterUsageOut.model_validate(usage))
