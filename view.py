import threading

from flask import Flask, jsonify, request, Response
from main import app, con
from flask_bcrypt import generate_password_hash, check_password_hash
from funcao import valida_senha
from fpdf import FPDF
from flask import send_file
import os
import pygal
import smtplib
import threading
from email.mime.text import MIMEText

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/grafico')
def grafico():
    cur = con.cursor()
    cur.execute("""select tipo, count(*) 
                    from usuario 
                    group by tipo
                    order by tipo
    """)
    resultado = cur.fetchall()
    cur.close()
    grafico = pygal.Bar()
    grafico.titile = 'Quantidade de usuários por tipo'

    for i in resultado:
        grafico.add(str(i[0]), i[1])
    return Response(grafico.render(), mimetype='image/svg+xml')

@app.route('/listar_usuario', methods=['GET'])
def listar_usuario():
    cur = con.cursor()
    try:
        cur.execute('select id_usuario, nome, email, senha from usuario')
        usuarios = cur.fetchall()

        usuarios_lista = []
        for usuario in usuarios:
            usuarios_lista.append({
                'id_usuario': usuario[0],
                'nome': usuario[1],
                'email': usuario[2],
                'senha': usuario[3]
            })

        return jsonify(mensagem='Lista de usuarios', usuarios =usuarios_lista)

    except Exception as e:
        return jsonify({"message": "Erro ao consultar banco de dados"})
    finally:
        cur.close()


@app.route('/criar_usuario', methods=['POST'])
def criar_usuario():
    cur = con.cursor()
    try:
        nome = request.form.get('nome')
        email = request.form.get('email')
        senha = request.form.get('senha')
        certo = valida_senha(senha)
        imagem = request.files.get('imagem')


        print(certo)
        if certo == True:
            senha_cripto = generate_password_hash(senha)
            cur.execute('select 1 from usuario where nome =?', (nome,))
            if cur.fetchone():
                return jsonify({"error":"Usuário já cadastrado"}), 400

            cur.execute("""insert into usuario(nome, email, senha)
                              values(?,?,?) RETURNING id_usuario""", (nome, email, senha_cripto))
            codigo_usuario = cur.fetchone()[0]
            con.commit()

            caminho_imagem = None
            if imagem:
                nome_imagem = f"{codigo_usuario}"
                caminho_imagem_destino = os.path.join(app.config['UPLOAD_FOLDER'], "Usuarios")
                os.makedirs(caminho_imagem_destino, exist_ok=True)
                caminho_imagem = os.path.join(caminho_imagem_destino, nome_imagem)
                imagem.save(caminho_imagem)

            return jsonify({
                "message": "Usuário cadastrado com sucesso",
                'usuario':{
                    "nome": nome,
                    "email": email,
                    "senha": senha
                }
            }),201
        return jsonify({"error": "Senha Fraca"}), 400
    except Exception as e:
        return jsonify({"message": "Erro ao cadastrar"})
    finally:
        cur.close()


@app.route('/editar_usuario/<int:id>', methods=['PUT'])
def editar_usuario(id):
    cur = con.cursor()
    cur.execute("""select id_usuario, nome, email, senha from usuario where id_usuario =? """, (id,))
    tem_usuario = cur.fetchone()
    if not tem_usuario:
        cur.close()
        return jsonify({"error": "Usuário não encontrado"}), 404

    dados = request.get_json()
    nome = dados.get('nome')
    email = dados.get('email')
    senha = dados.get('senha')

    cur.execute(""" update usuario set nome = ?, email = ?, senha =? where id_usuario = ? """, (nome, email, senha, id))
    con.commit()
    cur.close()

    return jsonify({
        "message": "Usuário atualizado com sucesso",
        'usuario': {
            "nome": nome,
            "email": email,
            "senha": senha
        }
    })

@app.route ('/deletar_usuario/<int:id>', methods=['DELETE'])
def deletar_usuario(id):
    cur = con.cursor()
    cur.execute("""select 1 from usuario where id_usuario =? """, (id,))
    if not cur.fetchone():
        cur.close()
        return jsonify({"error": "Usuário não encontrado"}), 404
    cur.execute('delete from usuario where id_usuario = ?', (id,))
    con.commit()
    cur.close()
    return  jsonify({"message": "Usuario deletado com sucesso", 'id_usuario':id})


@app.route('/login', methods=['POST'])
def login():
    dados = request.get_json()

    email = dados.get('email')
    senha = dados.get('senha')

    cur = con.cursor()
    cur.execute("SELECT u.EMAIL , u.SENHA  FROM USUARIO u WHERE u.EMAIL = 	?", (email,))
    usuario = cur.fetchone()
    if usuario:
        if check_password_hash(usuario[1], senha):
            return jsonify({"message": "Usuário logado com sucesso!"}), 200
        return jsonify({"error": "Dados Incorretos!"}), 400
    return jsonify({"error": "Dados Incorretos!"}), 400

@app.route('/relatorio', methods=['GET'])
def relatorio():
    cursor = con.cursor()
    cursor.execute("SELECT id_usuario, nome, email, senha FROM usuario")
    usuarios = cursor.fetchall()
    cursor.close()
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", style='B', size=16)
    pdf.cell(200, 10, "Relatorio de Usuarios", ln=True, align='C')
    pdf.ln(5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    pdf.set_font("Arial", size=12)
    for usuario in usuarios:
        pdf.cell(200, 10, f"ID: {usuario[0]} - {usuario[1]} - {usuario[2]} - {usuario[3]}", ln=True)
    contador_usuarios = len(usuarios)
    pdf.ln(10)
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(200, 10, f"Total de usuarios cadastrados: {contador_usuarios}", ln=True, align='C')
    pdf_path = "relatorio_usuarios.pdf"
    pdf.output(pdf_path)
    return send_file(pdf_path, as_attachment=True, mimetype='application/pdf')


@app.route("/enviar_email", methods=['POST'])
def enviar_email():
    dados = request.json
    assunto = dados.get("assunto")
    mensagem = dados.get("mensagem")
    destinatario = dados.get("destinatario")

    thread = threading.Thread(target=enviar_email,
                              args=(destinatario, assunto, mensagem))

    thread.start()
    return jsonify({"mensagem": "Email enviado com sucesso"}), 200
