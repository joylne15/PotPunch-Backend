from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import engine, Base, get_db
from models import Member, Payment, Setting
from schemas import SettingUpdate, SettingResponse
from routes.members import router as members_router

# Create all tables in the database
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Money Collection API", version="1.0")

# CORS — allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include member routes
app.include_router(members_router)


# --- Settings endpoints ---

@app.get("/api/settings", response_model=list[SettingResponse])
def get_settings(db: Session = Depends(get_db)):
    return db.query(Setting).all()


@app.put("/api/settings")
def update_setting(data: SettingUpdate, db: Session = Depends(get_db)):
    setting = db.query(Setting).filter(Setting.key == data.key).first()
    if setting:
        setting.value = data.value
    else:
        setting = Setting(key=data.key, value=data.value)
        db.add(setting)

    # If target changed, recalculate all members' remaining
    if data.key == "target":
        target = float(data.value)
        all_members = db.query(Member).all()
        total_members = len(all_members)
        if total_members > 0:
            per_member = round(target / total_members)
            for m in all_members:
                m.remaining = max(per_member - m.total_paid, 0)

    db.commit()
    return {"message": "Setting updated"}


# --- Dashboard stats endpoint ---

@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    members = db.query(Member).all()
    setting = db.query(Setting).filter(Setting.key == "target").first()
    target = float(setting.value) if setting else 130000

    total_collected = sum(m.total_paid for m in members)
    total_remaining = sum(m.remaining for m in members)
    total_members = len(members)
    active_members = len([m for m in members if m.total_paid > 0])
    paid_members = len([m for m in members if m.remaining <= 0])
    unpaid_members = len([m for m in members if m.total_paid == 0])
    progress_percent = round((total_collected / target) * 100, 1) if target > 0 else 0

    return {
        "totalMembers": total_members,
        "activeMembers": active_members,
        "totalCollected": total_collected,
        "totalRemaining": total_remaining,
        "paidMembers": paid_members,
        "unpaidMembers": unpaid_members,
        "progressPercent": progress_percent,
        "target": target,
    }


# --- Recent activity endpoint ---

@app.get("/api/activity")
def get_activity(db: Session = Depends(get_db)):
    activities = []

    payments = db.query(Payment).order_by(Payment.created_at.desc()).limit(10).all()
    for p in payments:
        member = db.query(Member).filter(Member.id == p.member_id).first()
        activities.append({
            "type": "payment",
            "memberName": member.name if member else "Unknown",
            "amount": p.amount,
            "note": p.note,
            "date": p.created_at.isoformat() if p.created_at else None,
        })

    activities.sort(key=lambda x: x["date"] or "", reverse=True)
    return activities[:10]


# --- Seed database with sample data ---

@app.post("/api/seed")
def seed_data(db: Session = Depends(get_db)):
    if db.query(Setting).count() == 0:
        db.add(Setting(key="target", value="130000"))

    if db.query(Member).count() == 0:
        sample_members = [
            Member(name="Alice Wanjiku", phone="+254 712 345 678", total_paid=10000, remaining=3000),
            Member(name="Brian Odhiambo", phone="+254 723 456 789", total_paid=13000, remaining=0),
            Member(name="Charity Achieng", phone="+254 734 567 890", total_paid=5000, remaining=8000),
            Member(name="David Kamau", phone="+254 745 678 901", total_paid=0, remaining=13000),
            Member(name="Esther Njoroge", phone="+254 756 789 012", total_paid=8000, remaining=5000),
            Member(name="Francis Mwangi", phone="+254 767 890 123", total_paid=11000, remaining=2000),
            Member(name="Grace Wambui", phone="+254 778 901 234", total_paid=13000, remaining=0),
            Member(name="Henry Kiprop", phone="+254 789 012 345", total_paid=2000, remaining=11000),
        ]
        db.add_all(sample_members)

    db.commit()
    return {"message": "Database seeded successfully"}