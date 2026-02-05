import pytest
from datetime import datetime, timedelta

from hotel_planner.models.resource import Item, Employee, Resource
from hotel_planner.models.event import Event
from hotel_planner.models.inventory import Inventory
from hotel_planner.core.scheduler import Scheduler


def test_corequisite_success():
    inv = Inventory()
    inv.add_resource(Item("Cámara RED", quantity=1, requires=["Técnico de Cámara Certificado"]))
    inv.add_resource(Employee("Técnico de Cámara Certificado", role="cámara"))

    sched = Scheduler(inv)

    e = Event(
        "Rodaje",
        datetime(2026, 2, 1, 9, 0),
        datetime(2026, 2, 1, 12, 0),
        resources=[
            {"name": "Cámara RED", "quantity": 1},
            {"name": "Técnico de Cámara Certificado", "quantity": 1},
        ],
    )
    ok, reason = sched.add_event(e)
    assert ok, f"Debe permitir evento cuando se incluyen los co-requisitos: {reason}"


def test_corequisite_missing_fails():
    inv = Inventory()
    inv.add_resource(Item("Cámara RED", quantity=1, requires=["Técnico de Cámara Certificado"]))
    # NOT adding the technician to the event selection intentionally
    sched = Scheduler(inv)

    e = Event(
        "RodajeSinTec",
        datetime(2026, 2, 2, 9, 0),
        datetime(2026, 2, 2, 11, 0),
        resources=[{"name": "Cámara RED", "quantity": 1}],
    )
    ok, reason = sched.add_event(e)
    assert not ok
    assert isinstance(reason, dict)
    assert "constraint_error" in reason
    errs = reason["constraint_error"]
    assert "missing_requires" in errs
    # Cámara RED debe listar el técnico faltante
    assert any("Cámara RED" == k or k.lower() == "cámara red" for k in errs["missing_requires"].keys())


def test_mutual_exclusion_by_name_fails():
    inv = Inventory()
    inv.add_resource(Item("Mechero Bunsen", quantity=1, excludes=["Contenedor de Éter"]))
    inv.add_resource(Item("Contenedor de Éter", quantity=1, excludes=["Mechero Bunsen"]))

    sched = Scheduler(inv)

    e = Event(
        "Experimento Peligroso",
        datetime(2026, 3, 3, 10, 0),
        datetime(2026, 3, 3, 12, 0),
        resources=[
            {"name": "Mechero Bunsen", "quantity": 1},
            {"name": "Contenedor de Éter", "quantity": 1},
        ],
    )
    ok, reason = sched.add_event(e)
    assert not ok
    assert isinstance(reason, dict) and "constraint_error" in reason
    errs = reason["constraint_error"]
    assert "mutual_exclusion" in errs
    conflicts = errs["mutual_exclusion"]
    # debe reportar conflicto entre ambos recursos
    names = {c["resource"] for c in conflicts}
    assert "Mechero Bunsen" in names or "Contenedor de Éter" in names
    # comprobar que la pareja aparece en conflicts_with
    assert any("Contenedor de Éter" in c["conflicts_with"] or "Mechero Bunsen" in c["conflicts_with"] for c in conflicts)


def test_mutual_exclusion_by_category_fails():
    inv = Inventory()
    # Room declares it cannot coexist with any 'item'
    inv.add_resource(Resource("Sala de Grabación A", category="room", excludes_categories=["item"]))
    inv.add_resource(Item("Batería Acústica", quantity=1))

    sched = Scheduler(inv)

    e = Event(
        "Sesión",
        datetime(2026, 4, 5, 14, 0),
        datetime(2026, 4, 5, 16, 0),
        resources=[
            {"name": "Sala de Grabación A", "quantity": 1},
            {"name": "Batería Acústica", "quantity": 1},
        ],
    )
    ok, reason = sched.add_event(e)
    assert not ok
    assert isinstance(reason, dict) and "constraint_error" in reason
    errs = reason["constraint_error"]
    assert "mutual_exclusion" in errs
    conflicts = errs["mutual_exclusion"]
    # Sala de Grabación A debe estar presente en los conflictos
    assert any(c["resource"] == "Sala de Grabación A" for c in conflicts)


def test_complex_requires_multiple_items_success():
    inv = Inventory()
    inv.add_resource(Item("Cirugía Robótica", quantity=1,
                          requires=["Consola Da Vinci", "Cirujano Certificado en Da Vinci"]))
    inv.add_resource(Item("Consola Da Vinci", quantity=1))
    inv.add_resource(Employee("Cirujano Certificado en Da Vinci", role="cirujano"))

    sched = Scheduler(inv)

    e = Event(
        "Cirugía Especial",
        datetime(2026, 5, 1, 8, 0),
        datetime(2026, 5, 1, 12, 0),
        resources=[
            {"name": "Cirugía Robótica", "quantity": 1},
            {"name": "Consola Da Vinci", "quantity": 1},
            {"name": "Cirujano Certificado en Da Vinci", "quantity": 1},
        ],
    )
    ok, reason = sched.add_event(e)
    assert ok, f"Debe permitir cirugía cuando se incluyen todos los co-requisitos: {reason}"