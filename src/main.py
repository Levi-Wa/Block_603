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

    form_options = ["Очная форма"]
    course_options = ["1 курс", "2 курс", "3 курс", "4 курс"]

    group_id_map = {
        "Очная форма 1 курс": {
            "БД-101": 26616,
            "БД-102": 26617,
            "ИД-101": 26618,
            "ИСПД-101": 26619,
            "ИСПД-102": 26620,
            "ИСПД-103": 26621,
            "МД-101": 26622,
            "РД-101": 26623,
            "РД-102": 26624,
            "РСОД-101": 26625,
            "УПД-101": 26626,
            "ЭБД-101": 26627,
            "ЭБД-102": 26628,
            "ЭД-101": 26629,
            "ЮД-101": 26630
        },
        "Очная форма 2 курс": {
            "БД-201": 26631,
            "БД-202": 26632,
            "ИД-201": 26633,
            "ИСПД-201": 26634,
            "ИСПД-202": 26635,
            "ИСПД-203": 26636,
            "МД-201": 26637,
            "РД-201": 26638,
            "РД-202": 26639,
            "РСОД-201": 26640,
            "УПД-201": 26641,
            "ЭБД-201": 26642,
            "ЭБД-202": 26643,
            "ЭД-201": 26644,
            "ЮД-201": 26645
        },
        "Очная форма 3 курс": {
            "БД-301": 26646,
            "БД-302": 26647,
            "ИД-301": 26648,
            "ИСПД-301": 26649,
            "ИСПД-302": 26650,
            "ИСПД-303": 26651,
            "МД-301": 26652,
            "РД-301": 26653,
            "РД-302": 26654,
            "РСОД-301": 26655,
            "УПД-301": 26656,
            "ЭБД-301": 26657,
            "ЭБД-302": 26658,
            "ЭД-301": 26659,
            "ЮД-301": 26660
        },
        "Очная форма 4 курс": {
            "БД-401": 26661,
            "БД-402": 26662,
            "ИД-401": 26663,
            "ИСПД-401": 26664,
            "ИСПД-402": 26665,
            "ИСПД-403": 26666,
            "МД-401": 26667,
            "РД-401": 26668,
            "РД-402": 26669,
            "РСОД-401": 26670,
            "УПД-401": 26671,
            "ЭБД-401": 26672,
            "ЭБД-402": 26673,
            "ЭД-401": 26674,
            "ЮД-401": 26675
        }
    }

    selected_form = None
    selected_course = None
    selected_group = None
    notes = page.client_storage.get("notes") or []

    def init_first_step():
        def select_form(e):
            global selected_form
            selected_form = form_dropdown.value
            form_alert_dialog.open = False
            page.update()
            init_second_step()

        form_dropdown = ft.Dropdown(
            label="Форма обучения",
            options=[ft.dropdown.Option(form) for form in form_options],
        )

        form_alert_dialog = ft.AlertDialog(
            title=ft.Text("Шаг 1: Выберите форму обучения"),
            content=form_dropdown,
            actions=[ft.TextButton("Продолжить", on_click=select_form)],
            open=True
        )

        page.dialog = form_alert_dialog
        page.controls.append(form_alert_dialog)
        page.update()

    def init_second_step():
        def select_course(e):
            global selected_course
            selected_course = course_dropdown.value
            course_alert_dialog.open = False
            page.update()
            init_third_step()

        course_dropdown = ft.Dropdown(
            label="Выберите курс",
            options=[ft.dropdown.Option(course) for course in course_options],
        )

        course_alert_dialog = ft.AlertDialog(
            title=ft.Text("Шаг 2: Выберите курс"),
            content=course_dropdown,
            actions=[ft.TextButton("Продолжить", on_click=select_course)],
            open=True
        )

        page.dialog = course_alert_dialog
        page.controls.append(course_alert_dialog)
        page.update()

    def init_third_step():
        def select_group(e):
            global selected_group
            selected_group = group_dropdown.value
            group_alert_dialog.open = False
            page.update()
            init_main_ui()

        # Получаем группы для выбранного курса
        full_groups = group_id_map[f"{selected_form} {selected_course}"]

        group_dropdown = ft.Dropdown(
            label="Выберите группу",
            options=[ft.dropdown.Option(group) for group in full_groups.keys()],
        )

        group_alert_dialog = ft.AlertDialog(
            title=ft.Text("Шаг 3: Выберите группу"),
            content=group_dropdown,
            actions=[ft.TextButton("Готово", on_click=select_group)],
            open=True
        )

        page.dialog = group_alert_dialog
        page.controls.append(group_alert_dialog)
        page.update()  

    def init_main_ui():
        slider_initialized = False  # Инициализируем её значением False
        current_group = page.client_storage.get("group")
        group_id = group_id_map.get(current_group)
        schedule_data = fetch_schedule(group_id)
        view_mode_dropdown= ft.Dropdown(
            label="Режим просмотра",
            options=[
                ft.dropdown.Option("Неделя"),
                ft.dropdown.Option("Месяц"),
                ft.dropdown.Option("Все")
                ],
                value="Неделя"
            )

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

        def get_next_lesson_date():
            today = datetime.now()
            all_days = [day for month in schedule_data["Month"] for day in month["Sched"]]
            all_days.sort(key=lambda d: datetime.strptime(d["datePair"], "%d.%m.%Y"))
            for day in all_days:
                day_date = datetime.strptime(day["datePair"], "%d.%m.%Y")
                if day_date > today:
                    return day_date.strftime("%d.%m.%Y")
            return None

        def show_notes_view():
            nonlocal notes

            validity_dropdown = ft.Dropdown(
                label="Актуально до",
                options=[
                    ft.dropdown.Option("До следующей практики"),
                    ft.dropdown.Option("До следующего занятия")
                ],
                value="До следующей практики"
            )

            note_input = ft.TextField(label="Введите заметку")
            subject_dropdown = ft.Dropdown(
                label="Выберите предмет",
                options=[ft.dropdown.Option(subject) for subject in sorted(all_subjects)]
            )

            notes_list = ft.Column()

            def add_note(e):
                subject = subject_dropdown.value
                note_text = note_input.value
                validity_type = validity_dropdown.value

                if subject and note_text:
                    if validity_type == "До следующей практики":
                        valid_until = get_next_practice_date(subject)
                    else:
                        valid_until = get_next_lesson_date()

                    note = {
                        "subject": subject,
                        "text": note_text,
                        "valid_until": valid_until,
                        "validity_type": validity_type  # сохраняем тип
                    }
                    notes.append(note)
                    page.client_storage.set("notes", notes)
                    update_notes_list()
                    note_input.value = ""
                    page.update()

            def delete_note(note):
                notes.remove(note)
                page.client_storage.set("notes", notes)
                update_notes_list()

            def change_validity(note):
                subject = note["subject"]
                validity_type = note.get("validity_type", "До следующего занятия")
                previous_valid_until = note.get("valid_until")  # Получаем предыдущую дату актуальности

                print(f"Предмет: {subject}, Тип актуальности: {validity_type}, Предыдущая дата: {previous_valid_until}")

                # Находим ближайшие дату занятия или практики ПОСЛЕ предыдущего установленного срока
                if validity_type == "До следующей практики":
                    new_date = find_next_practice_after(subject, previous_valid_until)
                else:
                    new_date = find_next_lesson_after(subject, previous_valid_until)

                if new_date:
                    print(f"Новая дата актуальности: {new_date}")
                    note["valid_until"] = new_date
                    page.client_storage.set("notes", notes)
                    update_notes_list()
                    page.update()
                else:
                    print("Не удалось найти следующую практику или занятие.")
                    page.snack_bar = ft.SnackBar(ft.Text("Не удалось найти следующее занятие."))
                    page.snack_bar.open = True
                    page.update()

            def find_next_lesson_after(subject, after_date):
                """Находит ближайшее занятие после указанной даты."""
                parsed_after_date = datetime.strptime(after_date, "%d.%m.%Y") if after_date else datetime.min
                filtered_lessons = (
                    lesson
                    for month in schedule_data["Month"]
                    for day in month["Sched"]
                    for lesson in day["mainSchedule"]
                    if lesson["SubjName"] == subject and datetime.strptime(day.get("datePair", ""), "%d.%m.%Y") >= parsed_after_date
                )
                next_lesson = next(filtered_lessons, None)
                return next_lesson.get("datePair") if next_lesson else None

            

            
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

            update_notes_list()
            return ft.Column([
                ft.Text("Ваши домашние задания", size=18, weight="bold"),
                subject_dropdown,
                validity_dropdown,
                note_input,
                ft.ElevatedButton("Создать", on_click=add_note),
                notes_list
            ])

        def show_schedule_view():
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
        def init_first_step():
    else:
        init_main_ui()

ft.app(target=main)