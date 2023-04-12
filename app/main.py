from fastapi import FastAPI, File
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

import insightface
import json
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.helper import file_to_image, string_to_nparray

import app.logger as log
import app.settings as settings
from app.exception import *
from app.exception.handling import *
from app.database.models import Face
from app.database import init as init_db, wait as wait_db
from app.analyze import *


app = FastAPI(title = "Insightface API")

log.debug("Constructing FaceAnalysis model.")
fa = insightface.app.FaceAnalysis()
log.debug("Preparing FaceAnalysis model.")
fa.prepare(ctx_id=0, det_size=(640, 640))


engine = create_engine(settings.DATABASE_URL)
Session = sessionmaker(bind=engine)

wait_db(engine)
init_db(engine)


@app.get("/")
def root():
    json_resp = {"message": "Server Error"}
    assert fa
    json_resp = JSONResponse(content={
        "status_code": 200,
        "message": "Insightface API web service is running"
        })

    return json_resp


@app.post("/add")
async def add_single_face(name: str, file: bytes = File(...)):
    # Supports single face in a single image

    log.debug("Calling upload_selfie.")
    session = Session()

    name = name.lower()
    db_face = session.query(Face).filter_by(name = name).first()
    if db_face is not None:
        raise ValidationError("Name must be unique.")
    

    image = file_to_image(file)
    fa_faces = analyze_image(image, fa)

    if len(fa_faces)>1 :
        raise Exception("More than one face was found. This function only supports adding of one face from an image with only single face in it.")
    
    fa_emb_str = str(json.dumps(fa_faces[0].embedding.tolist()))
    emb = "cube(ARRAY" + fa_emb_str+ ")"

    face = Face(name = name, age = fa_faces[0].age, gender = fa_faces[0].gender,  created_at = datetime.today())
    session.add(face)

    update_query = "UPDATE faces SET embedding = " + emb + " WHERE name = '" + str(face.name) + "';"
    session.commit()

    session.execute(update_query)
    session.commit()
    
    res_face = {"name": face.name, "age": face.age, "gender": face.gender}
    json_compatible_faces = jsonable_encoder(res_face)

    result = json_compatible_faces

    json_resp = JSONResponse(content={
        "status_code": 200,
        "statement":"Face sucessfully added",
        "result": result
        })

    session.close()
    return json_resp


@app.delete("/delete")
async def delete_face(name: str):
    # Delete face from db

    log.debug("Calling delete_face.")
    session = Session()

    target_face = session.query(Face).filter_by(name = name).first()
    if(target_face is None):
        raise NotFoundError("Face not found in the database.") 
    json_compatible_face = jsonable_encoder(target_face)
    result = {
        "face": json_compatible_face
    }
    session.delete(target_face)
    session.commit()

    json_resp = JSONResponse(content={
        "status_code": 200,
        "result": result,
        "statement":"Face sucessfully deleted"
        })

    session.close()
    return json_resp

@app.post("/recognize")
async def face_recognition(name: str, file: bytes = File(...)):
    # Supports single face in a single image

    log.debug("Calling face_recognition.")
    session = Session()
    
    name = name.lower()
    target_face = session.query(Face).filter_by(name = name).first()
    if target_face is None:
        raise NotFoundError("Face with that name does not exist in database.")

    image = file_to_image(file)

    fa_faces = analyze_image(image, fa)

    if len(fa_faces)>1 :
        raise Exception("More than one face was found. This function only supports input image with only single face in it.")

    inp_face = fa_faces[0]

    target_emb = string_to_nparray(target_face.embedding)

    sim = compute_similarity(inp_face.embedding, target_emb)
    assert(sim != -99) 
    sim *= 100
    if(sim >= 60):
        status = True
        verify=""
    else: 
        status = False
        verify="not "
    result = {
        "similarity": int(sim),
        "status": status
        }

    json_resp = JSONResponse(content={
        "status_code": 200,
        "statement": "The face in the image is "+verify+name,
        "result": result
        })

    session.close()
    return json_resp


@app.post("/face-search")
async def face_search(file: bytes = File(...), limit: int = 1):
    # Supports single face in a single image

    log.debug("Calling face_search.")

    if(limit > 10 or limit <= 0): # the number of search return 
        raise ValidationError("Limit must be more than 0 and less or equals 10.") 

    session = Session()

    image = file_to_image(file)

    fa_faces = analyze_image(image, fa)
    
    if len(fa_faces)>1 :
        raise Exception("More than one face was found. This function only supports input image with only single face in it.")
    
    inp_face = fa_faces[0]

    fa_emb_str = str(json.dumps(inp_face.embedding.tolist()))
    emb = "cube(ARRAY" + fa_emb_str+ ")"

    # Do Euclidean distance calculation over all record in db and rank the results 
    query = (
        "SELECT sub.* "
        "FROM "
        "( "
            "SELECT *, (1-(POWER(( embedding <-> " + emb + " ),2)/2))*100 AS similarity "
            "FROM faces "
        ") AS sub "
        "WHERE sub.gender = '" + inp_face.gender + "' AND sub.similarity > 50 "
        "ORDER BY sub.similarity DESC "
        "LIMIT " + str(limit) + ";"
        )
    
    query_res = session.execute(query)

    rows_proxy = query_res.fetchall()
    
    dict, arr = {}, []
    for row_proxy in rows_proxy:
        for column, value in row_proxy.items():
            dict = {**dict, **{column: value}}
        arr.append(dict)

    result = jsonable_encoder({
        "similar_faces": arr
        })

    json_resp = JSONResponse(content={
        "status_code": 200,
        "result": result
        })
        
    session.close()
    return json_resp


@app.get('/list-all') 
def get_all_faces():
    #get all faces from database
    session = Session()
    faces = session.query(Face).all()
    res_faces=[]
    for face in faces:
        res_faces.append({
            "name": face.name,
            "age": face.age, 
            "gender": face.gender
            })
    result = jsonable_encoder(res_faces)

    json_resp = JSONResponse(content={
        "status_code": 200,
        "statement": "There are(is) "+str(len(faces))+" faces in the database.",
        "result": result
        })
    return json_resp

@app.get("/get-single-face-by-name")
async def get_single_face(name:str):
    # Get faces from db

    log.debug("Calling get_single_face.")

    session = Session()
    target_face = session.query(Face).filter_by(name = name).first()
    if(target_face is None):
        raise NotFoundError("Face not found in the database.") 

    
    json_compatible_face = jsonable_encoder(target_face)
    result = {
        "face": json_compatible_face
        }

    json_resp = JSONResponse(content={
        "status_code": 200,
        "statement":name+" face sucessfully get",
        "result": result
        })
    session.close()
    return json_resp

####################################################################################

@app.post("/analyze-multiple-faces")
async def analyze_multiple_faces(file: bytes = File(...)):
    # Supports multiple faces in a single image
    # Not add to database

    log.debug("Calling analyze_multiple_faces.")

    image = file_to_image(file)
    faces = analyze_image(image, fa)
    
    res_faces = []
    for face in faces:
        res_faces.append({
            "age": face.age, 
            "gender": face.gender
            })
    result = jsonable_encoder(res_faces)

    json_resp = JSONResponse(content={
        "status_code": 200,
        "statement": str(len(faces))+" faces sucessfully being analysed.",
        "result": result
        })
    return json_resp


# @app.post("/upload-wefie-or-group-photo")
# async def upload_wefie_or_group_photo(name: str, file: bytes = File(...)):
    """Supports multiple face in a single image.
        -If the faces were to save in database.

    TODO(meiyih):
        1)First, detect and crop face
        2)Second, ask user to fill in detail for each face
    """

@app.post("/compute-two_faces-similarity")
async def compute_two_faces_similarity(file1: bytes = File(...), file2: bytes = File(...)):
    # Limited to one face for each images
    
    log.debug("Calling compute_selfie_image_files_similarity.")

    image1 = file_to_image(file1)
    image2 = file_to_image(file2)

    log.debug("Processing first image.")
    faces1 = fa.get(image1)
    emb1 = faces1[0].embedding

    log.debug("Processing second image.")
    faces2 = fa.get(image2)
    emb2 = faces2[0].embedding

    sim = compute_similarity(emb1, emb2)
    assert(sim != -99) 
    sim *= 100
    result = {
        "similarity": int(sim)
    }

    json_resp = JSONResponse(content={
        "status_code": 200,
        "statement": "Similarity between the two images are "+str(sim),
        "result": result
        })

    return json_resp

@app.exception_handler(NotFoundError)
async def not_found_error_handler(request, exc):
    log.error(str(exc))
    json_resp = get_error_response(status_code=404, message=str(exc))
    return json_resp

@app.exception_handler(ValidationError)
async def validation_error_handler(request, exc):
    log.error(str(exc))
    json_resp = get_error_response(status_code=422, message=str(exc))
    return json_resp


@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(request, exc):
    log.error(str(exc))
    json_resp = get_error_response(status_code=400, message=str(exc))
    return json_resp

@app.exception_handler(Exception)
async def exception_handler(request, exc):
    log.error(str(exc))
    json_resp = get_default_error_response()
    return json_resp