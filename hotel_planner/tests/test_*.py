import pytest
from datetime import datetime, timedelta

from hotel_planner.models.resource import Item
from hotel_planner.models.event import Event
from hotel_planner.models.inventory import Inventory
from hotel_planner.core.scheduler import Scheduler

def test_add_event_quantity_limits_and_count_reserved():
    inv = Inventory()
    inv.add_resource(Item("Proyector", quantity=2))

    sched = Scheduler(inv)

    e1 = Event("A", datetime(2026,1,10,9,0), datetime(2026,1,10,10,0),
               resources=[{"name": "Proyector", "quantity": 1}])
    ok, reason = sched.add_event(e1)
    assert ok, f"add_event should succeed but failed: {reason}"

    e2 = Event("B", datetime(2026,1,10,9,15), datetime(2026,1,10,9,45),
               resources=[{"name": "Proyector", "quantity": 1}])
    ok, reason = sched.add_event(e2)
    assert ok, f"second overlapping add_event should succeed (qty total 2): {reason}"

    e3 = Event("C", datetime(2026,1,10,9,30), datetime(2026,1,10,9,50),
               resources=[{"name": "Proyector", "quantity": 1}])
    ok, reason = sched.add_event(e3)
    assert not ok, "third overlapping event should fail due to insufficient quantity"

    reserved = sched._count_reserved("Proyector", datetime(2026,1,10,9,0), datetime(2026,1,10,10,0))
    assert reserved == 2

def test_find_next_available_finds_first_slot():
    inv = Inventory()
    inv.add_resource(Item("Sala", quantity=1))

    sched = Scheduler(inv)

    occ = Event("Ocupado", datetime(2026,1,10,9,0), datetime(2026,1,10,10,0),
                resources=[{"name": "Sala", "quantity": 1}])
    ok, _ = sched.add_event(occ)
    assert ok

    start_from = datetime(2026,1,10,9,0)
    window_end = datetime(2026,1,10,12,0)
    duration = timedelta(hours=1)

    slot = sched.find_next_available(duration, ["Sala"], start_from, window_end, step_minutes=30)
    assert slot == (datetime(2026,1,10,10,0), datetime(2026,1,10,11,0))

def test_remove_event_allows_readd():
    inv = Inventory()
    inv.add_resource(Item("Cable", quantity=1))

    sched = Scheduler(inv)

    e = Event("X", datetime(2026,1,11,14,0), datetime(2026,1,11,15,0),
              resources=[{"name": "Cable", "quantity": 1}])
    ok, _ = sched.add_event(e)
    assert ok

    removed = sched.remove_event("X")
    assert removed is True

    e2 = Event("Y", datetime(2026,1,11,14,0), datetime(2026,1,11,15,0),
               resources=[{"name": "Cable", "quantity": 1}])
    ok, reason = sched.add_event(e2)
    assert ok, f"re-adding after removal should succeed but failed: {reason}"