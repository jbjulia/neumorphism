from PyQt5 import QtWidgets, QtCore, QtGui


class NeumorphismEffect(QtWidgets.QGraphicsEffect):
    originChanged = QtCore.pyqtSignal(QtCore.Qt.Corner)
    distanceChanged = QtCore.pyqtSignal(float)
    colorChanged = QtCore.pyqtSignal(QtGui.QColor)
    clip_radiusChanged = QtCore.pyqtSignal(int)

    _cornerShift = (QtCore.Qt.TopLeftCorner, QtCore.Qt.TopRightCorner,
                    QtCore.Qt.BottomRightCorner, QtCore.Qt.BottomLeftCorner)

    def __init__(self, distance=4, color=None, origin=QtCore.Qt.TopLeftCorner, clip_radius=0):
        super().__init__()

        self._leftGradient = QtGui.QLinearGradient(1, 0, 0, 0)
        self._leftGradient.setCoordinateMode(QtGui.QGradient.ObjectBoundingMode)
        self._topGradient = QtGui.QLinearGradient(0, 1, 0, 0)
        self._topGradient.setCoordinateMode(QtGui.QGradient.ObjectBoundingMode)

        self._rightGradient = QtGui.QLinearGradient(0, 0, 1, 0)
        self._rightGradient.setCoordinateMode(QtGui.QGradient.ObjectBoundingMode)
        self._bottomGradient = QtGui.QLinearGradient(0, 0, 0, 1)
        self._bottomGradient.setCoordinateMode(QtGui.QGradient.ObjectBoundingMode)

        self._radial = QtGui.QRadialGradient(.5, .5, .5)
        self._radial.setCoordinateMode(QtGui.QGradient.ObjectBoundingMode)
        self._conical = QtGui.QConicalGradient(.5, .5, 0)
        self._conical.setCoordinateMode(QtGui.QGradient.ObjectBoundingMode)

        self._origin = origin
        distance = max(0, distance)
        self._clip_radius = min(distance, max(0, clip_radius))
        self._set_color(color or QtWidgets.QApplication.palette().color(QtGui.QPalette.Window))
        self._set_distance(distance)

    def color(self):
        return self._color

    @QtCore.pyqtSlot(QtGui.QColor)
    @QtCore.pyqtSlot(QtCore.Qt.GlobalColor)
    def set_color(self, color):
        if isinstance(color, QtCore.Qt.GlobalColor):
            color = QtGui.QColor(color)
        if color == self._color:
            return
        self._setColor(color)
        self._setDistance(self._distance)
        self.update()
        self.colorChanged.emit(self._color)

    def _set_color(self, color):
        self._color = color
        self._baseStart = color.lighter(125)
        self._baseStop = QtGui.QColor(self._baseStart)
        self._baseStop.setAlpha(0)
        self._shadowStart = self._baseStart.darker(125)
        self._shadowStop = QtGui.QColor(self._shadowStart)
        self._shadowStop.setAlpha(0)

        self.lightSideStops = [(0, self._baseStart), (1, self._baseStop)]
        self.shadowSideStops = [(0, self._shadowStart), (1, self._shadowStop)]
        self.cornerStops = [(0, self._shadowStart), (.25, self._shadowStop),
                            (.75, self._shadowStop), (1, self._shadowStart)]

        self._setOrigin(self._origin)

    def distance(self):
        return self._distance

    def set_distance(self, distance):
        if distance == self._distance:
            return
        old_radius = self._clip_radius
        self._setDistance(distance)
        self.updateBoundingRect()
        self.distanceChanged.emit(self._distance)
        if old_radius != self._clip_radius:
            self.clip_radiusChanged.emit(self._clip_radius)

    def _get_corner_pixmap(self, rect, grad1, grad2=None):
        pm = QtGui.QPixmap(self._distance + self._clip_radius, self._distance + self._clip_radius)
        pm.fill(QtCore.Qt.transparent)
        qp = QtGui.QPainter(pm)
        if self._clip_radius > 1:
            path = QtGui.QPainterPath()
            path.addRect(rect)
            size = self._clip_radius * 2 - 1
            mask = QtCore.QRectF(0, 0, size, size)
            mask.moveCenter(rect.center())
            path.addEllipse(mask)
            qp.setClipPath(path)
        qp.fillRect(rect, grad1)
        if grad2:
            qp.setCompositionMode(qp.CompositionMode_SourceAtop)
            qp.fillRect(rect, grad2)
        qp.end()
        return pm

    def _set_distance(self, distance):
        distance = max(1, distance)
        self._distance = distance
        if self._clip_radius > distance:
            self._clip_radius = distance
        distance += self._clip_radius
        r = QtCore.QRectF(0, 0, distance * 2, distance * 2)

        light_side_stops = self.lightSideStops[:]
        shadow_side_stops = self.shadowSideStops[:]
        if self._clip_radius:
            grad_start = self._clip_radius / (self._distance + self._clip_radius)
            light_side_stops[0] = (grad_start, light_side_stops[0][1])
            shadow_side_stops[0] = (grad_start, shadow_side_stops[0][1])

        # create the 4 corners as if the light source was top-left
        self._radial.setStops(light_side_stops)
        top_left = self._getCornerPixmap(r, self._radial)

        self._conical.setAngle(359.9)
        self._conical.setStops(self.cornerStops)
        top_right = self._getCornerPixmap(r.translated(-distance, 0), self._radial, self._conical)

        self._conical.setAngle(270)
        self._conical.setStops(self.cornerStops)
        bottom_left = self._getCornerPixmap(r.translated(0, -distance), self._radial, self._conical)

        self._radial.setStops(shadow_side_stops)
        bottom_right = self._getCornerPixmap(r.translated(-distance, -distance), self._radial)

        # rotate the images according to the actual light source
        images = top_left, top_right, bottom_right, bottom_left
        shift = self._cornerShift.index(self._origin)
        if shift:
            transform = QtGui.QTransform().rotate(shift * 90)
            for img in images:
                img.swap(img.transformed(transform, QtCore.Qt.SmoothTransformation))

        # and reorder them if required
        self.topLeft, self.topRight, self.bottomRight, self.bottomLeft = images[-shift:] + images[:-shift]

    def origin(self):
        return self._origin

    @QtCore.pyqtSlot(QtCore.Qt.Corner)
    def set_origin(self, origin):
        origin = QtCore.Qt.Corner(origin)
        if origin == self._origin:
            return
        self._setOrigin(origin)
        self._setDistance(self._distance)
        self.update()
        self.originChanged.emit(self._origin)

    def _set_origin(self, origin):
        self._origin = origin

        gradients = self._leftGradient, self._topGradient, self._rightGradient, self._bottomGradient
        stops = self.lightSideStops, self.lightSideStops, self.shadowSideStops, self.shadowSideStops

        # assign color stops to gradients based on the light source position
        shift = self._cornerShift.index(self._origin)
        for grad, stops in zip(gradients, stops[-shift:] + stops[:-shift]):
            grad.setStops(stops)

    def clip_radius(self):
        return self._clip_radius

    @QtCore.pyqtSlot(int)
    @QtCore.pyqtSlot(float)
    def set_clip_radius(self, radius):
        if radius == self._clip_radius:
            return
        old_radius = self._clip_radius
        self._setclip_radius(radius)
        self.update()
        if old_radius != self._clip_radius:
            self.clip_radiusChanged.emit(self._clip_radius)

    def _set_clip_radius(self, radius):
        radius = min(self._distance, max(0, int(radius)))
        self._clip_radius = radius
        self._setDistance(self._distance)

    def boundingRectFor(self, rect):
        d = self._distance + 1
        return rect.adjusted(-d, -d, d, d)

    def draw(self, qp):
        restore_transform = qp.worldTransform()

        qp.setPen(QtCore.Qt.NoPen)
        x, y, width, height = self.sourceBoundingRect(QtCore.Qt.DeviceCoordinates).getRect()
        right = x + width
        bottom = y + height
        clip = self._clip_radius
        double_clip = clip * 2

        qp.setWorldTransform(QtGui.QTransform())
        left_rect = QtCore.QRectF(x - self._distance, y + clip, self._distance, height - double_clip)
        qp.setBrush(self._leftGradient)
        qp.drawRect(left_rect)

        top_rect = QtCore.QRectF(x + clip, y - self._distance, width - double_clip, self._distance)
        qp.setBrush(self._topGradient)
        qp.drawRect(top_rect)

        right_rect = QtCore.QRectF(right, y + clip, self._distance, height - double_clip)
        qp.setBrush(self._rightGradient)
        qp.drawRect(right_rect)

        bottom_rect = QtCore.QRectF(x + clip, bottom, width - double_clip, self._distance)
        qp.setBrush(self._bottomGradient)
        qp.drawRect(bottom_rect)

        qp.drawPixmap(x - self._distance, y - self._distance, self.topLeft)
        qp.drawPixmap(right - clip, y - self._distance, self.topRight)
        qp.drawPixmap(right - clip, bottom - clip, self.bottomRight)
        qp.drawPixmap(x - self._distance, bottom - clip, self.bottomLeft)

        qp.setWorldTransform(restore_transform)
        if self._clip_radius:
            path = QtGui.QPainterPath()
            source, offset = self.sourcePixmap(QtCore.Qt.DeviceCoordinates)

            source_bounding_rect = self.sourceBoundingRect(QtCore.Qt.DeviceCoordinates)
            qp.save()
            qp.setTransform(QtGui.QTransform())
            path.addRoundedRect(source_bounding_rect, self._clip_radius, self._clip_radius)
            qp.setClipPath(path)
            qp.drawPixmap(source.rect().translated(offset), source)
            qp.restore()
        else:
            self.drawSource(qp)
