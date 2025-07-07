from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import qt


def iconPath(icon_name) -> str:
    return Path(__file__).parent.joinpath("..", "Resources", "Icons", icon_name).as_posix()


def icon(icon_name) -> "qt.QIcon":
    import qt

    return qt.QIcon(iconPath(icon_name))
