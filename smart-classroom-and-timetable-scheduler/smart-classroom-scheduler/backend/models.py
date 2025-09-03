from .db import Base
from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Boolean, ForeignKey, UniqueConstraint
from typing import List, Optional
from .db import Base

class Teacher(Base):
    __tablename__ = "teachers"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    subjects: Mapped[list["TeacherSubject"]] = relationship(back_populates="teacher", cascade="all, delete-orphan")

class Subject(Base):
    __tablename__ = "subjects"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True)

class TeacherSubject(Base):
    __tablename__ = "teacher_subjects"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id"))
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"))
    teacher: Mapped["Teacher"] = relationship(back_populates="subjects")
    subject: Mapped["Subject"] = relationship()

    __table_args__ = (UniqueConstraint("teacher_id", "subject_id", name="uq_teacher_subject"),)

class ClassGroup(Base):
    __tablename__ = "class_groups"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    size: Mapped[int] = mapped_column(Integer, default=30)

class Room(Base):
    __tablename__ = "rooms"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    capacity: Mapped[int] = mapped_column(Integer, default=30)
    has_projector: Mapped[bool] = mapped_column(Boolean, default=False)
    has_smart_board: Mapped[bool] = mapped_column(Boolean, default=False)

class TimeSlot(Base):
    __tablename__ = "timeslots"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    day: Mapped[int] = mapped_column(Integer)   # 0=Mon ... 4=Fri
    slot: Mapped[int] = mapped_column(Integer)  # 0..N-1 within day
    label: Mapped[str] = mapped_column(String)

    __table_args__ = (UniqueConstraint("day", "slot", name="uq_day_slot"),)

class SubjectRequirement(Base):
    __tablename__ = "subject_requirements"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    class_id: Mapped[int] = mapped_column(ForeignKey("class_groups.id"))
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"))
    periods_per_week: Mapped[int] = mapped_column(Integer)

    __table_args__ = (UniqueConstraint("class_id", "subject_id", name="uq_class_subject"),)

class Assignment(Base):
    __tablename__ = "assignments"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    class_id: Mapped[int] = mapped_column(ForeignKey("class_groups.id"))
    timeslot_id: Mapped[int] = mapped_column(ForeignKey("timeslots.id"))
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"))
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id"))
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id"))

    __table_args__ = (UniqueConstraint("class_id", "timeslot_id", name="uq_class_timeslot"),)
