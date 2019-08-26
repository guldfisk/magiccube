import typing as t

from promise import Promise

from proxypdf.write import save_proxy_pdf

from mtgimg.load import Loader as ImageLoader

from magiccube.laps.lap import Lap


def proxy_laps(
    laps: t.Iterable[Lap],
    image_loader: ImageLoader,
    file: t.Union[t.BinaryIO, str],
    margin_size: float = .1,
    card_margin_size: float = .01,
) -> None:
    save_proxy_pdf(
        file = file,
        images = Promise.all(
            tuple(
                image_loader.get_image(lap, save = False)
                for lap in
                laps
            )
        ).get(),
        margin_size = margin_size,
        card_margin_size = card_margin_size,
    )
