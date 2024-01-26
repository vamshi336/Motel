from flask import Flask, render_template, request,session


import pdfplumber
import re
import io
import pdb

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
import os

app.secret_key = os.urandom(24)






@app.route("/")
def home():
  return render_template("home.html")


def select_rooms_in_range(room_status_list, start, end):
  selected_rooms = [
      room for room in room_status_list
      if start <= int(room['Room Number']) < end
  ]
  return selected_rooms


def modify_room_type(room_extracted_list):
  for room in room_extracted_list:
    if room.get('Reservation Status') == 'Stayover':
      room['Reservation Status'] = 'SO'
    elif room.get('Reservation Status') == 'Due':
      room['Reservation Status'] = 'DO'
    elif room.get('Reservation Status') == 'Not Reserved':
      room['Reservation Status'] = 'OUT'
    else:
      room['Reservation Status'] = 'DV'
  return room_extracted_list  # Corrected variable name


def extract_room_status(file_like_object):
  with pdfplumber.open(file_like_object) as pdf:
    text = ""
    for page_num in range(len(pdf.pages)):
      page = pdf.pages[page_num]
      text += page.extract_text()

  room_status_pattern = re.compile(
      r'(\d{3,4})\s+(\w+)\s+Dirty\s+(\w+)\s+(\w+)')
  matches = room_status_pattern.findall(text)

  room_status_list = [{
      'Room Number': match[0],
      'Room Type': match[1],
      'Reservation Status': match[3]
  } for match in matches]

  return room_status_list


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
  global room_status_list  # Use the global keyword to modify the global variable
  if request.method == "POST":
    file_content = request.files['file'].read()
    file_like_object = io.BytesIO(file_content)

    room_status_list = extract_room_status(file_like_object)
    session['room_status_list'] = room_status_list


    return render_template("upload_form.html",
                           room_status_list=room_status_list)

  # Render the upload form for GET requests
  return render_template("upload_form.html")


@app.route('/room_range', methods=['GET'])
def room_range():
  start = int(request.args.get('start', 101))
  end = int(request.args.get('end', 200))
  series = request.args.get('series', 'even')
  room_status_list = session.get('room_status_list', [])
  print(room_status_list)

  # Select rooms in the specified range
  selected_rooms = select_rooms_in_range(room_status_list, start, end)

  if series == 'even':
    selected_even_rooms = [
        room for room in selected_rooms if int(room['Room Number']) % 2 == 0
    ]
    yyy = modify_room_type(selected_even_rooms)
    return render_template('upload_form.html', room_list=yyy)

  elif series == 'odd':
    selected_odd_rooms = [
        room for room in selected_rooms if int(room["Room Number"]) % 2 != 0
    ]
    xxx = modify_room_type(selected_odd_rooms)
    return render_template('upload_form.html', room_list=xxx)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
    session(app)
