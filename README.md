# Facial Recognition System API in Docker

##

A <a href="https://github.com/deepinsight/insightface">deepinsight/insightface</a> implementation with <a href="https://github.com/tiangolo/fastapi">FastAPI</a> for face recognition.

## Run

Using docker-compose:

```
docker-compose up
```

## Swagger UI

Swagger UI served at http://127.0.0.1:5000/docs .

## Available APIs

It is recommended to test the available APIs from `[GET] /docs`

- `[GET] /` - Root

  - Check API status

- `[POST] /add` - Add Single Face

  - Upload a single face image file with person name and store it to database

- `[DELETE] /delete` - Delete Face

  - Delete a face from database using name from database

- `[POST] /recognize` - Face Recognition

  - Upload a single face image file and a person name from the database to verify

- `[POST] /face-search` - Face Search

  - Upload a single face file to search for similar faces in database

- `[GET] /list-all` - Get All Faces

  - Get all faces from database

- `[GET] /get-single-face-by-name` - Get Single Face

  - Get single face from database

- `[POST] ​/analyze-multiple-faces` - Analyze Multiple Faces

  - Upload a multiple face image to analyze (does not save to database)

- `[POST] /compute-two_faces-similarity` - Compute Two Faces similarity
  - Compute similarity of 2 faces from 2 images (does not save to database)
