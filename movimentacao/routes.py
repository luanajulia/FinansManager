# criar as rotas do nosso site (os links)
from flask import flash, render_template, request, url_for, redirect, session
from movimentacao import app, database, bcrypt
from movimentacao.models import Cliente, Usuario, Movimentacao, database
from flask_login import login_required, login_user, logout_user, current_user
from movimentacao.forms import FormLogin, FormCriarConta, FormCliente
from werkzeug.utils import secure_filename
import os
import sqlite3 as sql
import email_validator
import sqlite3
from datetime import datetime, date, timedelta, time
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

engine = create_engine('sqlite:///meubanco.db', poolclass=NullPool)

conn = sqlite3.connect(r"C:\inetpub\wwwroot\projetinho\instance\comunidade.db", check_same_thread=False)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()


@app.route("/", methods=["GET", "POST"])
def homepage():
    form_login = FormLogin()
    if form_login.validate_on_submit():
        usuario = Usuario.query.filter_by(email=form_login.email.data).first()
        if usuario and bcrypt.check_password_hash(usuario.senha, form_login.senha.data):
            login_user(usuario)
            return redirect(url_for("clientes"))
    return render_template("homepage.html", form=form_login)

@app.route("/criarconta", methods=["GET", "POST"])
def criar_conta():
    form_criarconta = FormCriarConta()
    if form_criarconta.validate_on_submit():
        senha = bcrypt.generate_password_hash(form_criarconta.senha.data)
        usuario = Usuario(username=form_criarconta.username.data,
                          nivel=form_criarconta.nivel.data,
                          senha=senha, 
                          email=form_criarconta.email.data)
        database.session.add(usuario)
        database.session.commit()
        login_user(usuario, remember=True)
        return redirect(url_for("clientes"))
    return render_template("criarconta.html", form=form_criarconta)

@app.route("/criarcliente", methods=["GET", "POST"])
def criarcliente():
    form_criarcliente = FormCliente()
    user = Usuario.query.get(int(current_user.id))
    usuarios = Usuario.query.filter(Usuario.nivel == "Vendedor").all()
    if form_criarcliente.validate_on_submit():
        clientes = Cliente(nome=form_criarcliente.nome.data,
                           saldo="0",
                          cpf=form_criarcliente.cpf.data,
                          telefone=form_criarcliente.telefone.data,
                          email=form_criarcliente.email.data,
                          data_nascimento=form_criarcliente.data_nascimento.data, 
                          usuario_insert=current_user.id,
                          id_vendedor=request.form.get("vendedor"))
        database.session.add(clientes)
        database.session.commit()
        return redirect(url_for("clientes"))
    return render_template("criarcliente.html", form=form_criarcliente, usuarios=usuarios, user=user)

@app.route("/criar_vendedor", methods=["GET", "POST"])
def criar_vendedor():
    form_criarconta = FormCriarConta()
    vend="vend"
    user = Usuario.query.get(int(current_user.id))
    if form_criarconta.validate_on_submit():
        senha = bcrypt.generate_password_hash(form_criarconta.senha.data)
        usuario = Usuario(username=form_criarconta.username.data,
                          nivel=form_criarconta.nivel.data,
                          senha=senha, 
                          email=form_criarconta.email.data)
        database.session.add(usuario)
        database.session.commit()
        return redirect(url_for("vendedores"))
    return render_template("criar_vendedor.html", form=form_criarconta, vend=vend, user=user)

@app.route("/movimentacao",methods=['GET', "POST"])
@login_required
def movimentacao():
    movi="movi"
    user = Usuario.query.get(int(current_user.id))
    clientes = Cliente.query.order_by(Cliente.nome).all()
    datas = cursor.execute("select DISTINCT SUBSTR(data, 0, 11) as data_movi FROM movimentacao ").fetchall()
    movimentacoes = database.session.query(Movimentacao, Cliente, Usuario).join(Cliente, Movimentacao.id_cliente == Cliente.id).join(Usuario, Movimentacao.usuario_insert == Usuario.id).all()
    total_saida = database.session.query(database.func.sum(Movimentacao.valor_emprestado)).first()
    total_recebido = database.session.query(database.func.sum(Movimentacao.valor_pago)).first()
    total_saldo = database.session.query(database.func.sum(Cliente.saldo)).first()
    return render_template("movimentacoes.html", movimentacoes_completas=movimentacoes, datas=datas, movi=movi, user=user, total_saida=total_saida,total_recebido=total_recebido, total_saldo=total_saldo, clientes=clientes)

@app.route("/movimentacao_pesquisa",methods=['GET', "POST"])
@login_required
def movimentacao_pesquisa():
    if request.method == 'POST':
        client = request.form.get('cliente')
        dat = request.form.get('data')
        session['client'] = client 
        session['dat'] = dat
    client = session['client']
    dat = session['dat']
    movi="movi"
    user = Usuario.query.get(int(current_user.id))
    clientes = Cliente.query.order_by(Cliente.nome).all()
    datas = cursor.execute("select DISTINCT SUBSTR(data, 0, 11) as data_movi FROM movimentacao ").fetchall()
    if client != "":
        cliente=Cliente.query.get(int(client))
        movimentacoes = cursor.execute("SELECT *, c.saldo, u.username FROM  Movimentacao LEFT JOIN Cliente as c ON  c.id = Movimentacao.id_cliente LEFT JOIN Usuario as u ON  u.id = Movimentacao.usuario_insert where  id_cliente = '"+client+"'").fetchall()
        total_saida = cursor.execute("select sum(valor_emprestado) as emprestado FROM movimentacao where  id_cliente = '"+client+"'").fetchall()
        total_recebido = cursor.execute("select sum(valor_pago) as pago FROM movimentacao where  id_cliente = '"+client+"'").fetchall()
        total_saldo = database.session.query(database.func.sum(Cliente.saldo)).filter(Cliente.id == client).first()
        return render_template("movimentacoes_pesquisa.html", movimentacoes_completas=movimentacoes, dat=dat, datas=datas, movi=movi, user=user, total_saida=total_saida,total_recebido=total_recebido, clientes=clientes, client=client, cliente=cliente)
    if dat != "":
        movimentacoes = cursor.execute("SELECT *, c.saldo, u.username FROM  Movimentacao LEFT JOIN Cliente as c ON  c.id = Movimentacao.id_cliente LEFT JOIN Usuario as u ON  u.id = Movimentacao.usuario_insert where SUBSTR(data, 0, 11) = '"+dat+"'").fetchall()
        total_saida = cursor.execute("select sum(valor_emprestado) as emprestado FROM movimentacao where SUBSTR(data, 0, 11) = '"+dat+"'").fetchall()
        total_recebido = cursor.execute("select sum(valor_pago) as pago FROM movimentacao where SUBSTR(data, 0, 11) = '"+dat+"'").fetchall()
        return render_template("movimentacoes_pesquisa.html", movimentacoes_completas=movimentacoes, dat=dat, datas=datas, movi=movi, user=user, total_saida=total_saida,total_recebido=total_recebido, clientes=clientes, client=client)
    if dat and client:
        cliente=Cliente.query.get(int(client))
        movimentacoes = cursor.execute("SELECT *, c.saldo, u.username FROM  Movimentacao LEFT JOIN Cliente as c ON  c.id = Movimentacao.id_cliente LEFT JOIN Usuario as u ON  u.id = Movimentacao.usuario_insert where SUBSTR(data, 0, 11) = '"+dat+"' and id_cliente = '"+client+"'").fetchall()
        total_saida = cursor.execute("select sum(valor_emprestado) as emprestado FROM movimentacao where SUBSTR(data, 0, 11) = '"+dat+"' and id_cliente = '"+client+"'").fetchall()
        total_recebido = cursor.execute("select sum(valor_pago) as pago FROM movimentacao where SUBSTR(data, 0, 11) = '"+dat+"' and id_cliente = '"+client+"'").fetchall()
        return render_template("movimentacoes_pesquisa.html", movimentacoes_completas=movimentacoes, dat=dat, datas=datas, movi=movi, user=user, total_saida=total_saida,total_recebido=total_recebido, clientes=clientes, client=client, cliente=cliente)
    



@app.route("/extrato/<string:id>")
@login_required
def extrato(id):
    extr="extr"
    user = Usuario.query.get(int(current_user.id))
    movimentacoes = database.session.query(Movimentacao, Cliente, Usuario).join(Cliente, Movimentacao.id_cliente == Cliente.id).join(Usuario, Movimentacao.usuario_insert == Usuario.id).filter(Cliente.id == id).all()
    total_saida = database.session.query(database.func.sum(Movimentacao.valor_emprestado)).filter(Movimentacao.id_cliente == id).first()
    total_recebido = database.session.query(database.func.sum(Movimentacao.valor_pago)).filter(Movimentacao.id_cliente == id).first()
    total_saldo = database.session.query(database.func.sum(Cliente.saldo)).filter(Cliente.id == id).first()
    return render_template("extrato_cliente.html", movimentacoes_completas=movimentacoes, extr=extr, user=user, total_saida=total_saida,total_recebido=total_recebido, total_saldo=total_saldo)

@app.route("/clientes")
@login_required
def clientes():
    cli="cli"
    user = Usuario.query.get(int(current_user.id))
    clientes = database.session.query(Cliente, Usuario).join(Usuario, Cliente.id_vendedor == Usuario.id).filter(Cliente.saldo != '0').all()
    movimentacao = conn.execute("SELECT max(data), id_cliente, obs from movimentacao group by id_cliente").fetchall()
    movimentacao_map = {row[1]: row[0] for row in movimentacao}
    movimentacao_map_obs = {row[1]: row[2] for row in movimentacao}
    total_saldo = database.session.query(database.func.sum(Cliente.saldo)).first()
    return render_template("cliente.html", clientes=clientes, cli=cli, user=user, movimentacao_map=movimentacao_map, total_saldo=total_saldo, movimentacao_map_obs=movimentacao_map_obs)

@app.route("/quitado")
@login_required
def quitado():
    qui="qui"
    user = Usuario.query.get(int(current_user.id))
    clientes = database.session.query(Cliente, Usuario).join(Usuario, Cliente.id_vendedor == Usuario.id).filter(Cliente.saldo == '0').all()
    movimentacao = conn.execute("SELECT max(data), id_cliente, obs from movimentacao group by id_cliente").fetchall()
    movimentacao_map = {row[1]: row[0] for row in movimentacao}
    movimentacao_map_obs = {row[1]: row[2] for row in movimentacao}
    total_saldo = database.session.query(database.func.sum(Cliente.saldo)).first()
    return render_template("quitado.html", clientes=clientes, qui=qui, user=user, movimentacao_map=movimentacao_map, total_saldo=total_saldo, movimentacao_map_obs=movimentacao_map_obs)


@app.route("/vendedores")
@login_required
def vendedores():
    vend="vend"
    user = Usuario.query.get(int(current_user.id))
    vendedores = Usuario.query.order_by(Usuario.id).all()
    return render_template("vendedores.html", vendedores=vendedores, vend=vend, user=user)

@app.route("/vendedor_cliente/<string:id>")
@login_required
def vendedor_cliente(id):
    vend="vend"
    user = Usuario.query.get(int(current_user.id))
    vendedor = Usuario.query.get(int(id))
    clientes = Cliente.query.filter(Cliente.id_vendedor == id).all()
    total_saldo = database.session.query(database.func.sum(Cliente.saldo)).filter(Cliente.id_vendedor == id).first()
    return render_template("vendedor_clientes.html", clientes=clientes, vendedor=vendedor, vend=vend, user=user, total_saldo=total_saldo)

@app.route("/valor_emprestimo/<string:id_user>",methods=['GET', "POST"])
def valor_emprestimo(id_user):
    if request.method == "GET":
        user = Usuario.query.get(int(current_user.id))
        clientes = Cliente.query.get(int(id_user))
        movi="movi"
        return render_template("criaremprestimo.html", clientes=clientes, movi=movi, user=user)
    if request.method == "POST":
        movi="movi"
        user = Usuario.query.get(int(current_user.id))
        clientes = Cliente.query.get(int(id_user))
        valor_pago=request.form.get("valor")
        data=datetime.now().strftime('%d/%m/%Y %H:%M')
        obs=request.form.get("obs")
        cursor.execute("UPDATE CLIENTE SET saldo = saldo-'"+str(valor_pago)+"' WHERE id = '"+id_user+"'")
        cursor.execute("INSERT INTO MOVIMENTACAO (id_cliente, data, valor_emprestado, usuario_insert, obs, ultimo_saldo) VALUES ('"+str(id_user)+"', '"+data+"', '"+valor_pago+"', '"+str(current_user.id)+"', '"+obs+"', '"+clientes.saldo+"'-'"+str(valor_pago)+"')")
        conn.commit()
        flash('User Deleted','warning')
        return redirect(url_for("vendedor_cliente", id=clientes.id_vendedor))
    return render_template("criaremprestimo.html", clientes=clientes, movi=movi, user=user)




@app.route("/valor_pago/<string:id_user>",methods=['GET', "POST"])
def valor_pago(id_user):
    if request.method == "GET":
        movi="movi"
        user = Usuario.query.get(int(current_user.id))
        clientes = Cliente.query.get(int(id_user))
        return render_template("criarpagou.html", clientes=clientes, movi=movi, user=user)
    if request.method == "POST":
        movi="movi"
        user = Usuario.query.get(int(current_user.id))
        clientes = Cliente.query.get(int(id_user))
        valor_pago=request.form.get("valor")
        atrasado=request.form.get("atrasado")
        obs=request.form.get("obs")
        data=datetime.now().strftime('%d/%m/%Y %H:%M')
        cursor.execute("UPDATE CLIENTE SET saldo = saldo+'"+str(valor_pago)+"' WHERE id = '"+id_user+"'")
        cursor.execute("INSERT INTO MOVIMENTACAO (id_cliente, data, valor_pago, usuario_insert, obs, ultimo_saldo, atrasado) VALUES ('"+str(id_user)+"', '"+data+"', '"+valor_pago+"', '"+str(current_user.id)+"', '"+obs+"', '"+clientes.saldo+"'+'"+str(valor_pago)+"', '"+atrasado+"')")
        conn.commit()
        flash('User Deleted','warning')
        return redirect(url_for("vendedor_cliente", id=clientes.id_vendedor))
    return render_template("criarpagou.html", clientes=clientes, movi=movi, user=user)

engine.dispose()