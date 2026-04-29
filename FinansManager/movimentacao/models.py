# criar a estrutura do banco de dados
from movimentacao import database, login_manager
from datetime import datetime
from flask_login import UserMixin


@login_manager.user_loader
def load_usuario(id_usuario):
    return Usuario.query.get(int(id_usuario))


class Usuario(database.Model, UserMixin):
    id = database.Column(database.Integer, primary_key=True)
    username = database.Column(database.String, nullable=False)
    email = database.Column(database.String, nullable=False, unique=True)
    senha = database.Column(database.String, nullable=False)
    nivel = database.Column(database.String, nullable=False)


class Cliente(database.Model):
    id_vendedor = database.Column(database.Integer, database.ForeignKey('cliente.id'), nullable=False)
    id = database.Column(database.Integer, primary_key=True)
    nome = database.Column(database.String, nullable=False)
    cpf = database.Column(database.String, nullable=False)
    saldo = database.Column(database.String, nullable=True)
    telefone = database.Column(database.String, nullable=False)
    email = database.Column(database.String, nullable=False)
    data_nascimento = database.Column(database.String, nullable=False)
    endereco = database.Column(database.String, nullable=False)
    usuario_insert = database.Column(database.String, nullable=False)

class Movimentacao(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    id_cliente = database.Column(database.Integer, database.ForeignKey('cliente.id'), nullable=False)
    data = database.Column(database.String, nullable=False)
    valor_pago = database.Column(database.String)
    valor_emprestado = database.Column(database.String)
    atrasado = database.Column(database.String)
    obs = database.Column(database.String)
    ultimo_saldo = database.Column(database.String)
    usuario_insert = database.Column(database.String, nullable=False)
    id_contrato = database.Column(database.Integer, database.ForeignKey('contrato.id'), nullable=False)

class Contrato(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    id_cliente = database.Column(database.Integer, database.ForeignKey('cliente.id'), nullable=False)
    id_contrato = database.Column(database.Integer, database.ForeignKey('pagamento.id'), nullable=False)
    data = database.Column(database.String, nullable=False)
    valor = database.Column(database.String)
    status = database.Column(database.String)
    juros = database.Column(database.String)
    saldo = database.Column(database.String)
    frequencia = database.Column(database.String)
    pagamento = database.Column(database.String)
    parcelas = database.Column(database.String)
    ultimo_insert = database.Column(database.String)

class Pagamento(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    valor_juros = database.Column(database.String)
    valor = database.Column(database.String)
    juros = database.Column(database.String)
    parcelas = database.Column(database.String)
    result_parcelas = database.Column(database.String)
    porcentagem_comissao = database.Column(database.String)
    valor_comissao = database.Column(database.String)
