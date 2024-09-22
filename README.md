# gcode-geom

This is a library that offers tools for converting between Gcode and geometry. The following classes are available; please check their source for more detail:

* `Angle`: an angle type to avoid confusion between radians and degrees.
* `GPoint`: a point in space. Can be instantiated from a line of Gcode.
* `GSegent`: a segment representing printed geometry or a move.
* `GHalfLine`: a half-line, or ray; useful for intersection tests.
* `GPolyLine`: a polyline made of a list of `GPoint`s, representable as `GSegment`s.

There are a number of handy utility functions in `utils.py`.
