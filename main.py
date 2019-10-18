from uos import urandom
from ubinascii import hexlify
from utime import ticks_ms, ticks_diff
from drok200220 import *
from charger_comm_module import *
from charger_comm_config import *
import gc
PIN_RELAY_OUTPUT = 0
PIN_UART_TX = 17
PIN_UART_RX = 16
UART_NUMBER = 1
RW_DELAY = 1
RETRY_COUNT = 3
TRANSITION_CURRENT = 200

pin_relay = Pin(PIN_RELAY_OUTPUT, Pin.OUT, value=1)
led_1 = Pin(21, Pin.OUT, value=1)
led_2 = Pin(22, Pin.OUT, value=1)
led_3 = Pin(23, Pin.OUT, value=1)

class battery_handler(object):
	def __init__(self, dc_buck_object, relay_pin_object, abs_led, float_led, em_led, buzzer_pin_object, voltage_never_exceed, absorption_voltage_ref, float_voltage_ref, desired_current, transition_current_hi, transition_current_lo, init_time, emergency_time, json_enabled, charger_id, json_post_url):
		self.dc_buck_object = dc_buck_object
		self.relay_pin_object = relay_pin_object
		self.buzzer_pin_object = buzzer_pin_object
		self.abs_led = abs_led
		self.float_led = float_led
		self.em_led = em_led
		self.voltage_never_exceed = voltage_never_exceed
		self.absorption_voltage_ref = absorption_voltage_ref
		self.float_voltage_ref = float_voltage_ref
		self.desired_current = desired_current
		self.transition_current_hi = transition_current_hi
		self.transition_current_lo = transition_current_lo
		self.absorption_mode = True
		self.vne_triggered = False
		self.emergency_time = emergency_time
		self.init_time = init_time
		self.init = False
		if (absorption_voltage_ref <= float_voltage_ref) or (transition_current_hi <= transition_current_lo):
			raise ConfigError
		self.em_led.value(0)
		self.abs_led.value(1)
		self.float_led.value(1)
		self.json_enabled = json_enabled
		self.charger_id = charger_id
		self.json_post_url = json_post_url
		self.current_session = None
		self.triggered_emergency = False
		self.last_measurement_data = (False, False, False)
		self.generate_charge_session()
	def show_transmission_status(self, status):
		if status:
			orig_val = self.abs_led.value()
			self.abs_led.value(not orig_val)
			time.sleep(0.25)
			self.abs_led.value(orig_val)
		else:
			orig_val = self.em_led.value()
			self.em_led.value(not orig_val)
			time.sleep(0.25)
			self.em_led.value(orig_val)
	def generate_charge_session(self):
		if self.json_enabled:
			self.current_session = hexlify(urandom(31)).decode('utf-8')
	def try_send_json_data_if_enabled(self, voltage, current, emergency=0):
		if self.json_enabled == False:
			return False
		if emergency == 0:
			if self.triggered_emergency == True:
				self.triggered_emergency = False
				self.generate_charge_session()
			voltage = self.dc_buck_object.read_actual_output_voltage()
			current = self.dc_buck_object.read_actual_output_current()
			if self.last_measurement_data[0] == False:
				milliamps_second = 0
			else:
				time_difference_ms = ticks_diff(ticks_ms(), self.last_measurement_data[1])
				print("TD:", time_difference_ms)
				#subtracting the 60mA waste
				average_current = max((((self.last_measurement_data[2] + current) // 2)-6),0)
				print("C1", self.last_measurement_data[2])
				print("C2", current)
				print("avg", average_current)
				milliamps_second = (average_current * 10 * time_difference_ms) // 1000
				print("mAs", milliamps_second)
			self.last_measurement_data = (True, ticks_ms(), current)
		else:
			milliamps_second = 0
		try:
			send_json_data(self.json_post_url, self.charger_id, self.current_session, current, voltage, emergency, milliamps_second)
			self.show_transmission_status(True)
		except:
			self.show_transmission_status(False)
	def report_status(self):
		self.try_send_json_data_if_enabled(self.dc_buck_object.read_actual_output_voltage(), self.dc_buck_object.read_actual_output_current())
	def set_emergency_mode(self, emergency_type=1):
		self.triggered_emergency = True
		self.last_measurement_data = (False, False, False)
		try:
			self.relay_pin_object.value(1)
		except:
			pass
		try:
			self.em_led.value(0)
			self.abs_led.value(1)
			self.float_led.value(1)
			self.buzzer_pin_object.value(1)
		except:
			pass
		try:
			self.dc_buck_object.write_output_status(False)
		except:
			pass
		try:
			self.try_send_json_data_if_enabled(0, 0, emergency=emergency_type)
		except:
			pass
		self.init = False
		print("Emergency mode")
	def set_init_mode(self):
		self.set_absorption_mode()
		self.dc_buck_object.write_output_status(True)
		self.relay_pin_object.value(0)
		self.init = True
		time.sleep(self.init_time)
		print("Init OK")
		self.triggered_emergency = False
		self.generate_charge_session()
		self.last_measurement_data = (True, ticks_ms(), self.dc_buck_object.read_actual_output_current())
	def set_absorption_mode(self):
		self.dc_buck_object.write_output_voltage(self.absorption_voltage_ref)
		self.dc_buck_object.write_output_current(self.desired_current)
		self.abs_led.value(0)
		self.float_led.value(1)
		self.em_led.value(1)
		self.absorption_mode = True
	def set_float_mode(self):
		self.dc_buck_object.write_output_voltage(self.float_voltage_ref)
		self.dc_buck_object.write_output_current(self.desired_current)
		self.abs_led.value(1)
		self.float_led.value(0)
		self.em_led.value(1)
		self.absorption_mode = False
	def set_mode(self, absorption):
		if absorption:
			self.set_absorption_mode()
		else:
			self.set_float_mode()
	def check_vne(self):
		if self.dc_buck_object.read_actual_output_voltage() >= self.voltage_never_exceed:
			self.vne_triggered = True
			self.set_emergency_mode(emergency_type=2)
			while True:
				print("VNE EXCEEDED")
				time.sleep(self.emergency_time)
	def check_absorption_current(self):
		current = self.dc_buck_object.read_actual_output_current()
		print("CURRENT:",current,"ABS:",self.absorption_mode)
		if self.absorption_mode == True:
			if current < self.transition_current_lo:
				return False
			else:
				return True
		else:
			if current > self.transition_current_hi:
				return True
			else:
				return False
	def run_loop(self):
		while self.vne_triggered == False:
			try:
				if self.init == False:
					self.set_init_mode()
				else:
					self.check_vne()
					self.report_status()
					self.set_mode(self.check_absorption_current())
			except:
				self.set_emergency_mode()
				time.sleep(self.emergency_time)
			try:
				print("memory", gc.mem_free())
				print("collecting")
				gc.collect()
				print("memory", gc.mem_free())
			except:
				pass
				

drok_obj = UART_DROK_200220(UART_NUMBER, PIN_UART_TX, PIN_UART_RX, RW_DELAY, RETRY_COUNT)
bat_obj = battery_handler(drok_obj, pin_relay, led_2, led_1, led_3, False, 2850, 2815, 2670, 0500, 0400, 0200, 5, 10, True, SECRET_CHARGER_ID, JSON_API_URL)
bat_obj.run_loop()


