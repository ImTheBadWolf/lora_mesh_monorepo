import json

class AddressBook():
  def __init__(self, contacts_path, sensors_path):
    self.contacts_path = contacts_path
    self.sensors_path = sensors_path
    self.contacts = []
    self.sensors = []
    self.load_contacts()
    self.load_sensors()

  def load_contacts(self):
    try:
      f = open(self.contacts_path)
      self.contacts = json.load(f)
      f.close()
    except:
      self.contacts = []

  def load_sensors(self):
    try:
      f = open(self.sensors_path)
      self.sensors = json.load(f)
      f.close()
    except:
      self.sensors = []

  def save_contacts(self):
    with open(self.contacts_path, 'w') as f:
      json.dump(self.contacts, f)

  def save_sensors(self):
    with open(self.sensors_path, 'w') as f:
      json.dump(self.sensors, f)

  def add_contact(self, name, address):
    address = address[:2] + address[2:].upper()
    for contact in self.contacts:
      if contact['address'] == address:
        self.contacts.remove(contact)
        self.contacts.append({'address': address, 'name': name})
        self.save_contacts()
        return
    self.contacts.append({'address': address, 'name': name})
    self.save_contacts()

  def add_sensor(self, name, address):
    address = address[:2] + address[2:].upper()
    for sensor in self.sensors:
      if sensor['address'] == address:
        self.sensors.remove(sensor)
        self.sensors.append({'address': address, 'name': name})
        self.save_sensors()
        return
    self.sensors.append({'address': address, 'name': name})
    self.save_sensors()

  def del_contact(self, address):
    for contact in self.contacts:
      if contact['address'] == address:
        self.contacts.remove(contact)
        self.save_contacts()
        return True
    return False

  def del_sensor(self, address):
    for sensor in self.sensors:
      if sensor['address'] == address:
        self.sensors.remove(sensor)
        self.save_sensors()
        return True
    return False

  def get_contacts(self):
    return self.contacts

  def get_sensors(self):
    return self.sensors

  def update_contact_info(self, address, last_snr, hop_count):
    for contact in self.contacts:
      if contact['address'] == address:
        contact['last_snr'] = last_snr
        contact['hop_count'] = hop_count
        self.save_contacts()
        return True
    return False

  def update_sensor_info(self, address, last_snr):
    for sensor in self.sensors:
      if sensor['address'] == address:
        sensor['last_snr'] = last_snr
        self.save_sensors()
        return True
    return False
