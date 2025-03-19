from flask import jsonify, request, render_template_string
from functools import wraps
from database import (
    criar_tabela_api_keys,
    get_db_connection_api,
    get_db_connection_mangas,
    gerar_chave,
    verificar_chave
)

def requer_chave(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        chave = kwargs.get('key')
        ip = request.remote_addr
        if not chave or not verificar_chave(chave, ip):
            return jsonify({"error": "Chave inválida, expirada ou IP incorreto"}), 401
        return f(*args, **kwargs)
    return decorator

def configurar_rotas(app):
    @app.route("/api/chaves", methods=["GET"])
    def listar_chaves():
        ip = request.remote_addr
        conn = get_db_connection_api()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM api_keys WHERE ip = ?", (ip,))
        chaves = cursor.fetchall()
        conn.close()
        return jsonify([dict(chave) for chave in chaves])

    @app.route("/api/gerar_chave", methods=["GET"])
    def criar_chave():
        ip = request.remote_addr
        nova_chave = gerar_chave(ip)
        if nova_chave:
            return jsonify({"chave": nova_chave, "expira_em": "10 minutos"})
        else:
            return jsonify({"error": "Já existe uma chave ativa para este IP."}), 400

    @app.route("/api/<key>/filmes", methods=["GET"])
    @requer_chave
    def listar_filmes(key):
        conn = get_db_connection_api()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM filmes")
        filmes = cursor.fetchall()
        conn.close()
        return jsonify([dict(filme) for filme in filmes])

    @app.route("/api/<key>/mangas", methods=["GET"])
    @requer_chave
    def listar_mangas(key):
        conn = get_db_connection_mangas()
        cursor = conn.cursor()

        # Buscar todos os mangás
        cursor.execute("SELECT * FROM mangas")
        mangas = cursor.fetchall()

        # Estrutura para armazenar os dados
        dados_mangas = []

        for manga in mangas:
            # Buscar capítulos do mangá
            cursor.execute("SELECT * FROM chapters WHERE manga_id = ?", (manga['id'],))
            capitulos = cursor.fetchall()

            # Estrutura para armazenar os capítulos
            dados_capitulos = []

            for capitulo in capitulos:
                # Adicionar informações do capítulo
                dados_capitulos.append({
                    "id": capitulo['id'],
                    "titulo": capitulo['title'],
                    "link": capitulo['link'],
                    "data_lancamento": capitulo['release_date'],
                    "imagens": capitulo['images'].split(", ")  # Converter string de imagens em lista
                })

            # Adicionar informações do mangá
            dados_mangas.append({
                "id": manga['id'],
                "titulo": manga['title'],
                "rating": manga['rating'],
                "ano": manga['year'],
                "capa": manga['cover'],
                "link": manga['link'],
                "generos": manga['genres'].split(", "),  # Converter string de gêneros em lista
                "sinopse": manga['synopsis'],
                "capitulos": dados_capitulos
            })

        conn.close()
        return jsonify(dados_mangas)

    @app.route("/", methods=["GET"])
    def documentacao():
        return render_template_string(open("templates/index.html").read())

    @app.route("/api/gerenciar_chaves", methods=["GET"])
    def gerenciar_chaves():
        return render_template_string(open("templates/gerenciar_chaves.html").read())