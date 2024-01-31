import ctypes


class CircularBufferHeader(ctypes.Structure):
    _fields_ = [
        ("head_index", ctypes.c_uint32),
        ("tail_index", ctypes.c_uint32),
        ("capacity", ctypes.c_uint32),
    ]


class CircularBuffer:

    def __init__(self, buffer) -> None:
        self._header = CircularBufferHeader.from_buffer(buffer)
        self._buffer_ptr = ctypes.addressof(self._header) + ctypes.sizeof(CircularBufferHeader)

    def full(self) -> bool:
        ...

    def empty(self) -> bool:
        ...

    def capacity(self) -> int:
        ...

    def size(self) -> int:
        ...

    def reset(self) -> None:
        ...

    def put(self, item) -> None:
        ...

    def get(self):
        ...
