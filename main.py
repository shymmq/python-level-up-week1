import dataclasses
import datetime
from hashlib import sha512
from typing import List

from fastapi import FastAPI, Request
from fastapi.params import Depends
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException
from starlette.responses import HTMLResponse, Response
from fastapi.security import HTTPBasic, HTTPBasicCredentials

app = FastAPI()


# week 1

@app.get("/")
def hello_world():
    return {"message": "Hello world!"}


@app.get("/method")
def method():
    return {"method": "GET"}


@app.post("/method", status_code=201)
def method():
    return {"method": "POST"}


@app.put("/method")
def method():
    return {"method": "PUT"}


@app.options("/method")
def method():
    return {"method": "OPTIONS"}


@app.delete("/method")
def method():
    return {"method": "DELETE"}


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


@app.post("/login_session", status_code=201)
async def login_session(response: Response, credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username == username and credentials.password == password:
        response.set_cookie(key="session_token", value=f'{username}:{password}:{datetime.datetime.now()}')
        return "logged in"
    else:
        raise HTTPException(401, "Invalid creds")


@app.post("/login_token", status_code=201)
async def login_token(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username == username and credentials.password == password:
        return {"token": f'{username}:{password}:{datetime.datetime.now()}'}
    else:
        raise HTTPException(401, "Invalid creds")
