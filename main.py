from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.checkbox import CheckBox
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
import re
import os

FEES = {
    "reg": {
        "2.1_submit": 4000, "2.1_extra_class": 1000,
        "2.4_exam": 13000, "2.4_extra_class": 2500,
        "2.4_extra_term": 500, "2.11_base": 18000,
        "2.11_extra_class": 2000, "2.11_threshold": 5,
        "2.14_paper_svid": 3000,
    },
    "renewal": {
        "2.22_renewal": 50000, "2.22_extra_class": 10000,
    },
}

MKTU = {
    "01":"Хим. продукты", "02":"Краски, лаки", "03":"Косметика",
    "04":"Масла, смазки", "05":"Фармацевтика", "06":"Металлы",
    "07":"Машины", "08":"Инструменты", "09":"Электроника, ПО",
    "10":"Мед. приборы", "11":"Освещение", "12":"Транспорт",
    "13":"Оружие", "14":"Ювелирка", "15":"Муз. инструменты",
    "16":"Бумага", "17":"Резина, пластик", "18":"Кожа, сумки",
    "19":"Стройматериалы", "20":"Мебель", "21":"Посуда",
    "22":"Верёвки", "23":"Пряжа", "24":"Ткани",
    "25":"Одежда, обувь", "26":"Кружева", "27":"Ковры",
    "28":"Игры, спорт", "29":"Мясо, рыба", "30":"Кофе, чай",
    "31":"Сельхоз", "32":"Пиво, напитки", "33":"Алкоголь",
    "34":"Табак", "35":"Реклама", "36":"Финансы",
    "37":"Строительство", "38":"Телеком", "39":"Транспорт",
    "40":"Обработка", "41":"Образование", "42":"IT, наука",
    "43":"Гостиницы", "44":"Медицина", "45":"Юр. услуги"
}


class RegTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=5, spacing=2, **kwargs)
        
        self.add_widget(Label(text="РЕГИСТРАЦИЯ ТОВАРНОГО ЗНАКА", size_hint_y=None, height=28, bold=True, font_size=15))
        
        self.reg_input = TextInput(
            hint_text='35 — реклама; маркетинг\n42 — ПО; разработка',
            size_hint_y=None, height=65, multiline=True, font_size=13
        )
        self.add_widget(self.reg_input)
        
        btns = BoxLayout(size_hint_y=None, height=38, spacing=4)
        btns.add_widget(Button(text="Распознать", on_press=self.parse_text, font_size=12))
        btns.add_widget(Button(text="Очистить", on_press=self.clear_all, font_size=12))
        self.add_widget(btns)
        
        self.add_widget(Label(text="Классы МКТУ:", size_hint_y=None, height=22, bold=True, font_size=12))
        self.class_grid = GridLayout(cols=6, spacing=1, size_hint_y=None)
        self.class_grid.bind(minimum_height=self.class_grid.setter('height'))
        self.class_checks = {}
        
        for i in range(1, 46):
            cls = f"{i:02d}"
            box = BoxLayout(size_hint_y=None, height=30)
            check = CheckBox(size_hint_x=None, width=26)
            check.bind(active=self.on_class_toggle)
            box.add_widget(check)
            box.add_widget(Label(text=cls, size_hint_x=None, width=30, font_size=10))
            self.class_checks[cls] = check
            self.class_grid.add_widget(box)
        
        scroll = ScrollView(size_hint_y=0.2)
        scroll.add_widget(self.class_grid)
        self.add_widget(scroll)
        
        self.add_widget(Label(text="Термины:", size_hint_y=None, height=22, bold=True, font_size=12))
        self.terms_inputs = {}
        self.terms_layout = BoxLayout(orientation='vertical', spacing=1, size_hint_y=None)
        self.terms_layout.bind(minimum_height=self.terms_layout.setter('height'))
        terms_scroll = ScrollView(size_hint_y=0.12)
        terms_scroll.add_widget(self.terms_layout)
        self.add_widget(terms_scroll)
        
        self.add_widget(Button(text="💰 РАССЧИТАТЬ", on_press=self.calculate, size_hint_y=None, height=42, font_size=14, bold=True))
        
        self.result_label = Label(text="Выберите классы\nи нажмите «Рассчитать»", size_hint_y=0.35, font_size=10, halign='left', valign='top')
        self.result_label.bind(size=self.result_label.setter('text_size'))
        result_scroll = ScrollView()
        result_scroll.add_widget(self.result_label)
        self.add_widget(result_scroll)
        
        self.update_terms()
    
    def on_class_toggle(self, instance, value):
        self.update_terms()
        self.calculate()
    
    def update_terms(self, *args):
        self.terms_layout.clear_widgets()
        self.terms_inputs.clear()
        
        selected = sorted([c for c, ch in self.class_checks.items() if ch.active])
        
        if not selected:
            self.terms_layout.add_widget(Label(text="Классы не выбраны", size_hint_y=None, height=25))
            return
        
        for cls in selected:
            box = BoxLayout(size_hint_y=None, height=28, spacing=4)
            box.add_widget(Label(text=f"Кл.{cls}:", size_hint_x=None, width=50, font_size=11))
            inp = TextInput(text="0", size_hint_x=None, width=50, multiline=False, font_size=11)
            inp.bind(text=self.on_term_change)
            box.add_widget(inp)
            self.terms_inputs[cls] = inp
            self.terms_layout.add_widget(box)
    
    def on_term_change(self, instance, value):
        self.calculate()
    
    def parse_text(self, instance):
        text = self.reg_input.text.strip()
        if not text:
            return
        
        for check in self.class_checks.values():
            check.active = False
        
        parsed = {}
        for line in text.split('\n'):
            m = re.match(r'(?:Класс\s+)?(\d{1,2})\s*[—\-–]\s*(.+)', line.strip())
            if m:
                cls = m.group(1).strip().zfill(2)
                terms = [t.strip() for t in m.group(2).split(';') if t.strip()]
                if cls in self.class_checks:
                    self.class_checks[cls].active = True
                    parsed[cls] = len(terms)
        
        self.update_terms()
        
        for cls, cnt in parsed.items():
            if cls in self.terms_inputs:
                self.terms_inputs[cls].text = str(cnt)
        
        self.calculate()
    
    def calculate(self, *args):
        selected = sorted([c for c, ch in self.class_checks.items() if ch.active])
        
        if not selected:
            self.result_label.text = "Классы не выбраны"
            return
        
        f = FEES["reg"]
        cnt = len(selected)
        tt = 0
        et = 0
        breakdown = []
        
        for cls in selected:
            try:
                t = int(self.terms_inputs[cls].text)
            except:
                t = 0
            tt += t
            extra = max(0, t - 10)
            et += extra
            breakdown.append((cls, t, extra))
        
        f21 = f["2.1_submit"] + max(0, cnt-1) * f["2.1_extra_class"]
        f24 = f["2.4_exam"] + max(0, cnt-1) * f["2.4_extra_class"] + et * f["2.4_extra_term"]
        f211 = f["2.11_base"] if cnt <= f["2.11_threshold"] else f["2.11_base"] + (cnt - f["2.11_threshold"]) * f["2.11_extra_class"]
        f214 = f["2.14_paper_svid"] * cnt
        total_el = f21 + f24 + f211
        total_bum = total_el + f214
        
        result = "=" * 38 + "\n"
        result += " РАСЧЁТ ПОШЛИН ЗА РЕГИСТРАЦИЮ ТЗ\n"
        result += "=" * 38 + "\n\n"
        result += f"2.1. Подача:        {f21:>9,} ₽\n"
        result += f"2.4. Экспертиза:    {f24:>9,} ₽\n"
        result += f"2.11. Эл. св-во:    {f211:>9,} ₽\n"
        result += f"2.14. Бум. св-во:   {f214:>9,} ₽\n\n"
        result += "-" * 38 + "\n"
        result += f"Сумма 2.1.+2.4.:    {f21+f24:>9,} ₽\n"
        result += "-" * 38 + "\n"
        result += f"ИТОГО (эл.):        {total_el:>9,} ₽\n"
        result += f"ИТОГО (бум.):       {total_bum:>9,} ₽\n"
        result += "=" * 38 + "\n\n"
        result += f"Классов: {cnt} | Терминов: {tt} | Сверх 10: {et}\n"
        result += f"Классы: {', '.join(selected)}\n\n"
        result += "РАЗБИВКА:\n"
        for cls, t, extra in breakdown:
            if extra > 0:
                result += f"  Класс {cls}: {t} терм. (+{extra})\n"
            else:
                result += f"  Класс {cls}: {t} терм.\n"
        
        self.result_label.text = result
    
    def clear_all(self, instance):
        for check in self.class_checks.values():
            check.active = False
        self.reg_input.text = ""
        self.result_label.text = "Выберите классы\nи нажмите «Рассчитать»"
        self.update_terms()


class RenewalTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=15, spacing=10, **kwargs)
        
        self.add_widget(Label(text="ПРОДЛЕНИЕ ТЗ НА 10 ЛЕТ", size_hint_y=None, height=32, bold=True, font_size=17))
        
        box = BoxLayout(size_hint_y=None, height=42, spacing=10)
        box.add_widget(Label(text="Классов МКТУ:", size_hint_x=None, width=120, font_size=14))
        self.classes_input = TextInput(text="1", size_hint_x=None, width=70, multiline=False, font_size=17)
        box.add_widget(self.classes_input)
        box.add_widget(Label(text=""))
        self.add_widget(box)
        
        self.add_widget(Button(text="💰 РАССЧИТАТЬ", on_press=self.calc, size_hint_y=None, height=48, font_size=16))
        
        self.result = Label(text="", size_hint_y=0.7, font_size=13)
        self.result.bind(size=self.result.setter('text_size'))
        self.add_widget(self.result)
    
    def calc(self, instance):
        try:
            cnt = int(self.classes_input.text)
        except:
            cnt = 1
        
        total = FEES["renewal"]["2.22_renewal"] + max(0, cnt-1) * FEES["renewal"]["2.22_extra_class"]
        
        self.result.text = f"ПРОДЛЕНИЕ ТЗ НА 10 ЛЕТ\n{'='*35}\nКлассов: {cnt}\n2.22. Продление: {total:>10,} ₽\n{'='*35}\nИТОГО: {total:>10,} ₽"


class QRTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=15, spacing=10, **kwargs)
        
        self.add_widget(Label(text="QR-КОД ДЛЯ ОПЛАТЫ ПОШЛИНЫ", size_hint_y=None, height=32, bold=True, font_size=17))
        
        self.add_widget(Label(text="Сумма (руб.):", size_hint_y=None, height=22, font_size=13))
        self.amount = TextInput(text="", size_hint_y=None, height=42, multiline=False, font_size=17)
        self.add_widget(self.amount)
        
        self.add_widget(Label(text="Назначение:", size_hint_y=None, height=22, font_size=13))
        self.purpose = TextInput(text="Пошлина за регистрацию ТЗ", size_hint_y=None, height=42, font_size=13)
        self.add_widget(self.purpose)
        
        self.add_widget(Button(text="📱 СОЗДАТЬ QR-КОД", on_press=self.gen_qr, size_hint_y=None, height=48, font_size=16))
        
        self.qr_info = Label(text="Введите сумму и нажмите кнопку", size_hint_y=0.6, font_size=13)
        self.add_widget(self.qr_info)
    
    def gen_qr(self, instance):
        try:
            import qrcode
            amount = self.amount.text
            purpose = self.purpose.text
            
            if not amount:
                self.qr_info.text = "❌ Введите сумму!"
                return
            
            qr = qrcode.QRCode(box_size=6, border=3)
            qr_data = (
                f"ST00012|Name={purpose}|"
                f"PersonalAcc=40102810045370000002|"
                f"BankName=ОПЕРУ Банка России|"
                f"BIC=024501901|"
                f"CorrespAcc=03100643000000019500|"
                f"PayeeINN=7730176088|"
                f"KPP=773001001|"
                f"Sum={amount}00"
            )
            qr.add_data(qr_data)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            save_path = '/sdcard/Download/patentcalc_qr.png'
            os.makedirs('/sdcard/Download', exist_ok=True)
            img.save(save_path)
            
            self.qr_info.text = f"✅ QR-код создан!\n\nСумма: {amount} ₽\nНазначение: {purpose}\n\nСохранён в:\n{save_path}"
        except Exception as e:
            self.qr_info.text = f"Ошибка:\n{str(e)}"


class RefTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=8, **kwargs)
        
        self.add_widget(Label(text="КЛАССЫ МКТУ", size_hint_y=None, height=30, bold=True, font_size=16))
        
        layout = BoxLayout(orientation='vertical', spacing=1, size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))
        
        for cls in sorted(MKTU.keys()):
            row = BoxLayout(size_hint_y=None, height=26)
            row.add_widget(Label(text=f"[{cls}]", size_hint_x=None, width=42, bold=True, font_size=10))
            row.add_widget(Label(text=MKTU[cls], font_size=10, halign='left'))
            layout.add_widget(row)
        
        scroll = ScrollView()
        scroll.add_widget(layout)
        self.add_widget(scroll)


class PatentCalcApp(App):
    def build(self):
        self.title = "PatentCalc Pro"
        
        tabs = TabbedPanel()
        tabs.do_default_tab = False
        
        reg = TabbedPanelItem(text="📋 Регистрация")
        reg.content = RegTab()
        tabs.add_widget(reg)
        
        ren = TabbedPanelItem(text="🔄 Продление")
        ren.content = RenewalTab()
        tabs.add_widget(ren)
        
        qr = TabbedPanelItem(text="📱 QR-код")
        qr.content = QRTab()
        tabs.add_widget(qr)
        
        ref = TabbedPanelItem(text="📚 МКТУ")
        ref.content = RefTab()
        tabs.add_widget(ref)
        
        tabs.default_tab = reg
        return tabs


if __name__ == "__main__":
    PatentCalcApp().run()
