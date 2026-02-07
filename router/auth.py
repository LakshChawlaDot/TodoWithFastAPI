from datetime import timedelta, datetime, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette import status
from ..database import SessionLocal
from ..models import Users
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

router = APIRouter(
    prefix='/auth',
    tags=['auth']
)

SECRET_KEY = '197b2c37c391bed93fe80344fe73b806947a65e36206e05a1a23c2fa12702fe3'
ALGORITHM = 'HS256'

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')


class CreateUserRequest(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    password: str
    role: str
    phone_number: str


class Token(BaseModel):
    access_token: str
    token_type: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]

templates = Jinja2Templates(directory="TODOapp/templates")


### Pages ###

@router.post("/login")
async def login(request: Request, db: db_dependency):
    try:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        user = authenticate_user(username, password, db)
        if not user:
            msg = "Incorrect username or password"
            return templates.TemplateResponse("login.html", {"request": request, "msg": msg})

        token = create_access_token(user.username, user.id, user.role, timedelta(minutes=20))

        response = RedirectResponse(url="/todos/todo-page", status_code=status.HTTP_302_FOUND)
        response.set_cookie(key="access_token", value=token, httponly=True)

        return response

    except Exception as e:
        msg = "Unknown error"
        return templates.TemplateResponse("login.html", {"request": request, "msg": msg})


@router.post("/register")
async def register_user(request: Request, db: db_dependency):
    try:
        form = await request.form()

        # Check if passwords match
        if form.get("password") != form.get("password2"):
            msg = "Passwords do not match"
            return templates.TemplateResponse("register.html", {"request": request, "msg": msg})

        # Check if username already exists
        existing_user = db.query(Users).filter(Users.username == form.get("username")).first()
        if existing_user:
            msg = "Username already exists"
            return templates.TemplateResponse("register.html", {"request": request, "msg": msg})

        # Check if email already exists
        existing_email = db.query(Users).filter(Users.email == form.get("email")).first()
        if existing_email:
            msg = "Email already registered"
            return templates.TemplateResponse("register.html", {"request": request, "msg": msg})

        # Create new user
        create_user_model = Users(
            email=form.get("email"),
            username=form.get("username"),
            first_name=form.get("firstname"),
            last_name=form.get("lastname"),
            role=form.get("role"),
            hashed_password=bcrypt_context.hash(form.get("password")),
            is_active=True,
            phone_number=form.get("phone")
        )

        db.add(create_user_model)
        db.commit()

        msg = "User created successfully! Please login."
        return templates.TemplateResponse("login.html", {"request": request, "msg": msg})

    except Exception as e:
        msg = f"Error creating user: {str(e)}"
        return templates.TemplateResponse("register.html", {"request": request, "msg": msg})

@router.get("/login-page")
def render_login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/register-page")
def render_register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

### Endpoints ###
def authenticate_user(username: str, password: str, db):
    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user


def create_access_token(username: str, user_id: int, role: str, expires_delta: timedelta):
    encode = {'sub': username, 'id': user_id, 'role': role}
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({'exp': expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        user_id: int = payload.get('id')
        user_role: str = payload.get('role')
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail='Could not validate user.')
        return {'username': username, 'id': user_id, 'user_role': user_role}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Could not validate user.')


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency,
                      create_user_request: CreateUserRequest):
    create_user_model = Users(
        email=create_user_request.email,
        username=create_user_request.username,
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        role=create_user_request.role,
        hashed_password=bcrypt_context.hash(create_user_request.password),
        is_active=True,
        phone_number=create_user_request.phone_number
    )

    db.add(create_user_model)
    db.commit()


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                                 db: db_dependency):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Could not validate user.')
    token = create_access_token(user.username, user.id, user.role, timedelta(minutes=20))

    return {'access_token': token, 'token_type': 'bearer'}







