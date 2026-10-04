# mini-rag

this is a minimal implementation of the RAG model for question answering.

## requirements

- python 3.14

### install python using uv

1) 

2) creat a new inviroment 

3) activate the inviroment :




set your  enviroment variable `.env` file.  like `OPEN_API_KEY` value

## run Docker compose service

```bash
$ cd socker
$ sudo docker compose up -d

```

- update `.env` with your credentials

## Run the FastApi server

```bash
    uvicorn rag_app.main:app --reload --host 0.0.0.0 --port 5000
```~