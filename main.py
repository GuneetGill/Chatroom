from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
import random
from string import ascii_uppercase

app = Flask(__name__)
app.config["SECRET_KEY"] = "hjhjsdahhds"
socketio = SocketIO(app)

# store all info related to room 
rooms = {}

# to create room codes 
def generate_unique_code(length):
    while True:
        code = ""
        for _ in range(length):
            # create random code with uppercase ASCI elements 
            code += random.choice(ascii_uppercase)
        
        #check if code exists 
        if code not in rooms:
            break
        
    return code

@app.route("/", methods=["POST", "GET"])
def home():
    #once we get homepage session gets cleared
    session.clear()
    
    if request.method == "POST":
        
        #get all data from input feilds 
        name = request.form.get("name")
        code = request.form.get("code")
        
        # attempt to get this key out of dicttionary if it does not exist return False
        join = request.form.get("join", False)
        create = request.form.get("create", False)

        #if user did not enter name create error and pass it to html
        if not name:
            return render_template("home.html", error="Please enter a name.", code=code, name=name)

        # if no code for room 
        if join != False and not code:
            return render_template("home.html", error="Please enter a room code.", code=code, name=name)
        
        room = code
        
        #create room code 
        if create != False:
            # create room code
            room = generate_unique_code(4)
            # add to rooms dictionary 
            rooms[room] = {"members": 0, "messages": []}
            
        # if ur joining room and room does not exist create error
        elif code not in rooms:
            return render_template("home.html", error="Room does not exist.", code=code, name=name)
        
        #create session: temp data stored on server so room code and username 
        #stored so when we refresh it does not get rid of everything
        session["room"] = room
        session["name"] = name
        
        #if all was successfull send them to another room 
        return redirect(url_for("room"))

    return render_template("home.html")

@app.route("/room")
def room():
    room = session.get("room")
    
    #go back to homepage, only enter room thorugh homepage in hopes user cannot directly go to room with url 
    if room is None or session.get("name") is None or room not in rooms:
        return redirect(url_for("home"))

    return render_template("room.html", code=room, messages=rooms[room]["messages"])


@socketio.on("message")
def message(data):
    room = session.get("room")
    if room not in rooms:
        return 
    
    content = {
        "name": session.get("name"),
        "message": data["data"]
    }
    
    send(content, to=room)
    rooms[room]["messages"].append(content)
    print(f"{session.get('name')} said: {data['data']}")

@socketio.on("connect")
def connect(auth):
    #look in session for user name and room id 
    room = session.get("room")
    name = session.get("name")
    
    if not room or not name:
        return
    
    if room not in rooms:
        # leave room function is from socket io
        leave_room(room)
        return
    
    # join room function is from socket io
    join_room(room)
    # socket 
    send({"name": name, "message": "has entered the room"}, to=room)
    rooms[room]["members"] += 1
    print(f"{name} joined room {room}")

@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    
    #function from socketio
    leave_room(room)

    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            # if everyone left room delete room
            del rooms[room]
    
    send({"name": name, "message": "has left the room"}, to=room)
    print(f"{name} has left the room {room}")

if __name__ == "__main__":
    socketio.run(app, debug=True)