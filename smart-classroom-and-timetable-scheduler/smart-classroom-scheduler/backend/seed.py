from __future__ import annotations
from sqlalchemy.orm import Session
from .db import engine, Base
from .models import Teacher, Subject, TeacherSubject, ClassGroup, Room, TimeSlot, SubjectRequirement

def run():
    Base.metadata.create_all(bind=engine)
    from .db import SessionLocal
    db: Session = SessionLocal()

    # Only seed if empty
    if db.query(Teacher).count() > 0:
        db.close()
        return

    # Teachers
    t1 = Teacher(name="Anita Sen")
    t2 = Teacher(name="Rahul Mehta")
    t3 = Teacher(name="Joseph D")
    db.add_all([t1, t2, t3])

    # Subjects
    s_math = Subject(name="Mathematics")
    s_sci = Subject(name="Science")
    s_eng = Subject(name="English")
    s_hist = Subject(name="History")
    db.add_all([s_math, s_sci, s_eng, s_hist])
    db.flush()

    # Teacher qualifications
    db.add_all([
        TeacherSubject(teacher=t1, subject=s_math),
        TeacherSubject(teacher=t2, subject=s_sci),
        TeacherSubject(teacher=t3, subject=s_eng),
        TeacherSubject(teacher=t2, subject=s_hist),
    ])

    # Class groups
    c1 = ClassGroup(name="Grade 8 - A", size=28)
    c2 = ClassGroup(name="Grade 8 - B", size=30)
    db.add_all([c1, c2])

    # Rooms
    r1 = Room(name="Room 101", capacity=30, has_projector=True)
    r2 = Room(name="Room 102", capacity=32, has_smart_board=True)
    db.add_all([r1, r2])

    # TimeSlots: 5 days x 6 periods
    labels = ["09:00-09:45","09:50-10:35","10:40-11:25","11:35-12:20","13:10-13:55","14:00-14:45"]
    for d in range(5):  # Mon..Fri
        for i, lbl in enumerate(labels):
            db.add(TimeSlot(day=d, slot=i, label=lbl))

    db.flush()

    # Subject requirements per class (periods per week)
    # Keep small/easy for prototype
    def req(c, s, n): db.add(SubjectRequirement(class_id=c.id, subject_id=s.id, periods_per_week=n))

    req(c1, s_math, 5)
    req(c1, s_sci, 4)
    req(c1, s_eng, 4)
    req(c1, s_hist, 3)

    req(c2, s_math, 5)
    req(c2, s_sci, 4)
    req(c2, s_eng, 4)
    req(c2, s_hist, 3)

    db.commit()
    db.close()

if __name__ == "__main__":
    run()
