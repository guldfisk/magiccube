import typing as t

from PIL import Image, ImageDraw, ImageFont
import numpy as np
import aggdraw


def center_box(parent_width: int, parent_height: int, child_width: int, child_height: int):
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
):
	_xy = np.asarray(xy)
	for offset in (
		(-1, -1),
		(-1, 1),
		(-1, 0),
		(0, -1),
		(0, 1),
		(1, -1),
		(1, 0),
		(1, 1),
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
):

	if not name:
		return

	x, y, width, height = box

	font = ImageFont.truetype(font_path, font_size)
	text_width, text_height = draw.multiline_textsize(name, font)

	if text_width>width:
		font = ImageFont.truetype(font_path, font_size * width // text_width )
		text_width, text_height = draw.multiline_textsize(name, font)
	if 	text_height>height:
		font = ImageFont.truetype(font_path, font_size * height // text_height )
		text_width, text_height = draw.multiline_textsize(name, font)

	x_1, y_1, x_2, y_2 = center_box(width, height, text_width, text_height)

	draw_text_with_outline(
		draw = draw,
		xy = (x_1+x, y_1+y),
		text = name,
		font = font,
		color = (255, 255, 255),
		background_color = (0, 0, 0),
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
	offset = shrink
	return (
		x + offset if sides & 1 else x,
		y + offset if sides >> 1 & 1 else y,
		w - (offset if sides >> 2 & 1 else 0) - (offset if sides & 1 else 0),
		h - (offset if sides >> 3 & 1 else 0) - (offset if sides >> 1 & 1 else 0),
	)


# def inline_box(
# 	draw: ImageDraw.Draw,
# 	box: t.Tuple[int, int, int, int],
# 	width: int = 10,
# 	color: t.Tuple[int, int, int] = (0, 0, 0),
# 	sides: int = ALL_SIDES,
# ) -> None:
# 	line_box(
# 		draw = draw,
# 		box = shrunk_box(*box, width // 2),
# 		width = width,
# 		color = color,
# 		sides = sides,
# 	)


def rounded_corner_box(
	image: Image.Image,
	corner_radius: int,
	line_width: int = 1,
	line_color: t.Tuple[int, int, int] = (0, 0, 0),
) -> None:
	draw = aggdraw.Draw(image)

	pen = aggdraw.Pen(line_color, line_width, 255)

	path = aggdraw.Path()

	cr = corner_radius
	w, h = image.size

	path.moveto(cr, 0)

	path.lineto(w - cr, 0)
	path.curveto(w - cr / 2, 0, w, cr / 2, w, cr)

	path.lineto(w, h - cr)
	path.curveto(w, h - cr / 2, w - cr / 2, h, w - cr, h)

	path.lineto(cr, h)
	path.curveto(cr / 2, h, 0, h - cr / 2, 0, h - cr)

	path.lineto(0, cr)
	path.curveto(0, cr / 2, cr / 2, 0, cr, 0)

	draw.path(path, pen)

	draw.flush()


def section(value: int, partitions: int) -> t.Iterable[t.Tuple[int, int]]:
	offset, leftover = value // partitions, value % partitions

	if partitions > 1:
		for i in range(partitions-1):
			yield offset * i, offset * (i+1)

	yield value - offset - leftover, value


def fit_image(image: Image.Image, width: int, height: int) -> Image.Image:
	if width > image.width:
		_image = image.resize((width, image.height * width // image.width))
	elif height > image.height:
		_image = image.resize((image.width * height // image.height, height))
	else:
		_image = image

	if _image.width == width and _image.height == height:
		return image

	return _image.crop(center_box(_image.width, _image.height, width, height))


# def space_images_vertical(images: t.Tuple[Image.Image, ...], height: int) -> t.Iterable[Image.Image]:
# 	try:
# 		offset = (height - images[0].height) // (len(images) - 1)
# 	except ZeroDivisionError:
# 		offset = 0
#
# 	image_width, images_height = images[0].width, images[0].height
#
# 	for i in range(len(images)-1):
# 		background_image = Image.new('RGBA', (image_width, height), (0, 0, 0, 0))
# 		background_image.paste(
# 			images[i],
# 			(
# 				0,
# 				i*offset,
# 			),
# 		)
# 		yield background_image
#
# 	background_image = Image.new('RGBA', (image_width, height), (0, 0, 0, 0))
# 	background_image.paste(
# 		images[-1],
# 		(
# 			0,
# 			height-images_height,
# 			image_width,
# 			height,
# 		),
# 	)
# 	yield background_image
#
#
# def space_images_horizontal(images: t.Tuple[Image.Image, ...], width: int) -> t.Iterable[Image.Image]:
# 	try:
# 		offset = (width - images[0].width) // (len(images) - 1)
# 	except ZeroDivisionError:
# 		offset = 0
#
# 	image_width, image_height = images[0].width, images[0].height
#
# 	for i in range(len(images)-1):
# 		background_image = Image.new('RGBA', (width, image_height), (0, 0, 0, 0))
# 		background_image.paste(
# 			images[i],
# 			(
# 				i*offset,
# 				0,
# 			)
# 		)
# 		yield background_image
#
# 	background_image = Image.new('RGBA', (width, image_height), (0, 0, 0, 0))
# 	background_image.paste(
# 		images[-1],
# 		(
# 			width - image_width,
# 			0,
# 			width,
# 			image_height,
# 		)
# 	)
# 	yield background_image
#
#
# def split_images_vertical(
# 	printings: t.Iterable[t.Tuple[Image.Image, str]],
# 	width: int,
# 	height: int,
# ) -> Image.Image:
#
# 	images, names = zip(*printings)
#
# 	_printings = tuple(
# 		zip(
# 			space_images_vertical(
# 				tuple(
# 					image
# 					if image.width == width else
# 					image.resize((width, image.height*width//image.width))
# 					for image in images
# 				),
# 				height,
# 			),
# 			names,
# 		)
# 	)
#
# 	_printings_iter = _printings.__iter__()
#
# 	background_original, background_name = copy.copy(_printings_iter.__next__())
#
# 	background = Image.alpha_composite(
# 		Image.new('RGBA', (width, height), (0, 0, 0, 0)),
# 		background_original,
# 	)
#
# 	offset = height // len(_printings)
# 	current_position = offset + height % len(_printings)
#
# 	draw = ImageDraw.Draw(background)
#
# 	draw_name(
# 		draw = draw,
# 		name = background_name,
# 		box = (
# 			0,
# 			0,
# 			width,
# 			current_position,
# 		),
# 		font_path = FONT_PATH,
# 	)
#
# 	for image, name in _printings_iter:
# 		box = (
# 			0,
# 			current_position,
# 			width,
# 			current_position + offset,
# 		)
#
# 		sub_section = image.crop(box)
# 		background.paste(
# 			sub_section,
# 			box
# 		)
#
# 		draw_name(
# 			draw = draw,
# 			name = name,
# 			box = (
# 				0,
# 				current_position,
# 				width,
# 				offset,
# 			),
# 			font_path = FONT_PATH,
# 		)
# 		current_position += offset
#
# 	return background
#
#
# def split_image_vertical_boxed(
# 	printings: t.Iterable[t.Tuple[Image.Image, str]],
# 	width: int,
# 	height: int,
# 	line_width: int = 10,
# 	line_color: t.Tuple[int, int, int] = (0, 0, 0),
# ) -> Image.Image:
#
# 	images, names = zip(*printings)
#
# 	_printings = tuple(
# 		zip(
# 			space_images_vertical(
# 				tuple(
# 					image
# 					if image.width == width else
# 					image.resize((width, image.height*width//image.width))
# 					for image in images
# 				),
# 				height,
# 			),
# 			names,
# 		)
# 	)
#
# 	_printings_iter = _printings.__iter__()
#
# 	background_original, background_name = copy.copy(_printings_iter.__next__())
#
# 	background = Image.alpha_composite(
# 		Image.new('RGBA', (width, height), (0, 0, 0, 0)),
# 		background_original,
# 	)
#
# 	offset = height // len(_printings)
# 	current_position = offset + height % len(_printings)
#
# 	draw = ImageDraw.Draw(background)
#
# 	draw_name(
# 		draw = draw,
# 		name = background_name,
# 		box = (
# 			0,
# 			0,
# 			width,
# 			current_position,
# 		),
# 		font_path = FONT_PATH,
# 	)
#
# 	for image, name in _printings_iter:
# 		box = (
# 			0,
# 			current_position,
# 			width,
# 			current_position + offset,
# 		)
#
# 		sub_section = image.crop(box)
# 		background.paste(
# 			sub_section,
# 			box
# 		)
#
# 		draw_name(
# 			draw = draw,
# 			name = name,
# 			box = (
# 				0,
# 				current_position,
# 				width,
# 				offset,
# 			),
# 			font_path = FONT_PATH,
# 		)
# 		current_position += offset
#
# 	inline_box(
# 		draw = draw,
# 		box = (
# 			0,
# 			0,
# 			width,
# 			height,
# 		),
# 		width = line_width,
# 		color = line_color,
# 	)
#
# 	return background
#
#
# def split_images_horizontal(
# 	printings: t.Iterable[t.Tuple[Image.Image, str]],
# 	width: int,
# 	height: int,
# ) -> Image.Image:
#
# 	font_path = os.path.join(
# 		locator.FONTS_PATH,
# 		'Beleren-Bold.ttf'
# 	)
#
# 	images, names = zip(*printings)
#
# 	_printings = tuple(
# 		zip(
# 			space_images_horizontal(
# 				tuple(
# 					image
# 					if image.height == height else
# 					image.resize((image.width*height//image.height, height))
# 					for image in images
# 				),
# 				width,
# 			),
# 			names,
# 		)
# 	)
#
#
# 	_printings_iter = _printings.__iter__()
#
# 	background_original, background_name = copy.copy(_printings_iter.__next__())
#
# 	background = Image.alpha_composite(
# 		Image.new('RGBA', (width, height), (0, 0, 0, 0)),
# 		background_original,
# 	)
#
# 	offset = width // len(_printings)
# 	current_position = offset + width % len(_printings)
#
# 	draw = ImageDraw.Draw(background)
#
# 	draw_name(
# 		draw = draw,
# 		name = ' {} '.format(background_name),
# 		box = (
# 			0,
# 			0,
# 			current_position,
# 			height,
# 		),
# 		font_path = font_path,
# 	)
#
# 	for image, name in _printings_iter:
# 		box = (
# 			current_position,
# 			0,
# 			current_position + offset,
# 			height,
# 		)
#
# 		sub_section = image.crop(box)
# 		background.paste(
# 			sub_section,
# 			box
# 		)
#
# 		draw_name(
# 			draw = draw,
# 			name = ' {} '.format(name),
# 			box = (
# 				current_position,
# 				0,
# 				offset,
# 				height,
# 			),
# 			font_path = font_path,
# 		)
#
# 		current_position += offset
#
# 	return background


# def polygon_crop(image: Image, polygon: t.Iterable[t.Tuple[int, int]]):
# 	image_array = np.asarray(
# 		image if image.format=='RGBA' else image.convert('RGBA')
# 	)
#
# 	mask_image = Image.new(
# 		'L',
# 		(image_array.shape[1], image_array.shape[0]),
# 		0,
# 	)
# 	ImageDraw.Draw(mask_image).polygon(polygon, outline=1, fill=1)
#
# 	cropped_image_array = np.empty(image_array.shape, dtype='uint8')
# 	cropped_image_array[:,:,:3] = image_array[:,:,:3]
# 	cropped_image_array[:,:,3] = np.asarray(mask_image)*255
#
# 	return Image.fromarray(cropped_image_array, 'RGBA')
