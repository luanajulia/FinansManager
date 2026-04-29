# criar os formularios do nosso site
from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, PasswordField, SubmitField, FileField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, NumberRange
from movimentacao.models import Usuario


class FormLogin(FlaskForm):
    email = StringField("E-mail", validators=[DataRequired(), Email()])
    senha = PasswordField("Senha", validators=[DataRequired()])
    botao_confirmacao = SubmitField("Fazer Login")


class FormCriarConta(FlaskForm):
    email = StringField("E-mail", validators=[DataRequired(), Email()])
    username = StringField("Nome de usuário", validators=[DataRequired()])
    nivel = SelectField('Nivel de acesso', choices=[
                  ('Administrador', 'Administrador'),
                  ('Vendedor', 'Vendedor')])
    senha = PasswordField("Senha", validators=[DataRequired(), Length(6, 20)])
    confirmacao_senha = PasswordField("Confirmação de Senha", validators=[DataRequired(), EqualTo("senha")])
    botao_confirmacao = SubmitField("Criar Conta")

    def validate_email(self, email):
        usuario = Usuario.query.filter_by(email=email.data).first()
        if usuario:
            return ValidationError("E-mail já cadastrado, faça login para continuar")


class FormCliente(FlaskForm):
    nome = StringField("Nome Cliente", validators=[DataRequired()])
    cpf = StringField("CPF", validators=[DataRequired()])
    telefone = StringField("Telefone:", validators=[DataRequired()])
    email = StringField("Email:", validators=[DataRequired()])
    endereco = StringField("Endereço", validators=[DataRequired()])
    data_nascimento = StringField("Data Nascimento:", validators=[DataRequired()])
    botao_confirmacao = SubmitField("Cadastrar")

class FormContrato(FlaskForm):
    valor = StringField("Valor:", validators=[DataRequired()])
    juros = StringField("Juros:", validators=[DataRequired()])
    frequencia = StringField("Frequência:", validators=[DataRequired()])
    data = StringField("Data Início Contrato:", validators=[DataRequired()])
    botao_confirmacao = SubmitField("Criar Contrato")

class FormPagamentos(FlaskForm):
    valorTotal = IntegerField("Valor Total:", validators=[DataRequired(), NumberRange(min=1)])
    porcentagem = IntegerField("Taxa de Juros:", validators=[DataRequired(), NumberRange(min=0, max=100)])
    divisor = IntegerField("Número de Parcelas:", validators=[DataRequired(), NumberRange(min=1)])
    porcentagemComissao = IntegerField("Porcentagem Comissão:", validators=[DataRequired(), NumberRange(min=0, max=100)])
    botao_confirmacao = SubmitField("Criar Condicao de Pagamento")