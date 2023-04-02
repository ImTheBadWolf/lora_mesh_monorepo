import json

REBOOT_REQUIRED_KEYS = ['MY_ADDRESS', 'LORA_CONFIG']
class ProtocolConfig():
  def __init__(self, config_path):
    self.config_path = config_path
    self.config = {}
    self.load_config()
    self.reboot_required = False

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
    print("Saving config")
    with open(self.config_path, 'w') as f:
      json.dump(self.config, f)

  def get_item_from_config(self, item_key):
    if item_key in self.config:
      return self.config[item_key]
    else:
      return None

  def update_item_in_config(self, item_key, item_value):
    if item_key not in self.config or self.config[item_key] != item_value:
      self.config[item_key] = item_value
      if item_key in REBOOT_REQUIRED_KEYS:
        self.reboot_required = True

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
    else:
      return None

  @MY_ADDRESS.setter
  def MY_ADDRESS(self, value):
    if self.get_item_from_config("MY_ADDRESS") is not None:
      raise ValueError("MY_ADDRESS can be set only once")
    self.update_item_in_config("MY_ADDRESS", value.upper())

  @property
  def RESEND_COUNT(self):
    return self.get_item_from_config("RESEND_COUNT")

  @RESEND_COUNT.setter
  def RESEND_COUNT(self, value):
    value = int(value)
    if value < 1 or value > 20:
      raise ValueError("RESEND_COUNT must be between 1 and 20")
    self.update_item_in_config("RESEND_COUNT", value)

  @property
  def RESEND_TIMEOUT(self):
    return self.get_item_from_config("RESEND_TIMEOUT")

  @RESEND_TIMEOUT.setter
  def RESEND_TIMEOUT(self, value):
    value = int(value)
    if value < 1 or value > 20:
      raise ValueError("RESEND_TIMEOUT must be between 1 and 20")
    self.update_item_in_config("RESEND_TIMEOUT", value)

  @property
  def ACK_WAIT_TIME(self):
    return self.get_item_from_config("ACK_WAIT_TIME")

  @ACK_WAIT_TIME.setter
  def ACK_WAIT_TIME(self, value):
    value = int(value)
    if value < 1 or value > 300:
      raise ValueError("ACK_WAIT_TIME must be between 1 and 300")
    self.update_item_in_config("ACK_WAIT_TIME", value)

  @property
  def DEFAULT_MAX_HOP(self):
    return self.get_item_from_config("DEFAULT_MAX_HOP")

  @DEFAULT_MAX_HOP.setter
  def DEFAULT_MAX_HOP(self, value):
    value = int(value)
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
  def MONITORING_ENABLED(self):
    return self.get_item_from_config("MONITORING_ENABLED")

  @MONITORING_ENABLED.setter
  def MONITORING_ENABLED(self, value):
    self.update_item_in_config("MONITORING_ENABLED", value)

  #Properties bellow are read-only, and can be changed only by changing the hard-coded values in this file
  @property
  def DEFAULT_TTL(self):
    return 50 #DEFAULT value (in seconds, max 2B - 65536)

  @property
  def DELETE_WAIT_TIME(self):
    return 120 #DEFAULT value (in seconds)

  @property
  def CSMA_TIMEOUT(self):
    return 150 #DEFAULT value (in ms)

  @property
  def BROADCAST_ADDRESS(self):
    return 0xFFFF

  @property
  def CONTACTS(self):
    return self.get_item_from_config("CONTACTS")

  @property
  def DEBUG(self):
    return False #True if you want the display to show all debug messages

  def is_reboot_required(self):
    return self.reboot_required

  def get_config(self):
    ret_dict = {
      'aes_key': self.AES_KEY,
      'resend_count': self.RESEND_COUNT,
      'resend_timeout': self.RESEND_TIMEOUT,
      'ack_wait': self.ACK_WAIT_TIME,
      'randomize_path': self.RANDOMIZE_PATH,
      'my_address': f"0x{self.MY_ADDRESS:04x}" if self.MY_ADDRESS is not None else None,
      'monitoring_enabled': self.MONITORING_ENABLED,
      'lora_config': "Bw500Cr45Sf128" #TODO
    }
    return ret_dict

  def update_config(self, config):
    self.AES_KEY = config['aes_key']
    self.RESEND_COUNT = config['resend_count']
    self.RESEND_TIMEOUT = config['resend_timeout']
    self.ACK_WAIT_TIME = config['ack_wait']
    self.RANDOMIZE_PATH = config['randomize_path']
    self.MONITORING_ENABLED = config['monitoring_enabled']

    if self.MY_ADDRESS is None:
      print("Setting my address")
      self.MY_ADDRESS = config['my_address']
    self.save_config()

    #TODO lora config

  def get_networks(self):
    return self.get_item_from_config("WIFI_NETWORKS")

  def add_network(self, network):
    networks = self.get_networks()
    if networks is None:
      networks = []
    #Check if networks doesnt contain network with same ssid
    if any(network['SSID'] == network_o['SSID'] for network_o in networks):
      raise ValueError("Network with same ssid already exists")
    if network['AP'] == True:
      if any(network_o['AP'] == True for network_o in networks):
        raise ValueError("Network defined as AP already exists")
    networks.append({
      'SSID': network['SSID'],
      'PASSWORD': network['PASSWORD'],
      'AP': network['AP']
    })
    self.update_item_in_config("WIFI_NETWORKS", networks)
    self.save_config()

  def remove_network(self, ssid):
    networks = self.get_networks()
    if networks is not None:
      networks = [network for network in networks if network['SSID'] != ssid]
      self.update_item_in_config("WIFI_NETWORKS", networks)
      self.save_config()

#TODO parse lora config and export each parameter separately. But set them all at once with string "Bw500Cr45Sf128"