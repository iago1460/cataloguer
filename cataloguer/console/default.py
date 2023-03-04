import time
from contextlib import suppress
from enum import Enum
from types import TracebackType
from typing import Optional, Type

from rich.console import Console, RenderableType
from rich.panel import Panel
from rich.status import Status


class State(Enum):
    START = 1
    STOP = 0


class ObservableStatus(Status):
    @property
    def console(self) -> "MyConsole":
        return self._live.console

    def __enter__(self) -> "Status":
        self.console.notify(self, state=State.START)
        return super().__enter__()

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        super().__exit__(exc_type, exc_val, exc_tb)
        self.console.notify(self, state=State.STOP)


class MyConsole(Console):
    """
    Extended Console with support for multiple Live components and print methods
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._status = []

    def notify(self, status_obj, state: State):
        if state == State.START:
            with suppress(IndexError):
                self._status[-1].stop()
            self._status.append(status_obj)
        else:
            self._status.remove(status_obj)
            with suppress(IndexError):
                self._status[-1].start()

    def status(
        self,
        status: RenderableType,
        *,
        spinner: str = "dots",
        spinner_style: str = "status.spinner",
        speed: float = 1.0,
        refresh_per_second: float = 12.5,
    ) -> ObservableStatus:
        """Display a status and spinner.

        Args:
            status (RenderableType): A status renderable (str or Text typically).
            spinner (str, optional): Name of spinner animation (see python -m rich.spinner). Defaults to "dots".
            spinner_style (StyleType, optional): Style of spinner. Defaults to "status.spinner".
            speed (float, optional): Speed factor for spinner animation. Defaults to 1.0.
            refresh_per_second (float, optional): Number of refreshes per second. Defaults to 12.5.

        Returns:
            Status: A Status object that may be used as a context manager.
        """

        return ObservableStatus(
            status,
            console=self,
            spinner=spinner,
            spinner_style=spinner_style,
            speed=speed,
            refresh_per_second=refresh_per_second,
        )

    def info(self, message) -> None:
        self.print(
            Panel(
                message,
                border_style="bright_blue",
                title_align="left",
                expand=True,
                title="Info",
            )
        )

    def warning(self, message) -> None:
        self.print(
            Panel(
                message,
                border_style="yellow",
                title_align="left",
                expand=True,
                title="Warning",
            )
        )


console = MyConsole()


if __name__ == "__main__":  # pragma: no cover

    with (
        console.status(
            "Preparing summary...",
        )
    ) as status:
        time.sleep(1)
        with (
            console.status(
                "Step 1",
            )
        ) as status:
            time.sleep(1)
            with (
                console.status(
                    "Step 1b",
                )
            ) as status:
                time.sleep(1)
                pass
            time.sleep(1)
        time.sleep(1)
