from typing import Callable, Dict, NewType, Optional, Sequence, Tuple, TypeVar

ProcessTID = NewType("ProcessTID", int)
ThreadTID = NewType("ThreadTID", int)

R = TypeVar("R")
T = TypeVar("T")
PoolTask =  Optional[Tuple[ProcessTID, Callable[..., R], Sequence[T], Dict[str, T]]]
