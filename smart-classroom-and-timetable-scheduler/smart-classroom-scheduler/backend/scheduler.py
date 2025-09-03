from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from sqlalchemy.orm import Session
from collections import defaultdict
import random

# Changed from .models import to models import
from models import (
    Teacher, Subject, TeacherSubject, ClassGroup, Room, TimeSlot,
    SubjectRequirement, Assignment
)

@dataclass
class Task:
    class_id: int
    subject_id: int
    remaining: int

def generate_schedule(db: Session) -> Dict[str, List[str]]:
    # Clear old assignments
    db.query(Assignment).delete()

    teachers = {t.id: t for t in db.query(Teacher).all()}
    subjects = {s.id: s for s in db.query(Subject).all()}
    classes = {c.id: c for c in db.query(ClassGroup).all()}
    rooms = sorted(db.query(Room).all(), key=lambda r: r.capacity)  # small to large
    timeslots = db.query(TimeSlot).order_by(TimeSlot.day, TimeSlot.slot).all()

    # qualifications: subject_id -> list of teacher_ids
    qual = defaultdict(list)
    for ts in db.query(TeacherSubject).all():
        qual[ts.subject_id].append(ts.teacher_id)

    # task list per class
    tasks: List[Task] = []
    reqs = db.query(SubjectRequirement).all()
    for r in reqs:
        tasks.append(Task(class_id=r.class_id, subject_id=r.subject_id, remaining=r.periods_per_week))

    # State occupancy
    teacher_busy = set()  # (teacher_id, timeslot_id)
    room_busy = set()     # (room_id, timeslot_id)
    class_busy = set()    # (class_id, timeslot_id)
    class_subject_day_count = defaultdict(lambda: defaultdict(int))  # class_id -> (day,subject) -> count

    # For simple heuristic, expand tasks into per-period items and shuffle by class
    expanded: List[Tuple[int,int]] = []  # (class_id, subject_id)
    for t in tasks:
        expanded.extend([(t.class_id, t.subject_id)] * t.remaining)

    # Spread sessions by interleaving classes and subjects
    random.seed(42)
    random.shuffle(expanded)

    # Greedy allocation over timeslots looping
    # For each timeslot, try to assign one period for each class in turn
    expanded_by_class = defaultdict(list)
    for c_id, s_id in expanded:
        expanded_by_class[c_id].append(s_id)

    success_count = 0
    for ts in timeslots:
        for c_id in classes.keys():
            if not expanded_by_class[c_id]:
                continue
            # choose a subject that we haven't taught too many times in this day to keep variety
            candidate_subjects = list(set(expanded_by_class[c_id]))
            # prefer subjects with lower count today
            candidate_subjects.sort(key=lambda sid: class_subject_day_count[(c_id, ts.day, sid)])
            placed = False
            for s_id in candidate_subjects:
                # find a qualified free teacher
                teacher_ids = qual.get(s_id, [])
                random.shuffle(teacher_ids)
                for t_id in teacher_ids:
                    if (t_id, ts.id) in teacher_busy:  # teacher conflict
                        continue
                    # find first room that fits and is free
                    for r in rooms:
                        if r.capacity < classes[c_id].size:
                            continue
                        if (r.id, ts.id) in room_busy:
                            continue
                        if (c_id, ts.id) in class_busy:
                            continue
                        # place
                        db.add(Assignment(
                            class_id=c_id,
                            timeslot_id=ts.id,
                            subject_id=s_id,
                            teacher_id=t_id,
                            room_id=r.id
                        ))
                        teacher_busy.add((t_id, ts.id))
                        room_busy.add((r.id, ts.id))
                        class_busy.add((c_id, ts.id))
                        class_subject_day_count[(c_id, ts.day, s_id)] += 1
                        # consume one from the list
                        expanded_by_class[c_id].remove(s_id)
                        placed = True
                        success_count += 1
                        break
                    if placed:
                        break
                if placed:
                    break

    db.commit()
    # Return simple stats
    total_needed = len(expanded)
    return {"placed": success_count, "needed": total_needed}
