from fastapi.params import Form
from fastapi import FastAPI,Request, Query, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import bcrypt
import re
import starlette.status as status
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse, Response
import starlette.status as status
from typing import Optional 
from dbcontroller import DBController
import sqlite3


app = FastAPI()

app.mount("/static",StaticFiles(directory="static"),"static")

templates = Jinja2Templates("templates")

# SessionMiddleware secret key
app.add_middleware(SessionMiddleware, secret_key="asdfghjkl")


db = DBController("app.db")


@app.get("/", response_class=HTMLResponse)
def index(request:Request):
    return templates.TemplateResponse("page1.html",{"request":request})


@app.post("/register",response_class=HTMLResponse)
def create_post(request:Request, name:str = Form(...),contact_number:str = Form(...), email:str = Form(...), date:str = Form(...), time:str = Form(...), whom_to_meet:str = Form(...),  purpose:str = Form(...), reason:str = Form(...)):
    data = {"name":name, "contact_number":contact_number, "email":email, "date":date, "time":time, "whom_to_meet":whom_to_meet,  "purpose":purpose, "reason":reason}
    if(db.insert("register1",data=data)):
        return templates.TemplateResponse("register.html",{"request":request,"msg":"Registered successfully"})
    return templates.TemplateResponse("register.html",{"request":request,"msg":"Unable to register"})

@app.post("/",response_class=HTMLResponse)
def admin_login(request:Request, email:str = Form(...), password:str=Form(...)):
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()

    # Retrieve the salt and hashed password for the user
    cursor.execute('select * from users where email =? and password=?', (email,password,))
    result = cursor.fetchone()
    if not result:
        return templates.TemplateResponse("/login2.html", {"request": request, "msg": "Invalid Email or Password"})
    else:
        request.session.setdefault("isLogin", True)
        request.session.setdefault('email', email)
        request.session.setdefault('role', 1)
        return RedirectResponse("/FFdashboard", status_code=status.HTTP_302_FOUND)


@app.post("/teacherlogin", response_class=HTMLResponse)
def teacher_login(request: Request, email: str = Form(...), password: str = Form(...)):
    
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()

    # Retrieve the salt and hashed password for the user
    cursor.execute('SELECT password FROM addteachers WHERE email =?', (email,))
    result = cursor.fetchone()
    if not result or not bcrypt.checkpw(password.encode('utf-8'), result[0]):
        return templates.TemplateResponse("/login2.html", {"request": request, "msg": "Invalid Email or Password"})
    else:
        request.session.setdefault("isLogin", True)
        request.session["email"] = email
        request.session.setdefault('role', 2)
        return RedirectResponse("/Tdashboard", status_code=status.HTTP_302_FOUND)

@app.get("/Tdashboard", response_class=HTMLResponse)
def Tdashboard(request:Request):
    isLogin = request.session.get('isLogin')
    role = request.session.get('role')
    email = request.session.get('email')
    users = db.executeQueryWithParams("select * from addteachers where email =?", [email,])[0]
    name = users['name']
    department = users['department']
    contact_number = users['contact_number']
    date_of_birth = users['date_of_birth']
    pfp = users['photo']
    
    if role == 2:
        #orders = db.executeQuery("select * from register1 where whom_to_meet =?", [name])
            # Connect to the database
        department_name= name+" - "+department
        conn = sqlite3.connect("app.db")
        cursor = conn.cursor()
    
        cursor.execute("SELECT COUNT(*) FROM register1 where whom_to_meet =?",(department_name,))
        total_visitors = cursor.fetchone()
        
        cursor.execute("SELECT COUNT(*) FROM register1 where whom_to_meet =? and purpose ='Personal'",(department_name,))
        visitors_personal = cursor.fetchone()
        
        cursor.execute("SELECT COUNT(*) FROM register1 where whom_to_meet =? and purpose ='Business'",(department_name,))
        visitors_business = cursor.fetchone()
        
        # Fetch the video records for the specified course
        cursor.execute("SELECT * FROM register1 where whom_to_meet=? order by id DESC", (department_name,))
        orders = cursor.fetchall()
        
        cursor.execute("SELECT * FROM register1 where whom_to_meet=? and purpose ='Personal'  order by id DESC "  , (department_name,))
        personal_visitors = cursor.fetchall()
        
        cursor.execute("SELECT * FROM register1 where whom_to_meet=? and purpose ='Business'  order by id DESC"  , (department_name,))
        business_visitors = cursor.fetchall()
        
       
        conn.close()
        return templates.TemplateResponse("Tdashboard.html",{"request":request, "orders": orders, "name": name, "department": department, "date_of_birth": date_of_birth, "contact_number":contact_number, "email":email, "pfp": pfp, "total_visitors":total_visitors[0], "visitors_personal": visitors_personal[0], "visitors_business":visitors_business[0], "personal_visitors": personal_visitors, "business_visitors": business_visitors})
    else:
        return "Unauthorized acess"


@app.get("/FFdashboard", response_class=HTMLResponse)
def FFdashboard(request:Request):
    isLogin = request.session.get('isLogin')
    role = request.session.get('role')
    email = request.session.get('email')
    
    users = db.executeQueryWithParams("select * from users where email =?", [email,])[0]
    name = users['name']
    department = users['department']
    contact_number = users['contact_number']
    date_of_birth = users['date_of_birth']
    pfp = users['pfp']
    whom_to_meet = name + " - " + department
    if role == 1:
        #if status != None:
        #db.executeQueryWithParams("UPDATE register1 set status = ? where id =? ",[status,id])
        conn = sqlite3.connect("app.db")
        cursor = conn.cursor()
        admin= cursor.execute("SELECT * FROM users where email=?", (email,))

        cursor.execute("SELECT COUNT(*) FROM register1 where whom_to_meet =?", (whom_to_meet,))
        total_visitors = cursor.fetchone()
        
        cursor.execute("SELECT COUNT(*) FROM register1 where whom_to_meet =? and purpose ='Personal'",(whom_to_meet,))
        visitors_personal = cursor.fetchone()
        
        cursor.execute("SELECT COUNT(*) FROM register1 where whom_to_meet =? and purpose ='Business'",(whom_to_meet,))
        visitors_business = cursor.fetchone()

        admin_meeting = db.executeQueryWithParams("select * from register1 where whom_to_meet =? order by id DESC", [whom_to_meet])
        admin_meeting_personal = db.executeQueryWithParams("select * from register1 where whom_to_meet =? and purpose =? order by id DESC", [whom_to_meet,"Personal"])
        admin_meeting_business = db.executeQueryWithParams("select * from register1 where whom_to_meet =? and purpose =? order by id DESC", [whom_to_meet,"Business"])
        orders = db.executeQuery("select * from register1 order by id DESC")
        return templates.TemplateResponse("FFdashboard.html",{"request":request, "orders": orders, "admin_meeting": admin_meeting, "admin_meeting_personal": admin_meeting_personal, "admin_meeting_business":  admin_meeting_business, "email":email, "admin": admin, "total_visitors":total_visitors[0], "visitors_personal": visitors_personal[0], "visitors_business":visitors_business[0], "name": name, "department": department, "date_of_birth": date_of_birth, "contact_number":contact_number, "pfp": pfp})
    else:
        return "Unauthorized Access"
    
@app.post("/Aauthorize", response_class=HTMLResponse)
def authorize(request:Request, statuses:str=Query(None),id:int=Query(None)):    
    db.executeQueryWithParams("UPDATE register1 set status = ? where id =? ",[statuses,id])
    return RedirectResponse('/FFdashboard', status_code=status.HTTP_302_FOUND)

@app.post("/Tauthorize", response_class=HTMLResponse)
def authorize(request:Request, statuses:str=Query(None),id:int=Query(None)):    
    db.executeQueryWithParams("UPDATE register1 set status = ? where id =? ",[statuses,id])
    return RedirectResponse('/Tdashboard', status_code=status.HTTP_302_FOUND)




   
@app.get("/logout", response_class=HTMLResponse)
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=status.HTTP_302_FOUND)
    



@app.get("/Fregister", response_class=HTMLResponse)
def create(request:Request):
    isLogin = request.session.get('isLogin')
    role = request.session.get('role')
    if role == 1:
        return templates.TemplateResponse("Fregister.html",{"request":request})
    else:
        return "Unauthorized acess"
    


   
@app.post("/Fregister", response_class=HTMLResponse)
def create_post(request: Request, name: str = Form(...), department: str = Form(...), contact_number: int = Form(...), date_of_birth: str = Form(...), email: str = Form(...), teachers_id: int = Form(...), password: str = Form(...), photo: UploadFile = File(...)):
    file_path = "static/images/" + photo.filename
    with open(file_path, "wb") as f:
        f.write(photo.file.read())

    # Hash the password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    data = {"name": name, "department": department, "contact_number": contact_number, "date_of_birth": date_of_birth, "email": email, "teachers_id": teachers_id, "password": hashed_password, "photo": file_path}
    if(db.insert("addteachers", data=data)):
        return templates.TemplateResponse("Fregister.html", {"request": request, "msg": "Account created successfully!!"})
    else:
        return templates.TemplateResponse("Fregister.html", {"request": request, "msg": "Unable to create account"})

    
@app.get("/login1", response_class=HTMLResponse)
def create(request:Request):
    return templates.TemplateResponse("login1.html",{"request":request})    
        

@app.get("/others", response_class=HTMLResponse)
def others(request:Request):
    email = request.session.get('email')
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT department FROM users WHERE email=?", (email,))
    department = cursor.fetchone()[0]
    
    
    cursor.execute("SELECT COUNT(*) FROM register1 WHERE whom_to_meet LIKE ? ORDER BY id DESC", ('% - ' + department,))
    total_visitors = cursor.fetchone()
        
    cursor.execute("SELECT COUNT(*) FROM register1 WHERE whom_to_meet LIKE ? and purpose='Personal' ORDER BY id DESC", ('% - ' + department,))
    visitors_personal = cursor.fetchone()
        
    cursor.execute("SELECT COUNT(*) FROM register1 WHERE whom_to_meet LIKE ? and purpose='Business' ORDER BY id DESC", ('% - ' + department,))
    visitors_business = cursor.fetchone()
    
    cursor.execute("SELECT * FROM register1 WHERE whom_to_meet LIKE ? ORDER BY id DESC", ('% - ' + department,))
    teacher_meeting = cursor.fetchall()
    cursor.execute("SELECT * FROM register1 WHERE whom_to_meet LIKE ? and purpose='Personal' ORDER BY id DESC", ('% - ' + department,))
    teacher_meeting_personal = cursor.fetchall()
    cursor.execute("SELECT * FROM register1 WHERE whom_to_meet LIKE ? and purpose='Business' ORDER BY id DESC", ('% - ' + department,))
    teacher_meeting_business = cursor.fetchall()
    orders = db.executeQuery("select * from register1 order by id DESC")
    return templates.TemplateResponse("others.html",{"request":request,"orders":orders, "teacher_meeting":teacher_meeting, "teacher_meeting_personal":teacher_meeting_personal, "teacher_meeting_business":teacher_meeting_business,  "total_visitors":total_visitors[0], "visitors_personal": visitors_personal[0], "visitors_business":visitors_business[0]})

@app.get("/login2", response_class=HTMLResponse)
def create(request:Request):
    return templates.TemplateResponse("login2.html",{"request":request})

@app.get("/page1", response_class=HTMLResponse)
def create(request:Request):
    return templates.TemplateResponse("page1.html",{"request":request})

@app.get("/visitor1", response_class=HTMLResponse)
def create(request:Request):
    return templates.TemplateResponse("visitor1.html",{"request":request})

@app.get("/register", response_class=HTMLResponse)
def create(request:Request):
    teachers = db.executeQuery("select * from addteachers")
    admins = db.executeQuery("select * from users")
    return templates.TemplateResponse("register.html",{"request":request, "teachers": teachers, "admins":admins})

@app.get("/check-status", response_class=HTMLResponse)
def check_status(request:Request):
    return templates.TemplateResponse("check-status.html",{"request":request})

@app.post("/check-status",response_class=HTMLResponse)
def check_status(request:Request, phone:str = Form(...)):
    status_check = db.executeQueryWithParams("select * from register1 where contact_number =?", [phone])
    response = templates.TemplateResponse("check-status.html", {"request": request, "status_check": status_check})
    return response