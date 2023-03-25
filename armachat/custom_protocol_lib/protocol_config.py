import json

CONTACT = 0x0002 #TODO just for testing

class ProtocolConfig():
  def __init__(self, config_path):
    self.config_path = config_path
    self.config = {}
    self.load_config()

  def load_config(self):
    try:
      f = open(self.config_path)
      self.config = json.load(f)
      f.close()
    except:
      print("Error loading config file")

  def is_initialised(self):
    if self.get_item_from_config("MY_ADDRESS") is None:
      return False
    return True

  def save_config(self):
    with open(self.config_path, 'w') as f:
      json.dump(self.config, f)

  def get_item_from_config(self, item_key):
    if item_key in self.config:
      return self.config[item_key]
    else:
      return None

  def update_item_in_config(self, item_key, item_value):
    self.config[item_key] = item_value
    self.save_config()

  @property
  def AES_KEY(self):
    return self.get_item_from_config("AES_KEY")

  @AES_KEY.setter
  def AES_KEY(self, value):
    if len(value) < 16:
      raise ValueError("AES key must be 16 characters long")
    self.update_item_in_config("AES_KEY", value)

  @property
  def MY_ADDRESS(self):
    str_address = self.get_item_from_config("MY_ADDRESS")
    if str_address is not None:
      return int(str_address, 16)

  @MY_ADDRESS.setter
  def MY_ADDRESS(self, value):
    if self.get_item_from_config("MY_ADDRESS") is not None:
      raise ValueError("MY_ADDRESS can be set only once")
    self.update_item_in_config("MY_ADDRESS", value)

  @property
  def RESEND_COUNT(self):
    return self.get_item_from_config("RESEND_COUNT")

  @RESEND_COUNT.setter
  def RESEND_COUNT(self, value):
    self.update_item_in_config("RESEND_COUNT", value)

  @property
  def RESEND_TIMEOUT(self):
    return self.get_item_from_config("RESEND_TIMEOUT")

  @RESEND_TIMEOUT.setter
  def RESEND_TIMEOUT(self, value):
    self.update_item_in_config("RESEND_TIMEOUT", value)

  @property
  def ACK_WAIT_TIME(self):
    return self.get_item_from_config("ACK_WAIT_TIME")

  @ACK_WAIT_TIME.setter
  def ACK_WAIT_TIME(self, value):
    self.update_item_in_config("ACK_WAIT_TIME", value)

  @property
  def ACK_WAIT_TIME(self):
    return self.get_item_from_config("ACK_WAIT_TIME")

  @ACK_WAIT_TIME.setter
  def ACK_WAIT_TIME(self, value):
    self.update_item_in_config("ACK_WAIT_TIME", value)

  @property
  def DEFAULT_MAX_HOP(self):
    return self.get_item_from_config("DEFAULT_MAX_HOP")

  @DEFAULT_MAX_HOP.setter
  def DEFAULT_MAX_HOP(self, value):
    if value > 255:
      raise ValueError("DEFAULT_MAX_HOP must be less than 256")
    self.update_item_in_config("DEFAULT_MAX_HOP", value)

  @property
  def RANDOMIZE_PATH(self):
    return self.get_item_from_config("RANDOMIZE_PATH")

  @RANDOMIZE_PATH.setter
  def RANDOMIZE_PATH(self, value):
    self.update_item_in_config("RANDOMIZE_PATH", value)

  @property
  def DELETE_WAIT_TIME(self):
    return 120 #DEFAULT value (in seconds)

  @property
  def DEFAULT_TTL(self):
    return 50 #DEFAULT value (in seconds, max 2B - 65536)

#TODO parse lora config and export each parameter separately. But set them all at once with string "Bw500Cr45Sf128"