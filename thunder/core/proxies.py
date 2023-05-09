from numbers import Number
from typing import Type, Optional, Any, Sequence, Tuple, List, Union
from functools import reduce, partial
import operator

from thunder.core.trace import VariableInterface, get_tracectx
from thunder.core.baseutils import ProxyInterface, NumberProxyInterface, TensorProxyInterface
import thunder.core.baseutils as baseutils
from thunder.core.langctx import langctx_for, get_langctx
import thunder.core.devices as devices
import thunder.core.dtypes as dtypes


# TODO Document this class
class Variable:
    def __init__(self, p: ProxyInterface):
        self.proxy = p

    def __hash__(self):
        return hash(self.proxy.name)

    def __eq__(self, other):
        if isinstance(other, Variable):
            return self.proxy.name == other.proxy.name

        return False

    def __repr__(self):
        return str(self.proxy)


def variableify(x: Any) -> Any:
    if isinstance(x, ProxyInterface):
        return Variable(x)

    return x


def unvariableify(x: Any) -> Any:
    if isinstance(x, Variable):
        return x.proxy

    return x


# TODO Document this class
class Proxy(VariableInterface, ProxyInterface):
    def __init__(self, name=None):
        trace = get_tracectx()
        if name is None:
            name = trace.make_name()
        else:
            trace.add_name(name)

        self._name = name

    @property
    def name(self):
        return self._name

    def replace_name(self, name):
        """Return a copy of this proxy with the given name."""
        return self.__class__(name=name)

    def __repr__(self):
        return f"{self._name}"

    def type_string(self):
        return "Any"


# NOTE NumberProxies are NOT Numbers
# TODO Maybe NumberProxies should be Numbers?
class NumberProxy(Proxy, NumberProxyInterface):
    def __init__(self, name=None, value=None, *, python_type):
        super().__init__(name)
        self.value = value
        self.python_type = python_type

    # NOTE: Python numbers hash to themselves, and this mimics that behavior
    def __hash__(self):
        return hash(self.value)

    def replace_name(self, name):
        """Return a copy of this proxy with the given name."""
        return self.__class__(name=name, value=self.value, python_type=self.python_type)

    def known_value(self):
        return self.value is not None


def pyval(x: Union[NumberProxy, Number]) -> Number:
    baseutils.check_type(x, (NumberProxy, Number))

    # NOTE This has to query NumberProxy, not Number, because NumberProxies are Numbers
    #   (but not all Numbers are NumberProxies)
    if isinstance(x, NumberProxy):
        return x.value

    return x


class ComplexProxy(NumberProxy, complex):
    def __new__(cls, *, name=None, value):
        if value is None:
            value = complex(float("nan"), float("nan"))

        return complex.__new__(cls, value)

    def __init__(self, name=None, value=None):
        NumberProxy.__init__(self, name=name, value=value, python_type=complex)

    def replace_name(self, name):
        """Return a copy of this proxy with the given name."""
        return ComplexProxy(name=name, value=self.value)

    def type_string(self):
        value_str = f"{self.value}" if self.value is not None else "?"
        return f"complex {value_str}"

    #
    # Elementwise unary operators
    #

    def __abs__(self):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__abs__()

        return langctx.abs(self)

    def __ceil__(self):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__ceil__()

        return langctx.ceil(self)

    def __floor__(self):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__floor__()

        return langctx.floor(self)

    def __invert__(self):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__invert__()

        return langctx.invert(self)

    def __neg__(self):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__neg__()

        return langctx.neg(self)

    def __pos__(self):
        if langctx is None:
            return pyval(self).__pos__()

        return self

    def __round__(self):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__round__()

        return langctx.round(self)

    def __trunc__(self):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__trunc__()

        return langctx.trunc(self)

    #
    # dtype conversion operators
    #

    def __complex__(self):
        raise self

    def __float__(self):
        raise NotImplemented

    def __int__(self):
        raise NotImplemented

    #
    # Elementwise binary operators
    #

    def __add__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self) + pyval(other)

        return langctx.add(self, other)

    def __radd__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(other) + pyval(self)

        return langctx.add(other, self)

    def __divmod__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__divmod__(pyval(other))

        return langctx.divmod(self, other)

    def __rdivmod__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__rdivmod__(pyval(other))

        return langctx.divmod(other, self)

    def __floordiv__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__floordiv__(pyval(other))

        return langctx.floor_divide(self, other)

    def __rfloordiv__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__rfloordiv__(pyval(other))

        return langctx.floor_divide(other, self)

    def __mod__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__mod__(pyval(other))

        return langctx.mod(self, other)

    def __rmod__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__rmod__(pyval(other))

        return langctx.mod(other, self)

    def __mul__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self) * pyval(other)

        return langctx.mul(self, other)

    def __rmul__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(other) * pyval(self)

        return langctx.mul(other, self)

    def __pow__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__pow__(pyval(other))

        return langctx.pow(self, other)

    def __rpow__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__rpow__(pyval(other))

        return langctx.pow(other, self)

    def __sub__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__sub__(pyval(other))

        return langctx.sub(self, other)

    def __rsub__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__rsub__(pyval(other))

        return langctx.sub(other, self)

    def __truediv__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__truediv__(pyval(other))

        return langctx.true_divide(self, other)

    def __rtruediv__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__rtruediv__(pyval(other))

        return langctx.true_divide(other, self)

    #
    # Logical operations
    #

    # def __eq__(self, other):
    #     langctx = get_langctx()
    #     return langctx.eq(self, other)

    # def __and__(self, other):
    #     langctx = get_langctx()
    #     return langctx.logical_and(self, other)

    # def __rand__(self, other):
    #     langctx = get_langctx()
    #     return langctx.logical_and(other, self)

    # def __ge__(self, other):
    #     langctx = get_langctx()
    #     return langctx.ge(self, other)

    # def __gt__(self, other):
    #     langctx = get_langctx()
    #     return langctx.gt(self, other)

    # def __le__(self, other):
    #     langctx = get_langctx()
    #     return langctx.le(self, other)

    # def __lt__(self, other):
    #     langctx = get_langctx()
    #     return langctx.lt(self, other)

    # def __ne__(self, other):
    #     langctx = get_langctx()
    #     return langctx.ne(self, other)

    # def __or__(self, other):
    #     langctx = get_langctx()
    #     return langctx.logical_or(self, other)

    # def __ror__(self, other):
    #     langctx = get_langctx()
    #     return langctx.logical_or(other, self)

    # def __xor__(self, other):
    #     langctx = get_langctx()
    #     return langctx.logical_xor(self, other)

    # def __rxor__(self, other):
    #     langctx = get_langctx()
    #     return langctx.logical_xor(other, self)

    #
    # Shift operations
    #

    def __lshift__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__lshift__(pyval(other))

        return langctx.lshift(self, other)

    def __rlshift__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__rlshift__(pyval(other))

        return langctx.lshift(other, self)

    def __rshift__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__rshift__(pyval(other))

        return langctx.rshift(self, other)

    def __rrshift__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__rrshift__(pyval(other))

        return langctx.rshift(other, self)

    #
    # Matmul
    #

    def __matmul__(self, other):
        raise NotImplemented

    def __rmatmul__(self, other):
        raise NotImplemented


# TODO Review dtype conversions
# TODO Review -9999 as the marker value for unknown values
class IntegerProxy(NumberProxy, int):
    def __new__(cls, *, name=None, value):
        if value is None:
            value = -9999

        return int.__new__(cls, value)

    def __init__(self, name=None, value=None):
        # NOTE bools are also integers in Python
        python_type = bool if isinstance(value, bool) else int
        NumberProxy.__init__(self, name=name, value=value, python_type=python_type)

    def replace_name(self, name):
        """Return a copy of this proxy with the given name."""
        return IntegerProxy(name=name, value=self.value)

    def type_string(self):
        value_str = f"{self.value}" if self.value is not None else "?"
        return f"int {value_str}"

    #
    # Elementwise unary operators
    #

    def __abs__(self):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__abs__()

        return langctx.abs(self)

    def __ceil__(self):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__ceil__()

        return langctx.ceil(self)

    def __floor__(self):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__floor__()

        return langctx.floor(self)

    def __invert__(self):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__invert__()

        return langctx.invert(self)

    def __neg__(self):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__neg__()

        return langctx.neg(self)

    def __pos__(self):
        if langctx is None:
            return pyval(self).__pos__()

        return self

    def __round__(self):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__round__()

        return langctx.round(self)

    def __trunc__(self):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__trunc__()

        return langctx.trunc(self)

    #
    # dtype conversion operators
    #

    def __complex__(self):
        raise NotImplemented

    def __float__(self):
        raise NotImplemented

    def __int__(self):
        return self

    #
    # Elementwise binary operators
    #

    def __add__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self) + pyval(other)

        return langctx.add(self, other)

    def __radd__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(other) + pyval(self)

        return langctx.add(other, self)

    def __divmod__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__divmod__(pyval(other))

        return langctx.divmod(self, other)

    def __rdivmod__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__rdivmod__(pyval(other))

        return langctx.divmod(other, self)

    def __floordiv__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__floordiv__(pyval(other))

        return langctx.floor_divide(self, other)

    def __rfloordiv__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__rfloordiv__(pyval(other))

        return langctx.floor_divide(other, self)

    def __mod__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__mod__(pyval(other))

        return langctx.mod(self, other)

    def __rmod__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__rmod__(pyval(other))

        return langctx.mod(other, self)

    def __mul__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self) * pyval(other)

        return langctx.mul(self, other)

    def __rmul__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(other) * pyval(self)

        return langctx.mul(other, self)

    def __pow__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__pow__(pyval(other))

        return langctx.pow(self, other)

    def __rpow__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__rpow__(pyval(other))

        return langctx.pow(other, self)

    def __sub__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__sub__(pyval(other))

        return langctx.sub(self, other)

    def __rsub__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__rsub__(pyval(other))

        return langctx.sub(other, self)

    def __truediv__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__truediv__(pyval(other))

        return langctx.true_divide(self, other)

    def __rtruediv__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__rtruediv__(pyval(other))

        return langctx.true_divide(other, self)

    #
    # Logical operations
    #
    # TODO Review these with constraint modeling

    # def __eq__(self, other):
    #     langctx = get_langctx()
    #     return langctx.eq(self, other)

    # def __and__(self, other):
    #     langctx = get_langctx()
    #     return langctx.logical_and(self, other)

    # def __rand__(self, other):
    #     langctx = get_langctx()
    #     return langctx.logical_and(other, self)

    # def __ge__(self, other):
    #     langctx = get_langctx()
    #     return langctx.ge(self, other)

    # def __gt__(self, other):
    #     langctx = get_langctx()
    #     return langctx.gt(self, other)

    # def __le__(self, other):
    #     langctx = get_langctx()
    #     return langctx.le(self, other)

    # def __lt__(self, other):
    #     langctx = get_langctx()
    #     return langctx.lt(self, other)

    # def __ne__(self, other):
    #     langctx = get_langctx()
    #     return langctx.ne(self, other)

    # def __or__(self, other):
    #     langctx = get_langctx()
    #     return langctx.logical_or(self, other)

    # def __ror__(self, other):
    #     langctx = get_langctx()
    #     return langctx.logical_or(other, self)

    # def __xor__(self, other):
    #     langctx = get_langctx()
    #     return langctx.logical_xor(self, other)

    # def __rxor__(self, other):
    #     langctx = get_langctx()
    #     return langctx.logical_xor(other, self)

    #
    # Shift operations
    #

    def __lshift__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__lshift__(pyval(other))

        return langctx.lshift(self, other)

    def __rlshift__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__rlshift__(pyval(other))

        return langctx.lshift(other, self)

    def __rshift__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__rshift__(pyval(other))

        return langctx.rshift(self, other)

    def __rrshift__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__rrshift__(pyval(other))

        return langctx.rshift(other, self)

    #
    # Matmul
    #

    def __matmul__(self, other):
        raise NotImplemented

    def __rmatmul__(self, other):
        raise NotImplemented


# TODO Review dtype conversions
class FloatProxy(NumberProxy, float):
    def __new__(cls, *, name=None, value):
        if value is None:
            value = float("nan")

        return float.__new__(cls, value)

    def __init__(self, name=None, value=None):
        NumberProxy.__init__(self, name=name, value=value, python_type=float)

    def replace_name(self, name):
        """Return a copy of this proxy with the given name."""
        return FloatProxy(name=name, value=self.value)

    def type_string(self):
        value_str = f"{self.value}" if self.value is not None else "?"
        return f"float {value_str}"

    #
    # Elementwise unary operators
    #

    def __abs__(self):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__abs__()

        return langctx.abs(self)

    def __ceil__(self):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__ceil__()

        return langctx.ceil(self)

    def __floor__(self):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__floor__()

        return langctx.floor(self)

    def __invert__(self):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__invert__()

        return langctx.invert(self)

    def __neg__(self):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__neg__()

        return langctx.neg(self)

    def __pos__(self):
        if langctx is None:
            return pyval(self).__pos__()

        return self

    def __round__(self):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__round__()

        return langctx.round(self)

    def __trunc__(self):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__trunc__()

        return langctx.trunc(self)

    #
    # dtype conversion operators
    #

    def __complex__(self):
        raise NotImplemented

    def __float__(self):
        return self

    def __int__(self):
        raise NotImplemented

    #
    # Elementwise binary operators
    #

    def __add__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self) + pyval(other)

        return langctx.add(self, other)

    def __radd__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(other) + pyval(self)

        return langctx.add(other, self)

    def __divmod__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__divmod__(pyval(other))

        return langctx.divmod(self, other)

    def __rdivmod__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__rdivmod__(pyval(other))

        return langctx.divmod(other, self)

    def __floordiv__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__floordiv__(pyval(other))

        return langctx.floor_divide(self, other)

    def __rfloordiv__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__rfloordiv__(pyval(other))

        return langctx.floor_divide(other, self)

    def __mod__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__mod__(pyval(other))

        return langctx.mod(self, other)

    def __rmod__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__rmod__(pyval(other))

        return langctx.mod(other, self)

    def __mul__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self) * pyval(other)

        return langctx.mul(self, other)

    def __rmul__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(other) * pyval(self)

        return langctx.mul(other, self)

    def __pow__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__pow__(pyval(other))

        return langctx.pow(self, other)

    def __rpow__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__rpow__(pyval(other))

        return langctx.pow(other, self)

    def __sub__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__sub__(pyval(other))

        return langctx.sub(self, other)

    def __rsub__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__rsub__(pyval(other))

        return langctx.sub(other, self)

    def __truediv__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__truediv__(pyval(other))

        return langctx.true_divide(self, other)

    def __rtruediv__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__rtruediv__(pyval(other))

        return langctx.true_divide(other, self)

    #
    # Logical operations
    #

    # def __eq__(self, other):
    #     langctx = get_langctx()
    #     return langctx.eq(self, other)

    # def __and__(self, other):
    #     langctx = get_langctx()
    #     return langctx.logical_and(self, other)

    # def __rand__(self, other):
    #     langctx = get_langctx()
    #     return langctx.logical_and(other, self)

    # def __ge__(self, other):
    #     langctx = get_langctx()
    #     return langctx.ge(self, other)

    # def __gt__(self, other):
    #     langctx = get_langctx()
    #     return langctx.gt(self, other)

    # def __le__(self, other):
    #     langctx = get_langctx()
    #     return langctx.le(self, other)

    # def __lt__(self, other):
    #     langctx = get_langctx()
    #     return langctx.lt(self, other)

    # def __ne__(self, other):
    #     langctx = get_langctx()
    #     return langctx.ne(self, other)

    # def __or__(self, other):
    #     langctx = get_langctx()
    #     return langctx.logical_or(self, other)

    # def __ror__(self, other):
    #     langctx = get_langctx()
    #     return langctx.logical_or(other, self)

    # def __xor__(self, other):
    #     langctx = get_langctx()
    #     return langctx.logical_xor(self, other)

    # def __rxor__(self, other):
    #     langctx = get_langctx()
    #     return langctx.logical_xor(other, self)

    #
    # Shift operations
    #

    def __lshift__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__lshift__(pyval(other))

        return langctx.lshift(self, other)

    def __rlshift__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__rlshift__(pyval(other))

        return langctx.lshift(other, self)

    def __rshift__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__rshift__(pyval(other))

        return langctx.rshift(self, other)

    def __rrshift__(self, other):
        langctx = get_langctx()

        if langctx is None:
            return pyval(self).__rrshift__(pyval(other))

        return langctx.rshift(other, self)

    #
    # Matmul
    #

    def __matmul__(self, other):
        raise NotImplemented

    def __rmatmul__(self, other):
        raise NotImplemented


# TODO Add remaining dunders
class TensorProxy(Proxy, TensorProxyInterface):
    def __init__(
        self,
        name=None,
        *,
        like=None,
        shape: Optional[Union[Tuple[int, ...], List[int]]] = None,
        device=None,
        dtype=None,
    ):
        super().__init__(name)

        self.device = None
        self.dtype = None
        self.shape = None

        if like is not None:
            baseutils.check_type(like, TensorProxy)
            self.shape = tuple(like.shape)
            self.device = like.device
            self.dtype = like.true_dtype

        self.shape = shape if shape is not None else self.shape
        self.device = device if device is not None else self.device
        self.dtype = dtype if dtype is not None else self.dtype
        self.dtype = dtypes.numbertype_to_dtype(self.dtype) if dtypes.is_numbertype(self.dtype) else self.dtype

        # Computes derived properties
        self.numel = reduce(operator.mul, self.shape, 1)

        # TODO Alias rank to ndim?
        self.ndim = len(self.shape)

        # Validates inputs
        baseutils.check_valid_shape(self.shape)
        baseutils.check_type(self.device, devices.Device)
        baseutils.check_type(self.dtype, dtypes.dtype)

        # NOTE for simplicity functions that want to reason about weak dtypes should explicitly request
        #   the true_dtype property
        self.true_dtype = self.dtype
        self.dtype = dtypes.to_strong_dtype(self.dtype)

    def replace_name(self, name):
        """Return a copy of this proxy with the given name."""
        return TensorProxy(name, like=self)

    def type_string(self):
        return f"{self.device} {self.dtype.shortname()}{list(self.shape)}"

    @property
    def size(self):
        langctx = get_langctx()
        return langctx.size(self)

    # NOTE __getattr__ is overridden to support language-specific methods
    def __getattr__(self, attr):
        langctx = get_langctx()
        method = langctx.method_lookup(attr)

        baseutils.check(method is not None, lambda: f"Unknown attribute {attr}", exception_type=AttributeError)

        return partial(method, self)

    #
    # Indexing operators
    #

    def __getitem__(self, key):
        ctx = get_langctx()
        return ctx.get_item(self, key)

    #
    # Elementwise unary operators
    #

    def __abs__(self):
        langctx = get_langctx()
        return langctx.abs(self)

    def __ceil__(self):
        langctx = get_langctx()
        return langctx.ceil(self)

    def __floor__(self):
        langctx = get_langctx()
        return langctx.floor(self)

    def __invert__(self):
        langctx = get_langctx()
        return langctx.invert(self)

    def __neg__(self):
        langctx = get_langctx()
        return langctx.neg(self)

    def __pos__(self):
        return self

    def __round__(self):
        langctx = get_langctx()
        return langctx.round(self)

    def __trunc__(self):
        langctx = get_langctx()
        return langctx.trunc(self)

    #
    # dtype conversion operators
    #

    def __complex__(self):
        raise NotImplemented

    def __float__(self):
        raise NotImplemented

    def __int__(self):
        raise NotImplemented

    #
    # Elementwise binary operators
    #

    def __add__(self, other):
        langctx = get_langctx()
        return langctx.add(self, other)

    def __radd__(self, other):
        langctx = get_langctx()
        return langctx.add(other, self)

    def __divmod__(self, other):
        langctx = get_langctx()
        return langctx.divmod(self, other)

    def __rdivmod__(self, other):
        langctx = get_langctx()
        return langctx.divmod(other, self)

    def __eq__(self, other):
        langctx = get_langctx()
        return langctx.eq(self, other)

    def __floordiv__(self, other):
        langctx = get_langctx()
        return langctx.floor_divide(self, other)

    def __rfloordiv__(self, other):
        langctx = get_langctx()
        return langctx.floor_divide(other, self)

    def __mod__(self, other):
        langctx = get_langctx()
        return langctx.mod(self, other)

    def __rmod__(self, other):
        langctx = get_langctx()
        return langctx.mod(other, self)

    def __mul__(self, other):
        langctx = get_langctx()
        return langctx.mul(self, other)

    def __rmul__(self, other):
        langctx = get_langctx()
        return langctx.mul(other, self)

    def __pow__(self, other):
        langctx = get_langctx()
        return langctx.pow(self, other)

    def __rpow__(self, other):
        langctx = get_langctx()
        return langctx.pow(other, self)

    def __sub__(self, other):
        langctx = get_langctx()
        return langctx.sub(self, other)

    def __rsub__(self, other):
        langctx = get_langctx()
        return langctx.sub(other, self)

    def __truediv__(self, other):
        langctx = get_langctx()
        return langctx.true_divide(self, other)

    def __rtruediv__(self, other):
        langctx = get_langctx()
        return langctx.true_divide(other, self)

    #
    # Logical operations
    #

    def __and__(self, other):
        langctx = get_langctx()
        return langctx.logical_and(self, other)

    def __rand__(self, other):
        langctx = get_langctx()
        return langctx.logical_and(other, self)

    def __ge__(self, other):
        langctx = get_langctx()
        return langctx.ge(self, other)

    def __gt__(self, other):
        langctx = get_langctx()
        return langctx.gt(self, other)

    def __le__(self, other):
        langctx = get_langctx()
        return langctx.le(self, other)

    def __lt__(self, other):
        langctx = get_langctx()
        return langctx.lt(self, other)

    def __ne__(self, other):
        langctx = get_langctx()
        return langctx.ne(self, other)

    def __or__(self, other):
        langctx = get_langctx()
        return langctx.logical_or(self, other)

    def __ror__(self, other):
        langctx = get_langctx()
        return langctx.logical_or(other, self)

    def __xor__(self, other):
        langctx = get_langctx()
        return langctx.logical_xor(self, other)

    def __rxor__(self, other):
        langctx = get_langctx()
        return langctx.logical_xor(other, self)

    #
    # Shift operations
    #

    def __lshift__(self, other):
        langctx = get_langctx()
        return langctx.lshift(self, other)

    def __rlshift__(self, other):
        langctx = get_langctx()
        return langctx.lshift(other, self)

    def __rshift__(self, other):
        langctx = get_langctx()
        return langctx.rshift(self, other)

    def __rrshift__(self, other):
        langctx = get_langctx()
        return langctx.rshift(other, self)

    #
    # Matmul
    #

    def __matmul__(self, other):
        langctx = get_langctx()
        return langctx.matmul(self, other)

    def __rmatmul__(self, other):
        langctx = get_langctx()
        return langctx.matmul(other, self)


#
# Helpers for creating and working with proxies
#

_cls_to_number_proxy_map = {
    float: FloatProxy,
    int: IntegerProxy,
    bool: IntegerProxy,
}


def numberproxy(cls: Type, value: Optional[Number]) -> NumberProxy:
    pcls = _cls_to_number_proxy_map[cls]
    return pcls(value=value)


def is_proxyable(x: Any) -> bool:
    if isinstance(x, Number):
        return True

    # NOTE The langctx may not have defined the tensor_cls attribute
    #   (the core language context has no associated tensor_cls)
    langctx = langctx_for(x)
    try:
        tensor_cls = langctx.tensor_cls
        return isinstance(x, tensor_cls)
    except AttributeError:
        return False


# TODO Improve type annotation to return type of X or Proxy
# TODO defer to langctx for tensor type -- consider all possible langctxs
# TODO maybe consider what happens when a proxy is passed to this
# TODO handle complex number type
def proxy(x: Any, *, name=None) -> Any:
    langctx = langctx_for(x)

    try:
        tensor_cls = langctx.tensor_cls
        if isinstance(x, tensor_cls):
            return langctx.tensorproxy(name, x)
    except AttributeError:
        pass

    if isinstance(x, Number):
        if isinstance(x, complex):
            return ComplexProxy(name=name, value=x)
        if isinstance(x, float):
            return FloatProxy(name=name, value=x)
        if isinstance(x, int):
            return IntegerProxy(name=name, value=x)

        raise NotImplementedError

    return x
