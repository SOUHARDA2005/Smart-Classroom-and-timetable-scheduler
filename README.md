# Smart Classroom & Timetable Scheduler (Prototype)

A minimal, unique, and **connected** web + backend app for generating conflict-free class timetables and managing smart classroom resources.

## ✨ What you get
- **FastAPI** backend with **SQLite** database (auto-seeded with demo data).
- **Simple scheduling algorithm** (pure Python; no heavy solvers).
- **Single-page web UI** with a clean glassmorphism design.
- **Generate / Clear / Override** timetable from the browser.
- API endpoints to list teachers, subjects, classes, rooms, timeslots, and schedule.

## 📦 Quickstart

```bash
# 1) Create & activate a virtual environment (recommended)
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 2) Install dependencies
pip install -r backend/requirements.txt

# 3) Run the server (serves the frontend too)
uvicorn backend.app:app --reload

# 4) Open the app
http://localhost:8000
```

> The database file `smart_classroom.db` will be created in the project root on first run and seeded with demo data.

## 🧠 Scheduler
The algorithm uses a **greedy, conflict-aware allocation**:
- Iterates across the week’s timeslots.
- For each class group, picks a subject (balancing day variety), a **qualified** free teacher, and a free room large enough for the class.
- Writes assignments to DB, avoiding conflicts (teacher/class/room double-booking).

Use **Override** to fix a specific slot if you want a different assignment; conflict checks protect against double-booking.

## 📚 API Quick Reference

- `GET /api/classes` — list classes
- `GET /api/teachers` — list teachers
- `GET /api/subjects` — list subjects
- `GET /api/rooms` — list rooms
- `GET /api/timeslots` — list timeslots
- `GET /api/requirements` — per-class weekly required periods
- `POST /api/schedule/generate` — run the scheduler
- `POST /api/schedule/clear` — remove all assignments
- `GET /api/schedule?class_id=ID` — schedule for a class
- `POST /api/schedule/override` — override a single (class, day, slot)

## 🛠 Make it your own
- Add teachers/subjects in **`backend/seed.py`** (and their qualifications in `TeacherSubject`).
- Add more classes/rooms and adjust **`SubjectRequirement`** per class (weekly periods).
- Change periods per day in `seed.py` to match your institute.
- Style tweaks in **`frontend/styles.css`**.

## 🚀 Roadmap ideas
- True **CSP/ILP** solver (e.g., OR-Tools) for optimality.
- Teacher availability windows and soft constraints (free periods, lab requirements).
- Drag-n-drop UI with undo/redo.
- Export to **PDF/Excel/ICS** calendar.
- Authentication/roles (Admin/Teacher/Student).

---

Built as a learning-friendly base you can extend quickly. Enjoy!

