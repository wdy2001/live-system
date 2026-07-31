from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models import User
from app.schemas.common import ApiResponse
from app.schemas.user import Login, Token, UserCreate, UserOut

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/register", response_model=ApiResponse[UserOut])
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == user_in.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="用户名已存在")
    user = User(
        username=user_in.username,
        password_hash=hash_password(user_in.password),
        full_name=user_in.full_name,
        phone=user_in.phone,
        address=user_in.address,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return ApiResponse(code=200, message="注册成功", data=UserOut.model_validate(user))


async def _get_form_or_none(request: Request) -> Optional[tuple[str, str]]:
    if request.headers.get("content-type", "").startswith("application/x-www-form-urlencoded"):
        try:
            form = await request.form()
            username = form.get("username")
            password = form.get("password")
            if username and password:
                return username, password
        except Exception:
            return None
    return None


async def _resolve_login_credentials(
    request: Request,
    login_data: Optional[Login] = None,
):
    if login_data is not None:
        return login_data.username, login_data.password
    form_creds = await _get_form_or_none(request)
    if form_creds is not None:
        return form_creds
    raise HTTPException(status_code=400, detail="缺少登录凭证")


@router.post("/login", response_model=ApiResponse[Token])
async def login(
    request: Request,
    login_data: Optional[Login] = None,
    db: Session = Depends(get_db),
):
    username, password = await _resolve_login_credentials(request, login_data)
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.id})
    return ApiResponse(code=200, message="登录成功", data=Token(access_token=access_token, token_type="bearer"))
