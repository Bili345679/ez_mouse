from screeninfo import get_monitors
from pynput import mouse
from pynput.keyboard import Controller, Key
from PIL import Image, ImageDraw, ImageFont
from pystray import Menu, Icon
from pystray import MenuItem as item
import threading
import os
import time


# 屏幕区域检测
def get_position_area(x, y, width=1, height=1, only_primary=False):
    area = False
    for monitor in get_monitors():
        mon_x = monitor.x
        mon_y = monitor.y
        mon_w = monitor.width
        mon_h = monitor.height

        if only_primary and monitor.is_primary is False:
            continue
        if x < mon_x or x > mon_x + mon_w - 1:
            continue
        if y < mon_y or y > mon_y + mon_h - 1:
            continue

        left = False
        right = False
        top = False
        bottom = False
        ver_center = False
        hor_center = False

        if x < mon_x + width:
            left = True
        elif x > mon_x + mon_w - 1 - width:
            right = True
        else:
            return False

        if y < mon_y + width:
            top = True
        elif y > mon_y + mon_h - 1 - height:
            bottom = True
        else:
            return False

        if left and top:
            area = "lt"
        if left and bottom:
            area = "lb"
        if right and top:
            area = "rt"
        if right and bottom:
            area = "rb"

    return area


# 键盘控制与鼠标监听
keyboard = Controller()

# 标志变量初始化
volume_ctl_flag = True
media_ctl_flag = True
page_ctl_flag = True


def execute_operation(operation):
    if operation is False:
        return False

    if isinstance(operation, Key):
        if (
            operation
            in [
                Key.media_volume_mute,
                Key.media_volume_up,
                Key.media_volume_down,
            ]
            and not volume_ctl_flag
        ):
            return False
        elif (
            operation in [Key.media_previous, Key.media_next, Key.media_play_pause]
            and not media_ctl_flag
        ):
            return False
        elif operation in [Key.page_up, Key.page_down] and not page_ctl_flag:
            return False

        flash_icon()
        keyboard.press(operation)
        keyboard.release(operation)

    elif callable(operation):
        operation()


operation_dict = {
    "lt": {
        "scroll": {"up": Key.media_volume_up, "down": Key.media_volume_down},
        "middle": Key.media_volume_mute,
        "x1": Key.media_volume_down,
        "x2": Key.media_volume_up,
    },
    "lb": {
        "scroll": {"up": Key.media_previous, "down": Key.media_next},
        "middle": Key.media_play_pause,
        "x1": Key.media_next,
        "x2": Key.media_previous,
    },
    "rt": {
        "scroll": {"up": Key.page_up, "down": Key.page_down},
        "middle": False,
        "x1": Key.page_down,
        "x2": Key.page_up,
    },
    "rb": {
        "scroll": {"up": False, "down": False},
        "middle": False,
        "x1": False,
        "x2": False,
    },
}


# 滚轮
def on_scroll(x, y, dx, dy):
    position_area = get_position_area(x, y)
    if position_area == False:
        return True
    execute_operation(
        operation_dict[position_area]["scroll"]["up" if dy > 0 else "down"]
    )


def on_click(x, y, button, pressed):
    if (
        not button in [mouse.Button.middle, mouse.Button.x1, mouse.Button.x2]
        or not pressed
    ):
        return True

    position_area = get_position_area(x, y)
    if position_area == False:
        return True
    if button == mouse.Button.middle:
        key = "middle"
    elif button == mouse.Button.x1:
        key = "x1"
    elif button == mouse.Button.x2:
        key = "x2"
    else:
        return True

    execute_operation(operation_dict[position_area][key])


# 创建托盘图标并添加菜单选项
def create_image():
    width = 48
    height = 64

    image = Image.new("RGBA", (64, 64), (255, 255, 255, 0))  # 白色背景
    draw = ImageDraw.Draw(image)

    draw_fill = (64, 150, 34)

    draw.rectangle((8, 0, width // 4 + 8, height), fill=draw_fill)

    draw.rectangle(
        (8, 0, width + 8, height // 4),
        fill=((72, 200, 50) if volume_ctl_flag else (200, 72, 50)),
    )
    draw.rectangle(
        (8, height // 8 * 3, width + 8, height // 8 * 5),
        fill=((68, 180, 47) if media_ctl_flag else (180, 68, 47)),
    )
    draw.rectangle(
        (8, height // 4 * 3, width + 8, height),
        fill=((64, 150, 40) if page_ctl_flag else (150, 64, 40)),
    )

    # 绘制斜线
    # 设置线的起点和终点
    start_point = (12, height)
    end_point = (width + 6, -8)
    line_color = (80, 220, 55)
    line_width = 16  # 线的宽度
    draw.line([start_point, end_point], fill=line_color, width=line_width)

    return image


# 托盘图标斜线闪烁
def flash_icon():
    width = 48
    height = 64

    image = create_image()

    draw = ImageDraw.Draw(image)

    # 绘制斜线
    # 设置线的起点和终点
    start_point = (12, height)
    end_point = (width + 6, -8)
    line_color = (255, 255, 255)
    line_width = 16  # 线的宽度
    draw.line([start_point, end_point], fill=line_color, width=line_width)

    icon.icon = image
    icon.update_menu()

    global restore_icon_time
    restore_icon_time = time.perf_counter() + flas_time - flas_time / 10
    threading.Timer(flas_time, restore_icon).start()


restore_icon_time = 0
flas_time = 0.1


# 延迟恢复图标样式
def restore_icon():
    if time.perf_counter() >= restore_icon_time:
        update_icon()


# 更新托盘
def update_icon():
    update_icon_img()
    update_menu()
    icon.update_menu()


# 更新托盘图标
def update_icon_img():
    image = create_image()
    icon.icon = image


# 更新托盘菜单
def update_menu():
    icon.menu = Menu(
        item(
            ("O" if volume_ctl_flag else "X") + " 音量调节",
            lambda icon, item: toggle("volume"),
        ),
        item(
            ("O" if media_ctl_flag else "X") + " 媒体控制",
            lambda icon, item: toggle("media"),
        ),
        item(
            ("O" if page_ctl_flag else "X") + " 页面滚动",
            lambda icon, item: toggle("page"),
        ),
        item("退出程序", lambda icon, item: close_program()),
    )


# 更改flag
def toggle(flag_name):
    global volume_ctl_flag, media_ctl_flag, page_ctl_flag
    if flag_name == "volume":
        volume_ctl_flag = not volume_ctl_flag
    elif flag_name == "media":
        media_ctl_flag = not media_ctl_flag
    elif flag_name == "page":
        page_ctl_flag = not page_ctl_flag

    update_icon()


# 按键绑定开关操作
def toggle_page_ctl():
    toggle("page")


operation_dict["rt"]["middle"] = toggle_page_ctl


def toggle_volume_ctl():
    toggle("volume")


operation_dict["rt"]["x2"] = toggle_volume_ctl


def toggle_media_ctl():
    toggle("media")


operation_dict["rt"]["x1"] = toggle_media_ctl


# 退出程序
def close_program():
    icon.stop()
    os._exit(0)


icon = Icon("test_icon", create_image())
update_menu()


# 启动托盘图标
def run_tray():
    icon.run()


thread = threading.Thread(target=run_tray, daemon=True)
thread.start()

# 启动鼠标监听器
with mouse.Listener(on_scroll=on_scroll, on_click=on_click) as listener:
    listener.join()
