
from flask import Flask, render_template, request, redirect, send_file
import sqlite3
from datetime import datetime
import openpyxl
from io import BytesIO

app = Flask(__name__)
NOME_BD = 'banco_de_dados.db'

def iniciar_banco():
    with sqlite3.connect(NOME_BD) as conexao:
        cursor = conexao.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS funcionarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                matricula TEXT NOT NULL,
                cargo TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS registros_ponto (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                funcionario_id INTEGER,
                tipo TEXT CHECK(tipo IN ('entrada', 'saida')),
                horario TEXT,
                FOREIGN KEY (funcionario_id) REFERENCES funcionarios(id)
            )
        ''')
        conexao.commit()

@app.route('/')
def pagina_inicial():
    return render_template('index.html')

@app.route('/funcionarios', methods=['GET', 'POST'])
def funcionarios():
    conexao = sqlite3.connect(NOME_BD)
    cursor = conexao.cursor()

    if request.method == 'POST':
        nome = request.form['nome']
        matricula = request.form['matricula']
        cargo = request.form['cargo']
        cursor.execute("INSERT INTO funcionarios (nome, matricula, cargo) VALUES (?, ?, ?)",
                      (nome, matricula, cargo))
        conexao.commit()

    cursor.execute("SELECT * FROM funcionarios")
    lista_funcionarios = cursor.fetchall()
    conexao.close()
    return render_template('funcionarios.html', funcionarios=lista_funcionarios)

@app.route('/remover_funcionario/<int:id>', methods=['POST'])
def remover_funcionario(id):
    conexao = sqlite3.connect(NOME_BD)
    cursor = conexao.cursor()
    cursor.execute('DELETE FROM registros_ponto WHERE funcionario_id = ?', (id,))
    cursor.execute('DELETE FROM funcionarios WHERE id = ?', (id,))
    conexao.commit()
    conexao.close()
    return redirect('/funcionarios')

@app.route('/registrar/<int:funcionario_id>/<tipo>', methods=['POST'])
def registrar_ponto(funcionario_id, tipo):
    if tipo not in ['entrada', 'saida']:
        return 'Tipo inválido', 400

    horario_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conexao = sqlite3.connect(NOME_BD)
    cursor = conexao.cursor()
    cursor.execute('''
        INSERT INTO registros_ponto (funcionario_id, tipo, horario)
        VALUES (?, ?, ?)
    ''', (funcionario_id, tipo, horario_atual))
    conexao.commit()
    conexao.close()
    return redirect('/funcionarios')

@app.route('/registros')
def registros():
    conexao = sqlite3.connect(NOME_BD)
    cursor = conexao.cursor()
    cursor.execute('''
        SELECT f.nome, r.tipo, r.horario
        FROM registros_ponto r
        JOIN funcionarios f ON r.funcionario_id = f.id
        ORDER BY r.horario DESC
    ''')
    registros = cursor.fetchall()
    conexao.close()
    return render_template('registros.html', registros=registros)

@app.route('/exportar')
def exportar_excel():
    conexao = sqlite3.connect(NOME_BD)
    cursor = conexao.cursor()
    cursor.execute('''
        SELECT f.nome, r.tipo, r.horario
        FROM registros_ponto r
        JOIN funcionarios f ON r.funcionario_id = f.id
        ORDER BY r.horario
    ''')
    registros = cursor.fetchall()
    conexao.close()

    planilha = openpyxl.Workbook()
    aba = planilha.active
    aba.title = "Registros de Ponto"
    aba.append(["Funcionário", "Tipo", "Horário"])

    for registro in registros:
        aba.append(registro)

    arquivo_memoria = BytesIO()
    planilha.save(arquivo_memoria)
    arquivo_memoria.seek(0)

    return send_file(arquivo_memoria,
                     as_attachment=True,
                     download_name="registros_ponto.xlsx",
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@app.route('/limpar_registros', methods=['POST'])
def limpar_registros():
    conexao = sqlite3.connect(NOME_BD)
    cursor = conexao.cursor()
    cursor.execute('DELETE FROM registros_ponto')
    conexao.commit()
    conexao.close()
    return redirect('/registros')

if __name__ == '__main__':
    iniciar_banco()
    app.run(debug=True)