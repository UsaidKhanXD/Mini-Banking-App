from pathlib import Path
from fastapi import Cookie, Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from database import Base,get_db,engine
import models

Base.metadata.create_all(bind=engine)

app = FastAPI()

templates = Jinja2Templates(directory="templates")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
TEMPLATE_DIR = Path(__file__).parent / "templates"


# --- Page Serving Routes ---
@app.get("/register", response_class=HTMLResponse)
def serve_register_page():
  return (TEMPLATE_DIR / "register.html").read_text(encoding="utf-8")


@app.get("/login", response_class=HTMLResponse)
def serve_login_page():
  return (TEMPLATE_DIR / "login.html").read_text(encoding="utf-8")


@app.get("/", response_class=HTMLResponse)
def serve_root():
  return (TEMPLATE_DIR / "login.html").read_text(encoding="utf-8")


# --- Register API Endpoint ---
@app.post("/register")
def signuppage(
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
  existing_email = (
      db.query(models.User).filter(models.User.email == email).first()
  )
  if existing_email:
    raise HTTPException(
        status_code=400, detail="Email is already registered!"
    )

  existing_name = db.query(models.User).filter(models.User.name == name).first()
  if existing_name:
    raise HTTPException(status_code=400, detail="Username is already taken!")

  hashed_password = pwd_context.hash(password)
  new_user = models.User(
      name=name, email=email, password=hashed_password, balance=0.0
  )
  db.add(new_user)
  db.commit()
  db.refresh(new_user)

  return RedirectResponse(url="/login", status_code=303)


# --- Login API Endpoint ---
@app.post("/login")
def login(
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
  db_user = db.query(models.User).filter(models.User.email == email).first()
  if not db_user:
    raise HTTPException(status_code=400, detail="Invalid email or password!")

  is_password_valid = pwd_context.verify(password, db_user.password)
  if not is_password_valid:
    raise HTTPException(status_code=400, detail="Invalid email or password!")

  response = RedirectResponse(url="/dashboard", status_code=303)
  response.set_cookie(key="user_email", value=db_user.email)
  return response


# --- Dashboard Route (GET) ---
# --- Dashboard Route (GET) ---
@app.get("/dashboard", response_class=HTMLResponse)
def serve_dashboard_page(
    request: Request,
    user_email: str = Cookie(None),
    db: Session = Depends(get_db),
):
  if not user_email:
    return RedirectResponse(url="/login", status_code=303)

  user = db.query(models.User).filter(models.User.email == user_email).first()
  if not user:
    return RedirectResponse(url="/login", status_code=303)

  # Fixed: Use explicit keyword arguments (request=request, context=...)
  return templates.TemplateResponse(
      request=request, name="main.html", context={"user": user}
  )

@app.post("/deposit")
def deposit(
    amount: float = Form(...),
    user_email: str = Cookie(None),
    db: Session = Depends(get_db),
):
  if not user_email:
    return RedirectResponse(url="/login", status_code=303)

  user = db.query(models.User).filter(models.User.email == user_email).first()
  if user and amount > 0:
    user.balance += amount
    statement = f"-${amount} has been added in your balance<br>"
    user.deposit_history += statement
    db.commit()
  
  return RedirectResponse(url="/dashboard", status_code=303)


@app.post("/withdraw")
def withdraw(
    amount: float = Form(...),
    user_email: str = Cookie(None),
    db: Session = Depends(get_db),
):
  if not user_email:
    return RedirectResponse(url="/login", status_code=303)

  # Fixed: changed models.UserDB to models.User
  user = db.query(models.User).filter(models.User.email == user_email).first()
  if user and 0 < amount <= user.balance:
    user.balance -= amount
    statement = f"-${amount} has been deducted from your balance<br>"
    user.withdraw_history += statement
    db.commit()

  return RedirectResponse(url="/dashboard", status_code=303)

@app.get("/history", response_class=HTMLResponse)
def serve_history_page(request: Request,user_email: str = Cookie(None),db: Session = Depends(get_db),):
  if not user_email:
    return RedirectResponse(url="/login", status_code=303)
  user = db.query(models.User).filter(models.User.email == user_email).first()
  if not user:
    return RedirectResponse(url="/login", status_code=303)
  return templates.TemplateResponse(
      request=request, name="history.html", context={"user": user}
  )