from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    sessionmaker,
)
from sqlalchemy import create_engine, select
from sqlalchemy.exc import StatementError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import pytest


import linearmoney as lm
from linearmoney.ext.sqlalchemy import VectorMoney, AtomicMoney


class BaseModel(DeclarativeBase): ...


class VectorModel(BaseModel):

    __tablename__ = "vector_model"

    id: Mapped[int] = mapped_column(primary_key=True)
    money_column: Mapped[VectorMoney] = mapped_column(VectorMoney)


class AtomicModel(BaseModel):

    __tablename__ = "atomic_model"

    id: Mapped[int] = mapped_column(primary_key=True)
    money_column: Mapped[AtomicMoney] = mapped_column(
        AtomicMoney(lm.data.currency("USD"))
    )


@pytest.fixture
def fixt_session():
    """A sync Session with a fresh in-memory sqlite db."""

    _engine = create_engine("sqlite:///:memory:", echo=False)
    BaseModel.metadata.create_all(bind=_engine)
    return sessionmaker(bind=_engine)


@pytest.fixture
async def fixt_async_session():
    """An async Session with a fresh in-memory sqlite db."""

    _async_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with _async_engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)
    return async_sessionmaker(bind=_async_engine, expire_on_commit=False)


def test_vector_money_read_write(fixt_session):
    """Ensure the VectorMoney column type serializes to the db correctly."""

    fo = lm.vector.forex({"base": "usd", "rates": {"jpy": 100}})
    sp = lm.vector.space(fo)
    asset_vec = lm.vector.asset(10, "usd", sp) + lm.vector.asset(100, "jpy", sp)
    assert lm.vector.evaluate(asset_vec, "usd", fo) == 11

    with fixt_session() as session:
        session.add(VectorModel(id=1, money_column=asset_vec))
        session.commit()
        stored_asset_vec = (
            session.execute(select(VectorModel).where(VectorModel.id == 1))
            .scalars()
            .first()
            .money_column
        )
        assert stored_asset_vec == asset_vec


async def test_vector_money_async_read_write(fixt_async_session):
    """Ensure the VectorMoney column type serializes to the db correctly in async sqlalchemy."""

    fo = lm.vector.forex({"base": "usd", "rates": {"jpy": 100}})
    sp = lm.vector.space(fo)
    asset_vec = lm.vector.asset(10, "usd", sp) + lm.vector.asset(100, "jpy", sp)
    assert lm.vector.evaluate(asset_vec, "usd", fo) == 11

    async with fixt_async_session() as session:
        session.add(VectorModel(id=1, money_column=asset_vec))
        await session.commit()
        stored_asset_vec = (
            (await session.execute(select(VectorModel).where(VectorModel.id == 1)))
            .scalars()
            .first()
            .money_column
        )
        assert stored_asset_vec == asset_vec


def test_vector_money_used_in_where_clause(fixt_session):
    """Ensure the VectorMoney column type allows using money vectors in where clauses."""

    fo = lm.vector.forex({"base": "usd", "rates": {"jpy": 100}})
    sp = lm.vector.space(fo)
    asset_vec = lm.vector.asset(10, "usd", sp) + lm.vector.asset(100, "jpy", sp)
    assert lm.vector.evaluate(asset_vec, "usd", fo) == 11

    with fixt_session() as session:
        session.add(VectorModel(id=1, money_column=asset_vec))
        session.commit()
        stored_asset_vec = (
            session.execute(
                select(VectorModel).where(VectorModel.money_column == asset_vec)
            )
            .scalars()
            .first()
            .money_column
        )
        assert stored_asset_vec == asset_vec


def test_atomic_money_read_write(fixt_session):
    """Ensure the AtomicMoney column type serializes to the db correctly."""

    fo = lm.vector.forex({"base": "usd", "rates": {}})
    sp = lm.vector.space(fo)
    asset_vec = lm.vector.asset(10, "usd", sp)
    assert lm.vector.evaluate(asset_vec, "usd", fo) == 10

    with fixt_session() as session:
        session.add(AtomicModel(id=1, money_column=asset_vec))
        session.commit()
        stored_asset_vec = (
            session.execute(select(AtomicModel).where(AtomicModel.id == 1))
            .scalars()
            .first()
            .money_column
        )
        assert stored_asset_vec == asset_vec


async def test_atomic_money_async_read_write(fixt_async_session):
    """Ensure the AtomicMoney column type serializes to the db correctly in async sqlalchemy."""

    fo = lm.vector.forex({"base": "usd", "rates": {}})
    sp = lm.vector.space(fo)
    asset_vec = lm.vector.asset(10, "usd", sp)
    assert lm.vector.evaluate(asset_vec, "usd", fo) == 10

    async with fixt_async_session() as session:
        session.add(AtomicModel(id=1, money_column=asset_vec))
        await session.commit()
        stored_asset_vec = (
            (await session.execute(select(AtomicModel).where(AtomicModel.id == 1)))
            .scalars()
            .first()
            .money_column
        )
        assert stored_asset_vec == asset_vec


def test_atomic_money_in_where_clause(fixt_session):
    """Ensure the AtomicMoney column type allows using money vectors in where clauses."""

    fo = lm.vector.forex({"base": "usd", "rates": {}})
    sp = lm.vector.space(fo)
    asset_vec = lm.vector.asset(10, "usd", sp)
    assert lm.vector.evaluate(asset_vec, "usd", fo) == 10

    with fixt_session() as session:
        session.add(AtomicModel(id=1, money_column=asset_vec))
        session.commit()
        stored_asset_vec = (
            session.execute(
                select(AtomicModel).where(AtomicModel.money_column == asset_vec)
            )
            .scalars()
            .first()
            .money_column
        )
        assert stored_asset_vec == asset_vec


def test_atomic_money_enforces_single_currency_asset(fixt_session):
    """Ensure the AtomicMoney column type does not allow storing multi-currency
    vectors."""

    fo = lm.vector.forex({"base": "usd", "rates": {"jpy": 100}})
    sp = lm.vector.space(fo)
    asset_vec = lm.vector.asset(10, "usd", sp) + lm.vector.asset(100, "jpy", sp)
    assert lm.vector.evaluate(asset_vec, "usd", fo) == 11

    with fixt_session() as session:
        with pytest.raises(StatementError):
            session.add(AtomicModel(id=1, money_column=asset_vec))
            session.commit()


def test_atomic_money_enforces_single_currency_space(fixt_session):
    """Ensure the AtomicMoney column type does not allow storing vectors with
    currency spaces larger than 1 dimension."""

    fo = lm.vector.forex({"base": "usd", "rates": {"jpy": 100}})
    sp = lm.vector.space(fo)
    asset_vec = lm.vector.asset(10, "usd", sp)
    assert lm.vector.evaluate(asset_vec, "usd", fo) == 10
    # Make sure the vector only has one value, so we are only testing the space.
    assert len([i for i in asset_vec if i != 0]) == 1

    with fixt_session() as session:
        with pytest.raises(StatementError):
            session.add(AtomicModel(id=1, money_column=asset_vec))
            session.commit()
