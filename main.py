#required module for this process

from typing import Union
import json
from fastapi import Cookie
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse
from pydantic import BaseModel
import time

class Baseparm(BaseModel):
    email:str
    passwd:str


#Initialing framework
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


#sample acccount details
# Here, I use dictionary instead of database or sql because of demo purpose

d = {'uname':'01@gmail.com',"passwd":'01'}

# I have stored user logged in details in details.json file with their 
# logged in device, ip, browser and logged in time details.
# Here these two funtions are used to read the 
## details of browsers that are logged in with same account
## and another one is used to update json file after logout

def read():
    f = open('details.json','r+')
    bjson = json.load(f)
    f.close()
    return bjson

def dump(bjson):
    f = open('details.json','w+')
    json.dump(bjson,f)
    f.close()


## root route
@app.get("/",response_class=HTMLResponse)
async def read_item(request: Request):

    ## reading logged in browser details and 
    ## check if present cookies matched with logged in details or not.
    ## if found load dashboard otherwise redirect to index.html after setting new cookies

    bjson = read()

    if request.headers.get('cookie') is not None:
        if request.headers.get('cookie') in bjson.keys():
            return templates.TemplateResponse("dashboard.html",{'request':request})
    #return templates.TemplateResponse("index.html",{'request':request})
    response = RedirectResponse(url="/index.html")
    response.set_cookie(
            "authorization",
            value=f"Bearer {time.ctime()}",
        )
    return response

## route for index.html, same as root route. Nothing new.

@app.get("/index.html", response_class=HTMLResponse)
async def indexhtml(request: Request):
    bjson = read()
    
    if request.headers.get('cookie') is not None:
        if request.headers.get('cookie') in bjson.keys():
            return templates.TemplateResponse("dashboard.html",{'request':request})

    return templates.TemplateResponse("index.html",{'request':request})

## route for dashboard, same as root route. Nothing new.

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    bjson = read()
    if request.headers.get('cookie') is not None:
        if request.headers.get('cookie') in bjson.keys():
            return templates.TemplateResponse("dashboard.html",{'request':request})

    #return templates.TemplateResponse("index.html",{'request':request})
    ## check if present cookies matched with logged in details or not.
    ## if found load dashboard otherwise redirect to root.
    response = RedirectResponse(url="/")
    return response
    


## route used to fetch data to show logged in browser details in dashboard.html
@app.get("/data")
async def fetchdata():
    bjson = read()
    return {"l":list(bjson.values())}

## login route , requests takes json data contains username and pass
## if post data matched with sample credentials 
## then dump to details.json of ip, time, os, browser's details of request.
@app.post("/login")
async def login(request: Request, baseparm : Baseparm):
    req_info = baseparm
    if (req_info.email == d['uname'] and req_info.passwd == d['passwd']):
        bjson = read()
        ## get user agents from request headers
        s = request.headers.get('user-agent')
        os_ = s[s.find('(')+1:s.find(')')]

        if request.headers.get('cookie') is not None:
            bjson[request.headers.get('cookie')] = {
                    "ip":str(request.client.host),
                    "time":str(time.ctime()),
                    "OS": str(os_).split("; ")[1],
                    "Browser" : s.split(" ")[-1]
                }
        dump(bjson)
        
        # if loggedin correctly, then send suceess as 1
        return {"login":"1"}
    # otherwise login failed as 0
    return {"login":"0"}


## logout route used to logout other sessions used timestamp
@app.get("/logout/{t}")
def logout(t, request: Request):
    bjson = read()
    new = {}

## if logout present session send none to user to redirect index.html
    if request.headers.get('cookie') not in list(bjson.keys()):
        return {"l":[None]}
    ## otherwise remove logged in session which contains specific timestamp
    for i,j in bjson.items():
        if j['time'] == t:
            continue
        new[i] = j
    dump(new)

    ## sending updated session details to the browser
    if bjson[request.headers.get('cookie')] in list(new.keys()):
        return {"l":list(new.values())}
