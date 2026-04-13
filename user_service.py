"""
user_service.py
---------------
Service layer untuk Credit-Based Billing system.
Menggantikan sistem subscription lama dengan pay-per-hit balance.
"""

import logging
from datetime import datetime, timezone, timedelta
from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession
from models import User, Transaction, Project, Task, Evaluation

logger = logging.getLogger(__name__)

SIGNUP_BONUS = 500  # 500 Poin bonus saldo untuk user baru


async def get_user_info(session: AsyncSession, tg_id: int) -> User | None:
    """Mengambil data user lengkap."""
    statement = select(User).where(User.user_id == tg_id)
    result = await session.execute(statement)
    return result.scalar_one_or_none()


async def register_or_get_user(
    session: AsyncSession, tg_id: int, username: str = None
) -> tuple[User, bool]:
    """
    Cek apakah user sudah terdaftar. Jika belum, registrasi otomatis
    dengan bonus saldo 500 Poin.

    Returns:
        (User, is_new) — is_new=True jika baru didaftarkan.
    """
    user = await get_user_info(session, tg_id)
    if user:
        # Update username jika berubah
        if username and user.username != username:
            user.username = username
            session.add(user)
            try:
                await session.commit()
            except Exception:
                await session.rollback()
        return user, False

    # Registrasi baru
    user = User(
        user_id=tg_id,
        username=username or f"User_{tg_id}",
        balance=SIGNUP_BONUS,
        is_registered=True,
        selected_lang="ID",
        selected_project="CHERRY_OPAL",
        selected_task="PR",
        selected_tier="BASIC",
    )
    session.add(user)

    # Log transaksi bonus
    tx = Transaction(
        user_id=tg_id,
        amount=SIGNUP_BONUS,
        type="topup",
        task_type="signup_bonus",
        model_used="",
    )
    session.add(tx)

    try:
        await session.commit()
        await session.refresh(user)
        logger.info(f"New user registered: {tg_id} ({username}), bonus={SIGNUP_BONUS}")
        return user, True
    except Exception as e:
        logger.error(f"Gagal registrasi user baru {tg_id}: {e}")
        await session.rollback()
        # Return a default object
        return User(user_id=tg_id, username=username, balance=0, is_registered=False), False


async def check_balance(session: AsyncSession, tg_id: int, price: int) -> bool:
    user = await get_user_info(session, tg_id)
    if not user:
        return False
    return user.balance >= price


async def deduct_balance(
    session: AsyncSession,
    tg_id: int,
    amount: int,
    task_type: str,
    model_used: str,
) -> int:
    """
    Potong saldo user secara atomik dan log transaksi.
    Hanya dipanggil SETELAH API call sukses.

    Returns:
        Sisa saldo setelah pemotongan.

    Raises:
        ValueError jika saldo tidak cukup.
    """
    user = await get_user_info(session, tg_id)
    if not user:
        raise ValueError("User tidak ditemukan")
        
    if user.balance < amount:
        raise ValueError(f"Saldo tidak cukup: {user.balance} < {amount}")

    user.balance -= amount
    session.add(user)

    tx = Transaction(
        user_id=tg_id,
        amount=-amount,
        type="deduction",
        task_type=task_type,
        model_used=model_used,
    )
    session.add(tx)

    try:
        await session.commit()
        await session.refresh(user)
        logger.info(f"Deducted {amount} from user {tg_id}. Remaining: {user.balance}")
        return user.balance
    except Exception as e:
        logger.error(f"Gagal deduct balance {tg_id}: {e}")
        await session.rollback()
        raise


async def deposit_balance(
    session: AsyncSession, tg_id: int, amount: int
) -> int:
    """
    Admin top-up: Tambah saldo user secara manual.

    Returns:
        Saldo baru setelah deposit.

    Raises:
        ValueError jika user tidak ditemukan.
    """
    user = await get_user_info(session, tg_id)
    if not user:
        raise ValueError(f"User dengan ID {tg_id} tidak ditemukan.")

    user.balance += amount
    session.add(user)

    tx = Transaction(
        user_id=tg_id,
        amount=amount,
        type="topup",
        task_type="admin_deposit",
        model_used="",
    )
    session.add(tx)

    try:
        await session.commit()
        await session.refresh(user)
        logger.info(f"Admin deposited {amount} to user {tg_id}. New balance: {user.balance}")
        return user.balance
    except Exception as e:
        logger.error(f"Gagal deposit untuk {tg_id}: {e}")
        await session.rollback()
        raise


async def update_language(session: AsyncSession, tg_id: int, lang: str) -> bool:
    """Update bahasa yang dipilih user."""
    user = await get_user_info(session, tg_id)
    if not user:
        return False
    user.selected_lang = lang
    session.add(user)
    try:
        await session.commit()
        return True
    except Exception as e:
        logger.error(f"Gagal update language untuk {tg_id}: {e}")
        await session.rollback()
        return False


async def update_task(session: AsyncSession, tg_id: int, task: str) -> bool:
    """Update jenis task yang dipilih user."""
    user = await get_user_info(session, tg_id)
    if not user:
        return False
    user.selected_task = task
    session.add(user)
    try:
        await session.commit()
        return True
    except Exception as e:
        logger.error(f"Gagal update task untuk {tg_id}: {e}")
        await session.rollback()
        return False


async def update_tier(session: AsyncSession, tg_id: int, tier: str) -> bool:
    """Update tier yang dipilih user (BASIC/PREMIUM)."""
    user = await get_user_info(session, tg_id)
    if not user:
        return False
    user.selected_tier = tier
    session.add(user)
    try:
        await session.commit()
        return True
    except Exception as e:
        logger.error(f"Gagal update tier untuk {tg_id}: {e}")
        await session.rollback()
        return False


async def update_project(session: AsyncSession, tg_id: int, project_code: str) -> bool:
    """Update proyek yang dipilih user."""
    user = await get_user_info(session, tg_id)
    if not user:
        return False
    user.selected_project = project_code
    session.add(user)
    try:
        await session.commit()
        return True
    except Exception as e:
        logger.error(f"Gagal update project untuk {tg_id}: {e}")
        await session.rollback()
        return False


async def get_projects(session: AsyncSession) -> list[Project]:
    """Mengambil semua proyek."""
    statement = select(Project).order_by(Project.code)
    result = await session.execute(statement)
    return result.scalars().all()


async def get_tasks_by_project(session: AsyncSession, project_code: str) -> list[Task]:
    """Mengambil semua task dalam proyek tertentu."""
    statement = select(Task).where(Task.project_code == project_code).order_by(Task.id)
    result = await session.execute(statement)
    return result.scalars().all()


async def get_stats(session: AsyncSession) -> dict:
    """
    Admin stats: total users, total saldo keseluruhan, dan total hits hari ini.
    """
    # Total users
    result = await session.execute(select(func.count(User.user_id)))
    total_users = result.scalar_one_or_none() or 0

    # Total balance
    result = await session.execute(select(func.sum(User.balance)))
    total_balance = result.scalar_one_or_none() or 0

    # Hits today (deductions)
    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    result = await session.execute(
        select(func.count(Transaction.id)).where(
            Transaction.type == "deduction",
            Transaction.timestamp >= today_start,
        )
    )
    hits_today = result.scalar_one_or_none() or 0

    return {
        "total_users": total_users,
        "total_balance": total_balance,
        "hits_today": hits_today,
    }


# ── EVALUATION & HISTORY FUNCTIONS ────────────────────────────────────────

async def add_evaluation(
    session: AsyncSession,
    user_id: int,
    task_code: str,
    user_input: str,
    ai_output: str,
) -> Evaluation:
    """Simpan evaluasi dan batasi 5 baris terakhir per user."""
    # 1. Tambah evaluasi baru
    new_eval = Evaluation(
        user_id=user_id,
        task_code=task_code,
        user_input=user_input,
        ai_output=ai_output
    )
    session.add(new_eval)

    # 2. Cleanup: hapus record lama jika sudah >= 5
    statement = (
        select(Evaluation)
        .where(Evaluation.user_id == user_id)
        .order_by(Evaluation.timestamp.desc())
    )
    result = await session.execute(statement)
    existing = result.scalars().all()
    
    if len(existing) >= 5:
        # Hapus mulai dari indeks ke-4 agar tersisa 4 lama + 1 baru = 5 total
        for old in existing[4:]:
            await session.delete(old)

    try:
        await session.commit()
        await session.refresh(new_eval)
        return new_eval
    except Exception as e:
        logger.error(f"Gagal simpan evaluasi {user_id}: {e}")
        await session.rollback()
        return None


async def get_user_history(session: AsyncSession, user_id: int) -> list[Evaluation]:
    """Ambil 5 history terakhir user."""
    statement = (
        select(Evaluation)
        .where(Evaluation.user_id == user_id)
        .order_by(Evaluation.timestamp.desc())
        .limit(5)
    )
    result = await session.execute(statement)
    return list(result.scalars().all())


async def get_eval_by_id(session: AsyncSession, eval_id: int) -> Evaluation | None:
    """Ambil data evaluasi berdasarkan ID."""
    try:
        return await session.get(Evaluation, eval_id)
    except Exception:
        return None


async def update_evaluation_feedback(session: AsyncSession, eval_id: int, feedback: str):
    """Update feedback (positive/negative)."""
    eval_obj = await session.get(Evaluation, eval_id)
    if eval_obj:
        eval_obj.feedback = feedback
        session.add(eval_obj)
        try:
            await session.commit()
            return True
        except Exception as e:
            logger.error(f"Gagal update feedback {eval_id}: {e}")
            await session.rollback()
            return False
    return False


async def get_recent_fails(session: AsyncSession) -> list[Evaluation]:
    """Admin: Ambil 5 evaluasi terakhir dengan feedback 'negative'."""
    statement = (
        select(Evaluation)
        .where(Evaluation.feedback == "negative")
        .order_by(Evaluation.timestamp.desc())
        .limit(5)
    )
    result = await session.execute(statement)
    return list(result.scalars().all())


async def get_all_user_ids(session: AsyncSession) -> list[int]:
    """Ambil semua ID user untuk broadcast."""
    statement = select(User.user_id)
    result = await session.execute(statement)
    return list(result.scalars().all())
