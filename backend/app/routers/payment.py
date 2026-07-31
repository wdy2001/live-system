import random
from datetime import datetime, date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.billing import calculate_bill, random_usage_for_type
from app.core.deps import get_db, get_current_user
from app.models import MeterUsage, PaymentOrder, BillDetail, User
from app.schemas.common import ApiResponse, PageData
from app.schemas.payment import (
    PaymentQuery,
    PaymentQueryResultOut,
    BillOut,
    PaymentPay,
    PaymentPayResultOut,
    PaymentOrderOut,
    PaymentOrderWithBillOut,
)

router = APIRouter(prefix="/api/payments", tags=["缴费"], dependencies=[Depends(get_current_user)])


def _gen_order_no() -> str:
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    rnd = "".join(random.choices("0123456789", k=6))
    return f"PAY{ts}{rnd}"


def _get_or_create_meter_usage(db: Session, house_no: str, type_: str, month: str) -> MeterUsage:
    usage = (
        db.query(MeterUsage)
        .filter(
            MeterUsage.house_no == house_no,
            MeterUsage.type == type_,
            MeterUsage.month == month,
        )
        .first()
    )
    if usage:
        return usage
    amount = random_usage_for_type(type_)
    usage = MeterUsage(
        house_no=house_no,
        type=type_,
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
                MeterUsage.type == type_,
                MeterUsage.month == month,
            )
            .first()
        )
    return usage


def _merge_bill_summary(bill: dict) -> str:
    lines = []
    for t in bill.get("tier_items", []):
        lines.append(
            f"{t['tier_min']}-{t['tier_max'] if t['tier_max'] else '∞'}: "
            f"{t['usage']}*{t['unit_price']}={t['subtotal']}"
        )
    for e in bill.get("extra_items", []):
        lines.append(f"{e['name']}: {e['usage']}*{e['rate']}={e['subtotal']}")
    lines.append(f"合计: {bill.get('total')}")
    return "; ".join(lines)


@router.post("/query", response_model=ApiResponse[PaymentQueryResultOut])
def query_bill(
    query_in: PaymentQuery,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    month = query_in.month or datetime.now().strftime("%Y-%m")

    meter_usage = _get_or_create_meter_usage(db, query_in.house_no, query_in.type, month)
    usage_amount = meter_usage.usage_amount or 0
    bill = calculate_bill(db, query_in.type, usage_amount)

    order = (
        db.query(PaymentOrder)
        .filter(
            PaymentOrder.user_id == current_user.id,
            PaymentOrder.house_no == query_in.house_no,
            PaymentOrder.type == query_in.type,
            PaymentOrder.month == month,
            PaymentOrder.status.in_(["unpaid", "paid"]),
        )
        .first()
    )

    if not order:
        order_no = _gen_order_no()
        order = PaymentOrder(
            order_no=order_no,
            user_id=current_user.id,
            house_no=query_in.house_no,
            type=query_in.type,
            month=month,
            total_amount=bill["total"],
            status="unpaid",
        )
        db.add(order)
        db.flush()

        bill_detail = BillDetail(
            order_id=order.id,
            base_total=bill["base_total"],
            extra_fee=bill["extra_fee"],
            tier_items=jsonable_encoder(bill["tier_items"]),
            extra_items=jsonable_encoder(bill["extra_items"]),
            summary=_merge_bill_summary(bill),
        )
        db.add(bill_detail)
        db.commit()
        db.refresh(order)
    else:
        if not order.bill_detail:
            bill_detail = BillDetail(
                order_id=order.id,
                base_total=bill["base_total"],
                extra_fee=bill["extra_fee"],
                tier_items=jsonable_encoder(bill["tier_items"]),
                extra_items=jsonable_encoder(bill["extra_items"]),
                summary=_merge_bill_summary(bill),
            )
            db.add(bill_detail)
            db.commit()
            db.refresh(order)
        else:
            bd = order.bill_detail
            bill = {
                "tier_items": bd.tier_items or [],
                "base_total": bd.base_total or 0,
                "extra_items": bd.extra_items or [],
                "extra_fee": bd.extra_fee or 0,
                "total": order.total_amount or 0,
            }

    bill_out = BillOut(**bill)
    result = PaymentQueryResultOut(
        order_id=order.id,
        order_no=order.order_no,
        house_no=order.house_no or query_in.house_no,
        type=order.type or query_in.type,
        month=order.month or month,
        total_amount=order.total_amount or bill["total"],
        status=order.status,
        bill=bill_out,
    )
    return ApiResponse(code=200, message="查询成功", data=result)


@router.post("/pay", response_model=ApiResponse[PaymentPayResultOut])
def pay_order(
    pay_in: PaymentPay,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = db.query(PaymentOrder).filter(PaymentOrder.id == pay_in.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作该订单")

    if order.status == "paid":
        return ApiResponse(
            code=200,
            message="订单已缴费",
            data=PaymentPayResultOut(
                success=True,
                order_id=order.id,
                paid_at=order.paid_at,
                total_amount=order.total_amount,
                already_paid=True,
            ),
        )

    order.status = "paid"
    order.paid_at = datetime.utcnow()
    db.commit()
    db.refresh(order)

    return ApiResponse(
        code=200,
        message="缴费成功",
        data=PaymentPayResultOut(
            success=True,
            order_id=order.id,
            paid_at=order.paid_at,
            total_amount=order.total_amount,
            already_paid=False,
        ),
    )


@router.get("/{order_id}", response_model=ApiResponse[PaymentOrderWithBillOut])
def get_order_detail(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = db.query(PaymentOrder).filter(PaymentOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权查看该订单")

    data = PaymentOrderWithBillOut(
        id=order.id,
        order_no=order.order_no,
        user_id=order.user_id,
        house_no=order.house_no,
        type=order.type,
        month=order.month,
        total_amount=order.total_amount,
        status=order.status,
        created_at=order.created_at,
        paid_at=order.paid_at,
        base_total=order.bill_detail.base_total if order.bill_detail else None,
        extra_fee=order.bill_detail.extra_fee if order.bill_detail else None,
        tier_items=order.bill_detail.tier_items if order.bill_detail else None,
        extra_items=order.bill_detail.extra_items if order.bill_detail else None,
        summary=order.bill_detail.summary if order.bill_detail else None,
    )
    return ApiResponse(code=200, message="获取成功", data=data)


@router.get("/", response_model=ApiResponse[PageData[PaymentOrderWithBillOut]])
def list_orders(
    type: str = Query("all", description="all/electric/water/gas"),
    status: str = Query("all", description="all/unpaid/paid/overdue"),
    start_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(PaymentOrder).filter(PaymentOrder.user_id == current_user.id)

    if type and type != "all":
        query = query.filter(PaymentOrder.type == type)
    if status and status != "all":
        query = query.filter(PaymentOrder.status == status)
    if start_date:
        start_dt = datetime.combine(date.fromisoformat(start_date), datetime.min.time())
        query = query.filter(PaymentOrder.created_at >= start_dt)
    if end_date:
        end_dt = datetime.combine(date.fromisoformat(end_date), datetime.max.time())
        query = query.filter(PaymentOrder.created_at <= end_dt)

    total = query.count()
    items = (
        query.order_by(PaymentOrder.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    out_items = []
    for order in items:
        out_items.append(
            PaymentOrderWithBillOut(
                id=order.id,
                order_no=order.order_no,
                user_id=order.user_id,
                house_no=order.house_no,
                type=order.type,
                month=order.month,
                total_amount=order.total_amount,
                status=order.status,
                created_at=order.created_at,
                paid_at=order.paid_at,
                base_total=order.bill_detail.base_total if order.bill_detail else None,
                extra_fee=order.bill_detail.extra_fee if order.bill_detail else None,
                tier_items=order.bill_detail.tier_items if order.bill_detail else None,
                extra_items=order.bill_detail.extra_items if order.bill_detail else None,
                summary=order.bill_detail.summary if order.bill_detail else None,
            )
        )

    page_data = PageData(items=out_items, total=total, page=page, page_size=page_size)
    return ApiResponse(code=200, message="获取成功", data=page_data)
