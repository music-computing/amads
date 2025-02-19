# noqa: F841

from amads.core.basics import Event, Note, Part, Score, cached_event_property


def test_cached_event_property():
    """Test that cached_event_property caches the property value after first computation."""
    computation_count = 0

    class TestEvent(Event):
        @cached_event_property
        def expensive_property(self):
            nonlocal computation_count
            computation_count += 1
            return "computed_value"

    event = TestEvent(duration=1, delta=0)

    # Access the property multiple times
    value1 = event.expensive_property
    value2 = event.expensive_property
    value3 = event.expensive_property

    # Assert that the property was computed only once
    assert computation_count == 1, "The property should be computed only once."

    # Assert that the cached value is correct
    assert value1 == "computed_value"
    assert value2 == "computed_value"
    assert value3 == "computed_value"

    # Modify the event and ensure cache is invalidated
    event.flag_modified()
    value4 = event.expensive_property
    assert (
        computation_count == 2
    ), "The property should be recomputed after modification."
    assert value4 == "computed_value"


def test_recursive_flag_modified():
    """Test that flag_modified recursively invalidates parent caches."""
    parent_computation_count = 0
    child_computation_count = 0

    class ParentEvent(Event):
        @cached_event_property
        def parent_property(self):
            nonlocal parent_computation_count
            parent_computation_count += 1
            return "parent_value"

    class ChildEvent(Event):
        @cached_event_property
        def child_property(self):
            nonlocal child_computation_count
            child_computation_count += 1
            return "child_value"

    parent = ParentEvent(duration=2, delta=0)
    child = ChildEvent(duration=1, delta=0)
    child.parent = parent

    # Access properties to cache values
    parent_val1 = parent.parent_property
    child_val1 = child.child_property

    # Ensure initial computations
    assert parent_computation_count == 1, "Parent property should be computed once."
    assert child_computation_count == 1, "Child property should be computed once."

    # Access properties again, should not recompute
    parent_val2 = parent.parent_property
    child_val2 = child.child_property

    assert parent_computation_count == 1, "Parent property should not be recomputed."
    assert child_computation_count == 1, "Child property should not be recomputed."

    # Modify the child, which should invalidate its cache and the parent's cache
    child.flag_modified()

    # Access properties again, should recompute both
    parent_val3 = parent.parent_property
    child_val3 = child.child_property

    assert (
        parent_computation_count == 2
    ), "Parent property should be recomputed after child is modified."
    assert (
        child_computation_count == 2
    ), "Child property should be recomputed after modification."

    # Ensure values are correct
    assert parent_val3 == "parent_value", "Parent property should return correct value."
    assert child_val3 == "child_value", "Child property should return correct value."


def test_multiple_instances():
    """Test that multiple instances of the same class maintain independent caches and return different values."""
    computation_count1 = 0
    computation_count2 = 0

    class MultiInstanceEvent(Event):
        def __init__(self, duration, delta, value_one, value_two):
            super().__init__(duration, delta)
            self._value_one = value_one
            self._value_two = value_two

        @cached_event_property
        def property_one(self):
            nonlocal computation_count1
            computation_count1 += 1
            return self._value_one

        @cached_event_property
        def property_two(self):
            nonlocal computation_count2
            computation_count2 += 1
            return self._value_two

    # Create two instances with different property values
    event1 = MultiInstanceEvent(
        duration=1,
        delta=0,
        value_one="value_one_instance1",
        value_two="value_two_instance1",
    )
    event2 = MultiInstanceEvent(
        duration=2,
        delta=1,
        value_one="value_one_instance2",
        value_two="value_two_instance2",
    )

    # Access properties on event1
    val1_e1 = event1.property_one
    val2_e1 = event1.property_two

    # Access properties on event2
    val1_e2 = event2.property_one
    val2_e2 = event2.property_two

    # Assert that each property was computed once per instance
    assert computation_count1 == 2, "Each instance should compute property_one once."
    assert computation_count2 == 2, "Each instance should compute property_two once."

    # Access properties again, should not recompute
    val1_e1_again = event1.property_one
    val2_e1_again = event1.property_two
    val1_e2_again = event2.property_one
    val2_e2_again = event2.property_two

    # Ensure computation counts haven't increased
    assert computation_count1 == 2, "property_one should not be recomputed."
    assert computation_count2 == 2, "property_two should not be recomputed."

    # Modify event1 and check cache invalidation
    event1.flag_modified()

    # Access properties after modification
    val1_e1_new = event1.property_one
    val2_e1_new = event1.property_two

    # Only event1's properties should have been recomputed
    assert (
        computation_count1 == 3
    ), "property_one should be recomputed after modification."
    assert (
        computation_count2 == 3
    ), "property_two should be recomputed after modification."

    # Validate the new values
    assert (
        val1_e1_new == "value_one_instance1"
    ), "event1.property_one should return correct value."
    assert (
        val2_e1_new == "value_two_instance1"
    ), "event1.property_two should return correct value."

    # Event2's properties should remain cached and return their original values
    assert (
        event2.property_one == "value_one_instance2"
    ), "event2.property_one should return correct value."
    assert (
        event2.property_two == "value_two_instance2"
    ), "event2.property_two should return correct value."


def test_multiple_cached_properties():
    """Test that multiple cached properties on the same instance are handled correctly."""
    computation_count_a = 0
    computation_count_b = 0

    class MultiplePropertiesEvent(Event):
        @cached_event_property
        def property_a(self):
            nonlocal computation_count_a
            computation_count_a += 1
            return "value_a"

        @cached_event_property
        def property_b(self):
            nonlocal computation_count_b
            computation_count_b += 1
            return "value_b"

    event = MultiplePropertiesEvent(duration=1, delta=0)

    # Access both properties
    a1 = event.property_a
    b1 = event.property_b

    # Assert that both properties were computed once
    assert computation_count_a == 1, "property_a should be computed once."
    assert computation_count_b == 1, "property_b should be computed once."

    # Access properties again, should not recompute
    a2 = event.property_a
    b2 = event.property_b

    assert computation_count_a == 1, "property_a should not be recomputed."
    assert computation_count_b == 1, "property_b should not be recomputed."

    # Modify the event to invalidate caches
    event.flag_modified()

    # Access properties after modification
    a3 = event.property_a
    b3 = event.property_b

    # Assert that both properties were recomputed
    assert (
        computation_count_a == 2
    ), "property_a should be recomputed after modification."
    assert (
        computation_count_b == 2
    ), "property_b should be recomputed after modification."

    # Validate the new values
    assert a3 == "value_a"
    assert b3 == "value_b"


def test_note_attribute_modification():
    """Test that modifying a Note's attribute invalidates cached properties."""
    computation_count = 0

    class TestNote(Event):
        def __init__(self, duration=1, delta=0, pitch=60):
            super().__init__(duration, delta)
            self.pitch = pitch

        @cached_event_property
        def expensive_property(self):
            nonlocal computation_count
            computation_count += 1
            return f"computed_value_{self.pitch}"

    # Create a note and access the property
    note = TestNote(duration=1, delta=0, pitch=60)
    value1 = note.expensive_property

    # Assert initial computation
    assert computation_count == 1, "Property should be computed once initially."
    assert value1 == "computed_value_60"

    # Access property again, should use cache
    value2 = note.expensive_property
    assert (
        computation_count == 1
    ), "Property should not be recomputed when accessed again."
    assert value2 == "computed_value_60"

    # Modify the note's pitch
    note.pitch = 72

    # Access property after modification, should recompute
    value3 = note.expensive_property
    assert (
        computation_count == 2
    ), "Property should be recomputed after pitch modification."
    assert value3 == "computed_value_72"

    # Access property again, should use new cached value
    value4 = note.expensive_property
    assert (
        computation_count == 2
    ), "Property should not be recomputed when accessed again after modification."
    assert value4 == "computed_value_72"


def test_score_is_monophonic_cache_invalidation():
    """Test that adding simultaneous notes to a Score invalidates the is_monophonic cached property."""
    # Create an empty score
    score = Score()
    part = Part()
    score.insert(part)

    # First access should compute the property
    assert score.is_monophonic is True

    # Second access should use cache
    assert score.is_monophonic is True

    # Add first note
    note1 = Note(duration=1, pitch=60, delta=0)
    part.insert(note1)

    # Access after modification should recompute
    assert score.is_monophonic is True

    # Add second note at same time (delta=0), which should make it non-monophonic
    note2 = Note(duration=1, pitch=72, delta=0)
    part.insert(note2)

    # Access after second modification should recompute and be non-monophonic
    assert score.is_monophonic is False

    # Add a third note at a different time, should still be non-monophonic
    note3 = Note(duration=1, pitch=64, delta=1)
    part.insert(note3)

    # Should still be non-monophonic
    assert score.is_monophonic is False

    # Space out the note so that they don't overlap any more
    note2.delta = 10
    note3.delta = 20

    # Now the score should be monophonic again
    assert score.is_monophonic
