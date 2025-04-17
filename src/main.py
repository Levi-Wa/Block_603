
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
    page.title = "Расписание и Д/з УрСЭИ"
    page.theme_mode = "light"
    page.window_width = 400
    page.window_height = 700

    group_id_map = {
        "Группа 1": 26616,
        "Группа 2": 26617,
        "Группа 3": 26618
    }

    selected_group = page.client_storage.get("group")
    notes = page.client_storage.get("notes") or []

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

        all_subjects = set(
            lesson["SubjName"]
            for month in schedule_data["Month"]
            for day in month["Sched"]
            for lesson in day["mainSchedule"]
        )

        def get_next_practice_date(subject_name):
            today = datetime.now()
            all_days = [day for month in schedule_data["Month"] for day in month["Sched"]]
            for day in all_days:
                day_date = datetime.strptime(day["datePair"], "%d.%m.%Y")
                if day_date > today:
                    for lesson in day["mainSchedule"]:
                        if lesson["SubjName"] == subject_name:
                            return day_date.strftime("%d.%m.%Y")
            return None

        def show_notes_view():
            nonlocal notes

            def add_note(e):
                subject = subject_dropdown.value
                note_text = note_input.value
                if subject and note_text:
                    validity_type = validity_dropdown.value
                    
            def delete_note(note):
                notes.remove(note)
                page.client_storage.set("notes", notes)
                update_notes_list()

            def change_validity(note):
                def save_new_date(e):
                    new_date = dp.value
                    if new_date:
                        note["valid_until"] = new_date.strftime("%d.%m.%Y")
                        page.client_storage.set("notes", notes)
                        update_notes_list()
                        page.update()

                dp = ft.DatePicker()
                dp.on_change = save_new_date
                page.dialog = ft.AlertDialog(
                    title=ft.Text("Выберите новую дату актуальности"),
                    content=dp,
                    actions=[ft.TextButton("OK", on_click=lambda _: page.dialog.close())]
                )
                page.dialog.open = True  # Открываем диалог для выбора даты
                page.update() 

            def update_notes_list():
                notes_list.controls.clear()
                if not notes:
                    notes_list.controls.append(ft.Text("Заметки пока отсутствуют."))
                else:
                    for note in notes:
                        valid_text = f"Актуально до: {note['valid_until']}" if note["valid_until"] else "Занятий больше нет."
                        notes_list.controls.append(
                            ft.Column([
                                ft.Text(f"Предмет: {note['subject']}", weight="bold"),
                                ft.Text(f"Заметка: {note['text']}"),
                                ft.Text(valid_text, italic=True, color="gray"),
                                ft.Row([
                                    ft.ElevatedButton("Удалить", on_click=lambda _, n=note: delete_note(n)),
                                    ft.ElevatedButton("Изменить актуальность", on_click=lambda _, n=note: change_validity(n)),
                                ])
                            ])
                        )
                page.update()

            note_input = ft.TextField(label="Введите заметку")
            subject_dropdown = ft.Dropdown(
                label="Выберите предмет",
                options=[ft.dropdown.Option(subject) for subject in sorted(all_subjects)]
            )
            notes_list = ft.Column()
            update_notes_list()
            return ft.Column([
                ft.Text("Ваши домашние задания", size=18, weight="bold"),
                subject_dropdown,
                note_input,
                ft.ElevatedButton("Создать", on_click=add_note),
                notes_list
            ])

        def show_schedule_view():
            slider_initialized = False
            view_mode_dropdown = ft.Dropdown(
                label="Вид расписания",
                options=[
                    ft.dropdown.Option("Неделя"),
                    ft.dropdown.Option("Месяц"),
                    ft.dropdown.Option("Все")
                ],
                value="Неделя"
            )
            slider = ft.Slider(min=0, max=0, value=0, divisions=1, visible=False)
            schedule_column = ft.Column(scroll=ft.ScrollMode.AUTO)

            offset_index = ft.Text("0")

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
                    if now.month == 12:
                        last_day = datetime(now.year, now.month, 31)
                    else:
                        next_month = datetime(now.year, now.month + 1, 1)
                        last_day = next_month - timedelta(days=1)
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
                page.update()

                now_date = datetime.now().date()
                tomorrow_date = now_date + timedelta(days=1)
                slider.on_change = lambda e: update_schedule_view()

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

                schedule_columns = []
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
                        if status == "ongoing":
                            text_control = ft.Text(lesson_text, bgcolor="lightgreen")
                        elif status == "finished":
                            text_control = ft.Text(lesson_text, color="gray")
                        else:
                            text_control = ft.Text(lesson_text)
                        lessons_controls.append(text_control)
                    schedule_columns.append(
                        ft.Column([
                            day_header,
                            *lessons_controls,
                            ft.Divider()
                        ])
                    )
                schedule_column.controls = schedule_columns if schedule_columns else [ft.Text("Нет данных")]
                page.update()

            view_mode_dropdown.on_change = update_schedule_view
            slider.on_change = update_schedule_view
            update_schedule_view()

            return ft.Column([
                view_mode_dropdown,
                slider,
                schedule_column
            ])

        def show_settings_view():
            def change_group(e):
                page.client_storage.remove("group")
                page.views.clear()
                page.controls.clear()
                page.update()
                init_group_selection()
            return ft.Column([
                ft.Text("Настройки", size=18, weight="bold"),
                ft.Text(f"Текущая группа: {current_group}"),
                ft.ElevatedButton("Сменить группу", on_click=change_group)
            ])

        page.views.clear()
        page.views.append(
            ft.View("/", controls=[
                ft.Tabs(
                    tabs=[
                        ft.Tab(text="Д/з", content=show_notes_view()),
                        ft.Tab(text="Расписание", content=show_schedule_view()),
                        ft.Tab(text="Настройки", content=show_settings_view())
                    ]
                )
            ])
        )
        page.update()

    if selected_group is None:
        init_group_selection()
    else:
        init_main_ui()

ft.app(target=main)