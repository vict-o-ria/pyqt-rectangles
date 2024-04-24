import sys
import random
from PyQt6 import QtWidgets, QtCore, QtGui

RECT_WIDTH = 100
RECT_HEIGHT = 50
MAX_ITERATIONS = 50

# Генерация случайного цвета
def random_color():
    return QtGui.QColor(
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255)
    )

# Класс для прямоугольника
class DraggableRectangle(QtWidgets.QGraphicsRectItem):
    def __init__(self, x, y):
        super().__init__(-RECT_WIDTH / 2, -RECT_HEIGHT / 2, RECT_WIDTH, RECT_HEIGHT)
        self.setBrush(random_color())
        self.setPen(QtGui.QPen(QtGui.QColor('black'), 1))
        self.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges, True)
        self.setPos(x, y)
        # Флаг того что прямоугольник выбран для создания связи
        self.selectedForLine=False
        # Связи прямоугольника с другими
        self.connections=[]
        # Значение для возврата на предыдущую позицию
        self.startTransition=None

    def mouseDoubleClickEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent | None) -> None:
        self.setPen(QtGui.QPen(QtGui.QColor('red'), 4))
        self.selectedForLine = True
        # Соединение прямоугольников происходит при последовательном двойном клике сначала на первый прямоугольник, потом на второй
        main_win.connect_rects(self)
        return super().mouseDoubleClickEvent(event)
    
    def mousePressEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent | None) -> None:
        self.startTransition = self.pos()
        return super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent | None) -> None:
        # Попытка найти ближайшее свободное место
        if (self.collides_with_others() or self.meet_scene_boundaries()):
            self.find_nearest_pos()

        self.startTransition = None
        # обновляем все линии
        self.update_all_lines()
        return super().mouseReleaseEvent(event)
    
    def get_combined_rect(self, rects: list[QtWidgets.QGraphicsRectItem]) -> QtCore.QRectF:
        # Находим объединение всех прямоугольников
        combined_rect = QtCore.QRectF()

        for rect in rects:
            combined_rect = combined_rect.united(rect.sceneBoundingRect())
        return combined_rect
    
    def get_boundary_offset(self):
        scene_rect = self.scene().sceneRect()
        item_rect = self.sceneBoundingRect()
        offsets = {"x": 0, "y": 0}

        # Проверка по оси x
        if item_rect.left() < scene_rect.left():
            offsets["x"] = scene_rect.left() - item_rect.left()  # Ушел за левую границу
        elif item_rect.right() > scene_rect.right():
            offsets["x"] = scene_rect.right() - item_rect.right()  # Ушел за правую границу
        
        # Проверка по оси y
        if item_rect.top() < scene_rect.top():
            offsets["y"] = scene_rect.top() - item_rect.top()  # Ушел за верхнюю границу
        elif item_rect.bottom() > scene_rect.bottom():
            offsets["y"] = scene_rect.bottom() - item_rect.bottom()  # Ушел за нижнюю границу

        return offsets

    # Перенос на ближайшее свободное место (не до конца реализован алгоритм, зацикливание при многих коллизиях - временное решение - MAX_ITERATIONS)
    def find_nearest_pos(self):
        iterations_count = 0
        while (self.collides_with_others() or self.meet_scene_boundaries()) and iterations_count < MAX_ITERATIONS:
            iterations_count += 1
            if (self.meet_scene_boundaries()):
                offset = self.get_boundary_offset()
                self.moveBy(offset["x"], offset["y"])
                continue
            
            collisions = list(filter(lambda item: type(item) is DraggableRectangle, self.collidingItems()))

            if len(collisions) > 1:
                combined = self.get_combined_rect(collisions)
                scene_rect = self.scene().sceneRect()
                rect = self.sceneBoundingRect()

                move_right = combined.right() - rect.left()
                move_left = combined.left() - rect.right()
                move_up = combined.top() - rect.bottom()
                move_down = combined.bottom() - rect.top()

                # Переместить вплотную
                if move_right >= 0 and (rect.right() + move_right) <= scene_rect.right():
                    self.moveBy(move_right, 0)
                elif move_left <= 0 and (rect.left() + move_left) >= scene_rect.left():
                    self.moveBy(move_left, 0)
                elif move_down >= 0 and (rect.bottom() + move_down) <= scene_rect.bottom():
                    self.moveBy(0, move_down)
                elif move_up <= 0 and (rect.top() + move_up) >= scene_rect.top():
                    self.moveBy(0, move_up)

            elif len(collisions) == 1:
                intersection = collisions[0].sceneBoundingRect().intersected(self.sceneBoundingRect())

                if (intersection.width() < intersection.height()):
                    if (collisions[0].sceneBoundingRect().x() < self.sceneBoundingRect().x()):
                        self.moveBy(intersection.width(), 0)
                    else:
                        self.moveBy(-intersection.width(), 0)
                else:
                    if (collisions[0].sceneBoundingRect().y() < self.sceneBoundingRect().y()):
                        self.moveBy(0, intersection.height())
                    else:
                        self.moveBy(0, -intersection.height())

        # Если не вышло найти подходящую позицию возвращаемся на предыдущую
        if (self.collides_with_others() or self.meet_scene_boundaries()):
            self.setPos(self.startTransition)

    # Проверка пересечения с другими объектами
    def collides_with_others(self):
        for item in self.collidingItems():
            if item != self and type(item) == DraggableRectangle:
                return True
        return False

    # Проверка пересечения с границами сцены
    def meet_scene_boundaries(self):
        scene_rect = self.scene().sceneRect()
        rect = self.sceneBoundingRect()
        # Проверка по оси x
        return (
            rect.left() < scene_rect.left()
            or rect.right() > scene_rect.right()
            or rect.top() < scene_rect.top()
            or rect.bottom() > scene_rect.bottom()
        )
    
    # Отмена выбора прямоугольника после создания линии
    def unselect_rect(self):
        self.selectedForLine=False
        self.setPen(QtGui.QPen(QtGui.QColor('black'), 1))
    
    # Обновление всех связей прямоугольника
    def update_all_lines(self):
        for line in self.connections:
            line.update_position()

    def itemChange(self, change, value):
        if change == QtWidgets.QGraphicsRectItem.GraphicsItemChange.ItemPositionChange and self.scene():
            self.update_all_lines()

        return super().itemChange(change, value)
    
# Класс для соединительной линии
class ConnectionLine(QtWidgets.QGraphicsLineItem):
    def __init__(self, start_rect: DraggableRectangle, end_rect: DraggableRectangle):
        super().__init__()
        self.setFlag(QtWidgets.QGraphicsLineItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setPen(QtGui.QPen(QtGui.QColor('black'), 3))
        self.start_rect = start_rect
        self.end_rect = end_rect
        self.update_position()
    
    # Удаление линии - по двойному клику на нее
    def mouseDoubleClickEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent | None) -> None:
        self.delete_line()
        return super().mouseDoubleClickEvent(event)

    # Обноввление позиции линии
    def update_position(self):
        start_x = self.start_rect.sceneBoundingRect().x()
        start_y = self.start_rect.sceneBoundingRect().y()
        end_x = self.end_rect.sceneBoundingRect().x()
        end_y = self.end_rect.sceneBoundingRect().y()
        if (start_x < end_x):
            if (start_y < end_y):
                start_point = self.start_rect.sceneBoundingRect().bottomRight()
                end_point = self.end_rect.sceneBoundingRect().topLeft()
                self.setLine(QtCore.QLineF(start_point, end_point))
            else:
                start_point = self.start_rect.sceneBoundingRect().topRight()
                end_point = self.end_rect.sceneBoundingRect().bottomLeft()
                self.setLine(QtCore.QLineF(start_point, end_point))
        elif (start_y < end_y):
            start_point = self.start_rect.sceneBoundingRect().bottomLeft()
            end_point = self.end_rect.sceneBoundingRect().topRight()
            self.setLine(QtCore.QLineF(start_point, end_point))
        else:
            start_point = self.start_rect.sceneBoundingRect().topLeft()
            end_point = self.end_rect.sceneBoundingRect().bottomRight()
            self.setLine(QtCore.QLineF(start_point, end_point))

    def delete_line(self):
        self.start_rect.connections.remove(self)
        self.end_rect.connections.remove(self)
        main_win.scene.removeItem(self)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Rectangles")
        self.setGeometry(200, 100, 600, 500)

        self.scene = QtWidgets.QGraphicsScene(self)
        self.scene.setSceneRect(0, 0, 600, 500)

        self.view = QtWidgets.QGraphicsView(self.scene, self)
        self.view.setMouseTracking(True)

        self.setCentralWidget(self.view)

    def mouseDoubleClickEvent(self, event: QtGui.QMouseEvent | None):
        click_pos = self.view.mapToScene(event.pos())
        # Проверяем, достаточно ли места для нового прямоугольника
        if (
            click_pos.x() - RECT_WIDTH / 2 >= self.scene.sceneRect().left() 
            and click_pos.x() + RECT_WIDTH / 2 <= self.scene.sceneRect().right()
            and click_pos.y() - RECT_HEIGHT / 2 >= self.scene.sceneRect().top() 
            and click_pos.y() + RECT_WIDTH / 2 <= self.scene.sceneRect().bottom()
        ):
            new_rect = DraggableRectangle(click_pos.x(), click_pos.y())
            self.scene.addItem(new_rect)

            # Проверка на пересечение
            if new_rect.collides_with_others():
                self.scene.removeItem(new_rect)  # Если пересекается, удалить
                QtWidgets.QMessageBox.warning(self, "Warning", "Пересечение с другим прямоугольником!")
        else:
            QtWidgets.QMessageBox.warning(self, "Warning", "Пересечение с границами области!")
        return super().mouseDoubleClickEvent(event)

    def on_double_click(self, event):
        click_pos = self.view.mapToScene(event.pos())

        # Проверяем, достаточно ли места для нового прямоугольника
        if (
            click_pos.x() - RECT_WIDTH / 2 >= self.scene.sceneRect().left() 
            and click_pos.x() + RECT_WIDTH / 2 <= self.scene.sceneRect().right()
            and click_pos.y() - RECT_HEIGHT / 2 >= self.scene.sceneRect().top() 
            and click_pos.y() + RECT_WIDTH / 2 <= self.scene.sceneRect().bottom()
        ):
            new_rect = DraggableRectangle(click_pos.x(), click_pos.y())
            self.scene.addItem(new_rect)

            # Проверка на пересечение
            if new_rect.collides_with_others():
                self.scene.removeItem(new_rect)  # Если пересекается, удалить

    def add_connection(self, start_rect: DraggableRectangle, end_rect: DraggableRectangle):
        line = ConnectionLine(start_rect, end_rect)
        self.scene.addItem(line)
        start_rect.connections.append(line)
        end_rect.connections.append(line)
    
    def connect_rects(self, rect: DraggableRectangle):
        items = self.scene.items()
        for item in items:
            if type(item) is DraggableRectangle and item.selectedForLine and item != rect:
                item.unselect_rect()
                rect.unselect_rect()
                self.add_connection(item, rect)

# Запуск приложения
app = QtWidgets.QApplication(sys.argv)
main_win = MainWindow()
main_win.show()
sys.exit(app.exec())
