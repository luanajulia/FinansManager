# criar as rotas do nosso site (os links)
from flask import flash,  render_template, request, url_for, redirect, session
from movimentacao import app, database, bcrypt
from movimentacao.models import Cliente, Usuario, Movimentacao, database, Contrato, Pagamento
from flask_login import login_required, login_user, logout_user, current_user
from movimentacao.forms import FormLogin, FormCriarConta, FormCliente, FormContrato, FormPagamentos
from werkzeug.utils import secure_filename
import os
import sqlite3 as sql
import email_validator
import sqlite3
from datetime import datetime, date, timedelta, time
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
import json

engine = create_engine('sqlite:///meubanco.db', poolclass=NullPool)

# 1. Pega o caminho de onde o routes.py está (pasta 'movimentacao')
caminho_atual = os.path.dirname(os.path.abspath(__file__))

# 2. Sobe um nível para chegar na raiz 'FinansManager'
projeto_raiz = os.path.dirname(caminho_atual)

# 3. Aponta para a pasta instance que está na raiz
caminho_db = os.path.join(projeto_raiz, "instance", "comunidade.db")

# 4. Conecta usando o caminho completo
conn = sqlite3.connect(caminho_db, check_same_thread=False)
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

@app.route("/criarpagamento", methods=["GET", "POST"])
def criar_pagamento():
    form_criarpagamento = FormPagamentos()
    user = Usuario.query.get(int(current_user.id))
    usuarios = Usuario.query.filter(Usuario.nivel == "Vendedor").all()
    if form_criarpagamento.validate_on_submit():
        try:
            valor = form_criarpagamento.valorTotal.data
            juros = form_criarpagamento.porcentagem.data
            parcelas = form_criarpagamento.divisor.data
            porcentagem_comissao = form_criarpagamento.porcentagemComissao.data
            
            valor_juros = int(((juros/100)*valor)+valor)
            result_parcelas = int((((juros/100)*valor)+valor) / parcelas)
            valor_comissao = int((porcentagem_comissao/100)*valor)
            
            pagamento = Pagamento(valor_juros=str(valor_juros),
                                  valor=str(valor),
                                  juros=str(juros),
                                  parcelas=str(parcelas),
                                  result_parcelas=str(result_parcelas),
                                  porcentagem_comissao=str(porcentagem_comissao),
                                  valor_comissao=str(valor_comissao))
            database.session.add(pagamento)
            database.session.commit()
            flash("Pagamento criado com sucesso!", "success")
            return redirect(url_for("pagamentos"))
        except Exception as e:
            flash(f"Erro ao criar pagamento: {str(e)}", "error")
            return redirect(url_for("criar_pagamento"))
    return render_template("criarpagamentos.html", form=form_criarpagamento, usuarios=usuarios, user=user)


@app.route("/editarpagamento/<int:id>", methods=["GET", "POST"])
def editar_pagamento(id):
    pagamentos = Pagamento.query.filter_by(id=id).all()
    user = Usuario.query.get(int(current_user.id))
    usuarios = Usuario.query.filter(Usuario.nivel == "Vendedor").all()
    if request.method == "GET":
        return render_template("editar_pagamentos.html", pagamentos=pagamentos, usuarios=usuarios, user=user)
    if request.method == "POST":
        try:
            valor = int(request.form.get("valorTotal") or 0)
            juros_int = int(request.form.get("porcentagem") or 0)
            parcelas = int(request.form.get("divisor") or 1)
            porcentagem_comissao = int(request.form.get("porcentagemComissao") or 0)
            
            if parcelas == 0:
                flash("Número de parcelas não pode ser zero.", "error")
                return redirect(url_for("editar_pagamento", id=id))
            
            valor_juros = int(((juros_int / 100) * valor) + valor)
            juros = request.form.get("porcentagem")
            result_parcelas = int((((juros_int / 100) * valor) + valor) / parcelas)
            porcentagem_comissao_str = request.form.get("porcentagemComissao")
            valor_comissao = int((porcentagem_comissao / 100) * valor)
            
            conn.execute("UPDATE pagamento SET valor_juros = ?, valor = ?, juros = ?, parcelas = ?, result_parcelas = ?, porcentagem_comissao = ?, valor_comissao = ? WHERE id = ?", 
                         (str(valor_juros), str(valor), str(juros), str(parcelas), str(result_parcelas), str(porcentagem_comissao_str), str(valor_comissao), str(id)))
            conn.commit()
            return redirect(url_for("pagamentos"))
        except (ValueError, TypeError) as e:
            flash(f"Erro nos dados: {str(e)}", "error")
            return redirect(url_for("editar_pagamento", id=id))
    return render_template("editar_pagamentos.html", pagamentos=pagamentos, usuarios=usuarios, user=user)

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
                          endereco=form_criarcliente.endereco.data,
                          data_nascimento=form_criarcliente.data_nascimento.data, 
                          usuario_insert=current_user.id,
                          id_vendedor=request.form.get("vendedor"))
        database.session.add(clientes)
        database.session.commit()
        return redirect(url_for("clientes"))
    return render_template("criarcliente.html", form=form_criarcliente, usuarios=usuarios, user=user)




@app.route("/criarcontrato", methods=["GET", "POST"])
def criarcontrato():
    pagamentos = database.session.query(Pagamento).all()
    form_criarcontrato = FormContrato()
    user = Usuario.query.get(int(current_user.id))
    usuarios = Cliente.query.order_by(Cliente.nome).all()
    if request.method == "POST":
        condioes = Pagamento.query.filter(Pagamento.id == request.form.get("condicao")).all()
        valor=condioes[0].valor_juros
        juros=condioes[0].juros
        parcelas=condioes[0].result_parcelas
        frequencia=condioes[0].parcelas
        contrato = Contrato(data=datetime.now().strftime('%d/%m/%Y %H:%M'),
                            valor=valor,
                            saldo=valor,
                            juros=juros,
                            frequencia=frequencia,
                            status="Ativo",
                            ultimo_insert="Sem movimentação",
                            id_cliente=request.form.get("cliente"),
                            parcelas=parcelas,
                            id_contrato=request.form.get("condicao"),
                            pagamento=request.form.get("frequencia"))
        database.session.add(contrato)
        database.session.commit()
        cursor.execute("UPDATE CLIENTE SET saldo = saldo-'"+str(valor)+"' WHERE id = '"+request.form.get("cliente")+"'")
        clientes = cursor.execute("SELECT * FROM CLIENTE where id = '"+request.form.get("cliente")+"'").fetchall()
        contrato=cursor.execute("SELECT * FROM CONTRATO where id_cliente = '"+request.form.get("cliente")+"' order by id desc limit 1").fetchall()
        for c in clientes:
            id_cliente = c[0]
            saldo = c[4]
            valor_pago=valor
            for co in contrato:
                id_contrato = co[0]
                if saldo == valor_pago:
                    cursor.execute("INSERT INTO MOVIMENTACAO (id_cliente, data, valor_emprestado, usuario_insert, obs, ultimo_saldo, id_contrato) VALUES ('"+str(request.form.get("cliente"))+"', '"+datetime.now().strftime('%d/%m/%Y %H:%M')+"', '"+str(valor_pago)+"', '"+str(current_user.id)+"', 'Contrato Valor pego', '-'"+str(valor_pago)+"', '"+str(id_contrato)+"')")
                    conn.commit()
                    return redirect(url_for("contratos"))
                else:
                    cursor.execute("INSERT INTO MOVIMENTACAO (id_cliente, data, valor_emprestado, usuario_insert, obs, ultimo_saldo, id_contrato) VALUES ('"+str(request.form.get("cliente"))+"', '"+datetime.now().strftime('%d/%m/%Y %H:%M')+"', '"+str(valor_pago)+"', '"+str(current_user.id)+"', 'Contrato Valor pego', '"+str(saldo)+"'-'"+str(valor_pago)+"', '"+str(id_contrato)+"')")
                    conn.commit()
                return redirect(url_for("contratos"))
    return render_template("criarcontrato.html", form=form_criarcontrato, usuarios=usuarios, user=user, pagamentos=pagamentos)

@app.route("/criar_vendedor", methods=["GET", "POST"])
def criar_vendedor():
    form_criarconta = FormCriarConta()
    vend="vend"
    user = Usuario.query.get(int(current_user.id))
    if request.method == "GET":
        form_criarconta.nivel.data = "Vendedor"
    if form_criarconta.validate_on_submit():
        senha = bcrypt.generate_password_hash(form_criarconta.senha.data)
        usuario = Usuario(username=form_criarconta.username.data,
                          nivel=form_criarconta.nivel.data,
                          senha=senha, 
                          email=form_criarconta.email.data)
        database.session.add(usuario)
        database.session.commit()
        flash("Vendedor criado com sucesso!", "success")
        return redirect(url_for("vendedores"))
    return render_template("criar_vendedor.html", form=form_criarconta, vend=vend, user=user)

@app.route("/editar_vendedor/<int:id>", methods=["GET", "POST"])
def editar_vendedor(id):
    vend="vend"
    user = Usuario.query.get(int(current_user.id))
    usuarios = Usuario.query.filter_by(id=id).all()
    if request.method == "GET":
        return render_template("editar_vendedor.html", vend=vend, user=user, usuarios=usuarios)
    if request.method == "POST":
        username=request.form.get("username")   
        nivel=request.form.get("nivel")
        email=request.form.get("email")
        senha=bcrypt.generate_password_hash(request.form.get("senha"))
        conn.execute("UPDATE usuario SET username = ?, nivel = ?, email = ?, senha = ? WHERE id = ?", (username, nivel, email, senha, str(request.form.get("id"))))
        return redirect(url_for("vendedores"))
    return render_template("editar_vendedor.html",  vend=vend, user=user, usuarios=usuarios)

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

@app.route("/pagamentos")
@login_required
def pagamentos():
    pag="pag"
    user = Usuario.query.get(int(current_user.id))
    pagamentos = database.session.query(Pagamento).all()
    return render_template("pagamentos.html", pagamentos=pagamentos, pag=pag, user=user)

@app.route("/cliente_vizualizar/<string:id>")
@login_required
def cliente_vizualizar(id):
    cli="cli"
    user = Usuario.query.get(int(current_user.id))
    cliente = Cliente.query.get(int(id))
    vendedores = database.session.query(Cliente, Usuario).join(Usuario, Cliente.id_vendedor == Usuario.id).all()
    return render_template("cliente_vizualizar.html", cliente=cliente, cli=cli, user=user, vendedores=vendedores)

@app.route("/clientes")
@login_required
def clientes():
    cli="cli"
    user = Usuario.query.get(int(current_user.id))
    clientess = Cliente.query.order_by(Cliente.nome).all()
    vendedores = Usuario.query.order_by(Usuario.id).all()
    datas = cursor.execute("select DISTINCT SUBSTR(data, 0, 11) as data_contrato FROM movimentacao ").fetchall()
    clientes = database.session.query(Cliente, Usuario).join(Usuario, Cliente.id_vendedor == Usuario.id).filter(Cliente.saldo != '0').all()
    movimentacao = conn.execute("SELECT max(data), id_cliente, obs from movimentacao group by id_cliente").fetchall()
    movimentacao_map = {row[1]: row[0] for row in movimentacao}
    movimentacao_map_obs = {row[1]: row[2] for row in movimentacao}
    total_saldo = database.session.query(database.func.sum(Cliente.saldo)).first()
    return render_template("cliente.html", clientess=clientess, vendedores=vendedores, datas=datas, clientes=clientes, cli=cli, user=user, movimentacao_map=movimentacao_map, total_saldo=total_saldo, movimentacao_map_obs=movimentacao_map_obs)

@app.route("/clientes_pesquisa", methods=['GET', "POST"])
@login_required
def clientes_pesquisa():
    cli="cli"
    user = Usuario.query.get(int(current_user.id))
    clientess = Cliente.query.order_by(Cliente.nome).all()
    vendedores = Usuario.query.order_by(Usuario.id).all()
    datas = cursor.execute("select DISTINCT SUBSTR(data, 0, 11) as data_contrato FROM contrato ").fetchall()
    if request.method == 'POST':
        client = request.form.get('cliente')
        vendor = request.form.get('vendedor')
        session['client'] = client 
        session['vendor'] = vendor
    client = session.get('client', '')
    vendor = session.get('vendor', '')
    if client != "":
        clientes = database.session.query(Cliente, Usuario).join(Usuario, Cliente.id_vendedor == Usuario.id).filter(Cliente.saldo != '0').filter(Cliente.id == client).all()
        movimentacao = conn.execute("SELECT max(data), id_cliente, obs from movimentacao   group by id_cliente").fetchall()
        movimentacao_map = {row[1]: row[0] for row in movimentacao}
        movimentacao_map_obs = {row[1]: row[2] for row in movimentacao}
        total_saldo = database.session.query(database.func.sum(Cliente.saldo)).first()
        return render_template("cliente.html",  clientes=clientes, clientess=clientess, vendedores=vendedores, cli=cli, user=user, datas=datas, movimentacao_map=movimentacao_map, total_saldo=total_saldo, movimentacao_map_obs=movimentacao_map_obs)
    elif vendor != "":
        clientes = database.session.query(Cliente, Usuario).join(Usuario, Cliente.id_vendedor == Usuario.id).filter(Cliente.saldo != '0').filter(Cliente.id_vendedor == vendor).all()
        movimentacao = conn.execute("SELECT max(data), id_cliente, obs from movimentacao group by id_cliente").fetchall()
        movimentacao_map = {row[1]: row[0] for row in movimentacao}
        movimentacao_map_obs = {row[1]: row[2] for row in movimentacao}
        total_saldo = database.session.query(database.func.sum(Cliente.saldo)).first()
        return render_template("cliente.html",  clientes=clientes, clientess=clientess, vendedores=vendedores, cli=cli, user=user, datas=datas, movimentacao_map=movimentacao_map, total_saldo=total_saldo, movimentacao_map_obs=movimentacao_map_obs)
    else:
        clientes = database.session.query(Cliente, Usuario).join(Usuario, Cliente.id_vendedor == Usuario.id).filter(Cliente.saldo != '0').all()
        movimentacao = conn.execute("SELECT max(data), id_cliente, obs from movimentacao group by id_cliente").fetchall()
        movimentacao_map = {row[1]: row[0] for row in movimentacao}
        movimentacao_map_obs = {row[1]: row[2] for row in movimentacao}
        total_saldo = database.session.query(database.func.sum(Cliente.saldo)).first()
        return render_template("cliente.html",  clientes=clientes, clientess=clientess, vendedores=vendedores, cli=cli, user=user, datas=datas, movimentacao_map=movimentacao_map, total_saldo=total_saldo, movimentacao_map_obs=movimentacao_map_obs)


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
    niveis = cursor.execute("SELECT DISTINCT nivel FROM usuario").fetchall()
    return render_template("vendedores.html", vendedores=vendedores, vend=vend, user=user, niveis=niveis)


@app.route("/vendedores_pesquisa", methods=['GET', "POST"])
@login_required
def vendedores_pesquisa():
    if request.method == 'POST':
        username = request.form.get('username')
        nivel = request.form.get('nivel')
        session['username'] = username
        session['nivel'] = nivel
    username = session['username']
    nivel = session['nivel']
    vend="vend"
    user = Usuario.query.get(int(current_user.id))
    niveis = cursor.execute("SELECT DISTINCT nivel FROM usuario").fetchall()

    vendedores = Usuario.query.order_by(Usuario.id).all()
    if username != "":
        vendedores = Usuario.query.filter(Usuario.id == username).all()
    if nivel != "":
        vendedores = Usuario.query.filter(Usuario.nivel == nivel).all()
    return render_template("vendedores.html", vendedores=vendedores, vend=vend, user=user, niveis=niveis)


@app.route("/vendedores_vizualizar/<string:id>")
@login_required
def vendedores_vizualizar(id):
    vend="vend"
    user = Usuario.query.get(int(current_user.id))
    clientes = f"""SELECT cli.nome as clientes, usu.username as vendedor,  pag.valor_comissao, concat(con.frequencia, ' x ', pag.valor_comissao / con.frequencia) as divisao,con.* FROM contrato as con 
                    LEFT JOIN cliente as cli on con.id_cliente = cli.id 
                    LEFT JOIN usuario as usu on cli.id_vendedor = usu.id
                    LEFT JOIN pagamento as pag on con.id_contrato = pag.id 
                    WHERE cli.id_vendedor = '{id}'"""
    vendedores = conn.execute(clientes).fetchall()
    return render_template("vendedor_vizualizar.html", vendedores=vendedores, vend=vend, user=user, clientes=clientes)

@app.route("/contratos")
@login_required
def contratos():
    contr="contr"
    user = Usuario.query.get(int(current_user.id))
    clientes = Cliente.query.order_by(Cliente.nome).all()
    vendedores = Usuario.query.order_by(Usuario.id).all()
    datas = cursor.execute("select DISTINCT SUBSTR(data, 0, 11) as data_contrato FROM contrato ").fetchall()
    contratos = cursor.execute("SELECT con.*, cli.nome as cliente, usu.username as vendedor FROM contrato as con LEFT JOIN cliente as cli on con.id_cliente = cli.id LEFT JOIN usuario as usu on cli.id_vendedor = usu.id ").fetchall()
    return render_template("contratos.html",  contratos=contratos, clientes=clientes, vendedores=vendedores, contr=contr, user=user, datas=datas)

@app.route("/contratos_pesquisa", methods=['GET', "POST"])
@login_required
def contratos_pesquisa():
    contr="contr"
    user = Usuario.query.get(int(current_user.id))
    clientes = Cliente.query.order_by(Cliente.nome).all()
    vendedores = Usuario.query.order_by(Usuario.id).all()
    datas = cursor.execute("select DISTINCT SUBSTR(data, 0, 11) as data_contrato FROM contrato ").fetchall()
    if request.method == 'POST':
        client = request.form.get('cliente')
        dat = request.form.get('data')
        vendor = request.form.get('vendedor')
        session['client'] = client 
        session['dat'] = dat
        session['vendor'] = vendor
    client = session.get('client', '')
    dat = session.get('dat', '')
    vendor = session.get('vendor', '')
    if client != "":
        contratos = cursor.execute("SELECT con.*, cli.nome as cliente, usu.username as vendedor FROM contrato as con LEFT JOIN cliente as cli on con.id_cliente = cli.id LEFT JOIN usuario as usu on cli.id_vendedor = usu.id where id_cliente = '"+client+"'").fetchall()
        return render_template("contratos.html",  contratos=contratos, clientes=clientes, vendedores=vendedores, contr=contr, user=user, datas=datas)
    elif dat != "":
        contratos = cursor.execute("SELECT con.*, cli.nome as cliente, usu.username as vendedor FROM contrato as con LEFT JOIN cliente as cli on con.id_cliente = cli.id LEFT JOIN usuario as usu on cli.id_vendedor = usu.id where SUBSTR(con.data, 0, 11) = '"+dat+"'").fetchall()    
        return render_template("contratos.html",  contratos=contratos, clientes=clientes, vendedores=vendedores, contr=contr, user=user, datas=datas)
    elif vendor != "":
        contratos = cursor.execute("SELECT con.*, cli.nome as cliente, usu.username as vendedor FROM contrato as con LEFT JOIN cliente as cli on con.id_cliente = cli.id LEFT JOIN usuario as usu on cli.id_vendedor = usu.id where usu.id = '"+vendor+"'").fetchall()
        return render_template("contratos.html",  contratos=contratos, clientes=clientes, vendedores=vendedores, contr=contr, user=user, datas=datas)
    else:
        contratos = cursor.execute("SELECT con.*, cli.nome as cliente, usu.username as vendedor FROM contrato as con LEFT JOIN cliente as cli on con.id_cliente = cli.id LEFT JOIN usuario as usu on cli.id_vendedor = usu.id ").fetchall()
        return render_template("contratos.html",  contratos=contratos, clientes=clientes, vendedores=vendedores, contr=contr, user=user, datas=datas)


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

@app.route("/valor_pago/<string:id_contrato>",methods=['GET', "POST"])
def valor_pago(id_contrato):
    contrato = cursor.execute("SELECT * FROM contrato where id = '"+id_contrato+"'").fetchall()
    for c in contrato:
        id_user = c[1]
        saldo = c[4]
    if request.method == "GET":
        movi="movi"
        user = Usuario.query.get(int(current_user.id))
        clientes = Cliente.query.get(int(id_user))
        return render_template("criarpagou.html", clientes=clientes, movi=movi, user=user, saldo=saldo)
    if request.method == "POST":
        movi="movi"
        user = Usuario.query.get(int(current_user.id))
        clientes = Cliente.query.get(int(id_user))
        valor_pago = float(request.form.get("valor"))
        atrasado=request.form.get("atrasado")
        obs=request.form.get("obs")
        data=datetime.now().strftime('%d/%m/%Y %H:%M')
        cursor.execute("UPDATE CLIENTE SET saldo = saldo+'"+str(valor_pago)+"' WHERE id = '"+str(id_user)+"'")
        cursor.execute("UPDATE CONTRATO SET ultimo_insert = 'no dia "+data+" foi pago "+str(valor_pago)+"', saldo = saldo-'"+str(valor_pago)+"' WHERE id = '"+id_contrato+"'")
        cursor.execute("INSERT INTO MOVIMENTACAO (id_cliente, data, valor_pago, usuario_insert, obs, ultimo_saldo, atrasado, id_contrato) VALUES ('"+str(id_user)+"', '"+data+"', '"+str(valor_pago)+"', '"+str(current_user.id)+"', '"+obs+"', '"+clientes.saldo+"'+'"+str(valor_pago)+"', '"+atrasado+"', '"+id_contrato+"')")
        conn.commit()
        flash('User Deleted','warning')
        if float(saldo) - float(valor_pago) <= 0:
            cursor.execute("UPDATE CONTRATO SET status = 'Quitado' WHERE id = '"+id_contrato+"'")
            conn.commit()
        return redirect(url_for("contratos"))
    return render_template("criarpagou.html", clientes=clientes, movi=movi, user=user, saldo=saldo)

@app.route("/grafico")
@login_required
def grafico():
    graf="graf"
    user = Usuario.query.get(int(current_user.id))
    total_saldo = database.session.query(database.func.sum(Cliente.saldo)).first()
    quitados = database.session.query(database.func.count(Contrato.id), Contrato.status).group_by(Contrato.status).order_by(database.func.count(Contrato.status)).all()

    saldos = cursor.execute("SELECT sum(saldo) as saldo FROM cliente").fetchall()
    saldo_cliente = cursor.execute("SELECT saldo, nome FROM cliente").fetchall()


    depart = []
    usuarios_data = []
    for amount, status in quitados:
        # Converter None para "Sem Status"
        status_label = status if status is not None else "Sem Status"
        depart.append(status_label)
        usuarios_data.append(amount if amount is not None else 0)

    saldo_c = []
    cliente_s = []
    for saldo_val, nome in saldo_cliente:
        try:
            saldo_num = float(saldo_val) if saldo_val else 0.0
        except ValueError:
            saldo_num = 0.0
        saldo_c.append(saldo_num)
        cliente_s.append(nome if nome is not None else "Sem Nome")

    return render_template("grafico.html", total_saldo=total_saldo, user=user, graf=graf, depart=depart, usuarios_data=usuarios_data, saldos=saldos, saldo_c=saldo_c, cliente_s=cliente_s)

engine.dispose()