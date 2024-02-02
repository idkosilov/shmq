import ctypes
import struct

import pytest

from shmq.circular_buffer import CircularBuffer, CircularBufferHeader
from shmq.exceptions import InsufficientBufferSize, InsufficientSpace


@pytest.fixture
def circular_buffer():
    ...


@pytest.fixture
def empty_buffer():
    buffer_size = 256
    return bytearray(buffer_size)


def write_data_in_buffer(buffer: bytearray, data: list[bytes]) -> bytearray:
    size_in_bytes_of_item_length = ctypes.sizeof(ctypes.c_uint32)
    header_size = ctypes.sizeof(CircularBufferHeader)
    read_index = 0
    write_index = sum(len(item) + size_in_bytes_of_item_length for item in data)
    max_size = len(buffer) - header_size

    # Pack the header information
    struct.pack_into("<III", buffer, 0, read_index, write_index, max_size)

    # Pack the data
    data_offset = header_size
    for item_data in data:
        struct.pack_into("<I", buffer, data_offset, len(item_data))
        data_offset += size_in_bytes_of_item_length
        buffer[data_offset:data_offset + len(item_data)] = item_data
        data_offset += len(item_data)

    return buffer


def test_initialization_with_empty_buffer(empty_buffer):
    """
    Test the initialization of a CircularBuffer with an empty buffer.
    Validates that the buffer is initially empty, not full, and that its size is 0.
    Also checks that the buffer's capacity is correctly calculated, taking into account
    the space used by the CircularBufferHeader.
    """
    circular_buffer = CircularBuffer(empty_buffer)

    assert circular_buffer.empty(), "Buffer should be empty upon initialization"
    assert not circular_buffer.full(), "Buffer should not be full upon initialization"

    assert circular_buffer.size() == 0, "Buffer size should be 0 upon initialization"

    expected_capacity = len(empty_buffer) - 1 - ctypes.sizeof(CircularBufferHeader)
    assert circular_buffer.capacity() == expected_capacity, (f"Buffer capacity should be {expected_capacity}, "
                                                             f"considering the CircularBufferHeader size")


@pytest.mark.parametrize("data", [
    [b'a', b'ab', b'abc'],
    [b'data', b'more data'],
])
def test_initialization_with_predefined_data(empty_buffer, data):
    """
    Test the initialization of a CircularBuffer with predefined data in the buffer.
    Validates that the buffer is not empty, checks if the buffer is full, and verifies
    the size and capacity of the buffer based on the predefined data.
    """
    buffer_with_predefined_data = write_data_in_buffer(empty_buffer, data)

    circular_buffer = CircularBuffer(buffer_with_predefined_data)
    capacity = len(buffer_with_predefined_data) - 1 - ctypes.sizeof(CircularBufferHeader)
    size_in_bytes_of_item_length = ctypes.sizeof(ctypes.c_uint32)

    assert not circular_buffer.empty(), "Buffer should not be empty after initialization with predefined data"
    assert not circular_buffer.full(), "Buffer should not be full based on the predefined data and implementation"

    expected_size = sum(len(item) + size_in_bytes_of_item_length for item in data)
    assert circular_buffer.size() == expected_size, (f"Expected buffer size to be {expected_size}, "
                                                     f"but got {circular_buffer.size()}")

    assert circular_buffer.capacity() == capacity, (f"Expected buffer capacity to be {capacity}, "
                                                    f"but got {circular_buffer.capacity()}")


def test_initialization_with_size_less_then_circular_buffer_header_size_raise_insufficient_buffer_size_exception():
    """
    Test that initializing a CircularBuffer with a buffer size smaller than the minimum
    required size (size of CircularBufferHeader) raises an InsufficientBufferSizeException.
    """
    insufficient_buffer_size = ctypes.sizeof(CircularBufferHeader) - 1
    buffer = bytearray(insufficient_buffer_size)

    with pytest.raises(InsufficientBufferSize):
        _ = CircularBuffer(buffer)


def test_empty_returns_true_if_has_not_items(empty_buffer):
    """
    Test that `empty()` returns True for a newly initialized CircularBuffer
    that has not had any items added to it, indicating it is empty.
    """
    circular_buffer = CircularBuffer(empty_buffer)

    assert circular_buffer.empty(), "CircularBuffer should be empty when no items have been added"


def test_empty_returns_false_if_has_items(empty_buffer):
    """
    Test that `empty()` returns False for a CircularBuffer after items have been added,
    indicating it is not empty.
    """
    buffer_with_data = write_data_in_buffer(empty_buffer, [b'abc', b'abcde'])
    circular_buffer = CircularBuffer(buffer_with_data)

    assert not circular_buffer.empty(), "CircularBuffer should not be empty after items have been added"


def test_empty_returns_false_if_buffer_is_full(empty_buffer):
    """
    Test that `empty()` returns False for a CircularBuffer that is full,
    ensuring that a full buffer is recognized as not empty.
    """
    item_size = 256 - ctypes.sizeof(CircularBufferHeader) - ctypes.sizeof(ctypes.c_uint32)
    write_data_in_buffer(empty_buffer, [b'x' * item_size, ])

    circular_buffer = CircularBuffer(empty_buffer)

    assert not circular_buffer.empty(), "CircularBuffer should not be empty when it is full"


def test_full_returns_true_if_buffer_is_full(empty_buffer):
    """
    Test that `full()` returns True when the CircularBuffer is filled to its capacity,
    indicating the buffer is full.
    """
    item_size = (255 - ctypes.sizeof(CircularBufferHeader) - ctypes.sizeof(ctypes.c_uint32))
    buffer_with_data = write_data_in_buffer(empty_buffer, [b'x' * item_size])

    circular_buffer = CircularBuffer(buffer_with_data)

    assert circular_buffer.full(), "CircularBuffer should be full when data fills up to its capacity"


def test_full_returns_false_if_buffer_has_items(empty_buffer):
    """
    Test that `full()` returns False if the buffer has items but is not filled to its capacity,
    indicating it is not full.
    """
    write_data_in_buffer(empty_buffer, [b'abc', b'abcde'])

    circular_buffer = CircularBuffer(empty_buffer)

    assert not circular_buffer.full(), "CircularBuffer should not be considered full when partially filled with items"


def test_full_returns_false_if_buffer_is_empty(empty_buffer):
    """
    Test that `full()` returns False for a newly initialized CircularBuffer,
    indicating it is not full when empty.
    """
    circular_buffer = CircularBuffer(empty_buffer)

    assert not circular_buffer.full(), "CircularBuffer should not be full when it is empty"


def test_size_returns_zero_if_buffer_is_empty(empty_buffer):
    """
    Verify that the size method returns 0 for an empty CircularBuffer,
    indicating that no items are stored in the buffer.
    """
    circular_buffer = CircularBuffer(empty_buffer)

    assert circular_buffer.size() == 0, "Expected size of an empty CircularBuffer to be 0"


def test_size_returns_capacity_if_buffer_is_full(empty_buffer):
    """
    Verify that the size method returns the full capacity of the buffer when it is full,
    indicating that the buffer's size matches its capacity when fully utilized.
    """
    capacity = 255 - ctypes.sizeof(CircularBufferHeader)
    item_size = capacity - ctypes.sizeof(ctypes.c_uint32)
    buffer_with_data = write_data_in_buffer(empty_buffer, [b'x' * item_size])

    circular_buffer = CircularBuffer(buffer_with_data)

    assert circular_buffer.size() == capacity, "Expected size of a full CircularBuffer to match its capacity"


def test_size_returns_actual_size_of_items(empty_buffer):
    """
    Verify that the size method returns the actual size of the items stored in the buffer,
    accounting for the data length and the overhead of storing each item's size.
    """
    data = [b'x', b'xx', b'xxx']
    expected_data_size = sum(len(item) + ctypes.sizeof(ctypes.c_uint32) for item in data)

    buffer_with_data = write_data_in_buffer(empty_buffer, data)

    circular_buffer = CircularBuffer(buffer_with_data)

    assert circular_buffer.size() == expected_data_size, ("Expected CircularBuffer size to match the "
                                                          "total size of stored items")


def test_reset_makes_buffer_empty(empty_buffer):
    """
    Verify that the reset method clears the buffer, making its content match an empty buffer state,
    effectively resetting the CircularBuffer to its initial state.
    """
    data = [b'x', b'xx', b'xxx']

    buffer_with_data = write_data_in_buffer(empty_buffer, data)

    circular_buffer = CircularBuffer(buffer_with_data)
    circular_buffer.reset()

    assert circular_buffer.empty(), "CircularBuffer should be empty after reset"
    assert not circular_buffer.full(), "CircularBuffer should not be full after reset"
    assert circular_buffer.size() == 0, "CircularBuffer size should be 0 after reset"


def test_put_item_simple_case(empty_buffer):
    buffer_size = len(empty_buffer)
    expected_buffer = bytearray(buffer_size)
    write_data_in_buffer(expected_buffer, [b'abc'])

    circular_buffer = CircularBuffer(empty_buffer)
    circular_buffer.put(b'abc')

    assert empty_buffer == expected_buffer


def test_put_item_with_size_more_then_capacity_raise_exception(empty_buffer):
    circular_buffer = CircularBuffer(empty_buffer)

    with pytest.raises(InsufficientSpace):
        circular_buffer.put(b'abc' * 1000)


def test_put_item_with_size_more_then_available_space_overwrites_old_data(empty_buffer):
    capacity = 256 - ctypes.sizeof(CircularBufferHeader)
    item_size = capacity - ctypes.sizeof(ctypes.c_uint32)
    buffer_with_data = write_data_in_buffer(empty_buffer, [b'x' * item_size])

    circular_buffer = CircularBuffer(empty_buffer)
    circular_buffer.put(b'new_data')

    header_offset = ctypes.sizeof(CircularBufferHeader)

    # TODO


def test_put_item_in_full_buffer_overwrites_old_data(circular_buffer):
    ...


def test_put_items_to_limit_of_capacity_makes_buffer_full(circular_buffer):
    ...


def test_put_item_after_read_operation_in_full_buffer_works_correct(circular_buffer):
    ...


def test_put_item_in_partially_filled_buffer(circular_buffer):
    ...


def test_put_various_sized_items(circular_buffer):
    ...


def test_sequential_put_and_get(circular_buffer):
    ...


def test_put_get_put_to_test_wraparound(circular_buffer):
    ...


def test_put_item_immediately_retrievable(circular_buffer):
    ...


def test_stress_put_and_get(circular_buffer):
    ...


def test_get_from_non_empty_buffer(circular_buffer):
    ...


def test_get_from_empty_buffer_raises_exception(circular_buffer):
    ...


def test_sequential_get_until_empty(circular_buffer):
    ...


def test_get_after_reset(circular_buffer):
    ...


def test_get_with_state_check_after_each_operation(circular_buffer):
    ...
