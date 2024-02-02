import ctypes

from shmq.exceptions import InsufficientBufferSize


class CircularBufferHeader(ctypes.Structure):
    """
    This class is a ctypes Structure that defines the layout of the header for a circular buffer.
    The header includes indices for the head and tail of the buffer, as well as its capacity. These
    indices are used to manage the state of the circular buffer efficiently.
    """
    _fields_ = [
        ("read_index", ctypes.c_uint32),  # Index of the buffer's head (the next position to read from)
        ("write_index", ctypes.c_uint32),  # Index of the buffer's tail (the next position to write to)
        ("max_size", ctypes.c_uint32),    # Total max_size of the buffer (maximum number of bytes it can hold)
    ]


class CircularBuffer:
    """
    A CircularBuffer class that provides a fixed-size buffer using a first-in-first-out (FIFO)
    data structure. This buffer is particularly useful for scenarios where a constant memory
    footprint is required, and old data can be safely overwritten by new data when the buffer is full.
    """
    HEADER_SIZE = ctypes.sizeof(CircularBufferHeader)
    ITEM_PREFIX_SIZE = ctypes.sizeof(ctypes.c_uint32)  # Size prefix for each item
    MIN_BUFFER_SIZE = HEADER_SIZE + 1

    def __init__(self, buffer: bytearray | memoryview) -> None:
        """
        Initialize the CircularBuffer with a given buffer.

        :param buffer: A bytearray object that backs the circular buffer. This buffer should be
                       large enough to accommodate the CircularBufferHeader and the data elements.
        """
        if len(buffer) < CircularBuffer.MIN_BUFFER_SIZE:
            raise InsufficientBufferSize

        self._header = CircularBufferHeader.from_buffer(buffer)

        if self._header.max_size == 0:
            self._header.max_size = len(buffer) - CircularBuffer.HEADER_SIZE

        self._buffer_ptr = ctypes.addressof(self._header) + CircularBuffer.HEADER_SIZE

    def full(self) -> bool:
        """
        Check if the circular buffer is full.

        :returns: True if the buffer is full, indicating that there is no space for new data
                  without overwriting existing ones, False otherwise.
        """
        return ((self._header.write_index + 1) % self._header.max_size) == self._header.read_index

    def empty(self) -> bool:
        """
        Check if the circular buffer is empty.

        :returns: True if the buffer has no data, indicating that no data can be read, False otherwise.
        """
        return self._header.read_index == self._header.write_index

    def capacity(self) -> int:
        """
        Get the capacity of the circular buffer.

        :returns: The total capacity of the buffer, measured in the maximum number of bytes it can hold.
        """
        return self._header.max_size - 1

    def size(self) -> int:
        """
        Get the current size of the circular buffer.

        :returns: The current number of data stored in the buffer.
        """
        if not self.full():
            if self._header.write_index >= self._header.read_index:
                return self._header.write_index - self._header.read_index
            else:
                return self._header.max_size + self._header.read_index - self._header.write_index
        else:
            return self.capacity()

    def reset(self) -> None:
        """
        Reset the circular buffer.

        This method clears the buffer by setting the head and tail indices back to their initial positions.
        """
        self._header.write_index = 0
        self._header.read_index = 0

    def put(self, item: bytes) -> None:
        """
        Put a new item into the circular buffer.

        :param item: The item (a bytes object) to be added to the buffer. If the buffer is full, this
                     operation overwrite the oldest data.

        :raise InsufficientSpace: If item size is more than buffer capacity.
        """
        ...

    def get(self) -> bytes:
        """
        Get an item from the circular buffer.

        This method returns the oldest item from the buffer. If the buffer is empty,
        no item can be returned.

        :returns: The oldest item from the buffer as a bytes object.

        :raises Empty: If the buffer is empty and no items are available to be returned.
        """
        ...
