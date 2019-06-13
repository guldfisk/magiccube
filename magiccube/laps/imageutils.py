import typing as t

from PIL import Image, ImageDraw, ImageFont
import numpy as np
import aggdraw


def center_box(
	parent_width: int,
	parent_height: int,
	child_width: int,
	child_height: int,
) -> t.Tuple[int, int, int, int]:
	"""
	Get absolute coordinates for box centered inside box

	:param parent_width: Width of parent box
	:param parent_height: Height of parent box
	:param child_width: Width of child box
	:param child_height: Height of child box
	:return: tuple: upper corner x, upper corner y, lower corner x, lower corner y
	"""
	parent_center_x, parent_center_y = parent_width // 2, parent_height // 2
	child_center_x, child_center_y = child_width // 2, child_height // 2

	return (
		parent_center_x - child_center_x,
		parent_center_y - child_center_y,
		parent_center_x + child_center_x,
		parent_center_y + child_center_y,
	)


def draw_text_with_outline(
	draw: ImageDraw.Draw,
	xy: t.Tuple[int, int],
	text: str,
	font,
	color: t.Tuple[int, int, int],
	background_color: t.Tuple[int, int, int],
) -> None:
	"""
	Draw outlined text

	:param draw: target
	:param xy: location
	:param text: content
	:param font: font
	:param color: text color
	:param background_color: outline color
	:return: None
	"""
	_xy = np.asarray(xy)
	offset_range = (-1, 0, 1)

	for offset in (
		(x, y)
		for x in offset_range
		for y in offset_range
	):
		draw.multiline_text(
			xy = _xy+np.asarray(offset),
			text = text,
			font = font,
			fill = background_color,
			align = 'center',
		)

	draw.multiline_text(
		xy = _xy,
		text = text,
		font = font,
		fill = color,
		align='center',
	)


def draw_name(
	draw: ImageDraw.Draw,
	name: str,
	box: t.Tuple[int, int, int, int],
	font_path: str,
	font_size: int = 40
) -> None:
	"""
	Draw outlined text on image centered in box, downscaling font if necessary to fit.
	:param draw: target
	:param name: content
	:param box: location
	:param font_path: path to truetype font
	:param font_size: max font size
	:return:
	"""

	if not name:
		return

	x, y, w, h = box

	font = ImageFont.truetype(font_path, font_size)
	text_width, text_height = draw.multiline_textsize(name, font)

	downsize_factor = min(
		w / text_width,
		h / text_height,
	)
	if downsize_factor < 1.:
		font = ImageFont.truetype(font_path, int(font_size * downsize_factor))
		text_width, text_height = draw.multiline_textsize(name, font)

	x_1, y_1, x_2, y_2 = center_box(w, h, text_width, text_height)

	draw_text_with_outline(
		draw = draw,
		xy = (x_1+x, y_1+y),
		text = name,
		font = font,
		color = (255,) * 3,
		background_color = (0,) * 3,
	)


LEFT_SIDE = 0x1
TOP_SIDE = 0x2
RIGHT_SIDE = 0x4
BOTTOM_SIDE = 0x8

VERTICAL_SIDES = LEFT_SIDE + RIGHT_SIDE
HORIZONTAL_SIDES = TOP_SIDE + BOTTOM_SIDE

ALL_SIDES = VERTICAL_SIDES + HORIZONTAL_SIDES


def inline_box(
	draw, #aggdraw draw
	box: t.Tuple[int, int, int, int],
	width: int = 5,
	color: t.Tuple[int, int, int] = (0, 0, 0),
	sides: int = ALL_SIDES,
) -> None:
	"""
	Draw border inside box
	:param draw: Target
	:param box: Location
	:param width: Border width
	:param color: Border color
	:param sides: Sides to draw border on
	:return: None
	"""
	x, y, w, h = box
	x_1, y_1, x_2, y_2 = x, y, x + w, y + h
	brush = aggdraw.Brush(color=color)

	if sides & 1:
		draw.rectangle(
			(x_1, y_1, x_1 + width, y_2),
			brush,
		)
	if sides >> 1 & 1:
		draw.rectangle(
			(x_1, y_1, x_2, y_1 + width),
			brush,
		)
	if sides >> 2 & 1:
		draw.rectangle(
			(x_2 - width, y_1, x_2, y_2),
			brush,
		)
	if sides >> 3 & 1:
		draw.rectangle(
			(x_1, y_2 - width, x_2, y_2),
			brush,
		)

	draw.flush()


def triangled_inlined_box(
	draw, #aggdraw draw
	box: t.Tuple[int, int, int, int],
	width: int = 5,
	color: t.Tuple[int, int, int] = (0, 0, 0),
	bar_color: t.Tuple[int, int, int] = (255, 255, 255),
	triangle_length: int = 2,
	sides: int = ALL_SIDES,
) -> None:
	"""
	Draw border inside box with triangles in both ends of each bar
	:param draw: Target
	:param box: Location
	:param width: Border width
	:param color: Border color
	:param bar_color: Triangle color
	:param triangle_length: In pixels
	:param sides: Sides to draw border and triangles
	:return: None
	"""
	hw = width // 2
	x, y, w, h = box
	x_1, y_1, x_2, y_2 = x, y, x + w, y + h

	triangle_brush = aggdraw.Brush(color=bar_color)
	
	inline_box(
		draw = draw,
		box = box,
		width = width,
		color = color,
		sides = sides,
	)
	
	if sides & 1:
		draw.polygon(
			(
				x_1, y_2,
				x_1 + width, y_2,
				x_1 + hw, y_2 - triangle_length,
			),
			None,
			triangle_brush,
		)
		draw.polygon(
			(
				x_1, y_1,
				x_1 + width, y_1,
				x_1 + hw, y_1 + triangle_length,
			),
			None,
			triangle_brush,
		)
	if sides >> 1 & 1:
		draw.polygon(
			(
				x_1, y_1,
				x_1, y_1 + width,
				x_1 + triangle_length, y_1 + hw,
			),
			None,
			triangle_brush,
		)
		draw.polygon(
			(
				x_2, y_1,
				x_2, y_1 + width,
				x_2 - triangle_length, y_1 + hw,
			),
			None,
			triangle_brush,
		)
	if sides >> 2 & 1:
		draw.polygon(
			(
				x_2, y_1,
				x_2 - width, y_1,
				x_2 - hw, y_1 + triangle_length,
			),
			None,
			triangle_brush,
		)
		draw.polygon(
			(
				x_2, y_2,
				x_2 - width, y_2,
				x_2 - hw, y_2 - triangle_length,
			),
			None,
			triangle_brush,
		)
	if sides >> 3 & 1:
		draw.polygon(
			(
				x_2, y_2,
				x_2, y_2 - width,
				x_2 - triangle_length, y_2 - hw,
			),
			None,
			triangle_brush,
		)
		draw.polygon(
			(
				x_1, y_2,
				x_1, y_2 - width,
				x_1 + triangle_length, y_2 - hw,
			),
			None,
			triangle_brush,
		)

	draw.flush()


def shrunk_box(
	x: int,
	y: int,
	w: int,
	h: int,
	shrink: int,
	sides: int = ALL_SIDES,
) -> t.Tuple[int, int, int, int]:
	"""
	Returns box shrunk on select sides. Operates on x, y, w, h box.
	:param x: Box x position
	:param y: Box y position
	:param w: Box width
	:param h: box height
	:param shrink: Amount to shrink box by
	:param sides: Sides to shrink box on
	:return: Tuple shrunk box x, y, w, h
	"""
	return (
		x + shrink if sides & 1 else x,
		y + shrink if sides >> 1 & 1 else y,
		w - (shrink if sides >> 2 & 1 else 0) - (shrink if sides & 1 else 0),
		h - (shrink if sides >> 3 & 1 else 0) - (shrink if sides >> 1 & 1 else 0),
	)


def _rounded_corner_path(
	box: t.Tuple[int, int, int, int],
	corner_radius: int,
):
	path = aggdraw.Path()

	cr = corner_radius
	x, y, w, h = box

	path.moveto(x + cr, y)

	path.lineto(x + w - cr, y)
	path.curveto(
		x + w - cr / 2,
		y,
		x + w,
		y + cr / 2,
		x + w,
		y + cr,
	)

	path.lineto(x + w, y + h - cr)
	path.curveto(
		x + w,
		y + h - cr / 2,
		x + w - cr / 2,
		y + h,
		x + w - cr,
		y + h,
	)

	path.lineto(x + cr, y + h)
	path.curveto(
		x + cr / 2,
		y + h,
		x,
		y + h - cr / 2,
		x,
		y + h - cr,
	)

	path.lineto(x, y + cr)
	path.curveto(
		x,
		y + cr / 2,
		x + cr / 2,
		y,
		x + cr,
		y,
	)

	return path


def rounded_corner_box(
	draw, #aggdraw draw
	box: t.Tuple[int, int, int, int],
	corner_radius: int,
	line_width: int = 1,
	line_color: t.Tuple[int, int, int] = (0, 0, 0),
) -> None:
	"""

	:param draw:
	:param box:
	:param corner_radius:
	:param line_width:
	:param line_color:
	:return:
	"""

	pen = aggdraw.Pen(line_color, line_width, 255)
	path = _rounded_corner_path(box, corner_radius)
	draw.path(path, pen)
	draw.flush()


def filled_rounded_box(
	draw,  # aggdraw draw
	box: t.Tuple[int, int, int, int],
	corner_radius: int,
	color: t.Tuple[int, int, int] = (0, 0, 0),
) -> None:
	path = _rounded_corner_path(
		box,
		corner_radius,
	)
	brush = aggdraw.Brush(color, 255)
	draw.path(path, brush)
	draw.flush()



def section(value: int, partitions: int) -> t.Iterable[t.Tuple[int, int]]:
	"""
	Divide length into n int partitions. The total length of the partitions
	correspond to the divided length, with any leftover given to the last partition
	:param value: length to divide
	:param partitions: Number of partitions
	:return: iterable of start_offset, end_offset
	"""
	offset, leftover = value // partitions, value % partitions

	if partitions > 1:
		for i in range(partitions-1):
			yield offset * i, offset * (i+1)

	yield value - offset - leftover, value


def fit_image(image: Image.Image, width: int, height: int) -> Image.Image:
	"""
	Fit image to given size, scaling up if to small, cropping if to big.
	:param image: Image to fit
	:param width: Target width
	:param height: Target height
	:return: Rescaled image
	"""
	if width > image.width:
		_image = image.resize(
			(width, image.height * width // image.width),
			resample=Image.LANCZOS,
		)
	elif height > image.height:
		_image = image.resize(
			(image.width * height // image.height, height),
			resample=Image.LANCZOS,
		)
	else:
		_image = image

	if _image.width == width and _image.height == height:
		return image

	return _image.crop(center_box(_image.width, _image.height, width, height))

