from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import pymem
import pymem.process

from collections.abc import Sequence

def get_module(process_pymem:pymem.Pymem, module_name:str = ""):
        module = pymem.process.module_from_name(process_pymem.process_handle, module_name)
        return module if module else process_pymem.process_base

def get_module_address(process_pymem:pymem.Pymem, module_name:str = "") -> int:
    module = get_module(process_pymem, module_name)
    return module.lpBaseOfDll

@dataclass(frozen=True)
class StaticOffset(ABC):
    value: int
    
    def get_value(self, *args) -> int:
        return self.value

    @property
    @abstractmethod
    def use_read64(self) -> bool:
        pass

@dataclass(frozen=True)
class StaticOffset32(StaticOffset):
    def use_read64(self) -> bool:
        return False

@dataclass(frozen=True)
class StaticOffset64(StaticOffset):
    def use_read64(self) -> bool:
        return True

@dataclass(frozen=True)
class DynamicOffset(ABC):
    base: int
    offset: int = 0
    use_read64: bool = True

    def get_value(self, process_pymem: pymem.Pymem) -> int:
        return self._get_value(process_pymem)

    @abstractmethod
    def _get_value(self, process_pymem: pymem.Pymem) -> int:
        pass

@dataclass(frozen=True)
class DynamicOffset32(DynamicOffset):
    def _get_value(self, process_pymem: pymem.Pymem) -> int:
        value = process_pymem.read_int(self.base)
        assert isinstance(value, int)
        return value + self.offset

@dataclass(frozen=True)
class DynamicOffset64(DynamicOffset):
    def _get_value(self, process_pymem: pymem.Pymem) -> int:
        value = process_pymem.read_longlong(self.base)
        assert isinstance(value, int)
        return value + self.offset

@dataclass(frozen=True)
class PatternSrting():
    bytes: bytes
    offset: int
    lenght: int


@dataclass(frozen=True)
class PatternScan():
    patter: PatternSrting
    offset: int = 0
    use_read64: bool =False

    
    def get_address(self, process_pymem: pymem.Pymem, _module_name: str = "") -> int:
        if not self.patter.bytes:
            return 0
        
        return_address: int = 0
        module = get_module(process_pymem, _module_name)

        scan_address = process_pymem.pattern_scan_module(self.patter.bytes, module)
        if not isinstance(scan_address, int):
            return 0
        
        command_address = scan_address + self.patter.offset
        if self.use_read64:
            offset = process_pymem.read_longlong(command_address + self.patter.lenght - 8)
        else:
            offset = process_pymem.read_int(command_address + self.patter.lenght - 4)

        if offset and isinstance(offset, int):
            return_address = offset + command_address + self.patter.lenght + self.offset
    
        return 0 if return_address <= 0 else return_address 
        

@dataclass(frozen=True)
class Pointer():
    base: int|PatternScan
    offset: Sequence[DynamicOffset|StaticOffset] = field(default_factory=lambda: [StaticOffset32(0)])
    finally_offset: int = 0

    def __post_init__(self):
        if isinstance(self.base, int) and self.base <= 0:
            raise ValueError("base address must be positive")

    def get_address(self, process_pymem: pymem.Pymem, _module_name: str = ""):
        base_address:int = get_module_address(process_pymem, _module_name)

        if isinstance(self.base ,int):
            finally_address = base_address + self.base
        else:
            finally_address = base_address + self.base.get_address(process_pymem)

        for offset in self.offset:
            if offset.use_read64:
                finally_address = process_pymem.read_longlong(finally_address)
            else:
                finally_address = process_pymem.read_int(finally_address)
            if isinstance(finally_address, int):
                finally_address = finally_address + offset.get_value(process_pymem)
            else:
                return 0

        finally_address += self.finally_offset

        return 0 if finally_address <= 0 else finally_address
        
@dataclass(frozen=True)
class Address(ABC):
    address: int|Pointer|PatternScan
    module_name: str = ""

    def __post_init__(self):
        if isinstance(self.address, int) and self.address <= 0:
            raise ValueError("base address must be positive")

    def get_address(self, process_pymem: pymem.Pymem) -> int:
        if isinstance(self.address, int):
            base_address:int = get_module_address(process_pymem, self.module_name)
            return self.address + base_address

        elif isinstance(self.address, Pointer):
            return self.address.get_address(process_pymem, self.module_name)
        
        elif isinstance(self.address, PatternScan):
            return self.address.get_address(process_pymem, self.module_name)

        else:
            raise TypeError("address type error")
