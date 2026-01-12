from movimentacao import database, app
from movimentacao.models import Cliente, Usuario, Movimentacao

with app.app_context():
    database.create_all()