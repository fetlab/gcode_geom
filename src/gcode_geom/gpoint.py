from __future__ import annotations     #Allow self-referencing for typing inside class
from copy import copy
from Geometry3D import Point, Vector
from fastcore.basics import listify
from .angle import Angle, atan2
from . import Number

class GPoint(Point):
	def __init__(self, *args, **kwargs):
		"""Pass Geometry3D.Point arguments or a gcline.GCLine and optionally a *z*
		argument. If *z* is missing it will be set to 0."""
		self.line = None
		z = kwargs.get('z', 0) or 0

		if len(args) == 1:
			#Using type() rather than isinstance() to avoid circular import issues
			if type(args[0]).__name__ == 'GCLine':
				l = args[0]
				if not (l.code in ('G0', 'G1') and 'X' in l.args and 'Y' in l.args):
					raise ValueError(f"GCLine instance isn't an X or Y move:\n\t{args[0]}")
				super().__init__(l.args['X'], l.args['Y'], z)
				self.line = l

			elif isinstance(args[0], (list,tuple)):
				if len(args[0]) == 2:
					super().__init__(*args[0], 0)
				else:
					super().__init__(args[0])

			elif isinstance(args[0], Point):
				super().__init__(
					kwargs.get('x', args[0].x),
					kwargs.get('y', args[0].y),
					kwargs.get('z', args[0].z))

			else:
				raise ValueError(f'Invalid type for arg to GPoint: ({type(args[0])}) {args[0]}')

		elif len(args) == 2:
			super().__init__(*args, 0)

		elif len(args) == 3:
			super().__init__(*args)

		else:
			raise ValueError(f"Can't init GPoint with args {args}")


	def __repr__(self):
		return "{{{:>6.2f}, {:>6.2f}, {:>6.2f}}}".format(self.x, self.y, self.z)


	def __neg__(self):
		return self.__class__(-self.x, -self.y, -self.z)


	def __add__(self, other:GPoint): return self.moved(Vector(*other))
	def __sub__(self, other:GPoint): return self.moved(Vector(*-other))

	@property
	def xy(self): return self.x, self.y

	@property
	def xyz(self): return self.x, self.y, self.z


	def as2d(self) -> GPoint:
		"""Return a copy of this point with *z* set to 0. If z is already 0, return self."""
		if self.z == 0: return self
		return self.copy(z=0)


	def inside(self, seglist):
		"""Return True if this point is inside the polygon formed by the Segments
		in seglist."""
		from .gsegment import GSegment
		#We make a segment from this point to 0,0,0 and test intersections; if
		# there are an even number, the point is inside the polygon.
		test_seg = GSegment(self.as2d(), (0,0,0))
		return len([s for s in seglist if test_seg.intersection(s.as2d())]) % 2


	def copy(self, x=None, y=None, z=None) -> GPoint:
		c = copy(self)
		if x is not None: c.x = x
		if y is not None: c.y = y
		if z is not None: c.z = z
		return c


	def moved(self, vec:Vector=None, x:Number|None=None, y:Number|None=None, z:Number|None=None) -> GPoint:
		"""Return a copy of this point moved by vector vec or by x/y/z."""
		x, y, z = vec[:] if vec else (x or 0, y or 0, z or 0)
		return self.__class__(self.x + x, self.y + y, self.z + z)


	def intersecting(self, check) -> set:
		return {o for o in listify(check) if self in o}


	def angle(self, other:Point=None) -> Angle:
		"""Return the angle in degrees of a line drawn through this point from
		either the origin or a second point (ignoring the z-coordinate)."""
		x, y = (other.x, other.y) if isinstance(other, Point) else (0, 0)
		return atan2(self.y - y, self.x - x)
