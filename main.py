import dataclasses
import datetime
from hashlib import sha512
from typing import List

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()


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
        appointment = Appointment(
            id=max([appointment.id for appointment in appointments]) + 1 if appointments else 1,
            name=name_,
            surname=surname_,
            register_date=datetime.date.today().isoformat(),
            vaccination_date=(datetime.date.today() + datetime.timedelta(
                days=(len(name_) + len(surname_)))).isoformat())
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
