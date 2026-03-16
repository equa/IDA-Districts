from qgis.PyQt.QtWidgets import QLabel
from qgis.PyQt.QtGui import QPainter
from qgis.PyQt.QtSvg import QSvgRenderer
from qgis.PyQt.QtCore import Qt, QRectF, QSize


class SvgLabel(QLabel):
    """
    QLabel subclass for displaying SVGs sharply without creating a pixmap.
    Supports optional min/max width and height.
    Works with Qt Designer Promote.
    Preserves aspect ratio and centers the SVG.
    """

    def __init__(self, svg_path=None,
                 min_width=None, max_width=None,
                 min_height=None, max_height=None,
                 parent=None):
        super().__init__(parent)
        self._svg_renderer = None
        self._min_width = min_width
        self._max_width = max_width
        self._min_height = min_height
        self._max_height = max_height
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if svg_path:
            self.load_svg(svg_path)

    # -------------------- Load SVG --------------------
    def load_svg(self, svg_path):
        """Load an SVG file."""
        self._svg_renderer = QSvgRenderer(svg_path)
        self.update()

    # -------------------- Width/Height setters --------------------
    def set_max_width(self, max_width):
        self._max_width = max_width
        self.updateGeometry()  # <-- trigger layout update
        self.update()          # <-- repaint

    def set_min_width(self, min_width):
        self._min_width = min_width
        self.updateGeometry()
        self.update()

    def set_max_height(self, max_height):
        self._max_height = max_height
        self.updateGeometry()
        self.update()

    def set_min_height(self, min_height):
        self._min_height = min_height
        self.updateGeometry()
        self.update()

    # -------------------- Size hints for layout --------------------
    def sizeHint(self):
        """Preferred size for layouts."""
        if self._svg_renderer and self._svg_renderer.isValid():
            svg_size = self._svg_renderer.defaultSize()
            width = svg_size.width()
            height = svg_size.height()

            if self._min_width:
                width = max(width, self._min_width)
            if self._max_width:
                width = min(width, self._max_width)
            if self._min_height:
                height = max(height, self._min_height)
            if self._max_height:
                height = min(height, self._max_height)

            return QSize(width, height)

        return super().sizeHint()

    def minimumSizeHint(self):
        """Minimum size for layouts (enforced if min values are set)."""
        width = self._min_width or 0
        height = self._min_height or 0
        return QSize(width, height)

    # -------------------- Paint the SVG --------------------
    def paintEvent(self, event):
        super().paintEvent(event)
        if not self._svg_renderer or not self._svg_renderer.isValid():
            return

        painter = QPainter(self)
        w, h = self.width(), self.height()

        # Apply min/max height
        if self._max_height and h > self._max_height:
            h = self._max_height
        if self._min_height and h < self._min_height:
            h = self._min_height

        # Apply min/max width
        if self._max_width and w > self._max_width:
            w = self._max_width
        if self._min_width and w < self._min_width:
            w = self._min_width

        svg_size = self._svg_renderer.defaultSize()
        if svg_size.width() == 0 or svg_size.height() == 0:
            return

        # Preserve aspect ratio
        aspect_ratio = svg_size.width() / svg_size.height()
        if w / h > aspect_ratio:
            w = h * aspect_ratio
        else:
            h = w / aspect_ratio

        x = (self.width() - w) / 2
        y = (self.height() - h) / 2

        rect = QRectF(x, y, w, h)
        self._svg_renderer.render(painter, rect)