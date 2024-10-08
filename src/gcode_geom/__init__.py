#Monkey-patch Geometry3D to remove its unify_types function, which appears to
# be unecessary and is extremely slow
import Geometry3D
Geometry3D.geometry.point.unify_types = lambda x: x
Geometry3D.utils.vector.unify_types   = lambda x: x

#Create Number type
Number = float|int

from .gpoint import GPoint
from .gsegment import GSegment, list2gsegments
from .ghalfline import GHalfLine
from .gpolyline import GPolyLine
from .angle import Angle, atan2
from .utils import tangent_points

from Geometry3D import Vector
Vector.__repr__ = lambda self: "↗{:>6.2f}° ({:>6.2f}, {:>6.2f}, {:>6.2f})".format(
		atan2(self[1], self[0]), *self._v)

__all__ = (
	'Angle',
	'GPoint',
	'GSegment',
	'GHalfLine',
	'GPolyLine',
	'tangent_points',
	'list2gsegments',
)
