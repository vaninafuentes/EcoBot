from app.router import route_question

def test_inflacion():
    r = route_question("¿Qué es la inflación?")
    assert "inflación" in r.lower() or "inflacion" in r.lower()

def test_elasticidad():
    r = route_question("Explicame la elasticidad precio de la demanda")
    assert "elasticidad" in r.lower()

def test_no_economia():
    r = route_question("¿Cómo programo en Python?")
    assert "únicamente preguntas de economía" in r.lower()
