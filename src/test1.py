import flet as ft
import requests
from datetime import datetime, timedelta

def fetch_schedule(group_id):
    url = f"https://api.ursei.su/public/schedule/rest/GetGsSched?grpid={group_id}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса к API: {e}")
        return None

def main(page: ft.Page):
    page.title = "Расписание УрСЭИ"
    page.theme_mode = "light"
    page.window_width = 400
    page.window_height = 700

    group_id_map = {
        "Группа 1": 26616,
        "Группа 2": 26617,
        "Группа 3": 26618
    }

    selected_group = page.client_storage.get("group")

    def init_group_selection():
        def save_group(e):
            chosen_group = group_dropdown.value
            if chosen_group:
                page.client_storage.set("group", chosen_group)
                page.dialog.open = False
                page.update()
                init_main_ui()

        group_dropdown = ft.Dropdown(
            label="Выберите вашу группу",
            options=[ft.dropdown.Option(g) for g in group_id_map.keys()]
        )
        alert_dialog = ft.AlertDialog(
            title=ft.Text("Выбор группы"),
            content=group_dropdown,
            actions=[ft.TextButton("OK", on_click=save_group)],
            open=True
        )
        page.dialog = alert_dialog
        page.controls.append(alert_dialog)
        page.update()

    def init_main_ui():
        current_group = page.client_storage.get("group")
        group_id = group_id_map.get(current_group)
        schedule_data = fetch_schedule(group_id)

        if not schedule_data or "Month" not in schedule_data:
            page.controls.append(ft.Text("Не удалось загрузить расписание. Попробуйте позже."))
            page.update()
            return

        slider = ft.Slider(min=0, max=0, value=0, divisions=1, visible=False)
        schedule_column = ft.Column(scroll=ft.ScrollMode.AUTO)
        view_mode_dropdown = ft.Dropdown(
            label="Режим просмотра",
            options=[ft.dropdown.Option("Неделя"), ft.dropdown.Option("Месяц"), ft.dropdown.Option("Все")],
            value="Неделя"
        )
        offset_index = ft.Text("0")
        slider_initialized = False

        def update_schedule_view(e=None):
            nonlocal slider_initialized
            mode = view_mode_dropdown.value
            all_days = [day for month in schedule_data["Month"] for day in month["Sched"]]
            all_days.sort(key=lambda d: datetime.strptime(d["datePair"], "%d.%m.%Y"))
            displayed_days = []

            if mode == "Неделя":
                today = datetime.now()
                start_of_week = today - timedelta(days=today.weekday())
                end_of_week = start_of_week + timedelta(days=6)
                displayed_days = [day for day in all_days 
                                  if start_of_week <= datetime.strptime(day["datePair"], "%d.%m.%Y") <= end_of_week]
                slider.visible = False
            elif mode == "Месяц":
                now = datetime.now()
                first_day = datetime(now.year, now.month, 1)
                last_day = (datetime(now.year, now.month + 1, 1) - timedelta(days=1)).date() if now.month != 12 else datetime(now.year, now.month, 31).date()
                displayed_days = [day for day in all_days 
                                  if first_day <= datetime.strptime(day["datePair"], "%d.%m.%Y") <= last_day]
                slider.visible = True
            elif mode == "Все":
                displayed_days = all_days
                slider.visible = True

            if len(displayed_days) > 7:
                slider.max = len(displayed_days) - 7
                slider.divisions = len(displayed_days) - 7
            else:
                slider.max = 0
                slider.divisions = 1

            if not slider_initialized and mode in ["Месяц", "Все"]:
                today_str = datetime.now().strftime("%d.%m.%Y")
                for i, day in enumerate(displayed_days):
                    if day["datePair"] == today_str:
                        slider.value = max(0, min(i, len(displayed_days) - 7))
                        break
                slider_initialized = True

            start_index = int(slider.value)
            offset_index.value = f"Страница: {start_index + 1}"
            chunk = displayed_days[start_index:start_index+7] if len(displayed_days) > 7 else displayed_days

            now_date = datetime.now().date()
            tomorrow_date = now_date + timedelta(days=1)
            schedule_columns = []

            def get_lesson_status(lesson, day_date):
                lesson_start = datetime.combine(day_date, datetime.strptime(lesson["TimeStart"], "%H:%M").time())
                lesson_end = lesson_start + timedelta(minutes=95)
                current = datetime.now()
                if current < lesson_start:
                    return "upcoming"
                elif lesson_start <= current <= lesson_end:
                    return "ongoing"
                else:
                    return "finished"

            for day in chunk:
                day_date = datetime.strptime(day["datePair"], "%d.%m.%Y").date()
                day_header = ft.Text(f"{day['datePair']} ({day['dayWeek']})", size=16, weight="bold")
                if day_date == now_date:
                    day_header.color = "green"
                elif day_date == tomorrow_date:
                    day_header.color = "blue"

                lessons_controls = []
                for lesson in day["mainSchedule"]:
                    status = get_lesson_status(lesson, day_date) if day_date == now_date else "default"
                    lesson_text = f"{lesson['TimeStart']} — {lesson['SubjName']} ({lesson['LoadKindSN']}, {lesson['FIO']}, ауд. {lesson['Aud']})"
                    lesson_container = ft.Container(
                        content=ft.Text(lesson_text),
                        padding=10,
                        border_radius=12,
                        border=ft.border.all(2, ft.Colors.GREY),
                        margin=ft.margin.all(8),
                        bgcolor=ft.Colors.WHITE
                    )
                    if status == "ongoing":
                        lesson_container.bgcolor = ft.Colors.LIGHT_GREEN
                    elif status == "finished":
                        lesson_container.color = ft.Colors.GREY
                    lessons_controls.append(lesson_container)

                schedule_columns.append(
                    ft.Column([day_header, *lessons_controls, ft.Divider()])
                )

            schedule_column.controls = schedule_columns if schedule_columns else [ft.Text("Нет данных")]
            page.update()

        view_mode_dropdown.on_change = update_schedule_view
        slider.on_change = update_schedule_view
        update_schedule_view()

        page.views.clear()
        page.views.append(
            ft.View(
                "/",
                controls=[
                    ft.Container(
                        content=schedule_column,
                        height=600,
                        expand=True
                    ),
                    view_mode_dropdown,
                    slider
                ]
            )
        )
        page.update()

    if selected_group is None:
        init_group_selection()
    else:
        init_main_ui()

ft.app(target=main)
