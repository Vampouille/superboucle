from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPainter, QBrush, QColor, QPen, QPainterPath, QPixmap
from PyQt5.QtWidgets import QWidget
from svgpathtools import svg2paths, Path, Line, QuadraticBezier, CubicBezier

class LoopPathWidget(QWidget):
    def __init__(self, parent, svg_path, num_segments=100, fill_factor=0.9, point_radius=5):
        super().__init__(parent)
        self.setFixedSize(600, 200)
        self.point_radius = point_radius
        self.fill_factor = fill_factor

        # Load the original path from the SVG file
        self.paths, self.attributes = svg2paths(svg_path)
        self.original_path = self.paths[0]

        # Approximate the path with straight line segments
        self.approx_path = self.approximate_path_with_lines(self.original_path, num_segments)
        self.approx_path_length = self.approx_path.length()
        self.position_on_path = 0

        # Calculate the bounding box
        xmin, xmax, ymin, ymax = self.original_path.bbox()
        self.bounding_box_width = xmax - xmin
        self.bounding_box_height = ymax - ymin

        # Create a QPixmap for the background path
        self.background_pixmap = QPixmap(self.width(), self.height())
        self.background_pixmap.fill(QColor(211, 211, 211))  # Fill with light gray
        self.draw_background_path()
        self.update()

    def approximate_path_with_lines(self, path, num_segments):
        new_path = Path()

        for i in range(num_segments):
            point_start = path.point(i / num_segments)
            point_end = path.point((i + 1) / num_segments)
            line_segment = Line(start=point_start, end=point_end)
            new_path.append(line_segment)

        return new_path

    def set_position(self, pos):
        self.position_on_path = self.approx_path_length * (pos % 1)
        self.update()

    def draw_background_path(self):
        painter = QPainter(self.background_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor(0, 0, 0), 2))

        # Calculate scale factor to fit the widget and occupy 90% of the width without deformation
        scale_factor_x = (self.width() * self.fill_factor) / self.bounding_box_width
        scale_factor_y = (self.height() * self.fill_factor) / self.bounding_box_height
        scale_factor = min(scale_factor_x, scale_factor_y)

        # Center the path within the widget
        offset_x = (self.width() - (self.bounding_box_width * scale_factor)) / 2
        offset_y = (self.height() - (self.bounding_box_height * scale_factor)) / 2

        # Draw the original path
        for seg in self.original_path:
            if isinstance(seg, Line):
                start = seg.start
                end = seg.end

                start_x = (start.real - self.original_path.bbox()[0]) * scale_factor + offset_x
                start_y = (start.imag - self.original_path.bbox()[2]) * scale_factor + offset_y
                end_x = (end.real - self.original_path.bbox()[0]) * scale_factor + offset_x
                end_y = (end.imag - self.original_path.bbox()[2]) * scale_factor + offset_y

                painter.drawLine(QPointF(start_x, start_y), QPointF(end_x, end_y))

            elif isinstance(seg, QuadraticBezier):
                path = QPainterPath()
                start_x = (seg.start.real - self.original_path.bbox()[0]) * scale_factor + offset_x
                start_y = (seg.start.imag - self.original_path.bbox()[2]) * scale_factor + offset_y
                ctrl_x = (seg.control.real - self.original_path.bbox()[0]) * scale_factor + offset_x
                ctrl_y = (seg.control.imag - self.original_path.bbox()[2]) * scale_factor + offset_y
                end_x = (seg.end.real - self.original_path.bbox()[0]) * scale_factor + offset_x
                end_y = (seg.end.imag - self.original_path.bbox()[2]) * scale_factor + offset_y

                path.moveTo(start_x, start_y)
                path.quadTo(ctrl_x, ctrl_y, end_x, end_y)
                painter.drawPath(path)

            elif isinstance(seg, CubicBezier):
                path = QPainterPath()
                start_x = (seg.start.real - self.original_path.bbox()[0]) * scale_factor + offset_x
                start_y = (seg.start.imag - self.original_path.bbox()[2]) * scale_factor + offset_y
                ctrl1_x = (seg.control1.real - self.original_path.bbox()[0]) * scale_factor + offset_x
                ctrl1_y = (seg.control1.imag - self.original_path.bbox()[2]) * scale_factor + offset_y
                ctrl2_x = (seg.control2.real - self.original_path.bbox()[0]) * scale_factor + offset_x
                ctrl2_y = (seg.control2.imag - self.original_path.bbox()[2]) * scale_factor + offset_y
                end_x = (seg.end.real - self.original_path.bbox()[0]) * scale_factor + offset_x
                end_y = (seg.end.imag - self.original_path.bbox()[2]) * scale_factor + offset_y

                path.moveTo(start_x, start_y)
                path.cubicTo(ctrl1_x, ctrl1_y, ctrl2_x, ctrl2_y, end_x, end_y)
                painter.drawPath(path)

        painter.end()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw the background pixmap with the original path
        painter.drawPixmap(0, 0, self.background_pixmap)

        # Set the brush for the white point
        painter.setBrush(QBrush(QColor(255, 255, 255), Qt.SolidPattern))

        # Calculate the position of the point on the approximated path
        point = self.approx_path.point(self.position_on_path / self.approx_path_length)

        # Map the SVG coordinates to the widget coordinates
        scale_factor_x = (self.width() * self.fill_factor) / self.bounding_box_width
        scale_factor_y = (self.height() * self.fill_factor) / self.bounding_box_height
        scale_factor = min(scale_factor_x, scale_factor_y)
        offset_x = (self.width() - (self.bounding_box_width * scale_factor)) / 2
        offset_y = (self.height() - (self.bounding_box_height * scale_factor)) / 2

        point_x = (point.real - self.original_path.bbox()[0]) * scale_factor + offset_x
        point_y = (point.imag - self.original_path.bbox()[2]) * scale_factor + offset_y

        # Draw the point
        painter.drawEllipse(QPointF(point_x, point_y), self.point_radius, self.point_radius)