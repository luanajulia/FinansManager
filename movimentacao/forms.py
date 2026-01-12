# criar os formularios do nosso site
from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, PasswordField, SubmitField, FileField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
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
    data_nascimento = StringField("Data Nascimento:", validators=[DataRequired()])
    botao_confirmacao = SubmitField("Cadastrar")