import typing as t

from mtgimg import interface
from promise import Promise
from proxypdf.write import save_proxy_pdf

from magiccube.laps.lap import Lap


def proxy_laps(
    laps: t.Iterable[Lap],
    image_loader: interface.ImageLoader,
    file: t.Union[t.BinaryIO, str],
    margin_size: float = 0.1,
    card_margin_size: float = 0.01,
    size_slug: interface.SizeSlug = interface.SizeSlug.ORIGINAL,
) -> None:
    save_proxy_pdf(
        file=file,
        images=Promise.all(
            tuple(
                image_loader.get_image(
                    lap,
                    size_slug=size_slug,
                    save=False,
                )
                for lap in laps
            )
        ).get(),
        margin_size=margin_size,
        card_margin_size=card_margin_size,
    )
