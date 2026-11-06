# Accounts: sign-up, sign-in, cabinet, passwords, audit events.  Russian -> (Kazakh, English)
T = {
    # e-mails
    "Здравствуйте, {name}!": ("Сәлеметсіз бе, {name}!", "Hello, {name}!"),
    "Кто-то (возможно, вы) запросил сброс пароля для аккаунта {username}.": (
        "Біреу (мүмкін, сіз) {username} аккаунтының құпиясөзін қалпына келтіруді сұрады.",
        "Someone (possibly you) asked to reset the password of the account {username}."),
    "Ссылка одноразовая и действует {minutes} минут.": (
        "Сілтеме бір рет қолданылады және {minutes} минут жарамды.",
        "The link works once and is valid for {minutes} minutes."),
    "Если вы не запрашивали сброс, просто проигнорируйте это письмо — пароль не изменится.": (
        "Егер сіз сұрамасаңыз, бұл хатты елемеңіз — құпиясөз өзгермейді.",
        "If you didn't ask for this, just ignore this e-mail: your password won't change."),
    "Задать новый пароль": ("Жаңа құпиясөз орнату", "Set a new password"),
    "Пароль изменён": ("Құпиясөз өзгертілді", "Password changed"),
    "Пароль аккаунта {username} только что был изменён.": (
        "{username} аккаунтының құпиясөзі жаңа ғана өзгертілді.",
        "The password of the account {username} was just changed."),
    "Если это были не вы, сразу сбросьте пароль и завершите чужие сессии в личном кабинете.": (
        "Егер бұл сіз болмасаңыз, құпиясөзді бірден қалпына келтіріп, жеке кабинетте бөтен сессияларды аяқтаңыз.",
        "If this wasn't you, reset your password right away and end unknown sessions in your account."),
    # forms
    "Электронная почта": ("Электрондық пошта", "E-mail"),
    "Латинские буквы, цифры и символы @/./+/-/_.": (
        "Латын әріптері, сандар және @/./+/-/_ таңбалары.",
        "Latin letters, digits and @/./+/-/_ only."),
    "Минимум 8 символов, не только цифры.": (
        "Кемінде 8 таңба, тек сандардан тұрмауы керек.",
        "At least 8 characters, not digits only."),
    "Повторите пароль": ("Құпиясөзді қайталаңыз", "Repeat the password"),
    "Этот логин зарезервирован системой. Выберите другой.": (
        "Бұл логин жүйеге арналған. Басқа логин таңдаңыз.",
        "This username is reserved by the system. Please choose another."),
    "Эта почта уже зарегистрирована. Войдите или укажите другую.": (
        "Бұл пошта бұрын тіркелген. Кіріңіз немесе басқа пошта енгізіңіз.",
        "This e-mail is already registered. Sign in or use another one."),
    "Неверный логин или пароль. Проверьте и попробуйте снова.": (
        "Логин немесе құпиясөз қате. Қайта тексеріп көріңіз.",
        "Wrong username or password. Please check and try again."),
    "Этот аккаунт заблокирован.": ("Бұл аккаунт бұғатталған.", "This account is blocked."),
    "Текущий пароль": ("Ағымдағы құпиясөз", "Current password"),
    "Новый пароль": ("Жаңа құпиясөз", "New password"),
    "Минимум 8 символов, не только цифры и не похож на логин.": (
        "Кемінде 8 таңба, тек сандар емес және логинге ұқсамауы керек.",
        "At least 8 characters, not digits only and not similar to the username."),
    "Повторите новый пароль": ("Жаңа құпиясөзді қайталаңыз", "Repeat the new password"),
    "Выйти на всех других устройствах": ("Барлық басқа құрылғылардан шығу", "Sign out on all other devices"),
    "Текущий пароль введён неверно.": ("Ағымдағы құпиясөз қате енгізілді.", "The current password is incorrect."),
    "Пароли не совпадают.": ("Құпиясөздер сәйкес келмейді.", "The passwords don't match."),
    # login methods and audit events
    "QR-код": ("QR-код", "QR code"),
    "QR создан": ("QR жасалды", "QR created"),
    "QR отсканирован": ("QR сканерленді", "QR scanned"),
    "QR подтверждён": ("QR расталды", "QR confirmed"),
    "QR отклонён": ("QR бас тартылды", "QR rejected"),
    "QR истёк": ("QR мерзімі өтті", "QR expired"),
    "Недействительный QR": ("Жарамсыз QR", "Invalid QR"),
    "Повтор заблокирован": ("Қайталау бұғатталды", "Replay blocked"),
    "Fingerprint не совпал": ("Fingerprint сәйкес емес", "Fingerprint mismatch"),
    "Успешный вход": ("Сәтті кіру", "Successful sign-in"),
    "Неудачный вход": ("Сәтсіз кіру", "Failed sign-in"),
    "Выход": ("Шығу", "Sign-out"),
    "Превышен лимит": ("Лимит асты", "Rate limited"),
    "Сессия завершена": ("Сессия аяқталды", "Session ended"),
    "Регистрация": ("Тіркелу", "Sign up"),
    "Действие администратора": ("Әкімші әрекеті", "Admin action"),
    "Запрошен сброс пароля": ("Құпиясөзді қалпына келтіру сұралды", "Password reset requested"),
    "Пароль сброшен": ("Құпиясөз қалпына келтірілді", "Password reset"),
    # view messages
    "Аккаунт создан. Теперь вы можете сканировать QR этим аккаунтом на телефоне.": (
        "Аккаунт жасалды. Енді телефонда осы аккаунтпен QR сканерлей аласыз.",
        "Account created. You can now scan QR codes with this account on your phone."),
    "Вы вышли из системы.": ("Сіз жүйеден шықтыңыз.", "You have signed out."),
    "Текущая сессия завершена.": ("Ағымдағы сессия аяқталды.", "This session has ended."),
    "Сессия завершена: {device}.": ("Сессия аяқталды: {device}.", "Session ended: {device}."),
    "Завершено других сессий: {count}.": ("Басқа сессиялар аяқталды: {count}.", "Other sessions ended: {count}."),
    "Пароль изменён. Завершено других сессий: {count}.": (
        "Құпиясөз өзгертілді. Басқа сессиялар аяқталды: {count}.",
        "Password changed. Other sessions ended: {count}."),
    "Пароль обновлён. Войдите с новым паролем.": (
        "Құпиясөз жаңартылды. Жаңа құпиясөзбен кіріңіз.",
        "Password updated. Sign in with your new password."),
    # cabinet
    "06 · Личный кабинет": ("06 · Жеке кабинет", "06 · My account"),
    "Здравствуйте, {name}": ("Сәлем, {name}", "Hello, {name}"),
    "Сменить пароль": ("Құпиясөзді өзгерту", "Change password"),
    "Сканировать QR": ("QR сканерлеу", "Scan a QR"),
    "Всего входов": ("Барлық кіру", "Total sign-ins"),
    "Через QR": ("QR арқылы", "With QR"),
    "Обновляется в реальном времени": ("Нақты уақытта жаңарады", "Updates in real time"),
    "Завершить все остальные": ("Басқаларының бәрін аяқтау", "End all others"),
    "это устройство": ("осы құрылғы", "this device"),
    "{ip} · вход {when} · активность {ago}": (
        "{ip} · кірді {when} · белсенді {ago} бұрын",
        "{ip} · signed in {when} · active {ago} ago"),
    "Завершить сессию {device}": ("{device} сессиясын аяқтау", "End session {device}"),
    "Завершить": ("Аяқтау", "End"),
    "Активных сессий нет.": ("Белсенді сессиялар жоқ.", "No active sessions."),
    "Журнал входов": ("Кіру журналы", "Sign-in log"),
    "последние 30 событий": ("соңғы 30 оқиға", "last 30 events"),
    "Журнал пуст.": ("Журнал бос.", "The log is empty."),
    # login / register
    "Вход": ("Кіру", "Sign in"),
    "С возвращением": ("Қош келдіңіз", "Welcome back"),
    "<b>Ваша сессия завершена с другого устройства.</b> Чтобы продолжить, войдите снова.": (
        "<b>Сессияңыз басқа құрылғыдан аяқталды.</b> Жалғастыру үшін қайта кіріңіз.",
        "<b>Your session was ended from another device.</b> Sign in again to continue."),
    "<b>QR-код распознан.</b> Чтобы подтвердить вход на компьютере, сначала войдите в аккаунт на телефоне — код на компьютере вас ждёт.": (
        "<b>QR-код танылды.</b> Компьютерге кіруді растау үшін алдымен телефонда аккаунтқа кіріңіз — компьютердегі код сізді күтіп тұр.",
        "<b>QR code recognised.</b> To confirm the sign-in on the computer, first sign in on your phone: the code on the computer is waiting for you."),
    "Войдите один раз на телефоне — дальше на компьютер вы будете входить только по QR.": (
        "Телефонда бір рет кіріңіз — кейін компьютерге тек QR арқылы кіресіз.",
        "Sign in once on your phone; after that you sign in on computers with QR only."),
    "Вы уже вошли как <b>{username}</b>. Можно войти в другой аккаунт.": (
        "Сіз қазір <b>{username}</b> ретінде кірдіңіз. Басқа аккаунтпен кіруге болады.",
        "You're already signed in as <b>{username}</b>. You can sign in to another account."),
    "В кабинет": ("Кабинетке өту", "Go to my account"),
    "Забыли пароль?": ("Құпиясөзді ұмыттыңыз ба?", "Forgot your password?"),
    "ИЛИ": ("НЕМЕСЕ", "OR"),
    "Войти по QR-коду": ("QR-код арқылы кіру", "Sign in with a QR code"),
    "Нет аккаунта?": ("Аккаунт жоқ па?", "No account yet?"),
    "Новый аккаунт": ("Жаңа аккаунт", "New account"),
    "Аккаунт нужен, чтобы подтверждать QR-коды на телефоне.": (
        "Аккаунт телефонда QR-кодтарды растау үшін керек.",
        "You need an account to confirm QR codes on your phone."),
    "Вы уже вошли как <b>{username}</b>. Если создать новый аккаунт, вы переключитесь на него.": (
        "Сіз қазір <b>{username}</b> ретінде кірдіңіз. Жаңа аккаунт жасасаңыз, соған ауысасыз.",
        "You're already signed in as <b>{username}</b>. Creating a new account switches you to it."),
    "Создать аккаунт": ("Аккаунт жасау", "Create account"),
    "Уже есть аккаунт?": ("Аккаунтыңыз бар ма?", "Already have an account?"),
    # password pages
    "Смена пароля": ("Құпиясөзді өзгерту", "Change password"),
    "Введите текущий пароль и придумайте новый. На этом устройстве вы останетесь в системе.": (
        "Ағымдағы құпиясөзді енгізіп, жаңасын ойлап табыңыз. Осы құрылғыда жүйеде қаласыз.",
        "Enter your current password and choose a new one. You stay signed in on this device."),
    "Рекомендуется, если пароль мог узнать кто-то другой.": (
        "Құпиясөзді басқа біреу білуі мүмкін болса, ұсынылады.",
        "Recommended if someone else might know your password."),
    "Сохранить новый пароль": ("Жаңа құпиясөзді сақтау", "Save new password"),
    "Отмена": ("Болдырмау", "Cancel"),
    "Не помню текущий пароль": ("Ағымдағы құпиясөзді ұмыттым", "I don't remember my current password"),
    "Сброс пароля": ("Құпиясөзді қалпына келтіру", "Reset password"),
    "Забыли пароль": ("Құпиясөзді ұмыттыңыз", "Forgot password"),
    "Укажите почту, с которой вы регистрировались. Мы пришлём одноразовую ссылку для нового пароля.": (
        "Тіркелген поштаңызды көрсетіңіз. Жаңа құпиясөз үшін бір реттік сілтеме жібереміз.",
        "Enter the e-mail you signed up with. We'll send a one-time link to set a new password."),
    "Отправка писем на этом сервере пока не настроена. Если письмо не придёт, обратитесь к администратору — он может создать для вас ссылку для сброса.": (
        "Бұл серверде хат жіберу әлі бапталмаған. Хат келмесе, әкімшіге хабарласыңыз — ол сізге қалпына келтіру сілтемесін жасай алады.",
        "Sending e-mail isn't set up on this server yet. If no e-mail arrives, contact the administrator: they can create a reset link for you."),
    "Отправить ссылку": ("Сілтеме жіберу", "Send the link"),
    "Вспомнили пароль?": ("Құпиясөз есіңізге түсті ме?", "Remembered your password?"),
    "Аккаунт <b>{username}</b>. После сохранения вы выйдете на всех устройствах и войдёте уже с новым паролем.": (
        "Аккаунт <b>{username}</b>. Сақтағаннан кейін барлық құрылғылардан шығасыз да, жаңа құпиясөзбен кіресіз.",
        "Account <b>{username}</b>. After saving you'll be signed out everywhere and sign in with the new password."),
    "Сохранить пароль": ("Құпиясөзді сақтау", "Save password"),
    "Ссылка недействительна": ("Сілтеме жарамсыз", "Invalid link"),
    "Ссылка уже использована, устарела или повреждена. Запросите новую.": (
        "Сілтеме бұрын қолданылған, ескірген немесе бүлінген. Жаңасын сұраңыз.",
        "The link was already used, has expired or is broken. Please request a new one."),
    "Запросить новую ссылку": ("Жаңа сілтеме сұрау", "Request a new link"),
    "Ко входу": ("Кіру бетіне", "Back to sign in"),
    "Проверьте почту": ("Поштаңызды тексеріңіз", "Check your e-mail"),
    "Если аккаунт с этой почтой существует, мы отправили на неё ссылку для сброса пароля. Ссылка одноразовая и действует {minutes} минут.": (
        "Егер осы поштамен аккаунт бар болса, оған құпиясөзді қалпына келтіру сілтемесін жібердік. Сілтеме бір рет қолданылады және {minutes} минут жарамды.",
        "If an account with this e-mail exists, we've sent it a password reset link. The link works once and is valid for {minutes} minutes."),
    "Нет письма? Проверьте папку «Спам» или запросите ссылку ещё раз через несколько минут.": (
        "Хат жоқ па? «Спам» қалтасын тексеріңіз немесе бірнеше минуттан кейін сілтемені қайта сұраңыз.",
        "No e-mail? Check your spam folder or request the link again in a few minutes."),
    "Отправить ещё раз": ("Қайта жіберу", "Send again"),
}
