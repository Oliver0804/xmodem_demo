#include <XModem.h>
XModem xmodem;

const int ledPin = 2; // D2 is GPIO 2 on ESP32

// The Arduino toolchain will add these declarations automatically, but doing
// manually so things also just work if someone uses a different/custom toolchain
bool process_block(void *blk_id, size_t idSize, byte *data, size_t dataSize);

/*
 * You can test this over your USB port using lrzsz: `stty -F /dev/ttyUSB0 4800 && sx -vaX /path/to/send/file > /dev/ttyUSB0 < /dev/ttyUSB0`
 * If you want to try CRC_XMODEM then add a o flag to the sx command (-vaoX)
 */
void setup() {
  Serial.begin(4800, SERIAL_8N1);
  xmodem.begin(Serial, XModem::ProtocolType::XMODEM);
  xmodem.setRecieveBlockHandler(process_block);

  pinMode(ledPin, OUTPUT); // Set D2 as an output pin
}

void loop() {
  // This simple example continuously tries to read data
  xmodem.receive();
}

bool process_block(void *blk_id, size_t idSize, byte *data, size_t dataSize) {
  byte id = *((byte *) blk_id);

  // Toggle LED
  digitalWrite(ledPin, HIGH); // Turn the LED on
  delay(100);                 // Keep it on for a short duration
  digitalWrite(ledPin, LOW);  // Turn the LED off

  for (int i = 0; i < dataSize; ++i) {
    // Do stuff with the received data
  }

  // Return false to stop the transfer early
  return true;
}
