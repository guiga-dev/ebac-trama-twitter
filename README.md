# Trama — microblog com Django REST

Projeto final da EBAC com cadastro, login, perfil opcional, seguidores, feed, CRUD de publicações, curtidas e comentários. A interface usa templates Django, CSS e JavaScript; toda interação de dados passa pela API REST.

## Executar localmente

Requer Python 3.12.

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
$env:DJANGO_DEBUG='true'
.venv\Scripts\python manage.py migrate
.venv\Scripts\python manage.py seed_demo
.venv\Scripts\python manage.py runserver
```

Abra http://127.0.0.1:8000/. `seed_demo` é opcional e cria apenas perfis fictícios sem senhas utilizáveis. Cadastre sua própria conta pela interface. Os dados ficam no SQLite local; nenhum banco ou arquivo privado acompanha o código.

## Comportamento

- Cadastro cria conta com senha protegida por hash; login usa sessão HttpOnly e CSRF. A API também aceita tokens.
- Nome, biografia e foto são alterações independentes. Não selecionar foto preserva a existente. A troca de senha exige senha atual e invalida tokens antigos.
- Seguir e deixar de seguir não duplicam relações. É possível consultar seguidores e seguidos.
- O feed exibe **somente publicações das pessoas seguidas**. Publicações próprias ficam no perfil e em Explorar.
- Apenas o autor pode editar/excluir publicações e excluir seus comentários. Curtidas são únicas por pessoa e publicação.
- Publicações e comentários têm limite de 280 caracteres. Fotos são validadas e limitadas a 3 MB. O conteúdo é escapado na interface.
- Listagens são paginadas. A interface permite carregar mais publicações e buscar perfis.

## API

| Recurso | Operações |
| --- | --- |
| `/api/auth/register/`, `/api/auth/login/`, `/api/auth/logout/` | POST |
| `/api/auth/token/` | POST username/password para obter token |
| `/api/me/` | GET e PATCH perfil (multipart para foto) |
| `/api/me/password/` | POST old_password/new_password |
| `/api/users/`, `/api/users/{id}/` | GET |
| `/api/users/{id}/follow/` | POST e DELETE |
| `/api/users/{id}/followers/`, `/following/` | GET |
| `/api/tweets/`, `/api/tweets/{id}/` | CRUD REST |
| `/api/tweets/feed/` | GET autenticado |
| `/api/tweets/{id}/like/` | POST e DELETE |
| `/api/tweets/{id}/comments/` | GET e POST |
| `/api/comments/{id}/` | DELETE pelo autor |

## Testes

`DJANGO_DEBUG=true python manage.py test social` (PowerShell: definir `$env:DJANGO_DEBUG='true'` antes).

Os testes verificam cadastro e hash de senha, login/logout, CSRF, alteração parcial de perfil e imagem, troca de senha, follow/unfollow, listas de conexões, composição estrita do feed, isolamento de autoria, curtidas, comentários, validação, paginação e busca.

## Publicar

Dockerfile e Procfile prontos para provedor Python/Docker. Configurar variáveis privadas no painel do provedor:

- `DJANGO_DEBUG=false`
- `DJANGO_SECRET_KEY`: valor aleatório privado, nunca incluir em Git
- `DJANGO_ALLOWED_HOSTS`: domínio exato separado por vírgula
- `DATABASE_URL`: PostgreSQL de produção (com SSL por padrão)
- `MEDIA_ROOT`: diretório de volume persistente para avatares

Executar migrações e `collectstatic` no deploy. Servir com Gunicorn. WhiteNoise serve CSS/JavaScript, e o endpoint de avatar entrega imagens do armazenamento configurado. SQLite e sistema de arquivos efêmero não garantem persistência entre deploys; para produção configurar PostgreSQL e volume persistente.

**Status da entrega:** código e testes locais em preparação. Repositório GitHub, publicação online e URL de deploy são etapas externas centralizadas pelo agente principal. Não considerar este arquivo prova de hospedagem pública.
