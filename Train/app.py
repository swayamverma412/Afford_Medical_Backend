from flask import jsonify,Flask,request
import json
import requests
from datetime import datetime, timedelta

app=Flask(__name__)

def register_company(c_name,o_name,r_no,o_email,access_code):
    url="http://20.244.56.144/train/register"
    request_data={
        "companyName":c_name,
        "ownerName":o_name,
        "rollNo":r_no,
        "ownerEmail":o_email,
        "accessCode":access_code
    }

    response=requests.post(url,json=request_data)
    print(response.json())
    if response.status_code==200:
        with open("creds.json","w") as f:
            f.write(response.text)




def save_auth_data(auth_json):
    try:
        # Parse the JSON data

        # Extract the access token and expiry date
        access_token = auth_json.get("access_token")
        expires_in = auth_json.get("expires_in")
        # Calculate the expiry date
        expires_in = int(expires_in)/10  # expires_in is in seconds
        current_time = datetime.now()
        expiry_date = current_time + timedelta(microseconds=expires_in)

        # Prepare the data to save
        data_to_save = {
            "access_token": access_token,
            "expiry_date": expiry_date.isoformat()
        }
        print(data_to_save)
        # Save the data to a file (e.g., auth_data.json)
        with open("auth_data.json", "w") as file:
            json.dump(data_to_save, file)

        print("Auth data saved successfully.")
    except Exception as e:
        print("Error while saving auth data:", str(e))



#wrapper for auth
def auth_wrapper():
    url="http://20.244.56.144/train/auth"
    with open("auth_data.json","r+") as f:
        data=f.read()
    data=json.loads(data)
    expiry=data.get("expiry_date",str(datetime.now()))
    expiry=datetime.fromisoformat(expiry)
    if expiry>datetime.now():
        # print("token is valid")
        return data["access_token"]
    else:
        with open("creds.json","r+") as f:
            data=f.read()
        req_data=json.loads(data)
        print(req_data)
        response=requests.post(url,json=req_data)
        print(response.text)
        if response.status_code==200:
            save_auth_data(response.json())
            return response.json()["access_token"]
        pass
    
def filter_and_sort_trains(train_data):
    # Get the current time
    current_time = datetime.now()

    # Define a function to calculate total delay in minutes
    def calculate_total_delay(departure_time, delay):
        dep_time = datetime(current_time.year, current_time.month, current_time.day,
                            departure_time['Hours'], departure_time['Minutes'], departure_time['Seconds'])
        total_delay = delay
        if dep_time <= current_time:
            total_delay += (current_time - dep_time).seconds // 60
        return total_delay

    # Filter trains departing in the next 12 hours and not in the next 30 minutes (considering delays)
    filtered_trains = []
    for train in train_data:
        total_delay = calculate_total_delay(train['departureTime'], train['delayedBy'])
        if total_delay >= 30 and total_delay < 12 * 60:  # 30 minutes and 12 hours in minutes
            filtered_trains.append({**train, 'totalDelay': total_delay})

    # Sort the filtered trains based on price (ascending), seats availability (descending),
    # and departure time (descending after considering delays)
    sorted_trains = sorted(filtered_trains, key=lambda x: (x['price']['sleeper'], -x['seatsAvailable']['sleeper'], -x['totalDelay']))

    return sorted_trains

def get_all_train_list():
    url="http://20.244.56.144/train/trains"
    auth_token=auth_wrapper()
    headers={"Authorization":f"Bearer {auth_token}"}
    response=requests.get(url,headers=headers)
    print(response.text)
    response=response.json()
    return filter_and_sort_trains(response)


def get_specific_train(train_no):
    url=f"http://20.244.56.144/train/trains/{train_no}"
    auth_token=auth_wrapper()
    headers={"Authorization":f"Bearer {auth_token}"}
    response=requests.get(url,headers=headers)
    try:
        response=response.json()
    except:
        response=response.text
    return response

@app.route("/")
def home():
    return "Swayam Train API"


@app.route("/all_trains")
def all_trains():
    trains=get_all_train_list()
    return jsonify(trains)

@app.route("/specific_train")
def specific_train():
    train_no=request.args.get("train_no")

    if not train_no:
        return jsonify({"message":"train_no is required"}),400

    train=get_specific_train(train_no)
    return jsonify(train)

if __name__=="__main__":
    # register_company("DONE IN 20","Swayam","2006385","2006385@kiit.ac.in","oJnNPG")  
    app.run(debug=True,port=3000)