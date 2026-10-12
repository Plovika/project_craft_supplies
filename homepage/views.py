"""Главная страница, общий каркас страниц и страница 404."""

from django.http import HttpRequest, HttpResponse

BOOTSTRAP = (
    "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3"
    "/dist/css/bootstrap.min.css"
)


def page(title: str, content: str) -> str:
    """Собрать HTML-документ: каркас, Bootstrap, навигация и content."""
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title}</title>
    <link rel="stylesheet" href="{BOOTSTRAP}">
</head>
<body class="bg-light">
    <nav class="navbar navbar-expand bg-white border-bottom mb-4">
        <div class="container">
            <a class="navbar-brand" href="/"> Мастерская</a>
            <div class="navbar-nav">
                <a class="nav-link" href="/">Главная</a>
                <a class="nav-link" href="/materials/">Материалы</a>
                <a class="nav-link" href="/operations/">Операции</a>
            </div>
        </div>
    </nav>
    <main class="container pb-5">{content}</main>
</body>
</html>"""


def index(request: HttpRequest) -> HttpResponse:
    """Главная страница: описание сервиса и переходы в разделы."""
    content = """
    <h1 class="display-5">Учёт материалов для творчества</h1>
    <p class="lead">
        Краски, кисти, пряжа и бисер под контролем:
        что есть, сколько осталось и кто что брал.
    </p>
    <a href="/materials/" class="btn btn-primary me-2">Материалы</a>
    <a href="/operations/" class="btn btn-secondary">История операций</a>
    """
    return HttpResponse(page("Учёт материалов", content))


def page_not_found(request: HttpRequest, exception: Exception) -> HttpResponse:
    """Собственная страница 404 для адресов без маршрута."""
    content = """
    <h1 class="text-danger">404 – страница не найдена</h1>
    <p>Проверьте адрес или вернитесь на главную.</p>
    <a href="/" class="btn btn-primary">На главную</a>
    """
    return HttpResponse(
        page("404 – страница не найдена", content),
        status=404,
    )
