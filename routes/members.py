from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models import Member, Payment, Setting
from schemas import MemberCreate, MemberResponse, PaymentCreate, PaymentResponse
from database import get_db

router = APIRouter(prefix="/api/members", tags=["Members"])


# --- Get all members ---
@router.get("/", response_model=list[MemberResponse])
def get_members(db: Session = Depends(get_db)):
    members = db.query(Member).order_by(Member.created_at.desc()).all()
    return members


# --- Get single member ---
@router.get("/{member_id}", response_model=MemberResponse)
def get_member(member_id: int, db: Session = Depends(get_db)):
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return member


# --- Add a new member ---
@router.post("/", response_model=MemberResponse)
def add_member(data: MemberCreate, db: Session = Depends(get_db)):
    # Check duplicate name (case-insensitive)
    existing = db.query(Member).filter(Member.name.ilike(data.name.strip())).first()
    if existing:
        raise HTTPException(status_code=400, detail="A member with this name already exists")

    # Get target from settings
    setting = db.query(Setting).filter(Setting.key == "target").first()
    target = float(setting.value) if setting else 130000

    # Calculate remaining based on total members
    total_members = db.query(Member).count() + 1
    per_member = round(target / total_members)

    # Recalculate remaining for all existing members
    all_members = db.query(Member).all()
    for m in all_members:
        m.remaining = max(per_member - m.total_paid, 0)

    # Create new member
    new_member = Member(
        name=data.name.strip(),
        phone=data.phone.strip() if data.phone else None,
        total_paid=0.0,
        remaining=per_member,
    )
    db.add(new_member)
    db.commit()
    db.refresh(new_member)
    return new_member


# --- Delete a member ---
@router.delete("/{member_id}")
def delete_member(member_id: int, db: Session = Depends(get_db)):
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    # Delete member's payments first
    db.query(Payment).filter(Payment.member_id == member_id).delete()

    # Delete member
    db.delete(member)

    # Recalculate remaining for all remaining members
    setting = db.query(Setting).filter(Setting.key == "target").first()
    target = float(setting.value) if setting else 130000
    total_members = db.query(Member).count()
    if total_members > 0:
        per_member = round(target / total_members)
        all_members = db.query(Member).all()
        for m in all_members:
            m.remaining = max(per_member - m.total_paid, 0)

    db.commit()
    return {"message": "Member deleted successfully"}


# --- Record a payment ---
@router.post("/{member_id}/payment", response_model=PaymentResponse)
def record_payment(member_id: int, data: PaymentCreate, db: Session = Depends(get_db)):
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    # No overpayment — business rule
    if data.amount > member.remaining:
        raise HTTPException(
            status_code=400,
            detail=f"Amount exceeds remaining balance (KSH {member.remaining:,.0f})"
        )

    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than 0")

    # Create payment record
    payment = Payment(
        member_id=member_id,
        amount=data.amount,
        note=data.note,
    )
    db.add(payment)

    # Update member totals
    member.total_paid += data.amount
    member.remaining = max(member.remaining - data.amount, 0)

    db.commit()
    db.refresh(payment)
    return payment


# --- Get payment history for a member ---
@router.get("/{member_id}/payments", response_model=list[PaymentResponse])
def get_member_payments(member_id: int, db: Session = Depends(get_db)):
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    payments = db.query(Payment).filter(Payment.member_id == member_id).order_by(Payment.date.desc()).all()
    return payments