from flask import Flask, jsonify, request, render_template_string
from functools import wraps
from database import (
    get_db_connection_api,
    get_db_connection_mangas,
    gerar_chave,
    verificar_chave
)

app = Flask(__name__)

def requer_chave(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        chave = kwargs.get('key')
        ip = request.remote_addr
        if not chave or not verificar_chave(chave, ip):
            return jsonify({"error": "Chave inválida, expirada ou IP incorreto"}), 401
        return f(*args, **kwargs)
    return decorator

@app.route("/api/gerar_chave", methods=["GET"])
def criar_chave():
    ip = request.remote_addr
    nova_chave = gerar_chave(ip)
    if nova_chave:
        return jsonify({"chave": nova_chave, "expira_em": "24 horas"})
    else:
        return jsonify({"error": "Já existe uma chave ativa para este IP."}), 400

@app.route("/api/chaves", methods=["GET"])
def listar_chaves():
    ip = request.remote_addr
    conn = get_db_connection_api()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM api_keys WHERE ip = ?", (ip,))
    chaves = cursor.fetchall()
    conn.close()
    return jsonify([dict(chave) for chave in chaves])

@app.route("/api/<key>/filmes", methods=["GET"])
@requer_chave
def listar_filmes(key):
    nome = request.args.get('q', '')
    id_filme = request.args.get('id', None)

    conn = get_db_connection_api()
    cursor = conn.cursor()

    if id_filme:
        cursor.execute("SELECT * FROM filmes WHERE id = ?", (id_filme,))
        filmes = cursor.fetchall()
    elif nome:
        cursor.execute("SELECT * FROM filmes WHERE title LIKE ?", ('%' + nome + '%',))
        filmes = cursor.fetchall()
    else:
        cursor.execute("SELECT * FROM filmes")
        filmes = cursor.fetchall()

    conn.close()
    return jsonify([dict(filme) for filme in filmes])

@app.route("/api/<key>/mangas", methods=["GET"])
@requer_chave
def listar_mangas(key):
    conn = get_db_connection_mangas()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM mangas")
    mangas = cursor.fetchall()

    dados_mangas = []
    for manga in mangas:
        cursor.execute("SELECT * FROM chapters WHERE manga_id = ?", (manga['id'],))
        capitulos = cursor.fetchall()

        dados_capitulos = [
            {
                "id": capitulo['id'],
                "titulo": capitulo['title'],
                "link": capitulo['link'],
                "data_lancamento": capitulo['release_date'],
                "imagens": capitulo['images'].split(", ")
            } for capitulo in capitulos
        ]

        dados_mangas.append({
            "id": manga['id'],
            "titulo": manga['title'],
            "rating": manga['rating'],
            "ano": manga['year'],
            "capa": manga['cover'],
            "link": manga['link'],
            "generos": manga['genres'].split(", "),
            "sinopse": manga['synopsis'],
            "capitulos": dados_capitulos
        })

    conn.close()
    return jsonify(dados_mangas)

@app.route("/", methods=["GET"])
def documentacao():
    return render_template_string(open("templates/index.html").read())

@app.route("/chaves", methods=["GET"])
def gerenciar_chaves():
    return render_template_string(open("templates/gerenciar_chaves.html").read())

if __name__ == "__main__":
    app.run(debug=True)
