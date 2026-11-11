# Presentation pages.  Russian -> (Kazakh, English)
T = {}

# --- home --------------------------------------------------------------------------
T.update({
    "Главная": ("Басты бет", "Home"),
    "Дипломный проект · 2026": ("Дипломдық жоба · 2026", "Diploma project · 2026"),
    '<span class="grad">Безопасная</span> аутентификация по QR-коду': (
        'QR-код арқылы <span class="grad">қауіпсіз</span> аутентификация',
        '<span class="grad">Secure</span> QR-code authentication'),
    "Система аутентификации, которая обеспечивает быстрый и безопасный вход по QR-коду: временные токены, WebSocket в реальном времени и защита от QRLjacking.": (
        "Пайдаланушылардың жүйеге QR-код арқылы жылдам әрі қауіпсіз кіруін қамтамасыз ететін аутентификация жүйесі: уақытша токендер, нақты уақыттағы WebSocket және QRLjacking-тен қорғау.",
        "An authentication system for fast and secure QR-code sign-in: short-lived tokens, real-time WebSocket and protection against QRLjacking."),
    "Смотреть демо": ("Демоны көру", "View the demo"),
    "О проекте": ("Жоба туралы", "About the project"),
    "Время жизни токена": ("Токеннің өмір сүру уақыты", "Token lifetime"),
    "Энтропия токена": ("Токен энтропиясы", "Token entropy"),
    "Балл безопасности": ("Қауіпсіздік бағасы", "Security score"),
    "Отсканируйте телефоном": ("Телефонмен сканерлеңіз", "Scan with your phone"),
    "Наведите камеру на этот код — откроется часть демо для телефона.": (
        "Камераны осы кодқа бағыттаңыз — демоның телефон бөлігі ашылады.",
        "Point your camera at this code to open the phone part of the demo."),
    "Цель проекта": ("Жобаның мақсаты", "Project goal"),
    "Вход без пароля — одним сканированием": ("Құпиясөзсіз кіру — бір сканерлеуде", "Password-free sign-in in one scan"),
    "Вместо ввода пароля на компьютере пользователь сканирует QR-код телефоном, на котором он уже вошёл, и подтверждает вход. Пароль не набирается на клавиатуре, поэтому кейлоггеры и подглядывание через плечо теряют смысл.": (
        "Пайдаланушы компьютерде құпиясөз терудің орнына, жүйеге бұрын кірген телефонымен QR-кодты сканерлейді және кіруді растайды. Құпиясөз пернетақтадан енгізілмейді, сондықтан keylogger мен «иық үстінен қарау» шабуылдарының мәні жойылады.",
        "Instead of typing a password on the computer, the user scans the QR code with a phone that is already signed in and confirms. The password is never typed, so keyloggers and shoulder-surfing become pointless."),
    "Каждый QR — это временный токен: действует всего 60 секунд, используется один раз, подписан HMAC и привязан к браузеру, который его создал.": (
        "Әр QR — 60 секундқа ғана жарамды, бір рет қолданылатын, HMAC қолтаңбасы бар және оны жасаған браузерге байланған уақытша токен.",
        "Every QR is a short-lived token: valid for only 60 seconds, single-use, HMAC-signed and bound to the browser that created it."),
    "Задачи": ("Міндеттері", "Objectives"),
    "Путь из пяти шагов": ("Бес қадамдық жол", "A five-step path"),
    "Проектирование": ("Жобалау", "Design"),
    "Сессия": ("Сессия", "Session"),
    "Оценка": ("Бағалау", "Assessment"),
    "Провести обзор технологии QR-кода и способов её применения в аутентификации.": (
        "QR-код технологиясы мен оны аутентификацияда қолдану тәсілдеріне шолу жасау.",
        "Review QR-code technology and the ways it is used for authentication."),
    "Спроектировать механизм генерации и сканирования QR-кода.": (
        "QR-кодты генерациялау және сканерлеу механизмін жобалау.",
        "Design the QR-code generation and scanning mechanism."),
    "Выбрать и внедрить метод безопасного управления сессией (временный токен).": (
        "Сессияны қауіпсіз басқару әдісін (уақытша токен) таңдау және енгізу.",
        "Choose and implement secure session management (a short-lived token)."),
    "Реализовать и протестировать прототип системы.": (
        "Жүйенің прототипін іске асыру және тестілеу.",
        "Build and test a prototype of the system."),
    "Оценить уровень безопасности разработанной системы.": (
        "Әзірленген жүйенің қауіпсіздік деңгейін бағалау.",
        "Assess the security level of the system."),
    "Архитектура": ("Архитектура", "Architecture"),
    "Три устройства, одна цепочка доверия": ("Үш құрылғы, бір сенім тізбегі", "Three devices, one chain of trust"),
    "Компьютер показывает QR, телефон сканирует и подтверждает его, а сервер проверяет каждый шаг и передаёт результат через WebSocket в реальном времени.": (
        "Компьютер QR көрсетеді, телефон оны сканерлеп растайды, ал сервер әр қадамды тексеріп, нәтижені WebSocket арқылы нақты уақытта жеткізеді.",
        "The computer shows the QR, the phone scans and confirms it, and the server checks every step and reports the result over WebSocket in real time."),
    "Полная схема": ("Толық схема", "Full diagram"),
    "Компьютер": ("Компьютер", "Computer"),
    "Сервер": ("Сервер", "Server"),
    "Телефон": ("Телефон", "Phone"),
    "QR-сессия": ("QR сессиясы", "QR session"),
    "только хэш": ("тек хэш", "hash only"),
    "обновляется каждые 30 с": ("30 с сайын жаңарады", "rotates every 30 s"),
    "Попробуйте сами": ("Өзіңіз байқап көріңіз", "Try it yourself"),
    "Откройте QR на компьютере и отсканируйте телефоном — через 5 секунд вы в кабинете.": (
        "Компьютерде QR ашыңыз да, телефонмен сканерлеңіз — 5 секундта кабинеттесіз.",
        "Open the QR on a computer and scan it with your phone: five seconds later you're in."),
})

# --- overview ------------------------------------------------------------------------
T.update({
    "01 · Обзор технологии": ("01 · Технологияға шолу", "01 · Technology overview"),
    "Что такое QR-код?": ("QR-код деген не?", "What is a QR code?"),
    "QR (Quick Response) — двумерный матричный код, изобретённый компанией Denso Wave в 1994 году. Он хранит до 7 089 цифр или 2 953 байт и читается даже при повреждении — благодаря кодам Рида–Соломона.": (
        "QR (Quick Response) — 1994 жылы Denso Wave компаниясы ойлап тапқан екі өлшемді матрицалық код. Ол 7 089 санға немесе 2 953 байтқа дейін деректі сақтай алады және бүлінген жағдайда да оқылады — Рид–Соломон кодтарының арқасында.",
        "QR (Quick Response) is a two-dimensional matrix code invented by Denso Wave in 1994. It holds up to 7,089 digits or 2,953 bytes and can be read even when damaged, thanks to Reed–Solomon codes."),
    "СКОРОСТЬ": ("ЖЫЛДАМДЫҚ", "SPEED"),
    "Время чтения камерой смартфона": ("Смартфон камерасымен оқу уақыты", "Read time with a phone camera"),
    "ЁМКОСТЬ": ("СЫЙЫМДЫЛЫҚ", "CAPACITY"),
    "байт": ("байт", "bytes"),
    "Версия 40, уровень L": ("40-нұсқа, L деңгейі", "Version 40, level L"),
    "УСТОЙЧИВОСТЬ": ("ТӨЗІМДІЛІК", "RESILIENCE"),
    "Восстановление на уровне H": ("H деңгейінде қалпына келтіру", "Recovery at level H"),
    "ВЕРСИИ": ("НҰСҚАЛАР", "VERSIONS"),
    "От 21×21 до 177×177 модулей": ("21×21-ден 177×177 модульге дейін", "From 21×21 to 177×177 modules"),
    "Структура": ("Құрылымы", "Structure"),
    "Анатомия QR-кода": ("QR-кодтың анатомиясы", "Anatomy of a QR code"),
    "Выберите элемент — он подсветится на коде.": ("Элементті таңдаңыз — ол кодта жарықтанады.", "Pick an element and it lights up on the code."),
    "Схема структуры QR-кода": ("QR-код құрылымының схемасы", "Diagram of the QR code structure"),
    "Поисковые узоры (finder patterns)": ("Іздеу үлгілері (finder patterns)", "Finder patterns"),
    "Квадраты 7×7 в трёх углах. Позволяют сканеру найти код и определить угол поворота.": (
        "Үш бұрыштағы 7×7 шаршылар. Сканерге кодтың орны мен бұрылу бұрышын анықтауға мүмкіндік береді.",
        "7×7 squares in three corners. They let the scanner find the code and its rotation."),
    "Линии синхронизации (timing)": ("Синхрондау сызықтары (timing)", "Timing patterns"),
    "Чередующиеся тёмные и светлые модули — задают координатную сетку.": (
        "Ақ-қара кезектесетін модульдер — тор координаттарын анықтайды.",
        "Alternating dark and light modules that define the coordinate grid."),
    "Выравнивающий узор (alignment)": ("Туралау үлгісі (alignment)", "Alignment pattern"),
    "Есть начиная с версии 2; помогает читать код на наклонной или изогнутой поверхности.": (
        "2-нұсқадан бастап болады; қисайған немесе майысқан бетте оқуды түзетеді.",
        "Present from version 2; helps read the code on a tilted or curved surface."),
    "Информация о формате": ("Формат ақпараты", "Format information"),
    "Уровень коррекции ошибок и шаблон маски (15 бит, записаны дважды).": (
        "Қате түзету деңгейі мен маска үлгісі (15 бит, екі рет қайталанады).",
        "Error-correction level and mask pattern (15 bits, stored twice)."),
    "Данные и коды коррекции": ("Деректер және түзету кодтары", "Data and error correction"),
    "Закодированный URL и байты коррекции Рида–Соломона.": ("Кодталған URL және Рид–Соломон түзету байттары.", "The encoded URL and Reed–Solomon correction bytes."),
    "Уровни коррекции ошибок": ("Қатені түзету деңгейлері", "Error-correction levels"),
    'В проекте используется уровень <b class="mono" style="color:var(--cyan)">M</b>: оптимальный баланс между надёжностью чтения с экрана и плотностью кода.': (
        'Жобада <b class="mono" style="color:var(--cyan)">M</b> деңгейі қолданылады: экраннан оқу үшін сенімділік пен код тығыздығы арасындағы оңтайлы баланс.',
        'The project uses level <b class="mono" style="color:var(--cyan)">M</b>: the best balance between reliable reading from a screen and code density.'),
    "Версии": ("Нұсқалар", "Versions"),
    "Размер = 4V + 17": ("Өлшем = 4V + 17", "Size = 4V + 17"),
    "Чем больше версия (V), тем больше модулей и данных. Наш URL длиной ~90 символов помещается в версии 5–6.": (
        "Нұсқа (V) неғұрлым үлкен болса, соғұрлым көп модуль және дерек. Біздің ~90 таңбалық URL 5–6 нұсқаға сыяды.",
        "The higher the version (V), the more modules and data. Our ~90-character URL fits in version 5–6."),
    "Применение в аутентификации": ("Аутентификацияда қолдану", "Use in authentication"),
    "Три способа входа по QR": ("QR арқылы кірудің үш тәсілі", "Three ways to sign in with QR"),
    "Передача сессии через доверенное устройство": ("Сессияны сенімді құрылғымен беру", "Handing over a session via a trusted device"),
    'Компьютер показывает QR, уже вошедший телефон его подтверждает (WhatsApp Web, Telegram Desktop). <b style="color:var(--cyan)">Используется в этом проекте.</b>': (
        'Компьютер QR көрсетеді, бұрын кірген телефон оны растайды (WhatsApp Web, Telegram Desktop). <b style="color:var(--cyan)">Осы жобада қолданылады.</b>',
        'The computer shows a QR and an already signed-in phone confirms it (WhatsApp Web, Telegram Desktop). <b style="color:var(--cyan)">Used in this project.</b>'),
    "Передача ключа TOTP": ("TOTP кілтін тарату", "Sharing a TOTP key"),
    "В QR передаётся URI otpauth:// — приложение-аутентификатор генерирует коды на 30 секунд.": (
        "QR ішінде otpauth:// URI беріледі — аутентификатор қосымшасы 30 секундтық кодтар жасайды.",
        "The QR carries an otpauth:// URI; an authenticator app then generates 30-second codes."),
    "Гибрид FIDO2 (passkey)": ("FIDO2 гибрид (passkey)", "FIDO2 hybrid (passkey)"),
    "QR лишь открывает канал CTAP 2.2 с проверкой близости по Bluetooth — полностью устойчив к фишингу.": (
        "QR тек Bluetooth арқылы жақындықты тексеретін CTAP 2.2 каналын ашады — фишингке толық төзімді.",
        "The QR only opens a CTAP 2.2 channel with a Bluetooth proximity check: fully phishing-resistant."),
    "Сравнение": ("Салыстыру", "Comparison"),
    "Методы аутентификации": ("Аутентификация әдістері", "Authentication methods"),
    "Удобство": ("Ыңғайлылық", "Convenience"),
    "Устойчивость к фишингу": ("Фишингке төзімділік", "Phishing resistance"),
    "Доп. устройство": ("Қосымша құрылғы", "Extra device"),
    "Стоимость внедрения": ("Енгізу құны", "Cost to deploy"),
    "Время входа": ("Кіру уақыты", "Sign-in time"),
    "наша система": ("біздің жүйе", "our system"),
    # comparison table data (core/views.py)
    "Нет": ("Жоқ", "No"),
    "Не нужно": ("Қажет емес", "Not needed"),
    "Очень низкая": ("Өте төмен", "Very low"),
    "8–15 с": ("8–15 с", "8–15 s"),
    "Телефон (SIM)": ("Телефон (SIM)", "Phone (SIM)"),
    "Оплата SMS": ("SMS үшін төлем", "SMS fees"),
    "20–40 с": ("20–40 с", "20–40 s"),
    "Аутентификатор": ("Аутентификатор", "Authenticator app"),
    "Низкая": ("Төмен", "Low"),
    "12–20 с": ("12–20 с", "12–20 s"),
    "Частично + контекст": ("Ішінара + контекст", "Partial + context"),
    "Смартфон": ("Смартфон", "Smartphone"),
    "4–7 с": ("4–7 с", "4–7 s"),
    "Полная": ("Толық", "Full"),
    "Ключ / биометрия": ("Кілт / биометрия", "Key / biometrics"),
    "Средняя": ("Орташа", "Medium"),
    "3–6 с": ("3–6 с", "3–6 s"),
})

# --- how it works --------------------------------------------------------------------
T.update({
    "02 · Как это работает": ("02 · Қалай жұмыс істейді", "02 · How it works"),
    "Шесть шагов: от экрана до кабинета": ("Алты қадам: экраннан кабинетке дейін", "Six steps: from the screen to your account"),
    "Прокручивайте вниз — схема рисуется шаг за шагом, а пакеты данных «летят» между устройствами.": (
        "Төмен айналдырыңыз — схема қадам-қадаммен сызылады, ал деректер пакеттері құрылғылар арасында «ұшады».",
        "Scroll down: the diagram draws itself step by step while data packets “fly” between the devices."),
    "ШАГ 01 / 06": ("ҚАДАМ 01 / 06", "STEP 01 / 06"),
    "ШАГ 02 / 06": ("ҚАДАМ 02 / 06", "STEP 02 / 06"),
    "ШАГ 03 / 06": ("ҚАДАМ 03 / 06", "STEP 03 / 06"),
    "ШАГ 04 / 06": ("ҚАДАМ 04 / 06", "STEP 04 / 06"),
    "ШАГ 05 / 06": ("ҚАДАМ 05 / 06", "STEP 05 / 06"),
    "ШАГ 06 / 06": ("ҚАДАМ 06 / 06", "STEP 06 / 06"),
    "Компьютер открывает страницу входа": ("Компьютер кіру бетін ашады", "The computer opens the sign-in page"),
    "Браузер открывает /login и запрашивает у сервера новую QR-сессию. Вместе с запросом отправляется fingerprint браузера.": (
        "Браузер /login бетін ашып, сервердан жаңа QR сессиясын сұрайды. Сұраумен бірге браузердің fingerprint-і жіберіледі.",
        "The browser opens /login and asks the server for a new QR session, sending its browser fingerprint along."),
    "Сервер создаёт временный токен": ("Сервер уақытша токен жасайды", "The server creates a short-lived token"),
    "Токен secrets.token_urlsafe(32), nonce и подпись HMAC. В базу записывается только хэш SHA-256. Браузер открывает канал WebSocket; QR обновляется каждые 30 с.": (
        "secrets.token_urlsafe(32) токені, nonce және HMAC қолтаңбасы. Дерекқорға тек SHA-256 хэш жазылады. Браузер WebSocket арнасын ашады; QR 30 с сайын жаңарады.",
        "A secrets.token_urlsafe(32) token, a nonce and an HMAC signature. Only the SHA-256 hash is stored. The browser opens a WebSocket; the QR rotates every 30 s."),
    "Телефон сканирует QR": ("Телефон QR-ды сканерлейді", "The phone scans the QR"),
    "Телефон, на котором уже выполнен вход, считывает код. Сервер проверяет подпись и срок и переводит статус в <b>scanned</b>.": (
        "Жүйеге бұрын кірген телефон кодты оқиды. Сервер қолтаңбаны, мерзімді тексеріп, күйді <b>scanned</b> етеді.",
        "A phone that is already signed in reads the code. The server checks the signature and expiry and sets the status to <b>scanned</b>."),
    "Компьютер узнаёт об этом мгновенно": ("Компьютер нақты уақытта біледі", "The computer knows instantly"),
    "Через WebSocket на компьютер приходит «Подтвердите на телефоне». Если WebSocket недоступен — long-polling.": (
        "WebSocket арқылы компьютерге «Телефонда растаңыз» хабары келеді. WebSocket қолжетімсіз болса — long-polling.",
        "Over WebSocket the computer gets “Confirm on your phone”. Without WebSocket it falls back to long-polling."),
    "Пользователь подтверждает": ("Пайдаланушы растайды", "The user confirms"),
    "На телефоне видны браузер, ОС, IP и время запроса (защита от QRLjacking). Кнопки «Подтвердить» или «Отклонить».": (
        "Телефонда сұрау жіберген браузер, ОЖ, IP және уақыт көрсетіледі (QRLjacking-тен қорғау). «Растау» немесе «Бас тарту».",
        "The phone shows the requesting browser, OS, IP and time (QRLjacking protection), with “Confirm” and “Reject”."),
    "Одноразовый код → сессия": ("Бір реттік код → сессия", "One-time code → session"),
    "Сервер выдаёт компьютеру одноразовый код на 30 секунд. Браузер обменивает его на Django-сессию, токен удаляется. Повторное использование невозможно.": (
        "Сервер компьютерге 30 секундтық бір реттік код береді. Браузер оны Django-сессияға айырбастайды, токен жойылады. Қайта қолдану мүмкін емес.",
        "The server gives the computer a one-time code valid for 30 seconds. The browser exchanges it for a Django session and the token is deleted. It can't be reused."),
    "Поток данных между компьютером, сервером и телефоном": ("Компьютер, сервер және телефон арасындағы деректер ағыны", "Data flow between the computer, server and phone"),
    "браузер · /login": ("браузер · /login", "browser · /login"),
    "вошедший пользователь": ("кірген пайдаланушы", "signed-in user"),
    "Конечный автомат": ("Күйлер машинасы", "State machine"),
    "Статусы сессии": ("Сессия күйлері", "Session statuses"),
    "Sequence-диаграмма": ("Sequence-диаграмма", "Sequence diagram"),
    "Порядок сообщений": ("Хабарламалар реті", "Message order"),
    "Sequence-диаграмма входа по QR": ("QR арқылы кірудің sequence-диаграммасы", "Sequence diagram of a QR sign-in"),
    "Посмотрите схему вживую": ("Схеманы тірі түрде көріңіз", "See the diagram in action"),
    "Перейти к демо": ("Демоға өту", "Go to the demo"),
    "Компьютер (браузер)": ("Компьютер (браузер)", "Computer (browser)"),
    "Сервер (Django + Channels)": ("Сервер (Django + Channels)", "Server (Django + Channels)"),
    "Телефон (вошедший)": ("Телефон (кірген)", "Phone (signed in)"),
    "WS /ws/qr/<sid>/ (привязан к сессии)": ("WS /ws/qr/<sid>/ (сессияға байланған)", "WS /ws/qr/<sid>/ (bound to the session)"),
    "камера: сканирование QR": ("камера: QR сканерлеу", "camera: scanning the QR"),
    "страница подтверждения: браузер, ОС, IP, время": ("растау беті: браузер, ОЖ, IP, уақыт", "confirmation page: browser, OS, IP, time"),
    "status = confirmed · одноразовый код": ("status = confirmed · бір реттік код", "status = confirmed · one-time code"),
})

# --- demo ------------------------------------------------------------------------------
T.update({
    "03 · Демо": ("03 · Демо", "03 · Demo"),
    "Работающий прототип": ("Жұмыс істейтін прототип", "A working prototype"),
    "Нужны два устройства: компьютер (или ноутбук) и телефон с камерой. Сайт работает с любого устройства и из любой сети.": (
        "Екі құрылғы керек: компьютер (немесе ноутбук) және камерасы бар телефон. Сайт кез келген құрылғыдан және кез келген желіден ашылады.",
        "You need two devices: a computer (or laptop) and a phone with a camera. The site works from any device and any network."),
    "УСТРОЙСТВО 1 · КОМПЬЮТЕР": ("1-ҚҰРЫЛҒЫ · КОМПЬЮТЕР", "DEVICE 1 · COMPUTER"),
    "Страница входа по QR": ("QR арқылы кіру беті", "QR sign-in page"),
    "QR-код обновляется каждые 30 секунд, статус показывается в реальном времени через WebSocket. После подтверждения вы автоматически попадаете в кабинет.": (
        "QR-код 30 секунд сайын жаңарады, күйі WebSocket арқылы нақты уақытта көрсетіледі. Расталғаннан кейін автоматты түрде кабинетке өтесіз.",
        "The QR code rotates every 30 seconds and its status is shown live over WebSocket. Once confirmed, you're taken to your account automatically."),
    "Откройте страницу входа": ("Кіру бетін ашыңыз", "Open the sign-in page"),
    "В браузере компьютера — /login.": ("Компьютер браузерінде /login.", "In the computer's browser: /login."),
    "Покажите QR телефону": ("QR-ды телефонға көрсетіңіз", "Show the QR to the phone"),
    "Отсканируйте, пока не закончился таймер.": ("Таймер біткенше сканерлеңіз.", "Scan it before the timer runs out."),
    "Открыть вход по QR": ("QR кіру бетін ашу", "Open QR sign-in"),
    "УСТРОЙСТВО 2 · ТЕЛЕФОН": ("2-ҚҰРЫЛҒЫ · ТЕЛЕФОН", "DEVICE 2 · PHONE"),
    "Сканер и подтверждение": ("Сканер және растау", "Scanner and confirmation"),
    "Отсканируйте этот код камерой телефона, чтобы открыть страницу сканера. Сначала войдите или зарегистрируйтесь на телефоне.": (
        "Осы кодты телефон камерасымен сканерлеп, сканер бетін ашыңыз. Алдымен телефонда аккаунтқа кіріңіз немесе тіркеліңіз.",
        "Scan this code with your phone camera to open the scanner page. Sign in or sign up on the phone first."),
    "Войдите на телефоне": ("Телефонда кіріңіз", "Sign in on the phone"),
    "По паролю или создав новый аккаунт.": ("Құпиясөзбен немесе жаңа аккаунт жасап.", "With a password or by creating a new account."),
    "Со страницы сканера или обычной камерой телефона.": ("Сканер бетінен немесе телефонның кәдімгі камерасымен.", "From the scanner page or with the phone's regular camera."),
    "Убедитесь, что браузер, ОС, IP и время — ваши.": ("Браузер, ОЖ, IP және уақыт сіздікі екеніне көз жеткізіңіз.", "Make sure the browser, OS, IP and time are yours."),
    "Открыть сканер": ("Сканерді ашу", "Open the scanner"),
})

# --- testing -----------------------------------------------------------------------------
T.update({
    "04 · Тестирование": ("04 · Тестілеу", "04 · Testing"),
    "Результаты в цифрах": ("Нәтижелер сандармен", "Results in numbers"),
    'Unit-, интеграционные и нагрузочные тесты (pytest-django), а также время полного цикла входа, измеренное командой <span class="mono">benchmark_qr</span>.': (
        'Unit, интеграциялық және жүктеме тесттері (pytest-django), сондай-ақ <span class="mono">benchmark_qr</span> командасымен өлшенген толық кіру циклінің уақыты.',
        'Unit, integration and load tests (pytest-django), plus the full sign-in cycle time measured with <span class="mono">benchmark_qr</span>.'),
    'Метрик пока нет. Чтобы загрузить данные: <span class="mono" style="color:var(--cyan)">python manage.py seed_metrics --benchmark</span>': (
        'Метрикалар әлі жоқ. Деректерді жүктеу үшін: <span class="mono" style="color:var(--cyan)">python manage.py seed_metrics --benchmark</span>',
        'No metrics yet. To load data: <span class="mono" style="color:var(--cyan)">python manage.py seed_metrics --benchmark</span>'),
    "Наборы тестов": ("Тест жиынтықтары", "Test suites"),
    "Все тесты пройдены": ("Барлық тесттер өтті", "All tests pass"),
    "{passed} / {total} {unit} успешно": ("{passed} / {total} {unit} сәтті", "{passed} / {total} {unit} passed"),
    "тестов": ("тест", "tests"),
    "РАСПРЕДЕЛЕНИЕ": ("ТАРАЛУ", "DISTRIBUTION"),
    "Время входа (от сканирования до кабинета)": ("Кіру уақыты (сканерлеуден кабинетке дейін)", "Sign-in time (from scan to account)"),
    "% входов": ("% кірулер", "% of sign-ins"),
    "ДИНАМИКА": ("ДИНАМИКА", "TREND"),
    "Среднее время входа за 14 дней": ("Орташа кіру уақыты, 14 күн", "Average sign-in time, 14 days"),
    "секунды": ("секунд", "seconds"),
    "НАГРУЗОЧНЫЙ ТЕСТ": ("ЖҮКТЕМЕ ТЕСТІ", "LOAD TEST"),
    "Задержка p95: create → scan → confirm → exchange": ("p95 кешігу: create → scan → confirm → exchange", "p95 latency: create → scan → confirm → exchange"),
    "измерено benchmark_qr": ("benchmark_qr өлшеді", "measured by benchmark_qr"),
    "данные seed": ("seed деректері", "seed data"),
    "Измерение: SQLite, один процесс, на уровне сервисного слоя. В production (PostgreSQL + Redis) задержка будет ниже.": (
        "Өлшеу: SQLite, бір процесс, сервистік қабат деңгейінде. Production (PostgreSQL + Redis) ортада кешігу төменірек болады.",
        "Measured on SQLite, one process, at the service layer. In production (PostgreSQL + Redis) latency will be lower."),
    "Живая статистика": ("Тірі статистика", "Live statistics"),
    "Реальные входы на этом сервере": ("Осы серверде нақты кірулер", "Real sign-ins on this server"),
    "Считается напрямую по QR-сессиям в базе — меняется каждый раз, когда кто-то пользуется демо.": (
        "Дерекқордағы QR сессияларынан тікелей есептеледі — демоны қолданған сайын өзгереді.",
        "Computed directly from QR sessions in the database: it changes every time someone uses the demo."),
    "Создано QR": ("QR жасалды", "QR codes created"),
    "Успешных входов": ("Сәтті кіру", "Successful sign-ins"),
    "Успешность после сканирования": ("Сканерленгеннен кейін сәттілік", "Success after scanning"),
    "Среднее время входа": ("Орташа кіру уақыты", "Average sign-in time"),
    "Отсканировано": ("Сканерленді", "Scanned"),
    "Истекло / заменено": ("Мерзімі өтті / ауыстырылды", "Expired / replaced"),
    "TTL / обновление": ("TTL / жаңарту", "TTL / refresh"),
    "Успешные входы": ("Сәтті кірулер", "Successful sign-ins"),
    "Пропускная способность": ("Өткізу қабілеті", "Throughput"),
    "входов/с": ("кіру/с", "sign-ins/s"),
    "Сервер p95": ("Сервер p95", "Server p95"),
    "Unit-тесты": ("Unit тесттер", "Unit tests"),
    "Интеграционные тесты": ("Интеграциялық тесттер", "Integration tests"),
    "Нагрузочные сценарии": ("Жүктеме сценарийлері", "Load scenarios"),
    "{count} сессий": ("{count} сессия", "{count} sessions"),
})

# --- security --------------------------------------------------------------------------
T.update({
    "05 · Оценка безопасности": ("05 · Қауіпсіздікті бағалау", "05 · Security assessment"),
    "Угрозы и защита": ("Қауіп-қатерлер және қорғаныс", "Threats and protection"),
    "/ 10 баллов": ("/ 10 балл", "/ 10 points"),
    "Итоговая оценка: высокая": ("Жалпы баға: жоғары", "Overall rating: high"),
    "Из семи основных угроз {protected} закрыты полностью, {partial} — частично: они зависят от внимательности пользователя (социальная инженерия). Оценка — среднее по 10-балльной шкале для каждой угрозы.": (
        "Жеті негізгі қауіптің {protected}-і толық жабылған, {partial}-і ішінара — олар пайдаланушының назарына тәуелді (әлеуметтік инженерия). Баға әр қауіп бойынша 10 балдық шкаланың орташа мәні.",
        "Of the seven main threats, {protected} are fully covered and {partial} partly: those depend on the user's attention (social engineering). The score is the average of a 10-point scale per threat."),
    "Защищено · {n}": ("Қорғалған · {n}", "Protected · {n}"),
    "Частично · {n}": ("Ішінара · {n}", "Partial · {n}"),
    "Не защищено · 0": ("Қорғалмаған · 0", "Unprotected · 0"),
    "Угроза": ("Қауіп", "Threat"),
    "Меры защиты": ("Қорғау шаралары", "Countermeasures"),
    "Защищено": ("Қорғалған", "Protected"),
    "Частично": ("Ішінара", "Partial"),
    "Реализованные механизмы": ("Іске асырылған механизмдер", "Implemented mechanisms"),
    "Уровни защиты": ("Қорғаныс қабаттары", "Layers of defence"),
    "В production: SECURE_SSL_REDIRECT, HSTS на 1 год, Secure cookie.": ("Production-да SECURE_SSL_REDIRECT, HSTS 1 жыл, Secure cookie.", "In production: SECURE_SSL_REDIRECT, 1-year HSTS, Secure cookies."),
    "Только хэши": ("Тек хэштер", "Hashes only"),
    "QR-токен и код обмена хранятся как хэши SHA-256 и удаляются после использования.": (
        "QR токені мен алмасу коды SHA-256 хэш түрінде сақталады және қолданылғаннан кейін өшіріледі.",
        "The QR token and exchange code are stored as SHA-256 hashes and wiped after use."),
    "Привязка к fingerprint": ("Fingerprint байланысы", "Fingerprint binding"),
    "Обмен возможен только из браузера, создавшего QR (сессия + fingerprint).": (
        "Алмасу тек QR жасаған браузерден (сессия + fingerprint) мүмкін.",
        "The exchange only works from the browser that created the QR (session + fingerprint)."),
    "Лимиты": ("Лимиттер", "Rate limits"),
    "Генерация QR 12/мин, подтверждение 10/мин, пароль 8/5 мин, сброс пароля 5/час — по IP или пользователю.": (
        "QR генерациясы 12/мин, растау 10/мин, құпиясөз 8/5 мин, құпиясөзді қалпына келтіру 5/сағ — IP немесе пайдаланушы бойынша.",
        "QR generation 12/min, confirmation 10/min, password 8/5 min, password reset 5/hour, per IP or user."),
    "Каждое действие — создание, сканирование, подтверждение, отказ, replay, лимит, смена пароля — пишется с IP и User-Agent.": (
        "Әр әрекет — жасау, сканерлеу, растау, бас тарту, replay, лимит, құпиясөзді өзгерту — IP және User-Agent-пен жазылады.",
        "Every action (create, scan, confirm, reject, replay, limit, password change) is logged with IP and User-Agent."),
    "CSP и запрет фреймов": ("CSP және фрейм тыйымы", "CSP and no framing"),
    # threats table data (core/views.py)
    "Злоумышленник даёт жертве отсканировать свой QR-код и крадёт её сессию.": (
        "Шабуылдаушы өз QR-кодын құрбанға сканерлетіп, оның сессиясын ұрлайды.",
        "An attacker gets the victim to scan the attacker's QR code and steals the session."),
    "На телефоне показываются браузер, ОС, IP и время запроса": (
        "Телефонда сұрау жіберген браузер, ОЖ, IP және уақыт көрсетіледі",
        "The phone shows the requesting browser, OS, IP and time"),
    "QR действует 60 с и меняется каждые 30 с": ("QR 60 с жарамды, 30 с сайын ауысады", "The QR lives 60 s and rotates every 30 s"),
    "Токен привязан к fingerprint браузера-инициатора": ("Токен бастамашы браузердің fingerprint-іне байланған", "The token is bound to the initiating browser's fingerprint"),
    "Replay-атака": ("Replay шабуылы", "Replay attack"),
    "Повторная отправка перехваченного токена или кода обмена.": ("Ұсталған токенді немесе алмасу кодын қайта жіберу.", "Re-sending an intercepted token or exchange code."),
    "Код обмена используется только один раз (атомарный UPDATE)": ("Алмасу коды бір рет қана қолданылады (атомарлы UPDATE)", "The exchange code works only once (atomic UPDATE)"),
    "После подтверждения хэш QR-токена удаляется": ("Расталғаннан кейін QR токен хэші өшіріледі", "The QR token hash is wiped after confirmation"),
    "Nonce + подпись HMAC": ("Nonce + HMAC қолтаңба", "Nonce + HMAC signature"),
    "Перехват токена": ("Токенді ұстап алу", "Token interception"),
    "Кража токена в сети или из базы данных.": ("Желіде немесе дерекқордан токенді ұрлау.", "Stealing the token on the network or from the database."),
    "Только HTTPS + HSTS (production)": ("Тек HTTPS + HSTS (production)", "HTTPS + HSTS only (production)"),
    "В базе хранится только хэш SHA-256": ("Дерекқорда тек SHA-256 хэш сақталады", "Only the SHA-256 hash is stored"),
    "Код обмена доставляется только сессии-инициатору через WebSocket": (
        "Алмасу коды тек бастамашы сессияға WebSocket арқылы жеткізіледі",
        "The exchange code is delivered only to the initiating session over WebSocket"),
    "Перебор токенов или паролей.": ("Токендерді немесе құпиясөзді іріктеу.", "Guessing tokens or passwords."),
    "256 бит энтропии (secrets.token_urlsafe(32))": ("256-биттік энтропия (secrets.token_urlsafe(32))", "256 bits of entropy (secrets.token_urlsafe(32))"),
    "Rate limiting на генерацию, сканирование, подтверждение и вход": (
        "Генерация, сканерлеу, растау және кіруге rate limiting",
        "Rate limiting on generation, scanning, confirmation and sign-in"),
    "Все неудачные попытки пишутся в журнал аудита": ("Барлық сәтсіз әрекеттер аудит журналына жазылады", "Every failed attempt is written to the audit log"),
    "Фишинг": ("Фишинг", "Phishing"),
    "Поддельный сайт показывает настоящий QR и обманывает пользователя.": (
        "Жалған сайт нағыз QR-ды көрсетіп, пайдаланушыны алдайды.",
        "A fake site shows the real QR and tricks the user."),
    "Сканер открывает только URL этого домена": ("Сканер тек осы доменнің URL-дарын ашады", "The scanner opens only this domain's URLs"),
    "На экране подтверждения виден домен и контекст запроса": ("Растау экранында домен мен сұрау контексті көрсетіледі", "The confirmation screen shows the domain and request context"),
    "Без подтверждения пользователем вход невозможен": ("Пайдаланушы растамайынша кіру болмайды", "No sign-in without the user's confirmation"),
    "Отправка запроса от имени пользователя с чужого сайта.": ("Бөтен сайттан пайдаланушы атынан сұрау жіберу.", "Sending a request on the user's behalf from another site."),
    "CSRF-токен во всех POST-запросах": ("Барлық POST сұрауларда CSRF токен", "A CSRF token on every POST request"),
    "Нет GET-эндпоинтов, меняющих состояние (кроме сканирования, которое требует входа)": (
        "Күйді өзгертетін GET эндпоинттер жоқ (сканерлеуден басқа, ол логин талап етеді)",
        "No state-changing GET endpoints (except scanning, which requires sign-in)"),
    "Злоумышленник подсовывает заранее известный идентификатор сессии.": (
        "Шабуылдаушы алдын ала белгілі сессия идентификаторын тықпалайды.",
        "An attacker plants a session identifier they already know."),
    "После входа ключ сессии меняется (cycle_key)": ("Кіргеннен кейін сессия кілті ауыстырылады (cycle_key)", "The session key rotates after sign-in (cycle_key)"),
    "Любую сессию можно завершить на странице «Активные сессии»": (
        "«Белсенді сессиялар» бетінен кез келген сессияны аяқтауға болады",
        "Any session can be ended on the “Active sessions” page"),
})
