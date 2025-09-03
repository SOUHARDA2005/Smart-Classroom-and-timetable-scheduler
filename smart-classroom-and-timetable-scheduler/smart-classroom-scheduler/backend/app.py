from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from .db import get_db, Base, engine
from .models import Teacher, Subject, TeacherSubject, ClassGroup, Room, TimeSlot, SubjectRequirement, Assignment
from .scheduler import generate_schedule
from . import seed

app = FastAPI(title="Smart Classroom & Timetable Scheduler")

# Initialize DB and seed on startup
@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    seed.run()

# Serve frontend (static) from /
app.mount("/", StaticFiles(directory="../frontend", html=True), name="static")

# ---------- Schemas ----------
class TeacherOut(BaseModel):
    id: int
    name: str
    class Config:
        from_attributes = True

class SubjectOut(BaseModel):
    id: int
    name: str
    class Config:
        from_attributes = True

class ClassGroupOut(BaseModel):
    id: int
    name: str
    size: int
    class Config:
        from_attributes = True

class RoomOut(BaseModel):
    id: int
    name: str
    capacity: int
    has_projector: bool
    has_smart_board: bool
    class Config:
        from_attributes = True

class TimeSlotOut(BaseModel):
    id: int
    day: int
    slot: int
    label: str
    class Config:
        from_attributes = True

class AssignmentOut(BaseModel):
    id: int
    class_id: int
    timeslot_id: int
    subject_id: int
    teacher_id: int
    room_id: int
    class Config:
        from_attributes = True

class OverrideIn(BaseModel):
    class_id: int
    day: int
    slot: int
    subject_id: int
    teacher_id: int
    room_id: int

# ---------- API ----------
@app.get("/api/teachers", response_model=List[TeacherOut])
def get_teachers(db: Session = Depends(get_db)):
    return db.query(Teacher).all()

@app.get("/api/subjects", response_model=List[SubjectOut])
def get_subjects(db: Session = Depends(get_db)):
    return db.query(Subject).all()

@app.get("/api/classes", response_model=List[ClassGroupOut])
def get_classes(db: Session = Depends(get_db)):
    return db.query(ClassGroup).all()

@app.get("/api/rooms", response_model=List[RoomOut])
def get_rooms(db: Session = Depends(get_db)):
    return db.query(Room).all()

@app.get("/api/timeslots", response_model=List[TimeSlotOut])
def get_timeslots(db: Session = Depends(get_db)):
    return db.query(TimeSlot).order_by(TimeSlot.day, TimeSlot.slot).all()

@app.get("/api/requirements")
def get_requirements(db: Session = Depends(get_db)):
    rows = db.query(SubjectRequirement).all()
    out = []
    for r in rows:
        out.append({
            "id": r.id,
            "class_id": r.class_id,
            "subject_id": r.subject_id,
            "periods_per_week": r.periods_per_week
        })
    return out

@app.post("/api/schedule/generate")
def post_generate(db: Session = Depends(get_db)):
    stats = generate_schedule(db)
    return {"status": "ok", "stats": stats}

@app.get("/api/schedule")
def get_schedule(class_id: Optional[int] = None, db: Session = Depends(get_db)):
    # Return schedule as: { class_id: { (day,slot): {subject, teacher, room} } }
    q = db.query(Assignment, TimeSlot, Subject, Teacher, Room)         .join(TimeSlot, Assignment.timeslot_id == TimeSlot.id)         .join(Subject, Assignment.subject_id == Subject.id)         .join(Teacher, Assignment.teacher_id == Teacher.id)         .join(Room, Assignment.room_id == Room.id)

    if class_id is not None:
        q = q.filter(Assignment.class_id == class_id)

    data = {}
    for a, ts, s, t, r in q.all():
        key = a.class_id
        if key not in data:
            data[key] = {}
        data[key][(ts.day, ts.slot)] = {
            "assignment_id": a.id,
            "subject_id": s.id, "subject": s.name,
            "teacher_id": t.id, "teacher": t.name,
            "room_id": r.id, "room": r.name,
            "label": ts.label
        }
    return data

@app.post("/api/schedule/clear")
def clear_schedule(db: Session = Depends(get_db)):
    db.query(Assignment).delete()
    db.commit()
    return {"status": "ok"}

@app.post("/api/schedule/override")
def override_slot(payload: OverrideIn, db: Session = Depends(get_db)):
    # resolve timeslot_id
    ts = db.query(TimeSlot).filter(TimeSlot.day == payload.day, TimeSlot.slot == payload.slot).first()
    if not ts:
        raise HTTPException(status_code=400, detail="Invalid day/slot")

    # conflict checks
    # class conflict
    existing_for_class = db.query(Assignment)         .filter(Assignment.class_id == payload.class_id, Assignment.timeslot_id == ts.id)     .first()
    if existing_for_class:
        db.delete(existing_for_class)
        db.commit()

    # teacher conflict
    t_conflict = db.query(Assignment)        .filter(Assignment.teacher_id == payload.teacher_id, Assignment.timeslot_id == ts.id).first()
    if t_conflict:
        raise HTTPException(status_code=409, detail="Teacher already booked in this slot.")

    # room conflict
    r_conflict = db.query(Assignment)         .filter(Assignment.room_id == payload.room_id, Assignment.timeslot_id == ts.id).first()
    if r_conflict:
        raise HTTPException(status_code=409, detail="Room already booked in this slot.")

    # insert
    a = Assignment(
        class_id=payload.class_id,
        timeslot_id=ts.id,
        subject_id=payload.subject_id,
        teacher_id=payload.teacher_id,
        room_id=payload.room_id
    )
    db.add(a)
    db.commit()
    db.refresh(a)
    return {"status": "ok", "assignment_id": a.id}
