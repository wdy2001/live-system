from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models import User
from app.schemas.common import ApiResponse
from app.schemas.user import UserOut, UserUpdate

router = APIRouter(prefix="/api/users", tags=["用户"], dependencies=[Depends(get_current_user)])


@router.get("/me", response_model=ApiResponse[UserOut])
def get_me(current_user: User = Depends(get_current_user)):
    return ApiResponse(code=200, message="获取成功", data=UserOut.model_validate(current_user))


@router.put("/me", response_model=ApiResponse[UserOut])
def update_me(
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if user_in.full_name is not None:
        current_user.full_name = user_in.full_name
    if user_in.phone is not None:
        current_user.phone = user_in.phone
    if user_in.address is not None:
        current_user.address = user_in.address
    db.commit()
    db.refresh(current_user)
    return ApiResponse(code=200, message="更新成功", data=UserOut.model_validate(current_user))
