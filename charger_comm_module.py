try:
	import urequests as requests
except ImportError:
	import requests
import time

def send_json_data(url, charger_id, charge_session, current, voltage, emergency, milliamps_second, retry_count=3):
	json_data = {
	"charger-id": charger_id,
	"charge-session": charge_session,
	"current": current,
	"voltage": voltage,
	"emergency": emergency,
	"milliamps-second": milliamps_second
	}
	while retry_count > 0:
		try:
			r = requests.post(url, json=json_data)
			if r.status_code == 201:
				return True
			else:
				time.sleep(1)
				print("resp status", r.status_code)
				retry_count -= 1
		except Exception as e:
			print(e)
			time.sleep(1)
			retry_count -= 1
	if retry_count == 0:
		raise Exception