import usocket
from drok200220 import *

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
	def __init__(self, dc_buck_object, relay_pin_object, abs_led, float_led, em_led, buzzer_pin_object, absorption_voltage_ref, float_voltage_ref, desired_current, transition_current_hi, transition_current_lo, init_time, emergency_time):
		self.dc_buck_object = dc_buck_object
		self.relay_pin_object = relay_pin_object
		self.buzzer_pin_object = buzzer_pin_object
		self.abs_led = abs_led
		self.float_led = float_led
		self.em_led = em_led
		self.absorption_voltage_ref = absorption_voltage_ref
		self.float_voltage_ref = float_voltage_ref
		self.desired_current = desired_current
		self.transition_current_hi = transition_current_hi
		self.transition_current_lo = transition_current_lo
		self.absorption_mode = True
		self.emergency_time = emergency_time
		self.init_time = init_time
		self.init = False
		if (absorption_voltage_ref <= float_voltage_ref) or (transition_current_hi <= transition_current_lo):
			raise ConfigError
		self.em_led.value(0)
		self.abs_led.value(1)
		self.float_led.value(1)
	def set_emergency_mode(self):
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
		self.init = False
		print("Emergency mode")
	def set_init_mode(self):
		self.set_absorption_mode()
		self.dc_buck_object.write_output_status(True)
		self.relay_pin_object.value(0)
		self.init = True
		time.sleep(self.init_time)
		print("Init OK")
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
		while True:
			try:
				if self.init == False:
					self.set_init_mode()
				else:
					self.set_mode(self.check_absorption_current())
			except:
				self.set_emergency_mode()
				time.sleep(self.emergency_time)
				

drok_obj = UART_DROK_200220(UART_NUMBER, PIN_UART_TX, PIN_UART_RX, RW_DELAY, RETRY_COUNT)
bat_obj = battery_handler(drok_obj, pin_relay, led_2, led_1, led_3, False, 2800, 2600, 0500, 0400, 0200, 5, 10)
bat_obj.run_loop()


