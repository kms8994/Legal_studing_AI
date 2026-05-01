from urllib.parse import quote


BASE_URL = "https://www.law.go.kr"


def build_law_go_kr_url(path: str) -> str:
    return BASE_URL + quote(path, safe="/(),")


def case_url(case_number: str, decision_date: str | None = None) -> str:
    if decision_date:
        return build_law_go_kr_url(f"/판례/({case_number},{decision_date})")
    return build_law_go_kr_url(f"/판례/({case_number})")


def case_title_url(title: str) -> str:
    return build_law_go_kr_url(f"/판례/{title}")


def statute_url(law_name: str, article: str | None = None) -> str:
    if article:
        return build_law_go_kr_url(f"/법령/{law_name}/{article}")
    return build_law_go_kr_url(f"/법령/{law_name}")


def legal_term_url(term: str) -> str:
    return build_law_go_kr_url(f"/용어/{term}")
