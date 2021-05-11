import dataclasses
import sqlite3
from datetime import datetime
from hashlib import sha512
from typing import List, Optional

from fastapi import Cookie, FastAPI, HTTPException, Request, Response, Depends
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.responses import JSONResponse, PlainTextResponse, RedirectResponse
from starlette.templating import Jinja2Templates

app = FastAPI()
app.db_connection = None


@app.on_event("startup")
async def startup():
    app.db_connection = sqlite3.connect("northwind.db")
    app.db_connection.text_factory = lambda b: b.decode(errors="ignore")  # northwind specific


@app.on_event("shutdown")
async def shutdown():
    app.db_connection.close()


@app.get("/categories")
async def list_categories():
    categories = app.db_connection.execute(
        "SELECT CategoryID, CategoryName FROM Categories ORDER BY CategoryID").fetchall()
    return {"categories": [{"id": c[0], "name": c[1]} for c in categories]}


@app.get("/customers")
async def list_customers():
    customers = app.db_connection.execute(
        "SELECT * FROM Customers ORDER BY CustomerID").fetchall()
    return {"customers": customers}


@app.get("/auth")
def auth(password='', password_hash=''):
    print(sha512(str(password).encode('utf-8')).__str__())
    if password != '' and password_hash != '' and sha512(str(password).encode('utf-8')).hexdigest() == password_hash:
        return JSONResponse(status_code=204)
    else:
        return JSONResponse(status_code=401)


@dataclasses.dataclass
class Appointment:
    id: int
    name: str
    surname: str
    register_date: str
    vaccination_date: str


appointments: List[Appointment] = []


@app.post("/register", status_code=201)
async def register(req: Request):
    json = await req.json()
    print(json)
    name_ = json['name']
    surname_ = json['surname']
    if type(name_) is str and type(surname_) is str:
        delta = sum(c.isalpha() for c in name_ + surname_)
        appointment = Appointment(
            id=max([appointment.id for appointment in appointments]) + 1 if appointments else 1,
            name=name_,
            surname=surname_,
            register_date=datetime.date.today().isoformat(),
            vaccination_date=(datetime.date.today() + datetime.timedelta(days=delta)).isoformat())
        appointments.append(appointment)
        return appointment
    else:
        return JSONResponse(status_code=400)


@app.get("/patient/{id}")
def patient(id: int):
    if id < 1:
        return JSONResponse(status_code=400)
    appointment = list(filter(lambda a: a.id == id, appointments))
    if appointment:
        return appointment[0]
    else:
        return JSONResponse(status_code=404)


# week 3
# 3.1
templates = Jinja2Templates(directory="templates")


@app.get("/hello", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse("hello.html", {"request": request, "date_str": datetime.date.today().isoformat()})


# 3.2

security = HTTPBasic()
username = "4dm1n"
password = "NotSoSecurePa$$"

app.authorized_sessions = []
app.authorized_tokens = []


@app.post("/login_session", status_code=201)
def login_session(response: Response, credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username == username and credentials.password == password:
        new_session = f'{username}:{password}:{datetime.datetime.now()}'
        app.authorized_sessions.append(new_session)
        if len(app.authorized_sessions) > 3:
            app.authorized_sessions.pop(0)
        response.set_cookie(key="session_token", value=new_session)
        return "logged in"
    else:
        raise HTTPException(401, "Invalid creds")


@app.post("/login_token", status_code=201)
def login_token(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username == username and credentials.password == password:
        new_token = f'{username}:{password}:{datetime.datetime.now()}'
        app.authorized_tokens.append(new_token)
        if len(app.authorized_tokens) > 3:
            app.authorized_tokens.pop(0)
        return {"token": new_token}
    else:
        raise HTTPException(401, "Invalid creds")


# 3.3

@app.get("/welcome_session")
def welcome_session(format: Optional[str] = None, session_token: Optional[str] = Cookie(None)):
    if session_token and session_token in app.authorized_sessions:
        if format == "json":
            return {"message": "Welcome!"}
        elif format == "html":
            return HTMLResponse(content="<h1>Welcome!</h1>")
        else:
            return PlainTextResponse("Welcome!")
    raise HTTPException(401, "Not authorized")


@app.get("/welcome_token")
def welcome_token(format: Optional[str] = None, token: Optional[str] = None):
    if token and token in app.authorized_tokens:
        if format == "json":
            return {"message": "Welcome!"}
        elif format == "html":
            return HTMLResponse(content="<h1>Welcome!</h1>")
        else:
            return PlainTextResponse("Welcome!")
    raise HTTPException(401, "Not authorized")


# 3.4

@app.delete("/logout_session")
def logout_session(format: Optional[str] = None, session_token: Optional[str] = Cookie(None)):
    if session_token and session_token in app.authorized_sessions:
        app.authorized_sessions.remove(session_token)
        return RedirectResponse(f"/logged_out?format={format}", status_code=303)
    else:
        raise HTTPException(401, "Not authorized")


@app.delete("/logout_token")
def logout_token(format: Optional[str] = None, token: Optional[str] = None):
    if token and token in app.authorized_tokens:
        app.authorized_tokens.remove(token)
        return RedirectResponse(f"/logged_out?format={format}", status_code=303)
    else:
        raise HTTPException(401, "Not authorized")


@app.get("/logged_out")
def logged_out(format: Optional[str] = None):
    if format == "json":
        return {"message": "Logged out!"}
    elif format == "html":
        return HTMLResponse(content="<h1>Logged out!</h1>")
    else:
        return PlainTextResponse("Logged out!")
