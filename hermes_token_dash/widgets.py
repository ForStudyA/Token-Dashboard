"""Custom sidebar widgets for Hermes Token Dashboard.

Textual 8.2.7 ships no ``Panel`` widget, so we build bordered containers
out of ``Vertical`` + CSS border properties and populate them with
``Static`` / ``ModelItem`` children.
"""

from __future__ import annotations

from textual.containers import Vertical
from textual.message import Message
from textual.widgets import Static

from hermes_token_dash.models import ModelStats

# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------


def fmt_tokens(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.0f}K"
    return str(n)


def fmt_cost(v: float) -> str:
    if abs(v) >= 1.0:
        return f"${v:.2f}"
    return f"${v:.4f}"


def fmt_pct(v: float) -> str:
    return f"{v:.1f}%"


def hit_color(v: float) -> str:
    if v >= 80:
        return "green"
    if v >= 40:
        return "yellow"
    return "red"


def cache_bar(v: float, width: int = 8) -> str:
    filled = int(v / 100 * width)
    bar = "█" * filled + "░" * (width - filled)
    col = hit_color(v)
    return f"[{col}]{bar} {v:.1f}%[/]"


# ---------------------------------------------------------------------------
# PulseDot  — animated auto-refresh indicator
# ---------------------------------------------------------------------------


class PulseDot(Static):
    """Green circle that pulses bright/dim when auto-refresh is active."""

    def __init__(self) -> None:
        super().__init__("●", id="pulse-dot")
        self._active = False
        self._bright = False
        self._timer = None

    def set_active(self, active: bool) -> None:
        self._active = active
        if active:
            self._start()
        else:
            self._stop()
        self._draw()

    def _start(self) -> None:
        if self._timer is None:
            self._timer = self.set_interval(0.8, self._tick)

    def _stop(self) -> None:
        if self._timer is not None:
            try:
                self._timer.stop()
            except Exception:
                pass
            self._timer = None
        self._bright = False

    def _tick(self) -> None:
        self._bright = not self._bright
        self._draw()

    def _draw(self) -> None:
        if self._active and self._bright:
            self.update("[bright_green]●[/]")
        elif self._active:
            self.update("[green dim]●[/]")
        else:
            self.update("[bright_black]●[/]")


# ---------------------------------------------------------------------------
# ModelItem  — single clickable model entry
# ---------------------------------------------------------------------------


class ModelItem(Static):
    """One model row in the sidebar filter list.

    Posts ``Pressed`` when clicked.
    """

    class Pressed(Message):
        def __init__(self, model_name: str) -> None:
            self.model_name = model_name
            super().__init__()

    def __init__(
        self,
        model_name: str,
        request_count: int,
        active: bool,
        is_all: bool = False,
    ) -> None:
        super().__init__()
        self._model_name = model_name
        self._request_count = request_count
        self._active = active
        self._is_all = is_all

    def render(self) -> str:
        mark = "●" if self._active else "○"
        if self._is_all:
            return f" {mark} [bold]All Models[/]"
        cnt = f"[dim]({self._request_count})[/]"
        return f" {mark} {self._model_name} {cnt}"

    def on_click(self) -> None:
        self.post_message(self.Pressed(self._model_name))


# ---------------------------------------------------------------------------
# ModelsBox  — bordered container with title + model list
# ---------------------------------------------------------------------------


class ModelsBox(Vertical):
    """Sidebar box listing models as clickable entries.

    Emits ``ModelSelected`` when the user clicks a model row.
    """

    class ModelSelected(Message):
        def __init__(self, model_name: str) -> None:
            self.model_name = model_name
            super().__init__()

    def __init__(self) -> None:
        super().__init__(id="models-box")
        self._items: list[tuple[str, int]] = []
        self._active: str = "__all__"

    def compose(self) -> ...:
        yield Static("🤖 MODELS", id="models-title", classes="box-title")
        yield Static("", id="models-container")

    def on_mount(self) -> None:
        self._rebuild()

    def set_models(
        self,
        models: list[tuple[str, int]],
        active: str = "__all__",
    ) -> None:
        self._items = models
        self._active = active
        self._rebuild()

    def _rebuild(self) -> None:
        container = self.query_one("#models-container")
        container.remove_children()

        # "All Models" entry
        all_btn = ModelItem("__all__", 0, self._active == "__all__", is_all=True)
        container.mount(all_btn)

        # Individual models
        for name, count in self._items:
            item = ModelItem(name, count, active=(name == self._active))
            container.mount(item)

    def on_model_item_pressed(self, event: ModelItem.Pressed) -> None:
        event.stop()
        self.post_message(self.ModelSelected(event.model_name))


# ---------------------------------------------------------------------------
# SummaryBox  — bordered container with title + stats
# ---------------------------------------------------------------------------


class SummaryBox(Vertical):
    """Sidebar summary box showing aggregated token / cost numbers."""

    def __init__(self) -> None:
        super().__init__(id="summary-box")
        self._body = Static("", id="summary-body")

    def compose(self) -> ...:
        yield Static("📊 SUMMARY", id="summary-title", classes="box-title")
        yield self._body

    def on_mount(self) -> None:
        self._body.update("[dim italic]No data[/]")

    def refresh(self, stats: list[ModelStats]) -> None:
        if not stats:
            self._body.update("[dim italic]No data[/]")
            return

        total_reqs = sum(s.request_count for s in stats)
        total_rc = sum(s.requests_with_cache for s in stats)
        total_in = sum(s.total_input for s in stats)
        total_out = sum(s.total_output for s in stats)
        total_cr = sum(s.total_cache_read for s in stats)
        total_cc = sum(s.total_cache_creation for s in stats)
        hit = (total_rc / total_reqs * 100) if total_reqs else 0.0
        total_cost = sum(s.estimated_cost for s in stats)

        w = 8
        hc = hit_color(hit)
        n_filled = int(hit / 100 * w)
        bar = "█" * n_filled + "░" * (w - n_filled)

        lines = [
            "",
            f"Requests       [bold]{total_reqs:>9,}[/]",
            f"Input Tok      [bold]{fmt_tokens(total_in):>9}[/]",
            f"Output Tok     [bold]{fmt_tokens(total_out):>9}[/]",
            f"Cache Read     [bold]{fmt_tokens(total_cr):>9}[/]",
            f"Cache Create   [bold]{fmt_tokens(total_cc):>9}[/]",
            "  " + "─" * 20,
            f"  [{hc}]{bar}[/]  [{hc}]{fmt_pct(hit)}[/]",
            f"Est. Cost      [bold]{fmt_cost(total_cost):>9}[/]",
            "",
        ]
        self._body.update("\n".join(lines))
