VECTOR + site2.0 (inclusive_frontend/site2)

Запуск (Windows):
1) Открой PowerShell в корне проекта и выполни:
   .\run_all_windows.bat

Это откроет 2 окна:
- Flask: http://127.0.0.1:5000
- Next : http://127.0.0.1:3000

Если Next.js на другом порту/URL — задай переменную окружения:
INCLUSIVE_URL=http://127.0.0.1:3000

В интерфейсе студента:
- /student/inclusive — встроенная страница (Flask)
- кнопка "Открыть новый интерфейс (site2.0)" — откроет Next.js

node_modules и .next удалены из архива (чтобы zip был лёгким). npm install выполнится при первом запуске.
