from __future__ import annotations
from copy import copy
from typing import Collection, Set, List
from Geometry3D import Vector, Segment, Point, Line
from fastcore.basics import listify
from .gpoint import GPoint
from .gcast import gcast
from .utils import distance_linelike_point
from .angle import Angle, atan2

def list2gsegments(points:Collection):
	return [GSegment(s, e) for s,e in points]


class GSegment(Segment):
	def __init__(self, a, b=None, z=None, gc_lines=None, is_extrude=False, **kwargs):
		"""Instantiate a GSegment.

		If the first argument is a Segment, the second argument will be ignored and
		a copy of the segment will be returned.

		Otherwise, the first two arguments can be any combination of Point, GCLine,
		or tuple/list (passed to the GPoint constructor).
		"""
		#Label whether this is an extrusion move or not
		self.is_extrude = is_extrude

		#Save the movement lines of gcode
		self.gc_line1 = None
		self.gc_line2 = None

		#Save *all* lines of gcode involved in this segment
		self.gc_lines = gc_lines

		#Argument |a| is a GSegment: instantiate a copy
		if isinstance(a, Segment):
			if b is not None:
				raise ValueError('Second argument must be None when first is a Segment')
			copyseg = a
			#Make copies of the start/end points to ensure we avoid accidents
			a = copy(kwargs.get('start_point', copyseg.start_point))
			b = copy(kwargs.get('end_point',   copyseg.end_point))
			gc_lines   = getattr(copyseg, 'gc_lines', []) if gc_lines is None else gc_lines
			is_extrude = getattr(copyseg, 'is_extrude', is_extrude)

		#If instantiating a copy, |a| and |b| have been set from the passed GSegment
		if isinstance(a, Point):
			point1 = a if isinstance(a, GPoint) else GPoint(a)
		elif type(a).__name__ == 'GCLine': #Using type() rather than isinstance() to avoid circular import issues
			point1 = GPoint(a, z=z)
			self.gc_line1 = a
			self.gc_lines.append(a)
		elif isinstance(a, (tuple,list)):
			point1 = GPoint(*a)
		else:
			print(a, type(a), type(a) == GSegment)
			raise ValueError("Attempt to instantiate a GSegment with argument |a| as "
					f"type {type(a)}, but only <GSegment>, <Point>, <GCLine>, <tuple> and <list> are supported.\n"
					" If this occurrs in a Jupyter notebook, it's because reloading messes things up. Try restarting the kernel.")

		if isinstance(b, Point):
			point2 = b if isinstance(b, GPoint) else GPoint(b)
		elif type(b).__name__ == 'GCLine': #Using type() rather than isinstance() to avoid circular import issues
			point2 = GPoint(b, z=z)
			self.gc_line2 = b
			self.gc_lines.append(b)
		elif isinstance(b, (tuple,list)):
			point2 = GPoint(*b)
		else:
			raise ValueError(f"Arg b is type {type(b)} = {b} but that's not supported!")

		#Ensure that we're not going to overwrite anything
		if point1 is a: point1 = point1.copy()
		if point2 is b: point2 = point2.copy()

		if z is not None:
			point1.z = point2.z = z

		if point1 == point2:
			raise ValueError("Cannot initialize a Segment with two identical Points\n"
					f"Init args: a={a}, b={b}, z={z}")

		self.line = Line(point1, point2)
		self.start_point = point1
		self.end_point   = point2

		#Sort any gcode lines by line number
		if self.gc_lines:
			self.gc_lines.sort()


	def __repr__(self) -> str:
		if not(self.gc_line1 and self.gc_line2):
			return "<{}←→{} ({:.2f} mm)>".format(
					self.start_point,
					self.end_point,
					self.length)
		return "<[{:>2}] {}:{}←→{}:{} ({:.2f} mm)>".format(
				len(self.gc_lines),
				self.gc_line1.lineno, self.start_point,
				self.gc_line2.lineno, self.end_point,
				self.length)


	#We define __eq__ so have to inherit __hash__:
	# https://docs.python.org/3/reference/datamodel.html#object.__hash__
	__hash__ = Segment.__hash__

	intersection = gcast(Segment.intersection)

	def __eq__(self, other) -> bool:
		return False if not isinstance(other, Segment) else super().__eq__(other)


	@property
	def length(self): return super().length()


	def intersecting(self, check, ignore:Point | Collection[Point]=()) -> Set[Segment]:
		"""Return objects in check that this GSegment intersects with, optionally
		ignoring intersections with Points in ignore."""
		ignore = [None] + listify(ignore)
		return {o for o in listify(check) if
				self != o and
				(isinstance(o, Point) and o not in ignore and o in self) or
				(self.intersection(o) not in ignore)}


	def intersections(self, check:Collection[Segment], ignore:Point|Collection[Point]=()) -> dict[Segment,Point]:
		"""Return {seg_from_check: intersection, ...}"""
		isecs = {seg: self.intersection(seg) for seg in listify(check)}
		return {seg:isec for seg,isec in isecs.items() if isec not in listify(ignore)}


	def intersection2d(self, other):
		return self.as2d().intersection(other.as2d())


	def as2d(self):
		if self.start_point.z == 0 and self.end_point.z == 0:
			return self
		return self.__class__(self.start_point.as2d(), self.end_point.as2d())


	def set_z(self, z):
		"""Set both endpoints of this Segment to a new z."""
		return self.copy(z=z)


	def copy(self, start_point=None, end_point=None, z=None, **kwargs):
		seg = self.__class__(self, None,
			start_point=start_point or self.start_point,
			end_point=end_point     or self.end_point,
			z=z, gc_lines=self.gc_lines, is_extrude=self.is_extrude, **kwargs)
		seg.gc_line1 = self.gc_line1
		seg.gc_line2 = self.gc_line2

		return seg


	def moved(self, vec=None, x=None, y=None, z=None):
		"""Return a copy of this GSegment moved by vector vec or coordinates."""
		sp = self.start_point if isinstance(self.start_point, GPoint) else GPoint(self.start_point)
		ep = self.end_point   if isinstance(self.end_point,   GPoint) else GPoint(self.end_point)
		return self.copy(sp.moved(vec, x, y, z), ep.moved(vec, x, y, z))


	def rotated(self, by:Angle=Angle(degrees=0), to:Angle=Angle(degrees=0), from_end=False):
		"""Return a copy of this GSegment rotated by `by_angle` or to `to_angle`
		around its start point (or end point if `from_end` is False)."""
		if by != 0 and to != 0:
			raise ValueError(f"Can't rotate both by_angle ({by}) and to_angle ({to})")

		from .ghalfline import GHalfLine
		hl = GHalfLine(self.start_point, self.end_point).rotated(
			(to - self.angle()) if to else by)
		return self.__class__(self.start_point,
													hl.point + hl.line.dv.normalized() * self.length)


	def parallels2d(self, distance=1, inc_self=False):
		"""Return two GSegments parallel to this one, offset by `distance` to either
		side. Include this segment if in_self is True."""
		v = self.line.dv.normalized()
		mv1 = Vector(v[1], -v[0], v[2]) * distance
		mv2 = Vector(-v[1], v[0], v[2]) * distance
		return [self.moved(mv1), self.moved(mv2)] + ([self] if inc_self else [])


	#Support +/- with a GPoint by treating the point as a vector
	def __add__(self, other:GPoint): return self.moved(Vector(*other))
	def __sub__(self, other:GPoint): return self.moved(Vector(*-other))


	def __mul__(self, other):
		"""Lengthen the segment, preserving its start point."""
		if not isinstance(other, (int, float)):
			return self * other
		return self.copy(end_point=self.end_point.moved(
			self.line.dv.normalized() * self.length * (other-1)))


	def point_at_dist(self, dist:int|float, from_end=False) -> GPoint:
		"""Return the point that is `dist` from this GSegment's start point (end
		point) in the direction of the GSegment. Note that the returned point might
		not be on the GSegment!"""
		if from_end:
			return self.end_point - self.line.dv.normalized() * dist
		else:
			return self.start_point + self.line.dv.normalized() * dist


	def split_at(self, split_loc:GPoint) -> List:
		"""Return a set of two GSegments resulting from splitting this one into two
		pieces at `location`."""
		if split_loc not in self:
			raise ValueError(f"Requested split location {split_loc} isn't on {self}")

		#Create the new segment pieces
		seg1 = self.copy(end_point   = split_loc)
		seg2 = self.copy(start_point = split_loc)

		#Update the wrapped gcode lines
		if self.gc_line1 and self.gc_line2:

			#First segment
			seg1_frac = seg1.length / self.length
			seg1_args = {
					'X': split_loc.x,
					'Y': split_loc.y,
					'E': self.gc_line2.args['E'] * seg1_frac,
			}
			if 'F' in self.gc_line2.args:
				seg1_args['F'] = self.gc_line2.args['F']

			seg1.gc_line2 = self.gc_line2.__class__(
					code=self.gc_line2.code,
					args=seg1_args,
					lineno=self.gc_line1.lineno+seg1_frac)
			seg1.gc_line2.relative_extrude = seg1.gc_line1.relative_extrude * seg1_frac


			#Second segment
			seg2_frac = 1 - seg1_frac
			seg2.gc_line1 = copy(seg1.gc_line2)
			seg2.gc_line2 = self.gc_line2.copy(args={'E': self.gc_line2.args['E'] * seg2_frac})
			seg2.gc_line2.relative_extrude *= seg2_frac

			#Cleanup
			seg1.gc_line1.fake = True
			seg1.gc_line2.fake = True
			seg2.gc_line1.fake = True
			seg2.gc_line2.fake = True

			seg1.gc_lines = copy(self.gc_lines)
			seg1.gc_lines[self.gc_line1.lineno] = seg1.gc_line1
			seg1.gc_lines[self.gc_line2.lineno] = seg1.gc_line2

			seg2.gc_lines = copy(self.gc_lines)
			seg2.gc_lines[self.gc_line1.lineno] = seg2.gc_line1
			seg2.gc_lines[self.gc_line2.lineno] = seg2.gc_line2

		return [seg1, seg2]


	def split(self, locations:GPoint|Collection[GPoint]) -> list[GSegment]:
		"""Split this GSegment into multiple pieces at the given `locations`."""
		locations = listify(locations)
		splits    = []
		to_split  = self

		for loc in sorted(locations, key=self.start_point.distance):
			seg1, seg2 = to_split.split_at(loc)
			splits.append(seg1)
			to_split = seg2
		splits.append(seg2)

		return splits


	def distance(self, other):
		if isinstance(other, GPoint):
			return other.distance(self.closest(other))
		return distance_linelike_point(self, other)


	#Source: https://math.stackexchange.com/a/3128850/205121
	def closest(self, other:GPoint) -> GPoint:
		"""Return the point on this GSegment that is closest to the given point."""
		#Convert points to vectors for easy math
		seg_start = Vector(self.start_point.x, self.start_point.y, 0)
		seg_end   = Vector(self.end_point.x,   self.end_point.y,   0)
		p         = Vector(other.x,            other.y,            0)

		v = seg_end - seg_start
		u = seg_start - p

		vu = v[0]*u[0] + v[1]*u[1]
		vv = v * v

		t = -vu / vv

		if 0 < t < 1: return GPoint(*(self.line.dv * t + self.start_point))
		elif t <= 0:  return self.start_point
		else:         return self.end_point


	def angle(self) -> Angle:
		"""Return the angle between this segment and the X axis."""
		return atan2(self.end_point.y - self.start_point.y, self.end_point.x - self.start_point.x)
