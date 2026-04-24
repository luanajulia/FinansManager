from movimentacao import database, app
from movimentacao.models import Cliente, Usuario, Movimentacao, Contrato, Pagamento

with app.app_context():
    database.create_all()